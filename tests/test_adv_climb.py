"""Replay the JS CLIMB rules against production C step by step, plus rule edges and mutations."""
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT/'firmware/main'
FIELDS = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'row', 'side', 'act', 'act_t', 'act_len', 'from_row', 'from_side',
          'to_row', 'to_side', 'press', 'queue', 'fragile_t', 'drain_acc', 'gen_top', 'canteen_next', 'rock_next',
          'invuln', 'cheer', 'message', 'feedback', 'hits', 'misses', 'crumbles', 'canteens']
NORMAL, FRAGILE, ICE = 1, 2, 3
IDLE, SWITCH, JUMP, SLIDE = 0, 1, 2, 3


class Rock(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int32) for n in ('on', 'side', 'y')]


class Climb(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint32 if i < 3 else ctypes.c_int32) for i, n in enumerate(FIELDS)] + \
               [('grid', ctypes.c_uint8*32), ('rocks', Rock*4)]


class Input(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint8) for n in ('ok_down', 'ok_up', 'up_down', 'down_down', 'down_up', 'ok_held', 'down_held', 'up_held')]


def build(folder, mutation=None):
    folder = Path(folder)
    for name in ('adv_climb.c', 'adv_climb.h'):
        source = (BOARD/name).read_text('utf-8')
        if mutation and mutation[0] == name:
            assert mutation[1] in source, mutation
            source = source.replace(mutation[1], mutation[2], 1)
        (folder/name).write_text(source, 'utf-8')
    target = folder/'climb.dll'
    subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror', '-I', str(folder),
                    '-I', str(BOARD), str(folder/'adv_climb.c'), '-o', str(target)], check=True)
    lib = ctypes.CDLL(str(target))
    lib.adv_climb_start.argtypes = [ctypes.POINTER(Climb), ctypes.c_uint32]
    lib.adv_climb_step.argtypes = [ctypes.POINTER(Climb), ctypes.POINTER(Input)]
    for fn in ('adv_climb_hand_y', 'adv_climb_body_side'):
        getattr(lib, fn).argtypes = [ctypes.POINTER(Climb)]
    lib.adv_climb_hold.argtypes = [ctypes.POINTER(Climb), ctypes.c_int, ctypes.c_int]
    lib.adv_climb_canteen.argtypes = [ctypes.POINTER(Climb), ctypes.c_int, ctypes.c_int]
    lib.adv_climb_canteen.restype = ctypes.c_bool
    return lib


def view(lib, g):
    return [getattr(g, k) for k in FIELDS] + list(g.grid) + [getattr(r, k) for r in g.rocks for k in ('on', 'side', 'y')] + \
           [lib.adv_climb_hand_y(ctypes.byref(g)), lib.adv_climb_body_side(ctypes.byref(g))]


def replay(lib, trace):
    g = Climb()
    lib.adv_climb_start(ctypes.byref(g), trace['seed'])
    for i, (action, expected) in enumerate(zip(trace['actions'], trace['states'])):
        if action[0] == 'reset': lib.adv_climb_start(ctypes.byref(g), action[1])
        else: lib.adv_climb_step(ctypes.byref(g), ctypes.byref(Input(*action)))
        actual = view(lib, g)
        if actual != expected:
            diff = [(FIELDS[j] if j < len(FIELDS) else j, a, e) for j, (a, e) in enumerate(zip(actual, expected)) if a != e]
            return i, diff[:6]
    return None


class ClimbModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.lib = build(cls.temp.name)
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/climb_golden').glob('*.json')}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.temp.cleanup()

    def new(self, seed=1):
        g = Climb()
        self.lib.adv_climb_start(ctypes.byref(g), seed)
        return g

    def step(self, g, n=1, **bits):
        for _ in range(n): self.lib.adv_climb_step(ctypes.byref(g), ctypes.byref(Input(**bits)))

    def press(self, g, frames):
        """OK down, held for `frames` steps, released on the last one (the press counter reads frames-1)."""
        self.step(g, ok_down=1, ok_held=1)
        self.step(g, frames-2, ok_held=1)
        self.step(g, ok_up=1)

    def hold(self, g, row, side): return self.lib.adv_climb_hold(ctypes.byref(g), row, side)

    def test_all_goldens_match(self):
        self.assertEqual(set(self.traces), {'idle', 'skilled', 'casual', 'tapper', 'lazy', 'icy', 'fuzz'})
        self.assertEqual(ctypes.sizeof(Climb), 200)
        for name, trace in self.traces.items():
            with self.subTest(name=name): self.assertIsNone(replay(self.lib, trace))

    def test_idle_lasts_exactly_200_seconds_of_drain(self):
        g = self.new()
        self.step(g, 1999)
        self.assertEqual((g.res, g.over), (1, 0))
        self.step(g)
        self.assertEqual((g.res, g.over, g.cue, g.tick), (0, 1, 8, 2000))

    def test_starter_ladder_and_reachability_guarantee(self):
        for seed in range(1, 60):
            g = self.new(seed)
            for r in range(5): self.assertEqual((self.hold(g, r, 0), self.hold(g, r, 1)), (NORMAL, NORMAL))
            for _ in range(400):   # walk the generator far up and check every finished row
                g.row = g.gen_top - 12
                self.step(g)
                for r in range(max(0, g.gen_top-28), g.gen_top-2):
                    for s in (0, 1):
                        if not self.hold(g, r, s): continue
                        solid = lambda rr, ss: self.hold(g, rr, ss) in (NORMAL, ICE)
                        self.assertTrue(solid(r+1, 1-s) or solid(r+2, s) or solid(r+3, s), (seed, r, s))
                g.res = 1000

    def test_tap_switches_and_twelve_frames_is_a_jump(self):
        g = self.new()
        self.press(g, 12)   # press counter 11 on release: a tap
        self.assertEqual((g.act, g.to_row, g.to_side), (SWITCH, 1, 1))
        self.step(g, 24)
        self.assertEqual((g.act, g.row, g.side, g.score), (IDLE, 1, 1, 1))
        self.assertEqual(g.res, 999)   # +20 at the new row is capped at 1000 before later drain
        self.press(g, 13)   # counter 12: jump two rows on the same wall
        self.assertEqual((g.act, g.to_row, g.to_side), (JUMP, 3, 1))
        self.step(g, 30)
        self.press(g, 41)   # counter 40: jump three rows
        self.assertEqual((g.act, g.to_row), (JUMP, 6))

    def test_queued_intent_runs_when_the_move_lands(self):
        g = self.new()
        self.press(g, 3)
        self.press(g, 3)   # released mid-switch
        self.assertEqual((g.act, g.queue), (SWITCH, 1))
        self.step(g, 24)
        self.assertEqual((g.row, g.side, g.act, g.to_row, g.to_side), (1, 1, SWITCH, 2, 0))

    def test_missing_hold_slides_and_costs(self):
        g = self.new()
        g.row = 3; g.side = 0
        g.grid[4] = NORMAL   # row 4: left only, so a tap to the right misses
        self.press(g, 3)
        self.assertEqual((g.act, g.to_row, g.to_side, g.misses, g.message), (SLIDE, 2, 0, 1, 1))
        self.assertLess(g.res, 1000-99)
        self.step(g, 30)
        self.assertEqual((g.act, g.row, g.score), (IDLE, 2, 0))

    def test_new_rows_restore_but_reclimbing_does_not(self):
        g = self.new()
        g.res = 500; g.score = 3; g.row = 1; g.side = 1
        self.press(g, 3); self.step(g, 24)   # to row 2: below the record, no gain
        self.assertEqual((g.row, g.score, g.res), (2, 3, 500 - g.tick//2))
        self.press(g, 3); self.step(g, 24); self.press(g, 3); self.step(g, 24)   # row 4: one new row
        self.assertEqual((g.row, g.score, g.res), (4, 4, 500 - g.tick//2 + 20))

    def test_fragile_crumbles_after_a_second(self):
        g = self.new()
        g.grid[1] = FRAGILE | (NORMAL << 2)
        g.row = 0; g.side = 1
        self.press(g, 3); self.step(g, 24)
        self.assertEqual((g.row, g.side, g.fragile_t), (1, 0, 59))   # the landing step already counts
        self.step(g, 58)
        self.assertEqual((g.act, self.hold(g, 1, 0)), (IDLE, FRAGILE))
        self.step(g)
        self.assertEqual((g.act, self.hold(g, 1, 0), g.crumbles, g.to_row), (SLIDE, 0, 1, 0))

    def test_ice_doubles_drain(self):
        g = self.new()
        g.grid[0] = ICE | (NORMAL << 2)
        self.step(g, 60)
        self.assertEqual(g.res, 940)

    def test_rock_hits_only_its_column_then_grants_invulnerability(self):
        g = self.new()
        g.score = 8; g.rock_next = 100000
        g.rocks[0] = Rock(1, 1, 30)
        self.step(g, 20)
        self.assertEqual((g.hits, g.rocks[0].on), (0, 1))
        g.rocks[0] = Rock(1, 0, 24)
        self.step(g)
        self.assertEqual((g.hits, g.res, g.act, g.invuln, g.message), (1, 1000-250-g.tick//2, SLIDE, 60, 2))
        g.rocks[1] = Rock(1, 0, 24)
        self.step(g)
        self.assertEqual(g.hits, 1)

    def test_canteen_restores_and_is_consumed(self):
        g = self.new()
        g.res = 300; g.grid[1] |= 1 << 5
        self.assertTrue(self.lib.adv_climb_canteen(ctypes.byref(g), 1, 1))
        self.press(g, 3); self.step(g, 24)
        self.assertEqual((g.canteens, g.message), (1, 4))
        self.assertFalse(self.lib.adv_climb_canteen(ctypes.byref(g), 1, 1))
        self.assertGreater(g.res, 300+250)

    def test_skilled_trace_climbs_far_and_tapper_earns_nothing(self):
        self.assertGreaterEqual(self.traces['skilled']['states'][-1][2], 100)
        self.assertLess(self.traces['tapper']['states'][-1][2], 50)

    def test_mutations_are_caught(self):
        mutations = [
            ('adv_climb.c', 'g->press < ADV_CLIMB_TAP ? 1', 'g->press <= ADV_CLIMB_TAP ? 1'),
            ('adv_climb.c', '&& !solid(g, k, s))', '&& !adv_climb_hold(g, k, s))'),
            ('adv_climb.c', 'icy ? ADV_CLIMB_ICE_DRAIN : ADV_CLIMB_DRAIN', 'icy ? ADV_CLIMB_DRAIN : ADV_CLIMB_DRAIN'),
            ('adv_climb.c', 'r->side == side &&', '(r->side == side || r->on) &&'),
            ('adv_climb.c', 'if ((uint32_t)g->row > g->score) {', 'if ((uint32_t)g->row >= g->score) {'),
            ('adv_climb.c', 'int side = (int)(adv_rand(&g->rng) & 1);', 'int side = 0;'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation[1]), tempfile.TemporaryDirectory() as folder:
                lib = build(folder, mutation)
                try:
                    self.assertTrue(any(replay(lib, t) for t in self.traces.values()), mutation)
                finally:
                    unload_library(lib._handle)


if __name__ == '__main__':
    unittest.main()
