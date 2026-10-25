#!/usr/bin/env python3
"""Exercise NIGHT through guarded real inputs; never writes fabricated progress."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from smoke_adventure import Link,SmokeError,verify_candidate,analyse_memory
from smoke_post import BufferedPort,restore,tap,edge

ROOT=Path(__file__).resolve().parents[1]

def query(link):
    link.send('>night.status');until=time.monotonic()+8;retry=time.monotonic()+.5
    while time.monotonic()<until:
        line=link.read()
        if line.startswith('@night '):
            state=json.loads(line[7:])
            if not all(type(state.get(k)) is int for k in ('tick','score','res','over','lane','x','move','cooldown','target','interval')):
                raise SmokeError('Invalid NIGHT status')
            if len(state.get('bugs',[]))!=8 or any(len(b)!=6 for b in state['bugs']):raise SmokeError('Invalid NIGHT objects')
            return state
        if time.monotonic()>=retry:link.send('>night.status');retry=time.monotonic()+.5
    raise SmokeError('No NIGHT telemetry')

def drive(g):
    """Use the public HUD predicate and visible objects, as in night_policy.js."""
    target=g['target']
    if target>=0 and g['bugs'][target][0]==1 and g['cooldown']<=1:return 1
    best=None
    for bug in g['bugs']:
        if bug[0]!=1:continue
        lane=bug[3];travel=(abs((54,160,266)[lane]-g['x'])+4)//5+6
        if 108-bug[5]<travel+2:continue
        cost=108-bug[5]+travel*.2
        if best is None or cost<best[0]:best=(cost,lane)
    return (2 if (54,160,266)[best[1]]<g['x'] else 0) if best and abs((54,160,266)[best[1]]-g['x'])>8 else None

def quick_return(link):
    # Two genuinely short presses; movement presses must never satisfy this.
    for _ in range(2):edge(link,0,True);edge(link,0,False)
    link.key('double_up')

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

def play(link,target=15):
    first=enter(link);start=time.monotonic();checked=start;last_score=-1;profile=[];phases=[];held=None
    while time.monotonic()-start<220:
        p=query(link)
        if p['score']!=last_score:
            print(f'NIGHT score={p["score"]} spirit={p["res"]}',flush=True);last_score=p['score']
        if p['over']:
            if held is not None:edge(link,held,False);held=None
            latest=link.expect(7);phases.append(latest['phase'])
            if latest['phase']==5:
                if p['score']<target:raise SmokeError('NIGHT ended before target')
                return {'score':p['score'],'seconds':time.monotonic()-start,'end_phases':sorted(set(phases)),
                        'profile':profile,'misses':p['misses']}
            time.sleep(.1);continue
        button=drive(p) if p['score']<target else None
        desired=button if button in (0,2) else None
        if held!=desired:
            if held is not None:edge(link,held,False)
            held=desired
            if held is not None:edge(link,held,True)
        if button==1:tap(link,1)
        now=time.monotonic()
        if now-checked>=1:
            state=link.expect(7)
            if state['heap']<60000 or state['largest']<30000:raise SmokeError('Insufficient active-game heap')
            profile.append({'time':now-start,'frames':state['frames'],'draw_us':state['draw_us'],'bytes':state['bytes']})
            checked=now
        time.sleep(.04)
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
                link.key('up');state=link.expect(7)
                if state['phase']!=2:raise SmokeError('Single UP left play')
                edge(link,2,True);time.sleep(.55);edge(link,2,False);p=query(link)
                if p['lane']!=0 or p['x']!=54:raise SmokeError('Physical left OK did not finish left slide')
                for _ in range(2):edge(link,0,True);time.sleep(.22);edge(link,0,False);time.sleep(.04)
                link.key('double_up');state=link.expect(7);p=query(link)
                if state['phase']!=2 or p['x']<=54:raise SmokeError('Repeated held-right movement caused an exit')
                edge(link,0,True);time.sleep(.85);link.key('long_up');edge(link,0,False);state=link.expect(7)
                if state['phase']!=2 or query(link)['x']!=266:raise SmokeError('Held right stopped or paused before the edge')
                link.key('long_down');state=link.expect(7)
                if state['phase']!=3:raise SmokeError('Long middle DOWN did not pause')
                tick=query(link)['tick'];time.sleep(.4)
                if query(link)['tick']!=tick:raise SmokeError('Paused game advanced')
                link.key('long_up');state=link.expect(7)
                if state['phase']!=3:raise SmokeError('Long UP left pause')
                link.key('down');state=link.expect(7)
                if state['phase']!=2:raise SmokeError('Middle DOWN did not resume')
                quick_return(link);samples.append(link.map())
            result['memory']=analyse_memory(samples)
            restored=restore(link)
            if restored['test'] or (restored['best'],restored['seen'])!=before:raise SmokeError('Durable progress changed')
            result.update(status='PASS: SERIAL NIGHT ONLY',rounds=args.rounds,warmup_rounds=1,
                          normal_mode_restored=True,durable_progress_unchanged=True,
                          physical_checks='User buttons, catch timing, costume, sound and sleep/wake still required')
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
