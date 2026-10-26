"""SPACE V2: approved integer JS goldens, physical rule edges and mutations."""
import ctypes,json,tempfile,unittest
from game_harness import ROOT,Input,build,replay_hashed
from host_tools import unload_library
HEAD=['rng','tick','score','res','over','cue','mode','modeT','win','alt','v','vTarget','x','vx','fuel','hull','heat',
 'boostT','lastBoost','invuln','ign','ignScore','sep','sepT','sepQ','tli','tliT','tliHit','tliQ','zoneSeen','combo','best',
 'stars','near','hits','perfects','rings','cans','bonus','nextObj','push','lx','ly','lvx','lvy','pad','landings','presses','blocked','fxHead']
F={n:i for i,n in enumerate(HEAD)};OBJ0=len(HEAD);FX0=OBJ0+24*6;WORDS=FX0+6*5
class SpaceModel(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.lib,cls.State=build(cls.temp.name,'space',WORDS)
  cls.traces={p.stem:json.loads(p.read_text('utf-8')) for p in (ROOT/'tests/space_golden').glob('*.json')}
 @classmethod
 def tearDownClass(cls):unload_library(cls.lib._handle);cls.temp.cleanup()
 def new(self,mode=0):
  g=self.State();self.lib.adv_space_start(ctypes.byref(g),1);g.w[F['mode']]=mode;g.w[F['nextObj']]=1<<28
  return g
 def step(self,g,n=1,**bits):
  for _ in range(n):self.lib.adv_space_step(ctypes.byref(g),ctypes.byref(Input(**bits)))
 def obj(self,g,kind,x,dy=20):g.w[OBJ0:OBJ0+6]=(kind,x*256,(g.w[F['alt']]>>8)+dy,0,0,0)
 def test_all_goldens_match(self):
  self.assertEqual(set(self.traces),{'idle','hover','casual','skilled','sloppy','fuzz'})
  self.assertEqual(ctypes.sizeof(self.State),WORDS*4)
  for name,t in self.traces.items():
   with self.subTest(name=name):self.assertIsNone(replay_hashed(self.lib,self.State,'space',t))
 def test_ignition_precision_and_automatic_launch(self):
  g=self.new();g.w[F['modeT']]=23;self.step(g,down_down=1)
  self.assertEqual((g.w[F['ign']],g.w[F['ignScore']],g.w[F['bonus']]),(1,2,100))
  self.step(g,300);self.assertEqual(g.w[F['mode']],1)
  e=self.new();self.step(e,300);self.assertEqual((e.w[F['mode']],e.w[F['vTarget']]),(1,520))
 def test_boost_gap_heat_and_invulnerability(self):
  g=self.new(1);g.w[F['vTarget']]=520;self.step(g,down_down=1);spent=g.w[F['fuel']]
  self.step(g,down_down=1);self.assertEqual(spent-g.w[F['fuel']],14)
  g.w[F['heat']]=1200;self.step(g);self.assertEqual((g.w[F['hull']],g.w[F['hits']]),(2,1))
  g.w[F['heat']]=1200;self.step(g);self.assertEqual(g.w[F['hull']],2)
 def test_shield_smashes_small_objects_and_pickups(self):
  for kind,key in ((1,'combo'),(3,'combo'),(11,'combo'),(6,'stars'),(7,'cans'),(15,'hull')):
   g=self.new(1);g.w[F['boostT']]=20;g.w[F['hull']]=2;self.obj(g,kind,160);before=g.w[F[key]];self.step(g)
   self.assertEqual(g.w[F[key]],before+1,kind);self.assertEqual(g.w[OBJ0],0)
 def test_separation_perfect_reward_and_tli(self):
  g=self.new(1);g.w[F['alt']]=4000<<8;g.w[F['sep']]=1;g.w[F['sepT']]=74;g.w[F['fuel']]=50000
  self.step(g,down_down=1);self.assertEqual((g.w[F['sep']],g.w[F['sepQ']],g.w[F['fuel']]),(2,2,77486))
  g.w[F['alt']]=14000<<8;g.w[F['tli']]=1;g.w[F['tliT']]=49
  self.step(g,down_down=1);self.assertEqual((g.w[F['tliHit']],g.w[F['tliQ']]),(1,2))
 def test_landing_alignment_speed_crash_retry_and_fuel_exhaustion(self):
  g=self.new(2);g.w[F['lx']]=g.w[F['pad']]=0
  g.w[F['pad']]=160;g.w[F['lx']]=160<<8;g.w[F['ly']]=206<<8;g.w[F['lvy']]=100
  self.step(g);self.assertEqual((g.w[F['mode']],g.w[F['win']],g.w[F['landings']]),(3,1,1))
  self.step(g,150);self.assertEqual(g.w[F['over']],1)
  e=self.new(2);e.w[F['lx']]=160<<8;e.w[F['pad']]=60;e.w[F['ly']]=206<<8;e.w[F['lvy']]=400
  self.step(e);self.assertEqual((e.w[F['hits']],e.w[F['hull']],e.w[F['mode']]),(1,2,2))
  self.assertIn(10,[e.w[FX0+i*5] for i in range(6)])
  e.w[F['fuel']]=1;self.step(e);self.assertEqual((e.w[F['fuel']],e.w[F['mode']]),(0,4))
 def test_mutations_are_caught(self):
  mutations=[('g->fuel-=2500','g->fuel-=2400'),('g->heat+=170','g->heat+=171'),
   ('g->vTarget=520+g->ignScore*20','g->vTarget=521+g->ignScore*20'),('g->lvy-=170','g->lvy-=169'),
   ('g->v+4','g->v+5'),('g->invuln=70','g->invuln=71')]
  for before,after in mutations:
   with self.subTest(mutation=before),tempfile.TemporaryDirectory() as folder:
    lib,State=build(folder,'space',WORDS,mutation=('adv_space.c',before,after))
    try:self.assertTrue(any(replay_hashed(lib,State,'space',t) for t in self.traces.values()))
    finally:unload_library(lib._handle)
if __name__=='__main__':unittest.main()
