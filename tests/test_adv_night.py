"""NIGHT V2: replay the JS rules (prototype/adv_night.js) against production C step by step,
plus rule edges and mutations. Goldens store an FNV-1a hash of the full state per step."""
import ctypes
import json
import tempfile
import unittest
from game_harness import ROOT, Input, build
from host_tools import unload_library

HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'light', 'x', 'screen', 'gait', 'stun', 'stun_kind', 'swing', 'swing_caught',
        'last_swing', 'burst', 'combo', 'caught', 'meter', 'bursts', 'event', 'event_t', 'next_group', 'next_root', 'next_owl', 'last_loss',
        'max_combo', 'whiffs', 'trips', 'owl_hits', 'owl_near', 'moth_hits', 'missed', 'golds', 'multi', 'swings', 'presses',
        'roots_passed', 'blocked', 'fx_head']
FLIES, MOTHS, ROOTS, OWLS, FXN = 40, 12, 6, 4, 6
LOSS = len(HEAD)
FLY0 = LOSS + 6
MOTH0 = FLY0 + FLIES*7
ROOT0 = MOTH0 + MOTHS*6
OWL0 = ROOT0 + ROOTS*3
FX0 = OWL0 + OWLS*3
WORDS = FX0 + FXN*5
F = {n: i for i, n in enumerate(HEAD)}


def fnv(words):
    h = 0x811c9dc5
    for w in words:
        u = w & 0xffffffff
        for k in (0, 8, 16, 24):
            h ^= (u >> k) & 255
            h = (h * 0x01000193) & 0xffffffff
    return h


def view(g):
    return [v & 0xffffffff if i < 3 else v for i, v in enumerate(g.w)]


def replay(lib, State, trace):
    g = State()
    lib.adv_night_start(ctypes.byref(g), trace['seed'])
    for i, action in enumerate(trace['actions']):
        if action[0] == 'reset': lib.adv_night_start(ctypes.byref(g), action[1])
        else: lib.adv_night_step(ctypes.byref(g), ctypes.byref(Input(*action)))
        actual = view(g)
        if fnv(actual) != trace['hashes'][i]:
            near = min((int(k) for k in trace['states'] if int(k) >= i), default=None)
            return i, near
        if str(i) in trace['states'] and actual != trace['states'][str(i)]: return i, 'checkpoint'
    return None


class NightModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.lib, cls.State = build(cls.temp.name, 'night', WORDS)
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/night_golden').glob('*.json')}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle); cls.temp.cleanup()

    def new(self, seed=1):
        g = self.State(); self.lib.adv_night_start(ctypes.byref(g), seed); return g

    def step(self, g, n=1, **bits):
        for _ in range(n): self.lib.adv_night_step(ctypes.byref(g), ctypes.byref(Input(**bits)))

    def quiet(self, g):
        g.w[F['next_group']] = g.w[F['next_root']] = 1 << 30

    def fly(self, g, slot, x, y, kind=1):
        g.w[FLY0+slot*7:FLY0+slot*7+7] = (kind, x << 8, y, 0, 0, 0, 0)

    def test_all_goldens_match(self):
        self.assertEqual(set(self.traces), {'idle', 'spam', 'mistakes', 'casual', 'skilled', 'fuzz'})
        self.assertEqual(ctypes.sizeof(self.State), WORDS*4)
        for name, trace in self.traces.items():
            with self.subTest(name=name): self.assertIsNone(replay(self.lib, self.State, trace))

    def test_light_runs_out_without_play_and_running_costs_more(self):
        walk, run = self.new(), self.new()
        self.quiet(walk); self.quiet(run)
        self.step(walk, 600); self.step(run, 600, up_held=1)
        self.assertGreater(walk.w[F['light']], run.w[F['light']])
        self.assertGreater(run.w[F['x']], walk.w[F['x']])
        while not walk.w[F['over']]: self.step(walk)
        self.assertEqual((walk.w[F['res']], walk.w[F['cue']], walk.w[F['light']]), (0, 8, 0))
        tick = walk.w[F['tick']]; self.step(walk, 5)
        self.assertEqual(walk.w[F['tick']], tick)

    def test_net_catches_inside_arc_only_during_active_frames(self):
        g = self.new(); self.quiet(g)
        x = g.w[F['x']] >> 8
        self.fly(g, 0, x + 20 + 2, 158)           # inside the arc
        self.fly(g, 1, x + 20 + 40, 158)          # outside
        self.step(g, 1, down_down=1)
        self.assertEqual(g.w[F['caught']], 0)     # frame 0 of the swing is wind-up
        self.step(g, 4)
        self.assertEqual((g.w[F['caught']], g.w[F['combo']], g.w[F['score']]), (1, 1, 1))
        self.assertEqual(g.w[FLY0+7], 1)
        self.step(g, 20)
        self.assertEqual(g.w[F['whiffs']], 0)

    def test_whiff_breaks_combo_and_costs_light(self):
        g = self.new(); self.quiet(g); g.w[F['combo']] = 9
        light = g.w[F['light']]
        self.step(g, 1, down_down=1); self.step(g, 17)
        self.assertEqual((g.w[F['whiffs']], g.w[F['combo']]), (1, 0))
        self.assertLess(g.w[F['light']], light - 16000)

    def test_multiplier_and_gold(self):
        g = self.new(); self.quiet(g); g.w[F['combo']] = 11
        x = g.w[F['x']] >> 8
        self.fly(g, 0, x + 21, 158, kind=2)
        self.step(g, 1, down_down=1); self.step(g, 4)
        self.assertEqual((g.w[F['score']], g.w[F['meter']]), (5*3, 5))

    def test_root_trips_only_at_a_run(self):
        for held, tripped in ((dict(up_held=1), 1), ({}, 0), (dict(ok_held=1), 0)):
            g = self.new(); self.quiet(g)
            x = g.w[F['x']] >> 8
            g.w[ROOT0:ROOT0+3] = (x + 20, 12, 1)
            self.step(g, 40, **held)
            self.assertEqual(g.w[F['trips']], tripped, held)
            self.assertEqual(g.w[F['roots_passed']], 1 - tripped, held)

    def test_burst_needs_full_meter_and_double_tap(self):
        g = self.new(); self.quiet(g)
        x = g.w[F['x']] >> 8
        for i in range(5): self.fly(g, i, x + 100 + i*20, 120)
        g.w[F['meter']] = 29
        self.step(g, 1, down_down=1); self.step(g, 2); self.step(g, 1, down_down=1)
        self.assertEqual(g.w[F['bursts']], 0)
        g = self.new(); self.quiet(g)
        for i in range(5): self.fly(g, i, x + 100 + i*20, 120)
        g.w[F['meter']] = 30
        self.step(g, 1, down_down=1); self.step(g, 17); self.step(g, 1, down_down=1)
        self.assertEqual(g.w[F['bursts']], 0)      # too slow: second tap starts a new swing
        self.step(g, 2); self.step(g, 1, down_down=1)
        self.assertEqual((g.w[F['bursts']], g.w[F['caught']], g.w[F['meter']]), (1, 5, 5))
        for gap, burst in ((16, 1), (17, 0)):      # the second tap may come exactly DOUBLE frames later
            g = self.new(); self.quiet(g); g.w[F['meter']] = 30
            self.step(g, 1, down_down=1); self.step(g, gap - 1); self.step(g, 1, down_down=1)
            self.assertEqual(g.w[F['bursts']], burst, gap)

    def test_owl_hits_where_the_ring_was_and_changing_pace_dodges(self):
        for held, hit in (({}, 1), (dict(up_held=1), 0)):
            g = self.new(); self.quiet(g)
            g.w[OWL0:OWL0+3] = (g.w[F['x']] + 294*96, 96, 1)
            self.step(g, 96, **held)
            self.assertEqual(g.w[F['owl_hits']], hit, held)

    def test_events_rotate(self):
        g = self.new(); self.quiet(g)
        seen = []
        for _ in range(900 + 1500*3):
            self.step(g); g.w[F['light']] = 1000000
            if g.w[F['event']] and (not seen or seen[-1] != g.w[F['event']]): seen.append(g.w[F['event']])
        self.assertEqual(seen, [1, 2, 3, 1])

    def test_skilled_trace_scores_well(self):
        last = self.traces['skilled']['states'][str(len(self.traces['skilled']['hashes'])-1)]
        self.assertGreater(last[F['score']], 1000)

    def test_mutations_are_caught(self):
        for mutation in [('adv_night.c', 'age >= ADV_NIGHT_SWING_ON && age <= ADV_NIGHT_SWING_OFF', 'age >= ADV_NIGHT_SWING_ON && age < ADV_NIGHT_SWING_OFF'),
                         ('adv_night.c', 'return 1 + imin(4, g->combo / 6);', 'return 1 + imin(4, g->combo / 5);'),
                         ('adv_night.c', 'return DECAY * (9000 +', 'return DECAY * (9100 +'),
                         ('adv_night.c', 'METER_STEP = 12', 'METER_STEP = 11'),
                         ('adv_night.c', 'int rr = 15 + rnd(g, 9);\n                int sign = rnd(g, 2) ? -1 : 1;', 'int sign = rnd(g, 2) ? -1 : 1;\n                int rr = 15 + rnd(g, 9);'),
                         ('adv_night.c', 'm->y += adv_night_isin(ai * 13 / 10)', 'm->y += adv_night_isin(ai * 4 / 3)'),
                         ('adv_night.h', '#define ADV_NIGHT_NET_R 31', '#define ADV_NIGHT_NET_R 30')]:
            with self.subTest(mutation=mutation[1]), tempfile.TemporaryDirectory() as folder:
                lib, State = build(folder, 'night', WORDS, mutation=mutation)
                try: self.assertTrue(any(replay(lib, State, t) for t in self.traces.values()), mutation)
                finally: unload_library(lib._handle)


if __name__ == '__main__':
    unittest.main()
