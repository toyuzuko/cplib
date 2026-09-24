# cplib.mathematics

`cplib.mathematics` contains number-theoretic and algebraic algorithms.

## Modules

### `arithmetic.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `GaussianInteger` | class | `GaussianInteger(real: int, imag: int = 0)` | Gaussian integer ``real + imag * i``. | Space: O(1) |
| `NimProduct64` | class | `NimProduct64(...)` | Nim product for unsigned 64-bit integers. | Space: O(1) per value, plus fixed-size class tables after initialization. |
| `two_square_sum` | function | `two_square_sum(n: int) -> list[tuple[int, int]]` | Enumerate representations of ``n`` as a sum of two squares. | Time: Factorization time for ``n``, plus output-size polynomial arithmetic. |
| `linear_indeterminate_equation` | function | `linear_indeterminate_equation(a: int, b: int, c: int) -> 'tuple[bool, int, int]'` | Solve the linear Diophantine equation ax + by = c. | Time: O(log(min(abs(a), abs(b)) + 1)) integer operations |
| `linear_indeterminate_equation_min_abs_sum` | function | `linear_indeterminate_equation_min_abs_sum(a: int, b: int, c: int) -> 'tuple[bool, int, int]'` | Solve ``a * x + b * y = c`` while minimizing ``abs(x) + abs(y)``. | Time: O(log(min(abs(a), abs(b)) + 1)) integer operations |
| `linear_indeterminate_equation_with_limits` | function | `linear_indeterminate_equation_with_limits(a: int, b: int, c: int, x_min: int, x_max: int, y_min…` | Solve the linear Diophantine equation ax + by = c with constraints on the solution. | Time: O(log(min(abs(a), abs(b)) + 1)) integer operations |
| `linear_congruence` | function | `linear_congruence(a: int, b: int, m: int) -> 'tuple[bool, int]'` | Solve the linear congruence equation a * x ≡ b (mod m). | Time: O(log(min(abs(a), m) + 1)) integer operations |
| `GcdConvolution` | class | `GcdConvolution(...)` | A class for computing convolutions based on Greatest Common Divisor (GCD). | Space: ``O(N)`` |
| `LcmConvolution` | class | `LcmConvolution(...)` | A class for computing convolutions based on Least Common Multiple (LCM). | Space: ``O(N)`` |

### `bigint.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `BigInt` | class | `BigInt(value: 'int \| str \| BigInt' = 0)` | Arbitrary precision integer implementation. | Space: ``O(n)`` |
| `BigIntHex` | class | `BigIntHex(value: 'int \| str \| BigIntHex' = 0)` | Arbitrary precision integer implementation with hexadecimal representation. | Space: ``O(n)`` |

### `bit.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `sum_of_all_pairs_of_xor` | function | `sum_of_all_pairs_of_xor(arr: list[int]) -> int` | Sum XOR over all unordered pairs of distinct positions. | Time: O(n W) integer operations, where W is one plus the maximum bit length. |
| `popcount` | function | `popcount(x: int) -> int` | Count set bits in the low 32 bits. | Time: O(1) for fixed-width integers. |
| `bit_reverse` | function | `bit_reverse(x: int) -> int` | Reverse the low 32 bits. | Time: O(1) for fixed-width integers. |
| `tzcount` | function | `tzcount(x: int) -> int` | Count trailing zeros in the low 32 bits. | Time: O(1) for fixed-width integers. |
| `lzcount` | function | `lzcount(x: int) -> int` | Count leading zeros in the low 32 bits. | Time: O(1) for fixed-width integers. |
| `rmbit` | function | `rmbit(x: int) -> int` | Extract the rightmost set bit using Python's integer bit operations. | Time: O(W), where W is the bit length of x. |
| `lmbit` | function | `lmbit(x: int) -> int` | Extract the leftmost set bit in the low 32 bits. | Time: O(1) for fixed-width integers. |
| `filllower` | function | `filllower(x: int) -> int` | Set all low-32-bit positions at or below the leftmost set bit. | Time: O(1) for fixed-width integers. |
| `fillupper` | function | `fillupper(x: int) -> int` | Set all low-32-bit positions at or above the rightmost set bit. | Time: O(1) for fixed-width integers. |

### `combinatorics.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `enumerate_partition_number` | function | `enumerate_partition_number(n: int) -> list[int]` | Calculate partition numbers from 0 to n using pentagonal number theorem. | Time: O(n log n) with suitable NTT capacity; otherwise O(n sqrt(n)). |
| `enumerate_stirling_number_first` | function | `enumerate_stirling_number_first(n: int, fixed_k: int \| None) -> list[int]` | Enumerate Stirling numbers of the first kind. | Time: fixed_k is None: O(n log^2 n) using polynomial shift; fixed_k is specified: O(n log n) using formal power series With insufficient NTT capacity: O(n**2) for a row, or O(n * fixed_k) for a fixed column, plus O(n) output initialization. |
| `enumerate_stirling_number_second` | function | `enumerate_stirling_number_second(n: int, fixed_k: int \| None) -> list[int]` | Enumerate Stirling numbers of the second kind. | Time: ``O(n log n)`` for both branches With insufficient NTT capacity: O(n**2) for a row, or O(n * fixed_k) for a fixed column, plus O(n) output initialization. |
| `enumerate_bell_number` | function | `enumerate_bell_number(n: int) -> list[int]` | Enumerate Bell numbers from B(0) to B(n). | Time: O(n log n) with suitable NTT capacity; otherwise O(n**2). |
| `enumerate_bernoulli_number` | function | `enumerate_bernoulli_number(n: int) -> list[int]` | Enumerate Bernoulli numbers from B₀ to Bₙ. | Time: O(n log n) with suitable NTT capacity; otherwise O(n**2 + n log mod). |
| `count_four_sum` | function | `count_four_sum(a: list[int], b: list[int], c: list[int], d: list[int], target: int) -> int` | Count quadruples with one element from each list whose sum is ``target``. | Time: ``O(len(a) len(b) + len(c) len(d))`` expected |
| `count_subset_sums_with_size_in_range` | function | `count_subset_sums_with_size_in_range(values: list[int], size: int, lower: int, upper: int) -> i…` | Count subsets of fixed size whose sum lies in a closed interval. | Time: ``O(2^(n/2) log 2^(n/2))``, where ``n = len(values)`` |
| `TwelvefoldWay` | class | `TwelvefoldWay(distinguishable_balls: bool, distinguishable_boxes: bool, restriction: str = ANY,…` | Count distributions of balls into boxes under one twelvefold-way case. | Space: ``O(n + k)`` for cached factorials and dynamic programming buffers. |
| `enumerate_montmort_number` | function | `enumerate_montmort_number(n: int, mod: int) -> list[int]` | Enumerate Montmort numbers modulo ``mod``. | Time: ``O(n)`` |
| `count_all_subset_sums` | function | `count_all_subset_sums(arr: list[int], target: int) -> list[int]` | Count the number of subsets with each possible sum from 0 to target. | Time: O(target log target + len(arr)) with suitable NTT capacity; otherwise O(len(arr) * target + len(arr)). |

### `convolution.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `ConvolutionMod` | class | `ConvolutionMod(...)` | Convolution over a prime modulus using an NTT-style FFT. | Space: ``O(n + m)`` for the padded working arrays. |
| `ConvolutionLargeIntegers` | class | `ConvolutionLargeIntegers(...)` | Convolution for large integers via multi-modulus CRT reconstruction. | Space: ``O(k * n)`` for the temporary transformed arrays. |
| `Convolution64bit` | class | `Convolution64bit(...)` | Convolution modulo ``2**64`` using Garner-style reconstruction. | Space: ``O(n)``. |
| `BinaryField64` | class | `BinaryField64(...)` | Arithmetic in ``F_2[x] / (x^64 + x^4 + x^3 + x + 1)``. | Space: O(1) per value, plus fixed-size module tables after initialization. |
| `ConvolutionBinaryField64` | class | `ConvolutionBinaryField64(...)` | Convolution over ``F_2[x] / (x^64 + x^4 + x^3 + x + 1)``. | Space: O(n + m) for convolution operands and transform buffers. |

### `factorial.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `FactorialMod` | class | `FactorialMod(max_n: int)` | A class for computing factorials, permutations and combinations with modulo. | Space: ``O(max_n)`` |
| `LargeFactorialMod` | class | `LargeFactorialMod(block_size: int \| None = None)` | Compute large factorials modulo a prime without a full factorial table. | Space: ``O(B + M / B + Q)`` |
| `PowMod` | class | `PowMod(base: int, max_n: int)` | A class for computing powers of a fixed base with modulo efficiently. | Space: ``O(max_n)`` |
| `BinomialCoefficient` | class | `BinomialCoefficient()` | Compute binomial coefficients modulo a positive integer using prime powers. | Space: ``O(S)`` |

### `factorization.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `PrimeFactor` | class | `PrimeFactor(...)` | Provides utility functions related to prime factorization, primality testing, | Space: ``O(m)`` |

### `floating.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `FloatDouble` | class | `FloatDouble(value: float \| int \| 'FloatDouble' = 0.0, lo: float = 0.0)` | Double-double floating-point number. | Space: O(1) |

### `interval.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `range_mod` | function | `range_mod(l: int, r: int, mod: int) -> Iterator[tuple[int, int, int]]` | Generate normalized modulo subranges for the integer range ``[l, r)``. | Time: O(1) |
| `interval_union` | function | `interval_union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]` | Compute the union of a list of half-open intervals. | Time: ``O(n log n)``, where ``n = len(intervals)``. |
| `interval_intersection` | function | `interval_intersection(interval_lists: list[list[tuple[int, int]]]) -> list[tuple[int, int]]` | Compute the common intersection of sorted disjoint interval lists. | Time: ``O(T log k)``, where ``T`` is the total number of intervals and ``k`` is the number of interval lists. |

### `matrix.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `LinearEquationResult` | class | `LinearEquationResult(...)` | Solution description for a linear system. | Space: ``O(nm)`` for the stored solution vectors. |
| `DiagonalizationResult` | class | `DiagonalizationResult(...)` | Diagonalization over the current modular field. | Space: ``O(n^2)`` |
| `FrobeniusCyclicForm` | class | `FrobeniusCyclicForm(...)` | One-block Frobenius normal form of a cyclic matrix. | Space: ``O(n^2)`` |
| `FrobeniusForm` | class | `FrobeniusForm(...)` | Frobenius form represented by companion blocks. | Space: ``O(n^2)`` |
| `KrylovBlockForm` | class | `KrylovBlockForm(...)` | Krylov block decomposition of a matrix. | Space: ``O(n^2)`` |
| `MatrixMod` | class | `MatrixMod(n: int, m: int, from_array: list[list[int]] \| None = None)` | Matrix class with modular arithmetic. | Space: ``O(nm)`` |
| `LinearAlgebraFp` | class | `LinearAlgebraFp(...)` | Dense matrix over a prime finite field. | Space: ``O(nm)`` |
| `SparseMatrixMod` | class | `SparseMatrixMod(n: int, m: int, entries: Sequence[tuple[int, int, int]] \| None = None)` | Sparse matrix with modular arithmetic. | Space: ``O(n + nnz)`` |
| `BitSet` | class | `BitSet(n: int, bit_size: int = 63)` | Bitset backed by packed machine words. | Space: O(ceil(n / word_size) + 1) packed words. |
| `MatrixBit` | class | `MatrixBit(n: int, m: int, from_array: Sequence[Sequence[int]] \| None = None, transposed: bool =…` | Matrix class for Mod 2 operations using bit manipulation. | Space: O(n * (ceil(m / word_size) + 1)) packed words and row objects. |

### `modular.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `batch_inverse_mod` | function | `batch_inverse_mod(values: Sequence[int], mod: int) -> list[int]` | Compute modular inverses using one inverse of a product. | Time: O(n + log mod) arithmetic operations for n input values. |
| `discrete_logarithm` | function | `discrete_logarithm(base: int, value: int, mod: int) -> int` | Find the smallest nonnegative exponent with base**exponent == value modulo mod. | Time: O(sqrt(mod) log mod) |
| `tonelli_shanks` | function | `tonelli_shanks(square: int, mod: int) -> int` | Compute the square root modulo a prime using the Tonelli-Shanks algorithm. | Time: O(log^2 mod) - Average case complexity of the Tonelli-Shanks algorithm. |
| `extended_gcd` | function | `extended_gcd(a: int, mod: int) -> tuple[int, int]` | Return the gcd and a normalized coefficient from extended Euclid. | Time: O(log(mod + 1)) arithmetic operations after reducing ``a`` modulo ``mod``. |
| `chinese_remainder_theorem` | function | `chinese_remainder_theorem(rems: Sequence[int], mods: Sequence[int]) -> 'tuple[int, int]'` | Chinese Remainder Theorem (CRT) solver. | Time: O(k log M), where ``k = len(rems)`` and ``M`` is the final combined modulus. |
| `sqrt_mod` | function | `sqrt_mod(square: int, mod: int) -> int` | Compute a square root modulo any positive integer. | Time: Factorization time for ``mod``, plus root finding on each prime-power factor and CRT merge time. |
| `kth_root_mod` | function | `kth_root_mod(k: int, y: int, mod: int) -> int` | Compute a kth root modulo a prime. | Time: Factorization time for ``gcd(k, mod - 1)`` plus generalized Tonelli-Shanks steps. |

### `polynomial.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `polynomial_trim` | function | `polynomial_trim(coeffs: PolynomialLike, mod: int \| None = None) -> list[int]` | Normalize a low-to-high polynomial coefficient list by reducing modulo | Time: ``O(n)`` |
| `polynomial_normalize_monic` | function | `polynomial_normalize_monic(coeffs: PolynomialLike, mod: int \| None = None) -> list[int]` | Normalize a non-zero polynomial to monic form. | Time: ``O(n)`` |
| `polynomial_add` | function | `polynomial_add(left: PolynomialLike, right: PolynomialLike, mod: int \| None = None) -> list[int]` | Add two low-to-high polynomials. | Time: ``O(max(n, m))`` |
| `polynomial_sub` | function | `polynomial_sub(left: PolynomialLike, right: PolynomialLike, mod: int \| None = None) -> list[int]` | Subtract two low-to-high polynomials. | Time: ``O(max(n, m))`` |
| `polynomial_mul_naive` | function | `polynomial_mul_naive(left: PolynomialLike, right: PolynomialLike, mod: int \| None = None) -> li…` | Multiply two low-to-high polynomials by the quadratic algorithm. | Time: ``O(nm)`` |
| `polynomial_divmod_naive` | function | `polynomial_divmod_naive(left: PolynomialLike, right: PolynomialLike, mod: int \| None = None) ->…` | Divide low-to-high polynomials by the quadratic algorithm. | Time: ``O((n - m + 1) m)`` |
| `polynomial_is_zero` | function | `polynomial_is_zero(coeffs: PolynomialLike, mod: int \| None = None) -> bool` | Return whether all coefficients are zero modulo ``mod``. | Time: ``O(n)`` |
| `FormalPowerSeriesMod` | class | `FormalPowerSeriesMod(coef: Iterable[int])` | Formal power series with modular arithmetic. | Space: ``O(n)`` |
| `polynomial_product` | function | `polynomial_product(polys: list[FPS]) -> FPS` | Compute product of multiple polynomials efficiently. | Time: O(M(S) log(k + 1) + k log(k + 1)), where k is the number of factors, S is the total input coefficient count, and M(S) is the multiplication cost: O(S log S) with sufficient NTT capacity, otherwise O(S**2). |
| `coefficient_of_rational_polynomial` | function | `coefficient_of_rational_polynomial(numer: FPS, denom: FPS, k: int) -> int` | Find k-th coefficient of rational function P(x)/Q(x). | Time: O(d log(d + 1) log(k + 2)) with NTT, otherwise O(d**2 log(k + 2)), where d = max(len(numer), len(denom)). |
| `multipoint_evaluation` | function | `multipoint_evaluation(poly: FPS, xs: list[int]) -> list[int]` | Evaluate polynomial at multiple points. | Time: ``O((n + m) log^2(n + m))``, where ``n = len(poly)`` and ``m = len(xs)``. |
| `polynomial_interpolation` | function | `polynomial_interpolation(xs: list[int], ys: list[int]) -> FPS` | Find polynomial through given points. | Time: ``O(n log^2 n)``, where ``n = len(xs)``. |
| `polynomial_shift_sampling` | function | `polynomial_shift_sampling(n: int, m: int, ys: list[int], c: int) -> list[int]` | Evaluate polynomial at shifted consecutive points using sampling. | Time: O(m) for direct lookup or a constant polynomial. Otherwise, with t = min(m, mod), O((n+t) log(n+t) + m + log mod) using NTT, or O(n(n+t) + m + log mod) with direct multiplication. |
| `sum_of_exponential_times_polynomial` | function | `sum_of_exponential_times_polynomial(r: int, d: int, n: int \| None = None) -> int` | Compute a finite exponential-polynomial sum or its generating function. | Time: O((e + 1) log(e + 2) + log(n + 1)) modular operations for finite n, with the last term omitted for n = None. When e = mod - 1, O(log(n + 1)) for finite n and O(1) for n = None, excluding integer exponent reduction. |
| `polynomial_shift` | function | `polynomial_shift(poly: FPS, c: int) -> FPS` | Compute Taylor shift P(x+c). | Time: O(n log n) with suitable NTT capacity and invertible factorials, otherwise O(n**2). O(n) if the shift is zero modulo the modulus. |
| `polynomial_roots` | function | `polynomial_roots(poly: FPS) -> list[int]` | Find all roots of a polynomial over F_p. | Time: Expected ``O(M(n) log(mod) log(n))`` where ``n`` is the polynomial degree and ``M(n)`` is the cost of multiplying degree-``n`` polynomials. O(n) in characteristic two, by evaluating zero and one. |

### `rational.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Rational` | class | `Rational(num: int, den: int, _should_normalize: bool = True)` | Exact rational number with lazy normalization. | Space: ``O(1)`` |
| `SternBrocotTree` | class | `SternBrocotTree(num: int \| Rational = 1, den: int = 1)` | Node on the Stern-Brocot tree of positive rational numbers. | Space: ``O(k)`` where ``k`` is the number of direction runs in the path. |

### `recurrence.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `evaluate_linear_recurrence` | function | `evaluate_linear_recurrence(coef: list[int], init: list[int], k: int) -> int` | Compute the k-th term of a linear recurrence using formal power series (Bostan–Mori). | Time: O(n log(n + 1) log(k + 2)) with NTT, otherwise O(n**2 log(k + 2)). |
| `enumerate_linear_recurrence` | function | `enumerate_linear_recurrence(coef: list[int], init: list[int], k: int, m: int) -> list[int]` | Enumerate consecutive terms of a linear recurrence. | Time: Let ``d = len(coef)``. The current implementation runs in O((d + m) log(d + m + 1) log(k + 2)) with NTT, or at most O((d + m)**2 log(k + 2)) with quadratic polynomial operations. |
| `berlekamp_massey` | function | `berlekamp_massey(sequence: list[int]) -> list[int]` | Compute minimal linear recurrence coefficients for a given integer sequence | Time: O(n^2) |
| `find_linear_recurrence` | function | `find_linear_recurrence(sequence: list[int]) -> list[int]` | Derive coefficients for direct evaluation of a linear recurrence from a given sequence. | Time: ``O(n^2)`` |

### `sieve.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `enumerate_primes` | function | `enumerate_primes(n: int) -> list[int]` | Enumerate primes up to ``n`` using a segmented sieve. | Time: ``O(n log log n)`` |
| `enumerate_primes_by_index` | function | `enumerate_primes_by_index(n: int, a: int, b: int) -> tuple[int, list[int]]` | Count primes up to ``n`` and enumerate primes at selected indices. | Time: ``O(n log log n)`` |

### `subset.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `bitmask_from_indices` | function | `bitmask_from_indices(indices: Iterable[int]) -> int` | Build a bit mask whose listed bit positions are set. | Time: O(k), where ``k`` is the number of indices. |
| `bitmask_indices` | function | `bitmask_indices(mask: int) -> Iterator[int]` | Enumerate set bit positions in ascending order. | Time: O(k), where ``k`` is the number of set bits. |
| `format_bitmask` | function | `format_bitmask(value: int, width: int) -> str` | Format the low ``width`` bits of ``value`` as a fixed-width binary string. | Time: O(width) |
| `enumerate_bitmasks` | function | `enumerate_bitmasks(width: int) -> Iterator[int]` | Enumerate all masks on ``width`` bits in ascending integer order. | Time: O(2^width) |
| `enumerate_subsets_ascending` | function | `enumerate_subsets_ascending(mask: int) -> Iterator[int]` | Enumerate all subsets of a bit mask in ascending integer order. | Time: O(2^k), where ``k`` is the number of set bits. |
| `enumerate_supersets` | function | `enumerate_supersets(mask: int, width: int) -> Iterator[int]` | Enumerate all supersets of ``mask`` within ``width`` bits in ascending order. | Time: O(2^(width-k)), where ``k`` is the number of set bits in ``mask``. |
| `enumerate_combinations` | function | `enumerate_combinations(width: int, size: int) -> Iterator[int]` | Enumerate ``size``-element combinations as masks in ascending integer order. | Time: O(C(width, size)) |
| `BitFlagSet` | class | `BitFlagSet(width: int, value: int = 0)` | Mutable fixed-width bit flag set backed by one Python integer. | Space: O(ceil(width / word_size)) machine words. |
| `BitwiseAndConvolution` | class | `BitwiseAndConvolution(...)` | Bitwise AND convolution using zeta/mobius transforms. | Space: ``O(1)`` |
| `BitwiseOrConvolution` | class | `BitwiseOrConvolution(...)` | Bitwise OR convolution using zeta/mobius transforms. | Space: ``O(1)`` |
| `BitwiseXorConvolution` | class | `BitwiseXorConvolution(...)` | Bitwise XOR convolution using Walsh-Hadamard transform. | Space: ``O(1)`` |
| `enumerate_subsets_descending` | function | `enumerate_subsets_descending(bit: int) -> Iterator[int]` | Enumerate all subsets of a bit mask in descending integer order. | Time: ``O(2^k)`` where ``k = popcount(bit)`` |
| `SubsetConvolution` | class | `SubsetConvolution(...)` | Subset convolution using ranked zeta/mobius transforms. | Space: ``O(1)`` |

### `summatory.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `count_primes` | function | `count_primes(n: int) -> int` | Count the number of primes up to n using Lucy DP algorithm. | Time: ``O(n^(3/4) / log n)`` |
| `count_squarefrees` | function | `count_squarefrees(n: int) -> int` | Count square-free integers up to n. | Time: Roughly ``O(n^(2/5))`` with a precomputation of the Möbius function up to ``sqrt(n / n^(1/5))``. |
| `sum_of_primes` | function | `sum_of_primes(n: int) -> int` | Calculate the sum of all primes up to n using Lucy DP algorithm. | Time: ``O(n^(3/4) / log n)`` |

### `utility.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `absolute` | function | `absolute(x: int) -> int` | Return the absolute value of an arbitrary integer. | Time: O(1) |
| `sign` | function | `sign(x: int) -> int` | Return -1, 0, or 1 according to the sign of an arbitrary integer. | Time: O(1) |
| `clamp` | function | `clamp(x: int, a: int, b: int) -> int` | Clamp an arbitrary integer to the inclusive interval [a, b]. | Time: O(1) |
| `xorshift64` | function | `xorshift64(state: int) -> int` | Advance a 64-bit xorshift generator by one step. | Time: ``O(1)``. |
| `generate_quotient` | function | `generate_quotient(n: int) -> Iterator[tuple[int, int, int]]` | Generates all distinct quotients of floor(n/i) for i in range [1, n]. | Time: ``O(sqrt(n))`` |
