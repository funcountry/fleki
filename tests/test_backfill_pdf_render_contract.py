from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from common import copy_fixture_pdf, make_temp_repo, sample_save_decision
from knowledge_graph import SourceBinding


def _strip_pdf_render_contract(repo, manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text())
    render_manifest_path = manifest.pop("render_manifest_relative_path", None)
    render_markdown_path = manifest.pop("render_relative_path", None)
    manifest.pop("render_eligibility", None)
    manifest.pop("render_omission_reason", None)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    if render_manifest_path:
        (repo.data_root / render_manifest_path).unlink(missing_ok=True)
    if render_markdown_path:
        (repo.data_root / render_markdown_path).unlink(missing_ok=True)
        assets_dir = (repo.data_root / render_markdown_path).with_suffix(".assets")
        if assets_dir.exists():
            shutil.rmtree(assets_dir)
    return manifest_path.relative_to(repo.data_root).as_posix()


class BackfillPdfRenderContractTest(unittest.TestCase):
    def test_backfill_repairs_legacy_pdf_record(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = copy_fixture_pdf(root, "backfill.pdf")
        binding = SourceBinding(
            source_id="pdf.backfill.repair",
            local_path=pdf_path,
            source_kind="pdf_research",
            source_family="pdf",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/backfill-pdf-contract",
            candidate_title="Backfill PDF Contract",
            recommended_scope=["knowledge-system"],
        )
        decision["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"
        repo.apply_save(source_bindings=[binding], decision=decision)

        manifest_path = next((repo.data_root / "sources" / "pdf").glob("*.record.json"))
        relative_source_record = _strip_pdf_render_contract(repo, manifest_path)

        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo_root / 'src'}:{repo_root / 'tests'}"
        result = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "backfill_pdf_render_contract.py"),
                "--json",
                "--install-manifest-path",
                str(repo.install_manifest_path),
                "--repo-root",
                str(root),
                "--source-record",
                relative_source_record,
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=repo_root,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "repaired")
        self.assertEqual(payload["updated_source_records"], [relative_source_record])

        trace = repo.trace("knowledge-system/backfill-pdf-contract")
        self.assertEqual(trace["render_contract_gaps"], [])
        self.assertEqual(len(trace["render_manifests"]), 1)
        self.assertEqual(len(trace["render_artifacts"]), 1)

    def test_backfill_fails_loudly_when_raw_pdf_is_missing(self) -> None:
        temp_dir, root, repo = make_temp_repo()
        self.addCleanup(temp_dir.cleanup)

        pdf_path = copy_fixture_pdf(root, "backfill-missing.pdf")
        binding = SourceBinding(
            source_id="pdf.backfill.missing",
            local_path=pdf_path,
            source_kind="pdf_research",
            source_family="pdf",
            timestamp="2026-04-03T12:00:00+00:00",
        )
        decision = sample_save_decision(
            source_ids=[binding.source_id],
            topic_path="knowledge-system/backfill-pdf-contract-missing",
            candidate_title="Backfill PDF Contract Missing Raw",
            recommended_scope=["knowledge-system"],
        )
        decision["source_reading_reports"][0]["reading_mode"] = "direct_local_pdf"
        repo.apply_save(source_bindings=[binding], decision=decision)

        manifest_path = next((repo.data_root / "sources" / "pdf").glob("*.record.json"))
        relative_source_record = _strip_pdf_render_contract(repo, manifest_path)
        manifest = json.loads(manifest_path.read_text())
        (repo.data_root / manifest["relative_path"]).unlink()

        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo_root / 'src'}:{repo_root / 'tests'}"
        result = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "backfill_pdf_render_contract.py"),
                "--json",
                "--install-manifest-path",
                str(repo.install_manifest_path),
                "--repo-root",
                str(root),
                "--source-record",
                relative_source_record,
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=repo_root,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["result"], "failed")
        self.assertEqual(len(payload["errors"]), 1)
        self.assertIn("raw PDF is missing", payload["errors"][0]["error"])


if __name__ == "__main__":
    unittest.main()
