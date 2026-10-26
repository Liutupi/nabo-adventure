"""SKI V2: replay the JS rules (prototype/adv_ski.js) against production C step by step (hashed goldens),
plus rule edges and mutations."""
import ctypes
import json
import tempfile
import unittest
from game_harness import ROOT, Input, build, replay_hashed
from host_tools import unload_library

HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'x', 'vx', 'y', 'v', 'air', 'air_max', 'kicked', 'spin_t', 'spins', 'crash',
        'invuln', 'aval', 'combo', 'best', 'gates', 'passed', 'misses', 'tricks', 'flow', 'crashes', 'stumbles', 'near_miss',
        'next_gate', 'next_row', 'last_gate_x', 'section', 'section_t', 'on_ice', 'meters', 'bonus', 'presses', 'blocked', 'fx_head']
F = {n: i for i, n in enumerate(HEAD)}
OBJ0 = len(HEAD)
WORDS = OBJ0 + 28*4 + 6*5


class SkiModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.lib, cls.State = build(cls.temp.name, 'ski', WORDS)
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/ski_golden').glob('*.json')}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle); cls.temp.cleanup()

    def new(self, seed=1):
        g = self.State(); self.lib.adv_ski_start(ctypes.byref(g), seed)
        for i in range(OBJ0, OBJ0 + 28*4): g.w[i] = 0
        g.w[F['next_gate']] = g.w[F['next_row']] = 1 << 28
        return g

    def step(self, g, n=1, **bits):
        for _ in range(n): self.lib.adv_ski_step(ctypes.byref(g), ctypes.byref(Input(**bits)))

    def obj(self, g, i, kind, x, dy):
        g.w[OBJ0+i*4:OBJ0+i*4+4] = (kind, x, (g.w[F['y']] >> 8) + dy, 0)

    def test_all_goldens_match(self):
        self.assertEqual(set(self.traces), {'idle', 'spam', 'wiggle', 'casual', 'skilled', 'fuzz'})
        self.assertEqual(ctypes.sizeof(self.State), WORDS*4)
        for name, trace in self.traces.items():
            with self.subTest(name=name): self.assertIsNone(replay_hashed(self.lib, self.State, 'ski', trace))

    def test_carving_costs_speed(self):
        straight, carve = self.new(), self.new()
        self.step(straight, 120); self.step(carve, 120, up_held=1)
        self.assertGreater(straight.w[F['v']], carve.w[F['v']])
        self.assertEqual(carve.w[F['x']], 302 << 8)

    def test_gate_pass_and_miss(self):
        g = self.new(); self.obj(g, 0, 1, 165, 1); aval = g.w[F['aval']]
        self.step(g)
        self.assertEqual((g.w[F['passed']], g.w[F['combo']], g.w[F['bonus']], g.w[F['flow']]), (1, 1, 10, 85))
        for dx, ok in ((21, 1), (22, 0)):          # the gate half-width is inclusive
            e = self.new(); self.obj(e, 0, 1, 160 + dx, 1); self.step(e)
            self.assertEqual(e.w[F['passed']], ok, dx)
        g2 = self.new(); self.obj(g2, 0, 2, 220, 1); self.step(g2)
        self.assertEqual((g2.w[F['misses']], g2.w[F['combo']]), (1, 0))
        self.assertGreater(g2.w[F['aval']] - aval, g.w[F['aval']] - aval)

    def test_tree_crash_and_hop_over_pine(self):
        g = self.new(); self.obj(g, 0, 3, 160, 1); self.step(g)
        self.assertEqual((g.w[F['crashes']], g.w[F['crash']], g.w[F['v']]), (1, 36, 0))
        g = self.new(); self.obj(g, 0, 4, 160, 8); self.step(g, 1, down_down=1); self.step(g, 4)
        self.assertEqual(g.w[F['stumbles']], 0)

    def test_kicker_spin_lands_or_wipes(self):
        g = self.new(); self.obj(g, 0, 6, 160, 1); self.step(g)
        self.assertEqual((g.w[F['air']], g.w[F['kicked']]), (72, 1))
        self.step(g, 1, down_down=1); self.step(g, 21)
        self.assertEqual(g.w[F['tricks']], 1)
        self.step(g, 50)
        self.assertEqual(g.w[F['bonus']], 50)
        g = self.new(); self.obj(g, 0, 6, 160, 1); self.step(g); self.step(g, 60); self.step(g, 1, down_down=1); self.step(g, 12)
        self.assertEqual(g.w[F['crashes']], 1)

    def test_avalanche_ends_the_run(self):
        g = self.new()
        while not g.w[F['over']]: self.step(g, 1, ok_held=1); g.w[F['flow']] = 0
        self.assertEqual((g.w[F['res']], g.w[F['cue']]), (0, 8))

    def test_mutations_are_caught(self):
        for mutation in [('adv_ski.c', 'GATE_PUSH = 26', 'GATE_PUSH = 25'),
                         ('adv_ski.c', 'int target = V0 + g->flow - abs(g->vx) / 3;', 'int target = V0 + g->flow - abs(g->vx) / 4;'),
                         ('adv_ski.c', 'g->vx -= g->vx / 6;', 'g->vx -= g->vx / 5;'),
                         ('adv_ski.c', 'if (g->flow > 0 && (g->tick & 1)) g->flow--;', 'if (g->flow > 0) g->flow--;'),
                         ('adv_ski.c', 'int v = rnd(g, 100);\n        int x = ADV_SKI_LEFT + rnd(g, ADV_SKI_RIGHT - ADV_SKI_LEFT);', 'int x = ADV_SKI_LEFT + rnd(g, ADV_SKI_RIGHT - ADV_SKI_LEFT);\n        int v = rnd(g, 100);'),
                         ('adv_ski.c', 'AVAL_DIV = 12', 'AVAL_DIV = 13')]:
            with self.subTest(mutation=mutation[1]), tempfile.TemporaryDirectory() as folder:
                lib, State = build(folder, 'ski', WORDS, mutation=mutation)
                try: self.assertTrue(any(replay_hashed(lib, State, 'ski', t) for t in self.traces.values()), mutation)
                finally: unload_library(lib._handle)


if __name__ == '__main__':
    unittest.main()
