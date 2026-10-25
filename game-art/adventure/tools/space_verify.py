"""Run production C packing verification and exact neutral/attachment checks."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import numpy as np
from PIL import Image
from space_rig import ART,write_json

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from build_adventure_assets import build
from space_flag_review import verify_flag


def verify(check_c=False):
    manifest=json.loads((ART/'space-manifest.json').read_text('utf-8'));entries={(e['skin'],e['name']):e for e in manifest['animations']};checks=[]
    def same(a,ai,b,bi,fields=('frames','runtime_frames')):
        for field in fields:
            x=np.array(Image.open(ART/entries[a][field][ai]));y=np.array(Image.open(ART/entries[b][field][bi]))
            if not np.array_equal(x,y):raise ValueError(f'SPACE discontinuity: {a}/{ai} -> {b}/{bi} {field}')
        checks.append({'from':[a[0],a[1],ai],'to':[b[0],b[1],bi],'pixel_equal_fields':list(fields)})
    for skin in ('space_a','space_b'):
        idle=(skin,'cabin_idle');same(idle,0,(skin,'jet'),0)
        same((skin,'settlement_cheer'),0,(skin,'settlement_cheer'),-1)
        same(idle,0,(skin,'settlement_cheer'),0,('frames',))
    for name in ('land','hard_land','plant_flag'):
        same(('space_a','cabin_idle'),0,('space_a',name),0)
        same(('space_a',name),-1,('space_a','cabin_idle'),0)
    flag=entries[('space_a','plant_flag')]['attachments']['flag'];anchor=entries[('space_a','plant_flag')]['runtime_anchor']
    if flag[0]['visible'] or any(a['top_left']!=flag[-1]['top_left'] for a in flag[5:]):raise ValueError('Flag stored/planted lifecycle inconsistent')
    if flag[-1]['top_left'][1]+28!=anchor[1]:raise ValueError('Planted flag does not touch the fixed world ground')
    checks.append({'flag_planted_base_equals_world_root':True,'planted_frames':[5,6,7],'persistent_prop_after_clip':True})
    flag_report=verify_flag(manifest)
    checks.append({'touchdown_before_release':True,'exact_source_glove_contact_frames':[x['frame'] for x in flag_report['glove_flag_contacts']],
                   'max_flag_displacement_px':flag_report['after']['max_flag_displacement_px']})
    # Glass source layers have no nonbinary alpha or filled interior pixel.
    for skin in ('space_a','space_b'):
        for view in ('front','left','right'):
            for layer in ('helmet_back','helmet_front'):
                im=np.array(Image.open(ART/f'rig/space/{skin}/{view}/{layer}.png'))
                head=np.array(Image.open(ART/f'rig/space/{skin}/{view}/head.png'))
                if set(np.unique(im[:,:,3]))-{0,255} or np.count_nonzero(im[:,:,3])>2000:
                    raise ValueError('Glass is not a sparse binary equipment outline')
                if np.any((im[:,:,3]>0)&(head[:,:,3]>=128)):
                    raise ValueError('Glass outline covers immutable head source pixels')
    with tempfile.TemporaryDirectory(prefix='nabo-space-c-') as tmp:report=build(ART,Path(tmp)/'generated',['space'],check_c)
    write_json(ART/'preview/space/packing-qa.json',report)
    write_json(ART/'preview/space/continuity.json',{'checks':checks,'notes':[
        'Jet is periodic; finish at phase0 before switching to neutral, not an arbitrary loop frame.',
        'Landing/hard landing/plant flag body first and last frames equal idle0 at formal and runtime size.',
        'Flag is an explicit prop attachment; it remains planted in world space after the body returns to idle.',
        'Cabin front frame deliberately occludes lower crew legs; it is not a second resize or head mask.']})
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-c',action='store_true');a=p.parse_args();r=verify(a.verify_c)
    print(json.dumps({'production_c':r['production_c'],'groups':r['groups']},indent=2))
