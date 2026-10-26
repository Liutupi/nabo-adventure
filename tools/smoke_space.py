#!/usr/bin/env python3
"""Play SPACE V2 through read-only telemetry and real button edges, with guarded test ownership.

Uses the approved screen-information JS player. A failed landing remains a failed landing;
the report distinguishes it from a successful Moon journey. No scores/settings are injected.
"""
import argparse,json,subprocess,time
from datetime import datetime
from pathlib import Path
from smoke_adventure import Link,SmokeError,verify_candidate
from smoke_post import BufferedPort,restore,edge,tap
from smoke_late_games import enter
ROOT=Path(__file__).resolve().parents[1]
def query(link):
 link.send('>space.status');deadline=time.monotonic()+8;retry=time.monotonic()+.5
 while time.monotonic()<deadline:
  line=link.read()
  if line.startswith('@space '):
   g=json.loads(line[7:])
   if not all(type(g.get(k)) is int for k in ('tick','score','res','mode','modeT','alt','fuel','hull','x','vx')):raise SmokeError('Invalid SPACE telemetry')
   if len(g.get('objs',[]))>24 or any(len(o)!=6 for o in g.get('objs',[])):raise SmokeError('Invalid SPACE object count')
   return g
  if time.monotonic()>retry:link.send('>space.status');retry=time.monotonic()+.5
 raise SmokeError('Missing SPACE telemetry')
def play(link,node):
 enter(link,'space');start=time.monotonic();held={0:False,2:False};modes=set();zones=set();last={};profile=[];at=start
 player=subprocess.Popen([node,str(ROOT/'tools/space_serial_policy.js')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
 try:
  while time.monotonic()-start<180:
   g=query(link);last=g;modes.add(g['mode']);zones.add(1 if g['alt']>>8<4000 else 2 if g['alt']>>8<8000 else 3 if g['alt']>>8<14000 else 4)
   if g['over']:
    for button in held:
     if held[button]:edge(link,button,False);held[button]=False
    s=link.expect(7)
    if s['phase']==5:return {'seconds':time.monotonic()-start,'modes':sorted(modes),'zones':sorted(zones),'score':g['score'],'successful_landing':bool(g['win']),
                           'landings':g['landings'],'profile':profile,'terminal':g}
    time.sleep(.1);continue
   player.stdin.write(json.dumps(g)+'\n');player.stdin.flush();line=player.stdout.readline()
   if not line:raise SmokeError('Screen-information player stopped')
   action=json.loads(line)
   for button,key in ((2,'ok_held'),(0,'up_held')):
    want=bool(action.get(key))
    if want!=held[button]:edge(link,button,want);held[button]=want
   if action.get('down_down'):tap(link,1)
   if time.monotonic()-at>=1:
    s=link.expect(7)
    if s['heap']<60000 or s['largest']<30000:raise SmokeError('Insufficient active SPACE heap')
    profile.append({k:s[k] for k in ('heap','largest','frames','draw_us','score')});at=time.monotonic()
   time.sleep(.015)
  raise SmokeError('SPACE round did not end; last mode '+str(last.get('mode')))
 finally:
  for button,value in held.items():
   if value:edge(link,button,False)
  player.terminate();player.communicate(timeout=5)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--port',required=True);ap.add_argument('--app',type=Path,required=True)
 ap.add_argument('--sha256',required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--node',default='node');a=ap.parse_args()
 verify_candidate(a.app,a.sha256,a.receipt,a.port)
 import serial
 folder=ROOT/'private/space-smoke';folder.mkdir(parents=True,exist_ok=True);stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
 result={'candidate_sha256':a.sha256,'status':'INCOMPLETE'};owned=False
 with (folder/(stamp+'.log')).open('w',encoding='utf-8') as log:
  p=serial.Serial(port=None,baudrate=115200,timeout=.05);p.dtr=p.rts=False;p.port=a.port;p.open();p.set_buffer_size(rx_size=1024*1024,tx_size=16384);link=Link(BufferedPort(p),log)
  try:
   initial=link.status()
   if initial['test'] or initial['owner'] or initial['page'] not in (0,1):raise SmokeError('Normal cover/map required; no real round')
   before=(initial['best'],initial['seen']);owned=True;link.enable_test()
   for b in range(3):edge(link,b,True);edge(link,b,False)
   # Verify actual model-clock freezing; IGNITE has no fuel drain, so resource-only checks are insufficient.
   enter(link,'space');link.key('long_down')
   if link.expect(7)['phase']!=3:raise SmokeError('SPACE did not pause')
   tick=query(link)['tick'];time.sleep(.5)
   if query(link)['tick']!=tick:raise SmokeError('Paused SPACE model advanced')
   link.key('double_up');link.map();result['play']=play(link,a.node)
   link.key('double_up');link.map();normal=restore(link)
   if (normal['best'],normal['seen'])!=before:raise SmokeError('Real progress changed')
   result.update(status='PASS: SERIAL ROUND AND FREEZE ONLY',normal_mode_restored=True,durable_progress_unchanged=True,
                 physical_checks='User controls, art/readability, sound and sleep/wake remain unverified')
  except Exception as e:
   result.update(status='FAIL',error=str(e))
   if owned:
    try:result['normal_mode_restored']=restore(link)['test']==0
    except Exception as cleanup:result['cleanup_error']=str(cleanup)
  finally:p.close()
 (folder/(stamp+'.json')).write_text(json.dumps(result,indent=2)+'\n','utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='play'}|{'play':{k:v for k,v in result.get('play',{}).items() if k not in ('profile','terminal')}},indent=2))
 return 0 if result['status'].startswith('PASS') else 1
if __name__=='__main__':raise SystemExit(main())
