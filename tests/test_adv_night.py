"""Replay the actual JS rules against C, including catch timing and native jar geometry."""
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from host_tools import CC,SHARED_EXPORT,unload_library
ROOT=Path(__file__).resolve().parents[1];BOARD=ROOT/'firmware/main'
FIELDS=['rng','tick','score','res','over','lane','x','from_x','move','move_dir','next','drain_acc','cast','cooldown','good','bad','feedback','message','cue','misses','caught_x','caught_y','spawn_blocked']
class Bug(ctypes.Structure):_fields_=[(name,ctypes.c_int32) for name in ('type','x','base_y','dir','phase','age')]
class Night(ctypes.Structure):_fields_=[(name,ctypes.c_uint32 if i<3 else ctypes.c_int32) for i,name in enumerate(FIELDS)]+[('bugs',Bug*8)]
class Input(ctypes.Structure):_fields_=[(name,ctypes.c_uint8) for name in ('ok_down','ok_up','up_down','down_down','down_up','ok_held','down_held')]
def build(folder,mutation=None):
    folder=Path(folder)
    for name in ('adv_night.c','adv_night.h'):
        source=(BOARD/name).read_text('utf-8')
        if mutation and mutation[0]==name:
            assert mutation[1] in source;source=source.replace(mutation[1],mutation[2],1)
        (folder/name).write_text(source,'utf-8')
    target=folder/'night.dll'
    subprocess.run([CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror','-I',str(folder),'-I',str(BOARD),str(folder/'adv_night.c'),'-o',str(target)],check=True)
    lib=ctypes.CDLL(str(target));lib.adv_night_start.argtypes=[ctypes.POINTER(Night),ctypes.c_uint32]
    lib.adv_night_step.argtypes=[ctypes.POINTER(Night),ctypes.POINTER(Input)];lib.adv_night_target.argtypes=[ctypes.POINTER(Night)];lib.adv_night_speed.argtypes=[ctypes.POINTER(Night)]
    return lib
def view(lib,g):return [getattr(g,k) for k in FIELDS]+[getattr(e,k) for e in g.bugs for k,_ in Bug._fields_]+[lib.adv_night_target(ctypes.byref(g)),lib.adv_night_speed(ctypes.byref(g))]
def replay(lib,trace):
    g=Night();lib.adv_night_start(ctypes.byref(g),trace['seed'])
    for i,(action,expected) in enumerate(zip(trace['actions'],trace['states'])):
        if action[0]=='reset':lib.adv_night_start(ctypes.byref(g),action[1])
        else:lib.adv_night_step(ctypes.byref(g),ctypes.byref(Input(*action)))
        actual=view(lib,g)
        if actual!=expected:return i,actual,expected
    return None

class NightModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.lib=build(cls.temp.name)
        cls.traces={p.stem:json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/night_golden').glob('*.json')}
    @classmethod
    def tearDownClass(cls):unload_library(cls.lib._handle);cls.temp.cleanup()
    def new(self):
        g=Night();self.lib.adv_night_start(ctypes.byref(g),1);g.next=10000;return g
    def step(self,g,**bits):self.lib.adv_night_step(ctypes.byref(g),ctypes.byref(Input(**bits)))
    def bug(self,g,kind=1,dx=0,dy=0):g.bugs[0]=Bug(kind,(g.x+10+dx)*60,227+dy,1,16,0)
    def test_all_goldens_and_derived_catch_hints_match(self):
        self.assertEqual(set(self.traces),{'idle','drive','fuzz'});self.assertEqual(ctypes.sizeof(Night),284)
        for name,trace in self.traces.items():
            with self.subTest(name=name):self.assertIsNone(replay(self.lib,trace))
    def test_idle_resource_is_exactly40seconds(self):
        g=self.new()
        for _ in range(2399):self.step(g)
        self.assertEqual((g.res,g.over),(1,0));self.step(g);self.assertEqual((g.res,g.over,g.tick),(0,1,2400))
    def test_moves_use_actual_position_and_respect_edges(self):
        g=self.new();self.step(g,up_down=1);self.assertEqual(g.lane,0);self.assertTrue(48<g.x<120)
        for _ in range(19):self.step(g)
        self.assertEqual((g.x,g.move),(48,0));self.step(g,up_down=1);self.assertEqual(g.x,48)
        for _ in range(2):
            self.step(g,down_down=1)
            for _ in range(19):self.step(g)
        self.assertEqual((g.x,g.lane),(192,2));self.step(g,down_down=1);self.assertEqual(g.lane,2)
    def test_capture_uses_press_position_before_the_bug_moves(self):
        g=self.new();self.bug(g,dx=26);self.assertEqual(self.lib.adv_night_target(ctypes.byref(g)),0)
        self.step(g,ok_down=1);self.assertEqual((g.score,g.caught_x,g.message),(1,156,2));self.assertEqual(g.bugs[0].type,0)
        g=self.new();self.step(g,up_down=1);self.bug(g);self.step(g,ok_down=1);self.assertEqual(g.score,1)
    def test_empty_cast_and_held_ok_do_not_auto_catch(self):
        g=self.new();self.bug(g,dx=27);self.step(g,ok_down=1);self.assertEqual((g.score,g.misses,g.message,g.res),(0,1,1,1000))
        g=self.new();self.bug(g)
        for _ in range(8):self.step(g,ok_held=1)
        self.assertEqual(g.score,0);self.step(g,ok_down=1);self.assertEqual(g.score,1)
    def test_moth_penalty_caps_resource_and_ends_the_round(self):
        g=self.new();g.res=300;self.bug(g,2);self.step(g,ok_down=1);self.assertEqual((g.res,g.score,g.message,g.over),(50,0,3,0))
        g=self.new();g.res=250;self.bug(g,2);self.step(g,ok_down=1);self.assertEqual((g.res,g.over,g.cue),(0,1,8))
    def test_fixed_capacity_never_overwrites_live_bugs(self):
        g=self.new();g.next=1
        for i in range(8):g.bugs[i]=Bug(1,(30+i*20)*60,227,1,16,0)
        self.step(g);self.assertEqual(g.spawn_blocked,1);self.assertTrue(all(e.type==1 for e in g.bugs))
    def test_gold_threshold_is_reachable_without_empty_casts(self):
        end=self.traces['drive']['states'][-1];self.assertGreaterEqual(end[2],60);self.assertEqual((end[3],end[4],end[19]),(0,1,0))
    def test_catch_hotspot_matches_the_authored_jar_peak(self):
        manifest=json.loads((ROOT/'game-art/adventure/art/night-manifest.json').read_text('utf-8'))
        clip=next(a for a in manifest['animations'] if a['skin']=='night_a' and a['name']=='catch')
        x,y=clip['runtime_jar_opening'][2];ax,ay=clip['runtime_anchor']
        self.assertEqual((round(x-ax),280+round(y-ay)),(10,227))
    def test_unsigned_score_and_clock_do_not_wrap_into_invalid_difficulty(self):
        g=self.new();g.score=0xffffffff;g.tick=0xffffffff;self.bug(g);self.step(g,ok_down=1)
        self.assertEqual((g.score,g.tick),(0xffffffff,0));self.assertEqual(self.lib.adv_night_speed(ctypes.byref(g)),110)
    def test_mutants_are_caught_by_recorded_rules(self):
        mutations=[('adv_night.c','g->drain_acc+=25','g->drain_acc+=24'),('adv_night.c','g->res+=60','g->res+=59'),('adv_night.c','g->res-=250','g->res-=200'),('adv_night.h','#define ADV_NIGHT_RX 26','#define ADV_NIGHT_RX 25')]
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as folder:
                lib=build(folder,mutation)
                try:self.assertTrue(any(replay(lib,t) is not None for t in self.traces.values()))
                finally:unload_library(lib._handle)

if __name__=='__main__':unittest.main()
