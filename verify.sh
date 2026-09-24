#!/bin/sh
# Public verification-helper with repository-wide dependency tracking

set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec uv run --locked python "$ROOT_DIR/scripts/verify.py" "$@"
