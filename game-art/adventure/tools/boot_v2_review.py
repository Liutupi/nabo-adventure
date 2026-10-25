"""Read-only V2a pixel/timing/seam checks and native-size transition evidence."""
import json
import math
import shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from boot_v2_sources import ART,BASE,OUT,PREVIEW,sha,text
from rig_render import turn,translate,transformed


def pose_at(timeline,tick):
 return max(i for i,t in enumerate(timeline['exact_ticks']) if t<=tick)


def seam_checks(reports):
 rig=OUT/'rig';cuff=Image.open(rig/'cuff.png').convert('RGBA')
 hands={k:Image.open(rig/(k+'-palm.png')).convert('RGBA') for k in ('open','half')}
 hands['closed']=Image.open(rig/'closed-hand.png').convert('RGBA');result=[]
 for r in reports:
  m=turn(r['torso_angle'],[128,155])@turn(r['upper_arm_r_degrees'],[151,106])@turn(r['forearm_r_degrees'],[158,134])
  wrist=r['world_wrist'];c=np.asarray(transformed(cuff,m).getchannel('A'))>=64
  state=r['palm_state'];hm=m if state=='closed' else translate(wrist[0]-160,wrist[1]-154)@turn(r['palm_world_angle'],[160,154])
  h=np.asarray(transformed(hands[state],hm).getchannel('A'))>=64
  yy,xx=np.indices(c.shape);near=(xx-wrist[0])**2+(yy-wrist[1])**2<=12**2
  cp=np.argwhere(c&near);hp=np.argwhere(h&near)
  distance=math.sqrt(int(np.min(np.sum((cp[:,None,:]-hp[None,:,:])**2,axis=2)))) if len(cp) and len(hp) else None
  result.append(dict(label=r['label'],state=state,overlap_pixels=int(np.sum(c&h)),
   closest_local_pixel_centres=distance,visible_gap_estimate_px=None if distance is None else max(0,distance-1)))
 return result


def main():
 manifest_path=ART/'boot-v2-manifest.json';locked=sha(manifest_path)
 m=json.loads(manifest_path.read_text('utf-8'));e=m['animations'][0];t=m['timeline']
 assert m['package']=='boot-v2a-preview'
 folder=ART/e['masters'][0];folder=folder.parent.parent
 poses=json.loads((folder/'poses.json').read_text('utf-8'))['reports']
 rgba=[];palette=set()
 for p,h in zip(e['runtime_frames'],e['runtime_sha256']):
  path=ART/p;assert sha(path)==h
  image=Image.open(path).convert('RGBA');assert list(image.size)==e['runtime_canvas']
  pixels=np.asarray(image);assert set(np.unique(pixels[:,:,3]))<={0,255}
  palette.update(map(tuple,pixels[pixels[:,:,3]>0]));rgba.append(image.tobytes())
 assert len(rgba)==len(set(rgba))==32 and len(palette)<=48
 assert len(t['pose_start_ms'])==34 and sum(t['duration_ticks'])==53 and sum(t['duration_ms'])==4417
 assert all(d>0 for d in t['duration_ticks']) and t['pose_start_ms']==[round(x*1000/12) for x in t['exact_ticks']]
 assert t['voice_start_ms']==1400 and t['voice_end_ms']==4090.625
 assert all(0<i<len(e['runtime_frames']) or i==0 for i in t['pose_frame_indices'])
 masters=[Image.open(ART/p).convert('RGBA') for p in e['masters']]
 assert all(0<r['bbox'][0]<r['bbox'][2]<256 and 0<r['bbox'][1]<r['bbox'][3]<256 for r in poses)
 assert all(r['frame_root_translation']==[0,0] and abs(r['head_det']-1)<1e-9 for r in poses)
 original=json.loads((OUT/'attempt2/reviewed-v2/boot-v2-manifest.json').read_text('utf-8'))
 previous=original['animations'][0];previous_t=original['timeline']
 groups=[list(range(9,21)),list(range(26,34)),list(range(38,43))]
 width=1200;rowh=170;board=Image.new('RGB',(width,6*rowh),'#18303c');draw=ImageDraw.Draw(board)
 for group,ticks in enumerate(groups):
  for row,(entry,timeline,label) in enumerate(((previous,previous_t,'reviewed V2'),(e,t,'frozen V2a'))):
   y=(group*2+row)*rowh
   for col,tick in enumerate(ticks):
    i=pose_at(timeline,tick);im=Image.open(ART/entry['runtime_frames'][timeline['pose_frame_indices'][i]]).convert('RGBA')
    x=col*100+50-entry['runtime_anchor'][0];board.paste(im,(x,y+135-entry['runtime_anchor'][1]),im)
    text(draw,(col*100+3,y+138),f'{tick/12:.3f}s',11,'#fff0cd')
   text(draw,(3,y+157),label,10,'#fff0cd')
 board.save(PREVIEW/'v2a-transition-comparison-1x.png')
 seams=seam_checks(poses)
 rows=['#pragma once','#include <stdint.h>',
  'typedef struct {uint16_t at_ms; uint8_t frame; uint8_t reserved;} boot_v2_pose_t;',
  '_Static_assert(sizeof(boot_v2_pose_t)==4,"boot schedule layout");',
  'static const boot_v2_pose_t boot_v2_schedule[] = {']
 rows += [f' {{{ms},{idx},0}},' for ms,idx in zip(t['pose_start_ms'],t['pose_frame_indices'])]
 rows += ['};','typedef struct {uint32_t duration_ms,voice_start_ms,voice_end_us;uint16_t poses,fps;} boot_v2_meta_t;',
  '_Static_assert(sizeof(boot_v2_meta_t)==16,"boot metadata layout");',
  'static const boot_v2_meta_t boot_v2_meta={4417,1400,4090625,34,12};']
 header='\n'.join(rows)+'\n';(folder/'presentation-timeline.h').write_text(header,'utf-8')
 (OUT/'presentation-timeline.h').write_text(header,'utf-8')
 snapshots=folder/'source-snapshot';snapshots.mkdir(exist_ok=True)
 for name in ('boot_v2_build.py','boot_v2_sources.py','boot_v2_motion.py','boot_v2_render.py','boot_v2_media.py'):
  shutil.copyfile(BASE/'tools'/name,snapshots/name)
 shutil.copyfile(manifest_path,snapshots/'boot-v2-manifest.json')
 voice=BASE/m['voice']['path'];assert sha(voice)==m['voice']['sha256']
 report=dict(manifest_sha256=locked,logical_events=34,unique_runtime_frames=32,canvas=e['runtime_canvas'],anchor=e['runtime_anchor'],
  visible_palette_colours=len(palette),binary_alpha=True,source_canvas=[256,256],source_clip_boundaries='all alpha>=128 bboxes strictly inside source canvas',
  exact_ticks=53,exact_seconds=53/12,voice_unchanged=True,voice_sha256=sha(voice),timeline_table_bytes=152,
  closed_eye_ticks=sum(r['duration_ticks'] for r in poses if r['expression']=='closed'),
  half_eye_ticks=sum(r['duration_ticks'] for r in poses if r['expression']=='half'),
  source_head_policy='Official whole-head native expressions; rigid BICUBIC rotation, no mirror/nonuniform deformation or new mouth drawing',
  seams=seams,max_local_source_seam_gap=max(r['visible_gap_estimate_px'] or 0 for r in seams),
  dynamic_review='Native contacts viewed; continuous MP4 review delegated to root/host. Browser file:// attempt rejected by URL policy; no workaround attempted.',
  remaining_limits='Fixed original neutral mouth and 2D limb pivots remain less expressive than prior Grok footage; no claim of matching its full deformation.',
  budget='Not accepted against 160KiB yet; root/host lossless PoC owns current budget. Earlier packing JSON refers to prior 27-image V2, not this V2a.')
 assert sha(manifest_path)==locked
 (PREVIEW/'qa-v2a.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='seams'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
