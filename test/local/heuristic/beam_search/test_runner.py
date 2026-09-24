from __future__ import annotations

import random
import sys
import time

import config
from main import solve_case
from scenario import generate_case
from score import optimal_score, validate_and_score


def main() -> None:
    rng = random.Random(0)
    total_score = 0
    total_optimum = 0

    for case_id in range(config.NUM_CASES):
        case = generate_case(rng)
        case_start = time.perf_counter()
        solution = solve_case(case)
        elapsed = time.perf_counter() - case_start
        if elapsed > config.TIMEOUT_SECONDS:
            print(f'Case #{case_id}: TLE ({elapsed:.4f}s)', file=sys.stderr)
            raise SystemExit(1)
        score = validate_and_score(case, solution)
        optimum = optimal_score(case)
        total_score += score
        total_optimum += optimum
        ratio = 1.0 if optimum == 0 else score / optimum
        print(
            f'Case #{case_id}: score={score} optimum={optimum} '
            f'ratio={ratio:.4f} time={elapsed:.4f}s'
        )

    summary_ratio = 1.0 if total_optimum == 0 else total_score / total_optimum
    print()
    print('--- Summary ---')
    print(f'Valid : {config.NUM_CASES}')
    print(f'Total Score   : {total_score}')
    print(f'Total Optimum : {total_optimum}')
    print(f'Overall Ratio : {summary_ratio:.4f}')


if __name__ == '__main__':
    main()
