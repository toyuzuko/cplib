"""Simulated annealing helper library.

This module provides a small reusable framework for simulated annealing.
Users define:

- a state type
- an evaluation function
- a neighbor generator
- a temperature schedule

Examples:
    >>> import random
    >>> from cplib.heuristic.simulated_annealing import (
    ...     AnnealingSchedule,
    ...     SimulatedAnnealing,
    ... )
    >>> solver = SimulatedAnnealing[int](
    ...     evaluate=lambda x: -float((x - 7) ** 2),
    ...     generate_neighbor=lambda x, rng: min(10, max(0, x + rng.choice((-1, 1)))),
    ...     schedule=AnnealingSchedule(start_temp=5.0, end_temp=0.1),
    ...     rng=random.Random(0),
    ... )
    >>> result = solver.run(initial_state=0, iterations=200)
    >>> result.best_state
    7
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from sys import float_info
from typing import Generic

from cplib.heuristic.random import SplitMix64, XorShift
from cplib.tools.type import StateT

AnnealingRng = random.Random | SplitMix64 | XorShift


@dataclass(frozen=True)
class AnnealingSchedule:
    """
    Cooling schedule for simulated annealing.

    Uses exponential interpolation between the start and end temperatures.

    Attributes:
        start_temp: Temperature used at iteration 0.
        end_temp: Temperature used at the final iteration.

    Examples:
        >>> schedule = AnnealingSchedule(start_temp=10.0, end_temp=0.1)
        >>> round(schedule.temperature(0.0), 1)
        10.0
        >>> round(schedule.temperature(1.0), 1)
        0.1

    Raises:
        ValueError: If either temperature is non-positive or non-finite.

    Space Complexity:
        O(1)
    """

    start_temp: float
    end_temp: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.start_temp) and math.isfinite(self.end_temp)) or self.start_temp <= 0.0 or self.end_temp <= 0.0:
            raise ValueError('temperatures must be finite and positive')

    def temperature(self, progress: float) -> float:
        """
        Return the temperature at a normalized progress value in [0, 1].

        Args:
            progress: Search progress. Values outside [0, 1] are clamped.

        Returns:
            Finite positive temperature at the specified progress. The
            endpoints return the configured temperatures exactly.

        Raises:
            ValueError: If progress is NaN. Infinities are clamped.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``
        """
        if math.isnan(progress):
            raise ValueError('progress must not be NaN')
        if progress <= 0.0 or self.start_temp == self.end_temp:
            return self.start_temp
        if progress >= 1.0:
            return self.end_temp
        if self.start_temp > self.end_temp:
            upper, lower, exponent = self.start_temp, self.end_temp, progress
        else:
            upper, lower, exponent = self.end_temp, self.start_temp, 1.0 - progress
        ratio = lower / upper
        if ratio >= float_info.min:
            # Scale down the larger endpoint so intermediate rounding cannot
            # overflow even when it is the largest representable float.
            return max(lower, upper * (ratio ** exponent))
        # A ratio may underflow or lose precision before interpolation even
        # though both temperatures and every interpolated value are finite.
        temperature = math.exp((1.0 - progress) * math.log(self.start_temp) + progress * math.log(self.end_temp))
        return min(max(temperature, lower), upper)


@dataclass(frozen=True)
class AnnealingResult(Generic[StateT]):
    """
    Result of a simulated annealing run.

    Attributes:
        best_state: Best state found during the run.
        best_score: Score of ``best_state``.
        current_state: State at the end of the run.
        current_score: Score of ``current_state``.
        accepted_moves: Number of accepted neighbor transitions.
        iterations: Number of attempted transitions.

    The best state and the final state may differ because the annealer can
    accept worsening moves temporarily.

    Space Complexity:
        O(1)
    """

    best_state: StateT
    best_score: float
    current_state: StateT
    current_score: float
    accepted_moves: int
    iterations: int


class SimulatedAnnealing(Generic[StateT]):
    """
    Reusable simulated annealing solver.

    The solver keeps only the current state and best state, so it can be used with
    arbitrary immutable or mutable state objects. Without copy_state, the
    neighbor generator must return an independent candidate without modifying
    its input or previously returned states. With copy_state, it may mutate
    the provided copy in place.

    Args:
        evaluate: Function returning a finite score of a state.
        generate_neighbor: Function generating a neighboring state.
        schedule: Temperature schedule used during the run.
        maximize: If True, larger scores are better. If False, smaller scores are better.
        rng: Optional random.Random, SplitMix64, or XorShift instance.
        copy_state: Optional copier used when states are mutable. If provided,
            it must return an independent copy of all data mutated by the
            neighbor generator. It isolates initial, candidate, and best states.

    Raises:
        ValueError: Raised by ``AnnealingSchedule`` if its temperatures are not
            finite and positive.

    Space Complexity:
        - ``O(size of state)`` besides any storage used by user callbacks.

    Examples:
        >>> import random
        >>> solver = SimulatedAnnealing[int](
        ...     evaluate=lambda x: -float((x - 3) ** 2),
        ...     generate_neighbor=lambda x, rng: max(0, min(6, x + rng.choice((-1, 1)))),
        ...     schedule=AnnealingSchedule(start_temp=3.0, end_temp=0.1),
        ...     rng=random.Random(1),
        ... )
        >>> result = solver.run(initial_state=0, iterations=100)
        >>> result.best_state
        3
    """

    def __init__(
        self,
        evaluate: Callable[[StateT], float],
        generate_neighbor: Callable[[StateT, AnnealingRng], StateT],
        schedule: AnnealingSchedule,
        maximize: bool = True,
        rng: AnnealingRng | None = None,
        copy_state: Callable[[StateT], StateT] | None = None,
    ) -> None:
        """Configure the solver without running a search.

        Args:
            evaluate: Function returning a finite score for a state.
            generate_neighbor: Candidate generator receiving the current state
                (or its copy) and the selected RNG. See the class's copying contract.
            schedule: Positive finite temperature schedule.
            maximize: Whether larger scores are preferred.
            rng: Random generator; defaults to a new random.Random instance.
            copy_state: Optional independent state copier for mutable states.

        Returns:
            None.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1), excluding referenced callback and RNG objects.
        """
        self.evaluate = evaluate
        self.generate_neighbor = generate_neighbor
        self.schedule = schedule
        self.maximize = maximize
        self.rng = random.Random() if rng is None else rng
        self.copy_state = copy_state

    def _snapshot(self, state: StateT) -> StateT:
        copier = self.copy_state
        return state if copier is None else copier(state)

    def run(self, initial_state: StateT, iterations: int) -> AnnealingResult[StateT]:
        """Run simulated annealing from an initial state.

        Args:
            initial_state: Starting solution.
            iterations: Number of neighbor transitions to examine.

        Returns:
            Summary of the search, including the best state found.

        Raises:
            ValueError: If ``iterations`` is not positive or evaluate returns
                a non-finite score.

        Time Complexity:
            - ``O(iterations * (C_eval + C_neighbor + C_copy))``, where
              ``C_eval`` is the cost of ``evaluate``, ``C_neighbor`` is the
              cost of ``generate_neighbor``, and ``C_copy`` is the cost of
              ``copy_state`` when provided.

        Space Complexity:
            - ``O(size of state)`` besides user-managed callback state.

        Examples:
            >>> import random
            >>> solver = SimulatedAnnealing[int](
            ...     evaluate=lambda x: -float((x - 2) ** 2),
            ...     generate_neighbor=lambda x, rng: max(0, min(4, x + rng.choice((-1, 1)))),
            ...     schedule=AnnealingSchedule(start_temp=2.0, end_temp=0.1),
            ...     rng=random.Random(0),
            ... )
            >>> solver.run(initial_state=0, iterations=80).best_state
            2
        """
        if iterations <= 0:
            raise ValueError('iterations must be positive')

        current_state = self._snapshot(initial_state)
        current_score = self.evaluate(current_state)
        if not math.isfinite(current_score):
            raise ValueError('evaluate must return finite scores')
        best_state = self._snapshot(current_state)
        best_score = current_score
        accepted_moves = 0

        for step in range(iterations):
            progress = step / max(1, iterations - 1)
            temperature = self.schedule.temperature(progress)
            candidate_state = self.generate_neighbor(self._snapshot(current_state), self.rng)
            candidate_score = self.evaluate(candidate_state)
            if not math.isfinite(candidate_score):
                raise ValueError('evaluate must return finite scores')
            delta = candidate_score - current_score if self.maximize else current_score - candidate_score

            accept = False
            if delta >= 0.0:
                accept = True
            else:
                if delta == -math.inf:
                    scaled_delta = candidate_score / temperature - current_score / temperature if self.maximize else current_score / temperature - candidate_score / temperature
                else:
                    scaled_delta = delta / temperature
                probability = math.exp(scaled_delta)
                accept = self.rng.random() < probability

            if accept:
                current_state = candidate_state
                current_score = candidate_score
                accepted_moves += 1
                if (current_score > best_score if self.maximize else current_score < best_score):
                    best_state = self._snapshot(current_state)
                    best_score = current_score

        return AnnealingResult(
            best_state=best_state,
            best_score=best_score,
            current_state=current_state,
            current_score=current_score,
            accepted_moves=accepted_moves,
            iterations=iterations,
        )


__all__ = ['AnnealingRng', 'AnnealingResult', 'AnnealingSchedule', 'SimulatedAnnealing']
