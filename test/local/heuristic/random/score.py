from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence

from scenario import Case
from cplib.tools.type import T

_UINT64_MASK = (1 << 64) - 1
_FLOAT_DENOMINATOR = 1 << 53


class _RandomMixin:
    def _next_uint64(self) -> int:
        raise NotImplementedError

    def next_uint64(self) -> int:
        return self._next_uint64()

    def random(self) -> float:
        return float(self.next_uint64() >> 11) / float(_FLOAT_DENOMINATOR)

    def randbits(self, k: int) -> int:
        if k < 0:
            raise ValueError("k must be non-negative")
        if k == 0:
            return 0
        result = 0
        shift = 0
        while shift < k:
            result |= self.next_uint64() << shift
            shift += 64
        return result & ((1 << k) - 1)

    def _randbelow(self, upper: int) -> int:
        if upper <= 0:
            raise ValueError("upper must be positive")
        bits = upper.bit_length()
        while True:
            candidate = self.randbits(bits)
            if candidate < upper:
                return candidate

    def randrange(
        self,
        start: int,
        stop: int | None = None,
        step: int = 1,
    ) -> int:
        if stop is None:
            start, stop = 0, start
        if step == 0:
            raise ValueError("step must not be zero")
        options = range(start, stop, step)
        size = len(options)
        if size <= 0:
            raise ValueError("empty range")
        return options[self._randbelow(size)]

    def randint(self, a: int, b: int) -> int:
        if a > b:
            raise ValueError("a must be <= b")
        return self.randrange(a, b + 1)

    def choice(self, seq: Sequence[T]) -> T:
        if len(seq) == 0:
            raise IndexError("cannot choose from an empty sequence")
        return seq[self._randbelow(len(seq))]

    def shuffle(self, seq: MutableSequence[T]) -> None:
        for index in range(len(seq) - 1, 0, -1):
            swap_index = self._randbelow(index + 1)
            seq[index], seq[swap_index] = seq[swap_index], seq[index]


class _SplitMix64Ref(_RandomMixin):
    def __init__(self, seed: int = 0) -> None:
        self._state = seed & _UINT64_MASK

    def _next_uint64(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & _UINT64_MASK
        z = self._state
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9 & _UINT64_MASK
        z = (z ^ (z >> 27)) * 0x94D049BB133111EB & _UINT64_MASK
        return z ^ (z >> 31)


class _XorShiftRef(_RandomMixin):
    def __init__(self, seed: int = 0) -> None:
        mixer = _SplitMix64Ref(seed)
        self._state0 = mixer.next_uint64()
        self._state1 = mixer.next_uint64()
        if self._state0 == 0 and self._state1 == 0:
            self._state1 = 0x9E3779B97F4A7C15

    def _next_uint64(self) -> int:
        s1 = self._state0
        s0 = self._state1
        self._state0 = s0
        s1 ^= (s1 << 23) & _UINT64_MASK
        s1 ^= s1 >> 17
        s1 ^= s0
        s1 ^= s0 >> 26
        self._state1 = s1 & _UINT64_MASK
        return (self._state1 + s0) & _UINT64_MASK


def _run_case(
    case: Case,
    splitmix_cls: Callable[[int], _RandomMixin],
    xorshift_cls: Callable[[int], _RandomMixin],
) -> list[object]:
    splitmix = splitmix_cls(case.seed_sm)
    xorshift = xorshift_cls(case.seed_xs)
    outputs: list[object] = []
    for command in case.commands:
        rng = splitmix if command.generator == "SM" else xorshift
        if command.kind == "next":
            outputs.append(rng.next_uint64())
        elif command.kind == "randbits":
            outputs.append(rng.randbits(command.args[0]))
        elif command.kind == "randrange1":
            outputs.append(rng.randrange(command.args[0]))
        elif command.kind == "randrange2":
            outputs.append(rng.randrange(command.args[0], command.args[1]))
        elif command.kind == "randrange3":
            outputs.append(rng.randrange(command.args[0], command.args[1], command.args[2]))
        elif command.kind == "randint":
            outputs.append(rng.randint(command.args[0], command.args[1]))
        elif command.kind == "choice":
            length = command.args[0]
            outputs.append(rng.choice(list(command.args[1 : length + 1])))
        elif command.kind == "shuffle":
            length = command.args[0]
            values = list(command.args[1 : length + 1])
            rng.shuffle(values)
            outputs.append(tuple(values))
        else:
            raise AssertionError(f"unexpected command kind: {command.kind!r}")
    return outputs


def solve_case(case: Case) -> list[object]:
    return _run_case(case, _SplitMix64Ref, _XorShiftRef)
