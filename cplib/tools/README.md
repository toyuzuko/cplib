# cplib.tools

`cplib.tools` contains utility code for I/O, testing, and shared types.

## Modules

### `fastio.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `FastIO` | class | `FastIO(...)` | Buffered input/output for PyPy contest scripts. | Space: O(BUFFER_SIZE + longest token or line + buffered output), under normal reads. Explicit load() calls also retain all unread input. |

### `misc.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `yneos` | function | `yneos(result: bool) -> str` | Convert a boolean into ``'Yes'`` or ``'No'``. | Time: O(1) |

### `tester.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Result` | class | `Result(...)` | Outcome of one testcase executed by ``Tester``. | Space: O(1) |
| `OutputType` | class | `OutputType(...)` | Type of a log fragment captured during testcase execution. | Space: O(1) |
| `Output` | class | `Output(...)` | One typed log fragment collected during testcase execution. | Space: O(1) |
| `CaseData` | class | `CaseData(...)` | One non-interactive testcase input and optional expected output. | Space: O(N + M), where N is the input length and M is the expected output length when present. |
| `MainRun` | class | `MainRun(...)` | Result of one ``main.py`` subprocess execution. | Space: O(N), where N is the captured output or error length. |
| `Tester` | class | `Tester(*, num_of_cases: int = 100, timeout: float = 2.0, random_seed: int = 0, verbose: bool =…` | Run generated, fixed, or interactive local testcases. | Space: O(L + F), where L is the largest testcase's I/O log and F is the total fixed-case input/output text loaded in cases mode (zero otherwise). |
| `run_tester` | function | `run_tester(**kwargs: Any) -> bool` | Run :class:`Tester` with keyword arguments. | Time: Same as :meth:`Tester.run`. |
| `record_cases` | function | `record_cases(*, num_of_cases: int = 100, timeout: float = 2.0, random_seed: int = 0, generator:…` | Generate fixed input/output files for ``cases`` mode. | Time: Depends on ``num_of_cases`` and on the generator and trusted solver. |

### `type.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Comparable` | class | `Comparable(...)` | Protocol for types that define a strict weak ordering. | — |
