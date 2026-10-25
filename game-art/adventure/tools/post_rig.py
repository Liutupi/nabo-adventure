"""Separate new clothing pixels; reference the unchanged common head read-only."""
import base64
import copy
import hashlib
import io
import json
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from post_config import ART,GAME,RIG,CANVAS,SOURCES,SOURCE_LOCKS,HEAD_FILES,PARTS,DRAW_ORDER


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def svg(image,name,metadata):
 stream=io.BytesIO();image.save(stream,'PNG')
 encoded=base64.b64encode(stream.getvalue()).decode('ascii')
 return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">\n'
  f'<title>{name}: immutable source-pixel cutout</title>\n<metadata>'+json.dumps(metadata)+'</metadata>\n'
  f'<image width="256" height="256" href="data:image/png;base64,{encoded}"/>\n</svg>\n')


def normalize(source):
 core=source.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
 x0,y0,x1,y1=core;box=[x0-2,y0-2,x1+2,y1+2];scale=208/(y1-y0)
 image=source.crop(box);size=(round(image.width*scale),round(image.height*scale))
 sample=image.resize(size,Image.Resampling.LANCZOS)
 left=128-round((x0+x1-2*box[0])*scale/2);top=224-round((y1-box[1])*scale)
 result=Image.new('RGBA',CANVAS);result.alpha_composite(sample,(left,top))
 return result,dict(core_bbox=list(core),sampling_bbox=box,scale=scale,sampled_size=list(size),
  paste_xy=[left,top],canvas=list(CANVAS),anchor=[128,224],core_height=208,
  alpha_policy='Source RGBA retained; core threshold only chooses crop; final export thresholds alpha at 128.')


def mask_poly(points):
 mask=Image.new('L',CANVAS);ImageDraw.Draw(mask).polygon(points,fill=255);return mask


def build():
 RIG.mkdir(parents=True,exist_ok=True)
 common=json.loads((ART/'rig/rig.json').read_text('utf-8'))
 headparts=common['views']['front']['parts'];heads=[]
 headmask=Image.new('L',CANVAS);md=ImageDraw.Draw(headmask)
 md.rectangle((0,0,255,93),fill=255);md.rectangle((121,94,137,100),fill=255)
 headmask.save(RIG/'head-garment-exclusion-mask.png')
 for name,path in zip(('head','expression_neutral'),HEAD_FILES):
  assert sha(ART/path)==headparts[name]['rgba_sha256'],'Frozen common head changed; inspect before continuing'
  heads.append(dict(name=name,path=path,sha256=sha(ART/path),pivot=[128,97],parent='rigid_head',
   local_alpha_mask='rig/post/head-garment-exclusion-mask.png'))
 result=dict(version=1,canvas=list(CANVAS),anchors=dict(half=[128,160],full=[128,224]),fps=12,
  common_head=heads,common_source_sha256=common['source_sha256'],draw_order=DRAW_ORDER,
  identity_policy='No generated master head is used. Common front head and neutral expression share one rigid integer translation; never mirror or redraw.',
  garment_exclusion=dict(preserve_all_rows=[0,93],preserve_neck_rect=[121,94,137,100],
   reason='Frozen head slice includes old travel collar at its bottom; POST alpha-only mask excludes that garment. Common files and all retained RGB remain unchanged.'),
  representation='New costume raster pixels in editable SVG wrappers plus explicit joint masks; no new vector character.',skins={})
 result['cab_attachment']=dict(coordinate_space='locomotive native top-left (96x88)',driver_chest=[25,49],
  window=[10,8,39,49],roof_pulley=[12,7],grip_bone='forearm_hand_l',source_grip_xy=[96,161],
  animated_contact='post-manifest animations: post_props/whistle-cord.contacts',
  layering='wheel/body/cord/actor/foreground; use cord frame0 when not whistling')
 for skin,filename in SOURCES.items():
  source=GAME/'source'/filename;assert sha(source)==SOURCE_LOCKS[skin]
  raw=Image.open(source).convert('RGBA');normalized,sampling=normalize(raw)
  review=Image.new('RGB',raw.size,'#f6e2b4');review.paste(raw,(0,0),raw)
  review.resize((627,627)).save(source.with_name(source.name.replace('-master','-review')))
  normalized.save(RIG/f'{skin}-normalized-master.png')
  specs=copy.deepcopy(PARTS)
  if skin=='post_b':specs['secondary'].update(pivot=[147,141],poly=[(135,139),(149,135),(157,143),(157,158),(143,161),(136,153)])
  folder=RIG/'skins'/skin;folder.mkdir(parents=True,exist_ok=True)
  remaining=Image.new('L',CANVAS);ImageDraw.Draw(remaining).rectangle((0,98,255,255),fill=255)
  pieces={}
  # The two costume accents and collar are cut before the torso residue.
  order=['secondary','collar',*[n for n in specs if n not in ('secondary','collar','torso')],'torso']
  for name in order:
   spec=specs[name];region=mask_poly(spec['poly']) if spec['poly'] else remaining.copy()
   completion=False
   if skin=='post_a' and name.startswith('forearm_hand'):
    # Original pink fingertips extend a few pixels beyond the polygon. Assign
    # those existing pixels to the moving hand, never leave them on the torso.
    data=np.asarray(normalized).astype(int);yy,xx=np.indices((256,256))
    side=(xx<112) if name.endswith('_l') else (xx>149)
    pink=(data[:,:,0]-data[:,:,1]>15)&(data[:,:,0]-data[:,:,2]>30)
    extra=(side&(yy>=150)&(yy<=175)&pink).astype('uint8')*255
    region=ImageChops.lighter(region,Image.fromarray(extra));completion=True
    # Navy trouser edges must stay with the legs when a lowered hand swings.
    outer=(xx<105) if name.endswith('_l') else (xx>157)
    keep=np.where((yy>=156)&~(pink|outer),0,255).astype('uint8')
    region=ImageChops.multiply(region,Image.fromarray(keep))
   mask=ImageChops.multiply(region,remaining);remaining=ImageChops.subtract(remaining,mask)
   joints=[]
   if name.startswith(('upper_arm','forearm_hand','thigh','shin_foot')):joints=[(spec['pivot'],6)]
   elif name=='torso':joints=[([111,108],8),([148,108],8),([128,103],8)]
   for (x,y),radius in joints:ImageDraw.Draw(mask).ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)
   image=normalized.copy();image.putalpha(ImageChops.multiply(image.getchannel('A'),mask))
   path=folder/(name+'.png');image.save(path);mask.save(folder/(name+'-mask.png'))
   meta=dict(source_sha256=sha(source),parent=spec['parent'],pivot=spec['pivot'],polygon=spec['poly'],
    source_overlap_circles=joints,original_pink_fingertip_completion=completion,
    pixel_policy='Original normalized clothing RGB under explicit mask; source head excluded')
   path.with_suffix('.svg').write_text(svg(image,name,meta),'utf-8')
   pieces[name]={**meta,'raster':path.relative_to(ART).as_posix(),'svg':path.with_suffix('.svg').relative_to(ART).as_posix(),
    'mask':(folder/(name+'-mask.png')).relative_to(ART).as_posix(),'sha256':sha(path),'bbox':image.getchannel('A').getbbox()}
   if name=='forearm_hand_l':pieces[name]['grip_point']=[96,161]
  result['skins'][skin]=dict(source=source.relative_to(ART).as_posix(),source_sha256=sha(source),sampling=sampling,parts=pieces)
 (RIG/'rig.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 return result
