"""Replay the JS SPACE rules against production C step by step, plus rule edges and mutations."""
import ctypes
import json
import tempfile
import unittest
from game_harness import ROOT, Input, build, replay
from host_tools import unload_library

WORDS = 27 + 3*4
F = {n: i for i, n in enumerate(['rng', 'tick', 'score', 'res', 'over', 'cue', 'round', 'landings', 'crashes', 'cans', 'phase', 'timer',
     'x', 'y', 'vx', 'vy', 'pad', 'thrust', 'side', 'drain_acc', 'left_hold', 'right_hold', 'short_taps', 'down_taps', 'message',
     'feedback', 'last_bonus'])}


class SpaceModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.lib, cls.State = build(cls.temp.name, 'space', WORDS, events=('up', 'down'))
        cls.lib.adv_space_zone.argtypes = [ctypes.POINTER(cls.State)]
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/space_golden').glob('*.json')}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle); cls.temp.cleanup()

    def zone(self, g): return [self.lib.adv_space_zone(ctypes.byref(g))]

    def new(self):
        g = self.State(); self.lib.adv_space_start(ctypes.byref(g), 1)
        for i in range(27, WORDS): g.w[i] = 0
        return g

    def step(self, g, n=1, **bits):
        for _ in range(n): self.lib.adv_space_step(ctypes.byref(g), ctypes.byref(Input(**bits)))

    def test_all_goldens_match(self):
        self.assertEqual(set(self.traces), {'idle', 'hover', 'casual', 'skilled', 'sloppy', 'fuzz'})
        for name, trace in self.traces.items():
            with self.subTest(name=name): self.assertIsNone(replay(self.lib, self.State, 'space', trace, self.zone))

    def test_soft_landing_on_the_pad_scores(self):
        g = self.new(); g.w[F['x']] = g.w[F['pad']]*256; g.w[F['y']] = 269*256+200; g.w[F['vy']] = 100; g.w[F['vx']] = 0
        self.step(g)
        self.assertEqual((g.w[F['phase']], g.w[F['landings']], g.w[F['message']]), (1, 1, 1))
        self.assertEqual(g.w[F['score']], 100 + (300-105)*50//300 + 50)
        self.step(g, 150)
        self.assertEqual((g.w[F['phase']], g.w[F['round']]), (0, 1))

    def test_hard_and_missed_landings_cost(self):
        g = self.new(); g.w[F['x']] = g.w[F['pad']]*256; g.w[F['y']] = 269*256; g.w[F['vy']] = 400; g.w[F['vx']] = 0
        self.step(g)
        self.assertEqual((g.w[F['phase']], g.w[F['message']], g.w[F['res']]), (2, 2, 750))
        g = self.new(); g.w[F['x']] = (g.w[F['pad']]+60 if g.w[F['pad']] < 120 else g.w[F['pad']]-60)*256
        g.w[F['y']] = 269*256+200; g.w[F['vy']] = 100; g.w[F['vx']] = 0
        self.step(g)
        self.assertEqual((g.w[F['message']], g.w[F['score']]), (3, 0))
        g = self.new(); g.w[F['x']] = g.w[F['pad']]*256; g.w[F['y']] = 269*256+200; g.w[F['vy']] = 100; g.w[F['vx']] = 161
        self.step(g)
        self.assertEqual((g.w[F['message']], g.w[F['phase']]), (2, 2))   # still drifting sideways is a hard landing

    def test_side_thrusters_need_a_real_hold_and_cost_fuel(self):
        g = self.new()
        self.step(g, 5, down_held=1)
        self.assertEqual(g.w[F['side']], 0)
        self.step(g, 60, down_held=1)
        self.assertEqual(g.w[F['side']], 1)
        self.assertLess(g.w[F['res']], 1000)
        for _ in range(2): self.lib.adv_space_down_event(ctypes.byref(g), True); self.lib.adv_space_down_event(ctypes.byref(g), False)
        self.assertEqual(g.w[F['down_taps']], 2)

    def test_fuel_can_and_rock(self):
        g = self.new(); g.w[F['res']] = 500
        lx, ly = g.w[F['x']]//256, g.w[F['y']]//256
        g.w[27:31] = (1, lx*256, (ly-30)*256, 0)
        self.step(g)
        self.assertEqual((g.w[F['cans']], g.w[F['res']]), (1, 800))
        lx, ly = g.w[F['x']]//256, g.w[F['y']]//256
        g.w[31:35] = (2, lx*256, (ly-30)*256, 0)
        self.step(g)
        self.assertEqual((g.w[F['phase']], g.w[F['message']]), (2, 4))

    def test_skilled_reaches_gold_and_idle_scores_nothing(self):
        self.assertGreaterEqual(self.traces['skilled']['states'][-1][2], 900)
        self.assertEqual(self.traces['idle']['states'][-1][2], 0)

    def test_mutations_are_caught(self):
        for mutation in [('adv_space.c', 'max_i(14, 40 - g->round * 4)', 'max_i(14, 40 - g->round * 3)'),
                         ('adv_space.h', '#define ADV_SPACE_MAIN_DRAIN 90', '#define ADV_SPACE_MAIN_DRAIN 80'),
                         ('adv_space.c', 'oy <= ly + 4', 'oy <= ly'),
                         ('adv_space.h', '#define ADV_SPACE_GRAVITY 5', '#define ADV_SPACE_GRAVITY 6'),
                         ('adv_space.c', 'int from_left = (int)(adv_rand(&g->rng) & 1), y = range(g, 150, 230);',
                          'int y = range(g, 150, 230), from_left = (int)(adv_rand(&g->rng) & 1);')]:
            with self.subTest(mutation=mutation[1]), tempfile.TemporaryDirectory() as folder:
                lib, State = build(folder, 'space', WORDS, events=('up', 'down'), mutation=mutation)
                lib.adv_space_zone.argtypes = [ctypes.POINTER(State)]
                z = lambda g: [lib.adv_space_zone(ctypes.byref(g))]
                try: self.assertTrue(any(replay(lib, State, 'space', t, z) for t in self.traces.values()), mutation)
                finally: unload_library(lib._handle)


if __name__ == '__main__':
    unittest.main()
