"""Production V2 rules match the approved JS reference, including resets and held keys."""
import ctypes,json,tempfile,unittest
from pathlib import Path
from game_harness import ROOT,Input,build,replay_hashed
from host_tools import unload_library

class V2Rules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.games={}
        for game in ('sky','climb','post'):
            traces={p.stem:json.loads(p.read_text()) for p in (ROOT/'tests/v2_golden'/game).glob('*.json')}
            words=len(traces['idle']['initial']);folder=Path(cls.temp.name)/game;folder.mkdir()
            lib,State=build(folder,game+'_v2',words)
            cls.games[game]=(lib,State,traces,{k:i for i,k in enumerate(traces['idle']['fields'])})
    @classmethod
    def tearDownClass(cls):
        for lib,*_ in cls.games.values():unload_library(lib._handle)
        cls.temp.cleanup()
    def test_reference_replays(self):
        for game,(lib,State,traces,_) in self.games.items():
            self.assertEqual(set(traces),{'idle','spam','wiggle','casual','skilled','fuzz'})
            for kind,trace in traces.items():
                with self.subTest(game=game,kind=kind):self.assertIsNone(replay_hashed(lib,State,game+'_v2',trace))

    def new(self,game):
        lib,State,_,fields=self.games[game];g=State()
        getattr(lib,'adv_'+game+'_v2_start')(ctypes.byref(g),1)
        for name in ('nextGround','nextSky','nextRock','nextEvent'):
            if name in fields:g.w[fields[name]]=1<<29
        return g,fields

    def step(self,game,g,n=1,**bits):
        lib=self.games[game][0]
        for _ in range(n):getattr(lib,'adv_'+game+'_v2_step')(ctypes.byref(g),ctypes.byref(Input(**bits)))

    def test_sky_mailbox_and_bullseye_boundaries(self):
        for dx in (-11,-10,-4,-3,0,3,4,10,11):
            with self.subTest(dx=dx):
                g,f=self.new('sky');g.w[f['spd']]=0
                obj=len(f)+4;letter=obj+24*7
                g.w[obj:obj+7]=(1,200,180,0,0,0,0)
                g.w[letter:letter+6]=(1,(200+dx)*256,180*256-1,0,0,150)
                self.step('sky',g)
                self.assertEqual(g.w[f['delivered']],int(abs(dx)<=10))
                self.assertEqual(g.w[f['bulls']],int(abs(dx)<=3))
                self.assertEqual(g.w[f['bonus']],20 if abs(dx)<=3 else 10 if abs(dx)<=10 else 0)
                self.assertEqual(g.w[f['missDrops']],int(abs(dx)>10))

    def test_sky_lightning_has_a_finite_column(self):
        for y,hit in ((196,1),(200,0)):
            g,f=self.new('sky');g.w[f['y']]=y*256
            obj=len(f)+4;g.w[obj:obj+7]=(4,92,36,0,199,0,0)
            self.step('sky',g);self.assertEqual(g.w[f['hits']],hit)

    def test_climb_ice_requires_the_correct_held_hand(self):
        for held in (False,True):
            g,f=self.new('climb');rows=len(f)+2
            g.w[rows+4]=3
            self.step('climb',g,up_down=1)
            self.assertEqual((g.w[f['row']],g.w[f['ice']]),(1,15))
            self.step('climb',g,15,up_held=int(held))
            self.assertEqual(g.w[f['grabs']],int(held))
            self.assertEqual(g.w[f['iceSlips']],int(not held))

    def test_climb_crumble_expiry_and_empty_destination(self):
        g,f=self.new('climb');rows=len(f)+2;g.w[rows+4]=2
        self.step('climb',g,up_down=1);self.assertEqual(g.w[f['crumble']],41)
        self.step('climb',g,40);self.assertEqual(g.w[f['crumbles']],0)
        self.step('climb',g);self.assertEqual((g.w[f['crumbles']],g.w[f['row']]),(1,0))
        g,f=self.new('climb');rows=len(f)+2;g.w[f['row']]=3
        g.w[rows+2*4+1]=0;g.w[rows+3*4+1]=0
        self.step('climb',g,down_down=1);self.step('climb',g,14)
        self.assertEqual((g.w[f['lane']],g.w[f['row']]),(1,1))

    def test_climb_rock_collision_switches_lanes_at_half_traverse(self):
        for traverse,hit in ((9,1),(8,0)):
            g,f=self.new('climb');g.w[f['trav']]=traverse
            rock=len(f)+2+32*4;g.w[rock:rock+5]=(1,0,0,145,0)
            self.step('climb',g);self.assertEqual(g.w[f['rockHits']],hit)

    def test_post_throw_window_perfect_window_and_no_bags(self):
        for dx in (-15,-14,-5,-4,0,4,5,14,15):
            g,f=self.new('post');g.w[f['v']]=0;g.w[f['res']]=800;ev=len(f)
            g.w[ev:ev+6]=(1,120+dx,0,0,0,0)
            self.step('post',g,down_down=1)
            self.assertEqual(g.w[f['delivered']],int(abs(dx)<=14))
            self.assertEqual(g.w[f['perfects']],int(abs(dx)<=4))
            self.assertEqual(g.w[f['wasted']],int(abs(dx)>14))
        g,f=self.new('post');g.w[f['v']]=0;g.w[f['bags']]=0;ev=len(f)
        g.w[ev:ev+6]=(1,120,0,0,0,0);self.step('post',g,down_down=1)
        self.assertEqual((g.w[f['delivered']],g.w[f['wasted']],g.w[ev+5]),(0,0,0))

    def test_post_speed_limit_has_exact_grace_period(self):
        g,f=self.new('post');g.w[f['v']]=600;ev=len(f)
        g.w[ev:ev+6]=(3,180,360,180,0,0)
        self.step('post',g,23,up_held=1);self.assertEqual(g.w[f['derails']],0)
        self.step('post',g,up_held=1);self.assertEqual((g.w[f['derails']],g.w[f['stun']]),(1,50))

    def test_rule_mutations_are_caught(self):
        mutations={
            'sky':[('SKY_V2_BOX_HALF (10)','SKY_V2_BOX_HALF (8)'),('SKY_V2_BOLT_LEN (62)','SKY_V2_BOLT_LEN (82)')],
            'climb':[('CLIMB_V2_ICE_HOLD (15)','CLIMB_V2_ICE_HOLD (10)'),('CLIMB_V2_RHYTHM (24)','CLIMB_V2_RHYTHM (18)')],
            'post':[('POST_V2_WINDOW (14)','POST_V2_WINDOW (10)'),('POST_V2_OVER_GRACE (24)','POST_V2_OVER_GRACE (20)')],
        }
        for game,edits in mutations.items():
            _,_,traces,_=self.games[game];words=len(traces['idle']['initial'])
            for old,new in edits:
                with self.subTest(game=game,rule=old),tempfile.TemporaryDirectory() as folder:
                    lib,State=build(folder,game+'_v2',words,mutation=('adv_'+game+'_v2.h',old,new))
                    try:
                        caught=any(replay_hashed(lib,State,game+'_v2',trace) for trace in traces.values())
                        if game=='sky' and 'BOLT_LEN' in old:
                            # The replay players avoid this edge; the finite-column boundary must also kill the mutant.
                            probe=State();lib.adv_sky_v2_start(ctypes.byref(probe),1);fields=self.games[game][3]
                            probe.w[fields['nextGround']]=probe.w[fields['nextSky']]=1<<29
                            probe.w[fields['y']]=200*256;obj=len(fields)+4
                            probe.w[obj:obj+7]=(4,92,36,0,199,0,0)
                            lib.adv_sky_v2_step(ctypes.byref(probe),ctypes.byref(Input()))
                            caught=caught or probe.w[fields['hits']]!=0
                        self.assertTrue(caught)
                    finally:unload_library(lib._handle)
