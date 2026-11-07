"""跳一跳双人对战：两个真实 adv_vs 实例经模拟 ESP-NOW 链路（延迟/丢包/乱序/断线）对打。"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from host_tools import CC

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'firmware/main'
VS_LOBBY, VS_WAIT, VS_INVITED, VS_COUNTDOWN, VS_PLAY, VS_RESULT, VS_NOTICE, VS_PICK = range(8)
NOTE_NO_ANSWER, NOTE_DECLINED, NOTE_BUSY, NOTE_CANCELLED, NOTE_LOST, NOTE_LEFT = range(1, 7)


class Versus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        blob = (MAIN / 'jump_sprites.bin').read_bytes()
        snd = (MAIN / 'jump_sounds.bin').read_bytes()
        (tmp / 'blob.c').write_text(
            'const unsigned char sprites[] __asm__("_binary_jump_sprites_bin_start")={' + ','.join(map(str, blob)) + '};\n'
            'const unsigned char sounds[] __asm__("_binary_jump_sounds_bin_start")={' + ','.join(map(str, snd)) + '};\n', 'ascii')
        exe = tmp / 'vs_sim'
        subprocess.run([CC, '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror', '-I', str(MAIN),
                        str(ROOT / 'tests/vs_host/vs_sim.c'), str(MAIN / 'adv_vs.c'), str(MAIN / 'nabo_jump_model.c'),
                        str(MAIN / 'nabo_jump_rig.c'), str(MAIN / 'nabo_jump_codec.c'), str(tmp / 'blob.c'), '-o', str(exe)],
                       check=True, capture_output=True)
        out = subprocess.run([str(exe)], check=True, capture_output=True, text=True, timeout=120)
        cls.r = {d['case']: d for d in map(json.loads, out.stdout.splitlines())}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_pairing_shares_course_and_start(self):
        p = self.r['pair']
        self.assertEqual((p['a'], p['b']), (VS_COUNTDOWN, VS_COUNTDOWN))
        self.assertTrue(p['seed_eq'] and p['session_eq'])
        self.assertEqual((p['a_host'], p['b_host']), (1, 0))
        self.assertEqual(p['games'], [6, 6], 'the invitee (still on the game list) takes the inviter\'s game')
        self.assertLessEqual(abs(p['go_skew']), 40, 'both badges must start within 40 ms')

    def test_lossy_matches_agree_and_rematch(self):
        m = self.r['matches']
        self.assertEqual(m['stuck'], 0)
        self.assertEqual(m['matches'], 40)
        self.assertEqual(m['consistent'], 40, 'outcomes must mirror and both see the same two scores')
        self.assertEqual(m['rematch_ok'], 40)
        a, b = m['tallies_a'], m['tallies_b']
        self.assertEqual((a[0], a[1], a[2]), (b[1], b[0], b[2]))

    def test_link_cut_is_a_void_not_a_win(self):
        c = self.r['cut']
        self.assertEqual((c['a'], c['note']), (VS_NOTICE, NOTE_LOST))
        self.assertLessEqual(c['after_ms'], 4100)
        self.assertEqual(c['a_wins'], 0)

    def test_leave_decline_and_timeout(self):
        self.assertEqual((self.r['bye']['a'], self.r['bye']['note']), (VS_NOTICE, NOTE_LEFT))
        d = self.r['decline']
        self.assertEqual((d['a'], d['note'], d['b']), (VS_NOTICE, NOTE_DECLINED, VS_LOBBY))
        n = self.r['no_answer']
        self.assertEqual((n['a'], n['note']), (VS_NOTICE, NOTE_NO_ANSWER))

    def test_game_list(self):
        p = self.r['pick']
        self.assertEqual((p['start'], p['lobby'], p['game'], p['back'], p['pick']), (VS_PICK, VS_LOBBY, 4, VS_PICK, 2))

    def test_ghost_opponent(self):
        g = self.r['ghost']
        self.assertTrue(300 <= g['target'] <= 2500 and 30000 <= g['duration'] < 90000, g)
        self.assertTrue(0 < g['mid'] < g['target'] and not g['mid_over'])
        self.assertEqual((g['end'], g['end_over']), (g['target'], 1))

    def test_packets(self):
        p = self.r['packet']
        self.assertEqual((p['ok'], p['bad_sum'], p['short']), (1, 0, 0))
        self.assertEqual(p['name'], 'NABO-A958')

    def test_nabo_practice_needs_no_radio(self):
        p = self.r['practice']
        self.assertEqual(p['rounds'], 60)
        self.assertEqual(p['ended'], 60)
        self.assertEqual(p['radio_packets'], 0)
        self.assertTrue(15 <= p['bot_avg'] <= 60, p)


if __name__ == '__main__':
    unittest.main()
