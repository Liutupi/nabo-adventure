"""Replay the JS SKY rules against production C step by step, plus rule edges and mutations."""
import ctypes
import json
import tempfile
import unittest
from game_harness import ROOT, Input, build, replay
from host_tools import unload_library

WORDS = 22 + 10*5
F = {n: i for i, n in enumerate(['rng', 'tick', 'score', 'res', 'over', 'cue', 'alt', 'vy', 'dist', 'speed', 'heating', 'invuln',
     'drain_acc', 'next_spawn', 'bonus', 'message', 'feedback', 'hits', 'grounds', 'stamps', 'warms', 'blocked'])}


class SkyModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.lib, cls.State = build(cls.temp.name, 'sky', WORDS)
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/sky_golden').glob('*.json')}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle); cls.temp.cleanup()

    def new(self):
        g = self.State(); self.lib.adv_sky_start(ctypes.byref(g), 1)
        g.w[F['next_spawn']] = 1 << 30
        return g

    def step(self, g, n=1, **bits):
        for _ in range(n): self.lib.adv_sky_step(ctypes.byref(g), ctypes.byref(Input(**bits)))

    def obj(self, g, i, kind, dx, dy):
        base = 22 + i*5; g.w[base:base+5] = (kind, (g.w[F['dist']] >> 4) + dx, (g.w[F['alt']] >> 4) + dy, 16, 0)

    def test_all_goldens_match(self):
        self.assertEqual(set(self.traces), {'idle', 'hold', 'pulse', 'casual', 'skilled', 'expert', 'fuzz'})
        for name, trace in self.traces.items():
            with self.subTest(name=name): self.assertIsNone(replay(self.lib, self.State, 'sky', trace))

    def test_heat_only_drains_while_held_and_climbs(self):
        g = self.new()
        self.step(g, 60)
        self.assertEqual(g.w[F['res']], 1000)
        self.assertLess(g.w[F['alt']], 300*16)
        alt = g.w[F['alt']]
        self.step(g, 120, ok_held=1)
        self.assertEqual(g.w[F['res']], 880)
        self.assertGreater(g.w[F['alt']], alt)

    def test_treetops_cost_and_bounce(self):
        g = self.new(); g.w[F['alt']] = 8
        self.step(g, 10)
        self.assertEqual((g.w[F['grounds']], g.w[F['message']], g.w[F['invuln']] > 0), (1, 5, True))
        self.assertEqual(g.w[F['res']], 750)

    def test_hits_stamps_and_warm_currents(self):
        g = self.new()
        self.obj(g, 0, 2, 2, 141)   # storm in the envelope
        self.step(g)
        self.assertEqual((g.w[F['hits']], g.w[F['message']], g.w[F['res']]), (1, 2, 750))
        self.obj(g, 1, 1, 2, 141)   # a bird during invulnerability does nothing
        self.step(g)
        self.assertEqual(g.w[F['hits']], 1)
        self.obj(g, 2, 3, 30, 0)
        self.step(g)
        self.assertEqual((g.w[F['stamps']], g.w[F['bonus']]), (1, 10))
        self.obj(g, 3, 4, 0, -10)
        self.step(g)
        self.assertEqual((g.w[F['warms']], g.w[F['res']]), (1, 950))
        g.w[22+5:22+10] = (0, 0, 0, 0, 0)   # drop the bird that was ignored while invulnerable
        self.obj(g, 4, 2, 80, 141)   # outside the envelope
        g.w[F['invuln']] = 0
        self.step(g)
        self.assertEqual(g.w[F['hits']], 1)

    def test_expert_reaches_gold_and_holding_never_bronze(self):
        self.assertGreaterEqual(self.traces['expert']['states'][-1][2], 1000)
        self.assertLess(self.traces['hold']['states'][-1][2], 200)
        self.assertLess(self.traces['idle']['states'][-1][2], 200)

    def test_mutations_are_caught(self):
        for mutation in [('adv_sky.c', 'g->heating ? ADV_SKY_LIFT : -ADV_SKY_SINK', 'g->heating ? ADV_SKY_LIFT : -ADV_SKY_LIFT'),
                         ('adv_sky.c', 'dy <= ADV_SKY_BASKET_HI + r) return true;', 'dy <= ADV_SKY_BASKET_HI + r + 6) return true;'),
                         ('adv_sky.c', 'g->dist / (16 * 400)', 'g->dist / (16 * 300)'),
                         ('adv_sky.c', 'if (o->type == SKY_BIRD) { o->x--; o->phase++; }', 'if (o->type == SKY_BIRD) o->x--;'),
                         ('adv_sky.h', '#define ADV_SKY_ENV_RX 44', '#define ADV_SKY_ENV_RX 42')]:
            with self.subTest(mutation=mutation[1]), tempfile.TemporaryDirectory() as folder:
                lib, State = build(folder, 'sky', WORDS, mutation=mutation)
                try: self.assertTrue(any(replay(lib, State, 'sky', t) for t in self.traces.values()), mutation)
                finally: unload_library(lib._handle)


if __name__ == '__main__':
    unittest.main()
