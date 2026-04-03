from __future__ import annotations

import asyncio
import argparse
import mimetypes
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import unquote, urlsplit

from ..layout import resolve_knowledge_layout
from ..repository import KnowledgeRepository
from .digest import calculate_export_digest, load_saved_export_digest, write_saved_export_digest
from .exporter import build_export_snapshot, materialize_export_snapshot
from .layout import (
    REVIEW_WIKI_HOST,
    REVIEW_WIKI_POLL_SECONDS,
    REVIEW_WIKI_PORT,
    ReviewWikiLayout,
    resolve_review_wiki_layout,
)


BuildRunner = Callable[[Path, Path, Path], None]


@dataclass(frozen=True)
class ReviewWikiSyncResult:
    rebuilt: bool
    digest: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m knowledge_graph.review_wiki.daemon",
        description="Serve and refresh the local Fleki review wiki.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repo root used for layout resolution and template lookup.",
    )
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--config-root", type=Path)
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--install-manifest-path", type=Path)
    parser.add_argument("--once", action="store_true", help="Run one sync pass and exit.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    layout = resolve_knowledge_layout(
        data_root=args.data_root,
        config_root=args.config_root,
        state_root=args.state_root,
        install_manifest_path=args.install_manifest_path,
        repo_root=args.repo_root,
    )
    repository = KnowledgeRepository(layout)
    if args.once:
        sync_review_wiki(repository)
        return 0
    serve_review_wiki(repository)
    return 0


def sync_review_wiki(
    repository: KnowledgeRepository,
    *,
    build_runner: BuildRunner | None = None,
) -> ReviewWikiSyncResult:
    snapshot = build_export_snapshot(repository)
    digest = calculate_export_digest(snapshot)
    review_layout = resolve_review_wiki_layout(repository.layout)
    previous_digest = load_saved_export_digest(review_layout.export_digest_path)
    if previous_digest == digest and review_layout.public_root.exists():
        return ReviewWikiSyncResult(rebuilt=False, digest=digest)

    materialize_export_snapshot(snapshot, review_layout.content_root)
    _require_quartz_workspace(review_layout)
    staging_public_root = review_layout.quartz_root / ".public.next"
    if staging_public_root.exists():
        shutil.rmtree(staging_public_root)

    active_build_runner = build_runner or _run_quartz_build
    active_build_runner(review_layout.quartz_root, staging_public_root, review_layout.build_log_path)
    _replace_tree(staging_public_root, review_layout.public_root)
    write_saved_export_digest(review_layout.export_digest_path, digest)
    return ReviewWikiSyncResult(rebuilt=True, digest=digest)


def serve_review_wiki(repository: KnowledgeRepository) -> None:
    review_layout = resolve_review_wiki_layout(repository.layout)
    sync_review_wiki(repository)

    stop_event = threading.Event()
    poller = threading.Thread(
        target=_poll_loop,
        args=(repository, stop_event),
        daemon=True,
    )
    poller.start()

    try:
        asyncio.run(_serve_static_site(review_layout.public_root))
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()


def _poll_loop(repository: KnowledgeRepository, stop_event: threading.Event) -> None:
    while not stop_event.wait(REVIEW_WIKI_POLL_SECONDS):
        sync_review_wiki(repository)


def _require_quartz_workspace(review_layout: ReviewWikiLayout) -> None:
    package_json = review_layout.quartz_root / "package.json"
    if not package_json.exists():
        raise RuntimeError(f"missing review-wiki Quartz workspace: {package_json}")


def _run_quartz_build(quartz_root: Path, output_root: Path, build_log_path: Path) -> None:
    command = [
        "node",
        "./quartz/bootstrap-cli.mjs",
        "build",
        "-d",
        "content",
        "-o",
        output_root.name,
    ]
    result = subprocess.run(
        command,
        cwd=quartz_root,
        capture_output=True,
        text=True,
        check=False,
    )
    build_log_path.parent.mkdir(parents=True, exist_ok=True)
    build_log_path.write_text((result.stdout or "") + (result.stderr or ""))
    if result.returncode != 0:
        raise RuntimeError(f"Quartz build failed with exit code {result.returncode}")


def _replace_tree(source_root: Path, target_root: Path) -> None:
    if target_root.exists():
        shutil.rmtree(target_root)
    source_root.replace(target_root)


async def _serve_static_site(public_root: Path) -> None:
    server = await asyncio.start_server(
        lambda reader, writer: _handle_http_request(reader, writer, public_root),
        host=REVIEW_WIKI_HOST,
        port=REVIEW_WIKI_PORT,
        reuse_address=True,
    )
    async with server:
        await server.serve_forever()


async def _handle_http_request(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    public_root: Path,
) -> None:
    try:
        request_line = await reader.readline()
        if not request_line:
            return
        try:
            method, target, _version = request_line.decode("iso-8859-1").strip().split()
        except ValueError:
            await _write_simple_response(writer, status="400 Bad Request", body=b"bad request\n")
            return

        while True:
            header_line = await reader.readline()
            if not header_line or header_line in {b"\r\n", b"\n"}:
                break

        if method not in {"GET", "HEAD"}:
            await _write_simple_response(
                writer,
                status="405 Method Not Allowed",
                body=b"method not allowed\n",
                extra_headers={"Allow": "GET, HEAD"},
                send_body=method != "HEAD",
            )
            return

        target_path = _resolve_public_path(public_root, target)
        if target_path is None:
            fallback = public_root / "404.html"
            if fallback.exists():
                await _write_file_response(
                    writer,
                    fallback,
                    status="404 Not Found",
                    send_body=method != "HEAD",
                )
            else:
                await _write_simple_response(
                    writer,
                    status="404 Not Found",
                    body=b"not found\n",
                    send_body=method != "HEAD",
                )
            return

        await _write_file_response(writer, target_path, send_body=method != "HEAD")
    finally:
        writer.close()
        await writer.wait_closed()


def _resolve_public_path(public_root: Path, request_target: str) -> Path | None:
    raw_path = unquote(urlsplit(request_target).path or "/")
    relative_parts = [part for part in Path(raw_path).parts if part not in {"", "/", "."}]
    relative_path = Path(*relative_parts) if relative_parts else Path()
    candidate = (public_root / relative_path).resolve()
    resolved_public_root = public_root.resolve()
    if not candidate.is_relative_to(resolved_public_root):
        return None
    if candidate.is_dir():
        index_path = candidate / "index.html"
        return index_path if index_path.exists() else None
    if candidate.exists():
        return candidate
    if not candidate.suffix:
        html_candidate = candidate.with_suffix(".html")
        if html_candidate.exists() and html_candidate.is_relative_to(resolved_public_root):
            return html_candidate
        nested_index = candidate / "index.html"
        if nested_index.exists() and nested_index.is_relative_to(resolved_public_root):
            return nested_index
    return None


async def _write_file_response(
    writer: asyncio.StreamWriter,
    path: Path,
    *,
    status: str = "200 OK",
    send_body: bool = True,
) -> None:
    body = path.read_bytes() if send_body else b""
    content_type, _encoding = mimetypes.guess_type(path.name)
    headers = {
        "Content-Length": str(path.stat().st_size),
        "Content-Type": content_type or "application/octet-stream",
    }
    await _write_response(writer, status=status, headers=headers, body=body)


async def _write_simple_response(
    writer: asyncio.StreamWriter,
    *,
    status: str,
    body: bytes,
    extra_headers: dict[str, str] | None = None,
    send_body: bool = True,
) -> None:
    payload = body if send_body else b""
    headers = {
        "Content-Length": str(len(body)),
        "Content-Type": "text/plain; charset=utf-8",
    }
    if extra_headers:
        headers.update(extra_headers)
    await _write_response(writer, status=status, headers=headers, body=payload)


async def _write_response(
    writer: asyncio.StreamWriter,
    *,
    status: str,
    headers: dict[str, str],
    body: bytes,
) -> None:
    lines = [f"HTTP/1.1 {status}"]
    for key, value in headers.items():
        lines.append(f"{key}: {value}")
    lines.append("Connection: close")
    header_bytes = ("\r\n".join(lines) + "\r\n\r\n").encode("iso-8859-1")
    writer.write(header_bytes)
    if body:
        writer.write(body)
    await writer.drain()


if __name__ == "__main__":
    raise SystemExit(main())
