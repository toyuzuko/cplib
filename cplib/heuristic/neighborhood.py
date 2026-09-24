"""Thin abstractions for reversible local-search moves.

This module provides a small protocol for moves that can be applied to a
mutable state, reverted later, and report their score delta. It is intended for
contest code that keeps a current solution and explores its neighborhood with
minimal wrapper overhead.

Examples:
    >>> from dataclasses import dataclass
    >>> @dataclass(slots=True)
    ... class Flip:
    ...     index: int
    ...     delta: float
    ...     def apply(self, state: list[int]) -> None:
    ...         state[self.index] ^= 1
    ...     def revert(self, state: list[int]) -> None:
    ...         state[self.index] ^= 1
    ...     def score_delta(self) -> float:
    ...         return self.delta
    >>> neighborhood = Neighborhood([0, 1, 0], 1.5)
    >>> move = Flip(1, 0.5)
    >>> neighborhood.apply(move)
    2.0
    >>> neighborhood.revert(move)
    1.5
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, runtime_checkable

from cplib.tools.type import StateT, StateT_contra


@runtime_checkable
class Move(Protocol[StateT_contra]):
    """
    Protocol for a reversible local-search move.

    A move must be able to mutate the current state, undo the same mutation, and
    report the score delta caused by applying it. The score delta is expected to
    be the amount added to the current score when the move is applied, and the
    same value is subtracted when the move is reverted.
    Neighborhood reads score_delta after apply and after revert, so both
    calls must report that same delta. Revert must undo the matching apply;
    when moves overlap, undo them in reverse order.

    Space Complexity:
        Depends on the concrete move implementation.
    """

    def apply(self, state: StateT_contra) -> None:
        """
        Apply the move to ``state``.

        Args:
            state: Mutable state operated on by the move or search.

        Returns:
            None; state is modified in place.

        Time Complexity:
            Depends on the concrete move implementation.
        Space Complexity:
            Depends on the concrete move implementation.
        """
        ...

    def revert(self, state: StateT_contra) -> None:
        """
        Undo the move from ``state``.

        Args:
            state: Mutable state operated on by the move or search.

        Returns:
            None; state is restored in place.

        Time Complexity:
            Depends on the concrete move implementation.
        Space Complexity:
            Depends on the concrete move implementation.
        """
        ...

    def score_delta(self) -> float:
        """
        Return the score delta of applying the move.

        Returns:
            The same signed score change after applying or reverting the move.

        Time Complexity:
            Depends on the concrete move implementation.
        Space Complexity:
            Depends on the concrete move implementation.
        """
        ...


@dataclass(slots=True)
class Neighborhood(Generic[StateT]):
    """
    Pair a mutable state with its current score.

    The class is intentionally small: it only stores the current state and the
    current score, then updates both using a ``Move`` instance.

    Attributes:
        state: Mutable solution state.
        score: Current score of the solution.

    Space Complexity:
        - ``O(1)``
    """

    state: StateT
    score: float

    def apply(self, move: Move[StateT]) -> float:
        """
        Apply ``move`` and update the cached score.

        Args:
            move: Reversible move to apply.

        Returns:
            Updated score after the move.

        Time Complexity:
            - ``O(cost(move))``

        Space Complexity:
            O(1) auxiliary space besides storage used by move callbacks.
        """

        move.apply(self.state)
        self.score += move.score_delta()
        return self.score

    def revert(self, move: Move[StateT]) -> float:
        """
        Revert ``move`` and update the cached score.

        Args:
            move: Reversible move to undo.

        Returns:
            Updated score after reverting the move.

        Time Complexity:
            - ``O(cost(move))``

        Space Complexity:
            O(1) auxiliary space besides storage used by move callbacks.
        """

        move.revert(self.state)
        self.score -= move.score_delta()
        return self.score


__all__ = ["Move", "Neighborhood"]
