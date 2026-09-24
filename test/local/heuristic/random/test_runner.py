from __future__ import annotations

import random
import sys
import time

import config
from scenario import generate_case
from score import solve_case as solve_reference
from verify import check_primitives, solve_case as solve_verified


def main() -> None:
    rng = random.Random(0)
    check_primitives()

    for case_id in range(config.NUM_CASES):
        case = generate_case(rng)
        expected = solve_reference(case)
        case_start = time.perf_counter()
        actual = solve_verified(case)
        elapsed = time.perf_counter() - case_start
        if elapsed > config.TIMEOUT_SECONDS:
            print(f"Case #{case_id}: TLE ({elapsed:.4f}s)", file=sys.stderr)
            raise SystemExit(1)
        if actual != expected:
            print(f"Case #{case_id}: WA", file=sys.stderr)
            print(case, file=sys.stderr)
            print(f"expected: {expected}", file=sys.stderr)
            print(f"actual  : {actual}", file=sys.stderr)
            raise SystemExit(1)
        print(f"Case #{case_id}: AC ({elapsed:.4f}s)")

    print()
    print("--- Summary ---")
    print(f"AC  : {config.NUM_CASES}")
    print("WA  : 0")
    print("RE  : 0")
    print("TLE : 0")


if __name__ == "__main__":
    main()
