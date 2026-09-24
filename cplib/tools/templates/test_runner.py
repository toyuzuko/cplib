#!/usr/bin/env python3
"""Driver script that invokes ``cplib.tools.tester`` for one problem directory.

Usage:
    Place this file in the same directory as ``main.py``, ``generator.py``,
    ``naive.py``, and ``judge.py``.

    Edit ``CONFIG`` below to set the number of cases, interactive mode, and
    helper file paths.

    Run ``python test_runner.py`` or import ``main`` and call it.

Notes:
    All parameters are forwarded to ``cplib.tools.tester.run_tester``.
    Relative paths, main.py, and logs are resolved from this script's directory.
    The caller's working directory is restored when main returns or raises.
"""

from __future__ import annotations
from contextlib import chdir
from pathlib import Path

from cplib.tools.tester import run_tester


# ----------------------------------------------------------------------
# Configuration — edit freely
# ----------------------------------------------------------------------
CONFIG = dict(
    num_of_cases=100,        # number of testcases to generate
    interactive=False,       # set True for interactive tasks
    judge="judge.py",        # path or import-path to judge module
    generator="generator.py",# path or import-path to generator module
    naive="naive.py",        # path or import-path to naive module
    # naive_script=False,    # uncomment & set True if naive is script
    timeout=2.0,             # seconds per testcase
    random_seed=0,           # reproducibility
    verbose=False,           # print full I/O even for AC
    stop_on_failure=False,   # abort on first non-AC
)


# ----------------------------------------------------------------------
# Main wrapper — keeps the top-level import clean
# ----------------------------------------------------------------------
def main() -> None:
    """Run the tester from this problem directory using CONFIG.

    Returns:
        None when all cases pass.

    Raises:
        SystemExit: With status 1 if any testcase fails.

    Time Complexity:
        Depends on the configured generator, solver, and judge.

    Space Complexity:
        Depends on the configured testcase sizes and logs.
    """
    with chdir(Path(__file__).resolve().parent):
        if not run_tester(**CONFIG):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
