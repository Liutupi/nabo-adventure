#!/usr/bin/env python3
"""Play POST through real serial buttons in test mode, then restore durable state."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from smoke_adventure import Link,SmokeError,verify_candidate,analyse_memory

ROOT=Path(__file__).resolve().parents[1]
MAIL_X=156*60
MAIL_WINDOW=32*60

class BufferedPort:
    def __init__(self,port):self.port=port;self.pending=b''
    def write(self,data):return self.port.write(data)
    def flush(self):return self.port.flush()
    def readline(self):
        until=time.monotonic()+.15
        while b'\n' not in self.pending and time.monotonic()<until:
            self.pending+=self.port.read(max(1,self.port.in_waiting))
        if b'\n' not in self.pending:return b''
        line,self.pending=self.pending.split(b'\n',1);return line+b'\n'

def query(link):
    link.send('>post.status');until=time.monotonic()+8;retry=time.monotonic()+.5
    while time.monotonic()<until:
        line=link.read()
        if line.startswith('@post '):
            p=json.loads(line[6:])
            if not all(type(p.get(k)) is int for k in ('tick','score','res','lane','choice','remaining','lap','speed','hold','over')):
                raise SmokeError('Invalid POST status fields')
            if len(p['mail'])!=5 or len(p['events'])!=12 or any(len(e)!=6 for e in p['events']):
                raise SmokeError('Invalid POST arrays')
            return p
        if time.monotonic()>=retry:
            link.send('>post.status');retry=time.monotonic()+.5
    raise SmokeError('No POST telemetry')

def restore(link):
    link.armed=False;last=None
    for _ in range(3):
        link.send('>adv.test=0')
        try:
            last=link.status()
            if last['test']==0:return last
        except (SmokeError,OSError):pass
    raise SmokeError('Normal mode restoration was not acknowledged')

def edge(link,button,down):
    if not link.armed:raise SmokeError('No confirmed test guard')
    link.send(f'>adv.edge={button},{int(down)}')

def tap(link,button=2):edge(link,button,True);edge(link,button,False)

def enter(link):
    state=link.status()
    if state['page']==0:link.key('ok');link.map()
    elif state['page']!=1:raise SmokeError('POST entry expects cover or map')
    link.send('>adv.open=post');link.expect(7)
    link.key('ok')
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        state=link.status()
        if state['phase']==2:return state
        if state['phase']!=1:raise SmokeError('Unexpected POST countdown phase')
        time.sleep(.15)
    raise SmokeError('POST countdown stalled')

def play(link,target=5):
    first=enter(link);start=time.monotonic();checked=start;profile=[];held=False;last_score=-1
    phases=[];latest=first
    while time.monotonic()-start<180:
        p=query(link)
        if p['score']!=last_score:
            print(f'POST score={p["score"]} steam={p["res"]} lap={p["lap"]}',flush=True);last_score=p['score']
        if p['over']:
            if held:edge(link,2,False);held=False
            latest=link.status();phases.append(latest['phase'])
            if latest['phase']==5:
                if p['score']<target:raise SmokeError('POST ended before reaching the target')
                return {'score':p['score'],'laps':p['lap'],'seconds':time.monotonic()-start,'profile':profile,'end_phases':phases}
            time.sleep(.1);continue
        stations=sorted((e for e in p['events'] if e[0]==2 and not e[4] and e[1]>=MAIL_X-MAIL_WINDOW),key=lambda e:e[1])
        station=stations[0] if stations else None
        fork=any(e[0]==1 and not e[4] for e in p['events'])
        if fork and station and p['choice']!=station[2]:tap(link,station[2])
        animal=any(e[0]==4 and not e[4] and e[2]==p['lane'] and 6600<e[1]<6600+p['speed']*90 for e in p['events'])
        if p['score']>=target:
            if held:edge(link,2,False);held=False
            if not station or abs(station[1]-MAIL_X)>MAIL_WINDOW:tap(link)
        elif animal:
            if not held:edge(link,2,True);held=True
        else:
            if held:edge(link,2,False);held=False
            elif station and abs(p['y']-(212 if station[2] else 132))<=20 and station[3]==p['mail'][0] and abs(station[1]-MAIL_X)<900:tap(link)
        now=time.monotonic()
        if now-checked>=1:
            latest=link.expect(7)
            profile.append({'time':now-start,'frames':latest.get('frames',0),'draw_us':latest.get('draw_us',0),'bytes':latest['bytes']})
            checked=now
        time.sleep(.04)
    raise SmokeError('POST play timed out')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True);parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--sha256',required=True);parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=10);args=parser.parse_args()
    if args.rounds<2:parser.error('--rounds must be >=2')
    verify_candidate(args.app,args.sha256,args.receipt,args.port)
    import serial
    folder=ROOT/'private/post-smoke';folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S');result={'candidate_sha256':args.sha256,'status':'INCOMPLETE'}
    with (folder/(stamp+'.log')).open('w',encoding='utf-8') as log:
        port=serial.Serial(port=None,baudrate=115200,timeout=.05);port.dtr=port.rts=False;port.port=args.port;port.open()
        port.set_buffer_size(rx_size=1024*1024,tx_size=16384);link=Link(BufferedPort(port),log)
        try:
            initial=link.enable_test();before=(initial['best'],initial['seen'])
            if initial['page']==0:link.key('ok');link.map()
            if initial['page']!=0 and initial['page']!=1:raise SmokeError('Reset to cover/map first')
            result['play']=play(link)
            link.key('long_up');link.map();samples=[]
            for count in range(args.rounds+1):
                enter(link)
                # Exercise hold/release and pause/back in a running session.
                edge(link,2,True);time.sleep(.7)
                if not query(link)['whistle']:raise SmokeError('POST held OK did not activate the horn')
                edge(link,2,False)
                link.key('long_up');state=link.expect(7)
                if state['phase']!=3:raise SmokeError('POST did not pause')
                link.key('long_up');state=link.map();samples.append(state)
            result['memory']=analyse_memory(samples)
            after=link.status()
            if (after['best'],after['seen'])!=before:raise SmokeError('Test changed bests/stamps')
            restored=restore(link)
            if restored['test']!=0 or (restored['best'],restored['seen'])!=before:
                raise SmokeError('Normal state did not restore')
            result.update(status='PASS: SERIAL POST ONLY',rounds=args.rounds,warmup_rounds=1,
                          durable_progress_unchanged=True,normal_mode_restored=True,
                          physical_checks='Still requires user buttons, complete play, speaker and sleep/wake')
        except Exception as error:
            result.update(status='FAIL',error=str(error))
            try:
                restored=restore(link)
                result['normal_mode_restored']=restored['test']==0
            except Exception as cleanup:
                result['normal_mode_restored']=False;result['cleanup_error']=str(cleanup)
        finally:port.close()
    (folder/(stamp+'.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
    public={k:v for k,v in result.items() if k!='play'}
    public['play']={k:v for k,v in result.get('play',{}).items() if k!='profile'}
    print(json.dumps(public,indent=2));return 0 if result['status'].startswith('PASS') else 1

if __name__=='__main__':raise SystemExit(main())
