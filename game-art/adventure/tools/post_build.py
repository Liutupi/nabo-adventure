#!/usr/bin/env python3
"""Rebuild POST skins, native props, 256RGBA delivery and 40/72px runtime sprites."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from post_config import ART,ROOT,GAME,RIG,PREVIEW,SPECS,SKIN_ANIMS,HALF_ANCHOR,FULL_ANCHOR
from post_rig import build,sha
from post_render import render
from post_props import build_props
from post_palette import fixed_palette
from post_cab import build_cord,preview_cord

FONT=ROOT.parent/'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf'


def text(draw,xy,message,size=14,fill='#203849'):
 draw.text(xy,message,font=ImageFont.truetype(str(FONT),size),fill=fill)


def background():
 import re
 path=ROOT/'firmware/main/adv_ui_map.c'
 block=re.search(r'WORLD\[ADV_STATIONS\]\s*=\s*\{(.*?)\};',path.read_text('utf-8'),re.S)
 rows=[tuple(map(int,v)) for v in re.findall(r'\{\s*(\d+),\s*(\d+),\s*(\d+)\s*\}',block[1])]
 rgb=rows[3];rgb565=((rgb[0]>>3)<<11)|((rgb[1]>>2)<<5)|(rgb[2]>>3)
 return tuple([(rgb565>>11)*255//31,((rgb565>>5)&63)*255//63,(rgb565&31)*255//31]),path


def union(frames):
 mask=np.maximum.reduce([np.asarray(f.getchannel('A'))>=128 for f in frames]);y,x=np.where(mask)
 return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]


def rgba_colors(frames):
 return len(set().union(*[set(map(tuple,np.asarray(f).reshape(-1,4))) for f in frames]))


def gif(path,frames,loop,bg,zoom=3):
 screens=[]
 for frame in frames:
  big=frame.resize((frame.width*zoom,frame.height*zoom),Image.Resampling.NEAREST)
  out=Image.new('RGB',(max(160,big.width+24),big.height+30),bg)
  out.paste(big,((out.width-big.width)//2,12),big);screens.append(out)
 durations=[round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(len(frames))]
 options=dict(loop=0) if loop else {}
 screens[0].save(path,save_all=True,append_images=screens[1:],duration=durations,disposal=2,**options)


def contact(entry,frames,bg):
 count=len(frames);h=frames[0].height;zoom=3;cw=max(128,frames[0].width*zoom+16);ch=h*4+65
 sheet=Image.new('RGB',(cw*count,ch*2));d=ImageDraw.Draw(sheet)
 for row,(world,color) in enumerate((('rail RGB565',bg),('UI dark',(24,36,57)))):
  d.rectangle((0,row*ch,sheet.width,(row+1)*ch),fill=color)
  text(d,(8,row*ch+4),entry['skin']+' / '+entry['name']+f' / {h}px / '+world,13,'#203849' if row==0 else '#fff0cd')
  for i,frame in enumerate(frames):
   x,y=i*cw,row*ch
   sheet.paste(frame,(x+(cw-frame.width)//2,y+31),frame)
   big=frame.resize((frame.width*3,h*3),Image.Resampling.NEAREST)
   sheet.paste(big,(x+(cw-big.width)//2,y+h+41),big)
   text(d,(x+9,y+ch-19),f'{i:03d}',12,'#203849' if row==0 else '#fff0cd')
 path=PREVIEW/(entry['skin']+'-'+entry['name']+'-contact.png');sheet.save(path)
 for world,color in (('rail',bg),('dark',(24,36,57))):
  gif(PREVIEW/(entry['skin']+'-'+entry['name']+'-'+world+'.gif'),frames,entry['loop'],color)
 return path.relative_to(ART).as_posix()


def static_qa(assets):
 for a in assets:
  im=Image.open(ART/a['path']).convert('RGBA');data=np.asarray(im);alpha=set(np.unique(data[:,:,3]).tolist())
  a.setdefault('color_limit',2 if a.get('tintable') else 16)
  colors=rgba_colors([im]);bbox=im.getchannel('A').getbbox();seams={}
  if a.get('repeat_axes'):
   for axis in a['repeat_axes']:
    seams[axis]=bool(np.array_equal(data[:,0],data[:,-1])) if axis=='x' else bool(np.array_equal(data[0],data[-1]))
  a['qa']=dict(rgba_colors=colors,alpha=sorted(alpha),bbox=list(bbox),seams=seams,
   passed=im.size==tuple(a['size']) and alpha=={0,255} and colors<=a['color_limit'] and all(seams.values()))
  assert a['qa']['passed'],a['id']
  if a.get('tintable'):assert set(map(tuple,data[data[:,:,3]>0,:3]))=={(255,255,255)}
  a['id']='post/'+('tiles/' if a['category']=='tile' else 'props/')+a['id']


def props_preview(assets,bg):
 cw,ch=240,240;rows=(len(assets)+3)//4;out=Image.new('RGB',(cw*4,ch*rows),bg);d=ImageDraw.Draw(out)
 for i,a in enumerate(assets):
  x,y=i%4*cw,i//4*ch;im=Image.open(ART/a['path']).convert('RGBA')
  out.paste(im,(x+8,y+28),im);big=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
  out.paste(big,(x+cw-big.width-8,y+45),big)
  text(d,(x+7,y+5),a['id'].split('/')[-1],13)
  text(d,(x+7,y+ch-22),str(a['size'])+' / native + 2x',12)
  single=Image.new('RGB',im.size,bg);single.paste(im,(0,0),im)
  path=PREVIEW/'props'/(a['id'].split('/')[-1]+'.png');path.parent.mkdir(exist_ok=True);single.save(path)
  a['preview']=path.relative_to(ART).as_posix()
 out.save(PREVIEW/'props-contact.png')


def train_context(entries,bg,cab):
 board=Image.new('RGB',(1440,670),'#e7d5ad');d=ImageDraw.Draw(board)
 def png(name):return Image.open(GAME/'props'/(name+'.png')).convert('RGBA')
 for column,skin in enumerate(('post_a','post_b')):
  entry=next(e for e in entries if e['skin']==skin and e['name']=='idle')
  frames=[]
  for i in range(12):
   scene=Image.new('RGBA',(240,320),bg)
   mountain=Image.open(GAME/'tiles/far-mountains.png').convert('RGBA')
   for x in (0,96,192):scene.alpha_composite(mountain,(x,126))
   track=Image.open(GAME/'tiles/track-straight.png').convert('RGBA')
   for x in range(0,240,32):scene.alpha_composite(track,(x,224))
   platform=png('station-platform-mask');tint=Image.new('RGBA',platform.size,'#b64c43');tint.putalpha(platform.getchannel('A'))
   scene.alpha_composite(tint,(158,122))
   scene.alpha_composite(png('carriage'),(13,190))
   scene.alpha_composite(png('envelope-red'),(29,187))
   scene.alpha_composite(png('wheel-'+f'{i%4:03d}'),(80,154))
   scene.alpha_composite(png('locomotive-body'),(80,154))
   scene.alpha_composite(Image.open(GAME/'props/whistle-cord/000.png').convert('RGBA'),(80,154))
   actor=Image.open(ART/entry['runtime_frames'][i%6]).convert('RGBA');ax,ay=entry['runtime_anchor']
   scene.alpha_composite(actor,(80+cab['driver_chest'][0]-ax,154+cab['driver_chest'][1]-ay));scene.alpha_composite(png('cab-foreground'),(80,154))
   scene.alpha_composite(png('sheep'),(188,231));frames.append(scene)
  frames[0].convert('RGB').save(PREVIEW/(skin+'-train-native.png'))
  gif(PREVIEW/(skin+'-train-loop.gif'),frames,True,bg,1)
  board.paste(frames[0],(column*720,30));board.paste(frames[0].resize((480,640),Image.Resampling.NEAREST),(column*720+240,30))
  text(d,(column*720+8,5),skin+' / native 240x320 + 2x / host composition',13)
 board.save(PREVIEW/'train-composition-contact.png')


def identity_preview(rig):
 board=Image.new('RGB',(1024,300),'#f6e2b4');d=ImageDraw.Draw(board)
 for column,skin in enumerate(rig['skins']):
  original=Image.open(RIG/(skin+'-normalized-master.png')).convert('RGBA')
  composed,_=render(rig,skin,'settlement_cheer',0)
  composed.save(RIG/(skin+'-neutral-composite.png'))
  for offset,frame in enumerate((original,composed)):
   x=column*512+offset*256;board.paste(frame,(x,32),frame)
   text(d,(x+6,6),skin+(' generated master' if offset==0 else ' shared-head composite'),12)
 board.save(PREVIEW/'source-identity-review.png')


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
 PREVIEW.mkdir(parents=True,exist_ok=True);bg,bgsource=background();rig=build();assets,prop_anims=build_props()
 static_qa(assets);props_preview(assets,bg);identity_preview(rig)
 clips={}
 for skin,names in SKIN_ANIMS.items():
  for name in names:
   masters=[];reports=[]
   for i in range(SPECS[name]['count']):
    frame,report=render(rig,skin,name,i);masters.append(frame);reports.append(report)
   clips[(skin,name)]=dict(masters=masters,reports=reports,spec=SPECS[name])
 lock=json.loads((RIG/'export-palette-lock.json').read_text('utf-8'))
 all_masters=[f for c in clips.values() for f in c['masters']]
 formal,formal_report=fixed_palette(all_masters,lock['formal'],protect_head=True);offset=0
 for c in clips.values():c['formal']=formal[offset:offset+len(c['masters'])];offset+=len(c['masters'])
 for height in (40,72):
  rows=[c for c in clips.values() if c['spec']['target']==height];masters=[f for c in rows for f in c['masters']]
  frozen=lock['runtime'][str(height)];box=frozen['source_bbox'];scale=frozen['scale'];size=frozen['canvas']
  observed=union(masters);assert all(observed[i]>=box[i] for i in (0,1)) and all(observed[i]<=box[i] for i in (2,3))
  sampled=[f.crop(box).resize(tuple(size),Image.Resampling.LANCZOS) for f in masters]
  target,report=fixed_palette(sampled,frozen,protect_head=round(84*scale))
  anchor=HALF_ANCHOR if height==40 else FULL_ANCHOR
  report.update(source_bbox=box,scale=scale,canvas=size,anchor=[round((anchor[0]-box[0])*scale),round((anchor[1]-box[1])*scale)],
   policy='One union crop, scale and palette for all clips and both skins of the same target height; never recenter individual frames.')
  offset=0
  for c in rows:c['runtime']=target[offset:offset+len(c['masters'])];c['runtime_report']=report;offset+=len(c['masters'])
 entries=[];checks=[]
 for (skin,name),clip in clips.items():
  spec=clip['spec'];paths={};hashes={}
  for key,subdir in (('masters','masters/'),('formal',''),('runtime','runtime/')):
   folder=ART/f'frames/post/{subdir}{skin}/{name}';folder.mkdir(parents=True,exist_ok=True)
   paths[key]=[];hashes[key]=[]
   for i,frame in enumerate(clip[key]):
    path=folder/f'{i:03d}.png';frame.save(path);paths[key].append(path.relative_to(ART).as_posix());hashes[key].append(sha(path))
  count=spec['count'];rr=clip['runtime_report'];colors=rgba_colors(clip['runtime']);formal_colors=rgba_colors(clip['formal'])
  assert colors<=64 and formal_colors<=64
  entry=dict(name=name,skin=skin,facing='front',fps=12,loop=bool(spec['loop']),frames=paths['formal'],masters=paths['masters'],
   runtime_frames=paths['runtime'],frame_sha256=hashes['formal'],master_sha256=hashes['masters'],runtime_sha256=hashes['runtime'],
   canvas=[256,256],anchor=list(HALF_ANCHOR if spec['target']==40 else FULL_ANCHOR),target_height_px=spec['target'],
   runtime_canvas=rr['canvas'],runtime_anchor=rr['anchor'],runtime_group='post_half40' if spec['target']==40 else 'post_full72',
   hitbox=union(clip['masters']),shared_rgba_colors=formal_colors,runtime_shared_rgba_colors=colors,
   runtime_quantization=rr,delivery_quantization=formal_report,rig='rig/post/rig.json')
  if name=='throw':entry['events']=[dict(frame=3,event='release-envelope; engine owns subsequent projectile motion')]
  if name=='whistle':entry['events']=[dict(frame=2,event='grasp'),dict(frame=3,event='pull-whistle')]
  entry['preview']=contact(entry,clip['runtime'],bg);entries.append(entry)
  arrays=[np.asarray(f).astype(float) for f in clip['runtime']]
  differences=[float(np.abs(arrays[(i+1)%count]-arrays[i]).mean()) for i in range(count)]
  if spec['loop']:assert differences[-1]<=max(differences[:-1])*1.8
  checks.append(dict(skin=skin,name=name,frames=count,formal_colors=formal_colors,runtime_colors=colors,
   frame_reports=clip['reports'],runtime_adjacent_rgba_mae=differences,alpha=[0,255],passed=True))
 cab=next(a for a in assets if a['id']=='post/props/locomotive-body')
 whistle=next(e for e in entries if e['skin']=='post_a' and e['name']=='whistle')
 cord=build_cord(whistle,clips['post_a','whistle']['reports'],cab);prop_anims.append(cord)
 whistle.update(cab_attachment='post_props/whistle-cord',grip_contact=cord['contacts'])
 preview_cord(whistle,cab,cord,bg)
 for entry in prop_anims:
  entry['runtime_sha256']=[sha(ART/p) for p in entry['runtime_frames']]
  entry['runtime_shared_rgba_colors']=rgba_colors([Image.open(ART/p).convert('RGBA') for p in entry['runtime_frames']])
  assert entry['runtime_shared_rgba_colors']<=64
 entries+=prop_anims
 train_context(entries,bg,cab)
 tools=sorted(Path(__file__).parent.glob('post_*.py'))
 sources=[*tools,Path(__file__).parent/'rig_render.py',Path(__file__).parent/'rig_preview.py',Path(__file__).parent/'shared_static_canvas.py',
  ART/'rig/rig.json',RIG/'export-palette-lock.json',ART/'ui/design/round3/01-passport/palette.json',GAME/'source/generation.json',bgsource,FONT]
 manifest=dict(version=1,package='round6-post',status='host-rendered; user artwork and hardware acceptance pending',
  rig='rig/post/rig.json',animations=entries,assets=assets,background=dict(world='rail',preview_rgb=list(bg),source=bgsource.relative_to(ROOT).as_posix()),
  identity=dict(reference='reference/nabo-idle-original.png',sha256=sha(ART/'reference/nabo-idle-original.png'),
   selected_travel='design/round1/v2/01-hiker-design-board.png',common_head=rig['common_head'],generated_head_used=False,
   garment_exclusion=rig['garment_exclusion'],mirror=False,expressions='Original neutral face retained; gestures carry emotion.'),
  counts=dict(character_clips=len(clips),character_frames=len(all_masters),props=len(assets),wheel_frames=4,whistle_cord_frames=6),
  provenance={str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p):sha(p) for p in sources})
 (ART/'post-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
 (PREVIEW/'validation.json').write_text(json.dumps(dict(passed=True,checks=checks,static_assets=len(assets),
  native_background=list(bg),source_frame_policy='256 RGBA, immutable head pixels, source cutouts then shared palette',
  not_claimed=['new gameplay','firmware integration','on-device motion','human visual acceptance']),ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps(dict(passed=True,counts=manifest['counts'],manifest_sha256=sha(ART/'post-manifest.json')),indent=2))


if __name__=='__main__':main()
