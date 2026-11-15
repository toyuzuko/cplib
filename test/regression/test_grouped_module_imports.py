import importlib
import unittest


class GroupedModuleImportsTest(unittest.TestCase):
    def test_previous_and_grouped_imports_are_identical(self) -> None:
        for old, new, names in [
            ('algorithm.aliens', 'algorithm.dp', ('aliens_minimize',)),
            ('algorithm.monotone_minima', 'algorithm.dp', ('monotone_minima',)),
            ('graph.project_selection', 'graph.optimization',
             ('MaximumWeightClosureResult', 'maximum_weight_closure')),
            ('graph.binary_submodular_minimizer', 'graph.optimization',
             ('BinarySubmodularMinimizer', 'BinarySubmodularResult')),
            ('mathematics.xor_basis', 'mathematics.bit', ('XorBasis',)),
            ('sequence.nonadjacent', 'sequence.subseq',
             ('maximum_non_adjacent_sums', 'minimum_non_adjacent_sums')),
        ]:
            package_name = old.partition('.')[0]
            package = importlib.import_module(f'cplib.{package_name}')
            legacy = importlib.import_module(f'cplib.{old}')
            canonical = importlib.import_module(f'cplib.{new}')
            for name in names:
                with self.subTest(old=old, name=name):
                    self.assertIs(getattr(legacy, name), getattr(canonical, name))
                    self.assertIs(getattr(package, name), getattr(canonical, name))
