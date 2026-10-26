#!/usr/bin/env python3
"""Guarded SKI/SKY/SPACE lifecycle checks through real input events.

This checks natural round endings, controls and allocations, not expert scoring
or physical button feel. Test mode is acknowledged before any game input.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time
from smoke_adventure import Link,SmokeError,verify_candidate,analyse_memory
from smoke_post import BufferedPort,restore,edge,tap

ROOT=Path(__file__).resolve().parents[1]
STATIONS={'ski':6,'sky':7,'space':8}

def short_pair(link,button,event):
    for _ in range(2):tap(link,button)
    link.key(event)

def enter(link,name):
    s=link.status()
    if s['page']==0:link.key('ok');link.map()
    elif s['page']!=1:raise SmokeError('Entry requires map or cover')
    link.send('>adv.open='+name);s=link.expect(7)
    if s['station']!=STATIONS[name] or s['phase']!=0:raise SmokeError('Wrong game title')
    link.key('ok');deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        s=link.expect(7)
        if s['phase']==2:return s
        if s['phase']!=1:raise SmokeError('Unexpected countdown phase')
        time.sleep(.15)
    raise SmokeError('Countdown stalled')

def controls(link,name):
    start=enter(link,name)
    if name in ('ski','space'):
        for _ in range(2):
            edge(link,0,True);time.sleep(.25);edge(link,0,False)
        # A movement hold followed by one short tap must not satisfy return.
        tap(link,0);link.key('double_up')
        if link.expect(7)['phase']!=2:raise SmokeError('Held movement counted as return tap')
        edge(link,0,True);time.sleep(.8);link.key('long_up');edge(link,0,False)
        if link.expect(7)['phase']!=2:raise SmokeError('Moving UP paused or exited')
    if name=='space':
        edge(link,1,True);time.sleep(.25);edge(link,1,False)
        tap(link,1);link.key('double_down')
        if link.expect(7)['phase']!=2:raise SmokeError('Side thrust counted as pause tap')
        tap(link,1);link.key('double_down')
    else:link.key('long_ok' if name=='ski' else 'long_up')
    paused=link.expect(7)
    if paused['phase']!=3:raise SmokeError('Pause gesture failed')
    time.sleep(.45);frozen=link.expect(7)
    if (frozen['res'],frozen['score'])!=(paused['res'],paused['score']):raise SmokeError('Paused resources/score advanced')
    link.key('ok')
    if link.expect(7)['phase']!=2:raise SmokeError('OK did not resume')
    # Exercise the game's primary raw action, then release before returning.
    edge(link,2,True);time.sleep(.35);edge(link,2,False)
    if link.expect(7)['phase']!=2:raise SmokeError('Primary action left play')
    short_pair(link,0,'double_up')
    return {'initial_heap':start['heap'],'map':link.map()}

def natural_ending(link,name):
    start=enter(link,name);at=time.monotonic();last=start;phases={2};profile=[]
    before_at=time.monotonic();before=link.expect(7);before_end=time.monotonic()
    time.sleep(3)
    after_at=time.monotonic();after=link.expect(7);after_end=time.monotonic()
    if before['phase']!=2 or after['phase']!=2:raise SmokeError('Round ended during initial quiet frame sample')
    duration=(after_at+after_end-before_at-before_end)/2
    quiet={'seconds':duration,'frames':after['frames']-before['frames'],
           'fps':(after['frames']-before['frames'])/duration,
           'scope':'one initial idle 3-second window with only two status snapshots; not worst-case performance'}
    # Deliberately no fabricated state or score: miss gates, descend to trees,
    # or fall onto the lunar surface until the real resource rules end play.
    while time.monotonic()-at<150:
        s=link.expect(7);phases.add(s['phase'])
        if s['phase']==5:
            if 4 not in phases:raise SmokeError('End animation was not observed')
            result={'score':s['score'],'seconds':time.monotonic()-at,'phases':sorted(phases),
                    'profile':profile,'start_resource':start['res'],'end_resource':s['res'],'quiet_sample':quiet}
            short_pair(link,0,'double_up');link.map();return result
        if s['phase'] not in (2,4):raise SmokeError('Unexpected natural round phase')
        if s['heap']<60000 or s['largest']<30000:raise SmokeError('Insufficient active-game memory')
        profile.append({'elapsed':time.monotonic()-at,**{k:s[k] for k in ('frames','draw_us','bytes','res','score')}})
        last=s;time.sleep(.2)
    raise SmokeError(f'{name} did not naturally end; last phase {last["phase"]}')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',required=True);ap.add_argument('--app',type=Path,required=True)
    ap.add_argument('--sha256',required=True);ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('--rounds',type=int,default=10)
    args=ap.parse_args()
    if args.rounds<2:ap.error('--rounds must be >=2')
    verify_candidate(args.app,args.sha256,args.receipt,args.port)
    import serial
    folder=ROOT/'private/late-games-smoke';folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S');result={'candidate_sha256':args.sha256,'status':'INCOMPLETE','games':{}}
    with (folder/(stamp+'.log')).open('w',encoding='utf-8') as log:
        p=serial.Serial(port=None,baudrate=115200,timeout=.05);p.dtr=p.rts=False;p.port=args.port;p.open()
        p.set_buffer_size(rx_size=1024*1024,tx_size=16384);link=Link(BufferedPort(p),log);owned=False
        try:
            initial=link.status()
            if initial['test'] or initial['owner'] or initial['page'] not in (0,1):raise SmokeError('Start in normal cover/map, no real game')
            before=(initial['best'],initial['seen']);owned=True;link.enable_test()
            for button in range(3):edge(link,button,True);edge(link,button,False)
            for name in STATIONS:
                print('START '+name,flush=True);samples=[]
                for n in range(args.rounds+1):
                    check=controls(link,name);samples.append(check['map'])
                    print(f'{name} cycle {n+1}/{args.rounds+1}',flush=True)
                game={'memory':analyse_memory(samples),'rounds':args.rounds,'warmup_rounds':1,
                      'natural_round':natural_ending(link,name)}
                result['games'][name]=game;print('PASS '+name,flush=True)
            normal=restore(link)
            if (normal['best'],normal['seen'])!=before:raise SmokeError('Durable progress changed')
            result.update(status='PASS: SERIAL LIFECYCLE AND NATURAL ENDINGS ONLY',normal_mode_restored=True,
                          physical_checks='Actual controls, readability, costume, scoring feel, sleep/wake and audio are not certified')
        except Exception as error:
            result.update(status='FAIL',error=str(error))
            if owned:
                try:result['normal_mode_restored']=restore(link)['test']==0
                except Exception as cleanup:result.update(normal_mode_restored=False,cleanup_error=str(cleanup))
        finally:p.close()
    path=folder/(stamp+'.json');path.write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print(json.dumps({'status':result['status'],'error':result.get('error'),'report':str(path)},indent=2))
    return 0 if result['status'].startswith('PASS') else 1

if __name__=='__main__':raise SystemExit(main())
