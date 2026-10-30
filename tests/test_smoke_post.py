"""Serial retries must be idempotent reads and cleanup must be acknowledged."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from smoke_adventure import SmokeError
import smoke_post

def telemetry():
    return {'v2':1,'tick':1,'score':0,'res':1000,'speed':300,'dist':0,'bags':3,
            'delivered':0,'perfects':0,'cranes':0,'reds':0,'derails':0,'zone':0,
            'over':0,'events':[[0]*6 for _ in range(16)]}

class FakeLink:
    def __init__(self):self.commands=[];self.armed=True;self.reads=0;self.statuses=[]
    def send(self,value):self.commands.append(value)
    def read(self):
        self.reads+=1
        return '@post '+json.dumps(telemetry()) if self.reads==3 else ''
    def status(self):return self.statuses.pop(0)

class PostSerialRecovery(unittest.TestCase):
    def test_lost_telemetry_retries_only_read_commands(self):
        link=FakeLink();clock=iter([0,.1,.2,.7,.8,.9,1,1.1,1.2,1.3,1.4])
        with patch.object(smoke_post.time,'monotonic',side_effect=lambda:next(clock)):
            self.assertEqual(smoke_post.query(link)['res'],1000)
        self.assertGreaterEqual(len(link.commands),2)
        self.assertEqual(set(link.commands),{'>post.status'})

    def test_cleanup_retries_until_normal_mode_is_confirmed(self):
        link=FakeLink();link.statuses=[{'test':1},{'test':0,'best':[0,99],'seen':7}]
        state=smoke_post.restore(link)
        self.assertEqual(state['test'],0);self.assertFalse(link.armed)
        self.assertEqual(link.commands,['>adv.test=0','>adv.test=0'])

    def test_unacknowledged_cleanup_is_a_failure(self):
        link=FakeLink();link.statuses=[{'test':1}]*3
        with self.assertRaisesRegex(SmokeError,'not acknowledged'):smoke_post.restore(link)

if __name__=='__main__':unittest.main(verbosity=2)
