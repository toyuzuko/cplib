# cplib

Algorithms and data structures for competitive programming in Python.
The library covers graphs and trees, data structures, strings, mathematics,
geometry, sequences, and heuristic utilities.

See the package READMEs and module docstrings for API details, and
`test/library_checker/` and `test/aoj/` for examples.

## Setup

Python 3.11 or later is required. PyPy is recommended; `FastIO` requires PyPy.
Run the following commands from the repository directory:

```sh
uv python install
uv sync --locked --group dev
```

## Usage

```python
from cplib.datastructure.dsu import DisjointSetUnion

uf = DisjointSetUnion(5)
uf.merge(0, 1)
assert uf.same(0, 1)
```

Expand your solution into a single file for submission:

```sh
./expander.sh main.py
```

By default, the result is written to `./tmp/main.expanded.py`.
Pass an output path as the second argument, or `-` to write to stdout:

```sh
./expander.sh main.py submission.py
./expander.sh main.py -
```

## Verification

Verification uses `online-judge-verify-helper` (`oj-verify`) through `verify.sh`.

```sh
./verify.sh run test/library_checker/unionfind.test.py
```

Run `./verify.sh all` to verify all registered problems.
Use `./verify.sh -h` for usage examples and options, including per-case time
limits and parallel execution. Use `./expander.sh -h` for expansion options.

Each run saves the verdicts, elapsed times, and peak memory reported by the
underlying `oj test` command in `tmp/verify/<timestamp>/results.json`, with a
per-file overview in `summary.md`. These are the same measurements used in the
console output; no additional test run or separate per-case measurement is made.
Saved times are in seconds, and memory values are converted to MiB.
Memory measurements require GNU time (`gtime` on macOS). Unavailable measurements
are recorded as `null`; files skipped by the verification cache are not measured.

## License

Original contributions are dedicated to the public domain under
[CC0 1.0 Universal](LICENSE). Implementation references are credited
in the relevant source files.
