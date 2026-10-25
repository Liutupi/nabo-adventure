"""Independent saved-file contracts: identity pixels, clips, palettes and source hashes."""
import base64
import io
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageChops
from post_config import ART,RIG,PREVIEW,SKIN_ANIMS,SPECS
from post_rig import sha
from post_cab_verify import check_cab


def load(path):return Image.open(path).convert('RGBA')


def main():
 manifest=json.loads((ART/'post-manifest.json').read_text('utf-8'));rig=json.loads((RIG/'rig.json').read_text('utf-8'))
 checks=[];entries={(e['skin'],e['name']):e for e in manifest['animations']};rows=[]
 expected={(skin,name) for skin,names in SKIN_ANIMS.items() for name in names}
 assert expected<=set(entries)
 head=Image.new('RGBA',(256,256))
 for h in rig['common_head']:
  assert sha(ART/h['path'])==h['sha256']
  im=load(ART/h['path']);im.putalpha(ImageChops.multiply(im.getchannel('A'),Image.open(ART/h['local_alpha_mask'])))
  head.alpha_composite(im)
 headpixels=np.asarray(head);yy,xx=np.indices((256,256));protected=(yy<94)&(xx>=104)&(xx<=153)&(headpixels[:,:,3]>=250)
 validation=json.loads((PREVIEW/'validation.json').read_text('utf-8'))
 reports={(x['skin'],x['name']):x for x in validation['checks']}
 for key in sorted(expected):
  e=entries[key];skin,name=key;count=SPECS[name]['count'];assert len(e['frames'])==len(e['runtime_frames'])==count
  assert e['canvas']==[256,256] and e['anchor']==([128,224] if e['target_height_px']==72 else [128,160])
  assert e['fps']==12 and isinstance(e['loop'],bool)
  source=rig['skins'][skin];assert sha(ART/source['source'])==source['source_sha256']
  runtime=[]
  for field,hashfield,size in (('frames','frame_sha256',[256,256]),('masters','master_sha256',[256,256]),('runtime_frames','runtime_sha256',e['runtime_canvas'])):
   frames=[]
   for i,(path,digest) in enumerate(zip(e[field],e[hashfield])):
    assert sha(ART/path)==digest;im=load(ART/path);assert list(im.size)==size;frames.append(im)
    if field!='masters':assert set(np.unique(np.asarray(im)[:,:,3]))=={0,255}
    else:
     hx,hy=reports[key]['frame_reports'][i]['head_translation'];data=np.asarray(im)
     ys,xs=np.where(protected);assert np.array_equal(data[ys+hy,xs+hx,:3],headpixels[ys,xs,:3]),(key,i,'source identity RGB changed')
   if field!='masters':
    colours=set().union(*[set(map(tuple,np.asarray(f).reshape(-1,4))) for f in frames]);assert len(colours)<=64
   if field=='runtime_frames':runtime=frames
  if not e['loop'] and name!='throw':assert np.array_equal(np.asarray(runtime[0]),np.asarray(runtime[-1]))
  checks.append(dict(skin=skin,name=name,frames=count,source_face_cap_rgb_preserved=True,
   neutral_endpoints_equal=bool(not e['loop'] and name!='throw'),passed=True))
 for skin,names in SKIN_ANIMS.items():
  neutral=load(ART/entries[skin,'idle']['frames'][0])
  for name in names:
   if name not in ('idle','throw','settlement_cheer'):
    assert np.array_equal(np.asarray(neutral),np.asarray(load(ART/entries[skin,name]['frames'][0])))
 for skin,source in rig['skins'].items():
  original=load(RIG/(skin+'-normalized-master.png'))
  for part in source['parts'].values():
   raster=load(ART/part['raster']);mask=Image.open(ART/part['mask']);expected_layer=original.copy()
   expected_layer.putalpha(ImageChops.multiply(original.getchannel('A'),mask))
   assert np.array_equal(np.asarray(raster),np.asarray(expected_layer))
   node=ET.parse(ART/part['svg']).find('{http://www.w3.org/2000/svg}image')
   embedded=load(io.BytesIO(base64.b64decode(node.attrib['href'].split(',')[1])))
   assert np.array_equal(np.asarray(embedded),np.asarray(raster))
 for e in manifest['animations']:
  if e['skin']=='post_props' and e['name']=='wheel-cycle':
   assert len(e['runtime_frames'])==4 and e['loop'] and e['fps']==12
   assert len(set(e['runtime_sha256']))==4,'Wheel cycle must have four distinct states'
 for a in manifest['assets']:
  assert sha(ART/a['path'])==a['sha256'];assert list(load(ART/a['path']).size)==a['size']
  assert sha(ART/a['source_svg'])==a['source_sha256']
  assert a['qa']['passed'] and a['qa']['rgba_colors']<=a['color_limit']<=64
  ET.parse(ART/a['source_svg'])
 cab=check_cab(manifest,head,reports)
 result=dict(passed=True,character_clips=len(checks),character_frames=sum(x['frames'] for x in checks),
  cab_clearance_frames=cab['head_clearance_frames'],fixed_roof_cord_frames=cab['cord_frames'],
  shared_source_head_rgb_preserved=True,all_svg_slices_match_png=True,checks=checks,
  caveat='Identity RGB checks apply to high-color masters; formal/runtime palette reduction is explicitly lossy. Host checks do not imply user acceptance.')
 (PREVIEW/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))


if __name__=='__main__':main()
