#!/usr/bin/env python3


def sum_of_all_pairs_of_xor(arr: list[int]) -> int:
    """Sum XOR over all unordered pairs of distinct positions.

    Args:
        arr: Integers of any size, including negative values. XOR uses Python's
            infinite two's-complement convention.

    Returns:
        sum(arr[i] ^ arr[j] for 0 <= i < j < len(arr)).

    Time Complexity:
        O(n W) integer operations, where W is one plus the maximum bit length.

    Space Complexity:
        O(W + log(n)) bits of auxiliary integer storage.
    """
    n = len(arr)
    if n < 2:
        return 0
    width = max(x.bit_length() for x in arr) + 1
    answer = 0
    for i in range(width):
        bit = 1 << i
        count = sum(1 for x in arr if x & bit)
        contribution = bit * count * (n - count)
        answer += -contribution if i == width - 1 else contribution
    return answer


def popcount(x: int) -> int:
    """Count set bits in the low 32 bits.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Number of set bits, from 0 to 32.

    Examples:
        >>> popcount(5)
        2

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    return (x & 0xffffffff).bit_count()


def bit_reverse(x: int) -> int:
    """Reverse the low 32 bits.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Reversed unsigned 32-bit value.

    Examples:
        >>> bit_reverse(2)
        1073741824

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    x &= 0xffffffff
    x = (x >> 16) | (x << 16)
    x = ((x >> 8) & 0x00FF00FF) | ((x << 8) & 0xFF00FF00)
    x = ((x >> 4) & 0x0F0F0F0F) | ((x << 4) & 0xF0F0F0F0)
    x = ((x >> 2) & 0x33333333) | ((x << 2) & 0xCCCCCCCC)
    return ((x >> 1) & 0x55555555) | ((x << 1) & 0xAAAAAAAA)


def tzcount(x: int) -> int:
    """Count trailing zeros in the low 32 bits.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Trailing-zero count, or 32 if all low 32 bits are zero.

    Examples:
        >>> tzcount(8)
        3

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    x &= 0xffffffff
    return (x & -x).bit_length() - 1 if x else 32


def lzcount(x: int) -> int:
    """Count leading zeros in the low 32 bits.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Leading-zero count, or 32 if all low 32 bits are zero.

    Examples:
        >>> lzcount(2)
        30

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    return 32 - (x & 0xffffffff).bit_length()


def rmbit(x: int) -> int:
    """Extract the rightmost set bit using Python's integer bit operations.

    Args:
        x: Integer of any size; negative values use infinite sign extension.

    Returns:
        x & -x; zero if x is zero.

    Examples:
        >>> rmbit(10)
        2

    Time Complexity:
        O(W), where W is the bit length of x.

    Space Complexity:
        O(W) bits.
    """
    return x & -x


def lmbit(x: int) -> int:
    """Extract the leftmost set bit in the low 32 bits.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Highest power of two present, or 0 if all low 32 bits are zero.

    Examples:
        >>> lmbit(10)
        8

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    x &= 0xffffffff
    return 1 << (x.bit_length() - 1) if x else 0


def filllower(x: int) -> int:
    """Set all low-32-bit positions at or below the leftmost set bit.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Filled unsigned 32-bit value; zero if all low 32 bits are zero.

    Examples:
        >>> filllower(10)
        15

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    return (1 << (x & 0xffffffff).bit_length()) - 1


def fillupper(x: int) -> int:
    """Set all low-32-bit positions at or above the rightmost set bit.

    Args:
        x: Integer, reduced modulo 2**32.

    Returns:
        Filled unsigned 32-bit value; zero if all low 32 bits are zero.

    Examples:
        >>> fillupper(10)
        4294967294

    Time Complexity:
        O(1) for fixed-width integers.

    Space Complexity:
        O(1).
    """
    x &= 0xffffffff
    return -(x & -x) & 0xffffffff
