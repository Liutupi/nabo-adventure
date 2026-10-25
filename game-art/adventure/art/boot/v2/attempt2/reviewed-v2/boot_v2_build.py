#!/usr/bin/env python3
"""Render an independently reviewable, timed 120px boot performance with original audio."""
import argparse
import base64
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from boot_v2_render import prepare,render
from boot_v2_sources import ART,BASE,OUT,SRC,PREVIEW,sha,union,text
from boot_v2_motion import KEYS
from rig_preview import quantize
from boot_v2_optimize import optimize

VOICE=BASE/'audio/boot-welcome.wav';BG='#18303c'


def production_background():
 manifest=json.loads((ART/'ui/ui-manifest.json').read_text('utf-8'));cover=manifest['cover'];sources=[]
 image=Image.open(ART/'ui'/cover['background']).convert('RGBA');sources.append(ART/'ui'/cover['background'])
 for path,xy in ((cover['logo'],cover['logo_offset']),(cover['caption']['path'],cover['caption']['offset']),
                 (cover['start_button']['path'],cover['start_button']['offset'])):
  source=ART/'ui'/path;image.alpha_composite(Image.open(source).convert('RGBA'),tuple(xy));sources.append(source)
 return image.convert('RGB'),{p.relative_to(ART).as_posix():sha(p) for p in sources}


def screen(frame,anchor,background):
 result=background.copy();result.paste(frame,(120-anchor[0],266-anchor[1]),frame);return result


def browser_preview(entry,timeline,v1,background_path):
 def data(path,mime):return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode('ascii')
 payload=dict(frames=[data(ART/p,'image/png') for p in entry['runtime_frames']],anchor=entry['runtime_anchor'],
  oldframes=[data(ART/p,'image/png') for p in v1['runtime_frames']],oldanchor=v1['runtime_anchor'],
  timeline=timeline,audio=data(VOICE,'audio/wav'),background=data(background_path,'image/png'))
 html='''<!doctype html><meta charset="utf-8"><title>NABO boot V2 · 120px</title>
<style>body{background:#e7d5ad;color:#203849;font:16px system-ui;margin:24px}button{font:inherit;padding:8px 20px;margin-right:12px}main{display:flex;gap:24px}canvas{width:240px;height:320px;image-rendering:pixelated;background:#18303c}h2{font-size:18px}p{max-width:720px}#info{font-variant-numeric:tabular-nums}select{font:inherit}</style>
<h1>NABO 开机表演 V2</h1><p>原尺寸：人物参考高120px，固定脚锚(120,266)。原声1.4秒开始，4.090625秒结束。右侧一次表演后稳住；左侧仅对照旧16帧动作循环，未重演全人物平移入场。</p>
<button id="play">播放原声与演出</button><button id="stop">停止</button><span id="info"></span><main><section><h2>V1：旧动作</h2><canvas id="old" width="240" height="320"></canvas></section><section><h2>V2：多阶段候选</h2><canvas id="new" width="240" height="320"></canvas></section></main>
<p>提包带蓄势 → 扶帽檐抬头 → 张掌挥手 → 掌心邀请 → 脚尖/点头回稳。此页仅为离线预览，尚未接入固件。原生三表情是整头资源，未贴耳机或改画脸。</p>
<script>const P=__PAYLOAD__;let loaded,ctx,source,start=0,raf=0;async function images(a){return Promise.all(a.map(s=>new Promise(r=>{let i=new Image;i.onload=()=>r(i);i.src=s})));}
let bg;function draw(id,image,anchor){let c=document.getElementById(id),g=c.getContext('2d');g.imageSmoothingEnabled=false;g.drawImage(bg,0,0);g.drawImage(image,120-anchor[0],266-anchor[1]);}
async function setup(){bg=(await images([P.background]))[0];loaded=[await images(P.oldframes),await images(P.frames)];draw('old',loaded[0][0],P.oldanchor);draw('new',loaded[1][0],P.anchor)}setup();
function stop(){cancelAnimationFrame(raf);if(source){try{source.stop()}catch(e){}source=null}}
document.getElementById('stop').onclick=stop;
document.getElementById('play').onclick=async()=>{stop();if(!ctx)ctx=new AudioContext;await ctx.resume();let buf=await ctx.decodeAudioData(await (await fetch(P.audio)).arrayBuffer());source=ctx.createBufferSource();source.buffer=buf;source.connect(ctx.destination);source.start(ctx.currentTime+.05+1.4);start=performance.now()+50;function step(){let t=Math.max(0,performance.now()-start),k=0;while(k+1<P.timeline.pose_start_ms.length&&P.timeline.pose_start_ms[k+1]<=t)k++;draw('old',loaded[0][Math.floor(t*12/1000)%loaded[0].length],P.oldanchor);draw('new',loaded[1][P.timeline.pose_frame_indices[k]],P.anchor);document.getElementById('info').textContent=(t/1000).toFixed(3)+'s · '+P.timeline.labels[k];if(t<P.timeline.total_duration_ms)raf=requestAnimationFrame(step);}step();};</script>'''
 html=html.replace('__PAYLOAD__',json.dumps(payload,ensure_ascii=False));(PREVIEW/'welcome-v2-voice-preview.html').write_text(html,'utf-8')


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--attempt',default='attempt2');parser.add_argument('--dp-order',action='store_true');args=parser.parse_args()
 folder=OUT/args.attempt;folder.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(parents=True,exist_ok=True)
 prepared=prepare();masters=[];reports=[];background,ui_sources=production_background();background.save(OUT/'production-ui-background.png')
 for i in range(len(KEYS)):
  frame,report=render(prepared,i);masters.append(frame);reports.append(report)
  box=report['bbox'];assert 0<box[0]<box[2]<256 and 0<box[1]<box[3]<256,(i,box)
 box=union(masters);scale=120/208;size=[round((box[2]-box[0])*scale),round((box[3]-box[1])*scale)]
 sampled=[f.crop(box).resize(tuple(size),Image.Resampling.LANCZOS) for f in masters]
 runtime,qr=quantize(sampled,colours=48,protect_head=round(100*scale))
 anchor=[round((128-box[0])*scale),round((224-box[1])*scale)];qr.update(source_bbox=box,scale=scale,canvas=size,anchor=anchor,
  policy='Fixed 120/208 body scale, one union crop and palette; no per-frame shrink or whole-figure entry translation')
 paths=[];hashes=[];mpaths=[];screens=[];canonical={};pose_indices=[]
 for i,(master,frame) in enumerate(zip(masters,runtime)):
  for sub in ('masters','runtime','screens'):(folder/sub).mkdir(exist_ok=True)
  mpath=folder/'masters'/f'{i:03d}.png';master.save(mpath);mpaths.append(mpath.relative_to(ART).as_posix())
  digest=hashlib.sha256(frame.tobytes()).hexdigest()
  if digest not in canonical:
   canonical[digest]=len(paths);path=folder/'runtime'/f'{len(paths):03d}.png';frame.save(path);paths.append(path.relative_to(ART).as_posix());hashes.append(sha(path))
  pose_indices.append(canonical[digest])
  view=screen(frame,anchor,background);view.save(folder/'screens'/f'{i:03d}.png');screens.append(view)
 for old in (folder/'runtime').glob('*.png'):
  if old.relative_to(ART).as_posix() not in paths:old.unlink()
 unique_images=[Image.open(ART/p).convert('RGBA') for p in paths]
 physical_order,optimization=optimize(unique_images,args.dp_order);inverse={old:new for new,old in enumerate(physical_order)}
 paths=[paths[i] for i in physical_order];hashes=[hashes[i] for i in physical_order]
 pose_indices=[inverse[i] for i in pose_indices]
 (folder/'lossless-frame-order.json').write_text(json.dumps(optimization,ensure_ascii=False,indent=2)+'\n','utf-8')
 starts=[round(k[0]*1000/12) for k in KEYS];end=round(53*1000/12);durations=[b-a for a,b in zip(starts,starts[1:]+[end])]
 timeline=dict(timebase='milliseconds since screen visible t=0',pose_start_ms=starts,duration_ms=durations,
  duration_ticks=[r['duration_ticks'] for r in reports],exact_ticks=[k[0] for k in KEYS],labels=[r['label'] for r in reports],
  pose_frame_indices=pose_indices,unique_frame_count=len(paths),logical_pose_count=len(KEYS),
  total_duration_ms=end,exact_duration_s=53/12,voice_start_ms=1400,voice_end_ms=4090.625,voice_duration_ms=2690.625,
  playback='one shot; hold final idle, never loop or add whole-character entrance translation')
 entry=dict(name='welcome_v2',skin='travel',fps=12,loop=False,runtime_frames=paths,runtime_sha256=hashes,runtime_canvas=size,
  runtime_anchor=anchor,canvas=[256,256],anchor=[128,224],masters=mpaths,target_height_px=120,
  body_reference_height=208,gear_or_head_rotation_envelope_extra_px=size[1]-120,presentation=dict(screen_anchor=[120,266],timeline=timeline),
  timeline=timeline,runtime_quantization=qr,lossless_storage_order=optimization,
  identity='Original native three-expression head, selected hiker clothing; no new face or hat mirrored')
 old=json.loads((ART/'manifest.json').read_text('utf-8'));v1=next(e for e in old['animations'] if e['skin']=='travel' and e['name']=='welcome')
 v1={k:v1[k] for k in ('name','skin','fps','loop','runtime_frames','runtime_sha256','runtime_canvas','runtime_anchor')}
 (SRC/'v1-runtime-record.json').write_text(json.dumps(v1,ensure_ascii=False,indent=2)+'\n','utf-8')
 browser_preview(entry,timeline,v1,OUT/'production-ui-background.png')
 # GIF timing is centisecond-quantized. Browser/manifest use the same exact ms table.
 gif_durations=[round((start+dur)/10)*10-round(start/10)*10 for start,dur in zip(starts,durations)]
 screens[0].save(PREVIEW/(args.attempt+'-120px.gif'),save_all=True,append_images=screens[1:],duration=gif_durations,disposal=2)
 cols=6;rows=(len(runtime)+cols-1)//cols;cw=160;ch=176;board=Image.new('RGB',(cols*cw,rows*ch),BG);d=ImageDraw.Draw(board)
 for i,frame in enumerate(runtime):
  x,y=i%cols*cw,i//cols*ch;board.paste(frame,(x+80-anchor[0],y+132-anchor[1]),frame)
  text(d,(x+4,y+140),f'{i:02d} {starts[i]}ms',12,'#fff0cd');text(d,(x+4,y+157),reports[i]['label'],11,'#fff0cd')
 board.save(PREVIEW/(args.attempt+'-120px-contact.png'))
 # Preserve the real prior-series comparison and add eight new native-size acting beats.
 comparison=Image.open(BASE.parents[1]/'private/boot-reference/production-welcome-comparison-1x.png').convert('RGB')
 comp=Image.new('RGB',(1200,636),BG);comp.paste(comparison,(0,0));cd=ImageDraw.Draw(comp)
 for column,i in enumerate((0,3,6,10,14,17,21,28)):
  im=runtime[i];x=column*150+75-anchor[0];comp.paste(im,(x,622-anchor[1]),im)
  text(cd,(column*150+2,477),f'V2 {starts[i]/1000:.2f}s',10,'#fff0cd')
 comp.save(PREVIEW/'previous-series-v1-v2-1x.png')
 sources=[Path(__file__),*[Path(__file__).parent/x for x in ('boot_v2_sources.py','boot_v2_render.py','boot_v2_motion.py','boot_v2_optimize.py')],VOICE,ART/'rig/rig.json']
 manifest=dict(version=1,package='boot-v2-preview',status='acting candidate; review actual motion before firmware use',
  animations=[entry],presentation=entry['presentation'],timeline=timeline,source_provenance='boot/v2/source/provenance.json',
  voice=dict(path=VOICE.relative_to(BASE).as_posix(),sha256=sha(VOICE),display_text='NABO,陪你冒险',unchanged=True),
  reused_sleeve='Only isolated same-jacket sleeve pixels mirrored to complete the occluded arm; no head/hat/face mirrored',
  production_ui_sources=ui_sources,provenance={str(p.relative_to(BASE.parents[1])):sha(p) for p in sources})
 (ART/'boot-v2-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
 (folder/'poses.json').write_text(json.dumps(dict(timeline=timeline,reports=reports),ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps(dict(logical_poses=len(KEYS),unique_runtime_frames=len(paths),duration_ms=end,runtime_canvas=size,runtime_anchor=anchor,
  manifest_sha256=sha(ART/'boot-v2-manifest.json'),voice_unchanged=sha(VOICE)),indent=2))


if __name__=='__main__':main()
