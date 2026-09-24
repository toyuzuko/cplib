import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TesterExitCodeTest(unittest.TestCase):
    def run_case(self, source: str, *, expected: str | None = 'ok\n', timeout: float = 5.0, stop_on_failure: bool = False) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'main.py').write_text(source)
            (root / 'judge.py').write_text('')
            (root / 'cases').mkdir()
            for i in range(2):
                (root / 'cases' / f'{i}.in').write_text('')
                if expected is not None:
                    (root / 'cases' / f'{i}.out').write_text(expected)
            env = dict(os.environ)
            env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
            cmd = [sys.executable, '-m', 'cplib.tools.tester', '--mode', 'cases', '--timeout', str(timeout)]
            if stop_on_failure:
                cmd.append('--stop-on-failure')
            return subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=30)

    def test_accepted_cases_exit_zero(self) -> None:
        result = self.run_case("print('ok')")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('AC  : 2', result.stdout)

    def test_wrong_answers_exit_nonzero_after_all_cases(self) -> None:
        result = self.run_case("print('wrong')")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('WA  : 2', result.stdout)

    def test_runtime_errors_exit_nonzero_without_expected_output(self) -> None:
        result = self.run_case('raise RuntimeError()', expected=None)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('RE  : 2', result.stdout)

    def test_timeouts_exit_nonzero(self) -> None:
        result = self.run_case('import time; time.sleep(10)', timeout=0.2)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('TLE : 2', result.stdout)

    def test_stop_on_failure_exits_nonzero(self) -> None:
        result = self.run_case("print('wrong')", stop_on_failure=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('WA  : 1', result.stdout)


class TesterModuleLoadingTest(unittest.TestCase):
    def test_standalone_dataclass_modules_and_reload(self) -> None:
        import dataclasses
        from cplib.tools.tester import _load_module
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for directory, value in (('left', 1), ('right', 2)):
                (root/directory).mkdir()
                (root/directory/'generator.py').write_text(
                    'from __future__ import annotations\nfrom dataclasses import dataclass\n'
                    f'@dataclass\nclass Case:\n    value: int = {value}\n'
                )
            left = _load_module(str(root/'left/generator.py'), '')
            right = _load_module(str(root/'right/generator.py'), '')
            self.assertNotEqual(left.__name__, right.__name__)
            self.assertIs(sys.modules[left.__name__], left)
            self.assertIs(sys.modules[right.__name__], right)
            self.assertEqual(dataclasses.asdict(left.Case()), {'value': 1})
            self.assertEqual(dataclasses.asdict(right.Case()), {'value': 2})
            path = root/'left/generator.py'
            path.write_text(path.read_text().replace('= 1', '= 3'))
            reloaded = _load_module(str(path), '')
            self.assertEqual(reloaded.Case().value, 3)
            path.write_text('raise RuntimeError("failed import")\n')
            with self.assertRaises(RuntimeError):
                _load_module(str(path), '')
            self.assertIs(sys.modules[left.__name__], reloaded)
            path = root/'bad.py'
            path.write_text('raise RuntimeError("failed import")\n')
            before = set(sys.modules)
            with self.assertRaises(RuntimeError):
                _load_module(str(path), '')
            self.assertEqual(set(sys.modules), before)
        from cplib.tools import misc
        self.assertIs(_load_module('cplib.tools.misc', ''), misc)

    def test_invalid_configuration(self) -> None:
        from cplib.tools.tester import Tester
        with self.assertRaises(ValueError):
            Tester(num_of_cases=-1)
        for timeout in (0., -1., float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                Tester(timeout=timeout)

    def test_invalid_recording_does_not_touch_existing_cases(self) -> None:
        from cplib.tools.tester import record_cases
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'case_0.in'
            path.write_text('keep')
            for options in ({'num_of_cases': -1}, {'timeout': float('nan')}, {'timeout': 0.}):
                with self.assertRaises(ValueError):
                    record_cases(cases_dir=tmp, overwrite=True, **options)
                self.assertEqual(path.read_text(), 'keep')

    def test_template_runner_propagates_failure(self) -> None:
        templates = ROOT/'cplib/tools/templates'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('generator.py', 'naive.py', 'judge.py', 'test_runner.py'):
                (root/name).write_text((templates/name).read_text().replace('num_of_cases=100', 'num_of_cases=2'))
            for source, expected_code in (('import sys; sys.stdout.write(sys.stdin.read())', 0), ('print("wrong")', 1)):
                (root/'main.py').write_text(source)
                result = subprocess.run([sys.executable, 'test_runner.py'], cwd=root, env={**os.environ, 'PYTHONPATH': str(ROOT)}, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, expected_code, result.stdout+result.stderr)

    def test_local_runners_propagate_failure(self) -> None:
        paths = [path for path in (ROOT/'test/local').rglob('test_runner.py') if 'run_tester(' in path.read_text()]
        self.assertTrue(paths)
        for path in paths:
            for accepted in (False, True):
                with self.subTest(path=path, accepted=accepted):
                    code = (
                        'import runpy, sys\nfrom unittest.mock import patch\n'
                        f'sys.path.insert(0, {str(path.parent)!r})\n'
                        f'with patch("cplib.tools.tester.run_tester", return_value={accepted!r}):\n'
                        f'    runpy.run_path({str(path)!r}, run_name="__main__")\n'
                    )
                    result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0 if accepted else 1, result.stdout+result.stderr)



class TesterInteractiveTest(unittest.TestCase):
    def run_interaction(self, solver: str, judge: str, *, timeout: float = 1.0) -> tuple[subprocess.CompletedProcess[str], str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'main.py').write_text('import os\nfrom pathlib import Path\nPath("solver.pid").write_text(str(os.getpid()))\n'+solver)
            (root/'judge.py').write_text(judge)
            env = {**os.environ, 'PYTHONPATH': str(ROOT)}
            result = subprocess.run([sys.executable, '-m', 'cplib.tools.tester', '-i', '-n', '1', '-t', str(timeout)], cwd=root, env=env, capture_output=True, text=True, timeout=10)
            log = (root/'log/case_0.log').read_text() if (root/'log/case_0.log').exists() else ''
            if (root/'solver.pid').exists():
                pid = int((root/'solver.pid').read_text())
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
            if (root/'child.pid').exists():
                pid = int((root/'child.pid').read_text())
                for _ in range(50):
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(.01)
                else:
                    self.fail('solver descendant was not reaped')
            return result, log

    def one_line_judge(self, *, accepted: bool = True, initial: str = '', reply: str = '') -> str:
        return (
            'class InteractiveJudge:\n'
            f'    init_input = {initial!r}\n    finished = False\n    accepted = {accepted!r}\n'
            '    def next_input(self, line):\n        self.finished = True\n'
            f'        return {reply!r}\n'
        )

    def test_final_reply_and_stderr_drain(self) -> None:
        judge = r'''from __future__ import annotations
from dataclasses import dataclass
@dataclass
class InteractiveJudge:
    init_input: str = 'start\n'
    finished: bool = False
    accepted: bool = False
    def next_input(self, line):
        self.finished = True
        self.accepted = line == '日本語\n'
        return 'stop\n'
'''
        solver = 'import sys\nassert input() == "start"\nsys.stderr.write("x"*200000)\nsys.stderr.flush()\nprint("日本語", flush=True)\nassert input() == "stop"\nassert sys.stdin.read() == ""\n'
        result, log = self.run_interaction(solver, judge, timeout=3.)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('AC  : 1', result.stdout)
        self.assertEqual(sum(len(part) for part in re.findall(r'x{2,}', log)), 200000)
        self.assertIn('日本語', log)
        self.assertIn('stop', log)

    def test_multiple_lines_and_partial_final_line(self) -> None:
        judge = '''class InteractiveJudge:
    init_input = ''
    finished = False
    accepted = False
    count = 0
    def next_input(self, line):
        self.count += 1
        if self.count == 3:
            self.finished = True
            self.accepted = line == 'last'
        return ''
'''
        solver = 'import sys\nsys.stdout.write("one\\r\\ntwo\\nlast")\n'
        result, _ = self.run_interaction(solver, judge)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_wrong_answer_and_premature_eof(self) -> None:
        for solver, judge in (
            ('print("answer", flush=True)\n', self.one_line_judge(accepted=False)),
            ('pass\n', self.one_line_judge()),
        ):
            result, _ = self.run_interaction(solver, judge)
            self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
            self.assertIn('WA  : 1', result.stdout)

    def test_nonzero_exit_after_accepted_answer(self) -> None:
        result, log = self.run_interaction('import sys\nprint("answer", flush=True)\nraise RuntimeError("solver failed")\n', self.one_line_judge())
        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
        self.assertIn('RE  : 1', result.stdout)
        self.assertIn('solver failed', log)
        self.assertIn('status 1', log)

    def test_deadlines_for_blocked_reads_and_writes(self) -> None:
        import time
        for solver, judge in (
            ('import time\ntime.sleep(5)\n', self.one_line_judge()),
            ('import time\ntime.sleep(5)\n', self.one_line_judge(initial='x'*1000000)),
            ('import time\nprint("answer", flush=True)\ntime.sleep(5)\n', self.one_line_judge()),
            ('import time, sys\nsys.stdout.write("partial")\nsys.stdout.flush()\ntime.sleep(5)\n', self.one_line_judge()),
        ):
            start = time.monotonic()
            result, _ = self.run_interaction(solver, judge, timeout=.3)
            self.assertLess(time.monotonic()-start, 3.)
            self.assertEqual(result.returncode, 1, result.stdout[-2000:]+result.stderr)
            self.assertIn('TLE : 1', result.stdout)

    def test_judge_exception_cleans_up_solver(self) -> None:
        judge = 'class InteractiveJudge:\n    init_input = ""\n    finished = False\n    accepted = False\n    def next_input(self, line):\n        raise ValueError("judge failed")\n'
        result, log = self.run_interaction('import time\nprint("answer", flush=True)\ntime.sleep(5)\n', judge)
        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
        self.assertIn('RE  : 1', result.stdout)
        self.assertIn('judge failed', log)

    def test_non_string_judge_messages_are_runtime_errors(self) -> None:
        for judge in (
            self.one_line_judge().replace("init_input = ''", 'init_input = 1'),
            self.one_line_judge().replace("return ''", 'return 1'),
        ):
            result, log = self.run_interaction('import time\nprint("answer", flush=True)\ntime.sleep(5)\n', judge)
            self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
            self.assertIn('RE  : 1', result.stdout)
            self.assertIn('must', log)

    def test_initially_finished_judge(self) -> None:
        judge = 'class InteractiveJudge:\n    init_input = "hello"\n    finished = True\n    accepted = True\n'
        result, _ = self.run_interaction('import sys\nassert sys.stdin.read() == "hello"\n', judge)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups')
    def test_descendant_holding_pipes_is_stopped(self) -> None:
        child = 'import os,time; from pathlib import Path; Path("child.pid").write_text(str(os.getpid())); time.sleep(5)'
        solver = f'import subprocess, sys, time\nsubprocess.Popen([sys.executable, "-c", {child!r}])\nwhile not Path("child.pid").exists():\n    time.sleep(.01)\nprint("answer", flush=True)\n'
        result, _ = self.run_interaction(solver, self.one_line_judge(), timeout=.5)
        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
        self.assertIn('TLE : 1', result.stdout)

    def test_slow_judge_counts_toward_deadline(self) -> None:
        judge = 'import time\nclass InteractiveJudge:\n    init_input = ""\n    finished = False\n    accepted = True\n    def next_input(self, line):\n        time.sleep(.3)\n        self.finished = True\n        return ""\n'
        result, _ = self.run_interaction('print("answer", flush=True)\n', judge, timeout=.2)
        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
        self.assertIn('TLE : 1', result.stdout)


if __name__ == '__main__':
    unittest.main()
