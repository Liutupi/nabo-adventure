"""Replay the JS SKI rules against production C step by step, plus rule edges and mutations."""
import ctypes
import json
import tempfile
import unittest
from game_harness import ROOT, Input, build, replay, view
from host_tools import unload_library

WORDS = 30 + 16*4
F = {n: i for i, n in enumerate(['rng', 'tick', 'score', 'res', 'over', 'cue', 'x', 'vx', 'pos', 'speed', 'air', 'fall', 'invuln',
     'drain_acc', 'left_hold', 'right_hold', 'short_taps', 'next_gate', 'next_hazard', 'last_gate_x', 'gates', 'cabin_wait',
     'message', 'feedback', 'misses', 'crashes', 'bumps', 'cocoa', 'blocked', 'sub'])}


class SkiModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.lib, cls.State = build(cls.temp.name, 'ski', WORDS, events=('up',))
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/ski_golden').glob('*.json')}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle); cls.temp.cleanup()

    def new(self, seed=1):
        g = self.State(); self.lib.adv_ski_start(ctypes.byref(g), seed); return g

    def step(self, g, n=1, **bits):
        for _ in range(n): self.lib.adv_ski_step(ctypes.byref(g), ctypes.byref(Input(**bits)))

    def obj(self, g, i, kind, x, y):
        base = 30 + i*4; g.w[base:base+4] = (kind, x, y, 0)

    def clear_objs(self, g):
        for i in range(30, WORDS): g.w[i] = 0
        g.w[F['next_gate']] = g.w[F['next_hazard']] = 1 << 30

    def test_all_goldens_match(self):
        self.assertEqual(set(self.traces), {'idle', 'wiggle', 'casual', 'skilled', 'expert', 'fuzz'})
        self.assertEqual(ctypes.sizeof(self.State), WORDS*4)
        for name, trace in self.traces.items():
            with self.subTest(name=name): self.assertIsNone(replay(self.lib, self.State, 'ski', trace))

    def test_steering_waits_for_a_real_hold(self):
        g = self.new(); self.clear_objs(g)
        self.step(g, 5, up_held=1)
        self.assertEqual(g.w[F['vx']], 0)
        self.step(g, 1, up_held=1)
        self.assertEqual(g.w[F['vx']], -5)
        self.step(g, 30, down_held=1)
        self.assertEqual(g.w[F['vx']], 40)

    def test_gate_pass_miss_and_jump(self):
        g = self.new(); self.clear_objs(g)
        self.obj(g, 0, 1, 120, 2)
        self.step(g, 2)
        self.assertEqual((g.w[F['score']], g.w[F['message']], g.w[F['speed']]), (1, 1, 42))
        self.obj(g, 1, 2, 160, g.w[F['pos']]+1)
        self.step(g, 1)
        self.assertEqual((g.w[F['misses']], g.w[F['message']]), (1, 2))
        self.assertLess(g.w[F['res']], 901)
        self.obj(g, 2, 5, 120, g.w[F['pos']]+20)
        self.step(g, 1, ok_down=1)
        self.step(g, 12)
        self.assertEqual(g.w[F['bumps']], 0)
        self.obj(g, 3, 5, 120, g.w[F['pos']]+1)
        g.w[F['air']] = 0
        self.step(g, 1)
        self.assertEqual((g.w[F['bumps']], g.w[F['fall']]), (1, 24))

    def test_tree_crash_stops_progress_then_grants_invulnerability(self):
        g = self.new(); self.clear_objs(g)
        self.obj(g, 0, 3, 125, 1)
        self.step(g, 1)
        pos = g.w[F['pos']]
        self.assertEqual((g.w[F['crashes']], g.w[F['fall']], g.w[F['message']]), (1, 48, 3))
        self.step(g, 47)
        self.assertEqual((g.w[F['pos']], g.w[F['fall']]), (pos, 1))
        self.step(g, 1)
        self.assertEqual((g.w[F['fall']], g.w[F['invuln']]), (0, 40))

    def test_cocoa_and_short_taps(self):
        g = self.new(); self.clear_objs(g); g.w[F['res']] = 500
        self.obj(g, 0, 6, 140, 1)
        self.step(g)
        self.assertEqual((g.w[F['cocoa']], g.w[F['res']]), (1, 800))
        for _ in range(2): self.lib.adv_ski_up_event(ctypes.byref(g), True); self.lib.adv_ski_up_event(ctypes.byref(g), False)
        self.assertEqual(g.w[F['short_taps']], 2)
        self.lib.adv_ski_up_event(ctypes.byref(g), True); self.step(g, 6, up_held=1); self.lib.adv_ski_up_event(ctypes.byref(g), False)
        self.assertEqual(g.w[F['short_taps']], 0)

    def test_hazards_never_block_a_gate_corridor(self):
        for seed in range(1, 40):
            g = self.new(seed)
            for _ in range(1500):
                self.step(g)
                objs = [g.w[30+i*4:34+i*4] for i in range(16)]
                for t, x, y, _ in objs:
                    if t in (3, 4, 5):
                        for t2, x2, y2, _ in objs:
                            if t2 in (1, 2) and abs(y2-y) < 56: self.assertGreaterEqual(abs(x-x2), 48, (seed, x, x2))
                g.w[F['res']] = 1000

    def test_expert_trace_reaches_gold(self):
        self.assertGreaterEqual(self.traces['expert']['states'][-1][2], 45)

    def test_mutations_are_caught(self):
        for mutation in [('adv_ski.c', 'dx <= ADV_SKI_GATE_HALF', 'dx < ADV_SKI_GATE_HALF'),
                         ('adv_ski.c', 'if (in->ok_down && !g->air && !g->fall)', 'if (in->ok_down && !g->fall)'),
                         ('adv_ski.c', 'g->vx -= g->vx / 6;', 'g->vx -= g->vx / 5;'),
                         ('adv_ski.c', 'gate->x < 120 ?', 'gate->x <= 120 ?'),
                         ('adv_ski.h', '#define ADV_SKI_HOLD 6', '#define ADV_SKI_HOLD 5')]:
            with self.subTest(mutation=mutation[1]), tempfile.TemporaryDirectory() as folder:
                lib, State = build(folder, 'ski', WORDS, events=('up',), mutation=mutation)
                try: self.assertTrue(any(replay(lib, State, 'ski', t) for t in self.traces.values()), mutation)
                finally: unload_library(lib._handle)


if __name__ == '__main__':
    unittest.main()
