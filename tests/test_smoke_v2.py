"""The device suite uses approved landscape gestures for every V2 station."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import smoke_late_games as suite
from smoke_adventure import SmokeError

class Link:
    def __init__(self):
        self.armed=True;self.commands=[]
        self.s={'page':1,'test':1,'owner':0,'heap':120000,'largest':60000,'score':0,'res':1000}
    def status(self):return dict(self.s)
    def expect(self,page):
        if self.s['page']!=page:raise SmokeError('Wrong fake page')
        return dict(self.s)
    def map(self):return self.expect(1)
    def send(self,command):
        self.commands.append(command)
        if command.startswith('>adv.open='):
            self.s.update(page=7,station=suite.STATIONS[command.split('=')[1]],phase=0)
    def key(self,key):
        self.commands.append('key:'+key)
        if key=='down':self.s['phase']=2
        elif key=='long_down':self.s['phase']=3
        elif key=='double_up' and self.s['phase']==3:self.s['page']=1
        elif key not in ('double_up',):raise SmokeError('Unexpected gesture '+key)

class V2Smoke(unittest.TestCase):
    def test_every_station_starts_and_pauses_with_middle_and_only_exits_from_pause(self):
        for name in suite.STATIONS:
            with self.subTest(game=name),patch.object(suite.time,'sleep'):
                link=Link();result=suite.controls(link,name)
                self.assertEqual(result['map']['page'],1)
                self.assertEqual(link.commands[0],'>adv.open='+name)
                self.assertEqual(link.commands.count('key:long_down'),2)
                self.assertEqual(link.commands.count('key:double_up'),2)
                self.assertNotIn('key:long_up',link.commands)
                self.assertNotIn('key:ok',link.commands)
    def test_raw_edges_require_confirmed_test_ownership(self):
        link=Link();link.armed=False
        with self.assertRaisesRegex(SmokeError,'guard'):suite.edge(link,0,True)
        self.assertEqual(link.commands,[])
