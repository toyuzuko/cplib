from __future__ import annotations

import random
import sys
import time

import config
from main import solve_case
from scenario import generate_case
from score import total_weight, validate_and_score


def main() -> None:
    rng = random.Random(0)
    total_score_value = 0
    total_weight_value = 0

    for case_id in range(config.NUM_CASES):
        case = generate_case(rng)
        case_start = time.perf_counter()
        solution = solve_case(case)
        elapsed = time.perf_counter() - case_start
        if elapsed > config.TIMEOUT_SECONDS:
            print(f'Case #{case_id}: TLE ({elapsed:.4f}s)', file=sys.stderr)
            raise SystemExit(1)
        score = validate_and_score(case, solution)
        weight_sum = total_weight(case)
        total_score_value += score
        total_weight_value += weight_sum
        ratio = 1.0 if weight_sum == 0 else score / weight_sum
        print(
            f'Case #{case_id}: score={score} total_weight={weight_sum} '
            f'ratio={ratio:.4f} time={elapsed:.4f}s'
        )

    summary_ratio = 1.0 if total_weight_value == 0 else total_score_value / total_weight_value
    print()
    print('--- Summary ---')
    print(f'Valid : {config.NUM_CASES}')
    print(f'Total Score  : {total_score_value}')
    print(f'Total Weight : {total_weight_value}')
    print(f'Overall Ratio: {summary_ratio:.4f}')


if __name__ == '__main__':
    main()
