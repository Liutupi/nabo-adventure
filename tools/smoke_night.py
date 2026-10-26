#!/usr/bin/env python3
"""Exercise NIGHT V2 through guarded real inputs; never writes fabricated progress.

Runs one round with real middle-key taps, then N enter/run/slow/pause/return cycles.
UP never leaves while playing; the map is reached from the pause page."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from smoke_adventure import Link,SmokeError,verify_candidate,analyse_memory
from smoke_post import BufferedPort,restore,tap,edge

ROOT=Path(__file__).resolve().parents[1]

QSIN=(0,101,201,301,401,501,601,700,799,897,995,1092,1189,1285,1380,1474,1567,1660,1751,1842,1931,2019,2106,2191,2276,2359,
      2440,2520,2598,2675,2751,2824,2896,2967,3035,3102,3166,3229,3290,3349,3406,3461,3513,3564,3612,3659,3703,3745,3784,3822,
      3857,3889,3920,3948,3973,3996,4017,4036,4052,4065,4076,4085,4091,4095,4096)
NET_DX,NET_Y,NET_R=20,158,28   # NET_R is 3 px inside the rule radius to absorb serial latency

def isin(i):
    i&=255
    return QSIN[i] if i<64 else QSIN[128-i] if i<128 else -QSIN[i-128] if i<192 else -QSIN[256-i]

def fly_y(f,tick):
    _,_,base,amp,ph,freq,_=f;v=amp*isin(((ph+tick*freq)&0xffffffff)>>8)
    return base+(abs(v)//4096)*(1 if v>=0 else -1)

def query(link):
    link.send('>night.status');until=time.monotonic()+8;retry=time.monotonic()+.5
    while time.monotonic()<until:
        line=link.read()
        if line.startswith('@night '):
            state=json.loads(line[7:])
            if not all(type(state.get(k)) is int for k in ('tick','score','res','over','light','x','gait','stun','swing','meter','need','last_swing')):
                raise SmokeError('Invalid NIGHT status')
            if any(len(f)!=7 for f in state.get('flies',[])) or len(state['flies'])>40:raise SmokeError('Invalid NIGHT objects')
            return state
        if time.monotonic()>=retry:link.send('>night.status');retry=time.monotonic()+.5
    raise SmokeError('No NIGHT telemetry')

def drive(g,lead=6):
    """Swing when a visible firefly will sit inside the net arc a few frames from now (walking pace)."""
    if g['swing'] or g['stun']:return False
    nx=(g['x']>>8)+NET_DX+(294*lead>>8)
    for f in g['flies']:
        dx=((f[1]+f[6]*lead)>>8)-nx;dy=fly_y(f,g['tick']+lead)-NET_Y
        if dx*dx+dy*dy<=NET_R*NET_R:return True
    return False

def enter(link):
    state=link.status()
    if state['page']==0:link.key('ok');link.map()
    elif state['page']!=1:raise SmokeError('NIGHT entry expects cover or map')
    link.send('>adv.open=night');state=link.expect(7)
    if state['station']!=4 or state['phase']!=0:raise SmokeError('NIGHT title missing')
    link.key('down');deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        state=link.expect(7)
        if state['phase']==2:return state
        if state['phase']!=1:raise SmokeError('Unexpected NIGHT countdown')
        time.sleep(.15)
    raise SmokeError('NIGHT countdown stalled')

def play(link,target=5):
    """Walk (no held keys) and swing at reachable fireflies until the light runs out."""
    enter(link);start=time.monotonic();checked=start;last_score=-1;profile=[];phases=[]
    while time.monotonic()-start<240:
        p=query(link)
        if p['score']!=last_score:print(f'NIGHT score={p["score"]} light={p["res"]}',flush=True);last_score=p['score']
        if p['over']:
            latest=link.expect(7);phases.append(latest['phase'])
            if latest['phase']==5:
                if p['score']<target:raise SmokeError('NIGHT ended before target')
                return {'score':p['score'],'seconds':time.monotonic()-start,'end_phases':sorted(set(phases)),'profile':profile,
                        'whiffs':p['whiffs'],'caught':p['caught']}
            time.sleep(.1);continue
        if drive(p):tap(link,1)
        now=time.monotonic()
        if now-checked>=1:
            state=link.expect(7)
            if state['heap']<60000 or state['largest']<30000:raise SmokeError('Insufficient active-game heap')
            profile.append({'time':now-start,'frames':state['frames'],'draw_us':state['draw_us'],'bytes':state['bytes']})
            checked=now
        time.sleep(.02)
    raise SmokeError('NIGHT did not end')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True);parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--sha256',required=True);parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=10);args=parser.parse_args()
    if args.rounds<2:parser.error('--rounds must be >=2')
    verify_candidate(args.app,args.sha256,args.receipt,args.port)
    import serial
    folder=ROOT/'private/night-smoke';folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S');result={'candidate_sha256':args.sha256,'status':'INCOMPLETE'}
    with (folder/(stamp+'.log')).open('w',encoding='utf-8') as log:
        port=serial.Serial(port=None,baudrate=115200,timeout=.05);port.dtr=port.rts=False;port.port=args.port;port.open()
        port.set_buffer_size(rx_size=1024*1024,tx_size=16384);link=Link(BufferedPort(port),log)
        owned=False
        try:
            initial=link.status()
            if initial['test'] or initial['owner'] or initial['page'] not in (0,1):raise SmokeError('Start in normal cover/map with no real round active')
            owned=True;link.enable_test();before=(initial['best'],initial['seen'])
            for button in range(3):link.edge(button,True);link.edge(button,False)
            result['play']=play(link);link.key('double_up');link.map();samples=[]
            for count in range(args.rounds+1):
                enter(link)
                for _ in range(2):edge(link,0,True);edge(link,0,False)
                link.key('double_up');state=link.expect(7)
                if state['phase']!=2:raise SmokeError('UP taps/double UP left NIGHT V2 while playing')
                edge(link,0,True);time.sleep(.5);p=query(link);edge(link,0,False)
                if p['gait']!=2:raise SmokeError('Held UP did not run')
                edge(link,2,True);time.sleep(.4);p=query(link);edge(link,2,False)
                if p['gait']!=0:raise SmokeError('Held OK did not slow down')
                link.key('long_down');state=link.expect(7)
                if state['phase']!=3:raise SmokeError('Long middle DOWN did not pause')
                tick=query(link)['tick'];time.sleep(.4)
                if query(link)['tick']!=tick:raise SmokeError('Paused game advanced')
                link.key('down');state=link.expect(7)
                if state['phase']!=2:raise SmokeError('Middle DOWN did not resume')
                link.key('long_down');state=link.expect(7)
                if state['phase']!=3:raise SmokeError('Second pause failed')
                link.key('double_up');samples.append(link.map())
            result['memory']=analyse_memory(samples)
            restored=restore(link)
            if restored['test'] or (restored['best'],restored['seen'])!=before:raise SmokeError('Durable progress changed')
            result.update(status='PASS: SERIAL NIGHT ONLY',rounds=args.rounds,warmup_rounds=1,
                          normal_mode_restored=True,durable_progress_unchanged=True,
                          physical_checks='User feel (swing timing, darkness readability, frame rate), sound and sleep/wake still required')
        except Exception as error:
            result.update(status='FAIL',error=str(error))
            # Only restore state when this tool actually acquired test ownership.
            if owned:
                try:result['normal_mode_restored']=restore(link)['test']==0
                except Exception as cleanup:result['normal_mode_restored']=False;result['cleanup_error']=str(cleanup)
        finally:port.close()
    (folder/(stamp+'.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
    public={k:v for k,v in result.items() if k!='play'};public['play']={k:v for k,v in result.get('play',{}).items() if k!='profile'}
    print(json.dumps(public,indent=2));return 0 if result['status'].startswith('PASS') else 1

if __name__=='__main__':raise SystemExit(main())
