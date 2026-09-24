#!/usr/bin/env python3

from __future__ import annotations

from cplib.datastructure.treap import Treap


class IntervalSet:
    """
    Disjoint interval set with add/remove and point queries.

    Maintains a set of disjoint half-open intervals [l, r) over integers.
    Intervals are merged on insertion, and deletions may split intervals.

    Attributes:
        covered: Total covered length.

    Examples:
        >>> s = IntervalSet()
        >>> s.add(2, 5)
        >>> s.add(7, 9)
        >>> s.contains(3)
        True
        >>> s.remove(3, 8)
        >>> s.get(0)
        (2, 3)
        >>> s.mex(2)
        3

    Space Complexity:
        O(m), where m is the maximum number of stored intervals so far.
        The backing Treap reuses deleted nodes; the endpoint map stores only
        the currently active intervals.
    """
    INF: int = 1 << 60

    def __init__(self) -> None:
        """
        Initialize an empty interval set.

        Returns:
            None.

        Time Complexity:
            O(1)
        """
        self.tr = Treap[int]()
        self.R: dict[int, int] = {}
        self.covered = 0

    def __len__(self) -> int:
        """
        Return the number of stored intervals.

        Returns:
            Number of stored disjoint intervals.

        Time Complexity:
            O(1)
        """
        return self.tr.size()

    def covered_count(self) -> int:
        """
        Return the total length covered by all intervals.

        Returns:
            Total covered length.

        Time Complexity:
            O(1)
        """
        return self.covered

    def get(self, i: int) -> tuple[int, int] | None:
        """
        Return the i-th interval in sorted order.

        Args:
            i: 0-based index of the interval

        Returns:
            ``(l, r)`` if the interval exists, otherwise ``None``.

        Time Complexity:
            Expected O(log(n + 1)), where n is the number of active intervals.
        """
        if not (0 <= i < self.tr.size()):
            return None
        l = self.tr.get(i)
        return (l, self.R[l])

    def find_point(self, p: int) -> int:
        """
        Return the index of the interval containing p, or -1.

        Args:
            p: Query point

        Returns:
            Index in sorted order if ``p`` is covered, otherwise ``-1``.

        Time Complexity:
            Expected O(log(n + 1)), where n is the number of active intervals.
        """
        if self.tr.size() == 0:
            return -1
        idx = self.tr.bisect_right(p)
        if idx == 0:
            return -1
        l = self.tr.get(idx - 1)
        r = self.R[l]
        return (idx - 1) if (l <= p < r) else -1

    def contains(self, p: int) -> bool:
        """
        Check whether p is covered by any interval.

        Args:
            p: Integer point to query.

        Returns:
            Whether ``p`` belongs to some stored interval.

        Time Complexity:
            Expected O(log(n + 1)), where n is the number of active intervals.
        """
        return self.find_point(p) != -1

    def add(self, l: int, r: int) -> None:
        """
        Add interval [l, r), merging overlaps and touching endpoints.

        Time Complexity:
            Expected O((k + 1) log(n + 1)), where k intervals are affected.
            Expected amortized O(log(n + 1)) across additions and removals,
            where n is the maximum number of active intervals in the sequence.

        Args:
            l: Left endpoint, inclusive.
            r: Right endpoint, exclusive. If l >= r, do nothing.

        Returns:
            None.

        """
        if l >= r:
            return
        idx = self.tr.bisect_left(l)
        if idx > 0:
            pl = self.tr.get(idx - 1)
            pr = self.R[pl]
            if pr >= l:
                if pl < l:
                    l = pl
                if pr > r:
                    r = pr
                self.covered -= pr - pl
                self.tr.discard(pl, validity_check=False)
                del self.R[pl]
                idx -= 1
        while idx < self.tr.size():
            cl = self.tr.get(idx)
            if cl > r:
                break
            cr = self.R.pop(cl)
            if cr > r:
                r = cr
            self.covered -= cr - cl
            self.tr.discard(cl, validity_check=False)
        self.tr.add(l, validity_check=True)
        self.R[l] = r
        self.covered += r - l

    def remove(self, l: int, r: int) -> None:
        """
        Remove interval [l, r), splitting overlaps if needed.

        Time Complexity:
            Expected O((k + 1) log(n + 1)), where k intervals are affected.
            Expected amortized O(log(n + 1)) across additions and removals,
            where n is the maximum number of active intervals in the sequence.

        Args:
            l: Left endpoint, inclusive.
            r: Right endpoint, exclusive. If l >= r, do nothing.

        Returns:
            None.
        """
        if l >= r:
            return
        idx = self.tr.bisect_left(l)
        if idx > 0:
            pl = self.tr.get(idx - 1)
            if self.R[pl] > l:
                idx -= 1
        to_add: list[tuple[int, int]] = []
        while idx < self.tr.size():
            cl = self.tr.get(idx)
            if cl >= r:
                break
            cr = self.R[cl]
            if cr <= l:
                idx += 1
                continue
            self.covered -= cr - cl
            self.tr.discard(cl, validity_check=False)
            del self.R[cl]
            if cl < l:
                to_add.append((cl, min(cr, l)))
            if cr > r:
                to_add.append((max(cl, r), cr))
        for a, b in to_add:
            if a < b:
                self.tr.add(a, validity_check=True)
                self.R[a] = b
                self.covered += b - a

    def is_disjoint(self, l: int, r: int) -> bool:
        """
        Check if [l, r) is disjoint from all stored intervals.

        Args:
            l: Inclusive left boundary of a range.
            r: Exclusive right boundary of a range.

        Returns:
            ``True`` if the range is disjoint from every stored interval.

        Time Complexity:
            Expected O(log(n + 1)), where n is the number of active intervals.
        """
        if l >= r:
            return True
        idx = self.tr.bisect_left(l)
        if idx < self.tr.size():
            nl = self.tr.get(idx)
            if nl < r:
                return False
        if idx > 0:
            pl = self.tr.get(idx - 1)
            if self.R[pl] > l:
                return False
        return True

    def mex(self, p: int) -> int:
        """
        Return the minimum x >= p that is not covered.

        Args:
            p: Integer point to query.

        Returns:
            The smallest integer ``x >= p`` not covered by the set.

        Time Complexity:
            Expected O(log(n + 1)), where n is the number of active intervals.
        """
        if self.tr.size() == 0:
            return p
        idx = self.tr.bisect_right(p)
        if idx == 0:
            return p
        l = self.tr.get(idx - 1)
        r = self.R[l]
        if r <= p:
            return p
        p = r
        idx = self.tr.bisect_right(p)
        if idx == 0:
            return p
        l = self.tr.get(idx - 1)
        r = self.R[l]
        if r <= p:
            return p
        return r
