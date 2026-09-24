#!/usr/bin/env python3

from __future__ import annotations

from typing import NamedTuple

from cplib.graph.reachability import strongly_connected_components_raw_csr


class TwoSatResult(NamedTuple):
    """Result of 2-SAT solving.

    Attributes:
        satisfiable: Whether the formula is satisfiable.
        assignment: Boolean variable assignments if satisfiable, otherwise ``None``.

    Space Complexity:
        ``O(n)`` when an assignment is present.
    """
    satisfiable: bool
    assignment: list[bool] | None

    def __bool__(self) -> bool:
        """Return satisfiability for use in boolean contexts."""
        return self.satisfiable

    def __repr__(self) -> str:
        return f'TwoSatResult(satisfiable={self.satisfiable}, assignment={self.assignment})'


class TwoSatSolver:
    """2-SAT solver based on strongly connected components.

    The implication graph has ``2 * n`` vertices, one for each literal.

    Attributes:
        n: Number of boolean variables.

    Space Complexity:
        ``O(n + m)``

    Examples:
        >>> solver = TwoSatSolver(2)
        >>> solver.add_clause(0, True, 1, True)
        >>> solver.add_clause(0, False, 1, True)
        >>> solver.add_clause(0, True, 1, False)
        >>> result = solver.solve()
        >>> result.satisfiable
        True
    """

    def __init__(self, n: int) -> None:
        """Initialize a solver for ``n`` boolean variables.

        Args:
            n: Number of variables ``x_0, ..., x_{n-1}``.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(1)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self._source: list[int] = []
        self._target: list[int] = []

    def add_clause(self, i: int, f: bool, j: int, g: bool) -> None:
        """Add the clause ``(x_i = f) OR (x_j = g)``.

        Args:
            i: Index of the first variable.
            f: Desired truth value of the first literal.
            j: Index of the second variable.
            g: Desired truth value of the second literal.

        Returns:
            ``None``.

        Raises:
            IndexError: If a variable index is outside ``[0, n)``.

        Time Complexity:
            ``O(1)``
        """
        if not (0 <= i < self.n and 0 <= j < self.n):
            raise IndexError('variable index must be within [0, n)')
        self._source.append(2 * i + int(not f))
        self._target.append(2 * j + int(g))
        self._source.append(2 * j + int(not g))
        self._target.append(2 * i + int(f))

    def _build_csr(self) -> tuple[list[int], list[int]]:
        n = 2 * self.n
        degree = [0] * n
        for u in self._source:
            degree[u] += 1
        start = [0] * (n + 1)
        for i in range(n):
            start[i + 1] = start[i] + degree[i]
        to = [0] * len(self._target)
        cursor = start[:]
        for u, v in zip(self._source, self._target):
            p = cursor[u]
            to[p] = v
            cursor[u] += 1
        return start, to

    def solve(self) -> TwoSatResult:
        """Solve the stored 2-SAT instance.

        Returns:
            ``TwoSatResult`` containing satisfiability and one assignment when
            satisfiable.

        Time Complexity:
            ``O(n + m)``
        """
        start, to = self._build_csr()
        _, scc = strongly_connected_components_raw_csr(2 * self.n, start, to)
        assignment = [False] * self.n
        for i in range(self.n):
            if scc[2 * i] == scc[2 * i + 1]:
                return TwoSatResult(False, None)
            assignment[i] = scc[2 * i] < scc[2 * i + 1]
        return TwoSatResult(True, assignment)


Literal = tuple[int, int]  # (variable index, value 0|1)
Clause = list[Literal]


class ThreeSatResult(NamedTuple):
    """Result of 3-SAT solving.

    Attributes:
        satisfiable: Whether the formula is satisfiable.
        assignment: Boolean variable assignments if satisfiable,
            otherwise ``None``.

    Space Complexity:
        ``O(n)`` when an assignment is present.
    """
    satisfiable: bool
    assignment: list[bool] | None

    def __bool__(self) -> bool:
        """Return satisfiability for use in boolean contexts."""
        return self.satisfiable

    def __repr__(self) -> str:
        return f"ThreeSatResult(satisfiable={self.satisfiable}, assignment={self.assignment})"


class CnfSatResult(NamedTuple):
    """Result of general CNF-SAT solving via reduction to 3-SAT.

    Attributes:
        satisfiable: Whether the formula is satisfiable.
        assignment: Boolean assignments for the original variables if
            satisfiable, ``None`` otherwise.

    Space Complexity:
        ``O(n)`` when an assignment is present.
    """
    satisfiable: bool
    assignment: list[bool] | None

    def __bool__(self) -> bool:
        return self.satisfiable

    def __repr__(self) -> str:
        return f"CnfSatResult(satisfiable={self.satisfiable}, assignment={self.assignment})"


class ThreeSatSolver:
    """3-SAT solver using iterative backtracking with propagation.

    Attributes:
        n: Number of boolean variables.
        _clauses: Stored clauses as lists of literals.

    Space Complexity:
        ``O(n + m)``

    Examples:
        >>> solver = ThreeSatSolver(3)
        >>> solver.add_clause(0, True, 1, True, 2, True)
        >>> solver.add_clause(0, False, 1, True, 2, False)
        >>> # (x_0 OR x_1 OR x_2) AND (NOT x_0 OR x_1 OR NOT x_2) is satisfiable.
        >>> bool(solver.solve())
        True
    """

    def __init__(self, n: int) -> None:
        """Initialize a solver for ``n`` boolean variables.

        Args:
            n: Number of variables ``x_0, ..., x_{n-1}``.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(1)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self._clauses: list[Clause] = []

    def add_clause(self, i: int, f: bool, j: int, g: bool, k: int, h: bool) -> None:
        """Add the clause ``(x_i = f) OR (x_j = g) OR (x_k = h)``.

        Args:
            i: Index of the first variable.
            f: Desired truth value of the first literal.
            j: Index of the second variable.
            g: Desired truth value of the second literal.
            k: Index of the third variable.
            h: Desired truth value of the third literal.

        Returns:
            ``None``.

        Raises:
            IndexError: If a variable index is outside ``[0, n)``.

        Time Complexity:
            ``O(1)``
        """
        if not (0 <= i < self.n and 0 <= j < self.n and 0 <= k < self.n):
            raise IndexError('variable index must be within [0, n)')
        self._clauses.append([(i, int(f)), (j, int(g)), (k, int(h))])

    @staticmethod
    def _simplify_clauses(clauses: list[Clause]) -> None:
        """Simplify clauses in-place by removing tautologies and duplicates.

        Args:
            clauses: Clauses to simplify.

        Time Complexity:
            ``O(total_literals log m)`` in the current implementation.
        """
        new_clauses: list[Clause] = []
        for c in clauses:
            lit_dict: dict[int, int] = {}
            tautology = False
            for v, val in c:
                if v in lit_dict:
                    if lit_dict[v] != val:
                        tautology = True
                        break
                else:
                    lit_dict[v] = val
            if not tautology:
                new_clauses.append([(v, lit_dict[v]) for v in lit_dict])
        unique = [list(c) for c in set(tuple(sorted(c)) for c in new_clauses)]
        clauses[:] = unique

    def solve(self) -> ThreeSatResult:
        """Solve the stored 3-SAT instance.

        Returns:
            ``ThreeSatResult`` containing satisfiability and one assignment when
            satisfiable.

        Time Complexity:
            Worst case ``O(m * 2^n)``.
        """
        clauses: list[Clause] = [c[:] for c in self._clauses]
        self._simplify_clauses(clauses)

        m = len(clauses)
        if m == 0:
            return ThreeSatResult(True, [False] * self.n)

        assign: list[int] = [-1] * self.n  # -1 = unassigned
        stack: list[tuple[int, list[Literal], int, list[tuple[int, int]]]] = []

        k = 0

        while True:
            if k == m:
                # Unassigned variables can be set to False.
                return ThreeSatResult(True, [value == 1 for value in assign])
            clause = clauses[k]
            satisfied = False
            rem: list[Literal] = []
            for var, val in clause:
                cur = assign[var]
                if cur == val:
                    satisfied = True
                    break
                if cur == -1:
                    rem.append((var, val))

            if satisfied:
                stack.append((k, [], 0, []))
                k += 1
                continue

            if not rem:
                while stack:
                    prev_k, prev_rem, choice, changes = stack.pop()
                    for v, old in reversed(changes):
                        assign[v] = old
                    if prev_rem and choice + 1 < len(prev_rem):
                        next_choice = choice + 1
                        changes = ThreeSatSolver._apply_branch(assign, prev_rem, next_choice)
                        assert changes is not None
                        stack.append((prev_k, prev_rem, next_choice, changes))
                        k = prev_k + 1
                        break
                else:
                    return ThreeSatResult(False, None)
                continue

            changes = self._apply_branch(assign, rem, 0)
            if changes is None:
                while stack:
                    prev_k, prev_rem, choice, prev_changes = stack.pop()
                    for v, old in reversed(prev_changes):
                        assign[v] = old
                    if prev_rem and choice + 1 < len(prev_rem):
                        next_choice = choice + 1
                        changes = ThreeSatSolver._apply_branch(assign, prev_rem, next_choice)
                        if changes is None:
                            continue
                        stack.append((prev_k, prev_rem, next_choice, changes))
                        k = prev_k + 1
                        break
                else:
                    return ThreeSatResult(False, None)
                continue
            stack.append((k, rem, 0, changes))
            k += 1

    @staticmethod
    def _apply_branch(assign: list[int], rem: list[Literal], choice_idx: int) -> list[tuple[int, int]] | None:
        """Apply one branch choice and return the rollback log.

        Args:
            assign: Current assignment array using ``-1`` for unassigned.
            rem: Remaining unassigned literals in the current clause.
            choice_idx: Literal index in ``rem`` chosen to satisfy.

        Returns:
            Rollback log as ``(variable_index, old_value)`` pairs, or ``None``
            when the branch immediately conflicts.
        """
        changes: list[tuple[int, int]] = []
        for j in range(choice_idx):
            var, val = rem[j]
            target = 1 - val
            if assign[var] == val:
                for changed_var, old in reversed(changes):
                    assign[changed_var] = old
                return None
            if assign[var] != target:
                changes.append((var, assign[var]))
                assign[var] = target
        var_c, val_c = rem[choice_idx]
        if assign[var_c] == 1 - val_c:
            for changed_var, old in reversed(changes):
                assign[changed_var] = old
            return None
        if assign[var_c] != val_c:
            changes.append((var_c, assign[var_c]))
            assign[var_c] = val_c
        return changes


class CnfSatSolver:
    """General CNF-SAT solver via Tseitin-style reduction to 3-SAT.

    The formula is given in conjunctive normal form, where each clause may have
    any number of literals. The solver reduces the instance to an equivalent
    3-SAT formula and then calls :class:`ThreeSatSolver`.

    Literals are represented as ``(variable_index, bool_value)`` and mean
    ``x_i = bool_value``.

    Attributes:
        n: Number of original boolean variables.
        _clauses: Stored CNF clauses.

    Space Complexity:
        ``O(n + L)``, where ``L`` is the total number of stored literals.

    Examples:
        >>> solver = CnfSatSolver(3)
        >>> solver.add_clause([(0, True), (1, False), (2, True), (1, True)])
        >>> solver.add_clause([(0, False), (1, True), (2, False)])
        >>> # (x_0 OR NOT x_1 OR x_2 OR x_1) AND (NOT x_0 OR x_1 OR NOT x_2) is satisfiable.
        >>> bool(solver.solve())
        True
    """

    def __init__(self, n: int) -> None:
        """Initialize a CNF-SAT solver.

        Args:
            n: Number of original boolean variables.

        Returns:
            None.

        Raises:
            ValueError: If ``n`` is negative.

        Time Complexity:
            O(1)
        """
        if n < 0:
            raise ValueError('n must be non-negative')
        self.n = n
        self._clauses: list[Clause] = []

    def add_clause(self, literals: list[tuple[int, bool]]) -> None:
        """Add one CNF clause.

        Args:
            literals: Clause literals written as ``(variable_index, bool_value)``.

        Returns:
            ``None``.

        Raises:
            IndexError: If a variable index is outside ``[0, n)``.

        Time Complexity:
            ``O(k)`` where ``k`` is the clause length.
        """
        if any(not 0 <= var < self.n for var, _ in literals):
            raise IndexError('variable index must be within [0, n)')
        self._clauses.append([(var, int(value)) for var, value in literals])

    def solve(self) -> CnfSatResult:
        """Solve the CNF-SAT instance.

        Returns:
            ``CnfSatResult`` for the original variables.

        Time Complexity:
            Reduction time plus the complexity of the resulting
            :class:`ThreeSatSolver` instance.
        """
        reduced_clauses: list[Clause] = []
        next_var = self.n

        for clause in self._clauses:
            normalized = list(dict.fromkeys(clause))
            seen: dict[int, int] = {}
            tautology = False
            for var, val in normalized:
                if var in seen and seen[var] != val:
                    tautology = True
                    break
                seen[var] = val
            if tautology:
                continue
            normalized = [(var, seen[var]) for var in seen]
            length = len(normalized)
            if length == 0:
                return CnfSatResult(False, None)
            if length == 1:
                lit = normalized[0]
                reduced_clauses.append([lit, lit, lit])
            elif length == 2:
                lit1, lit2 = normalized
                reduced_clauses.append([lit1, lit2, lit2])
            elif length == 3:
                reduced_clauses.append(normalized)
            else:
                aux = next_var
                next_var += 1
                reduced_clauses.append([normalized[0], normalized[1], (aux, 1)])
                for i in range(2, length - 2):
                    new_aux = next_var
                    next_var += 1
                    reduced_clauses.append([(aux, 0), normalized[i], (new_aux, 1)])
                    aux = new_aux
                reduced_clauses.append([(aux, 0), normalized[-2], normalized[-1]])

        solver = ThreeSatSolver(next_var)
        for clause in reduced_clauses:
            (i, f), (j, g), (k, h) = clause
            solver.add_clause(i, bool(f), j, bool(g), k, bool(h))
        result = solver.solve()
        if not result.satisfiable:
            return CnfSatResult(False, None)
        assert result.assignment is not None
        return CnfSatResult(True, result.assignment[:self.n])
