import importlib.util
import io
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('cplib_verify', ROOT / 'scripts' / 'verify.py')
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class VerificationWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        cwd = patch.object(verify.Path, 'cwd', return_value=self.root)
        cwd.start()
        self.addCleanup(cwd.stop)

    def test_dependencies_include_library_helpers_and_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            names = ('cplib/graph.py', 'test/problem.test.py', 'test/helper.py', 'scripts/verify.py', 'uv.lock', 'pyproject.toml', '.python-version', 'verify.sh')
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('')
            (root / '.env').write_text('')
            actual = verify.list_dependencies(None, root / 'test/problem.test.py', basedir=root)
            expected = {root / name for name in names} | {root / name for name in ('cplib', 'test', 'scripts')}
            self.assertEqual(set(actual), expected)

    def test_all_runs_verification_without_documentation(self) -> None:
        original = verify.PythonLanguage.list_dependencies

        def main(*, args: list[str]) -> None:
            parsed = verify.get_parser().parse_args(args)
            self.assertEqual(parsed.subcommand, 'run')
            self.assertEqual(parsed.config_file, 'custom.toml')
            self.assertEqual(parsed.tle, 10)
            self.assertEqual(parsed.jobs, 2)
            self.assertIs(verify.PythonLanguage.list_dependencies, verify.list_dependencies)

        with patch.object(verify.sys, 'argv', ['verify.py', '--config-file', 'custom.toml', 'all', '--tle', '10', '-j', '2']):
            with patch.object(verify, 'main', side_effect=main), redirect_stderr(io.StringIO()):
                verify.run()
        self.assertIs(verify.PythonLanguage.list_dependencies, original)
        result = json.loads(next(self.root.glob('tmp/verify/*/results.json')).read_text())
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['files'], [])

    def test_help_does_not_create_report(self) -> None:
        with patch.object(verify.sys, 'argv', ['verify.py', 'run', '-h']), redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                verify.run()
        self.assertEqual(raised.exception.code, 0)
        self.assertFalse((self.root / 'tmp').exists())

    def test_case_statistics_and_unavailable_memory(self) -> None:
        report = verify.VerificationReport(['run', 'solution.test.py'])

        def execute(command: list[str]) -> None:
            logfile = Path(command[command.index('--log-file') + 1])
            cases = [
                {'testcase': {'name': 'one'}, 'status': 'AC', 'exitcode': 0, 'elapsed': 0.25, 'memory': 32.768, 'output': 'large output'},
                {'testcase': {'name': 'two'}, 'status': 'TLE', 'exitcode': -9, 'elapsed': 0.75, 'memory': None, 'output': ''},
            ]
            logfile.write_text(json.dumps(cases))
            raise subprocess.CalledProcessError(1, command)

        def verify_file(*args: object, **kwargs: object) -> bool:
            try:
                report.exec_command(['oj', 'test'])
            except subprocess.CalledProcessError:
                return False
            return True

        report.original_exec_command = execute
        report.original_verify_file = verify_file
        self.assertFalse(report.verify_file(self.root / 'solution.test.py', compilers=[], tle=1, jobs=1))
        with redirect_stderr(io.StringIO()):
            report.finish(1)
        result = json.loads((report.directory / 'results.json').read_text())
        record = result['files'][0]
        self.assertEqual(record['status'], 'FAILED')
        self.assertEqual(record['summary'], {
            'case_count': 2, 'verdicts': {'AC': 1, 'TLE': 1},
            'max_time_seconds': 0.75, 'mean_time_seconds': 0.5, 'max_memory_mib': 32.0,
        })
        self.assertIsNone(record['cases'][1]['memory_mib'])
        self.assertNotIn('output', record['cases'][0])
        self.assertFalse((report.directory / 'cases.pending.json').exists())

    def test_real_oj_failure_is_reported_without_changing_exit_code(self) -> None:
        # Exercise the installed oj JSON format, including its nonzero WA exit.
        directory = self.root / 'cases'
        directory.mkdir()
        (directory / 'sample.in').write_text('')
        (directory / 'sample.out').write_text('43\n')
        oj = Path(sys.executable).parent / 'oj'
        command = [str(oj), 'test', '-d', str(directory), '-c', shlex.join([sys.executable, '-c', 'print(42)'])]

        def execute(command: list[str]) -> None:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def verify_file(*args: object, **kwargs: object) -> bool:
            try:
                verify.verifier.exec_command(command)
            except subprocess.CalledProcessError:
                return False
            return True

        def main(*, args: list[str]) -> None:
            result = verify.verifier.verify_file(self.root / 'solution.test.py', compilers=[], tle=1, jobs=1)
            raise SystemExit(0 if result else 1)

        with patch.object(verify.verifier, 'exec_command', side_effect=execute), patch.object(verify.verifier, 'verify_file', side_effect=verify_file):
            with patch.object(verify, 'main', side_effect=main), patch.object(verify.sys, 'argv', ['verify.py', 'run', 'solution.test.py']):
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    verify.run()
        self.assertEqual(raised.exception.code, 1)
        result = json.loads(next(self.root.glob('tmp/verify/*/results.json')).read_text())
        self.assertEqual(result['exit_code'], 1)
        record = result['files'][0]
        self.assertEqual(record['status'], 'FAILED')
        self.assertEqual(record['measurement_errors'], [])
        self.assertEqual(record['summary']['verdicts'], {'WA': 1})
        self.assertGreater(record['cases'][0]['time_seconds'], 0)

    def test_download_failure_does_not_create_zero_measurements(self) -> None:
        report = verify.VerificationReport(['run'])
        report.original_verify_file = lambda *args, **kwargs: False
        report.verify_file(self.root / 'solution.test.py', compilers=[], tle=1, jobs=1)
        with redirect_stderr(io.StringIO()):
            report.finish(1)
        result = json.loads((report.directory / 'results.json').read_text())
        stats = result['files'][0]['summary']
        self.assertEqual(stats['case_count'], 0)
        self.assertIsNone(stats['max_time_seconds'])
        self.assertIsNone(stats['max_memory_mib'])


if __name__ == '__main__':
    unittest.main()
