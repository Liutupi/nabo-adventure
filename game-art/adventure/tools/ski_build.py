#!/usr/bin/env python3
"""Build two rear-view SKI skins, gear, shared snow references and native runtime frames."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from post_rig import sha
from post_build import text,union,rgba_colors,gif
from rig_preview import quantize as fixed_top_quantize
from ski_palette import quantize,head_masks
from ski_config import ART,ROOT,GAME,RIG,PREVIEW,ANIMS,SPECS
from ski_rig import build
from ski_render import render
from ski_props import build_props


def contact(entry,frames,bg):
 count=len(frames);w,h=frames[0].size;cw=max(160,w*3+16);ch=h*4+62
 board=Image.new('RGB',(cw*count,ch*2));d=ImageDraw.Draw(board)
 for row,color in enumerate((bg,(24,36,57))):
  d.rectangle((0,row*ch,board.width,(row+1)*ch),fill=tuple(color))
  text(d,(8,row*ch+3),entry['skin']+' / '+entry['name']+f" / body {entry['target_height_px']}px / gear envelope {w}x{h}",13,'#203849' if row==0 else '#fff0cd')
  for i,frame in enumerate(frames):
   x,y=i*cw,row*ch;board.paste(frame,(x+(cw-w)//2,y+29),frame)
   big=frame.resize((w*3,h*3),Image.Resampling.NEAREST);board.paste(big,(x+(cw-big.width)//2,y+h+39),big)
   text(d,(x+7,y+ch-18),str(i),12,'#203849' if row==0 else '#fff0cd')
 path=PREVIEW/(entry['skin']+'-'+entry['name']+'-contact.png');board.save(path)
 for label,color in (('snow',bg),('dark',(24,36,57))):gif(PREVIEW/(entry['skin']+'-'+entry['name']+'-'+label+'.gif'),frames,entry['loop'],tuple(color))
 return path.relative_to(ART).as_posix()


def props_preview(assets,bg):
 cw,ch=240,230;board=Image.new('RGB',(960,ch*((len(assets)+3)//4)),tuple(bg));d=ImageDraw.Draw(board)
 for i,a in enumerate(assets):
  x,y=i%4*cw,i//4*ch;im=Image.open(ART/a['path']).convert('RGBA')
  board.paste(im,(x+8,y+33),im);big=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  board.paste(big,(x+cw-big.width-7,y+35),big);text(d,(x+7,y+5),a['id'].split('/')[-1],13)
  text(d,(x+7,y+ch-20),str(a['size'])+(' shared frozen source' if a.get('shared_source') else ' native + 2x'),12)
  single=Image.new('RGB',im.size,tuple(bg));single.paste(im,(0,0),im);path=PREVIEW/'props'/(a['id'].split('/')[-1]+'.png')
  path.parent.mkdir(exist_ok=True);single.save(path);a['preview']=path.relative_to(ART).as_posix()
 board.save(PREVIEW/'props-contact.png')


def context(entries,bg):
 board=Image.new('RGB',(1440,670),'#e7d5ad');d=ImageDraw.Draw(board)
 def asset(name):return Image.open(GAME/'props'/(name+'.png')).convert('RGBA')
 for col,skin in enumerate(('ski_a','ski_b')):
  e=next(x for x in entries if x['skin']==skin and x['name']=='straight');frames=[]
  for i,path in enumerate(e['runtime_frames']):
   screen=Image.new('RGBA',(240,320),tuple(bg))
   for x,y in ((8,35),(174,91),(3,220)):screen.alpha_composite(asset('pine-large'),(x,y))
   small=Image.open(ART/'map/tiles/ski/snow-pine.png').convert('RGBA')
   for x,y in ((156,16),(205,185)):screen.alpha_composite(small,(x,y))
   screen.alpha_composite(asset('gate-red'),(74,68));screen.alpha_composite(asset('gate-blue'),(135,229))
   drift=Image.open(ART/'map/tiles/mountain/snow-drift.png').convert('RGBA')
   for x,y in ((50,278),(189,141)):screen.alpha_composite(drift,(x,y))
   screen.alpha_composite(asset('hot-cocoa-cabin'),(7,113))
   actor=Image.open(ART/path).convert('RGBA');ax,ay=e['runtime_anchor'];screen.alpha_composite(actor,(119-ax,211-ay))
   frames.append(screen)
  frames[0].convert('RGB').save(PREVIEW/(skin+'-slope-native.png'));gif(PREVIEW/(skin+'-slope-loop.gif'),frames,True,tuple(bg),1)
  board.paste(frames[0],(col*720,30));board.paste(frames[0].resize((480,640),Image.Resampling.NEAREST),(col*720+240,30))
  text(d,(col*720+8,5),skin+' / 240x320 + 2x / host composition, not gameplay',13)
 board.save(PREVIEW/'slope-composition-contact.png')


def identity_comparison(rig):
 board=Image.new('RGB',(1024,300),'#e1ecf8');d=ImageDraw.Draw(board)
 original=Image.open(ART/'reference/nabo-idle-original.png').convert('RGBA')
 box=original.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox();cut=original.crop(box)
 cut=cut.resize((round(cut.width*208/cut.height),208),Image.Resampling.LANCZOS)
 ref=Image.new('RGBA',(256,256));ref.alpha_composite(cut,((256-cut.width)//2,16))
 travel=Image.open(ART/'rig/common/front/sampled-reference.png').convert('RGBA')
 frames=[ref,travel,render(rig,'ski_a','straight',0)[0],render(rig,'ski_b','straight',0)[0]]
 for i,(label,frame) in enumerate(zip(('original identity','approved travel source','ski_a rear body + common head','ski_b rear body + common head'),frames)):
  board.paste(frame,(i*256,31),frame);text(d,(i*256+5,6),label,12)
 board.save(PREVIEW/'identity-and-body-view.png')


def main():
 argparse.ArgumentParser(description=__doc__).parse_args();PREVIEW.mkdir(parents=True,exist_ok=True)
 shared=json.loads((ART/'shared-static-manifest.json').read_text('utf-8'));bg=shared['backgrounds']['ski']['preview_rgb']
 rig=build();assets=build_props();clips={}
 for a in assets:
  im=Image.open(ART/a['path']).convert('RGBA');data=np.asarray(im);alpha=sorted(np.unique(data[:,:,3]).tolist())
  a['qa']=dict(colors=rgba_colors([im]),alpha=alpha,bbox=im.getchannel('A').getbbox())
  assert a['qa']['colors']<=a['color_limit'] and alpha==[0,255]
 props_preview(assets,bg)
 for skin,names in ANIMS.items():
  for name in names:
   masters=[];reports=[]
   for i in range(SPECS[name]['count']):
    frame,report=render(rig,skin,name,i);masters.append(frame);reports.append(report)
    assert report['no_clipping'],(skin,name,i,'clipped')
    assert all(x['actual_boot_board_overlap_pixels']>0 for x in report['boot_board_contacts'].values()),(skin,name,i,'boot-board contact')
    assert all(x['actual_mitten_pole_overlap_pixels']>0 for x in report['mitten_pole_contacts'].values()),(skin,name,i,'hand-pole contact')
   clips[skin,name]=dict(masters=masters,reports=reports,spec=SPECS[name],head_masks=head_masks(rig,ART,reports))
 masters=[f for c in clips.values() for f in c['masters']]
 formal,fr=quantize(masters,[m for c in clips.values() for m in c['head_masks']]);offset=0
 for clip in clips.values():
  n=len(clip['masters']);clip['formal']=formal[offset:offset+n];offset+=n
 for target in (56,72):
  selected=[c for c in clips.values() if c['spec']['target']==target];frames=[f for c in selected for f in c['masters']]
  box=union(frames)
  if target==56:
   # Preserve the V1 horizontal/upper registration; only extend lower gear space.
   box=[min(box[0],10),min(box[1],2),max(box[2],243),max(box[3],255)]
  # 56px measures NABO's reference body, not the extra skis/poles/jump clearance.
  scale=56/208 if target==56 else 72/(box[3]-box[1]);size=[round((box[2]-box[0])*scale),round((box[3]-box[1])*scale)]
  sampled=[f.crop(box).resize(tuple(size),Image.Resampling.LANCZOS) for f in frames]
  masks=[m.crop(box).resize(tuple(size),Image.Resampling.LANCZOS) for c in selected for m in c['head_masks']]
  ready,rr=quantize(sampled,masks) if target==56 else fixed_top_quantize(sampled,protect_head=round(85*scale))
  rr.update(source_bbox=box,scale=scale,canvas=size,
   anchor=[round((128-box[0])*scale),round((224-box[1])*scale)],
   policy='One crop/scale/palette for both skins and all clips of each target group; 56px body reference plus separate gear envelope, never per-frame recentering.')
  offset=0
  for c in selected:
   n=len(c['masters']);c['runtime']=ready[offset:offset+n];c['runtime_report']=rr;offset+=n
 entries=[];checks=[]
 for (skin,name),c in clips.items():
  paths={};hashes={};s=c['spec'];rr=c['runtime_report']
  for kind,folder in (('masters','masters/'),('formal',''),('runtime','runtime/')):
   target=ART/f'frames/ski/{folder}{skin}/{name}';target.mkdir(parents=True,exist_ok=True);paths[kind]=[];hashes[kind]=[]
   for i,f in enumerate(c[kind]):
    p=target/f'{i:03d}.png';f.save(p);paths[kind].append(p.relative_to(ART).as_posix());hashes[kind].append(sha(p))
  colours=rgba_colors(c['formal']);runtime_colours=rgba_colors(c['runtime']);assert max(colours,runtime_colours)<=64
  entry=dict(name=name,skin=skin,facing='rear-three-quarter-left-lookback',fps=12,loop=s['loop'],frames=paths['formal'],masters=paths['masters'],
   runtime_frames=paths['runtime'],frame_sha256=hashes['formal'],master_sha256=hashes['masters'],runtime_sha256=hashes['runtime'],
   canvas=[256,256],anchor=[128,224],runtime_canvas=rr['canvas'],runtime_anchor=rr['anchor'],target_height_px=s['target'],
   height_measure='NABO body reference; gear and jump clearance included in runtime_canvas',runtime_group='ski56' if s['target']==56 else 'ski72',
   runtime_quantization=rr,delivery_quantization=fr,shared_rgba_colors=colours,runtime_shared_rgba_colors=runtime_colours,
   rig='rig/ski/rig.json',hitbox=union(c['masters']))
  if name.startswith('lean'):entry['release_behavior']='Hold last pose while steering; reverse these frames to neutral before straight. Do not jump directly to straight.'
  if name=='fall':
   from ski_fall import runtime_contact
   entry['fall_contract']={'phases':[r['keyframe']['fall_phase'] for r in c['reports']],
     'head_body_rotation_degrees':[r['keyframe']['fall_pitch'] for r in c['reports']],
     'positive_rigid_determinant':True,'snow_contact_frames':[3,4],'contact_feature':'right mitten edge',
     'gear':'Both skis stay bound to boots; far board tips upward25deg at impact. Pole angles change around their actual grips.',
     'source_rgb':'shared source files unchanged; fall head/face/cap/eyewear rotate rigidly together, with explicit bicubic resampling',
     'per_frame':[{'frame':i,'phase':r['keyframe']['fall_phase'],'root':r['fall'],'snow_contact':r['snow_contact'],
                   'runtime_contact_edge':[round((r['snow_contact']['formal_edge'][0]-rr['source_bbox'][0])*rr['scale']),
                                           round((r['snow_contact']['formal_edge'][1]-rr['source_bbox'][1])*rr['scale'])]}
                  for i,r in enumerate(c['reports'])]}
   for i in (3,4):
    entry['fall_contract']['per_frame'][i].update(runtime_contact(rig,skin,i,rr['source_bbox'],rr['canvas']))
  entry['preview']=contact(entry,c['runtime'],bg);entries.append(entry)
  arr=[np.asarray(f).astype(float) for f in c['runtime']];diff=[float(np.abs(arr[(i+1)%len(arr)]-a).mean()) for i,a in enumerate(arr)]
  if s['loop']:assert diff[-1]<=max(diff[:-1])*1.8
  checks.append(dict(skin=skin,name=name,count=len(c['masters']),rgba_colors=colours,runtime_rgba_colors=runtime_colours,
   reports=c['reports'],runtime_adjacent_rgba_mae=diff))
 context(entries,bg);identity_comparison(rig)
 tools=sorted(Path(__file__).parent.glob('ski_*.py'))
 sources=[*tools,*[Path(__file__).parent/x for x in ('rig_render.py','rig_preview.py','post_rig.py','post_build.py','shared_static_canvas.py')],
  ART/'rig/rig.json',ART/'shared-static-manifest.json',ART/'ui/design/round3/01-passport/palette.json',GAME/'source/generation.json',
  *sorted((GAME/'source').glob('*-prompt.txt')),ROOT.parent/'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf']
 manifest=dict(version=1,package='round9-ski',status='host verified; user art and hardware acceptance pending',rig='rig/ski/rig.json',
  animations=entries,assets=assets,background=dict(world='ski',preview_rgb=bg,source='shared-static-manifest.json backgrounds.ski, original WORLD[6]'),
  identity=dict(reference='reference/nabo-idle-original.png',reference_sha256=sha(ART/'reference/nabo-idle-original.png'),
   selected_travel='design/round1/v2/01-hiker-design-board.png',selected_travel_sha256=sha(ART/'design/round1/v2/01-hiker-design-board.png'),
   common_head=rig['common_head'],generated_head_used=False,
   generated_goggles_accessory_only=True,mirror=False,original_neutral_expression=True),
  source_body_view=rig['view'],local_head_mask=rig['local_head_mask'],counts=dict(character_clips=len(clips),character_frames=len(masters),static_assets=len(assets)),
  provenance={str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p):sha(p) for p in sources})
 (ART/'ski-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
 (PREVIEW/'validation.json').write_text(json.dumps(dict(passed=True,checks=checks,static_assets=len(assets),
  not_claimed=['formal game implementation','on-device performance','user visual acceptance']),ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps(dict(passed=True,counts=manifest['counts'],manifest_sha256=sha(ART/'ski-manifest.json')),indent=2))


if __name__=='__main__':main()
