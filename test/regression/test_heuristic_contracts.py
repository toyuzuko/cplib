from decimal import Decimal, localcontext
from itertools import product
from math import isclose, isfinite, nextafter
from random import Random
import sys
import unittest
from unittest.mock import patch

from cplib.heuristic.beam_search import BeamSearch
from cplib.heuristic.neighborhood import Neighborhood
from cplib.heuristic.random import SplitMix64, XorShift
from cplib.heuristic.simulated_annealing import AnnealingSchedule, SimulatedAnnealing
from cplib.heuristic.time_manager import TimeManager


class FixedRandom(Random):
    def random(self) -> float:
        return 0.1


class HeuristicContractsTest(unittest.TestCase):
    def test_random_words_and_ranges(self) -> None:
        for cls in (SplitMix64, XorShift):
            for seed in (0, 1, -1, 2**64-1, 2**100+37):
                for width in (0, 1, 63, 64, 65, 127, 128, 129, 1025, 100003):
                    source, actual = cls(seed), cls(seed)
                    words = [source.next_uint64() for _ in range((width+63)//64)]
                    expected = sum(word << (64*i) for i, word in enumerate(words)) % (1 << width)
                    self.assertEqual(actual.randbits(width), expected)
                    self.assertEqual(actual.next_uint64(), source.next_uint64())
                a, b = cls(seed), cls(seed % 2**64)
                self.assertEqual([a.next_uint64() for _ in range(100)], [b.next_uint64() for _ in range(100)])
            for start, stop, step in product(range(-4, 5), range(-4, 5), range(-4, 5)):
                actual = cls(0)
                if step == 0 or not range(start, stop, step):
                    with self.assertRaises(ValueError):
                        actual.randrange(start, stop, step)
                    self.assertEqual(actual.next_uint64(), cls(0).next_uint64())
                    continue
                options = list(range(start, stop, step))
                # Force a rejection and then each valid index independently.
                for i, expected in enumerate(options):
                    with patch.object(cls, 'randbits', side_effect=[len(options), i]):
                        self.assertEqual(actual.randrange(start, stop, step), expected)
            for start, stop, step in ((0, 2**64, 1), (-2**200, 2**200, 7), (2**200, -2**200, -13)):
                for _ in range(50):
                    self.assertIn(cls(_).randrange(start, stop, step), range(start, stop, step))
                with patch.object(cls, 'randbits', return_value=0):
                    self.assertEqual(cls(0).randrange(start, stop, step), start)
            for _ in range(50):
                self.assertTrue(-2**100 <= cls(_).randint(-2**100, 2**100) <= 2**100)
                self.assertTrue(0 <= cls(_).randrange(2**64) < 2**64)
            for bad in (-1, -100):
                with self.assertRaises(ValueError):
                    cls(0).randbits(bad)
            with self.assertRaises(ValueError):
                cls(0).randint(2, 1)
            with self.assertRaises(TypeError):
                cls(0).randrange(2.5)  # type: ignore[arg-type]

    def test_random_sequence_operations(self) -> None:
        for cls in (SplitMix64, XorShift):
            with patch.object(cls, 'next_uint64', return_value=0):
                self.assertEqual(cls(0).random(), 0.0)
            with patch.object(cls, 'next_uint64', return_value=2**64-1):
                self.assertEqual(cls(0).random(), 1.0-2**-53)
            for n in range(80):
                values = [object() for _ in range(n)]
                before = values[:]
                cls(n).shuffle(values)
                self.assertCountEqual(values, before)
                if n:
                    self.assertIn(cls(n).choice(values), before)
            with self.assertRaises(IndexError):
                cls(0).choice([])

    def test_temperature(self) -> None:
        rng = Random(0)
        cases = [(1e300, 1e-300), (1e-300, 1e300), (5e-324, sys.float_info.max), (sys.float_info.max, 5e-324), (10., .1), (1., 1.)]
        cases += [(nextafter(sys.float_info.max, 0.), sys.float_info.max), (sys.float_info.max, nextafter(sys.float_info.max, 0.))]
        cases += [(10**rng.uniform(-300, 300), 10**rng.uniform(-300, 300)) for _ in range(60)]
        with localcontext() as context:
            context.prec = 80
            for start, end in cases:
                schedule = AnnealingSchedule(start, end)
                self.assertEqual(schedule.temperature(-float('inf')), start)
                self.assertEqual(schedule.temperature(float('inf')), end)
                self.assertEqual(schedule.temperature(0.), start)
                self.assertEqual(schedule.temperature(1.), end)
                previous = start
                for progress in (.001, .1, .5, .9, .999):
                    p = Decimal(progress)
                    expected = float(((1-p)*Decimal(start).ln()+p*Decimal(end).ln()).exp())
                    actual = schedule.temperature(progress)
                    self.assertTrue(isfinite(actual) and actual > 0)
                    self.assertTrue(isclose(actual, expected, rel_tol=3e-13, abs_tol=5e-324), (start, end, progress, actual, expected))
                    self.assertTrue(min(start, end) <= actual <= max(start, end))
                    self.assertTrue(actual >= previous if end >= start else actual <= previous)
                    previous = actual
                with self.assertRaises(ValueError):
                    schedule.temperature(float('nan'))
        for value in (0., -1., float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                AnnealingSchedule(value, 1.)
            with self.assertRaises(ValueError):
                AnnealingSchedule(1., value)

    def test_annealing_acceptance(self) -> None:
        rng = Random(0)
        with localcontext() as context:
            context.prec = 80
            for maximize in (False, True):
                cases = [(1e308, -1e308, 1e308), (-1e308, 1e308, 1e308)]
                cases += [(rng.uniform(-20, 20), rng.uniform(-20, 20), 10**rng.uniform(-2, 2)) for _ in range(300)]
                for start, candidate, temperature in cases:
                    difference = Decimal(candidate)-Decimal(start) if maximize else Decimal(start)-Decimal(candidate)
                    accept = difference >= 0 or Decimal(.1).ln() < difference/Decimal(temperature)
                    solver = SimulatedAnnealing[float](lambda x: x, lambda x, r: candidate, AnnealingSchedule(temperature, temperature), maximize=maximize, rng=FixedRandom())
                    result = solver.run(start, 1)
                    self.assertEqual(result.current_state, candidate if accept else start)
                    self.assertEqual(result.accepted_moves, int(accept))
                    self.assertEqual(result.best_score, max(start, candidate) if maximize else min(start, candidate))
                    self.assertEqual(result.iterations, 1)
        # Extreme schedules must remain usable when a worsening move is tested.
        for start, end in ((1e300, 1e-300), (1e-300, 1e300)):
            solver = SimulatedAnnealing[float](lambda x: x, lambda x, r: x-1, AnnealingSchedule(start, end), rng=FixedRandom())
            result = solver.run(0., 10)
            self.assertEqual(result.best_score, 0.)
            self.assertTrue(-10 <= result.current_score <= 0)
        for value in (float('nan'), float('inf'), -float('inf')):
            solver = SimulatedAnnealing[float](lambda x: x, lambda x, r: value, AnnealingSchedule(1., 1.))
            with self.assertRaises(ValueError):
                solver.run(value, 1)
            with self.assertRaises(ValueError):
                solver.run(0., 1)
        with self.assertRaises(ValueError):
            solver.run(0., 0)

    def test_annealing_mutable_states(self) -> None:
        proposals = iter((5., -1000., 4., 10., 9.))
        def neighbor(state: list[float], _: object) -> list[float]:
            state[0] = next(proposals)
            return state
        initial = [0.]
        solver = SimulatedAnnealing[list[float]](lambda x: x[0], neighbor, AnnealingSchedule(1., 1.), rng=FixedRandom(), copy_state=list.copy)
        result = solver.run(initial, 5)
        self.assertEqual(initial, [0.])
        self.assertEqual(result.best_state, [10.])
        self.assertEqual(result.current_state, [9.])
        self.assertEqual(result.accepted_moves, 4)
        result.current_state[0] = 100.
        self.assertEqual(result.best_state, [10.])
        self.assertEqual(initial, [0.])

    def test_time_manager(self) -> None:
        now = [10.]
        timer = TimeManager(3., clock=lambda: now[0])
        for time in (10., 10.5, 12.999, 13., 20.):
            now[0] = time
            self.assertEqual(timer.elapsed(), time-10.)
            self.assertEqual(timer.remaining(), max(0., 13.-time))
            self.assertEqual(timer.is_timeout(), time >= 13.)
        timer = TimeManager(1., start_time=25., clock=lambda: now[0])
        self.assertEqual(timer.elapsed(), -5.)
        self.assertEqual(timer.remaining(), 6.)
        self.assertFalse(timer.is_timeout())
        self.assertTrue(TimeManager(0., clock=lambda: 0.).is_timeout())
        self.assertFalse(TimeManager(float('inf'), start_time=0., clock=lambda: 1e300).is_timeout())
        timer = TimeManager(float('inf'), start_time=-1e308, clock=lambda: 1e308)
        self.assertFalse(timer.is_timeout())
        self.assertEqual(timer.remaining(), float('inf'))
        for timeout in (-1., -float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                TimeManager(timeout)
        for start in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                TimeManager(1., start_time=start)
            with self.assertRaises(ValueError):
                TimeManager(1., clock=lambda: start)

    def test_beam_search(self) -> None:
        rng = Random(0)
        for _ in range(500):
            n = rng.randrange(1, 15)
            scores = [rng.randrange(-5, 6) for _ in range(n)]
            edges = [[rng.randrange(n) for _ in range(rng.randrange(5))] for _ in range(n)]
            initial = [rng.randrange(n) for _ in range(rng.randrange(1, 8))]
            goals = {v for v in range(n) if rng.randrange(5) == 0}
            maximize, dedup = bool(rng.randrange(2)), bool(rng.randrange(2))
            width, limit = rng.randrange(1, 8), rng.randrange(7)
            # Reference materializes each complete layer and sorts it. Stable
            # first-seen deduplication precedes goal checking and pruning.
            layer = initial[:]
            best = None
            total = 0
            depth_reached = 0
            for depth in range(limit+1):
                if not layer:
                    break
                if dedup:
                    layer = list(dict.fromkeys(layer))
                total += len(layer)
                key = lambda v: -scores[v] if maximize else scores[v]
                layer.sort(key=key)
                if best is None or key(layer[0]) < key(best):
                    best = layer[0]
                depth_reached = depth
                goal = next((v for v in layer if v in goals), None)
                if goal is not None:
                    best = goal
                    break
                layer = [v for u in layer[:width] for v in edges[u]]
            solver = BeamSearch[int](lambda v: iter(edges[v]), lambda v: float(scores[v]), width, maximize, (lambda v: v) if dedup else None)
            result = solver.search(iter(initial), limit, lambda v: v in goals)
            self.assertEqual((result.best_state, result.best_score, result.depth_reached, result.nodes_expanded), (best, scores[best], depth_reached, total))
        solver = BeamSearch[list[int]](lambda x: ([x[0]+1], [x[0]+2]), lambda x: 0., 2)
        self.assertEqual(solver.search([[0]], 3).best_state, [0])
        for values, depth in (([], 1), ([[0]], -1)):
            with self.assertRaises(ValueError):
                solver.search(values, depth)
        with self.assertRaises(ValueError):
            BeamSearch[int](lambda x: [], float, 0)
        with self.assertRaises(ValueError):
            BeamSearch[int](lambda x: [1], lambda x: float('nan') if x else 0., 1).search([0], 1)
        with self.assertRaises(ValueError):
            BeamSearch[int](lambda x: [], lambda x: float('nan'), 1).search([0], 0)

    def test_neighborhood(self) -> None:
        class Move:
            def __init__(self, index: int, value: int, previous: int):
                self.index, self.value, self.previous = index, value, previous
            def apply(self, state: list[int]) -> None:
                state[self.index] = self.value
            def revert(self, state: list[int]) -> None:
                state[self.index] = self.previous
            def score_delta(self) -> float:
                return float(self.value**2-self.previous**2)
        rng = Random(0)
        original = [rng.randrange(-10, 11) for _ in range(20)]
        neighborhood = Neighborhood(original[:], float(sum(x*x for x in original)))
        history: list[Move] = []
        for _ in range(500):
            i = rng.randrange(len(original))
            move = Move(i, rng.randrange(-10, 11), neighborhood.state[i])
            history.append(move)
            self.assertEqual(neighborhood.apply(move), sum(x*x for x in neighborhood.state))
        for move in reversed(history):
            self.assertEqual(neighborhood.revert(move), sum(x*x for x in neighborhood.state))
        self.assertEqual(neighborhood.state, original)


if __name__ == '__main__':
    unittest.main()
