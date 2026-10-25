"""Validate production manifest, exact action endpoints and real C decoder."""
import argparse
from pathlib import Path
import sys
import tempfile
import numpy as np
from PIL import Image
from climb_rig import ART, write_json

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from build_adventure_assets import build


def verify(clips=None,check_c=False):
    import json
    manifest=json.loads((ART/'climb-manifest.json').read_text('utf-8'))
    assertions=[]
    lookup={(e['skin'],e['name']):e for e in manifest['animations']}
    def same(a,ai,b,bi):
        for field in ('frames','runtime_frames'):
            x=np.array(Image.open(ART/lookup[a][field][ai]));y=np.array(Image.open(ART/lookup[b][field][bi]))
            if not np.array_equal(x,y):raise ValueError(f'Endpoint does not match: {a}/{ai} -> {b}/{bi} ({field})')
        assertions.append({'from':[a[0],a[1],ai],'to':[b[0],b[1],bi],'formal_and_runtime_pixel_equal':True})
    for side in ('left','right'):
        idle=('climb_a','grip_idle_'+side);target='right' if side=='left' else 'left'
        same(idle,0,('climb_a','charge_'+side),0)
        same(('climb_a','charge_'+side),-1,('climb_a','jump_'+side),0)
        for name in ('jump','slide'):
            same(('climb_a',name+'_'+side),-1,idle,0)
        same(idle,0,('climb_a','slide_'+side),0)
        same(idle,0,('climb_a','switch_grab_'+side),0)
        same(('climb_a','switch_grab_'+side),-1,('climb_a','grip_idle_'+target),0)
        same(idle,0,('climb_a','summit_cheer_'+side),0)
    for skin in ('climb_a','climb_b'):same((skin,'settlement_cheer'),0,(skin,'settlement_cheer'),-1)
    with tempfile.TemporaryDirectory(prefix='nabo-climb-c-') as temporary:
        report=build(ART,Path(temporary)/'generated',['climb'],check_c)
    write_json(ART/'preview/climb/packing-qa.json',report)
    write_json(ART/'preview/climb/continuity.json',{'checks':assertions,'notes':[
        'Summit cheer ends at neutral in its wall-facing view; renderer should hold final pose or explicitly turn before front settlement.',
        'Switch head uses separately supplied left/front/right source views, never a mirror.',
        'Game engine applies world motion, collision displacement, and scrolling; these clips contain limb poses only.']})
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-c',action='store_true');args=p.parse_args()
    r=verify(check_c=args.verify_c);print(r['production_c']);print(r['groups'])
