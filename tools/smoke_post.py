#!/usr/bin/env python3
"""Play POST through real serial buttons in test mode, then restore durable state."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import time

from smoke_adventure import Link,SmokeError,verify_candidate,analyse_memory

ROOT=Path(__file__).resolve().parents[1]

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
            if not all(type(p.get(k)) is int for k in ('v2','tick','score','res','over','speed','dist','bags','delivered','perfects','cranes','reds','derails','zone')):
                raise SmokeError('Invalid POST status fields')
            if p['v2']!=1 or len(p.get('events',[]))!=16 or any(len(e)!=6 for e in p['events']):
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

def main():
    # The shared suite binds the candidate and guards/cleans up test mode once.
    import sys
    from smoke_late_games import main as suite
    return suite([*sys.argv[1:],"--game","post"])

if __name__=='__main__':raise SystemExit(main())
