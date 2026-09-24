from __future__ import annotations

from dataclasses import dataclass
import random

from config import BITS_MAX, LIST_MAX, Q_MAX, SEED_MAX, STEP_ABS_MAX, VALUE_ABS_MAX


@dataclass(frozen=True, slots=True)
class Command:
    generator: str
    kind: str
    args: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Case:
    seed_sm: int
    seed_xs: int
    commands: tuple[Command, ...]


def _randint_args(rng: random.Random) -> tuple[int, int]:
    left = rng.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX)
    right = rng.randint(left, VALUE_ABS_MAX)
    return left, right


def _randrange1_args(rng: random.Random) -> tuple[int, ...]:
    return (rng.randint(1, VALUE_ABS_MAX),)


def _randrange2_args(rng: random.Random) -> tuple[int, ...]:
    left = rng.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX - 1)
    right = rng.randint(left + 1, VALUE_ABS_MAX)
    return left, right


def _randrange3_args(rng: random.Random) -> tuple[int, ...]:
    step = rng.randint(1, STEP_ABS_MAX)
    if rng.random() < 0.5:
        step = -step
    length = rng.randint(1, LIST_MAX)
    span = abs(step) * length
    if step > 0:
        left = rng.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX - span)
        right = left + span
    else:
        left = rng.randint(-VALUE_ABS_MAX + span, VALUE_ABS_MAX)
        right = left - span
    return left, right, step


def _choice_args(rng: random.Random) -> tuple[int, ...]:
    length = rng.randint(1, LIST_MAX)
    values = tuple(rng.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX) for _ in range(length))
    return (length, *values)


def _shuffle_args(rng: random.Random) -> tuple[int, ...]:
    length = rng.randint(1, LIST_MAX)
    values = tuple(rng.randint(-VALUE_ABS_MAX, VALUE_ABS_MAX) for _ in range(length))
    return (length, *values)


def _random_command(rng: random.Random) -> Command:
    generator = "SM" if rng.random() < 0.5 else "XS"
    kind = rng.choices(
        [
            "next",
            "randbits",
            "randrange1",
            "randrange2",
            "randrange3",
            "randint",
            "choice",
            "shuffle",
        ],
        weights=[2, 2, 1, 1, 1, 2, 2, 1],
        k=1,
    )[0]
    if kind == "next":
        args: tuple[int, ...] = ()
    elif kind == "randbits":
        args = (rng.randint(0, BITS_MAX),)
    elif kind == "randrange1":
        args = _randrange1_args(rng)
    elif kind == "randrange2":
        args = _randrange2_args(rng)
    elif kind == "randrange3":
        args = _randrange3_args(rng)
    elif kind == "randint":
        args = _randint_args(rng)
    elif kind == "choice":
        args = _choice_args(rng)
    elif kind == "shuffle":
        args = _shuffle_args(rng)
    else:
        raise AssertionError(f"unexpected command kind: {kind!r}")
    return Command(generator=generator, kind=kind, args=args)


def generate_case(rng: random.Random) -> Case:
    seed_sm = rng.randint(0, SEED_MAX)
    seed_xs = rng.randint(0, SEED_MAX)

    commands: list[Command] = [
        Command("SM", "next", ()),
        Command("XS", "next", ()),
        Command("SM", "randbits", (0,)),
        Command("XS", "randbits", (BITS_MAX,)),
        Command("SM", "randrange1", _randrange1_args(rng)),
        Command("XS", "randrange2", _randrange2_args(rng)),
        Command("SM", "randrange3", _randrange3_args(rng)),
        Command("XS", "randint", _randint_args(rng)),
        Command("SM", "choice", _choice_args(rng)),
        Command("XS", "shuffle", _shuffle_args(rng)),
    ]

    target = rng.randint(len(commands), Q_MAX)
    while len(commands) < target:
        commands.append(_random_command(rng))

    return Case(seed_sm=seed_sm, seed_xs=seed_xs, commands=tuple(commands))
