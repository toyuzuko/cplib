from __future__ import annotations

import config
from cplib.tools.tester import run_tester


def main() -> None:
    if not run_tester(
        num_of_cases=config.NUM_CASES,
        timeout=config.TIMEOUT_SECONDS,
        generator="generator.py",
        naive="naive.py",
        judge="judge.py",
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
