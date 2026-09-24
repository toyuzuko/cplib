# Problem Statement

You are given two deterministic pseudo-random number generators, `SM` and
`XS`. `SM` follows the SplitMix64 recurrence, and `XS` follows the
xorshift128+ recurrence seeded through SplitMix64.

Initially, `SM` is seeded with `SEED_SM`, and `XS` is seeded with `SEED_XS`.
Then you must process `Q` commands.

The supported commands are:

- `SM NEXT` or `XS NEXT`
  - Advance the chosen generator once and output the next 64-bit unsigned
    integer.
- `SM RANDBITS K` or `XS RANDBITS K`
  - Output a uniformly chosen integer in the range `[0, 2^K)`.
- `SM RANDRANGE STOP`
  - Output a uniformly chosen integer from the range `[0, STOP)`.
- `SM RANDRANGE START STOP`
  - Output a uniformly chosen integer from the range `[START, STOP)`.
- `SM RANDRANGE START STOP STEP`
  - Output a uniformly chosen integer from the arithmetic progression defined
    by `range(START, STOP, STEP)`.
- `SM RANDINT A B`
  - Output a uniformly chosen integer in the inclusive interval `[A, B]`.
- `SM CHOICE N X_1 ... X_N`
  - Output one element chosen uniformly from the given list.
- `SM SHUFFLE N X_1 ... X_N`
  - Shuffle the given list in place and output the resulting list.

The `SM` prefix may be replaced by `XS` in every command.

## Input Format

```text
seed_sm seed_xs
q
command_0
...
command_(q-1)
```

Each command line has one of the forms described above. All lists are given as
`N` followed by `N` integers.

## Output Format

Print one line for each command.

- For `NEXT`, `RANDBITS`, `RANDRANGE`, `RANDINT`, and `CHOICE`, print the
  resulting integer.
- For `SHUFFLE`, print the shuffled list as space-separated integers.

## Constraints

The symbols below are configured in `config.py`. The bundled runner uses
`NUM_CASES = 100` and `TIMEOUT_SECONDS = 2.0`. These settings are chosen so
that the property-based verification usually finishes in about 2 seconds.

- `0 <= SEED_SM <= SEED_MAX`
- `0 <= SEED_XS <= SEED_MAX`
- `1 <= Q <= Q_MAX`
- For each `RANDBITS K`, `0 <= K <= BITS_MAX`
- For each `RANDINT A B`, `-VALUE_ABS_MAX <= A <= B <= VALUE_ABS_MAX`
- For each `RANDRANGE` command, the specified range is non-empty and all
  endpoints lie in `[-VALUE_ABS_MAX, VALUE_ABS_MAX]`
- For each `CHOICE` or `SHUFFLE`, `1 <= N <= LIST_MAX`
- For each list value, `-VALUE_ABS_MAX <= X_i <= VALUE_ABS_MAX`

## Notes

The bundled `verify.py` and `score.py` process commands sequentially. Under the
configurable bounds, a coarse worst-case bound per case is
`O(Q_MAX * max(BITS_MAX, LIST_MAX))`.
The verifier also directly checks the floating-point helper `random()` on fixed
seeds.
