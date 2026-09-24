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
./expander/cplib-expander.sh main.py main.expanded.py
```

## Verification

```sh
./verify.sh run test/library_checker/unionfind.test.py
```

Run `./verify.sh all` to verify all registered problems.

## License

Original contributions are dedicated to the public domain under
[CC0 1.0 Universal](LICENSE). Implementation references are credited
in the relevant source files.
