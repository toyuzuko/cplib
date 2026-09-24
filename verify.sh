#!/bin/sh
# Public verification-helper with repository-wide dependency tracking

set -eu

case "${1:-}" in
    ''|-h|--help)
        cat <<'EOF'
Usage:
  ./verify.sh run [PATH ...] [OPTIONS]
  ./verify.sh all [OPTIONS]
  ./verify.sh -h | --help

Commands:
  run PATH ...  Verify the specified *.test.py files.
  run           Verify all registered problems.
  all           Verify all registered problems without generating documentation.

Options for run/all:
  --tle SECONDS       Time limit per test case (default: 60).
  -j, --jobs N        Parallel test-case workers (default: 1).
  --timeout SECONDS   Verification time budget in GitHub Actions (default: 600).
                      Ignored for local runs; this is not a per-case time limit.

Examples:
  ./verify.sh run test/library_checker/unionfind.test.py
  ./verify.sh run test/aoj/ALDS1_2_C.test.py --tle 10
  ./verify.sh all -j 4
  ./verify.sh run -h

Paths are relative to the repository root. Unchanged, previously verified
files may be skipped. Test data is downloaded when needed.
Statistics are saved in tmp/verify/<timestamp>/results.json and summary.md.
Reports include case verdicts, elapsed seconds, and peak memory (MiB).
Memory requires GNU time; unavailable measurements are left empty.
Requires uv and the project Python environment; see README.md for setup.
This help does not install dependencies or run verification.
EOF
        exit 0
        ;;
esac

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec uv run --locked python "$ROOT_DIR/scripts/verify.py" "$@"
