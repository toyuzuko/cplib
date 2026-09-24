import os
import ast
from contextlib import redirect_stderr
from io import StringIO
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
EXPANDER_SCRIPT = ROOT_DIR / 'expander.sh'


class ExpanderIntegrationTest(unittest.TestCase):
    def test_default_output_from_another_directory(self) -> None:
        from expand_cplib import resolve_cplib_path

        with patch.dict(os.environ, {}, clear=True), patch('expand_cplib.find_installed_cplib_path', side_effect=AssertionError('Must locate the adjacent library')):
            self.assertEqual(resolve_cplib_path(ROOT_DIR / 'scripts/expander/expand_cplib.py'), ROOT_DIR / 'cplib')
        with tempfile.TemporaryDirectory(prefix='cplib-expand-default-') as folder:
            root = Path(folder)
            source = root / 'solutions' / 'sample.test.py'
            source.parent.mkdir()
            original = 'from cplib.mathematics.utility import sign\nprint(sign(-3))\n'
            source.write_text(original)
            result = subprocess.run([str(EXPANDER_SCRIPT), 'solutions/sample.test.py'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertEqual(source.read_text(), original)
            output = root / 'tmp' / 'sample.test.expanded.py'
            self.assertTrue(output.is_file())
            run = subprocess.run([sys.executable, '-S', str(output)], cwd=root, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout, '-1\n')

    def assert_strict_types(self, code: str) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expanded-types-') as folder:
            source = Path(folder) / 'expanded.py'
            source.write_text(code, encoding='utf-8')
            result = subprocess.run([str(ROOT_DIR / '.venv/bin/pyright'), '--project', str(ROOT_DIR), str(source)], cwd=ROOT_DIR, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_generic_tree_keeps_names_and_strict_types(self) -> None:
        source = (ROOT_DIR / 'test/library_checker/point_set_tree_path_composite_sum.test.py').read_text(encoding='utf-8')
        code, stdout = self.run_expander(source, '3 2\n1 2 3\n0 1 4 5\n1 2 6 7\n0 2 8 0\n1 0 9 10 1\n')
        self.assertEqual(stdout, '239\n76\n')
        self.assertIn('class RerootingLinkCutTreeWithEdges(Generic[ValueT, PointT, PathT]):', code)
        self.assertIn('class FastIO:', code)
        self.assertNotIn('_cplib_', code)
        self.assertIn('import __pypy__  # pyright: ignore[reportMissingModuleSource]', code)
        self.assert_strict_types(code)

    def test_typevar_collision_keeps_valid_declaration(self) -> None:
        code, stdout = self.run_expander('''
            from cplib.datastructure.cumulative import Cumulative

            ValueT = 7
            cum = Cumulative[int](3, 0, lambda a, b: a + b, lambda a, b: a - b)
            cum.build([2, 3, 5])
            print(cum.prod(0, 3), ValueT)
        ''')
        self.assertEqual(stdout, '10 7\n')
        self.assertIn("_cplib_tools_type_ValueT = TypeVar('_cplib_tools_type_ValueT')", code)
        self.assert_strict_types(code)

    def test_toptree_keeps_short_typing_imports(self) -> None:
        source = (ROOT_DIR / 'test/library_checker/point_set_tree_path_composite_sum.toptree.test.py').read_text(encoding='utf-8')
        code, stdout = self.run_expander(source, '3 2\n1 2 3\n0 1 4 5\n1 2 6 7\n0 2 8 0\n1 0 9 10 1\n')
        self.assertEqual(stdout, '239\n76\n')
        self.assertIn('from collections.abc import Callable\n', code)
        self.assertIn('from collections.abc import Sequence\n', code)
        self.assertTrue(any(isinstance(node, ast.ImportFrom) and node.module == 'typing' and any(alias.name == 'Generic' and alias.asname is None for alias in node.names) for node in ast.parse(code).body))
        self.assertNotIn('_cplib_', code)
        self.assert_strict_types(code)

    def test_typing_import_aliases_keep_real_collisions(self) -> None:
        source = (ROOT_DIR / 'test/library_checker/point_set_tree_path_composite_sum.toptree.test.py').read_text(encoding='utf-8')
        source += '\nGeneric = 7\nSequence = 9\nprint(Generic)\ndef local(Sequence: int) -> int:\n    return Sequence\nprint(local(Sequence))\n'
        code, stdout = self.run_expander(source, '1 1\n2\n0 0 3 0\n')
        self.assertEqual(stdout, '7\n9\n3\n')
        self.assertIn('from typing import Generic as _cplib_', code)
        self.assertIn('from collections.abc import Sequence as _cplib_', code)
        self.assert_strict_types(code)

    def test_import_alias_cleanup_preserves_strings_and_snapshots(self) -> None:
        from module_symbols import simplify_import_aliases

        generated = {'_cplib_Generic', '_cplib_other_Generic'}
        source = 'label = "日本語"; from typing import Generic as _cplib_Generic  # _cplib_Generic\nvalue = _cplib_Generic\n'
        expected = 'label = "日本語"; from typing import Generic  # _cplib_Generic\nvalue = Generic\n'
        self.assertEqual(simplify_import_aliases(source, generated), expected)
        for suffix in ('annotation: "_cplib_Generic[int]"\n', 'annotation: "Generic[int]"\n', 'from typing import Generic as _cplib_other_Generic\n'):
            with self.subTest(suffix=suffix):
                self.assertEqual(simplify_import_aliases(source + suffix, generated), source + suffix)

    def test_import_alias_cleanup_distinguishes_docstrings_and_class_scope(self) -> None:
        from module_symbols import simplify_import_aliases

        prefix = 'from math import gcd as _cplib_gcd\n'
        source = prefix + '''
class Demo:
    """Describe gcd without reserving it as an identifier."""
    def gcd(self):
        return _cplib_gcd(6, 9)
print(Demo().gcd())
'''
        code = simplify_import_aliases(source, {'_cplib_gcd'})
        self.assertNotIn('_cplib_gcd', code)
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, '3\n')
        source = prefix + '''
class Demo:
    def gcd(a, b):
        return 99
    value = _cplib_gcd(6, 9)
'''
        self.assertEqual(simplify_import_aliases(source, {'_cplib_gcd'}), source)

    def test_statement_type_directives_survive_expansion(self) -> None:
        code, stdout = self.run_expander('''
            from cplib.datastructure.queue import DeletablePriorityQueue

            heap = DeletablePriorityQueue[int](ascending=False)
            heap.build([2, 1, 3])
            print(heap.pop())
        ''')
        self.assertEqual(stdout, '3\n')
        self.assertIn('pyright: ignore[reportPrivateUsage, reportArgumentType]', code)
        self.assert_strict_types(code)

    def test_package_submodule_imports(self) -> None:
        _, stdout = self.run_expander(
            """
            from cplib.geometry import floating as first, integer
            import cplib.geometry.floating as second
            from cplib.geometry.floating import get_eps
            from cplib import geometry

            print(first is second is geometry.floating)
            first.set_eps(0.125)
            print(second.get_eps(), get_eps(), integer.Point(2, 3).x)
            print(geometry.floating.get_eps())
            """
        )
        self.assertEqual(stdout.splitlines(), ['True', '0.125 0.125 2', '0.125'])

    def test_nested_submodule_imports(self) -> None:
        _, stdout = self.run_expander(
            """
            def number():
                from cplib.mathematics import utility as m
                return m.sign(-3)

            def tolerance():
                from cplib.geometry import floating as m
                return m.get_eps()

            def qualified():
                import cplib.mathematics.utility
                return cplib.mathematics.utility.sign(2)

            def renamed():
                from cplib.mathematics import utility as cplib
                return cplib.sign(-2)

            if False:
                from cplib.geometry import integer as absent
            print(number(), tolerance(), 'm' in globals(), 'absent' in globals())
            from cplib.mathematics import sign, utility as u; print(sign(0), u.sign(2))
            print(qualified(), renamed())
            """
        )
        self.assertEqual(stdout.splitlines(), ['-1 1e-10 False False', '0 1', '1 -1'])

    def test_package_child_attribute_usage(self) -> None:
        _, stdout = self.run_expander(
            """
            from cplib.geometry import floating
            from cplib import geometry as g
            print(g.floating.get_eps())
            """
        )
        self.assertEqual(stdout.strip(), '1e-10')

    def test_submodule_import_uses_current_package_attribute(self) -> None:
        _, stdout = self.run_expander(
            """
            from cplib.geometry import floating
            from cplib import geometry
            geometry.floating = 13
            from cplib.geometry import floating as replacement
            print(replacement, floating.get_eps())
            del geometry.floating
            from cplib.geometry import floating as restored
            print(restored is floating)
            """
        )
        self.assertEqual(stdout.splitlines(), ['13 1e-10', 'True'])

    def test_package_exports_take_priority_over_submodule_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expander-package-') as folder:
            root = Path(folder)
            package = root/'cplib'
            for name in ('algorithm', 'datastructure', 'geometry', 'graph', 'mathematics', 'string', 'tools'):
                (package/name).mkdir(parents=True)
            (package/'__init__.py').write_text('')
            (package/'algorithm/__init__.py').write_text('VALUE = 3\nshadowed = 17\n')
            (package/'algorithm/left.py').write_text('VALUE = 5\ndef read():\n    return VALUE\n')
            (package/'algorithm/shadowed.py').write_text('This unused file is not valid Python.\n')
            source = '''
from cplib.algorithm import VALUE, left as m, shadowed
from cplib.algorithm.left import VALUE as snapshot
import cplib.algorithm.left as same
print(VALUE, m.read(), shadowed, m is same)
m.VALUE = 9
print(m.read(), snapshot)
def inner():
    from cplib.algorithm import left as local, VALUE as value
    return local.VALUE + value
print(inner(), 'local' in globals())
'''
            main, output = root/'main.py', root/'expanded.py'
            main.write_text(source)
            expected = subprocess.run([sys.executable, '-S', str(main)], env={**os.environ, 'PYTHONPATH': str(root)}, capture_output=True, text=True, check=True)
            expansion = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), str(output)], env={**os.environ, 'CPLIB_DIR': str(package)}, capture_output=True, text=True)
            self.assertEqual(expansion.returncode, 0, expansion.stderr)
            actual = subprocess.run([sys.executable, '-S', str(output)], env={key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}, capture_output=True, text=True)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(actual.stdout, expected.stdout)

    def test_from_import_snapshots_without_module_objects(self) -> None:
        code, stdout = self.run_expander(
            """
            from cplib.geometry.floating import EPS, get_eps, set_eps

            set_eps(0.125)
            print(EPS, get_eps())
            from cplib.geometry.floating import EPS as current
            print(current)
            """
        )
        self.assertEqual(stdout.splitlines(), ['1e-10 0.125', '0.125'])
        self.assertNotIn('class _CPLIB_MODULE', code)

    def test_imported_bindings_are_independent_snapshots(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expander-bindings-') as folder:
            root = Path(folder)
            package = root/'cplib'
            for name in ('algorithm', 'datastructure', 'geometry', 'graph', 'mathematics', 'string', 'tools'):
                (package/name).mkdir(parents=True)
            (package/'__init__.py').write_text('')
            (package/'algorithm/left.py').write_text('from math import gcd\nVALUE = 3\ndef read():\n    return VALUE\ndef set_value(value):\n    global VALUE\n    VALUE = value\ndef use_gcd():\n    return gcd(6, 9)\n')
            (package/'algorithm/right.py').write_text('from cplib.algorithm.left import VALUE, read as original_read\nfrom math import gcd\ndef read():\n    return VALUE\ndef use_gcd():\n    return gcd(6, 9)\n')
            source = '''
import cplib.algorithm.left as left
import cplib.algorithm.right as right
from cplib.algorithm.left import VALUE, read
left.set_value(5)
print(left.VALUE, right.VALUE, VALUE, right.read(), right.original_read())
right.VALUE = 13
print(left.VALUE, right.VALUE, right.read())
left.read = lambda: 99
print(left.read(), read(), right.original_read())
left.gcd = lambda *args: 17
print(left.use_gcd(), right.use_gcd())
from cplib.algorithm.left import read as updated
print(updated())
'''
            main, output = root/'main.py', root/'expanded.py'
            main.write_text(source)
            expected = subprocess.run([sys.executable, '-S', str(main)], env={**os.environ, 'PYTHONPATH': str(root)}, capture_output=True, text=True, check=True)
            expansion = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), str(output)], env={**os.environ, 'CPLIB_DIR': str(package)}, capture_output=True, text=True)
            self.assertEqual(expansion.returncode, 0, expansion.stderr)
            actual = subprocess.run([sys.executable, '-S', str(output)], env={key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}, capture_output=True, text=True)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(actual.stdout, expected.stdout)

    def test_global_rebinding_without_module_imports_keeps_snapshots(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expander-global-writes-') as folder:
            root = Path(folder)
            package = root / 'cplib'
            for name in ('algorithm', 'datastructure', 'geometry', 'graph', 'mathematics', 'string', 'tools'):
                (package / name).mkdir(parents=True)
            (package / '__init__.py').write_text('')
            (package / 'algorithm/left.py').write_text('''
from math import gcd
class Item:
    value = 5
Alias = Item
def read():
    return gcd(6, 9), Item.value
def change():
    global gcd, Item
    gcd = lambda a, b: 17
    class Item:
        value = 11
''')
            (package / 'algorithm/right.py').write_text('''
from math import gcd
def read():
    return gcd(6, 9)
''')
            source = '''
from cplib.algorithm.left import Item, Alias, read, change
from cplib.algorithm.right import read as right
print(read(), right(), Item.value, Alias.value)
change()
from cplib.algorithm.left import Item as current
print(read(), right(), Item.value, Alias.value, current.value)
'''
            main, output = root / 'main.py', root / 'expanded.py'
            main.write_text(source)
            expected = subprocess.run([sys.executable, '-S', str(main)], env={**os.environ, 'PYTHONPATH': str(root)}, capture_output=True, text=True, check=True)
            expansion = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), str(output)], env={**os.environ, 'CPLIB_DIR': str(package)}, capture_output=True, text=True)
            self.assertEqual(expansion.returncode, 0, expansion.stderr)
            actual = subprocess.run([sys.executable, '-S', str(output)], env={key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}, capture_output=True, text=True)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(actual.stdout, expected.stdout)

    def test_shared_modules_and_live_attributes(self) -> None:
        _, stdout = self.run_expander(
            """
            import cplib.geometry.floating as first
            import cplib.geometry.floating as second
            import cplib.geometry.floating
            from cplib.geometry.floating import EPS, get_eps
            from types import ModuleType

            print(first is second is cplib.geometry.floating, isinstance(first, ModuleType))
            print(first.__name__, first.__package__)
            first.set_eps(0.125)
            print(first.EPS, second.EPS, EPS, get_eps())
            second.EPS = 0.25
            print(first.get_eps(), get_eps())
            second.get_eps = lambda: 7
            print(first.get_eps(), get_eps())
            first.note = 'added'
            print(second.note, 'note' in dir(second), 'EPS' in dir(second))
            del second.note
            print(hasattr(first, 'note'))
            del first.EPS
            print(hasattr(second, 'EPS'), 'EPS' in dir(second))
            try:
                get_eps()
            except NameError:
                print('deleted')
            second.EPS = 0.5
            print(get_eps(), first.EPS, EPS)
            """
        )
        self.assertEqual(stdout.splitlines(), ['True True', 'cplib.geometry.floating cplib.geometry', '0.125 0.125 1e-10 0.125', '0.25 0.25', '7 0.25', 'added True True', 'False', 'False False', 'deleted', '0.5 0.5 1e-10'])

    def test_nested_module_imports_bind_only_when_executed(self) -> None:
        _, stdout = self.run_expander(
            """
            def number():
                import cplib.mathematics.utility as m
                return m.sign(-3)

            def tolerance():
                import cplib.geometry.floating as m
                return m.get_eps()

            if False:
                import cplib.mathematics.utility as absent
            import cplib.mathematics.utility as unused
            print(number(), tolerance(), 'm' in globals(), 'absent' in globals(), 'unused' in globals())
            """
        )
        self.assertEqual(stdout.strip(), '-1 1e-10 False False True')

    def test_deep_definition_dependencies(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expander-deep-') as folder:
            root = Path(folder)
            package = root/'cplib'
            for name in ('algorithm', 'datastructure', 'geometry', 'graph', 'mathematics', 'string', 'tools'):
                (package/name).mkdir(parents=True)
            definitions = [f'def f{index}():\n    return f{index - 1}\n' for index in range(1499, 0, -1)]
            definitions.append('def f0():\n    return 0\n')
            (package/'algorithm/chain.py').write_text('\n'.join(definitions))
            main, output = root/'main.py', root/'expanded.py'
            main.write_text('from cplib.algorithm.chain import f1499\nprint(f1499().__name__)\n')
            expansion = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), str(output)], env={**os.environ, 'CPLIB_DIR': str(package)}, capture_output=True, text=True)
            self.assertEqual(expansion.returncode, 0, expansion.stderr)
            result = subprocess.run([sys.executable, '-S', str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'f1498\n')

    def test_formatter_failure_uses_valid_unformatted_source(self) -> None:
        import expand_cplib

        with tempfile.TemporaryDirectory(prefix='cplib-expand-no-format-') as folder:
            main, output = Path(folder)/'main.py', Path(folder)/'expanded.py'
            main.write_text('from cplib.geometry.rational import Point\nprint((Point(1, 2) + Point(3, 4)).x)\n')
            with patch.object(expand_cplib, 'format_code', return_value=False), patch.object(sys, 'argv', ['expand_cplib.py', str(main), str(output)]), redirect_stderr(StringIO()):
                expand_cplib.main()
            run = subprocess.run([sys.executable, '-S', str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout, '4\n')

    def test_unknown_import_preserves_output_and_stdout_mode(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expand-import-error-') as folder:
            main, output = Path(folder)/'main.py', Path(folder)/'expanded.py'
            main.write_text('from cplib.mathematics.utility import does_not_exist\n')
            output.write_text('previous\n')
            run = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), str(output)], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('does_not_exist', run.stderr)
            self.assertEqual(output.read_text(), 'previous\n')
            main.write_text('from cplib.mathematics.utility import sign\nprint(sign(-3))\n')
            expanded = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), '-'], capture_output=True, text=True, check=True)
            run = subprocess.run([sys.executable, '-S', '-c', expanded.stdout], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout, '-1\n')

    def test_in_place_expansion(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expand-in-place-') as folder:
            path = Path(folder) / 'main.py'
            path.write_text('from cplib.mathematics.utility import sign\nprint(sign(-3))\n')
            subprocess.run(['bash', str(EXPANDER_SCRIPT), str(path), str(path)], capture_output=True, text=True, check=True)
            result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, '-1\n')
            self.assertNotIn('from cplib', path.read_text())
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_temporary_paths_with_shell_metacharacters(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expand-paths-') as folder:
            root = Path(folder)
            temporary = root / "temp space ' $(touch unexpected)"
            temporary.mkdir()
            path = root / 'main.py'
            output = root / "new output directory" / "output ' with spaces.py"
            path.write_text('from cplib.mathematics.utility import sign\nprint(sign(3))\n')
            result = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(path), str(output)], cwd=root, env={**os.environ, 'TMPDIR': str(temporary)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            run = subprocess.run([sys.executable, str(output)], capture_output=True, text=True, check=True)
            self.assertEqual(run.stdout, '1\n')
            self.assertEqual(list(temporary.iterdir()), [])
            self.assertFalse((root/'unexpected').exists())

    def test_failed_expansion_preserves_existing_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expand-failure-') as folder:
            root = Path(folder)
            path = root/'main.py'
            output = root/'output.py'
            path.write_text('def invalid(:\n')
            output.write_text('previous output\n')
            result = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(path), str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(), 'previous output\n')
            self.assertEqual(set(root.iterdir()), {path, output})

    def run_expander(self, source: str, input_text: str | None = None) -> tuple[str, str]:
        with tempfile.TemporaryDirectory(prefix="cplib-expander-test-") as tmpdir:
            tmpdir_path = Path(tmpdir)
            main_file = tmpdir_path / "main.py"
            output_file = tmpdir_path / "main.expanded.py"
            main_file.write_text(textwrap.dedent(source), encoding="utf-8")

            subprocess.run(
                ["bash", str(EXPANDER_SCRIPT), str(main_file), str(output_file)],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=True,
            )

            expanded_code = output_file.read_text(encoding="utf-8")
            run_result = subprocess.run(
                [sys.executable, "-S", str(output_file)],
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                input=input_text,
                capture_output=True,
                text=True,

            )
            self.assertEqual(run_result.returncode, 0, run_result.stderr)
            return expanded_code, run_result.stdout

    def test_distinct_geometry_classes_and_main_shadowing(self) -> None:
        _, stdout = self.run_expander(
            """
            from cplib.geometry.integer import Point as IntPoint
            from cplib.geometry.rational import Point as RationalPoint
            from cplib.geometry.floating import Point as FloatPoint
            from fractions import Fraction as Rational
            from typing import get_type_hints

            class Point:
                pass

            gcd = 99
            for cls in (IntPoint, RationalPoint, FloatPoint):
                point = cls(2, 3) + cls(4, 5)
                print(type(point.x).__name__, point.x, point.y)
            print(get_type_hints(RationalPoint.__add__)['return'] is RationalPoint)
            print(get_type_hints(type(RationalPoint(1, 2).x)._bounded_nonnegative)['return'].__args__[0] is type(RationalPoint(1, 2).x))
            print(Rational(2, 4), gcd, type(Point()) is Point)
            """
        )
        self.assertEqual(stdout.splitlines(), ['int 6 8', 'Rational 6 8', 'float 6.0 8.0', 'True', 'True', '1/2 99 True'])

    def test_library_method_with_local_cplib_import(self) -> None:
        code, stdout = self.run_expander(
            """
            from cplib.sequence.rangestat import OfflineStaticRangeInversionsQuery

            solver = OfflineStaticRangeInversionsQuery([3, 1, 2, 0])
            print(solver.solve([(0, 4), (0, 2), (1, 3), (2, 2)]))
            """
        )
        self.assertEqual(stdout.strip(), '[5, 1, 0, 0]')
        self.assertNotIn('from cplib.', code)
        self.assertNotIn('_cplib_', code)
        self.assert_strict_types(code)

    def test_late_and_nested_imports_preserve_binding_locations(self) -> None:
        code, stdout = self.run_expander(
            """
            value = -9
            from cplib.mathematics.utility import sign as first
            print(first(value))
            first = 42
            from cplib.mathematics.utility import sign as first
            print(first(value))

            def solve():
                from cplib.mathematics.utility import sign
                return sign(9)

            if False:
                from cplib.mathematics.utility import sign as absent
            print(solve(), 'absent' in globals())
            value = 5; from cplib.mathematics.utility import sign as inline; print(inline(value))
            # Keep this comment and this Unicode text: 日本語
            """
        )
        self.assertEqual(stdout.splitlines(), ['-1', '-1', '1 False', '1'])
        self.assertNotIn('from cplib.', code)
        self.assertIn('# Keep this comment and this Unicode text: 日本語', code)

    def test_colliding_module_imports(self) -> None:
        _, stdout = self.run_expander(
            """
            import cplib.geometry.integer as integer
            import cplib.geometry.rational as rational

            a = integer.Point(1, 2) + integer.Point(3, 4)
            b = rational.Point(1, 2) + rational.Point(3, 4)
            print(type(a.x).__name__, type(b.x).__name__)
            """
        )
        self.assertEqual(stdout.strip(), 'int Rational')

    def test_local_scopes_are_not_renamed_with_module_globals(self) -> None:
        with tempfile.TemporaryDirectory(prefix='cplib-expander-scopes-') as folder:
            root = Path(folder)
            package = root/'cplib'
            for name in ('algorithm', 'datastructure', 'geometry', 'graph', 'mathematics', 'string', 'tools'):
                (package/name).mkdir(parents=True)
            (package/'__init__.py').write_text('')
            template = '''
from math import gcd as divisor
OFFSET = {offset}
class Thing:
    OFFSET: int = OFFSET
    def pair(self, value: 'Thing') -> 'Thing':
        return Thing()
    def score(self):
        return OFFSET

def compute(values):
    def local(OFFSET):
        return OFFSET + 1
    def closure():
        OFFSET = 11
        def inner():
            return OFFSET
        return inner()
    squares = [OFFSET * OFFSET for OFFSET in values]
    captured = [(lambda OFFSET: OFFSET + 2)(item) for item in values]
    return OFFSET, Thing.OFFSET, Thing().score(), local(5), closure(), squares, captured, divisor(6, 9)
'''
            for name, offset in (('left', 3), ('right', 7)):
                (package/'algorithm'/f'{name}.py').write_text(template.format(offset=offset))
            source = '''
from cplib.algorithm.left import compute as left, Thing as Left
from cplib.algorithm.right import compute as right, Thing as Right
from typing import get_type_hints
print(left([2, 3]))
print(right([4, 5]))
print(get_type_hints(Left.pair)['return'] is Left, get_type_hints(Right.pair)['return'] is Right)
'''
            main, output = root/'main.py', root/'expanded.py'
            main.write_text(source)
            expected = subprocess.run([sys.executable, '-S', str(main)], env={**os.environ, 'PYTHONPATH': str(root)}, capture_output=True, text=True, check=True)
            expansion = subprocess.run(['bash', str(EXPANDER_SCRIPT), str(main), str(output)], env={**os.environ, 'CPLIB_DIR': str(package)}, capture_output=True, text=True)
            self.assertEqual(expansion.returncode, 0, expansion.stderr)
            actual = subprocess.run([sys.executable, '-S', str(output)], env={key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}, capture_output=True, text=True)
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(actual.stdout, expected.stdout)

    def test_fastio_split_tokens_and_repeated_flush(self) -> None:
        _, stdout = self.run_expander(
            '''
            import os
            from cplib.tools.fastio import FastIO

            original_read = os.read
            os.read = lambda fd, size: original_read(fd, min(size, 3))
            FastIO.writeln(str(sum(FastIO.read_ints(FastIO.read_int()))))
            FastIO.writeln(str(FastIO.read_float()))
            FastIO.writeln(FastIO.read())
            FastIO.writeln(FastIO.read_line())
            FastIO.flush()
            FastIO.flush()
            try:
                FastIO.read()
            except EOFError:
                FastIO.write('done')
            FastIO.atexit_register()
            ''',
            input_text='3\n123 -456 789\n1.25e-3\nword remaining line',
        )
        self.assertEqual(stdout, '456\n0.00125\nword\n remaining line\ndone')

    def test_heuristic_union_alias_does_not_end_library_prefix(self) -> None:
        expanded_code, stdout = self.run_expander(
            '''
            from cplib.heuristic.random import SplitMix64
            from cplib.heuristic.simulated_annealing import AnnealingSchedule, SimulatedAnnealing
            from cplib.heuristic.beam_search import BeamSearch

            def solve():
                solver = SimulatedAnnealing[int](float, lambda x, r: x+1, AnnealingSchedule(1e300, 1e-300), rng=SplitMix64(0))
                print(solver.run(0, 5).best_state)
                print(BeamSearch[int](lambda x: (x+1, x+2), float, 2).search([0], 3).best_state)

            solve()
            '''
        )
        self.assertEqual(stdout.splitlines(), ['5', '6'])
        self.assertIn('AnnealingRng = ', expanded_code)
        self.assertEqual(expanded_code.count('def solve('), 1)
        self.assertNotIn('__cplib_expander_library_end__', expanded_code)

    def test_main_declarations_stay_in_original_body(self) -> None:
        expanded_code, stdout = self.run_expander(
            '''
            import cplib.heuristic.random as rng

            LocalNumber = int | float
            CONSTANT = 3

            class LocalState:
                value = CONSTANT

            def local_function():
                return rng.SplitMix64(0).randrange(1) + LocalState.value

            print(local_function())
            '''
        )
        self.assertEqual(stdout.strip(), '3')
        for declaration in ('LocalNumber = ', 'CONSTANT = ', 'class LocalState:', 'def local_function('):
            self.assertEqual(expanded_code.count(declaration), 1)

    def test_floating_geometry_constants_and_type_alias(self) -> None:
        expanded_code, stdout = self.run_expander(
            '''
            from cplib.geometry.floating import Line, Point, Segment, projection, intersect

            N = 3

            def solve():
                line = Line(Point(0, 0), Point(N, 0))
                projected = projection(line, Point(1, 2))
                zero = Segment(Point(1, 0), Point(1, 0))
                print(projected.x, projected.y, intersect(zero, Segment(line.start, line.end)))

            solve()
            '''
        )
        self.assertEqual(stdout.strip(), '1.0 0.0 True')
        self.assertIn('EPS = ', expanded_code)
        self.assertEqual(expanded_code.count('N = 3'), 1)
        self.assertEqual(expanded_code.count('def solve('), 1)

    def test_floating_geometry_tolerance_without_other_geometry(self) -> None:
        _, stdout = self.run_expander(
            '''
            from cplib.geometry.floating import get_eps, set_eps

            print(get_eps())
            set_eps(0.125)
            print(get_eps())
            '''
        )
        self.assertEqual(stdout.splitlines(), ['1e-10', '0.125'])

    def test_type_alias_runtime_branch_dependencies(self) -> None:
        _, stdout = self.run_expander(
            '''
            from cplib.geometry.floating import Line, Point, projection

            projected = projection(Line(Point(0, 0), Point(1, 0)), Point(2, 3))
            print(projected.x, projected.y)
            '''
        )
        self.assertEqual(stdout.strip(), '2.0 0.0')

    def test_stdlib_import_before_cplib_import(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from collections import deque
            from cplib.datastructure.dsu import DisjointSetUnion

            def main() -> None:
                q = deque([1, 2])
                uf = DisjointSetUnion(2)
                print(q.popleft(), uf.same(0, 1))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "1 False")
        self.assertEqual(expanded_code.count("from collections import deque\n"), 1)

    def test_reexported_function_import_aliases(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from cplib.mathematics import extended_gcd as Gcd
            from cplib.mathematics.arithmetic import extended_gcd as arithmetic_gcd
            from cplib.mathematics.modular import extended_gcd as modular_gcd
            from cplib.mathematics.modular import extended_gcd as ModularGcd

            print(arithmetic_gcd(6, 15), modular_gcd(3, 7))
            print(Gcd is arithmetic_gcd is modular_gcd is ModularGcd)
            """
        )

        self.assertEqual(stdout.splitlines(), ['(3, 3) (1, 5)', 'True'])
        self.assertEqual(expanded_code.count('def extended_gcd('), 1)
        stores = [target.id for node in ast.parse(expanded_code).body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)]
        for name in ('arithmetic_gcd', 'modular_gcd', 'Gcd', 'ModularGcd'):
            self.assertEqual(stores.count(name), 1)

    def test_stdlib_import_after_cplib_import(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from cplib.datastructure.dsu import DisjointSetUnion
            from collections import deque

            def main() -> None:
                q = deque([1, 2])
                uf = DisjointSetUnion(2)
                print(q.popleft(), uf.same(0, 1))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "1 False")
        self.assertEqual(expanded_code.count("from collections import deque\n"), 1)

    def test_late_stdlib_import_stays_in_main_body(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from cplib.datastructure.dsu import DisjointSetUnion

            value = 3
            from collections import deque

            def main() -> None:
                q = deque([value])
                uf = DisjointSetUnion(2)
                print(q.popleft(), uf.same(0, 1))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "3 False")
        self.assertEqual(expanded_code.count("from collections import deque\n"), 1)
        self.assertLess(expanded_code.index("value = 3"), expanded_code.index("from collections import deque"))

    def test_future_import_stays_at_top(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from __future__ import annotations
            from collections import deque
            from cplib.datastructure.dsu import DisjointSetUnion

            class Wrapper:
                def __init__(self, uf: DisjointSetUnion) -> None:
                    self.uf = uf

            def main() -> None:
                wrapper = Wrapper(DisjointSetUnion(2))
                q = deque([wrapper.uf.same(0, 1)])
                print(q.popleft())

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "False")
        self.assertEqual(expanded_code.splitlines()[0], "from __future__ import annotations")
        self.assertEqual(expanded_code.count("from __future__ import annotations\n"), 1)
        self.assertEqual(expanded_code.count("from collections import deque\n"), 1)

    def test_shebang_is_preserved_before_expanded_imports(self) -> None:
        expanded_code, stdout = self.run_expander(
            """#!/usr/bin/env python3

from cplib.mathematics.factorial import FactorialMod

def main() -> None:
    print(FactorialMod(3).comb(3, 1))

if __name__ == '__main__':
    main()
"""
        )

        self.assertEqual(stdout.strip(), "3")
        self.assertTrue(expanded_code.startswith("#!/usr/bin/env python3\n\n"))
        self.assertLess(
            expanded_code.index("#!/usr/bin/env python3"),
            expanded_code.index("from __future__ import annotations"),
        )

    def test_expanded_code_keeps_pep8_top_level_blank_lines(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from cplib.datastructure.fenwicktree import SortedMultisetBIT

            def main() -> None:
                ms = SortedMultisetBIT([1, 2, 3])
                ms.add(2)
                print(ms.median())

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "2")
        self.assertIn("from typing import Generic, Protocol, TypeVar\n\n", expanded_code)
        self.assertIn("bound='Comparable')\n\n\nclass Comparable(Protocol):", expanded_code)
        self.assertIn("\n\n\nclass FenwickTree:", expanded_code)
        self.assertRegex(expanded_code, r"\n\n\nclass (?:_cplib_\w+_)?SortedMultisetBIT")

    def test_multiple_cplib_imports_expand_together(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from collections import deque
            from cplib.datastructure.dsu import DisjointSetUnion
            from cplib.string.matching import z_algorithm

            def main() -> None:
                q = deque([1, 2, 3])
                uf = DisjointSetUnion(3)
                uf.merge(0, 1)
                print(z_algorithm('aaab')[1], uf.same(q[0] - 1, q[1] - 1))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "2 True")
        self.assertEqual(expanded_code.count("from collections import deque\n"), 1)
        self.assertEqual(sum(isinstance(node, ast.ClassDef) and node.name.endswith('DisjointSetUnion') for node in ast.parse(expanded_code).body), 1)
        self.assertEqual(sum(isinstance(node, ast.FunctionDef) and node.name.endswith('z_algorithm') for node in ast.parse(expanded_code).body), 1)

    def test_interleaved_multiple_imports_do_not_duplicate_stdlib(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from collections import deque
            from cplib.datastructure.dsu import DisjointSetUnion
            from math import gcd
            from cplib.string.palindrome import manacher

            def main() -> None:
                q = deque([6, 9])
                uf = DisjointSetUnion(2)
                print(gcd(q[0], q[1]), manacher('abba')[2], uf.same(0, 1))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "3 1 False")
        self.assertEqual(expanded_code.count("from collections import deque\n"), 1)
        self.assertEqual(expanded_code.count("from math import gcd\n"), 1)

    def test_stdlib_import_used_only_in_main_is_preserved(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            import sys
            from cplib.datastructure.dsu import DisjointSetUnion

            def main() -> None:
                uf = DisjointSetUnion(2)
                sys.stdout.write(f"{uf.same(0, 1)}\\n")

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "False")
        self.assertEqual(expanded_code.count("import sys\n"), 1)

    def test_module_import_with_alias(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            import cplib.string.matching as sm

            def main() -> None:
                print(sm.z_algorithm('aaab')[1], sm.knuth_morris_pratt('ababa', 'aba')[1])

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "2 2")
        self.assertEqual(sum(isinstance(node, ast.FunctionDef) and node.name.endswith('z_algorithm') for node in ast.parse(expanded_code).body), 1)
        self.assertIn("def knuth_morris_pratt(text: str, pattern: str) -> list[int]:", expanded_code)

    def test_module_import_without_alias(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            import cplib.string.matching

            def main() -> None:
                print(cplib.string.matching.z_algorithm('aaab')[1])

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "2")
        self.assertEqual(sum(isinstance(node, ast.FunctionDef) and node.name.endswith('z_algorithm') for node in ast.parse(expanded_code).body), 1)

    def test_module_import_mixed_with_from_import(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            import cplib.datastructure.dsu as dsu
            from cplib.string.matching import z_algorithm

            def main() -> None:
                uf = dsu.DisjointSetUnion(2)
                print(z_algorithm('aaab')[1], uf.same(0, 1))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "2 False")
        self.assertEqual(sum(isinstance(node, ast.ClassDef) and node.name.endswith('DisjointSetUnion') for node in ast.parse(expanded_code).body), 1)
        self.assertEqual(sum(isinstance(node, ast.FunctionDef) and node.name.endswith('z_algorithm') for node in ast.parse(expanded_code).body), 1)

    def test_main_body_is_not_duplicated_after_merge(self) -> None:
        expanded_code, stdout = self.run_expander(
            """
            from cplib.datastructure.dsu import DisjointSetUnion
            from cplib.string.matching import z_algorithm

            def main() -> None:
                uf = DisjointSetUnion(3)
                print(z_algorithm('aaab')[1], uf.same(0, 0))

            if __name__ == '__main__':
                main()
            """
        )

        self.assertEqual(stdout.strip(), "2 True")
        self.assertEqual(expanded_code.count("def main() -> None:\n"), 1)
        self.assertEqual(expanded_code.count("if __name__ == "), 1)


if __name__ == "__main__":
    unittest.main()
