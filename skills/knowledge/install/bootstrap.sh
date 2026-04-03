#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd -- "$script_dir/.." && pwd -P)"
runtime_dir="$skill_dir/runtime"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to install the bundled knowledge CLI." >&2
  exit 1
fi

if [[ ! -d "$runtime_dir/src/knowledge_graph" ]]; then
  echo "missing bundled runtime at $runtime_dir" >&2
  echo "From a Fleki repo checkout, run ./install.sh so the runtime bundle is generated before install." >&2
  exit 1
fi

PYTHONPATH="$runtime_dir/src${PYTHONPATH:+:$PYTHONPATH}" \
  uv tool install --force --python 3.12 "$runtime_dir"

PYTHONPATH="$runtime_dir/src${PYTHONPATH:+:$PYTHONPATH}" \
  uv run --no-project --python 3.12 --with "$runtime_dir" python - "$skill_dir" <<'PY'
import sys
from pathlib import Path

from knowledge_graph import (
    KnowledgeRepository,
    build_install_manifest,
    load_install_manifest,
    migrate_legacy_install,
    resolve_knowledge_layout,
    write_install_manifest,
)


skill_dir = Path(sys.argv[1]).resolve()
migration = migrate_legacy_install()
layout = resolve_knowledge_layout()
existing = load_install_manifest(layout.install_manifest_path) if layout.install_manifest_path.exists() else None

manifest = build_install_manifest(
    layout,
    canonical_skill_path=skill_dir,
    codex_managed_skill_path=existing.codex_managed_skill_path if existing else None,
    hermes_skill_paths=existing.hermes_skill_paths if existing else (),
    openclaw_skill_paths=existing.openclaw_skill_paths if existing else (),
    legacy_repo_root=existing.legacy_repo_root if existing else None,
)
write_install_manifest(manifest)

repo = KnowledgeRepository(layout)
repo.initialize_layout()

if migration is not None:
    print(f"migrated legacy Fleki root to {layout.config_root}")
print(f"install manifest written: {layout.install_manifest_path}")
print(f"knowledge data root: {layout.data_root}")
print("installing or refreshing the CLI does not clear an existing graph")
print(f"knowledge skill bundle: {skill_dir}")
PY

echo "Installed knowledge CLI and refreshed install manifest."
