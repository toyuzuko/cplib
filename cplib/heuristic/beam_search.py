"""Beam search helper library.

This module provides a reusable beam search implementation that keeps only the
best ``beam_width`` candidates at each depth. It is suited to constructive
search problems where a solution is built level by level.

Examples:
    >>> solver = BeamSearch[str](
    ...     expand=lambda s: (s + '0', s + '1'),
    ...     evaluate=lambda s: float(sum(c == t for c, t in zip(s, '101'))),
    ...     beam_width=2,
    ...     state_key=lambda s: s,
    ... )
    >>> result = solver.search(initial_states=[''], max_depth=3)
    >>> result.best_state
    '101'
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from heapq import nlargest, nsmallest
from math import isnan
from typing import Generic
from cplib.tools.type import StateT


@dataclass(frozen=True)
class BeamSearchResult(Generic[StateT]):
    """
    Summary of a beam search run.

    Attributes:
        best_state: Best evaluated state, or best goal at the first depth with
            a goal when a goal predicate is supplied.
        best_score: Score of ``best_state``.
        depth_reached: Maximum fully processed depth, or the depth where a goal was found.
        nodes_expanded: Number of states scored during the search.

    Space Complexity:
        O(1)

    Examples:
        >>> BeamSearchResult(best_state='101', best_score=3.0, depth_reached=3, nodes_expanded=7)
        BeamSearchResult(best_state='101', best_score=3.0, depth_reached=3, nodes_expanded=7)
    """

    best_state: StateT
    best_score: float
    depth_reached: int
    nodes_expanded: int


class BeamSearch(Generic[StateT]):
    """
    Reusable beam search solver.

    The evaluator returns a score for each state. Higher scores are preferred by
    default, but minimization is also supported.

    Space Complexity:
        - ``O(B)`` plus the temporary candidate frontier.

    Examples:
        >>> solver = BeamSearch[int](
        ...     expand=lambda x: (x + 1, x + 2),
        ...     evaluate=lambda x: -abs(10 - x),
        ...     beam_width=3,
        ...     state_key=lambda x: x,
        ... )
        >>> solver.search(initial_states=[0], max_depth=6).best_state
        10
    """

    def __init__(
        self,
        expand: Callable[[StateT], Iterable[StateT]],
        evaluate: Callable[[StateT], float],
        beam_width: int,
        maximize: bool = True,
        state_key: Callable[[StateT], object] | None = None,
    ) -> None:
        """
        Initialize a beam search solver.

        Args:
            expand: Function enumerating independent next states, without
                mutating the input or previously yielded states.
            evaluate: Function returning the score of a state, never NaN.
            beam_width: Number of states kept at each depth.
            maximize: If True, larger scores are preferred.
            state_key: Optional hashable deduplication key within each depth,
                including the initial states. Only the first state for a key
                is evaluated or goal-tested. Keys should identify equivalent
                states (scores, goal status, and future transitions).

        Returns:
            None.

        Raises:
            ValueError: If ``beam_width`` is not positive.

        Time Complexity:
            - ``O(1)``

        Space Complexity:
            - ``O(1)``

        Examples:
            >>> solver = BeamSearch[int](expand=lambda x: (x + 1,), evaluate=float, beam_width=1)
            >>> solver.beam_width
            1
        """
        if beam_width <= 0:
            raise ValueError('beam_width must be positive')
        self.expand = expand
        self.evaluate = evaluate
        self.beam_width = beam_width
        self.maximize = maximize
        self.state_key = state_key

    def _is_better(self, lhs: float, rhs: float) -> bool:
        return lhs > rhs if self.maximize else lhs < rhs

    def _select_frontier(self, candidates: list[tuple[float, StateT]]) -> list[tuple[float, StateT]]:
        """Return the best next frontier in score order."""
        if len(candidates) <= self.beam_width:
            candidates.sort(key=lambda item: item[0], reverse=self.maximize)
            return candidates
        if self.maximize:
            selected = nlargest(self.beam_width, candidates, key=lambda item: item[0])
        else:
            selected = nsmallest(self.beam_width, candidates, key=lambda item: item[0])
        selected.sort(key=lambda item: item[0], reverse=self.maximize)
        return selected

    def search(
        self,
        initial_states: Iterable[StateT],
        max_depth: int,
        is_goal: Callable[[StateT], bool] | None = None,
    ) -> BeamSearchResult[StateT]:
        """Run beam search from one or more initial states.

        Args:
            initial_states: Starting frontier of the search.
            max_depth: Maximum number of expansion steps.
            is_goal: Optional predicate for early stopping.

        Returns:
            Summary of the search, including the best state found. If
            ``is_goal`` is provided and one or more goal states appear, the
            returned state is the best goal among the first depth where goals
            are found, after deduplication but before beam-width pruning.
            Equal scores retain encounter order. Without a goal, the best
            state may come from an earlier depth. States are not copied.

        Raises:
            ValueError: If max_depth is negative, initial_states is empty,
                or evaluate returns NaN.
            TypeError: If a state_key result is not hashable.

        Time Complexity:
            O(G + S log(B + 1)) expected, excluding callback costs, where G
            is the number of generated states including duplicates, S is the
            number evaluated, and B is beam_width. Hashing assumes expected
            constant-time set operations. Add all callback execution costs.

        Space Complexity:
            - ``O(B)`` plus the temporary candidate frontier.

        Examples:
            >>> solver = BeamSearch[str](
            ...     expand=lambda s: (s + 'A', s + 'B'),
            ...     evaluate=lambda s: float(s.count('A')),
            ...     beam_width=2,
            ... )
            >>> solver.search(initial_states=[''], max_depth=3).best_state
            'AAA'
        """
        if max_depth < 0:
            raise ValueError('max_depth must be non-negative')

        beam: list[tuple[float, StateT]] = []
        nodes_expanded = 0
        initial_goal: tuple[float, StateT] | None = None
        state_key = self.state_key
        seen_initial: set[object] | None = set() if state_key is not None else None
        for state in initial_states:
            if seen_initial is not None:
                assert state_key is not None
                key = state_key(state)
                if key in seen_initial:
                    continue
                seen_initial.add(key)
            score = self.evaluate(state)
            if isnan(score):
                raise ValueError('evaluate must not return NaN')
            beam.append((score, state))
            nodes_expanded += 1
            if is_goal is not None and is_goal(state):
                if initial_goal is None or self._is_better(score, initial_goal[0]):
                    initial_goal = (score, state)
        if not beam:
            raise ValueError('initial_states must not be empty')

        beam = self._select_frontier(beam)
        best_score, best_state = beam[0]
        if initial_goal is not None:
            return BeamSearchResult(initial_goal[1], initial_goal[0], 0, nodes_expanded)

        for depth in range(1, max_depth + 1):
            candidates: list[tuple[float, StateT]] = []
            goal_candidate: tuple[float, StateT] | None = None
            seen: set[object] | None = set() if state_key is not None else None
            for _, state in beam:
                for nxt in self.expand(state):
                    if seen is not None:
                        assert state_key is not None
                        key = state_key(nxt)
                        if key in seen:
                            continue
                        seen.add(key)
                    score = self.evaluate(nxt)
                    if isnan(score):
                        raise ValueError('evaluate must not return NaN')
                    candidates.append((score, nxt))
                    nodes_expanded += 1
                    if self._is_better(score, best_score):
                        best_score, best_state = score, nxt
                    if is_goal is not None and is_goal(nxt):
                        if goal_candidate is None or self._is_better(score, goal_candidate[0]):
                            goal_candidate = (score, nxt)

            if not candidates:
                return BeamSearchResult(best_state, best_score, depth - 1, nodes_expanded)
            if goal_candidate is not None:
                return BeamSearchResult(goal_candidate[1], goal_candidate[0], depth, nodes_expanded)

            beam = self._select_frontier(candidates)

        return BeamSearchResult(best_state, best_score, max_depth, nodes_expanded)
