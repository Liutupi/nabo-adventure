"""Guarded NIGHT automation must use public state and retry only reads."""
import json
import unittest
from unittest.mock import patch
import smoke_night

def telemetry():
    return dict(tick=10,score=0,res=1000,over=0,lane=1,x=120,move=0,cooldown=0,target=-1,speed=48,bugs=[[0]*6 for _ in range(8)])

class FakeLink:
    def __init__(self):self.commands=[];self.reads=0
    def send(self,value):self.commands.append(value)
    def read(self):
        self.reads+=1
        return '@night '+json.dumps(telemetry()) if self.reads==3 else ''

class NightSmoke(unittest.TestCase):
    def test_telemetry_loss_retries_reads_only(self):
        link=FakeLink();clock=iter([0,.1,.2,.7,.8,.9,1,1.1,1.2,1.3,1.4])
        with patch.object(smoke_night.time,'monotonic',side_effect=lambda:next(clock)):
            self.assertEqual(smoke_night.query(link)['res'],1000)
        self.assertGreaterEqual(len(link.commands),2)
        self.assertEqual(set(link.commands),{'>night.status'})

    def test_driver_catches_only_visible_firefly_in_hud_window(self):
        g=telemetry();g['target']=0;g['bugs'][0]=[1,130*60,227,1,16,0]
        self.assertEqual(smoke_night.drive(g),2)
        g['bugs'][0][0]=2;self.assertIsNone(smoke_night.drive(g))
        g['bugs'][0][0]=1;g['cooldown']=12;g['move']=1;self.assertIsNone(smoke_night.drive(g))

    def test_driver_waits_for_completed_move_and_avoids_expired_targets(self):
        g=telemetry();g['bugs'][0]=[1,10*60,227,1,16,0];self.assertEqual(smoke_night.drive(g),0)
        g['move']=10;self.assertIsNone(smoke_night.drive(g))
        g['move']=0;g['bugs'][0][1]=250*60;self.assertIsNone(smoke_night.drive(g))

if __name__=='__main__':unittest.main()
