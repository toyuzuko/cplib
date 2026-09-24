from contextlib import chdir, redirect_stdout
from io import StringIO
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from cplib.tools.tester import OutputType, Result, _load_fixed_cases, _run_main, record_cases

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = 'import random\ndef generate_testcase():\n    return f"{random.randrange(10000)}\\n"\n'
NAIVE = '''import sys
def solve(data):
    return f'{int(data)**2}\\n'
if __name__ == '__main__':
    sys.stdout.write(solve(sys.stdin.read()).replace('\\n', '\\r\\n'))
'''
MAIN = 'import sys\nprint(int(sys.stdin.read())**2)\n'


def initialize(root: Path) -> None:
    for name, source in (('generator.py', GENERATOR), ('naive.py', NAIVE), ('main.py', MAIN), ('judge.py', '')):
        (root/name).write_text(source)


def cli(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, '-m', 'cplib.tools.tester', *arguments], cwd=root, env={**os.environ, 'PYTHONPATH': str(ROOT)}, capture_output=True, text=True, timeout=15)


def snapshot(path: Path) -> dict[str, bytes]:
    return {file.name: file.read_bytes() for file in path.iterdir()}


class TesterBatchContractsTest(unittest.TestCase):
    def test_random_reference_modes_and_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize(root)
            records = []
            for extra in ((), ('--naive-script',)):
                result = cli(root, '-n', '8', '-r', '1234', *extra)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertIn('AC  : 8', result.stdout)
                records.append([p.read_text().split('[input]\n', 1)[1].split('[expected]\n', 1)[0] for p in sorted((root/'log').glob('*.log'))])
            self.assertEqual(records[0], records[1])
            self.assertGreater(len(set(records[0])), 1)
            result = cli(root, '-n', '8', '-r', '9876')
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            other = [p.read_text().split('[input]\n', 1)[1].split('[expected]\n', 1)[0] for p in sorted((root/'log').glob('*.log'))]
            self.assertNotEqual(records[0], other)

    def test_stress_validity_and_max_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize(root)
            (root/'naive.py').unlink()
            (root/'judge.py').write_text('def is_valid(inp, out):\n    return int(out) == int(inp)**2\n')
            (root/'generator.py').write_text('def generate_testcase():\n    raise AssertionError("small generator used")\ndef generate_max_testcase():\n    return "100\\n"\n')
            result = cli(root, '--mode', 'stress', '-n', '3')
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('AC  : 3', result.stdout)
            (root/'main.py').write_text('print(-1)\n')
            result = cli(root, '--mode', 'stress', '-n', '3')
            self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
            self.assertIn('WA  : 3', result.stdout)
            (root/'generator.py').write_text(GENERATOR)
            (root/'main.py').write_text(MAIN)
            result = cli(root, '--mode', 'stress', '-n', '2')
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            (root/'judge.py').write_text('')
            (root/'main.py').write_text('print("any output")\n')
            result = cli(root, '--mode', 'stress', '-n', '1')
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_fixed_cases_optional_outputs_and_custom_checker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize(root)
            (root/'generator.py').unlink()
            (root/'naive.py').unlink()
            cases = root/'fixed'
            cases.mkdir()
            (cases/'ignored.in').mkdir()
            (cases/'10.in').write_text('1 2 3\n')
            (cases/'10.out').write_text('1 2 3\n')
            (cases/'2.in').write_text('4 5\n')
            (root/'main.py').write_text('import sys\nprint(" ".join(reversed(sys.stdin.read().split())))\n')
            (root/'judge.py').write_text('def is_accepted(inp, out, expected):\n    return sorted(out.split()) == sorted(expected.split())\ndef is_valid(inp, out):\n    return out.split() == inp.split()[::-1]\n')
            result = cli(root, '--mode', 'cases', '--cases-dir', 'fixed', '-n', '99')
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('AC  : 2', result.stdout)
            self.assertEqual([case.inp for case in _load_fixed_cases(str(cases))], ['1 2 3\n', '4 5\n'])
            (cases/'10.in').unlink()
            (cases/'2.in').unlink()
            with self.assertRaises(ValueError):
                _load_fixed_cases(str(cases))
            with self.assertRaises(FileNotFoundError):
                _load_fixed_cases(str(root/'missing'))

    def test_recording_modes_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp), redirect_stdout(StringIO()):
            root = Path(tmp)
            initialize(root)
            (root/'generator.py').write_text(GENERATOR.replace('generate_testcase', 'generate_max_testcase')+'def generate_testcase():\n    raise AssertionError("recording did not prefer max generator")\n')
            answers = []
            for i, options in enumerate(({}, {'naive_script': True}, {'record_with': 'main'})):
                directory = root/f'cases{i}'
                record_cases(num_of_cases=12, random_seed=123, cases_dir=str(directory), **options)
                actual = snapshot(directory)
                self.assertEqual(len(actual), 24)
                self.assertIn('case_00.in', actual)
                self.assertIn('case_11.out', actual)
                for case in range(12):
                    value = int(actual[f'case_{case:02d}.in'])
                    self.assertEqual(actual[f'case_{case:02d}.out'], f'{value**2}\n'.encode())
                answers.append(actual)
            self.assertEqual(answers[0], answers[1])
            self.assertEqual(answers[0], answers[2])
            directory = root/'cases0'
            with self.assertRaises(FileExistsError):
                record_cases(num_of_cases=1, cases_dir=str(directory))
            self.assertEqual(snapshot(directory), answers[0])
            record_cases(num_of_cases=1, cases_dir=str(directory), overwrite=True)
            self.assertEqual(set(snapshot(directory)), {'case_0.in', 'case_0.out'})
            self.assertEqual(list(root.glob('.*.record-*')), [])

    def test_failed_generation_preserves_previous_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp), redirect_stdout(StringIO()):
            root = Path(tmp)
            initialize(root)
            directory = root/'cases'
            directory.mkdir()
            (directory/'old.in').write_text('old input')
            (directory/'old.out').write_text('old output')
            previous = snapshot(directory)
            failures = (
                ('calls = 0\ndef solve(inp):\n    global calls\n    calls += 1\n    if calls == 2: raise ValueError("reference failed")\n    return "ok"\n', {}, ValueError),
                ('def solve(inp):\n    return 7\n', {}, TypeError),
                ('raise RuntimeError("reference failed")\n', {'naive_script': True}, subprocess.CalledProcessError),
            )
            for source, options, error in failures:
                (root/'naive.py').write_text(source)
                with self.assertRaises(error):
                    record_cases(num_of_cases=3, cases_dir=str(directory), overwrite=True, **options)
                self.assertEqual(snapshot(directory), previous)
                self.assertEqual(list(root.glob('.*.record-*')), [])
            (root/'main.py').write_text('raise RuntimeError("main failed")\n')
            with self.assertRaisesRegex(RuntimeError, 'main failed'):
                record_cases(num_of_cases=1, cases_dir=str(directory), overwrite=True, record_with='main')
            self.assertEqual(snapshot(directory), previous)
            with self.assertRaises(RuntimeError):
                record_cases(num_of_cases=1, cases_dir='new', record_with='main')
            self.assertFalse((root/'new').exists())

    def test_recording_install_failure_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp), redirect_stdout(StringIO()):
            root = Path(tmp)
            initialize(root)
            (root/'cases').mkdir()
            (root/'cases/old.in').write_text('previous')
            rename = Path.rename
            def fail_install(source: Path, target: Path) -> Path:
                if source.name == 'new':
                    raise OSError('installation failed')
                return rename(source, target)
            with patch.object(Path, 'rename', fail_install), self.assertRaisesRegex(OSError, 'installation failed'):
                record_cases(num_of_cases=2, overwrite=True)
            self.assertEqual(snapshot(root/'cases'), {'old.in': b'previous'})
            self.assertEqual(list(root.glob('.*.record-*')), [])
            (root/'linked').symlink_to(root/'cases', target_is_directory=True)
            with self.assertRaises(ValueError):
                record_cases(cases_dir='linked', overwrite=True)
            self.assertEqual(snapshot(root/'cases'), {'old.in': b'previous'})

    def test_failed_rollback_retains_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp), redirect_stdout(StringIO()):
            root = Path(tmp)
            initialize(root)
            (root/'cases').mkdir()
            (root/'cases/old.in').write_text('previous')
            rename = Path.rename
            def fail_install_and_restore(source: Path, target: Path) -> Path:
                if source.name in ('new', 'previous'):
                    raise OSError('rename failed')
                return rename(source, target)
            with patch.object(Path, 'rename', fail_install_and_restore), self.assertRaises(OSError) as error:
                record_cases(num_of_cases=1, overwrite=True)
            backups = list(root.glob('.cases.record-*/previous'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(snapshot(backups[0]), {'old.in': b'previous'})
            self.assertIn(str(backups[0]), '\n'.join(error.exception.__notes__))

    def test_batch_output_and_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp):
            root = Path(tmp)
            (root/'main.py').write_text('import os\nos.write(1, b"ok\\r\\n")\nos.write(2, b"diagnostic\\xff")\n')
            run = _run_main('', 2.)
            self.assertIs(run.res, Result.AC)
            self.assertEqual(run.out, 'ok\n')
            self.assertTrue(any('diagnostic' in item.value for item in run.logs if item.type is OutputType.error))
            (root/'main.py').write_text('import sys\nprint("partial", flush=True)\nraise RuntimeError("solver failed")\n')
            run = _run_main('', 2.)
            self.assertIs(run.res, Result.RE)
            self.assertEqual(run.out, 'partial\n')
            self.assertTrue(math.isnan(run.elapsed))
            self.assertTrue(any('solver failed' in item.value for item in run.logs))
            (root/'main.py').write_text('import os\nos.write(1, b"\\xff")\n')
            run = _run_main('', 2.)
            self.assertIs(run.res, Result.RE)
            self.assertTrue(any('UTF-8' in item.value for item in run.logs))

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups')
    def test_batch_and_reference_timeouts_stop_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, chdir(tmp), redirect_stdout(StringIO()):
            root = Path(tmp)
            initialize(root)
            child = 'import os,time; from pathlib import Path; Path("child.pid").write_text(str(os.getpid())); time.sleep(5)'
            source = f'import os,sys,subprocess,time\nfrom pathlib import Path\nPath("solver.pid").write_text(str(os.getpid()))\nsubprocess.Popen([sys.executable,"-c",{child!r}])\nwhile not Path("child.pid").exists(): time.sleep(.01)\nprint("partial", flush=True)\nsys.stderr.write("diagnostic\\n"); sys.stderr.flush()\n'
            for parent_sleeps in (True, False):
                (root/'main.py').write_text(source+('time.sleep(5)\n' if parent_sleeps else ''))
                started = time.monotonic()
                run = _run_main('', .5)
                self.assertLess(time.monotonic()-started, 2.)
                self.assertIs(run.res, Result.TLE)
                self.assertEqual(run.out, 'partial\n')
                self.assertTrue(any('diagnostic' in item.value for item in run.logs))
                self.assert_processes_gone(root)
            (root/'cases').mkdir()
            (root/'cases/old.in').write_text('preserve')
            (root/'naive.py').write_text(source+'time.sleep(5)\n')
            with self.assertRaises(subprocess.TimeoutExpired) as error:
                record_cases(num_of_cases=1, timeout=.5, naive_script=True, overwrite=True)
            self.assertEqual(error.exception.timeout, .5)
            self.assertEqual(snapshot(root/'cases'), {'old.in': b'preserve'})
            self.assert_processes_gone(root)

    def assert_processes_gone(self, root: Path) -> None:
        for filename in ('solver.pid', 'child.pid'):
            path = root/filename
            self.assertTrue(path.exists())
            pid = int(path.read_text())
            for _ in range(50):
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(.01)
            else:
                self.fail(f'{filename} still exists')
            path.unlink()


if __name__ == '__main__':
    unittest.main()
