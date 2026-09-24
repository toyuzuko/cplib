from __future__ import annotations

from scenario import Case


def validate_and_score(case: Case, solution: list[int]) -> int:
    if len(solution) != case.length:
        raise ValueError('solution length does not match N')
    if any(color < 0 or color >= case.color_count for color in solution):
        raise ValueError('solution contains an out-of-range color')

    score = 0
    for index, color in enumerate(solution):
        score += case.position_scores[index][color]
        if index > 0:
            score += case.transition_scores[solution[index - 1]][color]
    return score


def optimal_score(case: Case) -> int:
    color_count = case.color_count
    dp = [case.position_scores[0][color] for color in range(color_count)]
    for index in range(1, case.length):
        next_dp = [0] * color_count
        for color in range(color_count):
            best_prev = 0
            for previous in range(color_count):
                best_prev = max(best_prev, dp[previous] + case.transition_scores[previous][color])
            next_dp[color] = best_prev + case.position_scores[index][color]
        dp = next_dp
    return max(dp)
