#!/bin/sh
# Usage: ./expander.sh <input_file> [output_file|-]

set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    export PATH="$ROOT_DIR/.venv/bin:$PATH"
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$ROOT_DIR/scripts/expander/expand_cplib.py" "$@"
