"""Current travel delivery entry point: source rig, six actions, facing turns and runtime QA."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from build_travel_rig import build,RIG,ART
from rig_config import ANIMATION_SPECS
from rig_render import render_frame
from rig_preview import font
from travel_transitions import turns,continuity
from travel_export import export
from welcome_timing_preview import build as welcome_preview
from travel_quality import write as motion_quality


def packing(entries):
    path=ART.parents[2]/'tools/generate_adv_sprites.py'
    spec=importlib.util.spec_from_file_location('travel_packer',path)
    packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
    result={}
    for entry in entries:
        frames=[Image.open(ART/p).convert('RGBA') for p in entry['runtime_frames']]
        palette,indexed=packer.index_frames(frames)
        w,h=frames[0].size;asset=packer.pack(w,h,indexed)
        assert all(packer.decode(asset,i)==frame for i,frame in enumerate(indexed))
        tables=len(palette)*2+len(asset['keys'])*2+len(asset['rows'])*4
        size=len(asset['data'])+tables+32
        result[entry['name']]={'rgb565_palette':len(palette),'rle_data_bytes':len(asset['data']),
            'table_bytes':tables,'c3_descriptor_bytes':32,'total_unaligned_bytes':size,
            'verified_frames':len(frames),'source':'actual repository generate_adv_sprites.index_frames/pack/decode',
            'comparison':'exact after shared RGB565 quantization, not C decoder validation'}
        if entry['name']=='welcome':
            assert size<=100*1024,('welcome exceeds 100KiB',size)
            entry['runtime_rle_budget']=result[entry['name']]
    (ART/'preview/travel/packing-estimates.json').write_text(json.dumps(result,indent=2)+'\n','utf-8')
    return result


def overview(entries):
    rows=(len(entries)+1)//2
    sheet=Image.new('RGB',(1200,rows*285),'#f4ecdc');d=ImageDraw.Draw(sheet)
    for row,entry in enumerate(entries):
        x=(row%2)*600;y=(row//2)*285
        d.text((x+8,y+5),f"{entry['name']} / {len(entry['frames'])}f / {entry['target_height_px']}px",fill='#182439',font=font(17))
        indices=sorted(set([0,len(entry['frames'])//3,2*len(entry['frames'])//3,len(entry['frames'])-1]))
        for column,index in enumerate(indices):
            frame=Image.open(ART/entry['frames'][index]).convert('RGBA')
            frame.thumbnail((145,235),Image.Resampling.LANCZOS)
            sheet.paste(frame,(x+column*150,y+34),frame)
    sheet.save(ART/'preview/travel/rig-overview.png')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skin',choices=['travel'],default='travel')
    parser.add_argument('--anim',default='all',help='All clips are rebuilt together to preserve locomotion scale/palette continuity')
    parser.add_argument('--facing',choices=['front','left','right'])
    parser.add_argument('--scale',type=float,default=1)
    parser.parse_args()
    rig=build();clips={}
    for name,spec in ANIMATION_SPECS.items():
        frames=[];reports=[]
        for index in range(spec['count']):
            frame,report=render_frame(rig,RIG,spec['facing'],name,index)
            frames.append(frame);reports.append(report)
        clips[name]={**spec,'frames':frames,'reports':reports}
    clips.update(turns(rig,RIG,clips))
    entries=export(clips,rig)
    qa=continuity(ART,clips,entries)
    (ART/'preview/travel/continuity-qa.json').write_text(json.dumps(qa,indent=2)+'\n','utf-8')
    estimates=packing(entries)
    manifest=json.loads((ART/'manifest.json').read_text('utf-8'))
    for entry in manifest['animations']:
        if entry['name']=='welcome':entry['runtime_rle_budget']=estimates['welcome']
    (ART/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    overview(entries)
    welcome_preview(entries)
    motion_quality(entries,qa)
    print(json.dumps({'animations':len(entries),'formal_frames':sum(len(e['frames']) for e in entries),
        'runtime_contracts':[{k:e[k] for k in ['name','runtime_canvas','runtime_anchor','target_height_px']} for e in entries],
        'welcome_rle_bytes':estimates['welcome']['total_unaligned_bytes'],
        'continuity_max_centroid_jump':{s:v['max_boundary_centroid_delta_px'] for s,v in qa.items()}},indent=2))


if __name__=='__main__':main()
