from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cplib.tools.templates.judge import InteractiveJudge
from cplib.tools.templates.naive import solve
from cplib.tools.tester import _load_module

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT/'cplib/tools/templates'


class TesterTemplatesTest(unittest.TestCase):
    def test_invalid_moves_are_rejected_without_raising(self) -> None:
        for message in ('', '²', 'hello', '1.5', '0', '-1', '8', '9'*10000, '٠'):
            with patch('cplib.tools.templates.judge.random.randint', return_value=3):
                judge = InteractiveJudge()
            self.assertEqual(judge.next_input(message), '0\n')
            self.assertTrue(judge.finished)
            self.assertFalse(judge.accepted)
        with patch('cplib.tools.templates.judge.random.randint', return_value=3):
            judge = InteractiveJudge()
        self.assertEqual(judge.next_input('1\n'), '2\n')
        self.assertEqual(judge.next_input('1\n'), '0\n')
        self.assertTrue(judge.finished)
        self.assertFalse(judge.accepted)

    def test_example_game_and_echo_output(self) -> None:
        for n in range(1, 9):
            with patch('cplib.tools.templates.judge.random.randint', return_value=n):
                judge = InteractiveJudge()
            remaining = set(range(1, 2*n+2))
            while remaining:
                move = max(remaining)
                remaining.remove(move)
                response = judge.next_input(f'{move}\n')
                if remaining:
                    expected = min(remaining)
                    remaining.remove(expected)
                    self.assertEqual(response, f'{expected}\n')
                    self.assertFalse(judge.finished)
                else:
                    self.assertEqual(response, '0\n')
                    self.assertTrue(judge.finished)
                    self.assertTrue(judge.accepted)
        for text in ('', 'no newline', 'with newline\n'):
            self.assertEqual(solve(text), text)

    def test_runner_uses_problem_directory_and_restores_caller(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            problem = root/'problem'
            problem.mkdir()
            for name in ('generator.py', 'naive.py', 'judge.py', 'test_runner.py'):
                (problem/name).write_text((TEMPLATES/name).read_text().replace('num_of_cases=100', 'num_of_cases=2'))
            (problem/'main.py').write_text('import sys\nsys.stdout.write(sys.stdin.read())\n')
            result = subprocess.run([sys.executable, str(problem/'test_runner.py')], cwd=root, env={**os.environ, 'PYTHONPATH': str(ROOT)}, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('AC  : 2', result.stdout)
            self.assertTrue((problem/'log').is_dir())
            self.assertFalse((root/'log').exists())
            module = _load_module(str(problem/'test_runner.py'), '')
            original_cwd = os.getcwd()
            with patch.object(module, 'run_tester', return_value=False) as run, redirect_stdout(StringIO()), self.assertRaises(SystemExit):
                module.main()
            self.assertTrue(run.called)
            self.assertEqual(os.getcwd(), original_cwd)
            with patch.object(module, 'run_tester', return_value=True), redirect_stdout(StringIO()):
                module.main()
            self.assertEqual(os.getcwd(), original_cwd)


if __name__ == '__main__':
    unittest.main()
