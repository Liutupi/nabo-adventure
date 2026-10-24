"""Replay the prototype's golden traces against the production shell model, step by step."""
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT/'firmware/main'
HOST = ROOT/'tests/adv_host'
GOLDEN = ROOT/'tests/adv_golden'
SOURCES = ['adv_model.c', 'adv_stations.c', 'adv_demo.c', 'collection_model.c']
REDRAW = 1

def build(folder, replace=None):
    folder = Path(folder)
    files = []
    for name in SOURCES:
        text = (BOARD/name).read_text('utf-8')
        if replace and replace[0] == name:
            assert replace[1] in text, replace
            text = text.replace(replace[1], replace[2], 1)
        (folder/name).write_text(text, 'utf-8')
        files.append(str(folder/name))
    library = folder/'adv_model.dll'
    subprocess.run([CC, '-std=gnu11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror', '-I', str(BOARD),
                    *files, str(HOST/'adv_snapshot.c'), '-o', str(library)], check=True)
    lib = ctypes.CDLL(str(library))
    lib.host_new.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32] + [ctypes.c_int] * 4
    lib.host_legacy.argtypes = [ctypes.c_uint32]
    lib.host_snapshot.argtypes = [ctypes.c_char_p, ctypes.c_int]
    return lib

def replay(lib, trace):
    """Returns None when every state matches, else a description of the first mismatch."""
    best = (ctypes.c_uint32 * 9)(*trace['best'])
    lib.host_new(trace['seed'], best, trace['seen'], *trace['settings'])
    buf = ctypes.create_string_buffer(2048)
    for i, (action, want) in enumerate(zip(trace['actions'], trace['states'])):
        kind = action[0]
        if kind == 'e': fx = lib.host_event(action[1], action[2])
        elif kind == 's': fx = lib.host_steps(action[1])
        elif kind == 'l': fx = lib.host_legacy(action[1])
        else: lib.host_test(action[1]); fx = 0
        lib.host_snapshot(buf, len(buf))
        got = {'view': json.loads(buf.value), 'fx': fx & ~REDRAW, 'cue': lib.host_cue()}
        if got != want:
            return f'action {i} {action}: want {want} got {got}'
    return None

class GoldenTraces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.lib = build(cls.tmp.name)
        cls.traces = {p.stem: json.loads(p.read_text('utf-8')) for p in sorted(GOLDEN.glob('*.json'))}

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def test_traces_exist(self):
        self.assertGreaterEqual(len(self.traces), 4)
        pages = {s['view']['page'] for t in self.traces.values() for s in t['states']}
        self.assertEqual(pages, set(range(8)), 'goldens must visit every page')
        phases = {s['view']['session'][1] for t in self.traces.values() for s in t['states'] if s['view']['session']}
        self.assertEqual(phases, set(range(6)), 'goldens must visit every session phase')

    def test_every_trace_matches_the_prototype(self):
        for name, trace in self.traces.items():
            with self.subTest(trace=name):
                self.assertIsNone(replay(self.lib, trace))

    def test_test_mode_never_saves(self):
        for trace in self.traces.values():
            test = False
            for action, state in zip(trace['actions'], trace['states']):
                if action[0] == 't': test = bool(action[1])
                if test: self.assertFalse(state['fx'] & 8)

    def test_stamps_follow_bests(self):
        # A finished journey shows each stamp once and never takes one back.
        trace = self.traces['journey']
        seen = [s['view']['seen'] for s in trace['states']]
        for a, b in zip(seen, seen[1:]):
            self.assertEqual(a & b, a)
        self.assertEqual(seen[-1] & 0b111, 0b001, 'jump 12: bronze only')
        self.assertEqual(seen[-1] >> 3 & 0b111, 0b011, 'dive 350 m: bronze and silver')

class Mutations(unittest.TestCase):
    """Deliberately broken rules must fail the goldens (the traces are strong enough)."""
    MUTANTS = [
        ('adv_model.c', 'if (--m->t == 0) { m->phase = ADV_PLAY;', 'if (--m->t == 1) { m->phase = ADV_PLAY;'),
        ('adv_demo.c', 'g->res -= 250;', 'g->res -= 200;'),
        ('adv_demo.c', 'g->zh = g->zh - 10 < 60 ? 60 : g->zh - 10;', 'g->zh = g->zh - 9 < 60 ? 60 : g->zh - 9;'),
        ('adv_model.c', 'return m->best[station - 1] >= adv_threshold(station - 1, 0);',
         'return m->best[station - 1] > adv_threshold(station - 1, 0);'),
        ('adv_model.c', 'm->passport = (m->passport + (b == ADV_BTN_UP ? 7 : 1)) % 8;',
         'm->passport = (m->passport + (b == ADV_BTN_UP ? 1 : 7)) % 8;'),
        ('adv_model.c', 'if (!m->test) {', 'if (true) {'),
        ('adv_stations.c', 'const uint32_t adv_demo_thresholds[3] = {3, 6, 10};',
         'const uint32_t adv_demo_thresholds[3] = {3, 7, 10};'),
    ]

    def test_mutants_are_caught(self):
        traces = [json.loads(p.read_text('utf-8')) for p in sorted(GOLDEN.glob('*.json'))]
        for mutant in self.MUTANTS:
            with self.subTest(mutant=mutant[2]), tempfile.TemporaryDirectory() as tmp:
                lib = build(tmp, mutant)
                try:
                    self.assertTrue(any(replay(lib, t) for t in traces), 'mutant survived')
                finally:
                    unload_library(lib._handle)

if __name__ == '__main__':
    unittest.main()
