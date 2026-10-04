#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export TMPDIR="$PWD/data/.cache/tmp"
mkdir -p "$TMPDIR"
uv_bin="${UV:-$HOME/.local/bin/uv}"
exec env -u PYTHONPATH "$uv_bin" run pytest --basetemp=data/.cache/pytest "$@"
