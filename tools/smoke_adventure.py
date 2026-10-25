#!/usr/bin/env python3
"""Serial-only adventure smoke check. Never flashes or changes persistent settings.

Run after a guarded app-only flash; --receipt can bind its verified readback to this
run. Test mode stays enabled afterwards: reset the badge before normal play.
Physical buttons, speaker quality and deep-sleep wake still need human checks.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PATH = [2, 0, 1, 3, 4, 5, 6, 7, 8]
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
FAULT = re.compile(r'Guru Meditation|assert failed|abort\(\) was called|panic|'
                   r'Stack smashing|input overflow|^E \(', re.I)
RESET = re.compile(r'ESP-ROM:|rst:0x|Rebooting|adventure ready;')


class SmokeError(RuntimeError):
    pass


class Blocked(SmokeError):
    pass


def verify_candidate(path, sha256, receipt=None, port=None):
    data = Path(path).read_bytes()
    if not re.fullmatch('[0-9a-f]{64}', sha256):
        raise SmokeError('An explicit lowercase SHA256 is required')
    if (not 256 <= len(data) <= 0x3f0000 or data[0] != 0xe9 or
            struct.unpack_from('<H', data, 12)[0] != 5):
        raise SmokeError('Candidate is not a valid-size ESP32-C3 app image')
    if hashlib.sha256(data).hexdigest() != sha256:
        raise SmokeError('Candidate SHA256 mismatch')
    if receipt:
        saved = json.loads(Path(receipt).read_text('utf-8'))
        if (saved.get('app_sha256') != sha256 or saved.get('port') != port or
                not saved.get('status', '').startswith('PASS: APP AND ALL PRESERVED BYTES VERIFIED')):
            raise SmokeError('Flash receipt does not confirm this app and port')
    return len(data)


def analyse_memory(samples, tolerance=0):
    """Reject sustained loss after warmup, retaining every sample for inspection."""
    if len(samples) < 2:
        raise SmokeError('Not enough map memory samples')
    result = {}
    for field in ('heap', 'largest'):
        values = [sample[field] for sample in samples]
        tail = values[-min(3, len(values) - 1):]
        result[field] = {'before': values[0], 'after': values[-1],
                         'minimum': min(values), 'maximum': max(values)}
        if all(value < values[0] - tolerance for value in tail):
            raise SmokeError(f'Sustained map {field} loss: {values}')
    return result


class Link:
    def __init__(self, serial, log, timeout=8, clock=time.monotonic, sleep=time.sleep):
        self.serial, self.log, self.timeout = serial, log, timeout
        self.clock, self.sleep = clock, sleep
        self.armed = False
        self.pending = b''

    def send(self, command):
        self.log.write('TX ' + command + '\n')
        self.log.flush()
        self.serial.write((command + '\n').encode('ascii'))
        self.serial.flush()

    def read(self):
        raw = self.serial.readline()
        if not raw:
            return ''
        # pyserial may time out in the middle of a long USB-console line.
        # Keep its bytes until a newline arrives instead of parsing a partial JSON/capture.
        self.pending += raw
        if len(self.pending) > 4096:
            raise SmokeError('Device line exceeds protocol limit')
        if not self.pending.endswith(b'\n'):
            return ''
        raw, self.pending = self.pending, b''
        line = ANSI.sub('', raw.decode('utf-8', errors='replace')).strip()
        self.log.write('RX ' + line + '\n')
        self.log.flush()
        if FAULT.search(line) or line.startswith('@error'):
            if 'unknown command' in line and self.armed:
                raise Blocked('Firmware lacks the requested test-only diagnostic command')
            raise SmokeError('Device reported error: ' + line)
        if self.armed and RESET.search(line):
            raise SmokeError('Device restarted during smoke run: ' + line)
        return line

    def status(self):
        self.send('>adv.status')
        deadline = self.clock() + self.timeout
        while self.clock() < deadline:
            line = self.read()
            if not line.startswith('@adv {'):
                continue
            try:
                state = json.loads(line[5:])
            except (ValueError, TypeError) as exc:
                raise SmokeError('Malformed adventure status JSON') from exc
            for field in ('page', 'owner', 'cursor', 'test', 'heap', 'largest', 'overflow'):
                if type(state.get(field)) is not int:
                    raise SmokeError('Missing or invalid status field: ' + field)
            if state['heap'] <= 0 or not 0 < state['largest'] <= state['heap']:
                raise SmokeError('Invalid heap metrics')
            if state['overflow']:
                raise SmokeError('Renderer overflow')
            if self.armed and state['test'] != 1:
                raise SmokeError('Test mode was lost; refusing further input')
            return state
        raise SmokeError('Timed out waiting for adventure status')

    def enable_test(self):
        self.send('>adv.test=1')
        state = self.status()
        if state['test'] != 1:
            raise SmokeError('Test mode not confirmed; refusing input')
        self.armed = True
        return state

    def expect(self, page, owner=0):
        state = self.status()
        if state['page'] != page or state['owner'] != owner:
            raise SmokeError(f'Expected page={page}, owner={owner}; received '
                             f'page={state["page"]}, owner={state["owner"]}')
        return state

    def key(self, name):
        if not self.armed:
            raise SmokeError('Input requires confirmed test mode')
        self.status()
        self.send('>adv.key=' + name)
        self.sleep(.10)

    def edge(self, button, down):
        if not self.armed:
            raise SmokeError('Input requires confirmed test mode')
        self.status()
        self.send(f'>adv.edge={button},{int(down)}')
        self.sleep(.08)

    def map(self):
        for _ in range(25):
            state = self.status()
            if state['page'] == 1 and state['owner'] == 0:
                return state
            if state['page'] != 5 or state['owner'] != 0:
                raise SmokeError('Expected map or pending stamp')
            self.key('ok')
        raise SmokeError('Stamp ceremony did not finish')

    def move(self, station):
        state = self.map()
        for _ in range(len(PATH)):
            if state['cursor'] == station:
                return state
            direction = 'up' if PATH.index(state['cursor']) < PATH.index(station) else 'down'
            self.key(direction)
            next_state = self.map()
            if next_state['cursor'] == state['cursor']:
                raise Blocked('Map station locked; no scores were fabricated')
            state = next_state
        raise SmokeError('Could not reach requested map station')


def check_shell(link):
    state = link.enable_test()
    if state['owner'] != 0 or state['page'] not in (0, 1, 5):
        raise SmokeError('Start at the cover or map after a verified flash/reset')
    # Raw shell edges do not navigate. A fresh press clears any swallowed bit;
    # its matching release clears held state before click-only navigation.
    for button in range(3):
        link.edge(button, True)
        link.edge(button, False)
    if state['page'] != 0:
        link.map()
        link.key('long_up')
    link.expect(0)
    link.key('ok')
    link.map()
    link.move(0)
    link.key('ok')
    link.expect(2)
    link.key('ok')
    link.expect(3)
    link.key('down')
    link.key('up')
    link.key('ok')
    link.expect(2)
    link.key('down')
    link.key('ok')
    link.expect(4)
    # Inspect the settings list and status; do not change any setting.
    for _ in range(4):
        link.key('down')
    link.key('ok')
    link.expect(4)
    link.key('ok')
    link.key('long_up')
    link.expect(2)
    link.key('long_up')
    link.map()
    link.key('long_ok')
    link.expect(3)
    link.key('ok')
    link.move(1)
    link.key('ok')
    link.expect(6, 1)  # Also verify the real, normally unlocked map entrance.
    link.key('up')
    return link.map()


def cycle_game(link, game, rounds):
    owner = 1 if game == 'jump' else 2
    samples, inside = [], []
    # One full warmup first; keep it in the raw log and separate from measurements.
    for iteration in range(rounds + 1):
        link.map()
        link.send('>adv.open=' + game)
        link.sleep(.4)
        link.expect(6, owner)
        link.edge(2, True)
        link.sleep(.28 if owner == 1 else .08)
        link.edge(2, False)
        link.sleep(.7)
        if owner == 2:
            link.edge(1, True)
            link.sleep(.35)
            link.edge(1, False)
        active = link.expect(6, owner)
        link.key('up' if owner == 1 else 'long_up')
        link.sleep(.35)
        returned = link.map()
        if iteration == 0:
            samples.append(returned)
        else:
            inside.append(active)
            samples.append(returned)
    return {'rounds': rounds, 'warmup_rounds': 1, 'memory': analyse_memory(samples),
            'map_samples': samples, 'game_samples': inside}


def run(link, rounds, result=None):
    check_shell(link)
    if result is None:
        result = {}
    for game in ('jump', 'dive'):
        result[game] = cycle_game(link, game, rounds)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--rounds', type=int, default=10)
    parser.add_argument('--timeout', type=float, default=8)
    parser.add_argument('--private-dir', type=Path, default=ROOT / 'private' / 'smoke')
    args = parser.parse_args()
    if args.rounds < 2 or args.timeout <= 0:
        parser.error('--rounds must be >= 2 and --timeout must be positive')
    private = args.private_dir.resolve()
    if not private.is_relative_to((ROOT / 'private').resolve()):
        parser.error('Device logs and results must stay under this repository private/')
    verify_candidate(args.app, args.sha256, args.receipt, args.port)
    import serial
    private.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d-%H%M%S-%f')
    result = {'candidate_sha256': args.sha256, 'flash_receipt_verified': bool(args.receipt),
              'status': 'INCOMPLETE', 'test_mode_left_enabled': True,
              'unverified': ['physical buttons', 'speaker quality', 'deep sleep and button wake'],
              'games': {}}
    code = 1
    try:
        with (private / (stamp + '.log')).open('w', encoding='utf-8') as log:
            # Explicit line states avoid an intentional bootloader/reset pulse on open.
            port = serial.Serial(port=None, baudrate=115200, timeout=.2)
            port.dtr = port.rts = False
            port.port = args.port
            try:
                port.open()
                link = Link(port, log, args.timeout)
                run(link, args.rounds, result['games'])
            finally:
                port.close()
        result['status'], code = 'PASS: SERIAL SMOKE ONLY', 0
    except (SmokeError, OSError, serial.SerialException) as exc:
        result['status'] = 'BLOCKED' if isinstance(exc, Blocked) else 'FAIL'
        result['error'] = str(exc)
    finally:
        (private / (stamp + '.json')).write_text(json.dumps(result, indent=2) + '\n', 'utf-8')
    public = {key: value for key, value in result.items() if key != 'games'}
    public['games'] = {game: {key: value for key, value in data.items()
                             if key not in ('map_samples', 'game_samples')}
                       for game, data in result['games'].items()}
    print(json.dumps(public, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
