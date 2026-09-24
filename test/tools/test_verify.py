import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('cplib_verify', ROOT / 'scripts' / 'verify.py')
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class VerificationWrapperTest(unittest.TestCase):
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
        with patch.object(verify.sys, 'argv', ['verify.py', 'all', '--tle', '10']):
            with patch.object(verify, 'main') as main:
                with patch.object(verify.PythonLanguage, 'list_dependencies'):
                    verify.run()
                    main.assert_called_once_with(args=['run', '--tle', '10'])
                    self.assertIs(verify.PythonLanguage.list_dependencies, verify.list_dependencies)


if __name__ == '__main__':
    unittest.main()
