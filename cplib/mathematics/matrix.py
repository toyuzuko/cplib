#!/usr/bin/env python3

from __future__ import annotations # for Library Checker

from collections.abc import Sequence
from typing import NamedTuple, TypeVar
from random import SystemRandom

from cplib.mathematics.factorization import PrimeFactor
from cplib.mathematics.recurrence import berlekamp_massey
from cplib.mathematics.polynomial import (
    FormalPowerSeriesMod,
    polynomial_roots,
)

_MatrixModT = TypeVar('_MatrixModT', bound='MatrixMod')


class LinearEquationResult(NamedTuple):
    """
    Solution description for a linear system.

    Attributes:
        dimension: Dimension of the affine solution space.
        particular_solution: One concrete solution when the system is
            consistent.
        basis_vectors: Basis of the homogeneous solution space.

    Any solution can be written as ``particular_solution`` plus a linear
    combination of ``basis_vectors``.
    When no solution exists, callers should rely on the enclosing API contract.

    Space Complexity:
        ``O(nm)`` for the stored solution vectors.
    """
    dimension: int
    particular_solution: list[int]
    basis_vectors: list[list[int]]


class DiagonalizationResult(NamedTuple):
    """
    Diagonalization over the current modular field.

    Attributes:
        eigenvalues: Eigenvalues in the same order as the columns of
            ``transform`` and the diagonal entries of ``diagonal``.
        transform: Matrix whose columns are eigenvectors.
        diagonal: Diagonal matrix satisfying ``transform^-1 A transform = diagonal``.

    Space Complexity:
        ``O(n^2)``
    """
    eigenvalues: list[int]
    transform: 'LinearAlgebraFp'
    diagonal: 'LinearAlgebraFp'


class FrobeniusCyclicForm(NamedTuple):
    """
    One-block Frobenius normal form of a cyclic matrix.

    Attributes:
        characteristic_polynomial: Monic characteristic polynomial in
            ascending-degree order.
        transform: Krylov basis matrix ``P``.
        companion: Companion matrix ``C`` satisfying ``A P = P C``.

    Space Complexity:
        ``O(n^2)``
    """
    characteristic_polynomial: list[int]
    transform: 'LinearAlgebraFp'
    companion: 'LinearAlgebraFp'


class FrobeniusForm(NamedTuple):
    """
    Frobenius form represented by companion blocks.

    Attributes:
        polynomials: Monic invariant factors in ascending-degree order. The
            non-constant factors divide the following factors.
        transform: Change-of-basis matrix ``P``.
        frobenius: Block diagonal companion matrix ``F`` satisfying
            ``A P = P F``.

    Space Complexity:
        ``O(n^2)``
    """
    polynomials: list[list[int]]
    transform: 'LinearAlgebraFp'
    frobenius: 'LinearAlgebraFp'


class KrylovBlockForm(NamedTuple):
    """
    Krylov block decomposition of a matrix.

    Attributes:
        transform: Change-of-basis matrix ``P``.
        action: Matrix ``T`` satisfying ``A P = P T``.
        block_ranges: Half-open index ranges for generated Krylov blocks.

    Space Complexity:
        ``O(n^2)``
    """
    transform: 'LinearAlgebraFp'
    action: 'LinearAlgebraFp'
    block_ranges: list[tuple[int, int]]


class MatrixMod:
    """
    Matrix class with modular arithmetic.

    Supports various matrix operations with all arithmetic performed modulo a specified value.
    Optimized for prime moduli but supports non-prime moduli for some operations.

    Attributes:
        _mod: Modulus for arithmetic operations.
        _is_prime: Whether the modulus is prime.
        _n: Number of rows.
        _m: Number of columns.
        _matrix: Dense matrix entries.

    Examples:
        >>> MatrixMod.set_mod(1000000007)
        >>> A = MatrixMod(2, 2, [[1, 2], [3, 4]])
        >>> B = MatrixMod(2, 2, [[5, 6], [7, 8]])
        >>> C = A * B
        >>> print(C)  # Matrix multiplication mod 1000000007
        19 22
        43 50

        >>> # Matrix power
        >>> I = MatrixMod.identity(3)  # 3x3 identity matrix
        >>> M = MatrixMod(3, 3, [[1, 1, 0], [1, 0, 1], [0, 1, 1]])
        >>> print(M ** 10)  # M^10 mod 1000000007
        342 341 341
        341 342 341
        341 341 342

    Notes:
        The modulus is shared by instances of the class; changing it affects
        subsequent arithmetic on existing matrices. Input entries and direct
        assignments are stored without normalization. Arithmetic and elimination
        interpret them modulo the current modulus.

    Space Complexity:
        ``O(nm)``

    Complexity Notation:
        ``n`` is the number of rows, ``m`` is the number of columns, and
        ``p`` is the shared dimension in matrix multiplication.
    """
    _mod = 998244353
    _is_prime = True

    def __init__(self, n: int, m: int, from_array: list[list[int]] | None = None) -> None:
        """Initialize n×m matrix.

        Args:
            n: Number of rows
            m: Number of columns
            from_array: Optional n by m array; copied without reducing entries.

        Returns:
            None.

        Raises:
            ValueError: If either dimension is negative or the array shape differs.

        Time Complexity:
            O(nm)
        """
        if n < 0 or m < 0:
            raise ValueError('matrix dimensions must be non-negative')
        self._n = n
        self._m = m
        if from_array is None:
            self._matrix = [[0] * m for _ in range(n)]
        else:
            if len(from_array) != n or any(len(row) != m for row in from_array):
                raise ValueError(f"Incompatible dimensions. Given 2Darray is not (n = {n}) * (m = {m}).")
            self._matrix = [row[:] for row in from_array]

    @classmethod
    def set_mod(cls, mod: int, primality_check: bool = True) -> None:
        """Set the modulus shared by instances of this class.

        Args:
            mod: Positive modulus, including 1 and composite values.
            primality_check: Whether to test primality. If False and mod > 1,
                the caller guarantees primality and field operations assume it.

        Returns:
            None. Existing entries are not rewritten.

        Raises:
            ValueError: If mod is not positive; the previous setting is preserved.

        Notes:
            Field operations require a prime modulus. The primality test is
            deterministic below 2**64 and probabilistic for larger values.

        Time Complexity:
            Cost of PrimeFactor.is_prime when checking, otherwise O(1).
            The prime helper may initialize its sieve on first use.
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        is_prime = mod > 1 and (not primality_check or PrimeFactor.is_prime(mod))
        cls._mod = mod
        cls._is_prime = is_prime

    def get_mod(self) -> int:
        """
        Return the current modulus.

        Returns:
            The modulus shared by instances of this class.

        Time Complexity:
            O(1)
        """
        return self._mod

    @classmethod
    def identity(cls: type[_MatrixModT], n: int) -> _MatrixModT:
        """
        Create n×n identity matrix.

        Args:
            n: Size of identity matrix

        Returns:
            n×n identity matrix

        Time Complexity:
            ``O(n^2)``
        """
        ret = cls(n, n)
        for i in range(n):
            ret[i, i] = 1 % cls._mod
        return ret

    def is_square(self) -> bool:
        """
        Return whether the matrix is square.

        Returns:
            True if the row and column counts are equal, including 0 by 0.

        Time Complexity:
            O(1)
        """
        return self._n == self._m

    def __str__(self) -> str:
        """Return the matrix as newline-separated rows."""
        return "\n".join(" ".join(map(str, row)) for row in self._matrix)

    def __getitem__(self, idxs: tuple[int, int]) -> int:
        """
        Get matrix element at given indices.

        Args:
            idxs: Tuple of (row, column) indices

        Returns:
            int: Matrix element at position [row][column]
        """
        return self._matrix[idxs[0]][idxs[1]]

    def __setitem__(self, idxs: tuple[int, int], value: int) -> None:
        """
        Set matrix element at given indices.

        Args:
            idxs: Tuple of (row, column) indices
            value: Value to set at position [row][column]
        """
        self._matrix[idxs[0]][idxs[1]] = value

    def __add__(self: _MatrixModT, other: 'MatrixMod') -> _MatrixModT:
        if self._n != other._n or self._m != other._m:
            raise ValueError('incompatible dimensions')
        ret = type(self)(self._n, self._m)
        for i in range(self._n):
            res_i = ret._matrix[i]
            self_i = self._matrix[i]
            other_i = other._matrix[i]
            for j in range(self._m):
                res_i[j] = (self_i[j] + other_i[j]) % self._mod
        return ret

    def __pos__(self: _MatrixModT) -> _MatrixModT:
        """
        Return positive copy of matrix (unary + operator).

        Returns:
            Independent copy with the same concrete class and stored entries.

        Time Complexity:
            O(nm).
        """
        return type(self)(self._n, self._m, self._matrix)

    def __neg__(self: _MatrixModT) -> _MatrixModT:
        ret = type(self)(self._n, self._m)
        for i in range(self._n):
            res_i = ret._matrix[i]
            self_i = self._matrix[i]
            for j in range(self._m):
                res_i[j] = -self_i[j] % self._mod
        return ret

    def __sub__(self: _MatrixModT, other: 'MatrixMod') -> _MatrixModT:
        if self._n != other._n or self._m != other._m:
            raise ValueError('incompatible dimensions')
        ret = type(self)(self._n, self._m)
        for i in range(self._n):
            res_i = ret._matrix[i]
            self_i = self._matrix[i]
            other_i = other._matrix[i]
            for j in range(self._m):
                res_i[j] = (self_i[j] - other_i[j]) % self._mod
        return ret

    def __mul__(self: _MatrixModT, other: 'MatrixMod') -> _MatrixModT:
        if self._m != other._n:
            raise ValueError("incompatible dimensions")
        ret = type(self)(self._n, other._m)
        for i in range(self._n):
            res_i = ret._matrix[i]
            self_i = self._matrix[i]
            for k in range(self._m):
                self_ik = self_i[k]
                other_k = other._matrix[k]
                for j in range(other._m):
                    res_i[j] += self_ik * other_k[j]
                    res_i[j] %= self._mod
        return ret

    def matvec(self, vector: Sequence[int]) -> list[int]:
        """
        Multiply this matrix by a column vector.

        Args:
            vector: Vector of length equal to the number of columns.

        Returns:
            Product vector ``A vector`` modulo ``_mod``.

        Raises:
            ValueError: If vector length is incompatible.

        Time Complexity:
            ``O(nm)``
        """
        if len(vector) != self._m:
            raise ValueError("incompatible dimensions")
        res = [0] * self._n
        for i in range(self._n):
            value = 0
            row = self._matrix[i]
            for j in range(self._m):
                value += row[j] * vector[j]
            res[i] = value % self._mod
        return res

    def times(self: _MatrixModT, k: int) -> _MatrixModT:
        """
        Multiply matrix by scalar.

        Args:
            k: Scalar value to multiply with

        Returns:
            MatrixMod: Matrix with all elements multiplied by k modulo _mod

        Time Complexity:
            ``O(nm)``
        """
        ret = type(self)(self._n, self._m)
        for i in range(self._n):
            res_i = ret._matrix[i]
            self_i = self._matrix[i]
            for j in range(self._m):
                res_i[j] = self_i[j] * k % self._mod
        return ret

    def __pow__(self: _MatrixModT, k: int) -> _MatrixModT:
        """Compute matrix power using fast exponentiation.

        Args:
            k: Exponent (non-negative)

        Returns:
            Matrix raised to power k, with normalized entries. Exponent zero
            returns the identity modulo the current modulus; self is unchanged.

        Raises:
            ValueError: If the matrix is not square or k is negative

        Time Complexity:
            O(n**3 log(k + 1) + n**2)
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if k < 0:
            raise ValueError('k must be non-negative')
        ret = type(self).identity(self._n)
        tmp = self
        while k:
            if k & 1:
                ret = ret * tmp
            k >>= 1
            if k:
                tmp = tmp * tmp
        return ret

    def determinant(self) -> int:
        """
        Compute determinant of square matrix.

        Returns:
            Determinant modulo the current modulus. The 0 by 0 determinant is
            1 modulo the modulus (0 when mod = 1). The matrix is not modified.

        Raises:
            ValueError: If matrix is not square

        Notes:
            Uses Gaussian elimination for prime moduli,
            division-free algorithm for non-prime moduli.

        Time Complexity:
            ``O(n^3)`` for prime moduli and ``O(n^3 log mod)`` for the
            division-free non-prime case.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            return self._determinant_nondivision()
        res = 1
        tmp = self.times(1)
        for j in range(self._n):
            if tmp._matrix[j][j] == 0:
                for i in range(j + 1, self._n):
                    if tmp._matrix[i][j] != 0:
                        break
                else:
                    return 0
                tmp._matrix[i], tmp._matrix[j] = tmp._matrix[j], tmp._matrix[i]
                res = -res
            tmp_j = tmp._matrix[j]
            inv = pow(tmp_j[j], self._mod - 2, self._mod)
            for i in range(j + 1, self._n):
                tmp_i = tmp._matrix[i]
                c = -inv * tmp_i[j] % self._mod
                for k in range(self._n):
                    tmp_i[k] += c * tmp_j[k]
                    tmp_i[k] %= self._mod
        for i in range(self._n):
            res *= tmp._matrix[i][i]
            res %= self._mod
        return res

    def _determinant_nondivision(self) -> int:
        if not self.is_square():
            raise ValueError("not a square matrix")
        res = 1 % self._mod
        mat = [[x % self._mod for x in row] for row in self._matrix]
        for i in range(self._n):
            for j in range(i + 1, self._n):
                while mat[j][i] != 0:
                    tmp = mat[i][i] // mat[j][i]
                    if tmp:
                        for k in range(i, self._n):
                            mat[i][k] -= tmp * mat[j][k]
                            mat[i][k] %= self._mod
                    mat[i], mat[j] = mat[j], mat[i]
                    res = -res
            res *= mat[i][i]
            res %= self._mod
        return res

    def transpose(self) -> MatrixMod:
        """
        Compute matrix transpose.

        Returns:
            Transposed matrix

        Time Complexity:
            ``O(nm)``
        """
        ret = type(self)(self._m, self._n)
        for i in range(self._n):
            for j in range(self._m):
                ret[j, i] = self[i, j]
        return ret


class LinearAlgebraFp(MatrixMod):
    """
    Dense matrix over a prime finite field.

    This class extends :class:`MatrixMod` with algorithms that require division
    in the coefficient ring, such as rank, inverse, linear equations,
    characteristic polynomials, and diagonalization.

    Space Complexity:
        ``O(nm)``
    """

    def transpose(self) -> 'LinearAlgebraFp':
        """
        Compute matrix transpose.

        Returns:
            Transposed matrix over the same prime field.

        Time Complexity:
            ``O(nm)``
        """
        ret = type(self)(self._m, self._n)
        for i in range(self._n):
            for j in range(self._m):
                ret[j, i] = self[i, j]
        return ret

    def rank(self) -> int:
        """
        Compute rank of matrix.

        Returns:
            Rank of the matrix

        Raises:
            NotImplementedError: If modulus is not prime

        Time Complexity:
            ``O(nm * min(n, m))``
        """
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        tmp = self.times(1)
        rank = 0
        for j in range(self._m):
            for i in range(rank, self._n):
                if tmp._matrix[i][j] != 0:
                    break
            else:
                continue
            tmp._matrix[i], tmp._matrix[rank] = tmp._matrix[rank], tmp._matrix[i]
            inv = pow(tmp._matrix[rank][j], self._mod - 2, self._mod)
            tmp_rank = tmp._matrix[rank]
            for k in range(self._m):
                tmp_rank[k] *= inv
                tmp_rank[k] %= self._mod
            for i in range(self._n):
                if i == rank:
                    continue
                tmp_i = tmp._matrix[i]
                c = -tmp_i[j]
                for k in range(self._m):
                    tmp_i[k] += c * tmp_rank[k]
                    tmp_i[k] %= self._mod
            rank += 1
        return rank

    def is_skew_symmetric(self) -> bool:
        """
        Check if matrix is skew-symmetric (A^T = -A).

        Returns:
            bool: True if matrix is skew-symmetric, False otherwise

        Notes:
            A skew-symmetric matrix satisfies A[i,j] = -A[j,i] for all i,j.
            Only square matrices can be skew-symmetric.

        Time Complexity:
            ``O(n^2)``
        """
        if not self.is_square():
            return False
        for i in range(self._n):
            for j in range(i, self._n):
                if (self[i, j] + self[j, i]) % self._mod:
                    return False
        return True

    def pfaffian(self) -> int:
        """
        Compute the Pfaffian of an alternating matrix.

        Returns:
            Pfaffian value modulo _mod

        Raises:
            ValueError: If the matrix is not square, is not skew-symmetric,
                or has a nonzero diagonal modulo the modulus.
            NotImplementedError: If modulus is not prime

        Notes:
            Requires A^T = -A and zero diagonal, also in characteristic two.
            For even-sized alternating A, det(A) = pf(A)**2. An odd-sized
            alternating matrix has Pfaffian 0; the empty matrix has Pfaffian 1.

        Time Complexity:
            ``O(n^3)``
        """
        if not self.is_skew_symmetric() or any(self[i, i] % self._mod for i in range(self._n)):
            raise ValueError('pfaffian requires an alternating matrix')
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        n = self._n
        if n % 2 == 1: return 0
        tmp = self.times(1)
        res = 1
        for k in range(0, n, 2):
            pivot = tmp._matrix[k][k + 1]
            if pivot == 0:
                for i in range(k + 2, n):
                    if tmp._matrix[k][i] != 0:
                        tmp._matrix[k + 1], tmp._matrix[i] = tmp._matrix[i], tmp._matrix[k + 1]
                        for row in tmp._matrix:
                            row[k + 1], row[i] = row[i], row[k + 1]
                        res = (-res) % self._mod
                        pivot = tmp._matrix[k][k + 1]
                        break
                else:
                    return 0
            res = res * pivot % self._mod
            inv_pivot = pow(pivot, self._mod - 2, self._mod)
            for i in range(k + 2, n):
                for j in range(i + 1, n):
                    tmp._matrix[i][j] = (tmp._matrix[i][j] - tmp._matrix[k][i] * tmp._matrix[k + 1][j] * inv_pivot + tmp._matrix[k][j] * tmp._matrix[k + 1][i] * inv_pivot) % self._mod
                    tmp._matrix[j][i] = -tmp._matrix[i][j] % self._mod
        return res

    def __invert__(self) -> 'LinearAlgebraFp':
        """Compute matrix inverse.

        Returns:
            Inverse matrix such that A * A^(-1) = I

        Raises:
            ValueError: If matrix is not square or not invertible
            NotImplementedError: If modulus is not prime

        Notes:
            Can be called with ~A syntax.

        Time Complexity:
            O(n^3)
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        ret = type(self).identity(self._n)
        tmp = self.times(1)
        for j in range(self._n):
            if tmp._matrix[j][j] == 0:
                for i in range(j + 1, self._n):
                    if tmp._matrix[i][j] != 0:
                        break
                else:
                    raise ValueError("not invertible")
                tmp._matrix[i], tmp._matrix[j] = tmp._matrix[j], tmp._matrix[i]
                ret._matrix[i], ret._matrix[j] = ret._matrix[j], ret._matrix[i]
            tmp_j = tmp._matrix[j]
            ret_j = ret._matrix[j]
            inv = pow(tmp_j[j], self._mod - 2, self._mod)
            for k in range(self._n):
                tmp_j[k] *= inv
                tmp_j[k] %= self._mod
                ret_j[k] *= inv
                ret_j[k] %= self._mod
            for i in range(self._n):
                if i == j:
                    continue
                tmp_i = tmp._matrix[i]
                ret_i = ret._matrix[i]
                c = -tmp_i[j]
                for k in range(self._n):
                    tmp_i[k] += c * tmp_j[k]
                    tmp_i[k] %= self._mod
                    ret_i[k] += c * ret_j[k]
                    ret_i[k] %= self._mod
        return ret

    def linear_equations(self, b: list[int]) -> LinearEquationResult:
        """
        Solve system of linear equations Ax = b.

        Args:
            b: Right-hand side vector

        Returns:
            LinearEquationResult: Contains dimension of solution space,
                                  particular solution vector, and basis vectors

        Raises:
            ValueError: If no solution exists or dimensions incompatible
            NotImplementedError: If modulus is not prime

        Notes:
            General solution is x = particular + sum(c_i * basis[i])

        Time Complexity:
            ``O(nm * min(n, m))``
        """
        if self._n != len(b):
            raise ValueError("incompatible dimensions")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        aug = [[x % self._mod for x in row] + [b[i] % self._mod] for i, row in enumerate(self._matrix)]
        rank = 0
        p: list[int] = []
        q: list[int] = []
        for j in range(self._m + 1):
            for i in range(rank, self._n):
                if aug[i][j] != 0:
                    break
            else:
                q.append(j)
                continue
            if j == self._m:
                raise ValueError("no solution")
            p.append(j)
            aug[i], aug[rank] = aug[rank], aug[i]
            inv = pow(aug[rank][j], self._mod - 2, self._mod)
            aug_rank = aug[rank]
            for k in range(self._m + 1):
                aug_rank[k] *= inv
                aug_rank[k] %= self._mod
            for i in range(self._n):
                if i == rank:
                    continue
                aug_i = aug[i]
                c = -aug_i[j]
                for k in range(self._m + 1):
                    aug_i[k] += c * aug_rank[k]
                    aug_i[k] %= self._mod
            rank += 1
        dim = self._m - rank
        sol = [0] * self._m
        for i in range(rank):
            sol[p[i]] = aug[i][self._m]
        vecs = [[0] * self._m for _ in range(dim)]
        for i in range(dim):
            vecs[i][q[i]] = 1
            for k in range(rank):
                vecs[i][p[k]] = -aug[k][q[i]]
                vecs[i][p[k]] %= self._mod
        return LinearEquationResult(dim, sol, vecs)

    @classmethod
    def _characteristic_polynomial_from_hessenberg(cls, hessenberg: list[list[int]]) -> list[int]:
        n = len(hessenberg)
        dp = [[0] * (i + 1) for i in range(n + 1)]
        dp[0][0] = 1
        for i in range(n):
            for k in range(i + 1):
                dp[i + 1][k + 1] = dp[i][k]
            for k in range(i + 1):
                dp[i + 1][k] += dp[i][k] * hessenberg[i][i]
                dp[i + 1][k] %= cls._mod
            p = 1
            for j in range(i)[::-1]:
                p *= -hessenberg[j + 1][j]
                p %= cls._mod
                c = p * hessenberg[j][i] % cls._mod
                for k in range(j + 1):
                    dp[i + 1][k] += dp[j][k] * c
                    dp[i + 1][k] %= cls._mod
        res = dp[n]
        for i in range(n + 1):
            if i & 1:
                res[~i] *= -1
                res[~i] %= cls._mod
        return res

    def hessenberg_decomposition(self) -> tuple['LinearAlgebraFp', 'LinearAlgebraFp']:
        """
        Return an upper Hessenberg matrix similar to this matrix.

        Returns:
            Pair ``(H, P)`` satisfying ``H = P^-1 A P``. The matrix ``H`` is
            upper Hessenberg, meaning ``H[i][j] = 0`` for ``i > j + 1``.

        Raises:
            ValueError: If matrix is not square
            NotImplementedError: If modulus is not prime

        Time Complexity:
            ``O(n^3)``
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        h = self.times(1)
        transform = type(self).identity(self._n)
        for j in range(self._m - 2):
            for i in range(j + 1, self._n):
                if h._matrix[i][j] != 0:
                    break
            else:
                continue
            k = j + 1
            h._matrix[i], h._matrix[k] = h._matrix[k], h._matrix[i]
            for row in h._matrix:
                row[i], row[k] = row[k], row[i]
            for row in transform._matrix:
                row[i], row[k] = row[k], row[i]
            if h._matrix[k][j] == 0:
                continue
            inv = pow(h._matrix[k][j], self._mod - 2, self._mod)
            for i in range(j + 2, self._n):
                c = inv * h._matrix[i][j] % self._mod
                for l in range(j, self._n):
                    h._matrix[i][l] -= c * h._matrix[k][l]
                    h._matrix[i][l] %= self._mod
                for l in range(self._m):
                    h._matrix[l][k] += c * h._matrix[l][i]
                    h._matrix[l][k] %= self._mod
                    transform._matrix[l][k] += c * transform._matrix[l][i]
                    transform._matrix[l][k] %= self._mod
        return h, transform

    def characteristic_polynomial(self) -> list[int]:
        """
        Compute characteristic polynomial of matrix.

        Returns:
            Coefficients of characteristic polynomial from degree 0 to n

        Raises:
            ValueError: If matrix is not square
            NotImplementedError: If modulus is not prime

        Notes:
            The characteristic polynomial is det(xI - A).
            Eigenvalues are roots of this polynomial.

        Time Complexity:
            ``O(n^3)``
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        h, _ = self.hessenberg_decomposition()
        return self._characteristic_polynomial_from_hessenberg(h._matrix)

    def _characteristic_root_multiplicities(self, char_poly: Sequence[int] | None = None) -> list[tuple[int, int]] | None:
        if FormalPowerSeriesMod.get_mod() != self._mod:
            FormalPowerSeriesMod.set_mod(self._mod)

        poly = FormalPowerSeriesMod(char_poly if char_poly is not None else self.characteristic_polynomial()).trimmed()
        roots = polynomial_roots(poly)
        multiplicities: list[tuple[int, int]] = []
        rem = poly
        for root in roots:
            linear = FormalPowerSeriesMod([(-root) % self._mod, 1])
            multiplicity = 0
            while True:
                quotient, remainder = rem.divmod_poly(linear)
                if not remainder.is_zero():
                    break
                multiplicity += 1
                rem = quotient.trimmed()
            if multiplicity:
                multiplicities.append((root, multiplicity))
        if rem.degree() > 0:
            return None
        return multiplicities

    @staticmethod
    def _restrict_basis_by_linear_equation(
        basis: list[list[int]],
        coeffs: Sequence[int],
        mod: int,
    ) -> list[list[int]]:
        values: list[int] = []
        for vector in basis:
            value = 0
            for coeff, x in zip(coeffs, vector):
                value += coeff * x
            values.append(value % mod)
        for pivot, value in enumerate(values):
            if value != 0:
                break
        else:
            return [vector[:] for vector in basis]
        inv = pow(values[pivot], -1, mod)
        restricted: list[list[int]] = []
        pivot_vector = basis[pivot]
        for i, vector in enumerate(basis):
            if i == pivot:
                continue
            factor = values[i] * inv % mod
            restricted.append([(x - factor * y) % mod for x, y in zip(vector, pivot_vector)])
        return restricted

    def _hessenberg_kernel(self, hessenberg: list[list[int]], root: int) -> list[list[int]]:
        n = len(hessenberg)
        if n == 0:
            return []
        basis = [[1]]
        for i in range(n - 1, 0, -1):
            coeffs = hessenberg[i][i:n]
            coeffs = coeffs[:]
            coeffs[0] = (coeffs[0] - root) % self._mod
            subdiag = hessenberg[i][i - 1]
            suffix_len = n - i
            if subdiag != 0:
                inv = pow(subdiag, -1, self._mod)
                new_basis: list[list[int]] = []
                for vector in basis:
                    value = 0
                    for coeff, x in zip(coeffs, vector):
                        value += coeff * x
                    new_basis.append([(-value * inv) % self._mod] + vector)
                basis = new_basis
            else:
                restricted = self._restrict_basis_by_linear_equation(basis, coeffs, self._mod)
                basis = [[1] + [0] * suffix_len]
                basis += [[0] + vector for vector in restricted]
        coeffs = hessenberg[0][:]
        coeffs[0] = (coeffs[0] - root) % self._mod
        return self._restrict_basis_by_linear_equation(basis, coeffs, self._mod)

    def diagonalize(self) -> DiagonalizationResult | None:
        """
        Diagonalize the matrix over the current modular field if possible.

        Returns:
            ``DiagonalizationResult`` when the matrix is diagonalizable over
            ``F_mod``; otherwise ``None``.

        Raises:
            ValueError: If matrix is not square
            NotImplementedError: If modulus is not prime

        Notes:
            The returned transform matrix ``P`` stores eigenvectors as columns,
            and satisfies ``P^-1 A P = D`` where ``D`` is the returned diagonal
            matrix. This method does not diagonalize over extension fields. When
            the characteristic polynomial splits over the current field,
            eigenspaces are computed on a similar upper Hessenberg matrix and
            mapped back through the similarity transform.

        Time Complexity:
            Expected ``O(n^3 + R(n))``, where ``R(n)`` is the cost of root
            finding for the characteristic polynomial.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        n = self._n
        hessenberg, transform_to_hessenberg = self.hessenberg_decomposition()
        char_poly = self._characteristic_polynomial_from_hessenberg(hessenberg._matrix)
        multiplicities = self._characteristic_root_multiplicities(char_poly)
        if multiplicities is None:
            return None

        eigenvalues: list[int] = []
        eigenvectors: list[list[int]] = []
        for root, multiplicity in multiplicities:
            kernel = self._hessenberg_kernel(hessenberg._matrix, root)
            if len(kernel) != multiplicity:
                return None
            for vector in kernel:
                original_vector: list[int] = transform_to_hessenberg.matvec(vector)
                eigenvalues.append(root)
                eigenvectors.append(original_vector)

        if len(eigenvectors) != n:
            return None

        transform = type(self)(n, n)
        diagonal = type(self)(n, n)
        for j, (root, vector) in enumerate(zip(eigenvalues, eigenvectors)):
            image = self.matvec(vector)
            if any((image[i] - root * vector[i]) % self._mod != 0 for i in range(n)):
                return None
            diagonal._matrix[j][j] = root
            for i in range(n):
                transform._matrix[i][j] = vector[i] % self._mod
        return DiagonalizationResult(eigenvalues, transform, diagonal)

    def pow_by_diagonalization(self, k: int) -> 'LinearAlgebraFp | None':
        """
        Compute matrix power using diagonalization when possible.

        Args:
            k: Exponent (non-negative)

        Returns:
            Matrix raised to power k, or ``None`` if this matrix is not
            diagonalizable over the current modular field.

        Raises:
            ValueError: If matrix is not square or k is negative
            NotImplementedError: If modulus is not prime

        Time Complexity:
            Expected O(n**3 + R(n) + n log(k + 1)), where R(n) is the cost of
            root finding for the characteristic polynomial.
        """
        if k < 0:
            raise ValueError("negative exponent is not supported")
        result = self.diagonalize()
        if result is None:
            return None
        n = self._n
        scaled_transform = type(self)(n, n)
        for j, eigenvalue in enumerate(result.eigenvalues):
            multiplier = pow(eigenvalue, k, self._mod)
            for i in range(n):
                scaled_transform._matrix[i][j] = result.transform._matrix[i][j] * multiplier % self._mod
        return scaled_transform * ~result.transform

    @classmethod
    def companion_matrix(cls, polynomial: Sequence[int]) -> 'LinearAlgebraFp':
        """
        Build a companion matrix.

        Args:
            polynomial: Monic polynomial ``[c_0, c_1, ..., c_n]`` in
                ascending-degree order.

        Returns:
            Companion matrix ``C`` satisfying ``C e_i = e_{i+1}`` for
            ``i < n - 1`` and ``C e_{n-1} = -sum(c_i e_i)``.

        Raises:
            ValueError: If the coefficient sequence is empty or its final
                coefficient is not congruent to 1 modulo the current modulus.

        Time Complexity:
            O(n**2), including allocation of the dense matrix.

        Space Complexity:
            O(n**2). The constant polynomial [1] gives a 0 by 0 matrix.
        """
        n = len(polynomial) - 1
        if n < 0 or polynomial[-1] % cls._mod != 1:
            raise ValueError("polynomial must be monic")
        ret = cls(n, n)
        for j in range(n - 1):
            ret._matrix[j + 1][j] = 1
        for i in range(n):
            ret._matrix[i][n - 1] = (-polynomial[i]) % cls._mod
        return ret

    @classmethod
    def companion_power(cls, characteristic_polynomial: Sequence[int], k: int) -> 'LinearAlgebraFp':
        """
        Compute the power of a companion matrix.

        Args:
            characteristic_polynomial: Monic polynomial
                ``[c_0, c_1, ..., c_n]`` in ascending-degree order.
            k: Exponent (non-negative)

        Returns:
            ``C^k`` where ``C`` is the companion matrix satisfying
            ``C e_i = e_{i+1}`` for ``i < n - 1`` and
            ``C e_{n-1} = -sum(c_i e_i)``.

        Raises:
            ValueError: If the polynomial is empty, is not monic modulo the
                current modulus, or k is negative.
            NotImplementedError: If the modulus is not prime.

        Time Complexity:
            O(M(n) log(k + 1) + n**2), where M(n) is polynomial multiplication
            cost, up to O(n**2) when the modulus has insufficient NTT capacity.

        Space Complexity:
            O(n**2).
        """
        if k < 0:
            raise ValueError("negative exponent is not supported")
        if not cls._is_prime:
            raise NotImplementedError('not implemented for non-prime moduli')
        n = len(characteristic_polynomial) - 1
        if n < 0 or characteristic_polynomial[-1] % cls._mod != 1:
            raise ValueError("characteristic_polynomial must be monic")
        ret = cls(n, n)
        if n == 0:
            return ret
        if FormalPowerSeriesMod.get_mod() != cls._mod:
            FormalPowerSeriesMod.set_mod(cls._mod)
        mod_poly = FormalPowerSeriesMod(characteristic_polynomial)
        column = FormalPowerSeriesMod([0, 1]).pow_mod(k, mod_poly).resize(n).coef
        coeffs = [c % cls._mod for c in characteristic_polynomial[:-1]]
        for j in range(n):
            for i in range(n):
                ret._matrix[i][j] = column[i]
            if j + 1 == n:
                break
            top = column[-1]
            next_column = [0] * n
            for i in range(1, n):
                next_column[i] = column[i - 1]
            if top:
                for i in range(n):
                    next_column[i] -= top * coeffs[i]
                    next_column[i] %= cls._mod
            column = next_column
        return ret

    @classmethod
    def block_companion_matrix(cls, polynomials: Sequence[Sequence[int]]) -> 'LinearAlgebraFp':
        """
        Build a block diagonal matrix of companion blocks.

        Args:
            polynomials: Monic block polynomials in ascending-degree order.

        Returns:
            Block diagonal companion matrix.

        Raises:
            ValueError: If any block polynomial is empty or not monic modulo
                the current modulus. Empty block lists are allowed.

        Time Complexity:
            O(b + n**2), where b is the number of blocks and n is their total
            degree. Constant blocks contribute no rows or columns.

        Space Complexity:
            O(n**2).
        """
        if any(not poly or poly[-1] % cls._mod != 1 for poly in polynomials):
            raise ValueError('block polynomials must be monic')
        n = sum(len(poly) - 1 for poly in polynomials)
        ret = cls(n, n)
        offset = 0
        for poly in polynomials:
            block = cls.companion_matrix(poly)
            size = block._n
            for i in range(size):
                row = ret._matrix[offset + i]
                block_i = block._matrix[i]
                for j in range(size):
                    row[offset + j] = block_i[j]
            offset += size
        return ret

    @classmethod
    def block_companion_power(cls, polynomials: Sequence[Sequence[int]], k: int) -> 'LinearAlgebraFp':
        """
        Compute the power of a block diagonal companion matrix.

        Args:
            polynomials: Monic block polynomials in ascending-degree order.
            k: Exponent (non-negative)

        Returns:
            ``diag(C(f_1)^k, C(f_2)^k, ...)``.

        Raises:
            ValueError: If k is negative or any block polynomial is empty or
                not monic modulo the current modulus.
            NotImplementedError: If the modulus is not prime.

        Time Complexity:
            O(b + n**2 + sum(M(deg(f_i)) log(k + 1))), including allocation
            of the dense n by n result; b is the number of blocks.

        Space Complexity:
            O(n**2).
        """
        if k < 0:
            raise ValueError('negative exponent is not supported')
        if not cls._is_prime:
            raise NotImplementedError('not implemented for non-prime moduli')
        if any(not poly or poly[-1] % cls._mod != 1 for poly in polynomials):
            raise ValueError('block polynomials must be monic')
        n = sum(len(poly) - 1 for poly in polynomials)
        ret = cls(n, n)
        offset = 0
        for poly in polynomials:
            block = cls.companion_power(poly, k)
            size = block._n
            for i in range(size):
                row = ret._matrix[offset + i]
                block_i = block._matrix[i]
                for j in range(size):
                    row[offset + j] = block_i[j]
            offset += size
        return ret

    def cyclic_frobenius_form(self, *, max_retry: int = 8) -> FrobeniusCyclicForm | None:
        """
        Compute a one-block Frobenius normal form when the matrix is cyclic.

        Args:
            max_retry: Non-negative number of random candidates to try after
                the first coordinate vector and the all-ones vector.

        Returns:
            ``FrobeniusCyclicForm`` if a cyclic vector is found; otherwise
            ``None``. For the returned form, ``A P = P C`` holds, where ``P``
            is the transform matrix and ``C`` is the companion matrix.

        Raises:
            ValueError: If the matrix is not square or max_retry is negative.
            NotImplementedError: If modulus is not prime

        Time Complexity:
            O((R + 2) n**3) in the worst case, with earlier termination when
            a cyclic vector is found. None does not prove that A is non-cyclic.

        Space Complexity:
            O(n**2). Candidates are generated only when needed.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        if max_retry < 0:
            raise ValueError('max_retry must be non-negative')
        n = self._n
        char_poly = self.characteristic_polynomial()
        companion = type(self).companion_matrix(char_poly)
        if n == 0:
            return FrobeniusCyclicForm(char_poly, type(self)(0, 0), companion)

        rng = SystemRandom()
        for trial in range(max_retry + 2):
            if trial == 0:
                vector = [0] * n
                vector[0] = 1
            elif trial == 1:
                vector = [1] * n
            else:
                vector = [rng.randrange(self._mod) for _ in range(n)]
            transform = type(self)(n, n)
            current = [x % self._mod for x in vector]
            for j in range(n):
                for i in range(n):
                    transform._matrix[i][j] = current[i]
                if j + 1 < n:
                    current = self.matvec(current)
            if transform.rank() == n:
                return FrobeniusCyclicForm(char_poly, transform, companion)
        return None

    def pow_by_frobenius(self, k: int, *, max_retry: int = 0) -> 'LinearAlgebraFp':
        """
        Compute matrix power through a Frobenius form.

        Args:
            k: Exponent (non-negative)
            max_retry: Number of optional random trials used after the
                deterministic form finder candidates.

        Returns:
            Matrix raised to power k.

        Raises:
            ValueError: If the matrix is not square, k is negative, or max_retry
                is negative.
            RuntimeError: If Frobenius construction fails for all candidates.
            NotImplementedError: If modulus is not prime

        Time Complexity:
            Cost of frobenius_form, then O(n**3 + sum(M(deg(f_i)) log(k + 1)))
            for block powers and reconstruction.
        """
        if k < 0:
            raise ValueError("negative exponent is not supported")
        form = self.frobenius_form(max_retry=max_retry)
        return self.pow_by_frobenius_form(form, k)

    def frobenius_form(self, *, max_retry: int = 0) -> FrobeniusForm:
        """
        Compute a Frobenius decomposition with invariant factors.

        Args:
            max_retry: Non-negative number of additional random leading vectors
                tried after the deterministic leading-vector candidates.

        Returns:
            ``FrobeniusForm``. The returned block polynomials are invariant
            factors: each non-constant factor divides the next one. The
            implementation first constructs a Krylov block decomposition and
            then computes invariant factors by a polynomial Smith
            transformation of the presentation matrix.

        Raises:
            ValueError: If the matrix is not square or max_retry is negative.
            RuntimeError: If all candidate decompositions fail certification.
            NotImplementedError: If modulus is not prime

        Time Complexity:
            Starts with two cyclic-vector trials, each O(n**3). Otherwise tries
            at most 6 + R + n leading-vector/basis-order combinations for n <= 64,
            or 6 + R for larger n. Each attempt includes O(n**3) for Krylov
            construction plus polynomial Smith elimination and generator
            reconstruction; their cost depends on intermediate polynomial degrees.

        Notes:
            Candidate transforms are checked for invertibility and A P = P F
            before being returned. No input entries are modified.
        """
        if max_retry < 0:
            raise ValueError('max_retry must be non-negative')
        cyclic_form = self.cyclic_frobenius_form(max_retry=0)
        if cyclic_form is not None:
            return FrobeniusForm(
                [cyclic_form.characteristic_polynomial],
                cyclic_form.transform,
                cyclic_form.companion,
            )

        leading_vectors: list[list[int] | None] = [None]
        if self._n > 0:
            leading_vectors.append([1] * self._n)
            leading_vectors.append([(i + 1) % self._mod for i in range(self._n)])
            leading_vectors.append([pow(i + 1, 2, self._mod) for i in range(self._n)])
            leading_vectors.append([pow(i + 1, 3, self._mod) for i in range(self._n)])
        rng = SystemRandom()
        for _ in range(max_retry):
            leading_vectors.append([rng.randrange(self._mod) for _ in range(self._n)])
        if self._n <= 64:
            for seed_index in range(self._n):
                seed = [0] * self._n
                seed[seed_index] = 1
                leading_vectors.append(seed)

        for leading_vector in leading_vectors:
            reverse_options = (False, True) if leading_vector is None else (False,)
            for reverse_basis in reverse_options:
                block_form = self.krylov_block_decomposition(
                    max_retry=0,
                    reverse_basis=reverse_basis,
                    leading_vector=leading_vector,
                )
                form = type(self)._block_extension_frobenius_form(
                    block_form.action,
                    block_form.block_ranges,
                )
                if form is not None:
                    return FrobeniusForm(
                        form.polynomials,
                        block_form.transform * form.transform,
                        form.frobenius,
                    )
        raise RuntimeError("failed to construct Frobenius form")

    @classmethod
    def _apply_polynomial_to_action_vector(
        cls,
        action: 'LinearAlgebraFp',
        polynomial: Sequence[int],
        vector: Sequence[int],
    ) -> list[int]:
        res = [0] * action._n
        current = [x % cls._mod for x in vector]
        last = len(polynomial) - 1
        for degree, coeff in enumerate(polynomial):
            coeff %= cls._mod
            if coeff:
                for i in range(action._n):
                    res[i] += coeff * current[i]
                    res[i] %= cls._mod
            if degree != last:
                current = action.matvec(current)
        return res

    @classmethod
    def _smith_polynomial_generator_transform(
        cls,
        matrix: list[list[list[int]]],
    ) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
        size = len(matrix)
        zero = [0]
        one = [1]
        mod = cls._mod

        def trim(coeffs: Sequence[int]) -> list[int]:
            res = [c % mod for c in coeffs]
            while len(res) > 1 and res[-1] == 0:
                res.pop()
            if not res:
                return [0]
            return res

        def is_zero(coeffs: Sequence[int]) -> bool:
            return len(coeffs) == 1 and coeffs[0] == 0

        def add(left: list[int], right: list[int]) -> list[int]:
            size = max(len(left), len(right))
            res = [0] * size
            left_len = len(left)
            right_len = len(right)
            for i in range(size):
                value = 0
                if i < left_len:
                    value += left[i]
                if i < right_len:
                    value += right[i]
                res[i] = value % mod
            while len(res) > 1 and res[-1] == 0:
                res.pop()
            return res

        def sub(left: list[int], right: list[int]) -> list[int]:
            size = max(len(left), len(right))
            res = [0] * size
            left_len = len(left)
            right_len = len(right)
            for i in range(size):
                value = 0
                if i < left_len:
                    value += left[i]
                if i < right_len:
                    value -= right[i]
                res[i] = value % mod
            while len(res) > 1 and res[-1] == 0:
                res.pop()
            return res

        def mul(left: Sequence[int], right: list[int]) -> list[int]:
            left = trim(left)
            if is_zero(left) or is_zero(right):
                return [0]
            res = [0] * (len(left) + len(right) - 1)
            for i, li in enumerate(left):
                if li == 0:
                    continue
                for j, rj in enumerate(right):
                    res[i + j] += li * rj
                    res[i + j] %= mod
            while len(res) > 1 and res[-1] == 0:
                res.pop()
            return res

        def divmod_poly(left: list[int], right: list[int]) -> tuple[list[int], list[int]]:
            if is_zero(right):
                raise ZeroDivisionError("polynomial division by zero")
            rem = left[:]
            if len(rem) < len(right):
                return [0], rem
            quotient = [0] * (len(rem) - len(right) + 1)
            inv_lead = pow(right[-1], -1, mod)
            right_degree = len(right) - 1
            while len(rem) >= len(right) and not is_zero(rem):
                degree_diff = len(rem) - len(right)
                coeff = rem[-1] * inv_lead % mod
                quotient[degree_diff] = coeff
                if coeff:
                    for i in range(right_degree + 1):
                        rem[degree_diff + i] -= coeff * right[i]
                        rem[degree_diff + i] %= mod
                while len(rem) > 1 and rem[-1] == 0:
                    rem.pop()
            while len(quotient) > 1 and quotient[-1] == 0:
                quotient.pop()
            return quotient, rem

        mat = [[trim(matrix[i][j]) for j in range(size)] for i in range(size)]
        generator_transform = [
            [one[:] if i == j else zero[:] for j in range(size)]
            for i in range(size)
        ]

        def swap_rows(i: int, j: int) -> None:
            mat[i], mat[j] = mat[j], mat[i]
            for row in generator_transform:
                row[i], row[j] = row[j], row[i]

        def swap_cols(i: int, j: int) -> None:
            for row in mat:
                row[i], row[j] = row[j], row[i]

        def add_row_multiple(dst: int, src: int, multiplier: Sequence[int]) -> None:
            for col in range(size):
                mat[dst][col] = add(
                    mat[dst][col],
                    mul(multiplier, mat[src][col]),
                )
            for row in range(size):
                generator_transform[row][src] = sub(
                    generator_transform[row][src],
                    mul(multiplier, generator_transform[row][dst]),
                )

        def add_col_multiple(dst: int, src: int, multiplier: Sequence[int]) -> None:
            for row in range(size):
                mat[row][dst] = add(
                    mat[row][dst],
                    mul(multiplier, mat[row][src]),
                )

        index = 0
        while index < size:
            entries: list[tuple[int, int, int]] = []
            for i in range(index, size):
                for j in range(index, size):
                    if not is_zero(mat[i][j]):
                        entries.append((len(mat[i][j]) - 1, i, j))
            if not entries:
                break
            _, pivot_row, pivot_col = min(entries)
            if pivot_row != index:
                swap_rows(index, pivot_row)
            if pivot_col != index:
                swap_cols(index, pivot_col)

            while True:
                changed = False
                for row in range(index + 1, size):
                    if is_zero(mat[row][index]):
                        continue
                    quotient, remainder = divmod_poly(mat[row][index], mat[index][index])
                    add_row_multiple(row, index, [(-c) % mod for c in quotient])
                    if not is_zero(remainder):
                        swap_rows(index, row)
                    changed = True
                    break
                if changed:
                    continue
                for col in range(index + 1, size):
                    if is_zero(mat[index][col]):
                        continue
                    quotient, remainder = divmod_poly(mat[index][col], mat[index][index])
                    add_col_multiple(col, index, [(-c) % mod for c in quotient])
                    if not is_zero(remainder):
                        swap_cols(index, col)
                    changed = True
                    break
                if changed:
                    continue

                bad_entry: tuple[int, int] | None = None
                for row in range(index + 1, size):
                    for col in range(index + 1, size):
                        _, remainder = divmod_poly(mat[row][col], mat[index][index])
                        if not is_zero(remainder):
                            bad_entry = (row, col)
                            break
                    if bad_entry is not None:
                        break
                if bad_entry is None:
                    break
                add_row_multiple(index, bad_entry[0], [1])

            lead = mat[index][index][-1]
            if lead != 1:
                lead_inv = pow(lead, -1, cls._mod)
                for col in range(size):
                    mat[index][col] = [(c * lead_inv) % mod for c in mat[index][col]]
                    generator_transform[col][index] = [(c * lead) % mod for c in generator_transform[col][index]]
            index += 1
        return mat, generator_transform

    @classmethod
    def _block_extension_frobenius_form(
        cls,
        action: 'LinearAlgebraFp',
        block_ranges: Sequence[tuple[int, int]],
    ) -> FrobeniusForm | None:
        block_count = len(block_ranges)
        size = action._n
        presentation = [[[0] for _ in range(block_count)] for _ in range(block_count)]
        starts = [start for start, _ in block_ranges]
        for block_index, (start, end) in enumerate(block_ranges):
            polynomial = [(-action._matrix[i][end - 1]) % cls._mod for i in range(start, end)]
            polynomial.append(1)
            presentation[block_index][block_index] = polynomial
            generator = [0] * size
            generator[start] = 1
            relation = cls._apply_polynomial_to_action_vector(action, polynomial, generator)
            for prev_index, (prev_start, prev_end) in enumerate(block_ranges[:block_index]):
                presentation[prev_index][block_index] = [
                    (-relation[i]) % cls._mod
                    for i in range(prev_start, prev_end)
                ]
            if any(relation[i] for i in range(end, size)):
                return None

        smith, generator_transform = cls._smith_polynomial_generator_transform(presentation)
        invariant_polynomials: list[list[int]] = []
        generator_indices: list[int] = []
        mod = cls._mod

        def is_zero(coeffs: list[int]) -> bool:
            return len(coeffs) == 1 and coeffs[0] == 0

        def normalize_monic(coeffs: list[int]) -> list[int]:
            if is_zero(coeffs):
                return [0]
            inv = pow(coeffs[-1], -1, mod)
            return [(c * inv) % mod for c in coeffs]

        for i in range(block_count):
            for j in range(block_count):
                if i != j and not is_zero(smith[i][j]):
                    return None
            poly = smith[i][i]
            if len(poly) > 1:
                invariant_polynomials.append(normalize_monic(poly))
                generator_indices.append(i)
        columns: list[list[int]] = []
        for poly, generator_index in zip(invariant_polynomials, generator_indices):
            generator = [0] * size
            for old_index, coeffs in enumerate(row[generator_index] for row in generator_transform):
                if is_zero(coeffs):
                    continue
                base = [0] * size
                base[starts[old_index]] = 1
                component = cls._apply_polynomial_to_action_vector(action, coeffs, base)
                for i in range(size):
                    generator[i] += component[i]
                    generator[i] %= cls._mod
            current = generator
            for _ in range(len(poly) - 1):
                columns.append(current)
                current = action.matvec(current)
        if len(columns) != size:
            return None
        transform = cls(size, size)
        for j, vector in enumerate(columns):
            for i, value in enumerate(vector):
                transform._matrix[i][j] = value
        if transform.rank() != size:
            return None
        frobenius = cls.block_companion_matrix(invariant_polynomials)
        if (action * transform)._matrix != (transform * frobenius)._matrix:
            return None
        return FrobeniusForm(invariant_polynomials, transform, frobenius)

    def krylov_block_decomposition(
        self,
        *,
        max_retry: int = 8,
        reverse_basis: bool = False,
        leading_vector: Sequence[int] | None = None,
    ) -> KrylovBlockForm:
        """
        Decompose the space into Krylov-generated blocks.

        Args:
            max_retry: Non-negative maximum number of random seed vectors tried
                after leading_vector and before the standard basis vectors.
            reverse_basis: Whether to try standard basis vectors in reverse
                order.
            leading_vector: Optional seed vector tried before the standard
                basis vectors.

        Returns:
            ``KrylovBlockForm`` containing a basis matrix ``P`` and an action
            matrix ``T`` satisfying ``A P = P T``.

        Raises:
            ValueError: If the matrix is not square, max_retry is negative, or
                leading_vector has an incompatible length.
            NotImplementedError: If modulus is not prime

        Notes:
            This works for any square matrix over the current prime field, but
            ``T`` is not necessarily block diagonal. It is an intermediate form
            toward a full Frobenius decomposition.

        Time Complexity:
            O(n**3 + R n**2) in the worst case. Stops once a complete basis is
            found, without generating or reducing the remaining seeds.

        Space Complexity:
            O(n**2).
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        if max_retry < 0:
            raise ValueError('max_retry must be non-negative')
        n = self._n
        basis_vectors: list[list[int]] = []
        block_ranges: list[tuple[int, int]] = []
        echelon_vectors: list[list[int]] = []
        echelon_coords: list[list[int]] = []
        pivot_rows: list[int] = []

        def reduce_vector(vector: Sequence[int]) -> tuple[list[int], list[int]]:
            reduced = [x % self._mod for x in vector]
            coords = [0] * len(basis_vectors)
            for pivot, echelon, echelon_coord in zip(pivot_rows, echelon_vectors, echelon_coords):
                factor = reduced[pivot]
                if factor == 0:
                    continue
                for i in range(n):
                    reduced[i] -= factor * echelon[i]
                    reduced[i] %= self._mod
                for i, c in enumerate(echelon_coord):
                    coords[i] -= factor * c
                    coords[i] %= self._mod
            return reduced, coords

        def coordinates(vector: Sequence[int]) -> list[int] | None:
            reduced, coords = reduce_vector(vector)
            if any(reduced):
                return None
            return [(-c) % self._mod for c in coords]

        def add_basis_vector(vector: Sequence[int]) -> bool:
            reduced, coords = reduce_vector(vector)
            for pivot, value in enumerate(reduced):
                if value != 0:
                    break
            else:
                return False
            inv = pow(reduced[pivot], -1, self._mod)
            for i in range(n):
                reduced[i] = reduced[i] * inv % self._mod
            for i in range(len(coords)):
                coords[i] = coords[i] * inv % self._mod
            for coord in echelon_coords:
                coord.append(0)
            coords.append(inv)
            basis_vectors.append([x % self._mod for x in vector])
            pivot_rows.append(pivot)
            echelon_vectors.append(reduced)
            echelon_coords.append(coords)
            return True

        if leading_vector is not None and len(leading_vector) != n:
            raise ValueError('incompatible dimensions')
        leading_count = int(leading_vector is not None)
        rng = SystemRandom()
        for candidate_index in range(leading_count + max_retry + n):
            if len(basis_vectors) == n:
                break
            if candidate_index < leading_count:
                assert leading_vector is not None
                seed = [x % self._mod for x in leading_vector]
            elif candidate_index < leading_count + max_retry:
                seed = [rng.randrange(self._mod) for _ in range(n)]
            else:
                seed_index = candidate_index - leading_count - max_retry
                if reverse_basis:
                    seed_index = n - 1 - seed_index
                seed = [0] * n
                seed[seed_index] = 1
            if coordinates(seed) is not None:
                continue
            start = len(basis_vectors)
            current = seed
            while add_basis_vector(current):
                current = self.matvec(current)
            block_ranges.append((start, len(basis_vectors)))

        transform = type(self)(n, n)
        for j, vector in enumerate(basis_vectors):
            for i in range(n):
                transform._matrix[i][j] = vector[i]
        action = type(self)(n, n)
        for j, vector in enumerate(basis_vectors):
            image = self.matvec(vector)
            coord = coordinates(image)
            if coord is None:
                raise ValueError("failed to build a complete Krylov basis")
            for i, value in enumerate(coord):
                action._matrix[i][j] = value
        return KrylovBlockForm(transform, action, block_ranges)

    def pow_by_frobenius_form(self, form: FrobeniusForm, k: int) -> 'LinearAlgebraFp':
        """
        Compute matrix power from a supplied Frobenius form.

        Args:
            form: Frobenius form for this matrix under the current modulus.
                The caller guarantees A P = P F and that the block polynomials
                describe F; these identities are not recomputed here.
            k: Exponent (non-negative)

        Returns:
            Matrix raised to power k.

        Raises:
            ValueError: If the matrix is not square, form dimensions are
                incompatible, k is negative, block polynomials are invalid,
                or the transform is singular.
            NotImplementedError: If the modulus is not prime.

        Time Complexity:
            O(n**3 + sum(M(deg(f_i)) log(k + 1))).
        """
        if not self.is_square():
            raise ValueError('not a square matrix')
        if not self._is_prime:
            raise NotImplementedError('not implemented for non-prime moduli')
        if k < 0:
            raise ValueError("negative exponent is not supported")
        if form.transform._n != self._n or form.transform._m != self._n:
            raise ValueError("incompatible Frobenius form")
        if form.frobenius._n != self._n or form.frobenius._m != self._n:
            raise ValueError('incompatible Frobenius form')
        frobenius_power = type(self).block_companion_power(form.polynomials, k)
        if frobenius_power._n != self._n:
            raise ValueError("incompatible Frobenius form")
        return form.transform * frobenius_power * ~form.transform

    def submatrix(self, i: int, j: int) -> 'LinearAlgebraFp':
        """
        Extract submatrix by removing row i and column j.

        Args:
            i: Row index to remove
            j: Column index to remove

        Returns:
            LinearAlgebraFp: (n-1) × (m-1) submatrix

        Raises:
            ValueError: If indices are out of range

        Time Complexity:
            ``O(nm)``
        """
        if i < 0 or i >= self._n or j < 0 or j >= self._m:
            raise ValueError("out of range")
        sub_array = [[self._matrix[r][c] for c in range(self._m) if c != j] for r in range(self._n) if r != i]
        return type(self)(self._n - 1, self._m - 1, from_array=sub_array)

    def minor(self, i: int, j: int) -> int:
        """
        Compute minor determinant by removing row i and column j.

        Args:
            i: Row index to remove
            j: Column index to remove

        Returns:
            int: Determinant of the (n-1) × (n-1) submatrix

        Raises:
            ValueError: If indices are out of range or the matrix is not square.

        Notes:
            Minor M_ij is the determinant of the submatrix obtained
            by deleting row i and column j.

        Time Complexity:
            ``O(n^3)``
        """
        return self.submatrix(i, j).determinant()

    def cofactor(self, i: int, j: int) -> int:
        """
        Compute cofactor C_ij = (-1)^(i+j) * M_ij.

        Args:
            i: Row index
            j: Column index

        Returns:
            int: Cofactor value modulo _mod

        Raises:
            ValueError: If indices are out of range or the matrix is not square.

        Notes:
            Cofactor is the signed minor: C_ij = (-1)^(i+j) * M_ij
            where M_ij is the minor determinant.

        Time Complexity:
            ``O(n^3)``
        """
        sign = -1 if ((i + j) & 1) else 1
        return self.minor(i, j) * sign % self._mod

    def adjugate(self) -> 'LinearAlgebraFp':
        """
        Compute adjugate (classical adjoint) matrix.

        Returns:
            Adjugate matrix such that A * adj(A) = det(A) * I

        Raises:
            ValueError: If matrix is not square
            NotImplementedError: If modulus is not prime

        Notes:
            Optimized algorithm that avoids computing all cofactors.

        Time Complexity:
            ``O(n^3)``
        """
        if not self.is_square():
            raise ValueError("adjugate is only defined for square matrices")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        n = self._n
        r = self.rank()
        if r <= n - 2:
            return type(self)(n, n)
        if r == n:
            detA = self.determinant()
            return (~self).times(detA)
        kernel: list[list[int]] = self.linear_equations([0] * n).basis_vectors
        u = kernel[0]
        transpose_kernel: list[list[int]] = self.transpose().linear_equations([0] * n).basis_vectors
        v = transpose_kernel[0]
        i0 = next(i for i, ui in enumerate(u) if ui % self._mod != 0)
        j0 = next(j for j, vj in enumerate(v) if vj % self._mod != 0)
        inv_uv = pow(u[i0] * v[j0] % self._mod, self._mod - 2, self._mod)
        alpha = self.cofactor(j0, i0) * inv_uv % self._mod
        ret = type(self)(n, n)
        for i in range(n):
            for j in range(n):
                ret[i, j] = alpha * u[i] * v[j] % self._mod
        return ret

    def hafnian(self) -> int:
        """
        Compute the weighted sum over perfect matchings of a symmetric matrix.

        Time Complexity:
            - ``O((n / 2)^4 2^{n/2})`` in the worst case

        Returns:
            Hafnian modulo the current modulus. Odd-sized matrices give 0;
            the empty matrix gives 1 modulo the modulus. Diagonal entries are
            ignored because matchings pair distinct indices. The input is unchanged.

        Raises:
            ValueError: If the matrix is not square or is not symmetric modulo
                the current modulus.

        Space Complexity:
            O(n**4) in the worst case for the explicit stack of polynomial matrices.

        Notes:
            This division-free method also works for composite moduli. It uses Bjorklund's algorithm on a polynomial-lifted
            lower-triangular representation. The traversal is implemented with
            an explicit stack to avoid recursive calls on PyPy.

        """
        if not self.is_square():
            raise ValueError("hafnian is only defined for square matrices")
        for i in range(self._n):
            for j in range(i):
                if (self._matrix[i][j] - self._matrix[j][i]) % self._mod:
                    raise ValueError('hafnian requires a symmetric matrix')
        n2 = self._n
        if n2 & 1:
            return 0
        n = n2 // 2
        mod = self._mod

        b: list[list[int]] = [[0] * (n + 1) for _ in range(n * (2 * n - 1))]
        for j in range(1, n2):
            base = j * (j - 1) // 2
            row = self._matrix[j]
            for k in range(j):
                b[base + k][0] = row[k] % mod

        g = [0] * (n + 1)
        g[0] = 1 % mod

        class HafnianFrame:
            __slots__ = ('poly_mat', 'size', 'sign', 'g', 'state', 'c', 'first')

            def __init__(self, poly_mat: list[list[int]], size: int, sign: int, g: list[int]) -> None:
                self.poly_mat = poly_mat
                self.size = size
                self.sign = sign
                self.g = g
                self.state = 0
                self.c: list[list[int]] | None = None
                self.first = 0

        stack = [HafnianFrame(b, n2, 1, g)]
        result = 0
        while stack:
            frame = stack[-1]
            poly_mat = frame.poly_mat
            size = frame.size
            sign = frame.sign
            g = frame.g
            if size == 0:
                result = g[n] if sign > 0 else (-g[n]) % mod
                stack.pop()
                continue
            if frame.state == 0:
                next_size = size - 2
                c: list[list[int]] = [[0] * (n + 1) for _ in range(next_size * (next_size - 1) // 2)]
                idx = 0
                for j in range(1, next_size):
                    src = (j + 1) * (j + 2) // 2 + 2
                    for k in range(j):
                        c[idx][:] = poly_mat[src + k]
                        idx += 1
                frame.state = 1
                frame.c = c
                stack.append(HafnianFrame(c, next_size, -sign, g))
            elif frame.state == 1:
                if frame.c is None:
                    raise RuntimeError("invalid hafnian stack frame")
                c = frame.c
                frame.first = result
                next_size = size - 2
                e = g[:]
                b0 = poly_mat[0]
                for u in range(n):
                    gu = g[u]
                    if gu == 0:
                        continue
                    for v in range(n - u):
                        e[u + v + 1] += gu * b0[v]
                for i in range(1, n + 1):
                    e[i] %= mod

                for j in range(1, next_size):
                    j0 = (j + 1) * (j + 2) // 2
                    poly_j0 = poly_mat[j0]
                    poly_j1 = poly_mat[j0 + 1]
                    dst = j * (j - 1) // 2
                    for k in range(j):
                        target = c[dst + k]
                        k0 = (k + 1) * (k + 2) // 2
                        poly_k0 = poly_mat[k0]
                        poly_k1 = poly_mat[k0 + 1]
                        for u in range(n):
                            a = poly_j0[u]
                            b_ = poly_k0[u]
                            if a == 0 and b_ == 0:
                                continue
                            for v in range(n - u):
                                target[u + v + 1] += a * poly_k1[v] + b_ * poly_j1[v]
                        for i in range(1, n + 1):
                            target[i] %= mod
                frame.state = 2
                stack.append(HafnianFrame(c, next_size, sign, e))
            else:
                result = (frame.first + result) % mod
                stack.pop()
        return result


class SparseMatrixMod:
    """
    Sparse matrix with modular arithmetic.

    Rows are stored as sorted ``(column, value)`` pairs, which makes the class
    suitable for black-box linear algebra on large sparse matrices.

    Attributes:
        _mod: Modulus for arithmetic operations.
        _is_prime: Whether the modulus is prime.
        _n: Number of rows.
        _m: Number of columns.
        _rows: Sparse rows stored as sorted ``(column, value)`` pairs.
        _nnz: Number of non-zero entries.

    Notes:
        Only prime moduli are supported. ``determinant`` and polynomial
        routines use randomized algorithms.

    Space Complexity:
        ``O(n + nnz)``

    Complexity Notation:
        ``n`` and ``m`` are the numbers of rows and columns, ``nnz`` is the
        number of non-zero entries, ``e`` is the number of input coordinate
        entries, and ``R`` is ``max_retry`` for randomized methods.
    """

    _mod = 998244353
    _is_prime = True

    def __init__(self, n: int, m: int, entries: Sequence[tuple[int, int, int]] | None = None) -> None:
        """Create an ``n`` by ``m`` sparse matrix.

        Args:
            n: Number of rows.
            m: Number of columns.
            entries: Optional ``(row, column, value)`` triples to preload.

        Returns:
            None.

        Raises:
            ValueError: If a dimension is negative or an entry is out of bounds.

        Time Complexity:
            ``O(n)`` without ``entries`` and ``O(n + e log e)`` with entries.
        """
        if n < 0 or m < 0:
            raise ValueError('matrix dimensions must be non-negative')
        self._n = n
        self._m = m
        self._rows: list[list[tuple[int, int]]] = [[] for _ in range(n)]
        self._nnz = 0
        if entries is not None:
            self._build_from_entries(entries)

    def _build_from_entries(self, entries: Sequence[tuple[int, int, int]]) -> None:
        rows = [dict[int, int]() for _ in range(self._n)]
        for i, j, value in entries:
            if not (0 <= i < self._n and 0 <= j < self._m):
                raise ValueError("index out of range")
            value %= self._mod
            if value == 0:
                continue
            rows[i][j] = (rows[i].get(j, 0) + value) % self._mod
            if rows[i][j] == 0:
                del rows[i][j]
        self._rows = []
        self._nnz = 0
        for row in rows:
            sparse_row = sorted(row.items())
            self._rows.append(sparse_row)
            self._nnz += len(sparse_row)

    @classmethod
    def from_edges(cls, n: int, m: int, entries: Sequence[tuple[int, int, int]]) -> SparseMatrixMod:
        """
        Construct a sparse matrix from coordinate entries.

        Args:
            n: Number of rows.
            m: Number of columns.
            entries: Sparse matrix entries.

        Returns:
            A new n by m matrix. Duplicate entries are summed modulo the
            current modulus, and entries that become zero are omitted.

        Time Complexity:
            ``O(n + e log e)``, where ``e = len(entries)``.
        """
        return cls(n, m, entries)

    @classmethod
    def set_mod(cls, mod: int, primality_check: bool = True) -> None:
        """Set the prime modulus shared by all instances of this class.

        Args:
            mod: Prime modulus greater than 1.
            primality_check: Whether to explicitly check primality. If False,
                the caller guarantees it; the FPS helper may also validate it.

        Returns:
            None. Also aligns the shared FormalPowerSeriesMod setting.

        Raises:
            ValueError: If the modulus is invalid. This class's old setting is
                preserved when validation or FPS initialization fails.

        Time Complexity:
            Primality testing plus FPS modulus initialization when it differs.
            Primality is deterministic below 2**64 and probabilistic above it.
        """
        if mod < 2 or (primality_check and not PrimeFactor.is_prime(mod)):
            raise ValueError('mod must be prime')
        if FormalPowerSeriesMod.get_mod() != mod:
            FormalPowerSeriesMod.set_mod(mod)
        cls._mod = mod
        cls._is_prime = True

    def get_mod(self) -> int:
        """
        Return the current modulus.

        Returns:
            The modulus shared by instances of this class.

        Time Complexity:
            O(1)
        """
        return self._mod

    def is_square(self) -> bool:
        """
        Return whether the sparse matrix is square.

        Returns:
            True if the row and column counts are equal, otherwise False.

        Time Complexity:
            O(1)
        """
        return self._n == self._m

    def nnz(self) -> int:
        """
        Return the number of non-zero entries currently stored.

        Returns:
            Number of stored non-zero entries after combining duplicates.

        Time Complexity:
            O(1)
        """
        return self._nnz

    def to_dense(self) -> MatrixMod:
        """
        Convert the sparse matrix into a dense ``MatrixMod`` instance.

        Returns:
            A dense matrix with the same entries and modulus.

        Notes:
            Aligns MatrixMod's shared modulus with this matrix, affecting existing
            MatrixMod instances as for MatrixMod.set_mod().

        Time Complexity:
            ``O(nm + nnz)``
        """
        mat = MatrixMod(self._n, self._m)
        if mat.get_mod() != self._mod:
            MatrixMod.set_mod(self._mod, primality_check=False)
        for i, row in enumerate(self._rows):
            for j, value in row:
                mat[i, j] = value
        return mat

    def matvec(self, vector: Sequence[int], row_scale: Sequence[int] | None = None) -> list[int]:
        """
        Compute the matrix-vector product ``A @ vector``.

        Args:
            vector: Column vector to multiply from the right.
            row_scale: Optional diagonal row scaling. When provided, this
                computes ``diag(row_scale) @ A @ vector``.

        Returns:
            The vector ``A @ vector`` modulo ``_mod``.

        Time Complexity:
            ``O(nnz + n)``
        """
        if len(vector) != self._m:
            raise ValueError("incompatible dimensions")
        if row_scale is not None and len(row_scale) != self._n:
            raise ValueError("incompatible dimensions")
        res = [0] * self._n
        for i, row in enumerate(self._rows):
            value = 0
            for j, coeff in row:
                value += coeff * vector[j]
            if row_scale is not None:
                value *= row_scale[i]
            res[i] = value % self._mod
        return res

    def transpose_matvec(self, vector: Sequence[int]) -> list[int]:
        """
        Compute the transposed matrix-vector product ``A^T @ vector``.

        This is useful for black-box linear algebra routines that need the
        action of both the matrix and its transpose, such as Wiedemann- or
        Lanczos-style solvers.

        Args:
            vector: Column vector to multiply by ``A^T``.

        Returns:
            The vector ``A^T @ vector`` modulo ``_mod``.

        Time Complexity:
            ``O(nnz + n + m)``
        """
        if len(vector) != self._n:
            raise ValueError("incompatible dimensions")
        res = [0] * self._m
        for i, row in enumerate(self._rows):
            vector_i = vector[i] % self._mod
            if vector_i == 0:
                continue
            for j, coeff in row:
                res[j] += coeff * vector_i
                res[j] %= self._mod
        return res

    @staticmethod
    def _random_vector(length: int, rng: SystemRandom, mod: int) -> list[int]:
        return [rng.randrange(mod) for _ in range(length)]

    def scalar_sequence(self, left: Sequence[int], right: Sequence[int], length: int, row_scale: Sequence[int] | None = None) -> list[int]:
        """
        Enumerate the scalar Krylov sequence ``left^T (B^i) right``.

        Here ``B`` is the matrix itself, or the row-scaled matrix
        ``diag(row_scale) @ A`` when ``row_scale`` is provided.

        Args:
            left: Row vector used on the left.
            right: Initial column vector.
            length: Non-negative number of terms to generate.
            row_scale: Optional diagonal row scaling applied before each
                matrix-vector multiplication.

        Returns:
            The sequence
            ``[left^T right, left^T B right, ..., left^T B^(length-1) right]``.

        Raises:
            ValueError: If dimensions differ, the matrix is not square, or length
                is negative. Row scaling is validated even for length zero.

        Time Complexity:
            O(length * (nnz + n + 1) + 1).

        Space Complexity:
            O(length + n).
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if len(left) != self._n or len(right) != self._n:
            raise ValueError("incompatible dimensions")
        if length < 0:
            raise ValueError('length must be non-negative')
        if row_scale is not None and len(row_scale) != self._n:
            raise ValueError('incompatible dimensions')
        if length == 0:
            return []
        cur = [x % self._mod for x in right]
        seq = [0] * length
        for i in range(length):
            seq[i] = sum(x * y for x, y in zip(left, cur)) % self._mod
            if i + 1 < length:
                cur = self.matvec(cur, row_scale=row_scale)
        return seq

    def _polynomial_action(self, coefficients: Sequence[int], vector: Sequence[int]) -> list[int]:
        """Evaluate ascending-degree coefficients at A on vector using Horner's rule."""
        if not coefficients:
            return [0] * self._n
        result = [coefficients[-1] * x % self._mod for x in vector]
        for coefficient in reversed(coefficients[:-1]):
            result = self.matvec(result)
            coefficient %= self._mod
            if coefficient:
                for i, value in enumerate(vector):
                    result[i] = (result[i] + coefficient * value) % self._mod
        return result

    def _verify_annihilating_polynomial(self, vector: Sequence[int], coeffs: Sequence[int]) -> bool:
        if not coeffs or coeffs[0] % self._mod != 1:
            return False
        result = self._polynomial_action(list(reversed(coeffs)), vector)
        return not any(result)

    def annihilating_polynomial(self, vector: Sequence[int], *, max_retry: int = 8) -> list[int]:
        """
        Compute a monic polynomial that annihilates the Krylov orbit of ``vector``.

        The returned coefficients are in descending-degree order:

        ``[1, c_1, ..., c_d]``

        and they satisfy

        ``A^d v + c_1 A^(d-1) v + ... + c_d v = 0``.

        This order matches the output of Berlekamp-Massey and is convenient
        for internal black-box linear algebra routines. If you want the usual
        polynomial coefficient order ``[c_0, c_1, ..., c_d]`` representing
        ``c_0 + c_1 x + ... + c_d x^d``, use
        :meth:`vector_minimum_polynomial` instead.

        Args:
            vector: Starting vector of the Krylov orbit.
            max_retry: Non-negative maximum number of random projections to try.

        Returns:
            Normalized descending-degree coefficients of the vector's monic
            minimum polynomial. A zero vector gives [1]. Inputs are not changed.

        Raises:
            ValueError: If dimensions differ, the matrix is not square,
                max_retry is negative, or no certified polynomial is recovered.
                Zero trials succeed only for a zero vector.

        Notes:
            Combines projection factors by their LCM and stops after a candidate
            is certified on vector. An unsuccessful random projection never
            causes an incorrect polynomial to be returned.

        Time Complexity:
            O(R n (nnz + n) + R M(n) log(n + 1)) in the worst case, with earlier
            termination on success. M(n) is polynomial multiplication cost.

        Space Complexity:
            O(n log(n + 1)), including polynomial GCD workspace.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if len(vector) != self._n:
            raise ValueError("incompatible dimensions")
        if max_retry < 0:
            raise ValueError('max_retry must be non-negative')
        if all(x % self._mod == 0 for x in vector):
            return [1]
        if FormalPowerSeriesMod.get_mod() != self._mod:
            FormalPowerSeriesMod.set_mod(self._mod)
        rng = SystemRandom()
        best = [1]
        for _ in range(max_retry):
            left = self._random_vector(self._n, rng, self._mod)
            seq = self.scalar_sequence(left, vector, 2 * self._n + 1)
            candidate = list(reversed(berlekamp_massey(seq)))
            combined = self._polynomial_lcm_low(best, candidate)
            if len(combined) == len(best):
                continue
            best = combined
            descending = list(reversed(best))
            if len(best) == self._n + 1 or self._verify_annihilating_polynomial(vector, descending):
                return descending
        raise ValueError('failed to find an annihilating polynomial; increase max_retry')

    @classmethod
    def _trim_polynomial_low(cls, coeffs: Sequence[int]) -> list[int]:
        res = [c % cls._mod for c in coeffs]
        while len(res) > 1 and res[-1] == 0:
            res.pop()
        if len(res) == 0:
            return [0]
        return res

    @classmethod
    def _normalize_monic_polynomial_low(cls, coeffs: Sequence[int]) -> list[int]:
        res = cls._trim_polynomial_low(coeffs)
        if len(res) == 1 and res[0] == 0:
            return [0]
        inv = pow(res[-1], -1, cls._mod)
        return [(c * inv) % cls._mod for c in res]

    @classmethod
    def _polynomial_lcm_low(cls, left: Sequence[int], right: Sequence[int]) -> list[int]:
        left = cls._trim_polynomial_low(left)
        right = cls._trim_polynomial_low(right)
        if (len(left) == 1 and left[0] == 0) or (len(right) == 1 and right[0] == 0):
            return [0]
        gcd_poly = FormalPowerSeriesMod(left).gcd(FormalPowerSeriesMod(right))
        lcm_poly = (
            (FormalPowerSeriesMod(left) // gcd_poly)
            * FormalPowerSeriesMod(right)
        ).coef
        return cls._normalize_monic_polynomial_low(lcm_poly)

    def vector_minimum_polynomial(
        self,
        vector: Sequence[int],
        *,
        max_retry: int = 8,
    ) -> list[int]:
        """
        Compute the minimum polynomial of the Krylov sequence generated by ``vector``.

        This returns the monic polynomial ``m(x)`` of smallest degree such that
        ``m(A) @ vector = 0``.

        The coefficients are returned in the usual ascending-degree order:

        ``[c_0, c_1, ..., c_d]`` representing ``c_0 + c_1 x + ... + c_d x^d``.

        For example, ``[0, 1]`` means ``m(x) = x``.

        Args:
            vector: Starting vector of the Krylov orbit.
            max_retry: Number of random projections to try.

        Returns:
            Normalized ascending-degree coefficients, or [1] for a zero vector.

        Raises:
            ValueError: Under the same conditions as annihilating_polynomial.

        Time Complexity:
            Same as :meth:`annihilating_polynomial`.
        """
        return list(reversed(self.annihilating_polynomial(vector, max_retry=max_retry)))

    def minimum_polynomial(self, *, max_retry: int = 8) -> list[int]:
        """
        Compute the minimum polynomial of the whole matrix.

        This returns the monic polynomial ``m(x)`` of smallest degree such that
        ``m(A) = 0`` as a linear operator.

        The coefficients are returned in ascending-degree order:

        ``[c_0, c_1, ..., c_d]`` representing ``c_0 + c_1 x + ... + c_d x^d``.

        Internally this is a randomized black-box algorithm. Each random
        projection yields a factor of the true minimum polynomial, and this
        method takes the least common multiple of the recovered factors. A
        degree-n candidate is already certified. A lower-degree candidate is
        checked on every coordinate vector before it can be returned; degree-one
        candidates are checked directly against the sparse entries.

        Args:
            max_retry: Non-negative maximum number of random projections to try.

        Returns:
            Normalized ascending-degree coefficients of the monic minimum
            polynomial. The empty matrix gives [1]. The matrix is unchanged.

        Raises:
            ValueError: If the matrix is not square, max_retry is negative, or
                the trials do not recover a candidate that annihilates A.
                Zero trials succeed only for the empty matrix.

        Time Complexity:
            O(R n (nnz + n) + R M(n) log(n + 1)) for candidate generation,
            where M(n) is polynomial multiplication cost. For candidate degree
            1 < d < n, certification adds O(n d (nnz + n)); for d = 1 it adds
            O(nnz + n). No extra certification is needed for d = n.

        Space Complexity:
            O(n log(n + 1)), including polynomial GCD workspace.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if max_retry < 0:
            raise ValueError('max_retry must be non-negative')
        if self._n == 0:
            return [1]
        if FormalPowerSeriesMod.get_mod() != self._mod:
            FormalPowerSeriesMod.set_mod(self._mod)
        rng = SystemRandom()
        minpoly = [1]
        for _ in range(max_retry):
            left = self._random_vector(self._n, rng, self._mod)
            right = self._random_vector(self._n, rng, self._mod)
            candidate = list(reversed(berlekamp_massey(
                self.scalar_sequence(left, right, 2 * self._n + 1)
            )))
            minpoly = self._polynomial_lcm_low(minpoly, candidate)
            if len(minpoly) - 1 == self._n:
                return minpoly
        # Projection polynomials divide the true minimum polynomial. Certifying
        # that their LCM annihilates A proves equality, without a probabilistic error.
        if len(minpoly) == 1:
            raise ValueError('failed to recover the minimum polynomial; increase max_retry')
        if len(minpoly) == 2:
            for i, row in enumerate(self._rows):
                diagonal = minpoly[0]
                for j, value in row:
                    if i == j:
                        diagonal += value
                    elif value % self._mod:
                        raise ValueError('failed to recover the minimum polynomial; increase max_retry')
                if diagonal % self._mod:
                    raise ValueError('failed to recover the minimum polynomial; increase max_retry')
        else:
            vector = [0] * self._n
            descending = list(reversed(minpoly))
            for i in range(self._n):
                vector[i] = 1
                if not self._verify_annihilating_polynomial(vector, descending):
                    raise ValueError('failed to recover the minimum polynomial; increase max_retry')
                vector[i] = 0
        return minpoly

    @classmethod
    def _polynomial_pow_x_mod(cls, k: int, coeffs: Sequence[int]) -> list[int]:
        degree = len(coeffs) - 1
        if degree == 0:
            return [0]
        if FormalPowerSeriesMod.get_mod() != cls._mod:
            FormalPowerSeriesMod.set_mod(cls._mod)
        mod_poly = FormalPowerSeriesMod(list(reversed(coeffs)))
        return FormalPowerSeriesMod([0, 1]).pow_mod(k, mod_poly).resize(degree).coef

    def apply_polynomial_to_vector(
        self,
        polynomial: Sequence[int],
        vector: Sequence[int],
        *,
        vector_minimum_polynomial: Sequence[int] | None = None,
    ) -> list[int]:
        """
        Compute ``f(A) @ vector`` for a polynomial ``f``.

        Args:
            polynomial: Coefficients ``[c_0, c_1, ..., c_d]`` representing
                ``f(x) = c_0 + c_1 x + ... + c_d x^d``.
            vector: Column vector to which the polynomial of the matrix is
                applied.
            vector_minimum_polynomial: Optional minimum polynomial of the
                Krylov sequence generated by ``vector`` in ascending-degree
                order. Supplying it avoids recomputation when applying several
                polynomials to the same vector. A nonzero scalar multiple or
                another annihilating polynomial also works; it is normalized and
                checked against vector before use.

        Returns:
            The vector ``f(A) @ vector`` modulo ``_mod``.

        Notes:
            The polynomial is first reduced modulo the minimum polynomial of
            ``vector``. This keeps the computation in the Krylov subspace
            spanned by ``vector, A vector, A^2 vector, ...``.

        Raises:
            ValueError: If dimensions differ, the matrix is not square, or a
                supplied relation is zero or does not annihilate vector. An
                internally computed relation can also fail to be recovered.

        Time Complexity:
            With a supplied relation of degree d and L input coefficients,
            O(M(max(L, d)) + d (nnz + n)), including validation. Without a
            supplied relation, add vector_minimum_polynomial's cost; constant
            polynomials need no relation and use O(n) time.

        Space Complexity:
            O(n + L + d) with a supplied relation. No Krylov basis is stored.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if len(vector) != self._n:
            raise ValueError("incompatible dimensions")
        minpoly: list[int] | None = None
        if vector_minimum_polynomial is not None:
            minpoly = self._normalize_monic_polynomial_low(vector_minimum_polynomial)
            if not self._verify_annihilating_polynomial(vector, list(reversed(minpoly))):
                raise ValueError('invalid vector minimum polynomial')
        poly = self._trim_polynomial_low(polynomial)
        if len(poly) == 1:
            return [poly[0] * x % self._mod for x in vector]
        if minpoly is None:
            minpoly = self.vector_minimum_polynomial(vector)
        if len(minpoly) == 1:
            return [0] * self._n
        if FormalPowerSeriesMod.get_mod() != self._mod:
            FormalPowerSeriesMod.set_mod(self._mod)
        reduced = self._trim_polynomial_low(
            (FormalPowerSeriesMod(poly) % FormalPowerSeriesMod(minpoly)).coef
        )
        return self._polynomial_action(reduced, vector)

    def pow_vec(self, k: int, vector: Sequence[int], *, annihilating_polynomial: Sequence[int] | None = None) -> list[int]:
        """
        Compute ``A^k @ vector`` without materializing dense matrix powers.

        The method first finds a polynomial relation among
        ``vector, A vector, A^2 vector, ...`` and then reduces ``x^k`` modulo
        that relation. This is much faster than repeated multiplication when
        ``k`` is large.

        Args:
            k: Non-negative exponent.
            vector: Column vector multiplied by ``A^k``.
            annihilating_polynomial: Optional descending-degree coefficients
                ``[1, c_1, ..., c_d]`` satisfying
                ``A^d v + c_1 A^(d-1) v + ... + c_d v = 0``. Supplying it
                avoids recomputation when calling this method repeatedly for the
                same vector. Coefficients must have leading residue 1. The
                relation is checked for k > 0 and ignored for k = 0.

        Returns:
            The vector ``A^k @ vector`` modulo ``_mod``.

        Raises:
            ValueError: If dimensions differ, the matrix is not square, k is
                negative, or the supplied relation is not monic or does not
                annihilate vector. Random relation recovery can also fail.

        Time Complexity:
            With a supplied relation of degree d and k > 0,
            O(M(d) log(k + 1) + d (nnz + n)), including validation.
            Otherwise add annihilating_polynomial's cost. Exponent zero is O(n).

        Space Complexity:
            O(n + d) with a supplied relation. No Krylov basis is stored.
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if len(vector) != self._n:
            raise ValueError("incompatible dimensions")
        if k < 0:
            raise ValueError("k must be non-negative")
        if k == 0:
            return [x % self._mod for x in vector]
        if annihilating_polynomial is None:
            coeffs = self.annihilating_polynomial(vector)
        else:
            coeffs = [c % self._mod for c in annihilating_polynomial]
            if not self._verify_annihilating_polynomial(vector, coeffs):
                raise ValueError('invalid annihilating polynomial')
        degree = len(coeffs) - 1
        if degree == 0:
            return [0] * self._n
        if k < degree:
            cur = [x % self._mod for x in vector]
            for _ in range(k):
                cur = self.matvec(cur)
            return cur
        coef = self._polynomial_pow_x_mod(k, coeffs)
        return self._polynomial_action(coef, vector)

    def determinant(self, *, max_retry: int = 8) -> int:
        """
        Compute the determinant of a sparse square matrix.

        This is a randomized black-box algorithm. It multiplies the matrix by a
        random non-singular diagonal matrix, recovers the characteristic
        polynomial of the preconditioned matrix through Berlekamp-Massey on a
        scalar Krylov sequence, and then removes the effect of the diagonal
        scaling.

        Returns:
            ``det(A)`` modulo ``_mod``.

        Args:
            max_retry: Non-negative maximum number of random projections to try.

        Raises:
            ValueError: If the matrix is not square, max_retry is negative, or
                the trials do not recover the determinant. Over small fields,
                diagonal preconditioning may fail for every trial.
            NotImplementedError: If the modulus is not prime.

        Time Complexity:
            ``O(R n (nnz + n))``
        """
        if not self.is_square():
            raise ValueError("not a square matrix")
        if not self._is_prime:
            raise NotImplementedError("not implemented for non-prime moduli")
        if max_retry < 0:
            raise ValueError('max_retry must be non-negative')
        if self._n == 0:
            return 1
        if FormalPowerSeriesMod.get_mod() != self._mod:
            FormalPowerSeriesMod.set_mod(self._mod)
        rng = SystemRandom()
        for _ in range(max_retry):
            row_scale = [rng.randrange(1, self._mod) for _ in range(self._n)]
            left = self._random_vector(self._n, rng, self._mod)
            right = self._random_vector(self._n, rng, self._mod)
            coeffs = berlekamp_massey(
                self.scalar_sequence(left, right, 2 * self._n + 1, row_scale=row_scale)
            )
            if coeffs[-1] == 0:
                return 0
            if len(coeffs) != self._n + 1:
                continue
            det = coeffs[-1]
            if self._n & 1:
                det = (-det) % self._mod
            scale_prod = 1
            for value in row_scale:
                scale_prod *= value
                scale_prod %= self._mod
            return det * pow(scale_prod, -1, self._mod) % self._mod
        raise ValueError("failed to recover determinant; increase max_retry")


class BitSet:
    """
    Bitset backed by packed machine words.

    The structure stores ``n`` booleans in a compact integer array and exposes
    set-like operations for membership, insertion, removal, and bitwise
    combination.

    Attributes:
        bit_size: Number of bits per machine word.
        n: Number of tracked bits.
        data: Packed words storing the bitset contents.

    Notes:
        The universe is the integer indices 0 <= x < n. len(bits) counts set
        bits; bits.n is the logical length. Negative indices do not wrap.
        Bitwise operations accept different block widths but require equal n.

    Space Complexity:
        O(ceil(n / word_size) + 1) packed words.

    Complexity Notation:
        ``word_size`` is the number of bits in each packed word.
    """
    def __init__(self, n: int, bit_size: int = 63):
        """Create an empty bitset with logical length n.

        Args:
            n: Non-negative size of the index universe.
            bit_size: Positive number of bits per storage block; defaults to 63.

        Returns:
            None.

        Raises:
            ValueError: If n is negative or bit_size is not positive.

        Time Complexity:
            O(ceil(n / bit_size) + 1).
        """
        if n < 0 or bit_size <= 0:
            raise ValueError('n must be non-negative and bit_size must be positive')
        self.bit_size = bit_size
        self.n = n
        self.data = [0] * ((n + bit_size - 1) // bit_size)

    def add(self, x: int) -> None:
        """
        Set bit ``x``.

        Args:
            x: Index in [0, n).

        Returns:
            None. Setting an already set bit has no effect.

        Raises:
            ValueError: If x is outside [0, n).

        Time Complexity:
            O(1)
        """
        if not 0 <= x < self.n:
            raise ValueError('bit index out of range')
        self.data[x // self.bit_size] |= 1 << (x % self.bit_size)

    def discard(self, x: int) -> None:
        """
        Clear bit ``x``.

        Args:
            x: Index to clear; indices outside [0, n) are treated as absent.

        Returns:
            None. Clearing an absent bit has no effect.

        Time Complexity:
            O(1)
        """
        if 0 <= x < self.n:
            self.data[x // self.bit_size] &= ~(1 << (x % self.bit_size))

    def __setitem__(self, x: int, v: bool) -> None:
        """Assign a bit by index.

        Args:
            x: Index in [0, n); negative indices do not wrap.
            v: Whether to set the bit.

        Returns:
            None.

        Raises:
            IndexError: If x is outside [0, n).

        Time Complexity:
            O(1) for fixed block width.
        """
        if not 0 <= x < self.n:
            raise IndexError('bit index out of range')
        if v:
            self.data[x // self.bit_size] |= 1 << (x % self.bit_size)
        else:
            self.data[x // self.bit_size] &= ~(1 << (x % self.bit_size))

    def __copy__(self) -> 'BitSet':
        """Return an independent copy with the same logical length and block width.

        Returns:
            Copy of this bitset.

        Time Complexity:
            O(ceil(n / bit_size) + 1).
        """
        ret = type(self)(self.n, self.bit_size)
        ret.data = self.data[:]
        return ret

    def __contains__(self, x: int) -> bool:
        """Check membership in the set of bit indices.

        Args:
            x: Integer index to query.

        Returns:
            True if x is set, or False if unset or outside [0, n).

        Time Complexity:
            O(1) for fixed block width.
        """
        return 0 <= x < self.n and bool(self.data[x // self.bit_size] & (1 << (x % self.bit_size)))

    def __getitem__(self, x: int) -> bool:
        """Read a bit by index.

        Args:
            x: Index in [0, n); negative indices do not wrap.

        Returns:
            Whether the bit is set.

        Raises:
            IndexError: If x is outside [0, n).

        Time Complexity:
            O(1) for fixed block width.
        """
        if not 0 <= x < self.n:
            raise IndexError('bit index out of range')
        return bool(self.data[x // self.bit_size] & (1 << (x % self.bit_size)))

    def __len__(self) -> int:
        """Return the number of set bits.

        Returns:
            Number of distinct indices currently present.

        Time Complexity:
            O(n / bit_size + 1) for a fixed word size.

        Examples:
            >>> bits = BitSet(64)
            >>> bits.add(8)
            >>> len(bits)
            1
        """
        return sum(x.bit_count() for x in self.data)

    def __xor__(self, other: 'BitSet') -> 'BitSet':
        """Return the symmetric difference of two bitsets.

        Args:
            other: Bitset with the same logical length; block widths may differ.

        Returns:
            New bitset with this bitset's block width. Neither input is modified.

        Raises:
            ValueError: If logical lengths differ.

        Time Complexity:
            O(ceil(n / bit_size) + ceil(n / other.bit_size) + 1) block operations.
        """
        if self.n != other.n:
            raise ValueError('bitsets must have the same logical length')
        right = other.data if self.bit_size == other.bit_size else _repack_bitset(other, self.bit_size).data
        ret = type(self)(self.n, self.bit_size)
        for i in range(len(self.data)):
            ret.data[i] = self.data[i] ^ right[i]
        return ret

    def __and__(self, other: 'BitSet') -> 'BitSet':
        """Return the intersection of two bitsets.

        Args:
            other: Bitset with the same logical length; block widths may differ.

        Returns:
            New bitset with this bitset's block width. Neither input is modified.

        Raises:
            ValueError: If logical lengths differ.

        Time Complexity:
            O(ceil(n / bit_size) + ceil(n / other.bit_size) + 1) block operations.
        """
        if self.n != other.n:
            raise ValueError('bitsets must have the same logical length')
        right = other.data if self.bit_size == other.bit_size else _repack_bitset(other, self.bit_size).data
        ret = type(self)(self.n, self.bit_size)
        for i in range(len(self.data)):
            ret.data[i] = self.data[i] & right[i]
        return ret

    def __str__(self) -> str:
        """Return the bitset as a ``0``/``1`` string."""
        return "".join(str(int(self[i])) for i in range(self.n))


def _repack_bitset(bits: BitSet, bit_size: int) -> BitSet:
    """Copy logical bits into another block width without constructing a giant integer."""
    if bits.bit_size == bit_size:
        return bits.__copy__()
    result = type(bits)(bits.n, bit_size)
    target = 0
    shift = 0
    for i, word in enumerate(bits.data):
        remaining = min(bits.bit_size, bits.n - i * bits.bit_size)
        while remaining:
            take = min(remaining, bit_size - shift)
            result.data[target] |= (word & ((1 << take) - 1)) << shift
            word >>= take
            remaining -= take
            shift += take
            if shift == bit_size:
                target += 1
                shift = 0
    return result


class MatrixBit:
    """
    Matrix class for Mod 2 operations using bit manipulation.

    Optimized for PyPy execution by using BitSet for efficient bit operations.
    Each row is stored as a BitSet, allowing fast row operations using XOR.

    Attributes:
        _n: Number of rows.
        _m: Number of columns.
        _rows: Independent BitSet rows, each with logical length m and 63-bit blocks.

    Notes:
        All operations are performed modulo 2 (GF(2)).
        Optimized for PyPy's JIT compiler with 63-bit chunks.

    Examples:
        >>> A = MatrixBit(3, 3, [[1, 0, 1], [0, 1, 1], [1, 1, 0]])
        >>> B = MatrixBit(3, 3, [[1, 1, 0], [0, 1, 0], [1, 0, 1]])
        >>> C = A * B  # Matrix multiplication in GF(2)
        >>> print(C)
        011
        111
        100

        >>> # Solving linear equations Ax = b in GF(2)
        >>> A = MatrixBit(3, 3, [[1, 0, 1], [0, 1, 1], [1, 1, 0]])
        >>> b = [1, 0, 1]
        >>> dim, sol, basis = A.linear_equations(b)

    Space Complexity:
        O(n * (ceil(m / word_size) + 1)) packed words and row objects.

    Complexity Notation:
        ``word_size`` is the bit width of a packed row block. For matrix
        multiplication, ``p`` is the shared dimension.
    """

    def __init__(self, n: int, m: int, from_array: Sequence[Sequence[int]] | None = None, transposed: bool = False) -> None:
        """Initialize n×m matrix in GF(2).

        Args:
            n: Number of rows
            m: Number of columns
            from_array: Optional 2D array to initialize matrix from (values mod 2)
            transposed: If True, treat from_array as transposed

        Returns:
            None.

        Raises:
            ValueError: If either dimension is negative or the supplied array
                has the wrong shape (m by n when transposed=True).

        Time Complexity:
            O(nm + n) with an input array, otherwise O(n * (ceil(m / 63) + 1)).
        """

        if n < 0 or m < 0:
            raise ValueError('matrix dimensions must be non-negative')
        self._n = n
        self._m = m
        self._rows = [BitSet(m) for _ in range(n)]

        if from_array is not None:
            if not transposed:
                if len(from_array) != n or any(len(row) != m for row in from_array):
                    raise ValueError(f"Incompatible dimensions. Given 2D array is not (n = {n}) × (m = {m}).")
                for i in range(n):
                    for j in range(m):
                        if from_array[i][j] & 1:
                            self._rows[i].add(j)
            else:
                if len(from_array) != m or any(len(row) != n for row in from_array):
                    raise ValueError(f"Incompatible dimensions. Given 2D array is not (m = {m}) × (n = {n}).")
                for i in range(m):
                    for j in range(n):
                        if from_array[i][j] & 1:
                            self._rows[j].add(i)

    @classmethod
    def from_bitset(cls, n: int, m: int, bitsets: Sequence[BitSet]) -> 'MatrixBit':
        """
        Create MatrixBit from a list of BitSet rows.

        Args:
            n: Number of rows
            m: Number of columns
            bitsets: BitSet rows of logical length m. Their block widths may differ.

        Returns:
            Independent matrix with the same bits, repacked into 63-bit blocks.

        Raises:
            ValueError: If dimensions are negative or row lengths/count differ.

        Time Complexity:
            O(n + sum(ceil(m / row.bit_size)) + n * ceil(m / 63)) block operations.
        """
        if len(bitsets) != n or any(bitset.n != m for bitset in bitsets):
            raise ValueError(f"Incompatible dimensions. Expected {n} rows and {m} columns.")
        matrix = cls(n, m)
        matrix._rows = [_repack_bitset(bitset, 63) for bitset in bitsets]
        return matrix

    def __str__(self) -> str:
        """String representation of the matrix."""
        return "\n".join(str(row) for row in self._rows)

    def __getitem__(self, idxs: tuple[int, int]) -> int:
        """Get matrix element at given indices.

        Args:
            idxs: (Row, column) indices. Negative indices wrap as in Python lists.

        Returns:
            int: Matrix element at position [row][column] (0 or 1)

        Raises:
            IndexError: If either index is outside its dimension after wrapping.

        Time Complexity:
            O(1).
        """
        row, column = idxs
        if column < 0:
            column += self._m
        return int(self._rows[row][column])

    def __setitem__(self, idxs: tuple[int, int], value: int) -> None:
        """Set matrix element at given indices.

        Args:
            idxs: (Row, column) indices. Negative indices wrap as in Python lists.
            value: Value to set at position [row][column] (taken mod 2)

        Returns:
            None.

        Raises:
            IndexError: If either index is outside its dimension after wrapping.

        Time Complexity:
            O(1).
        """
        row, column = idxs
        if column < 0:
            column += self._m
        self._rows[row][column] = bool(value & 1)

    def transpose(self) -> 'MatrixBit':
        """
        Compute matrix transpose.

        Returns:
            MatrixBit: Transposed matrix

        Time Complexity:
            ``O(nm)``
        """
        transposed = MatrixBit(self._m, self._n)
        for i in range(self._n):
            for j in range(self._m):
                transposed[j, i] = self[i, j]
        return transposed

    def is_square(self) -> bool:
        """
        Check if the matrix is square (n = m).

        Returns:
            bool: True if the matrix is square, False otherwise

        Time Complexity:
            O(1)
        """
        return self._n == self._m

    def __mul__(self, other: 'MatrixBit') -> 'MatrixBit':
        """Matrix multiplication in GF(2).

        Args:
            other: Right matrix for multiplication

        Returns:
            MatrixBit: Result of matrix multiplication in GF(2)

        Raises:
            ValueError: If dimensions are incompatible

        Time Complexity:
            O(n p (ceil(m / word_size) + 1) + n * (ceil(m / word_size) + 1)) for an ``n x p`` matrix multiplied
            by a ``p x m`` matrix.
        """
        if self._m != other._n:
            raise ValueError("Incompatible dimensions for matrix multiplication")

        result = MatrixBit(self._n, other._m)

        for i in range(self._n):
            result_data = result._rows[i].data
            for k in range(self._m):
                if self._rows[i][k]:
                    for j, word in enumerate(other._rows[k].data):
                        result_data[j] ^= word

        return result

    def rank(self) -> int:
        """
        Compute rank of matrix in GF(2).

        Returns:
            int: Rank of the matrix

        Time Complexity:
            ``O(nm + r n ceil(m / word_size))``, where ``r`` is the rank.
        """
        tmp_rows = [self._rows[i].__copy__() for i in range(self._n)]

        rank = 0
        for col in range(self._m):
            pivot_row = -1
            for row in range(rank, self._n):
                if tmp_rows[row][col]:
                    pivot_row = row
                    break

            if pivot_row == -1: continue

            if pivot_row != rank:
                tmp_rows[pivot_row], tmp_rows[rank] = tmp_rows[rank], tmp_rows[pivot_row]

            for row in range(self._n):
                if row != rank and tmp_rows[row][col]:
                    tmp_rows[row] = tmp_rows[row] ^ tmp_rows[rank]

            rank += 1

        return rank

    def determinant(self) -> int:
        """
        Compute determinant of square matrix in GF(2).

        Returns:
            int: Determinant (0 or 1 in GF(2))

        Raises:
            ValueError: If matrix is not square

        Time Complexity:
            Same as :meth:`rank`.
        """
        if not self.is_square():
            raise ValueError("Determinant is only defined for square matrices")

        # In GF(2), determinant is 1 if matrix is full rank, 0 otherwise
        return 1 if self.rank() == self._n else 0

    def __invert__(self) -> 'MatrixBit':
        """Compute matrix inverse in GF(2).

        Returns:
            MatrixBit: Inverse matrix such that A * A^(-1) = I in GF(2)

        Raises:
            ValueError: If matrix is not square or not invertible

        Time Complexity:
            O(n**2 * (ceil(2 * n / word_size) + 1)).
        """
        if not self.is_square():
            raise ValueError("Inverse is only defined for square matrices")

        n = self._n
        aug_rows: list[BitSet] = []
        for i in range(n):
            row = self._rows[i].__copy__()
            identity_part = BitSet(n)
            identity_part.add(i)
            combined = BitSet(2 * n)
            for j in range(self._m):
                if row[j]:
                    combined.add(j)
            for j in range(n):
                if identity_part[j]:
                    combined.add(n + j)
            aug_rows.append(combined)

        for col in range(n):
            pivot_row = -1
            for row in range(col, n):
                if aug_rows[row][col]:
                    pivot_row = row
                    break

            if pivot_row == -1:
                raise ValueError("Matrix is not invertible")

            if pivot_row != col:
                aug_rows[pivot_row], aug_rows[col] = aug_rows[col], aug_rows[pivot_row]

            for row in range(n):
                if row != col and aug_rows[row][col]:
                    aug_rows[row] = aug_rows[row] ^ aug_rows[col]

        result = MatrixBit(n, n)
        for i in range(n):
            for j in range(n):
                if aug_rows[i][n + j]:
                    result[i, j] = 1

        return result

    def linear_equations(self, b: list[int]) -> LinearEquationResult:
        """
        Solve system of linear equations Ax = b in GF(2).

        Args:
            b: Right-hand side vector (values taken mod 2)

        Returns:
            LinearEquationResult with the dimension, one particular solution,
            and a basis of homogeneous solutions, all with entries 0 or 1.
            It also supports unpacking as (dimension, solution, basis).
            Neither the matrix nor b is modified.

        Raises:
            ValueError: If no solution exists or dimensions incompatible

        Notes:
            General solution is x = particular + sum(c_i * basis[i]) where c_i ∈ {0, 1}

        Time Complexity:
            O(n * (m + 1) + r n ceil((m + 1) / word_size) + (m - r) * m),
            where r is the matrix rank. The final term accounts for the basis.

        Space Complexity:
            O(n * (ceil((m + 1) / word_size) + 1) + (m - r + 1) * m).
        """
        if self._n != len(b):
            raise ValueError("Incompatible dimensions")

        aug_rows: list[BitSet] = []
        for i in range(self._n):
            row = BitSet(self._m + 1)
            for j in range(self._m):
                if self._rows[i][j]:
                    row.add(j)
            if b[i] & 1:
                row.add(self._m)
            aug_rows.append(row)

        pivot_cols: list[int] = []
        free_cols: list[int] = []
        rank = 0

        for col in range(self._m + 1):
            pivot_row = -1
            for row in range(rank, self._n):
                if aug_rows[row][col]:
                    pivot_row = row
                    break

            if pivot_row == -1:
                if col < self._m:
                    free_cols.append(col)
                continue

            if col == self._m:
                raise ValueError("No solution exists")

            pivot_cols.append(col)

            if pivot_row != rank:
                aug_rows[pivot_row], aug_rows[rank] = aug_rows[rank], aug_rows[pivot_row]

            for row in range(self._n):
                if row != rank and aug_rows[row][col]:
                    aug_rows[row] = aug_rows[row] ^ aug_rows[rank]

            rank += 1

        particular = [0] * self._m
        for i in range(rank):
            particular[pivot_cols[i]] = int(aug_rows[i][self._m])

        dim = len(free_cols)
        basis: list[list[int]] = []
        for free_col in free_cols:
            vec = [0] * self._m
            vec[free_col] = 1
            for i in range(rank):
                vec[pivot_cols[i]] = int(aug_rows[i][free_col])
            basis.append(vec)

        return LinearEquationResult(dim, particular, basis)
