"""Skinning of real rear-view costume masters; common left head is never redrawn."""
import copy
import json
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from post_rig import sha,svg
from ski_config import ART,GAME,RIG,CANVAS,LOCKS,PARTS,ORDER


def polygon(points):
 mask=Image.new('L',CANVAS);ImageDraw.Draw(mask).polygon(points,fill=255);return mask


def build():
 RIG.mkdir(parents=True,exist_ok=True);common=json.loads((ART/'rig/rig.json').read_text('utf-8'))
 head_source=Image.open(ART/'rig/common/left/head.png').convert('RGBA');pixels=np.asarray(head_source).astype(int)
 yy,xx=np.indices((256,256));neck=(pixels[:,:,0]>=160)&(pixels[:,:,0]-pixels[:,:,1]>=5)&(pixels[:,:,0]-pixels[:,:,2]>=10)
 keep=(yy<=93)|((yy<=100)&(yy>=94)&(xx>=116)&(xx<=136)&neck)
 mask=Image.fromarray(keep.astype('uint8')*255)
 mask.save(RIG/'head-garment-exclusion-mask.png');heads=[]
 for name in ('head','expression_neutral'):
  p=common['views']['left']['parts'][name];path='rig/'+p['raster'];assert sha(ART/path)==p['rgba_sha256']
  heads.append(dict(name=name,path=path,sha256=p['rgba_sha256'],local_alpha_mask='rig/ski/head-garment-exclusion-mask.png'))
 result=dict(version=1,canvas=list(CANVAS),anchor=[128,224],common_head=heads,head_facing='left',
  head_reference_neck=[125,98],body_neck_bind=[111,98],common_source_sha256=common['source_sha256'],
  view='Actual elevated rear-three-quarter costume body, immutable left three-quarter head looking back; never mirrored',
  local_head_mask='All y0..93 retained; y94..100 only original warm neck pixels within x116..136; old green collar excluded without changing retained RGB',
  draw_order=ORDER,body_reference_height=208,skins={})
 for skin,digest in LOCKS.items():
  source=GAME/'source'/(skin.replace('_','-')+'-master.png');assert sha(source)==digest
  raw=Image.open(source).convert('RGBA');core=raw.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
  scale=126/(core[3]-480);left=128-round(635*scale);top=98-round(480*scale)
  resized=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS)
  normalized=Image.new('RGBA',CANVAS);normalized.alpha_composite(resized,(left,top))
  am=np.asarray(normalized.getchannel('A')).copy();rgb=np.asarray(normalized).astype(int);yy,xx=np.indices((256,256))
  if skin=='ski_a':garment=(rgb[:,:,1]>rgb[:,:,0]+5)|((rgb[:,:,0]>rgb[:,:,1]+35)&(rgb[:,:,1]<105)&(rgb[:,:,2]<95))
  else:garment=(rgb[:,:,0]>rgb[:,:,1])&(rgb[:,:,1]>rgb[:,:,2]+35)
  upper_collar=(yy>=94)&(yy<98)&garment
  am[(yy<98)&~upper_collar]=0;normalized.putalpha(Image.fromarray(am))
  normalized.save(RIG/(skin+'-normalized-clothes.png'))
  folder=RIG/'skins'/skin;folder.mkdir(parents=True,exist_ok=True);remaining=Image.new('L',CANVAS)
  ImageDraw.Draw(remaining).rectangle((0,98,255,255),fill=255);parts={}
  for name,spec in PARTS.items():
   region=polygon(spec['poly']) if spec['poly'] else remaining.copy()
   partmask=ImageChops.multiply(region,remaining);remaining=ImageChops.subtract(remaining,partmask)
   joints=[]
   if name.startswith(('upper_arm','forearm_hand','thigh','shin_foot')):joints=[(spec['pivot'],6)]
   if name=='torso':joints=[([96,111],7),([136,114],7),([111,99],8)]
   for (x,y),r in joints:ImageDraw.Draw(partmask).ellipse((x-r,y-r,x+r,y+r),fill=255)
   layer=normalized.copy();layer.putalpha(ImageChops.multiply(normalized.getchannel('A'),partmask))
   path=folder/(name+'.png');layer.save(path);partmask.save(folder/(name+'-mask.png'))
   meta=dict(parent=spec['parent'],pivot=spec['pivot'],polygon=spec['poly'],overlap_source_circles=joints,source_sha256=digest)
   path.with_suffix('.svg').write_text(svg(layer,name,meta),'utf-8')
   parts[name]={**meta,'raster':path.relative_to(ART).as_posix(),'svg':path.with_suffix('.svg').relative_to(ART).as_posix(),
    'mask':(folder/(name+'-mask.png')).relative_to(ART).as_posix(),'sha256':sha(path)}
  contacts={}
  for side in ('l','r'):
   layer=Image.open(ART/parts['shin_foot_'+side]['raster']);data=np.asarray(layer.getchannel('A'))>=128
   ys,xs=np.where(data);bottom=int(ys.max());select=data[max(0,bottom-2):bottom+1];_,cx=np.where(select)
   contacts[side]=[int(round(cx.mean())),bottom]
  if skin=='ski_a':
   # Only this non-identity accessory is retained from the generated head area.
   gm=Image.new('L',raw.size);ImageDraw.Draw(gm).polygon([(588,151),(625,151),(669,177),(696,219),(698,282),(678,307),(645,291),(610,260),(579,207)],fill=255)
   goggles=raw.copy();goggles.putalpha(ImageChops.multiply(raw.getchannel('A'),gm));goggles=goggles.crop((575,145,702,310)).resize((17,22),Image.Resampling.LANCZOS)
   goggles.save(folder/'goggles-crop.png');full_goggles=Image.new('RGBA',CANVAS);full_goggles.alpha_composite(goggles,(151,33))
   full_goggles.save(folder/'goggles.png');full_goggles.getchannel('A').point(lambda x:255 if x else 0).save(folder/'goggles-mask.png')
   gmeta=dict(source_sha256=digest,source_polygon=[(588,151),(625,151),(669,177),(696,219),(698,282),(678,307),(645,291),(610,260),(579,207)],
    source_crop=[575,145,702,310],sampled_size=[17,22],paste_xy=[151,33],identity_role='Costume goggles accessory only; no generated face, cap logo or hair used as identity')
   (folder/'goggles.svg').write_text(svg(full_goggles,'ski-goggles-accessory',gmeta),'utf-8')
  result['skins'][skin]=dict(source=source.relative_to(ART).as_posix(),source_sha256=digest,parts=parts,
   sampling=dict(raw_core_bbox=list(core),garment_cut_y=480,scale=scale,paste_xy=[left,top],
     rule='Clothing neck-to-lowest-boot normalized to y98..224; generated face/hair removed; shared identity head keeps original proportions'),
   foot_contacts=contacts,grips=dict(l=[71,158],r=[159,151]),
   goggles=({**gmeta,'raster':'rig/ski/skins/ski_a/goggles.png','svg':'rig/ski/skins/ski_a/goggles.svg',
     'sha256':sha(folder/'goggles.png')} if skin=='ski_a' else None))
 (RIG/'rig.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8');return result
