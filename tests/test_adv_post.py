"""Replay 30,000 frozen JS steps through the actual production POST model."""
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from host_tools import CC,SHARED_EXPORT,unload_library

ROOT=Path(__file__).resolve().parents[1];BOARD=ROOT/'firmware/main';HOST=ROOT/'tests/adv_host'
GOLDEN=ROOT/'tests/post_golden'
FIELDS='tick score res over lane choice y transition speed drain_acc hold whistle lap remaining refill next_fork next_coal next_animal hit miss delivered cue spawn_blocked distance rng practice lesson tap_target tap_reason miss_reason feedback presses taps'.split()
class Event(ctypes.Structure):_fields_=[(k,ctypes.c_int32) for k in 'type x lane color done horn'.split()]
class Game(ctypes.Structure):
    _fields_=[(k,ctypes.c_uint32 if k in ('tick','score','distance','rng','presses','taps') else ctypes.c_int32) for k in FIELDS]+[('mail',ctypes.c_int32*5),('events',Event*12)]

def build(folder,mutant=None):
    source=(BOARD/'adv_post.c').read_text('utf-8')
    if mutant:
        assert mutant[0] in source;source=source.replace(*mutant,1)
    p=Path(folder)/'adv_post.c';p.write_text(source,'utf-8');dll=Path(folder)/'post.dll'
    result=subprocess.run([CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror','-I',str(BOARD),'-I',str(HOST),str(p),str(HOST/'adv_post_host.c'),'-o',str(dll)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr)
    c=ctypes.CDLL(str(dll));c.host_post_new.argtypes=[ctypes.c_uint32];c.host_post_step.argtypes=[ctypes.c_uint]
    c.host_post_values.argtypes=[ctypes.POINTER(ctypes.c_int64)];c.host_post_state.restype=ctypes.POINTER(Game)
    return c

def replay(c,trace):
    (c.host_post_practice if trace.get('practice') else c.host_post_new)(trace['seed']);want=trace['initial'].copy();buf=(ctypes.c_int64*110)()
    c.host_post_values(buf)
    if list(buf)!=want:return 'initial'
    for at,(mask,delta) in enumerate(trace['rows']):
        for i in range(0,len(delta),2):want[delta[i]]=delta[i+1]
        c.host_post_step(mask);c.host_post_values(buf)
        if list(buf)!=want:return (at,[(i,a,b) for i,(a,b) in enumerate(zip(buf,want)) if a!=b])
    return None

class PostRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.c=build(cls.tmp.name)
        cls.traces=[json.loads(p.read_text('utf-8')) for p in sorted(GOLDEN.glob('*.json'))]
    @classmethod
    def tearDownClass(cls):unload_library(cls.c._handle);cls.tmp.cleanup()
    def new(self):
        self.c.host_post_new(1234);g=self.c.host_post_state().contents
        g.next_coal=g.next_fork=g.next_animal=10000
        return g
    def step(self,mask=0):self.c.host_post_step(mask)
    def station(self,g,lane=None,color=None,x=156):
        g.events[0]=Event(2,x*60,g.lane if lane is None else lane,g.mail[0] if color is None else color,0,0)
    def tap(self):self.step(1|32);self.step(2)

    def test_frozen_prototype_every_step_and_all_difficulty_stages(self):
        sha=hashlib.sha256((ROOT/'game-art/adventure/prototype/adv_post.js').read_bytes()).hexdigest()
        self.assertEqual(sum(len(t['rows']) for t in self.traces),33600)
        for t in self.traces:
            self.assertEqual(t['prototype_sha256'],sha)
            self.assertIsNone(replay(self.c,t))
        drive=next(t for t in self.traces if not t.get('practice') and t['final']['score'])
        self.assertGreaterEqual(drive['final']['score'],25);self.assertGreaterEqual(drive['final']['lap'],3)
        self.assertEqual(drive['final']['spawnBlocked'],0)

    def test_short_tap_delivery_wrong_lane_color_and_time(self):
        g=self.new();self.station(g);self.tap();self.assertEqual(g.score,1);self.assertEqual(g.remaining,2)
        for lane,color,x in ((0,None,156),(None,99,156),(None,None,210)):
            g=self.new();self.station(g,lane,color,x);self.tap()
            self.assertEqual(g.score,0);self.assertLessEqual(g.res,750)
        g=self.new();self.station(g,lane=0);self.tap();r=g.res
        for _ in range(35):self.step()
        self.assertGreater(g.res,r-20,'Wrong delivery must resolve that station once')

    def test_hold_threshold_release_never_unloads_and_scare_needs_continuity(self):
        g=self.new();self.station(g);self.step(33)
        for _ in range(23):self.step(32)
        self.assertEqual(g.whistle,1);self.step(2);self.assertEqual(g.score,0)
        g=self.new();g.events[0]=Event(4,250*60,1,0,0,0)
        self.step(33)
        for _ in range(61):self.step(32)
        self.assertEqual(g.events[0].done,2);self.assertEqual(g.hit,0)
        g=self.new();g.events[0]=Event(4,120*60,1,1,0,0)
        for _ in range(8):self.step()
        self.assertGreater(g.hit,0);self.assertLessEqual(g.res,750)

    def test_choice_changes_actual_lane_only_at_fork_and_smooths(self):
        g=self.new();self.step(4);self.assertEqual((g.choice,g.lane),(0,1))
        g.events[0]=Event(1,110*60,0,0,0,0);self.step()
        self.assertEqual(g.lane,0);self.assertGreater(g.y,184)
        for _ in range(80):self.step()
        self.assertEqual(g.y,184)

    def test_visible_nose_taps_use_press_position_and_report_misses(self):
        for duration in (5,9,15,21):
            g=self.new();g.speed=200;self.station(g);self.step(33)
            for _ in range(duration-1):self.step(32)
            self.step(2)
            self.assertEqual((g.score,g.taps,g.presses),(1,1,1))
            self.assertEqual(g.miss_reason,0)
        for lane,color,x,reason in ((0,None,156,2),(None,99,156,3),(None,None,220,1)):
            g=self.new();self.station(g,lane,color,x);self.tap()
            self.assertEqual(g.miss_reason,reason);self.assertGreater(g.feedback,0)
        g=self.new();g.events[0]=Event(2,120*60,1,g.mail[0],0,0);self.step()
        self.assertEqual(g.miss_reason,5)

    def test_practice_waits_without_drain_and_never_reports_a_real_score(self):
        self.c.host_post_practice(42);g=self.c.host_post_state().contents
        for _ in range(600):self.step(8)
        self.assertEqual((g.practice,g.lesson,g.res,g.distance),(1,0,1000,0))
        self.step(4)
        for _ in range(300):self.step()
        self.assertEqual((g.lesson,g.events[1].x,g.y),(2,156*60,184))
        self.step(33)
        for _ in range(14):self.step(32)
        self.step(2);self.assertEqual((g.lesson,g.score,g.res),(3,1,1000))
        self.assertEqual(self.c.host_post_score(),0)

    def test_coal_refill_and_speed_cap(self):
        g=self.new();g.res=900;g.events[0]=Event(3,110*60,1,0,0,0);self.step();self.assertEqual(g.res,1000)
        g=self.new();g.remaining=1;self.station(g);self.tap()
        self.assertEqual((g.remaining,g.refill),(0,1));self.assertTrue(any(e.type==5 for e in g.events))
        g.events[1]=Event(5,110*60,1,0,0,0);self.step()
        self.assertEqual(g.lap,1);self.assertEqual(g.speed,97);self.assertIn(g.remaining,range(3,6))
        g.speed=199;g.events[1]=Event(5,110*60,1,0,0,0);self.step();self.assertEqual(g.speed,200)

    def test_natural_drain_over_and_state_budget(self):
        g=self.new()
        for _ in range(60):self.step()
        self.assertEqual(g.res,980);g.res=1
        for _ in range(3):self.step()
        self.assertEqual((g.res,g.over),(0,1));score=g.score
        self.tap();self.assertEqual(g.score,score)
        self.assertEqual(self.c.host_post_size(),ctypes.sizeof(Game));self.assertLess(ctypes.sizeof(Game),1024)

    def test_rule_mutants_are_caught(self):
        for mutant in [('g->res-=250','g->res-=200'),('g->speed=90','g->speed=91'),
                       ('g->hold>=ADV_POST_HOLD','g->hold>ADV_POST_HOLD'),
                       ('g->mail[0]','g->mail[1]'),('e->horn>=36','e->horn>=35')]:
            with self.subTest(mutant=mutant),tempfile.TemporaryDirectory() as tmp:
                c=build(tmp,mutant)
                try:self.assertTrue(any(replay(c,t) for t in self.traces))
                finally:unload_library(c._handle)

if __name__=='__main__':unittest.main(verbosity=2)
