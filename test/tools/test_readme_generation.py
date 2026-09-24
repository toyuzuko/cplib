import ast
from pathlib import Path
import unittest

from scripts.generate_readmes import extract_apis, extract_complexity, public_modules, render_package


ROOT = Path(__file__).resolve().parents[2]


class ReadmeGenerationTest(unittest.TestCase):
    def test_complexity_keeps_wrapped_conditions_and_stops_at_next_section(self) -> None:
        doc = '''Summary.

Time Complexity:
    O(n log n) for a fixed threshold. In general,
    O(n log n + n * threshold).

    Integer operations are counted as constant time.

Space Complexity:
    O(n).
'''
        self.assertEqual(extract_complexity(doc, 'Time'), 'O(n log n) for a fixed threshold. In general, O(n log n + n * threshold). Integer operations are counted as constant time.')
        self.assertEqual(extract_complexity(doc, 'Space'), 'O(n).')
        self.assertEqual(extract_complexity('Time Complexity:\n\nNotes:\n    Not a bound.', 'Time'), '')

    def test_inline_and_bulleted_bounds(self) -> None:
        self.assertEqual(extract_complexity('Time Complexity: O(n),\n    including the output.\nReturns:\n    Values.', 'Time'), 'O(n), including the output.')
        self.assertEqual(extract_complexity('Time Complexities:\n    - Build: O(n)\n    - Query: O(log n)\n      in the worst case.', 'Time'), 'Build: O(n); Query: O(log n) in the worst case.')

    def test_generated_rows_keep_real_docstring_qualifications(self) -> None:
        apis = extract_apis('algorithm', ROOT / 'cplib/algorithm/dp.py')
        fibonacci = next(api for api in apis if api.name == 'fibonacci_number')
        self.assertIn('Integer arithmetic is not', fibonacci.complexity)
        source = ast.parse((ROOT / 'cplib/algorithm/dp.py').read_text())
        node = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == 'fibonacci_number')
        doc = ast.get_docstring(node)
        assert doc is not None
        bound = doc.split('Time Complexity:', 1)[1].split('Space Complexity:', 1)[0]
        self.assertEqual(fibonacci.complexity, ' '.join(bound.split()))
        rendered = render_package('algorithm', {'dp.py': apis})
        self.assertIn(fibonacci.complexity, rendered)

    def test_fastio_is_documented_without_importing_it(self) -> None:
        path = ROOT / 'cplib/tools/fastio.py'
        self.assertIn(path, public_modules(path.parent))
        apis = extract_apis('tools', path)
        self.assertIn('FastIO', [api.name for api in apis])


if __name__ == '__main__':
    unittest.main()
