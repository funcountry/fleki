#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required to run the Fleki installer." >&2
  exit 1
fi

PYTHONPATH="$script_dir/src${PYTHONPATH:+:$PYTHONPATH}" \
  uv run --python 3.12 python "$script_dir/scripts/install_knowledge_skill.py" "$@"
