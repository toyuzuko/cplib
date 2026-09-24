#!/bin/bash

# cplib-expand-with-format: Expand cplib imports and optionally format the library code
# Usage: cplib-expand-with-format <input_file> [output_file]

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Prefer the project-local virtualenv so behavior is consistent across terminals.
if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

# The Python driver owns expansion, formatting, cleanup, and atomic output.
exec "$PYTHON_BIN" "$SCRIPT_DIR/expand_cplib.py" "$@"
