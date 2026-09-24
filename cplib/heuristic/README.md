# cplib.heuristic

`cplib.heuristic` contains utilities for heuristic and optimization problems.

## Modules

### `beam_search.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `BeamSearchResult` | class | `BeamSearchResult(...)` | Summary of a beam search run. | Space: O(1) |
| `BeamSearch` | class | `BeamSearch(expand: Callable[[StateT], Iterable[StateT]], evaluate: Callable[[StateT], float], b…` | Reusable beam search solver. | Space: ``O(B)`` plus the temporary candidate frontier. |

### `neighborhood.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `Move` | class | `Move(...)` | Protocol for a reversible local-search move. | Space: Depends on the concrete move implementation. |
| `Neighborhood` | class | `Neighborhood(...)` | Pair a mutable state with its current score. | Space: ``O(1)`` |

### `random.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `SplitMix64` | class | `SplitMix64(seed: int = 0)` | 64-bit SplitMix64 pseudo-random number generator. | Space: ``O(1)`` |
| `XorShift` | class | `XorShift(seed: int = 0)` | xorshift128+ pseudo-random number generator. | Space: ``O(1)`` |

### `simulated_annealing.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `AnnealingSchedule` | class | `AnnealingSchedule(...)` | Cooling schedule for simulated annealing. | Space: O(1) |
| `AnnealingResult` | class | `AnnealingResult(...)` | Result of a simulated annealing run. | Space: O(1) |
| `SimulatedAnnealing` | class | `SimulatedAnnealing(evaluate: Callable[[StateT], float], generate_neighbor: Callable[[StateT, An…` | Reusable simulated annealing solver. | Space: ``O(size of state)`` besides any storage used by user callbacks. |

### `time_manager.py`

| API | Kind | Signature | Summary | Complexity |
| --- | --- | --- | --- | --- |
| `TimeManager` | class | `TimeManager(timeout_seconds: float, start_time: float \| None = None, clock: Callable[[], float]…` | Track elapsed time against a fixed timeout. | Space: ``O(1)`` |
