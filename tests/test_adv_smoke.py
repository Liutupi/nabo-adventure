"""Exercise smoke protocol and guardrails without opening any serial port."""
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from smoke_adventure import (Blocked, Link, SmokeError, analyse_memory,
                             check_shell, cycle_game, run, verify_candidate)


def state(**updates):
    result = dict(page=1, owner=0, cursor=1, test=1, heap=100000,
                  largest=60000, overflow=0)
    result.update(updates)
    return result


class Clock:
    def __init__(self): self.t = 0
    def now(self): self.t += .01; return self.t
    def sleep(self, seconds): self.t += seconds


class FakeSerial:
    def __init__(self, lines=()): self.lines = list(lines); self.writes = []
    def write(self, raw): self.writes.append(raw.decode().strip())
    def flush(self): pass
    def readline(self): return self.lines.pop(0) if self.lines else b''


def status_line(**updates):
    return ('@adv ' + json.dumps(state(**updates)) + '\n').encode()


class BadgeSerial(FakeSerial):
    """Documented serial surface; no board or filesystem is opened."""
    def __init__(self):
        super().__init__()
        self.state = state(page=0, test=0)
        self.kiosk = self.settings = 0
        self.from_page = 1

    def write(self, raw):
        super().write(raw)
        command = raw.decode().strip()
        s = self.state
        if command == '>adv.test=1': s['test'] = 1
        elif command == '>adv.status':
            self.lines.append(('@adv ' + json.dumps(s) + '\n').encode())
        elif command.startswith('>adv.open='):
            if s['test'] != 1 or s['page'] != 1 or s['owner'] != 0:
                self.lines.append(b'@error open precondition\n')
            else:
                s['cursor'] = s['owner'] = 1 if command.endswith('jump') else 2
                s['page'] = 6
        elif command.startswith('>adv.key='):
            key, page = command[9:], s['page']
            if page == 0 and key == 'ok': s['page'] = 1
            elif page == 1:
                if key in ('up', 'down'):
                    path = [2, 0, 1, 3, 4, 5, 6, 7, 8]
                    s['cursor'] = path[path.index(s['cursor']) + (1 if key == 'up' else -1)]
                elif key == 'long_up': s['page'] = 0
                elif key == 'long_ok': self.from_page, s['page'] = 1, 3
                elif key == 'ok':
                    s['page'] = 2 if s['cursor'] == 0 else 6
                    if s['page'] == 6: s['owner'] = s['cursor']
            elif page == 2:
                if key == 'down': self.kiosk = (self.kiosk + 1) % 3
                elif key == 'ok':
                    self.from_page = 2
                    s['page'] = [3, 4, 1][self.kiosk]
                elif key == 'long_up': s['page'] = 1
            elif page == 3 and key == 'ok': s['page'] = self.from_page
            elif page == 4 and key == 'long_up': s['page'] = 2
            elif page == 6 and key == 'double_up':
                s['page'], s['owner'] = 1, 0


class SmokeProtocol(unittest.TestCase):
    def link(self, lines=()):
        serial = FakeSerial(lines)
        clock = Clock()
        return Link(serial, io.StringIO(), .2, clock.now, clock.sleep)

    def test_test_mode_requires_status_confirmation_before_any_input(self):
        link = self.link([b'@adv test=1\n', status_line(test=0)])
        with self.assertRaisesRegex(SmokeError, 'not confirmed'): link.enable_test()
        with self.assertRaisesRegex(SmokeError, 'requires'): link.key('ok')
        self.assertEqual(link.serial.writes, ['>adv.test=1', '>adv.status'])

    def test_valid_status_ignores_normal_logging_and_arms(self):
        link = self.link([b'I (12) NABO: ready\n', status_line(), status_line()])
        self.assertEqual(link.enable_test()['heap'], 100000)
        link.key('ok')
        self.assertTrue(link.armed)
        self.assertEqual(link.serial.writes[-1], '>adv.key=ok')

    def test_timeout_fragments_are_joined_before_parsing(self):
        raw = status_line()
        link = self.link([raw[:23], b'', raw[23:87], raw[87:]])
        self.assertEqual(link.enable_test()['heap'], 100000)
        self.assertTrue(link.armed)
        capture = self.link([b'@cap 42 0 240 ', b'abcd\n'])
        self.assertEqual(capture.read(), '')
        self.assertEqual(capture.read(), '@cap 42 0 240 abcd')

    def test_restart_after_arming_is_a_failure(self):
        for line in (b'ESP-ROM:esp32c3\n', b'rst:0x1 (POWERON)\n',
                     b'I (123) NABO-Adventure: adventure ready; heap=123\n'):
            link = self.link([status_line(), line])
            link.enable_test()
            with self.assertRaisesRegex(SmokeError, 'restarted'): link.status()

    def test_errors_missing_diagnostic_and_timeout_stop_the_run(self):
        for line, exception in ((b'Guru Meditation Error\n', SmokeError),
                                (b'@error command queue full\n', SmokeError),
                                (b'@error unknown command\n', Blocked)):
            link = self.link([status_line(), line])
            link.enable_test()
            with self.assertRaises(exception): link.status()
        with self.assertRaisesRegex(SmokeError, 'Timed out'): self.link().status()

    def test_lost_test_mode_overflow_and_invalid_metrics_are_rejected(self):
        for bad in (dict(test=0), dict(overflow=1), dict(heap=-1),
                    dict(largest=200000), dict(owner='0')):
            link = self.link([status_line(), status_line(**bad)])
            link.enable_test()
            with self.assertRaises(SmokeError): link.status()
        with self.assertRaisesRegex(SmokeError, 'Malformed'):
            self.link([b'@adv {broken\n']).status()

    def test_every_input_reconfirms_test_mode_and_stops_after_reset(self):
        for action in (lambda link: link.key('ok'), lambda link: link.edge(2, True)):
            link = self.link([status_line(), status_line(test=0)])
            link.enable_test()
            with self.assertRaisesRegex(SmokeError, 'lost'): action(link)
            self.assertFalse(any(command.startswith(('>adv.key=', '>adv.edge='))
                                 for command in link.serial.writes))

    def test_sustained_memory_decline_fails_and_recovered_transient_passes(self):
        self.assertEqual(analyse_memory([state()] * 11)['heap']['after'], 100000)
        for field in ('heap', 'largest'):
            samples = [state(**{field: state()[field] - 16 * i}) for i in range(11)]
            with self.assertRaisesRegex(SmokeError, field): analyse_memory(samples)
        analyse_memory([state(), state(heap=99984), state(), state()])

    def test_candidate_hash_chip_and_flash_receipt_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            app, receipt = Path(directory) / 'app.bin', Path(directory) / 'receipt.json'
            image = bytearray(256); image[0] = 0xe9; struct.pack_into('<H', image, 12, 5)
            app.write_bytes(image); sha = hashlib.sha256(image).hexdigest()
            self.assertEqual(verify_candidate(app, sha), 256)
            with self.assertRaisesRegex(SmokeError, 'mismatch'): verify_candidate(app, '0' * 64)
            receipt.write_text(json.dumps(dict(app_sha256=sha, port='TEST',
                status='PASS: APP AND ALL PRESERVED BYTES VERIFIED; BOOT NOT YET OBSERVED')), 'utf-8')
            verify_candidate(app, sha, receipt, 'TEST')
            with self.assertRaisesRegex(SmokeError, 'receipt'): verify_candidate(app, sha, receipt, 'WRONG')
            image[12] = 9; app.write_bytes(image)
            with self.assertRaisesRegex(SmokeError, 'ESP32-C3'):
                verify_candidate(app, hashlib.sha256(image).hexdigest())

    def test_complete_navigation_and_twenty_round_protocol(self):
        serial, clock = BadgeSerial(), Clock()
        link = Link(serial, io.StringIO(), .2, clock.now, clock.sleep)
        result = run(link, 10)
        for game in ('jump', 'dive'):
            self.assertEqual(result[game]['rounds'], 10)
            self.assertEqual(len(result[game]['game_samples']), 10)
            self.assertEqual(serial.writes.count('>adv.open=' + game), 11)
        self.assertEqual(serial.state['page'], 1)
        self.assertEqual(serial.state['test'], 1)
        self.assertNotIn('>adv.test=0', serial.writes)
        self.assertNotIn('>adv.sleep', serial.writes)
        first_key = next(i for i, command in enumerate(serial.writes)
                         if command.startswith('>adv.key='))
        clean_edges = [command for command in serial.writes[:first_key]
                       if command.startswith('>adv.edge=')]
        self.assertEqual(clean_edges, [f'>adv.edge={button},{pressed}'
                                      for button in range(3) for pressed in (1, 0)])

    def test_wrong_owner_does_not_count_as_entering_a_game(self):
        link = self.link([status_line(), status_line(), status_line(page=6, owner=1)])
        link.enable_test()
        with self.assertRaisesRegex(SmokeError, 'owner=2'):
            cycle_game(link, 'dive', 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
