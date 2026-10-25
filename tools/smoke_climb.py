#!/usr/bin/env python3
"""Exercise CLIMB through guarded real inputs; never writes fabricated progress.

Same contract as smoke_night.py: verified candidate only, test mode for the run,
real OK press/release edges, and normal mode plus untouched records restored.
Written in the cloud without a device: it has not been run yet.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from smoke_adventure import Link, SmokeError, verify_candidate, analyse_memory
from smoke_post import BufferedPort, restore, edge

ROOT = Path(__file__).resolve().parents[1]
UP, DOWN, OK = 0, 1, 2
ROW = 40


def query(link):
    link.send('>climb.status'); until = time.monotonic()+8; retry = time.monotonic()+.5
    while time.monotonic() < until:
        line = link.read()
        if line.startswith('@climb '):
            state = json.loads(line[7:])
            if not all(type(state.get(k)) is int for k in ('tick', 'score', 'res', 'over', 'row', 'side', 'act', 'press')):
                raise SmokeError('Invalid CLIMB status')
            if len(state.get('holds', [])) != 6 or len(state.get('rocks', [])) != 4: raise SmokeError('Invalid CLIMB objects')
            return state
        if time.monotonic() >= retry: link.send('>climb.status'); retry = time.monotonic()+.5
    raise SmokeError('No CLIMB telemetry')


def choose(g):
    """Only what the screen shows: holds above NABO and rocks in each column."""
    side, holds = g['side'], g['holds']
    hand = g['row']*ROW
    danger = lambda s: any(on and rs == s and hand-41 <= y <= hand+5*ROW for on, rs, y in g['rocks'])
    if danger(side) and holds[1][1-side] and not danger(1-side): return 'tap'
    if holds[1][1-side] in (1, 3) and not danger(1-side): return 'tap'
    if holds[2][side] in (1, 3) and not danger(side): return 'jump2'
    if holds[3][side] in (1, 3) and not danger(side): return 'jump3'
    if holds[1][1-side]: return 'tap'
    return None


def press(link, kind):
    edge(link, OK, True)
    time.sleep({'tap': .05, 'jump2': .4, 'jump3': .85}[kind])
    edge(link, OK, False)


def enter(link):
    state = link.status()
    if state['page'] == 0: link.key('ok'); link.map()
    elif state['page'] != 1: raise SmokeError('CLIMB entry expects cover or map')
    link.send('>adv.open=climb'); state = link.expect(7)
    if state['station'] != 5 or state['phase'] != 0: raise SmokeError('CLIMB title missing')
    link.key('ok'); deadline = time.monotonic()+12
    while time.monotonic() < deadline:
        state = link.expect(7)
        if state['phase'] == 2: return state
        if state['phase'] != 1: raise SmokeError('Unexpected CLIMB countdown')
        time.sleep(.15)
    raise SmokeError('CLIMB countdown stalled')


def play(link, target=50):
    enter(link); start = time.monotonic(); checked = start; last = -1; profile = []
    while time.monotonic()-start < 300:
        g = query(link)
        if g['score'] != last: print(f'CLIMB height={g["score"]} stamina={g["res"]}', flush=True); last = g['score']
        if g['over']:
            state = link.expect(7)
            if state['phase'] == 5:
                if g['score'] < target: raise SmokeError('CLIMB ended before target')
                return {'score': g['score'], 'seconds': time.monotonic()-start, 'hits': g['hits'], 'misses': g['misses'],
                        'profile': profile}
            time.sleep(.1); continue
        if g['score'] < target and g['act'] == 0 and g['press'] < 0 and g['queue'] == 0:
            kind = choose(g)
            if kind: press(link, kind)
        now = time.monotonic()
        if now-checked >= 1:
            state = link.expect(7)
            if state['heap'] < 60000 or state['largest'] < 30000: raise SmokeError('Insufficient active-game heap')
            profile.append({'time': now-start, 'frames': state['frames'], 'draw_us': state['draw_us'], 'bytes': state['bytes']})
            checked = now
        time.sleep(.05)
    raise SmokeError('CLIMB did not end')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True); parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--sha256', required=True); parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=10); args = parser.parse_args()
    if args.rounds < 2: parser.error('--rounds must be >=2')
    verify_candidate(args.app, args.sha256, args.receipt, args.port)
    import serial
    folder = ROOT/'private/climb-smoke'; folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S'); result = {'candidate_sha256': args.sha256, 'status': 'INCOMPLETE'}
    with (folder/(stamp+'.log')).open('w', encoding='utf-8') as log:
        port = serial.Serial(port=None, baudrate=115200, timeout=.05); port.dtr = port.rts = False; port.port = args.port; port.open()
        port.set_buffer_size(rx_size=1024*1024, tx_size=16384); link = Link(BufferedPort(port), log)
        owned = False
        try:
            initial = link.status()
            if initial['test'] or initial['owner'] or initial['page'] not in (0, 1): raise SmokeError('Start in normal cover/map with no real round active')
            owned = True; link.enable_test(); before = (initial['best'], initial['seen'])
            result['play'] = play(link); link.key('double_up'); link.map(); samples = []
            for _ in range(args.rounds+1):
                enter(link)
                link.key('up'); state = link.expect(7)
                if state['phase'] != 2: raise SmokeError('Single UP left play')
                press(link, 'tap'); time.sleep(.6)
                if query(link)['row'] < 1: raise SmokeError('Tap did not climb')
                link.key('long_up'); state = link.expect(7)
                if state['phase'] != 3: raise SmokeError('Long UP did not pause')
                tick = query(link)['tick']; time.sleep(.4)
                if query(link)['tick'] != tick: raise SmokeError('Paused game advanced')
                link.key('ok'); state = link.expect(7)
                if state['phase'] != 2: raise SmokeError('OK did not resume')
                link.key('double_up'); samples.append(link.map())
            result['memory'] = analyse_memory(samples)
            restored = restore(link)
            if restored['test'] or (restored['best'], restored['seen']) != before: raise SmokeError('Durable progress changed')
            result.update(status='PASS: SERIAL CLIMB ONLY', rounds=args.rounds, warmup_rounds=1, normal_mode_restored=True,
                          durable_progress_unchanged=True,
                          physical_checks='User tap/charge feel, frame rate, costume, sound and sleep/wake still required')
        except Exception as error:
            result.update(status='FAIL', error=str(error))
            if owned:
                try: result['normal_mode_restored'] = restore(link)['test'] == 0
                except Exception as cleanup: result['normal_mode_restored'] = False; result['cleanup_error'] = str(cleanup)
        finally: port.close()
    (folder/(stamp+'.json')).write_text(json.dumps(result, indent=2)+'\n', 'utf-8')
    public = {k: v for k, v in result.items() if k != 'play'}
    public['play'] = {k: v for k, v in result.get('play', {}).items() if k != 'profile'}
    print(json.dumps(public, indent=2)); return 0 if result['status'].startswith('PASS') else 1


if __name__ == '__main__': raise SystemExit(main())
