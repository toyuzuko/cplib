#!/usr/bin/env python3

"""Bit-mask enumeration and modular subset transforms.

Complexities for mask utilities count integer arithmetic operations. For masks
wider than a machine word, each bitwise operation also scales with the number
of words in the mask; an O(1) mask count does not mean O(1) bits of storage.
"""

from collections.abc import Iterable, Iterator

from cplib.mathematics.bit import popcount


def _low_mask(width: int) -> int:
    if width < 0:
        raise ValueError('width must be non-negative')
    return (1 << width) - 1


def bitmask_from_indices(indices: Iterable[int]) -> int:
    """
    Build a bit mask whose listed bit positions are set.

    Args:
        indices: Bit positions to set.

    Returns:
        Integer bit mask.

    Raises:
        ValueError: If an index is negative.

    Time Complexity:
        O(k), where ``k`` is the number of indices.

    Space Complexity:
        O(1)
    """
    res = 0
    for index in indices:
        if index < 0:
            raise ValueError('bit index must be non-negative')
        res |= 1 << index
    return res


def bitmask_indices(mask: int) -> Iterator[int]:
    """
    Enumerate set bit positions in ascending order.

    Args:
        mask: Input bit mask.

    Yields:
        Set bit positions from low to high.

    Raises:
        ValueError: If ``mask`` is negative.

    Time Complexity:
        O(k), where ``k`` is the number of set bits.

    Space Complexity:
        O(1)
    """
    if mask < 0:
        raise ValueError('mask must be non-negative')
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def format_bitmask(value: int, width: int) -> str:
    """
    Format the low ``width`` bits of ``value`` as a fixed-width binary string.

    Args:
        value: Input integer.
        width: Number of bits to print.

    Returns:
        Binary representation padded with leading zeros to ``width`` digits;
        the empty string when width is zero.

    Raises:
        ValueError: If ``width`` is negative.

    Time Complexity:
        O(width)

    Space Complexity:
        O(width)
    """
    mask = _low_mask(width)
    return f'{value & mask:0{width}b}' if width else ''


def enumerate_bitmasks(width: int) -> Iterator[int]:
    """
    Enumerate all masks on ``width`` bits in ascending integer order.

    Args:
        width: Number of available bit positions.

    Yields:
        Masks from ``0`` to ``2^width - 1``.

    Raises:
        ValueError: If ``width`` is negative.

    Time Complexity:
        O(2^width)

    Space Complexity:
        O(1)
    """
    if width < 0:
        raise ValueError('width must be non-negative')
    for mask in range(1 << width):
        yield mask


def enumerate_subsets_ascending(mask: int) -> Iterator[int]:
    """
    Enumerate all subsets of a bit mask in ascending integer order.

    Args:
        mask: Input bit mask.

    Yields:
        Submasks of ``mask`` from small to large.

    Raises:
        ValueError: If ``mask`` is negative.

    Time Complexity:
        O(2^k), where ``k`` is the number of set bits.

    Space Complexity:
        O(1) integer masks, without storing all subsets.
    """
    if mask < 0:
        raise ValueError('mask must be non-negative')
    subset = 0
    while True:
        yield subset
        if subset == mask:
            break
        subset = (subset - mask) & mask


def enumerate_supersets(mask: int, width: int) -> Iterator[int]:
    """
    Enumerate all supersets of ``mask`` within ``width`` bits in ascending order.

    Args:
        mask: Required bits.
        width: Number of available bit positions.

    Yields:
        Masks ``x`` such that ``mask`` is a subset of ``x`` and
        ``0 <= x < 2^width``.

    Raises:
        ValueError: If ``width`` is negative or ``mask`` has bits outside
            ``width``.

    Time Complexity:
        O(2^(width-k)), where ``k`` is the number of set bits in ``mask``.

    Space Complexity:
        O(1) integer masks, without storing all supersets.
    """
    all_mask = _low_mask(width)
    if mask < 0 or mask & ~all_mask:
        raise ValueError('mask must be within width bits')
    free = all_mask ^ mask
    for subset in enumerate_subsets_ascending(free):
        yield mask | subset


def enumerate_combinations(width: int, size: int) -> Iterator[int]:
    """
    Enumerate ``size``-element combinations as masks in ascending integer order.

    Args:
        width: Number of available bit positions.
        size: Number of selected positions.

    Yields:
        Masks with exactly ``size`` set bits. No masks if size is outside
        [0, width]; the sole mask is zero if size is zero.

    Raises:
        ValueError: If ``width`` is negative.

    Time Complexity:
        O(C(width, size))

    Space Complexity:
        O(1)
    """
    if width < 0:
        raise ValueError('width must be non-negative')
    if size < 0 or size > width:
        return
    if size == 0:
        yield 0
        return
    mask = (1 << size) - 1
    limit = 1 << width
    while mask < limit:
        yield mask
        c = mask & -mask
        r = mask + c
        mask = (((r ^ mask) >> 2) // c) | r


class BitFlagSet:
    """
    Mutable fixed-width bit flag set backed by one Python integer.

    Attributes:
        width: Number of managed bit positions; do not modify after construction.
        value: Current integer state, which must remain within width bits.

    Space Complexity:
        O(ceil(width / word_size)) machine words.

    Notes:
        Methods described as O(1) assume a machine-word-sized width. For wider
        masks, integer bit operations take O(ceil(width / word_size)) time.
        Mutation through methods preserves the fixed-width invariant.
    """

    __slots__ = ('width', 'value', '_mask')

    def __init__(self, width: int, value: int = 0) -> None:
        """
        Initialize a fixed-width flag set.

        Args:
            width: Number of managed bit positions.
            value: Initial state.

        Returns:
            None.

        Raises:
            ValueError: If ``width`` is negative or ``value`` is outside the
                fixed-width domain.

        Time Complexity:
            O(1)
        """
        self.width = width
        self._mask = _low_mask(width)
        if value < 0 or value & ~self._mask:
            raise ValueError('value must be within width bits')
        self.value = value

    def _check_index(self, index: int) -> None:
        if not (0 <= index < self.width):
            raise ValueError('bit index is outside the fixed width')

    def _check_mask(self, mask: int) -> None:
        if mask < 0 or mask & ~self._mask:
            raise ValueError('mask must be within width bits')

    def test(self, index: int) -> bool:
        """
        Return whether a bit is set.

        Args:
            index: Bit position.

        Returns:
            True if the bit is set, otherwise False.

        Time Complexity:
            O(1)
        """
        self._check_index(index)
        return bool(self.value & (1 << index))

    def set_bit(self, index: int) -> None:
        """
        Set one bit.

        Args:
            index: Bit position.

        Returns:
            None.

        Raises:
            ValueError: If index is outside the fixed width.

        Time Complexity:
            O(1)
        """
        self._check_index(index)
        self.value |= 1 << index

    def clear_bit(self, index: int) -> None:
        """
        Clear one bit.

        Args:
            index: Bit position.

        Returns:
            None.

        Raises:
            ValueError: If index is outside the fixed width.

        Time Complexity:
            O(1)
        """
        self._check_index(index)
        self.value &= ~(1 << index)

    def flip_bit(self, index: int) -> None:
        """
        Flip one bit.

        Args:
            index: Bit position.

        Returns:
            None.

        Raises:
            ValueError: If index is outside the fixed width.

        Time Complexity:
            O(1)
        """
        self._check_index(index)
        self.value ^= 1 << index

    def set_mask(self, mask: int) -> None:
        """
        Set all bits contained in ``mask``.

        Args:
            mask: Bit mask to set.

        Returns:
            None.

        Raises:
            ValueError: If mask is outside the fixed width.

        Time Complexity:
            O(1)
        """
        self._check_mask(mask)
        self.value |= mask

    def clear_mask(self, mask: int) -> None:
        """
        Clear all bits contained in ``mask``.

        Args:
            mask: Bit mask to clear.

        Returns:
            None.

        Raises:
            ValueError: If mask is outside the fixed width.

        Time Complexity:
            O(1)
        """
        self._check_mask(mask)
        self.value &= self._mask ^ mask

    def flip_mask(self, mask: int) -> None:
        """
        Flip all bits contained in ``mask``.

        Args:
            mask: Bit mask to flip.

        Returns:
            None.

        Raises:
            ValueError: If mask is outside the fixed width.

        Time Complexity:
            O(1)
        """
        self._check_mask(mask)
        self.value ^= mask

    def all(self, mask: int | None = None) -> bool:
        """
        Return whether all selected bits are set.

        Args:
            mask: Selected bits. If omitted, all managed bits are selected.

        Returns:
            True if every selected bit is set.

        Time Complexity:
            O(1)
        """
        if mask is None:
            mask = self._mask
        self._check_mask(mask)
        return self.value & mask == mask

    def any(self, mask: int | None = None) -> bool:
        """
        Return whether any selected bit is set.

        Args:
            mask: Selected bits. If omitted, all managed bits are selected.

        Returns:
            True if at least one selected bit is set.

        Time Complexity:
            O(1)
        """
        if mask is None:
            mask = self._mask
        self._check_mask(mask)
        return bool(self.value & mask)

    def none(self, mask: int | None = None) -> bool:
        """
        Return whether no selected bit is set.

        Args:
            mask: Selected bits. If omitted, all managed bits are selected.

        Returns:
            True if every selected bit is clear.

        Time Complexity:
            O(1)
        """
        if mask is None:
            mask = self._mask
        self._check_mask(mask)
        return not self.value & mask

    def count(self, mask: int | None = None) -> int:
        """
        Count set bits among selected bits.

        Args:
            mask: Selected bits. If omitted, all managed bits are selected.

        Returns:
            Number of set selected bits.

        Time Complexity:
            O(width / word_size)
        """
        if mask is None:
            mask = self._mask
        self._check_mask(mask)
        return (self.value & mask).bit_count()

    def val(self, mask: int | None = None) -> int:
        """
        Return the integer value of selected bits.

        Args:
            mask: Selected bits. If omitted, all managed bits are selected.

        Returns:
            ``value & mask``.

        Time Complexity:
            O(1)
        """
        if mask is None:
            mask = self._mask
        self._check_mask(mask)
        return self.value & mask

    def complement_value(self) -> int:
        """
        Return the bitwise complement within the fixed width.

        Returns:
            ``~value`` masked to ``width`` bits.

        Time Complexity:
            O(1)
        """
        return self.value ^ self._mask

    def logical_left_shift_value(self, shift: int = 1) -> int:
        """
        Return the fixed-width logical left shift result.

        Args:
            shift: Number of shifted positions.

        Returns:
            ``(value << shift)`` masked to ``width`` bits.

        Raises:
            ValueError: If ``shift`` is negative.

        Time Complexity:
            O(1)
        """
        if shift < 0:
            raise ValueError('shift must be non-negative')
        if shift >= self.width:
            return 0
        return (self.value << shift) & self._mask

    def logical_right_shift_value(self, shift: int = 1) -> int:
        """
        Return the logical right shift result.

        Args:
            shift: Number of shifted positions.

        Returns:
            ``value >> shift``.

        Raises:
            ValueError: If ``shift`` is negative.

        Time Complexity:
            O(1)
        """
        if shift < 0:
            raise ValueError('shift must be non-negative')
        return self.value >> shift

    def to_binary(self) -> str:
        """
        Return the current state as a fixed-width binary string.

        Returns:
            Binary representation padded to ``width`` digits.

        Time Complexity:
            O(width)

        Space Complexity:
            O(width)
        """
        return format_bitmask(self.value, self.width)


class BitwiseAndConvolution:
    """
    Bitwise AND convolution using zeta/mobius transforms.

    Computes convolution over bitwise AND operation:
    result[i] = sum over all j,k where (j & k = i) of arr1[j] * arr2[k]

    Attributes:
        _mod: Modulus used for the transforms.

    Space Complexity:
        ``O(1)``

    Complexity Notation:
        ``n`` is the number of bits, so each input and output array has length
        ``2^n``.
    """
    _mod = 998244353

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set modulus for all subset convolution operations.

        Args:
            mod: Positive modulus used for arithmetic.

        Returns:
            None.

        Raises:
            ValueError: If mod is not positive.

        Time Complexity:
            O(1)
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            The positive modulus currently used for arithmetic.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def zeta(cls, n: int, arr: list[int]) -> list[int]:
        """
        Compute zeta transform for AND convolution.

        Computes zeta[i] = sum over all j where (i ⊆ j) of arr[j].

        Args:
            n: Number of bits.
            arr: Input array of length 2^n.

        Returns:
            Zeta transform of the input array, reduced modulo get_mod().

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> # zeta[00] = arr[00] + arr[01] + arr[10] + arr[11] = 1 + 2 + 3 + 4 = 10
            >>> # zeta[01] = arr[01] + arr[11] = 2 + 4 = 6
            >>> # zeta[10] = arr[10] + arr[11] = 3 + 4 = 7
            >>> # zeta[11] = arr[11] = 4
            >>> BitwiseAndConvolution.zeta(2, [1, 2, 3, 4])
            [10, 6, 7, 4]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr) != 1 << n:
            raise ValueError('n must be non-negative and len(arr) must equal 2**n')
        res = [x % cls._mod for x in arr]
        for k in range(n):
            i = 1 << k
            for j in range(1 << n):
                if not i & j:
                    res[j] += res[i | j]
                    res[j] %= cls._mod
        return res

    @classmethod
    def mobius(cls, n: int, arr: list[int]) -> list[int]:
        """
        Compute mobius transform (inverse of zeta).

        Computes mobius[i] = sum over all j where (i ⊆ j) of (-1)^(|j| - |i|) * arr[j].

        Args:
            n: Number of bits.
            arr: Input array of length 2^n.

        Returns:
            Mobius transform of the input array, reduced modulo get_mod().

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> # Inverse of the zeta transform example
            >>> BitwiseAndConvolution.mobius(2, [10, 6, 7, 4])
            [1, 2, 3, 4]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr) != 1 << n:
            raise ValueError('n must be non-negative and len(arr) must equal 2**n')
        res = [x % cls._mod for x in arr]
        for k in range(n):
            i = 1 << k
            for j in range(1 << n):
                if not i & j:
                    res[j] -= res[i | j]
                    res[j] %= cls._mod
        return res

    @classmethod
    def convolution(cls, n: int, arr1: list[int], arr2: list[int]) -> list[int]:
        """
        Compute AND convolution of two arrays.

        Computes result[i] = sum over all j,k where (j & k = i) of arr1[j] * arr2[k].

        Args:
            n: Number of bits.
            arr1: First input array of length 2^n.
            arr2: Second input array of length 2^n.

        Returns:
            AND convolution of arr1 and arr2, reduced modulo get_mod().

        Notes:
            Uses zeta-mobius transform:
            1. Apply zeta to both arrays
            2. Pointwise multiplication
            3. Apply mobius to get result

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> BitwiseAndConvolution.convolution(2, [1, 2, 3, 4], [5, 6, 7, 8])
            [103, 52, 73, 32]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr1) != 1 << n or len(arr2) != 1 << n:
            raise ValueError('n must be non-negative and both lengths must equal 2**n')
        zeta1 = cls.zeta(n, arr1)
        zeta2 = cls.zeta(n, arr2)
        res = [zeta1[i] * zeta2[i] % cls._mod for i in range(1 << n)]
        return cls.mobius(n, res)


class BitwiseOrConvolution:
    """
    Bitwise OR convolution using zeta/mobius transforms.

    Computes convolution over bitwise OR operation:
    result[i] = sum over all j,k where (j | k = i) of arr1[j] * arr2[k]

    Attributes:
        _mod: Modulus used for the transforms.

    Space Complexity:
        ``O(1)``

    Complexity Notation:
        ``n`` is the number of bits, so each input and output array has length
        ``2^n``.
    """
    _mod = 998244353

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set modulus for all subset convolution operations.

        Args:
            mod: Positive modulus used for arithmetic.

        Returns:
            None.

        Raises:
            ValueError: If mod is not positive.

        Time Complexity:
            O(1)
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            The positive modulus currently used for arithmetic.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def zeta(cls, n: int, arr: list[int]) -> list[int]:
        """
        Compute zeta transform for OR convolution.

        Computes zeta[i] = sum over all j where (j ⊆ i) of arr[j].

        Args:
            n: Number of bits.
            arr: Input array of length 2^n.

        Returns:
            Zeta transform of the input array, reduced modulo get_mod().

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> # zeta[00] = arr[00] = 1
            >>> # zeta[01] = arr[00] + arr[01] = 1 + 2 = 3
            >>> # zeta[10] = arr[00] + arr[10] = 1 + 3 = 4
            >>> # zeta[11] = arr[00] + arr[01] + arr[10] + arr[11] = 1 + 2 + 3 + 4 = 10
            >>> BitwiseOrConvolution.zeta(2, [1, 2, 3, 4])
            [1, 3, 4, 10]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr) != 1 << n:
            raise ValueError('n must be non-negative and len(arr) must equal 2**n')
        res = [x % cls._mod for x in arr]
        for k in range(n):
            i = 1 << k
            for j in range(1 << n):
                if i & j:
                    res[j] += res[j ^ i]
                    res[j] %= cls._mod
        return res

    @classmethod
    def mobius(cls, n: int, arr: list[int]) -> list[int]:
        """
        Compute mobius transform (inverse of zeta).

        Computes mobius[i] = sum over all j where (j ⊆ i) of (-1)^(|i| - |j|) * arr[j].

        Args:
            n: Number of bits.
            arr: Input array of length 2^n.

        Returns:
            Mobius transform of the input array, reduced modulo get_mod().

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> # mobius[00] = arr[00] = 1
            >>> # mobius[01] = arr[01] - arr[00] = 3 - 1 = 2
            >>> # mobius[10] = arr[10] - arr[00] = 4 - 1 = 3
            >>> # mobius[11] = arr[11] - arr[01] - arr[10] + arr[00] = 10 - 3 - 4 + 1 = 4
            >>> BitwiseOrConvolution.mobius(2, [1, 3, 4, 10])
            [1, 2, 3, 4]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr) != 1 << n:
            raise ValueError('n must be non-negative and len(arr) must equal 2**n')
        res = [x % cls._mod for x in arr]
        for k in range(n):
            i = 1 << k
            for j in range(1 << n):
                if i & j:
                    res[j] -= res[j ^ i]
                    res[j] %= cls._mod
        return res

    @classmethod
    def convolution(cls, n: int, arr1: list[int], arr2: list[int]) -> list[int]:
        """
        Compute OR convolution of two arrays.

        Computes result[i] = sum over all j,k where (j | k = i) of arr1[j] * arr2[k].

        Args:
            n: Number of bits.
            arr1: First input array of length 2^n.
            arr2: Second input array of length 2^n.

        Returns:
            OR convolution of arr1 and arr2, reduced modulo get_mod().

        Notes:
            Uses zeta-mobius transform:
            1. Apply zeta to both arrays
            2. Pointwise multiplication
            3. Apply mobius to get result

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> BitwiseOrConvolution.convolution(2, [1, 2, 3, 4], [5, 6, 7, 8])
            [5, 28, 43, 184]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr1) != 1 << n or len(arr2) != 1 << n:
            raise ValueError('n must be non-negative and both lengths must equal 2**n')
        zeta1 = cls.zeta(n, arr1)
        zeta2 = cls.zeta(n, arr2)
        res = [zeta1[i] * zeta2[i] % cls._mod for i in range(1 << n)]
        return cls.mobius(n, res)


class BitwiseXorConvolution:
    """
    Bitwise XOR convolution using Walsh-Hadamard transform.

    Computes convolution over bitwise XOR operation:
    result[i] = sum over all j,k where (j ^ k = i) of arr1[j] * arr2[k]

    Attributes:
        _mod: Modulus used for the transforms.

    Space Complexity:
        ``O(1)``

    Complexity Notation:
        ``n`` is the number of bits, so each input and output array has length
        ``2^n``.
    """
    _mod = 998244353

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set modulus for all subset convolution operations.

        Args:
            mod: Positive modulus used for arithmetic.

        Returns:
            None.

        Raises:
            ValueError: If mod is not positive.

        Time Complexity:
            O(1)
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            The positive modulus currently used for arithmetic.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def hadamard(cls, n: int, arr: list[int]) -> list[int]:
        """
        Compute Walsh-Hadamard transform.

        Args:
            n: Number of bits.
            arr: Input array of length 2^n.

        Returns:
            Walsh-Hadamard transform of the input array, reduced modulo get_mod().

        Notes:
            The transform matrix H_n is recursively defined as:
            H_0 = [1]
            H_1 = [[1, 1], [1, -1]]
            H_n = [[H_{n-1}, H_{n-1}], [H_{n-1}, -H_{n-1}]]

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> BitwiseXorConvolution.hadamard(2, [1, 2, 3, 4])
            [10, 998244351, 998244349, 0]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """
        if n < 0 or len(arr) != 1 << n:
            raise ValueError('n must be non-negative and len(arr) must equal 2**n')
        res = [x % cls._mod for x in arr]
        for k in range(n):
            i = 1 << k
            for j in range(1 << n):
                if not i & j:
                    res[j], res[i | j] = (res[j] + res[i | j]) % cls._mod, (res[j] - res[i | j]) % cls._mod
        return res

    @classmethod
    def convolution(cls, n: int, arr1: list[int], arr2: list[int]) -> list[int]:
        """
        Compute XOR convolution of two arrays.

        Computes result[i] = sum over all j,k where (j ^ k = i) of arr1[j] * arr2[k].

        Args:
            n: Number of bits.
            arr1: First input array of length 2^n.
            arr2: Second input array of length 2^n.

        Returns:
            XOR convolution of arr1 and arr2, reduced modulo get_mod().

        Notes:
            Uses Walsh-Hadamard transform:
            1. Apply Hadamard to both arrays
            2. Pointwise multiplication
            3. Apply Hadamard and normalize to get result

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.
                The length must be invertible modulo the modulus (for n>0,
                the modulus must be odd).

        Examples:
            >>> BitwiseXorConvolution.convolution(2, [1, 2, 3, 4], [5, 6, 7, 8])
            [70, 68, 62, 60]

        Time Complexity:
            ``O(n 2^n)``

        Space Complexity:
            O(2^n)
        """

        if n < 0 or len(arr1) != 1 << n or len(arr2) != 1 << n:
            raise ValueError('n must be non-negative and both lengths must equal 2**n')
        inv = pow(1 << n, -1, cls._mod)
        hadamard1 = cls.hadamard(n, arr1)
        hadamard2 = cls.hadamard(n, arr2)
        res = [hadamard1[i] * hadamard2[i] % cls._mod for i in range(1 << n)]
        res = cls.hadamard(n, res)
        res = [x * inv % cls._mod for x in res]
        return res


def enumerate_subsets_descending(bit: int) -> Iterator[int]:
    """
    Enumerate all subsets of a bit mask in descending integer order.

    Args:
        bit: The bit mask.

    Yields:
        All subsets of the bit mask in **descending** order.

    Raises:
        ValueError: If bit is negative.

    Examples:
        >>> # Subsets: 101, 100, 001, 000
        >>> list(enumerate_subsets_descending(5))  # 5 = 0b101
        [5, 4, 1, 0]

    Returns:
        Generator over all subsets of ``bit`` in descending order.

    Time Complexity:
        ``O(2^k)`` where ``k = popcount(bit)``

    Space Complexity:
        ``O(1)``
    """
    if bit < 0:
        raise ValueError('bit must be non-negative')
    x = bit
    while x:
        yield x
        x = (x - 1) & bit
    yield 0


class SubsetConvolution:
    """
    Subset convolution using ranked zeta/mobius transforms.

    Computes convolution over disjoint union operation:
    result[i] = sum over all j,k where (j ∩ k = ∅ and j ∪ k = i) of arr1[j] * arr2[k]

    Attributes:
        _mod: Modulus used for the transforms.

    Space Complexity:
        ``O(1)``

    Complexity Notation:
        ``n`` is the number of bits, so each input and output array has length
        ``2^n``.
    """
    _mod = 998244353

    @classmethod
    def set_mod(cls, mod: int) -> None:
        """
        Set modulus for all subset convolution operations.

        Args:
            mod: Positive modulus used for arithmetic.

        Returns:
            None.

        Raises:
            ValueError: If mod is not positive.

        Time Complexity:
            O(1)
        """
        if mod <= 0:
            raise ValueError('mod must be positive')
        cls._mod = mod

    @classmethod
    def get_mod(cls) -> int:
        """
        Get current modulus.

        Returns:
            The positive modulus currently used for arithmetic.

        Time Complexity:
            O(1)
        """
        return cls._mod

    @classmethod
    def _ranked_zeta(cls, n: int, ranked: list[int]) -> None:
        """Apply ranked zeta transform in-place.

        Applies zeta transform independently for each popcount rank.
        Modifies the input array in-place.

        Args:
            n: Number of bits.
            ranked: Ranked array of length 2^n * (n+1) to be transformed in-place.

        Time Complexity:
            ``O(n^2 2^n)``
        """

        assert len(ranked) == (1 << n) * (n + 1)

        for k in range(n):
            for i in range(1 << n):
                if (i & (1 << k)): continue
                prv = (i * (n + 1))
                nxt = (i | (1 << k)) * (n + 1)
                for j in range(n + 1):
                    ranked[nxt + j] += ranked[prv + j]
                    ranked[nxt + j] %= cls._mod

    @classmethod
    def _ranked_mobius(cls, n: int, ranked: list[int]) -> None:
        """Apply ranked mobius transform in-place (inverse of ranked zeta).

        Applies mobius transform independently for each popcount rank.
        Modifies the input array in-place.

        Args:
            n: Number of bits.
            ranked: Ranked array of length 2^n * (n+1) to be transformed in-place.

        Time Complexity:
            ``O(n^2 2^n)``
        """

        assert len(ranked) == (1 << n) * (n + 1)

        for k in range(n):
            for i in range(1 << n):
                if (i & (1 << k)): continue
                prv = (i * (n + 1))
                nxt = (i | (1 << k)) * (n + 1)
                for j in range(n + 1):
                    ranked[nxt + j] -= ranked[prv + j]
                    ranked[nxt + j] %= cls._mod

    @classmethod
    def convolution(cls, n: int, arr1: list[int], arr2: list[int]) -> list[int]:
        """
        Compute subset convolution of two arrays.

        Computes result[i] = sum over all j,k where (j ∩ k = ∅ and j ∪ k = i) of arr1[j] * arr2[k].

        Args:
            n: Number of bits.
            arr1: First input array of length 2^n.
            arr2: Second input array of length 2^n.

        Returns:
            Subset convolution of arr1 and arr2, reduced modulo get_mod().

        Notes:
            Uses ranked zeta-mobius transform:
            1. Apply ranked zeta to both arrays
            2. Pointwise multiplication with rank addition
            3. Apply ranked mobius to get result

        Raises:
            ValueError: If n is negative or an input length differs from 2**n.

        Examples:
            >>> SubsetConvolution.convolution(2, [1, 2, 3, 4], [5, 6, 7, 8])
            [5, 16, 22, 60]

        Time Complexity:
            ``O(n^2 2^n)``

        Space Complexity:
            O((n + 1) 2^n)
        """
        if n < 0 or len(arr1) != 1 << n or len(arr2) != 1 << n:
            raise ValueError('n must be non-negative and both lengths must equal 2**n')

        size = (1 << n) * (n + 1)

        # Create ranked arrays and distribute values by popcount
        ranked1 = [0] * size
        ranked2 = [0] * size

        for i, val in enumerate(arr1):
            ranked1[i * (n + 1) + popcount(i)] = val

        for i, val in enumerate(arr2):
            ranked2[i * (n + 1) + popcount(i)] = val

        # Apply ranked zeta transforms in-place
        cls._ranked_zeta(n, ranked1)
        cls._ranked_zeta(n, ranked2)

        # Reuse ranked1 as the product buffer to reduce peak memory.
        for i in range(1 << n):
            ofs = i * (n + 1)
            row = [0] * (n + 1)
            for d in range(n + 1):
                total = 0
                for j in range(d + 1):
                    total += ranked1[ofs + j] * ranked2[ofs + (d - j)]
                row[d] = total % cls._mod
            ranked1[ofs:ofs + n + 1] = row

        # Apply ranked mobius transform in-place
        cls._ranked_mobius(n, ranked1)

        # Extract result from diagonal (where popcount matches)
        result = [ranked1[i * (n + 1) + popcount(i)] for i in range(1 << n)]
        return result
