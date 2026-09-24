"""
cplib.tools.tester
==================
Reusable local testing framework.

Functional API:
    ``run_tester(...)`` runs the configured tester.

OO API:
    ``Tester(**kwargs).run()`` runs the configured tester.

Supported non-interactive modes:
    ``random`` generates small randomized inputs, compares ``main.py`` against
    ``naive.py``, and preserves the original random tester behavior.

    ``stress`` generates large inputs with ``generator.generate_max_testcase()``
    when available, otherwise ``generator.generate_testcase()``. It does not run
    a reference solver. If ``judge.is_valid(inp, out)`` exists, the output must
    pass that validity check; otherwise any run that avoids TLE/RE is accepted.

    ``cases`` reads fixed ``*.in`` files from ``cases_dir`` and compares each
    output with the sibling ``*.out`` file. If a matching ``*.out`` is absent,
    that input is treated like stress mode.

Optional local package conventions:
    ``generator.generate_max_testcase() -> str`` builds a maximum-size or
    otherwise stressful input, commonly using bounds from ``config.py``.

    ``judge.is_valid(inp, out) -> bool`` validates an output when no trusted
    expected output is available.

Interactive mode uses judge.InteractiveJudge with init_input, finished,
accepted, and next_input(line). A final reply is sent even when finished becomes
True, then solver stdin is closed. Solver stdout is processed line by line
(including a final unterminated line). EOF before finished gives WA; a nonzero
exit or judge exception gives RE. Stderr is drained into the log. The deadline
covers pipe waits and solver exit. Judge callbacks must terminate on their own;
their time is checked after they return. Timed-out solvers are killed and reaped;
on POSIX their isolated process group is also stopped.

The CLI (``python -m cplib.tools.tester -h``) also provides a case recorder for
building fixed ``cases/*.in`` and ``cases/*.out`` corpora.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import importlib
import importlib.util
import os
import pathlib
import random
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from math import isfinite
from queue import Empty, Queue
from threading import Thread
from tempfile import mkdtemp
from types import ModuleType
from typing import Any, Callable, Dict, List, Literal, Optional

# ------------------------- (1) tiny helpers --------------------------


def _load_module(path_or_name: str, default_file: str) -> ModuleType:
    """Load module from dotted path or *.py* file."""
    target = path_or_name or default_file
    if target.endswith(".py") or os.path.sep in target:
        p = pathlib.Path(target).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Module file not found: {p}")
        name = '_cplib_tester_' + hashlib.sha256(str(p).encode()).hexdigest()
        spec = importlib.util.spec_from_file_location(name, p)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create spec for {p}")
        mod = importlib.util.module_from_spec(spec)
        previous = sys.modules.get(name)
        sys.modules[name] = mod
        try:
            # Read the current source even when an edited file has the same
            # size and timestamp granularity as a cached bytecode file.
            exec(compile(p.read_bytes(), str(p), 'exec'), mod.__dict__)
        except BaseException:
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
            raise
        return mod
    return importlib.import_module(target)


def _prep_logdir(path: str = "log") -> None:
    os.makedirs(path, exist_ok=True)
    for f in pathlib.Path(path).glob("*.log"):
        try:
            f.unlink()
        except OSError:
            pass

# ------------------------- (2) enums / dataclass --------------------

class Result(Enum):
    """
    Outcome of one testcase executed by ``Tester``.

    The enum is used both in console summaries and in the per-case log files.
    The names follow standard competitive-programming verifier terminology.
    Each testcase is classified into exactly one of these outcomes.

    Space Complexity:
        O(1)
    """

    AC = 0
    WA = 1
    RE = 2
    TLE = 3

class OutputType(Enum):
    """
    Type of a log fragment captured during testcase execution.

    Input, solver output, expected output, and diagnostics (including stderr)
    are tracked separately. An error log fragment alone does not determine
    whether execution succeeded.
    The enum controls how each fragment is labeled in the log.

    Space Complexity:
        O(1)
    """

    input = 0
    output = 1
    expected = 2
    error = 3

@dataclass
class Output:
    """
    One typed log fragment collected during testcase execution.

    Attributes:
        type: Kind of log fragment.
        value: Raw text written to the log.

    Instances of this class are appended to the per-case log buffer.
    They are later rendered into the saved testcase log.

    Space Complexity:
        O(1)
    """

    type: OutputType
    value: str


@dataclass
class CaseData:
    """
    One non-interactive testcase input and optional expected output.

    Attributes:
        inp: Input text fed to ``main.py``.
        expected: Trusted expected output, or ``None`` when only validity,
            timeout, and runtime-error checks are available.

    Space Complexity:
        O(N + M), where N is the input length and M is the expected output
        length when present.
    """

    inp: str
    expected: Optional[str]


@dataclass
class MainRun:
    """
    Result of one ``main.py`` subprocess execution.

    Attributes:
        out: Captured stdout, including partial output on failure. Invalid
            UTF-8 is replaced for diagnostics and causes RE on a completed run.
        elapsed: Runtime in seconds, ``timeout`` for TLE, or NaN for RE.
        res: ``AC`` when the subprocess completed before judge classification,
            otherwise ``TLE`` or ``RE``.
        logs: Log fragments produced by the subprocess runner.

    Space Complexity:
        O(N), where N is the captured output or error length.
    """

    out: str
    elapsed: float
    res: Result
    logs: List[Output]


Mode = Literal['random', 'stress', 'cases']
RecordWith = Literal['naive', 'main']

# ------------------------- (3) engine (OO) --------------------------

class Tester:
    """Run generated, fixed, or interactive local testcases.

    Helper files are loaded as independent modules registered in sys.modules;
    dotted module names follow normal Python import caching. Each testcase is
    logged, and failures also appear on stdout. stop_on_failure selects whether
    to continue after a failing testcase. Helpers execute trusted Python code.

    Space Complexity:
        O(L + F), where L is the largest testcase's I/O log and F is the total
        fixed-case input/output text loaded in cases mode (zero otherwise).
    """

    def __init__(
        self,
        *,
        num_of_cases: int = 100,
        timeout: float = 2.0,
        random_seed: int = 0,
        verbose: bool = False,
        stop_on_failure: bool = False,
        interactive: bool = False,
        generator: str = "generator.py",
        naive: str = "naive.py",
        naive_script: bool = False,
        judge: str = "judge.py",
        mode: Mode = 'random',
        cases_dir: str = 'cases',
    ) -> None:
        """Configure a test run; helper modules are loaded by run().

        Args:
            num_of_cases: Non-negative number of random, stress, or interactive
                cases. Ignored in fixed cases mode, which uses every input file.
            timeout: Positive finite seconds per solver subprocess. An interactive
                dialogue includes all pipe waits, process exit, and judge callback
                time. Callbacks must terminate; Python callbacks are not preempted.
                Non-interactive generator/reference/checker callbacks have no
                enforced timeout; reference scripts have a separate timeout.
            random_seed: Seed for randomized testcase generation.
            verbose: Whether to print logs for accepted cases as well as failures.
            stop_on_failure: Whether to stop after the first non-AC result.
            interactive: Whether to use judge.InteractiveJudge instead of mode.
            generator: Generator .py file or dotted module name.
            naive: Reference .py file or dotted module; a script path if naive_script.
            naive_script: Whether to run the reference solver as a subprocess.
            judge: Judge .py file or dotted module name.
            mode: Non-interactive mode: random, stress, or cases.
            cases_dir: Directory of .in files and optional matching .out files.

        Returns:
            None.

        Raises:
            ValueError: If mode is unsupported, num_of_cases is negative, or
                timeout is not finite and positive.

        Time Complexity:
            O(1).

        Space Complexity:
            O(1), excluding referenced strings.
        """
        if mode not in ('random', 'stress', 'cases'):
            raise ValueError(f'Unknown tester mode: {mode}')
        if num_of_cases < 0:
            raise ValueError('num_of_cases must be non-negative')
        if not isfinite(timeout) or timeout <= 0:
            raise ValueError('timeout must be finite and positive')
        self.num_of_cases = num_of_cases
        self.timeout = timeout
        self.random_seed = random_seed
        self.verbose = verbose
        self.stop_on_failure = stop_on_failure
        self.interactive = interactive
        self.generator_path = generator
        self.naive_path = naive
        self.naive_script = naive_script
        self.judge_path = judge
        self.mode = mode
        self.cases_dir = cases_dir

        # modules are loaded lazily in run()
        self._gen_mod: Optional[ModuleType] = None
        self._naive_mod: Optional[ModuleType] = None
        self._judge_mod: Optional[ModuleType] = None

    # --------------------- public API --------------------

    def run(self) -> bool:
        """
        Execute all testcases and print a summary.

        Returns:
            True if all testcases pass, otherwise False.

        Time Complexity:
            Depends on ``num_of_cases`` and on the costs of the user-provided
            generator, solver, naive solver, and judge.

        Space Complexity:
            Depends on the sizes of the generated testcases, outputs, and logs.
        """
        random.seed(self.random_seed)
        needs_generator = not self.interactive and self.mode != 'cases'
        self._gen_mod = None if not needs_generator else _load_module(self.generator_path, "generator.py")
        needs_naive = not self.interactive and self.mode == 'random'
        self._naive_mod = (
            None if self.naive_script or not needs_naive else _load_module(self.naive_path, "naive.py")
        )
        self._judge_mod = _load_module(self.judge_path, "judge.py")
        return _engine(
            self,  # pass the object for easy setting access
            self._gen_mod,
            self._naive_mod,
            self._judge_mod,
        )

# ------------------------- (4) public functional API ----------------

def run_tester(**kwargs: Any) -> bool:
    """
    Run :class:`Tester` with keyword arguments.

    Args:
        **kwargs: Configuration passed to :class:`Tester`.

    Returns:
        True if all testcases pass, otherwise False.

    Time Complexity:
        Same as :meth:`Tester.run`.

    Space Complexity:
        Same as :meth:`Tester.run`.
    """
    return Tester(**kwargs).run()


def record_cases(
    *,
    num_of_cases: int = 100,
    timeout: float = 2.0,
    random_seed: int = 0,
    generator: str = 'generator.py',
    naive: str = 'naive.py',
    naive_script: bool = False,
    cases_dir: str = 'cases',
    record_with: RecordWith = 'naive',
    overwrite: bool = False,
) -> None:
    """
    Generate fixed input/output files for ``cases`` mode.

    Args:
        num_of_cases: Non-negative number of cases to record.
        timeout: Per-case timeout in seconds when running script solvers.
        random_seed: Seed for deterministic generation.
        generator: Generator module path or dotted name. Uses
            generate_max_testcase if present, otherwise generate_testcase.
        naive: Trusted naive solver module path or script path.
        naive_script: Whether ``naive`` should be executed as a script.
        cases_dir: Directory where ``case_*.in`` and ``case_*.out`` are written.
        record_with: Trusted solver, either ``naive`` or ``main``.
        overwrite: Replace a non-empty cases_dir when true. The directory is
            dedicated to this corpus: all previous contents are replaced, but
            only after every new input/output pair has been generated.

    Raises:
        FileExistsError: If ``cases_dir`` exists, is non-empty, and
            ``overwrite`` is false.
        ValueError: If record_with is unsupported, num_of_cases is negative,
            timeout is not finite and positive, or cases_dir is a symbolic
            link or filesystem root. Checked before modifying the output directory.
        NotADirectoryError: If cases_dir exists and is not a directory.
        Exception: Generator/reference errors propagate, leaving any previous
            corpus intact. A failing main.py raises RuntimeError with diagnostics.

    Returns:
        None. Generation uses a sibling staging directory; failed generation
        leaves the previous corpus unchanged. Installation uses two directory
        renames with rollback on an installation error, not a crash-atomic
        directory exchange. If rollback also fails, the previous corpus is
        retained in the staging directory identified in the exception note.
        Do not record concurrently into the same directory.

    Time Complexity:
        Depends on ``num_of_cases`` and on the generator and trusted solver.

    Space Complexity:
        O(N + M), where N is the largest generated input and M is the largest
        generated output. O(total new corpus size) additional disk space is
        used while retaining the previous corpus until successful installation.
    """
    if record_with not in ('naive', 'main'):
        raise ValueError(f'Unknown trusted solver: {record_with}')
    if num_of_cases < 0:
        raise ValueError('num_of_cases must be non-negative')
    if not isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')

    path = pathlib.Path(cases_dir).expanduser()
    if path.is_symlink():
        raise ValueError('cases_dir must not be a symbolic link')
    path = path.resolve()
    if path == path.parent:
        raise ValueError('cases_dir must not be a filesystem root')
    if path.exists() and not path.is_dir():
        raise NotADirectoryError(f'cases_dir is not a directory: {path}')
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise FileExistsError(
            f'{path} is non-empty; pass --overwrite to replace the recorded cases'
        )
    random.seed(random_seed)
    gen_mod = _load_module(generator, 'generator.py')
    naive_mod = None if naive_script or record_with == 'main' else _load_module(naive, 'naive.py')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = pathlib.Path(mkdtemp(prefix=f'.{path.name}.record-', dir=path.parent))
    backup = temporary / 'previous'
    installed = False
    try:
        staging = temporary / 'new'
        staging.mkdir()
        width = len(str(max(0, num_of_cases - 1)))
        for case in range(num_of_cases):
            inp = _generate_stress_input(gen_mod)
            if record_with == 'main':
                run = _run_main(inp, timeout)
                if run.res is not Result.AC:
                    diagnostics = ''.join(item.value for item in run.logs if item.type is OutputType.error)
                    raise RuntimeError(f'main.py failed while recording case #{case}: {run.res.name}\n{diagnostics}')
                out = run.out
            elif naive_script:
                run_script = _run_script(naive, inp, timeout)
                run_script.check_returncode()
                out = _decode_output(run_script.stdout)
            else:
                assert naive_mod is not None
                out = naive_mod.solve(inp)
            stem = f'case_{case:0{width}d}'
            (staging / f'{stem}.in').write_text(inp, encoding='utf-8')
            (staging / f'{stem}.out').write_text(out, encoding='utf-8')

        had_previous = path.exists()
        try:
            if had_previous:
                path.rename(backup)
            staging.rename(path)
            installed = True
        except BaseException:
            if backup.exists() and not path.exists():
                try:
                    backup.rename(path)
                except BaseException as exc:
                    exc.add_note(f'Previous cases are retained at {backup}')
                    raise
            raise
        for case in range(num_of_cases):
            stem = f'case_{case:0{width}d}'
            print(f'Recorded {path / f"{stem}.in"} and {path / f"{stem}.out"}')
    finally:
        if installed or not backup.exists():
            shutil.rmtree(temporary)

# ------------------------- (5) internal engine ----------------------

def _engine(
    args: Tester,
    gen_mod: ModuleType | None,
    naive_mod: ModuleType | None,
    judge_mod: ModuleType,
) -> bool:
    """
    Execute the configured tester loop.

    Time Complexity:
        Depends on the selected mode and user-provided generator, solver, and
        judge implementations.

    Space Complexity:
        O(N + M), where N is the largest testcase input/output and M is the
        largest per-case log.
    """
    random.seed(args.random_seed)
    _prep_logdir()

    # default checker
    def default_chk(_: str, out: str, exp: str) -> bool:
        return out == exp

    is_accepted: Callable[[str, str, str], bool] = getattr(
        judge_mod, "is_accepted", default_chk
    )

    stats: Dict[Result, int] = {r: 0 for r in Result}
    slow_t, slow_case = 0.0, -1
    fixed_cases = _load_fixed_cases(args.cases_dir) if not args.interactive and args.mode == 'cases' else None
    total_cases = len(fixed_cases) if fixed_cases is not None else args.num_of_cases

    for case in range(total_cases):
        logs: List[Output] = []

        # =============== INTERACTIVE ====================
        if args.interactive:
            if not hasattr(judge_mod, "InteractiveJudge"):
                raise AttributeError("InteractiveJudge class not found in judge.py")
            judge = judge_mod.InteractiveJudge()
            run = _run_interactive(judge, args.timeout)
            elapsed, res = run.elapsed, run.res
            logs.extend(run.logs)

        # =============== NON-INTERACTIVE ================
        else:
            data = _obtain_case(args, gen_mod, naive_mod, fixed_cases, case)
            logs.append(Output(OutputType.input, data.inp))
            if data.expected is not None:
                logs.append(Output(OutputType.expected, data.expected))

            run = _run_main(data.inp, args.timeout)
            elapsed = run.elapsed
            logs.extend(run.logs)
            if run.res is not Result.AC:
                res = run.res
            elif data.expected is not None:
                accepted = is_accepted(data.inp, run.out, data.expected)
                res = Result.AC if accepted else Result.WA
            else:
                res = _validate_without_expected(data.inp, run.out, judge_mod)

        # ---- logging ----
        _dump(case, total_cases, elapsed, logs, res, args.verbose)
        stats[res] += 1
        if elapsed == elapsed and elapsed > slow_t:
            slow_t, slow_case = elapsed, case
        if args.stop_on_failure and res is not Result.AC:
            break

    # ---- summary ----
    print("\n--- Summary ---")
    for r in Result:
        print(f"{r.name:4}: {stats[r]}")
    if slow_case != -1:
        print(f"Longest execution time: {slow_t:.4f} s  (Case #{slow_case})")
    return all(count == 0 for result, count in stats.items() if result is not Result.AC)


def _run_interactive(judge: Any, timeout: float) -> MainRun:
    """Run one line-based dialogue, with concurrent pipe I/O and a deadline.

    Judge callbacks run in the caller and must terminate. Their elapsed time
    counts toward the deadline, checked before and after each callback.
    """
    logs: list[Output] = []
    events: Queue[tuple[str, str]] = Queue()
    replies: Queue[str | None] = Queue()
    threads: list[Thread] = []
    proc: subprocess.Popen[str] | None = None
    start = time.perf_counter()
    deadline = start + timeout
    result = Result.RE
    elapsed = float('nan')
    try:
        initial: object = judge.init_input
        if not isinstance(initial, str):
            raise TypeError('judge.init_input must be a string')
        logs.append(Output(OutputType.input, initial))
        proc = subprocess.Popen(
            [sys.executable, 'main.py'],
            text=True,
            encoding='utf-8',
            bufsize=1,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == 'posix',
        )
        assert proc.stdin is not None and proc.stdout is not None and proc.stderr is not None
        stdin, stdout, stderr = proc.stdin, proc.stdout, proc.stderr

        def read_output() -> None:
            try:
                for line in stdout:
                    events.put(('line', line))
            except Exception as exc:
                events.put(('error', f'Stdout read failed: {exc}\n'))
            finally:
                events.put(('stdout_eof', ''))

        def read_errors() -> None:
            try:
                while True:
                    text = stderr.read(65536)
                    if not text:
                        break
                    events.put(('stderr', text))
            except Exception as exc:
                events.put(('error', f'Stderr read failed: {exc}\n'))
            finally:
                events.put(('stderr_eof', ''))

        def write_input() -> None:
            try:
                while True:
                    reply = replies.get()
                    if reply is None:
                        break
                    stdin.write(reply)
                    stdin.flush()
            except BrokenPipeError:
                # A solver may finish without consuming the final response.
                pass
            except Exception as exc:
                events.put(('error', f'Stdin write failed: {exc}\n'))
            finally:
                try:
                    stdin.close()
                except BrokenPipeError:
                    pass

        threads = [Thread(target=target, daemon=True) for target in (read_output, read_errors, write_input)]
        for thread in threads:
            thread.start()
        replies.put(initial)
        if judge.finished:
            replies.put(None)
        open_readers = 2
        while open_readers:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(proc.args, timeout)
            try:
                kind, text = events.get(timeout=remaining)
            except Empty:
                raise subprocess.TimeoutExpired(proc.args, timeout) from None
            if kind == 'line':
                logs.append(Output(OutputType.output, text))
                if not judge.finished:
                    reply: object = judge.next_input(text)
                    if not isinstance(reply, str):
                        raise TypeError('judge.next_input must return a string')
                    if time.perf_counter() >= deadline:
                        raise subprocess.TimeoutExpired(proc.args, timeout)
                    logs.append(Output(OutputType.input, reply))
                    replies.put(reply)
                    if judge.finished:
                        replies.put(None)
            elif kind == 'stderr':
                logs.append(Output(OutputType.error, text))
            elif kind == 'error':
                raise RuntimeError(text)
            else:
                open_readers -= 1
                if kind == 'stdout_eof':
                    replies.put(None)
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        returncode = proc.wait(timeout=remaining)
        elapsed = time.perf_counter() - start
        if elapsed >= timeout:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        if returncode:
            logs.append(Output(OutputType.error, f'main.py exited with status {returncode}\n'))
            result, elapsed = Result.RE, float('nan')
        else:
            result = Result.AC if judge.finished and judge.accepted else Result.WA
    except subprocess.TimeoutExpired:
        result, elapsed = Result.TLE, timeout
        logs.append(Output(OutputType.error, 'Execution timed out\n'))
    except Exception as exc:
        result, elapsed = Result.RE, float('nan')
        logs.append(Output(OutputType.error, f'{exc}\n'))
    finally:
        if proc is not None:
            # The POSIX session belongs only to this testcase, including any
            # descendants that inherited its pipes. Never leave a timed-out
            # solver behind or wait indefinitely for those pipes to close.
            readers_alive = any(thread.is_alive() for thread in threads[:2])
            if os.name == 'posix' and (proc.poll() is None or (result in (Result.TLE, Result.RE) and readers_alive)):
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif proc.poll() is None:
                proc.kill()
            proc.wait()
            replies.put(None)
            for thread in threads:
                thread.join(timeout=1.0)
            if all(not thread.is_alive() for thread in threads):
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    if stream is not None:
                        stream.close()
            # Preserve diagnostics emitted while the process was being stopped.
            while True:
                try:
                    kind, text = events.get_nowait()
                except Empty:
                    break
                if kind in ('stderr', 'error'):
                    logs.append(Output(OutputType.error, text))
                    if kind == 'error' and result is not Result.TLE:
                        result, elapsed = Result.RE, float('nan')
                elif kind == 'line':
                    logs.append(Output(OutputType.output, text))
    out = ''.join(item.value for item in logs if item.type is OutputType.output)
    return MainRun(out, elapsed, result, logs)


def _generate_stress_input(gen_mod: ModuleType) -> str:
    """
    Generate a stress input using the optional max-case convention.

    Args:
        gen_mod: Loaded generator module.

    Returns:
        Generated input text.

    Time Complexity:
        Depends on the selected generator function.

    Space Complexity:
        O(N), where N is the generated input length.
    """
    if hasattr(gen_mod, 'generate_max_testcase'):
        return gen_mod.generate_max_testcase()
    if not hasattr(gen_mod, 'generate_testcase'):
        raise AttributeError('generate_testcase not found in generator.py')
    return gen_mod.generate_testcase()


def _obtain_case(
    args: Tester,
    gen_mod: ModuleType | None,
    naive_mod: ModuleType | None,
    fixed_cases: Optional[List[CaseData]],
    case: int,
) -> CaseData:
    """
    Build or read one non-interactive testcase.

    Args:
        args: Tester settings.
        gen_mod: Loaded generator module.
        naive_mod: Loaded naive module, if needed.
        fixed_cases: Fixed cases for ``cases`` mode.
        case: Zero-based case index.

    Returns:
        Testcase input and optional expected output.

    Time Complexity:
        Depends on the selected generator, naive solver, or file size.

    Space Complexity:
        O(N + M), where N is input length and M is expected output length.
    """
    if args.mode == 'cases':
        assert fixed_cases is not None
        return fixed_cases[case]

    if gen_mod is None:
        raise ValueError('generator module is required for non-interactive testing')

    if args.mode == 'stress':
        return CaseData(_generate_stress_input(gen_mod), None)

    if not hasattr(gen_mod, 'generate_testcase'):
        raise AttributeError('generate_testcase not found in generator.py')
    inp = gen_mod.generate_testcase()
    if args.naive_script:
        run = _run_script(args.naive_path, inp, args.timeout)
        run.check_returncode()
        exp = _decode_output(run.stdout)
    else:
        assert naive_mod is not None
        exp = naive_mod.solve(inp)
    return CaseData(inp, exp)


def _load_fixed_cases(cases_dir: str) -> List[CaseData]:
    """
    Read fixed ``*.in`` cases and optional sibling ``*.out`` files.

    Args:
        cases_dir: Directory containing fixed case files.

    Returns:
        Fixed cases sorted by input filename.

    Raises:
        FileNotFoundError: If ``cases_dir`` does not exist.
        ValueError: If no ``*.in`` files exist.

    Time Complexity:
        O(C log C + T), where C is the number of input files and T is their
        total byte length.

    Space Complexity:
        O(T), where T is the total loaded input and expected output length.
    """
    path = pathlib.Path(cases_dir)
    if not path.is_dir():
        raise FileNotFoundError(f'cases_dir not found: {path}')
    inputs = sorted(inp for inp in path.glob('*.in') if inp.is_file())
    if not inputs:
        raise ValueError(f'No *.in files found in {path}')
    cases: List[CaseData] = []
    for inp_path in inputs:
        out_path = inp_path.with_suffix('.out')
        expected = out_path.read_text(encoding='utf-8') if out_path.is_file() else None
        cases.append(CaseData(inp_path.read_text(encoding='utf-8'), expected))
    return cases


def _run_main(inp: str, timeout: float) -> MainRun:
    """
    Run ``main.py`` once and classify subprocess-level failures.

    Args:
        inp: Input text.
        timeout: Per-case timeout in seconds.

    Returns:
        Captured output, elapsed time, subprocess-level result, and log
        fragments.

    Time Complexity:
        Depends on ``main.py`` and the timeout.

    Space Complexity:
        O(N), where N is the captured stdout or stderr length.
    """
    logs: list[Output] = []
    start = time.perf_counter()
    try:
        run = _run_script('main.py', inp, timeout)
    except subprocess.TimeoutExpired as exc:
        output = exc.output or b''
        error = exc.stderr or b''
        out = _decode_output(output, errors='replace')
        err = _decode_output(error, errors='replace')
        logs.append(Output(OutputType.output, out))
        if err:
            logs.append(Output(OutputType.error, err))
        logs.append(Output(OutputType.error, 'Execution timed out\n'))
        return MainRun(out, timeout, Result.TLE, logs)
    except OSError as exc:
        logs.append(Output(OutputType.error, f'{exc}\n'))
        return MainRun('', float('nan'), Result.RE, logs)
    elapsed = time.perf_counter() - start
    invalid_output = False
    try:
        out = _decode_output(run.stdout)
    except UnicodeDecodeError:
        out = _decode_output(run.stdout, errors='replace')
        invalid_output = True
    logs.append(Output(OutputType.output, out))
    if run.stderr:
        logs.append(Output(OutputType.error, _decode_output(run.stderr, errors='replace')))
    if run.returncode or invalid_output:
        if run.returncode:
            logs.append(Output(OutputType.error, f'main.py exited with status {run.returncode}\n'))
        if invalid_output:
            logs.append(Output(OutputType.error, 'Stdout is not valid UTF-8\n'))
        return MainRun(out, float('nan'), Result.RE, logs)
    return MainRun(out, elapsed, Result.AC, logs)


def _decode_output(data: bytes | str | None, errors: Literal['strict', 'replace'] = 'strict') -> str:
    """Decode captured text with the former runner's universal-newline rules."""
    text = data.decode('utf-8', errors=errors) if isinstance(data, bytes) else data or ''
    return text.replace('\r\n', '\n').replace('\r', '\n')


def _run_script(script: str, inp: str, timeout: float) -> subprocess.CompletedProcess[bytes]:
    """Run a batch solver and stop its owned POSIX process group on failure.

    Bytes are retained for diagnostics, including incomplete UTF-8 at a timeout.
    Trusted reference failures are left to the caller to classify or propagate.
    """
    start = time.perf_counter()
    with subprocess.Popen(
        [sys.executable, script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name == 'posix',
    ) as proc:
        communication_done = False
        try:
            out, err = proc.communicate(inp.encode('utf-8'), timeout=max(0.0, timeout - (time.perf_counter() - start)))
            communication_done = True
            if time.perf_counter() - start >= timeout:
                raise subprocess.TimeoutExpired(proc.args, timeout, output=out, stderr=err)
        except BaseException as exc:
            if isinstance(exc, subprocess.TimeoutExpired):
                exc.timeout = timeout
            if os.name == 'posix' and (proc.poll() is None or not communication_done):
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    # Some sandboxes report EPERM for a process group whose
                    # leader exited between poll() and killpg().
                    if proc.poll() is None:
                        raise
            elif proc.poll() is None:
                proc.kill()
            proc.wait()
            raise
        return subprocess.CompletedProcess(proc.args, proc.wait(), out, err)


def _validate_without_expected(inp: str, out: str, judge_mod: ModuleType) -> Result:
    """
    Classify a successful run when no expected output is available.

    Args:
        inp: Input text.
        out: Solver output.
        judge_mod: Loaded judge module.

    Returns:
        ``AC`` if the optional validity checker passes or is absent, otherwise
        ``WA``.

    Time Complexity:
        Depends on ``judge.is_valid`` when present.

    Space Complexity:
        Depends on ``judge.is_valid`` when present, otherwise O(1).
    """
    is_valid = getattr(judge_mod, 'is_valid', None)
    if is_valid is None:
        return Result.AC
    return Result.AC if is_valid(inp, out) else Result.WA


def _dump(case: int, total_cases: int, t: float, logs: List[Output], res: Result, verbose: bool) -> None:
    """
    Write one testcase log to stdout and the ``log`` directory.

    Args:
        case: Zero-based case index.
        total_cases: Total number of cases in the run.
        t: Runtime in seconds, timeout value, or NaN.
        logs: Log fragments to render.
        res: Final testcase result.
        verbose: Whether to print AC logs to stdout.

    Time Complexity:
        O(N), where N is the total log length.

    Space Complexity:
        O(1) beyond the provided log fragments.
    """
    name = f"log/case_{case:0{len(str(total_cases - 1))}d}.log"
    print(f"Case #{case} [judge]: {res.name}")
    if verbose or res is not Result.AC:
        for seg in logs:
            print(f"[{seg.type.name}]\n{seg.value}", end="")
    with open(name, "w", encoding="utf-8") as fh:
        fh.write(
            f"Case #{case}\nExecution time: {t:.3f} s\nResult: {res.name}\n"
        )
        for seg in logs:
            fh.write(f"[{seg.type.name}]\n{seg.value}")
        fh.write("\n")

# -------------------- (6) CLI wrapper --------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run the CP tester as CLI.")
    p.add_argument("-n", "--num-of-cases", type=int, default=100)
    p.add_argument("-t", "--timeout", type=float, default=2.0)
    p.add_argument("-r", "--random-seed", type=int, default=0)
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("-s", "--stop-on-failure", action="store_true")
    p.add_argument("-i", "--interactive", action="store_true")
    p.add_argument("--generator", default="generator.py")
    p.add_argument("--naive", default="naive.py")
    p.add_argument("--naive-script", action="store_true")
    p.add_argument("--judge", default="judge.py")
    p.add_argument("--mode", choices=("random", "stress", "cases"), default="random")
    p.add_argument("--cases-dir", default="cases")
    p.add_argument("--record", action="store_true")
    p.add_argument("--record-with", choices=("naive", "main"), default="naive")
    p.add_argument("--overwrite", action="store_true")
    return p

def _cli_main() -> None:
    ns = _build_parser().parse_args()
    if ns.record:
        try:
            record_cases(
                num_of_cases=ns.num_of_cases,
                timeout=ns.timeout,
                random_seed=ns.random_seed,
                generator=ns.generator,
                naive=ns.naive,
                naive_script=ns.naive_script,
                cases_dir=ns.cases_dir,
                record_with=ns.record_with,
                overwrite=ns.overwrite,
            )
        except FileExistsError as exc:
            print(f'Recording aborted: {exc}', file=sys.stderr)
            raise SystemExit(1) from exc
        return
    succeeded = run_tester(
        num_of_cases=ns.num_of_cases,
        timeout=ns.timeout,
        random_seed=ns.random_seed,
        verbose=ns.verbose,
        stop_on_failure=ns.stop_on_failure,
        interactive=ns.interactive,
        generator=ns.generator,
        naive=ns.naive,
        naive_script=ns.naive_script,
        judge=ns.judge,
        mode=ns.mode,
        cases_dir=ns.cases_dir,
    )
    if not succeeded:
        raise SystemExit(1)

if __name__ == "__main__":
    _cli_main()
