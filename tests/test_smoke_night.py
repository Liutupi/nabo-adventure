"""Guarded NIGHT V2 automation must use public telemetry, retry only reads, and match the rules' fly path."""
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
import smoke_night

ROOT = Path(__file__).resolve().parents[1]


def telemetry(**extra):
    g = dict(tick=10, score=0, res=720, over=0, light=720000, x=0, gait=1, stun=0, swing=0, combo=0, caught=0, meter=0, need=30,
             bursts=0, event=0, whiffs=0, trips=0, owl_hits=0, moth_hits=0, last_swing=-1000, flies=[], moths=[], roots=[], owls=[])
    g.update(extra); return g


class FakeLink:
    def __init__(self): self.commands = []; self.reads = 0
    def send(self, value): self.commands.append(value)
    def read(self):
        self.reads += 1
        return '@night ' + json.dumps(telemetry()) if self.reads == 3 else ''


class NightSmoke(unittest.TestCase):
    def test_telemetry_loss_retries_reads_only(self):
        link = FakeLink(); clock = iter([0, .1, .2, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4])
        with patch.object(smoke_night.time, 'monotonic', side_effect=lambda: next(clock)):
            self.assertEqual(smoke_night.query(link)['res'], 720)
        self.assertGreaterEqual(len(link.commands), 2)
        self.assertEqual(set(link.commands), {'>night.status'})

    def test_fly_path_matches_the_js_rules(self):
        script = ("const N=require('./game-art/adventure/prototype/adv_night.js');const out=[];"
                  "for(const [b,a,p,f,t] of [[150,30,1234,400,77],[128,-1,65000,623,36000],[104,36,0,261,1],[140,22,40000,500,123456]])"
                  "out.push(N.flyY({baseY:b,amp:a,ph:p,freq:f},t));console.log(JSON.stringify(out))")
        want = json.loads(subprocess.run(['node', '-e', script], cwd=ROOT, check=True, capture_output=True, text=True).stdout)
        got = [smoke_night.fly_y([1, 0, b, a, p, f, 0], t) for b, a, p, f, t in [[150, 30, 1234, 400, 77], [128, -1, 65000, 623, 36000], [104, 36, 0, 261, 1], [140, 22, 40000, 500, 123456]]]
        self.assertEqual(got, want)

    def test_driver_swings_only_at_reachable_fireflies(self):
        g = telemetry(flies=[[1, (20 + 7) << 8, 158, 0, 0, 0, 0]])
        self.assertTrue(smoke_night.drive(g))
        self.assertFalse(smoke_night.drive(dict(g, swing=5)))
        self.assertFalse(smoke_night.drive(dict(g, stun=3)))
        self.assertFalse(smoke_night.drive(telemetry(flies=[[1, 200 << 8, 158, 0, 0, 0, 0]])))
        self.assertFalse(smoke_night.drive(telemetry(flies=[[1, 27 << 8, 100, 0, 0, 0, 0]])))


if __name__ == '__main__': unittest.main()
