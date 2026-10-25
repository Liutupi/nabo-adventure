"""Saved SKI contracts: contact geometry, exact retained identity, palettes and endpoints."""
import base64
import io
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageChops
from post_rig import sha
from ski_config import ART,RIG,PREVIEW,ANIMS,SPECS
from rig_render import transformed


def image(path):return Image.open(path).convert('RGBA')


def main():
 m=json.loads((ART/'ski-manifest.json').read_text('utf-8'));r=json.loads((RIG/'rig.json').read_text('utf-8'))
 v=json.loads((PREVIEW/'validation.json').read_text('utf-8'));reports={(q['skin'],q['name']):q for q in v['checks']}
 entries={(e['skin'],e['name']):e for e in m['animations']};expected={(s,n) for s,names in ANIMS.items() for n in names}
 assert set(entries)==expected
 head=Image.new('RGBA',(256,256))
 for p in r['common_head']:
  assert sha(ART/p['path'])==p['sha256'];im=image(ART/p['path'])
  im.putalpha(ImageChops.multiply(im.getchannel('A'),Image.open(ART/p['local_alpha_mask'])));head.alpha_composite(im)
 hp=np.asarray(head);yy,xx=np.indices((256,256));protected=(yy<94)&(xx>=98)&(xx<=145)&(hp[:,:,3]>=250)
 checks=[];contacts=0;grips=0;minimum_boot_overlap=999;minimum_grip_overlap=999
 for key in sorted(expected):
  e=entries[key];count=SPECS[key[1]]['count'];assert len(e['frames'])==len(e['runtime_frames'])==count
  assert e['canvas']==[256,256] and e['anchor']==[128,224] and e['fps']==12 and isinstance(e['loop'],bool)
  collections={}
  for field,hfield,size in (('masters','master_sha256',[256,256]),('frames','frame_sha256',[256,256]),('runtime_frames','runtime_sha256',e['runtime_canvas'])):
   frames=[]
   for i,(path,digest) in enumerate(zip(e[field],e[hfield])):
    assert sha(ART/path)==digest;im=image(ART/path);assert list(im.size)==size;frames.append(im)
    if field=='masters':
     report=reports[key]['reports'][i];hx,hy=report['head_translation'];ys,xs=np.where(protected)
     if key[1]=='fall' and report['keyframe']['fall_pitch']:
      matrix=np.array(report['head_matrix']);assert np.linalg.det(matrix[:2,:2])>0
      assert np.allclose(matrix[:2,:2].T@matrix[:2,:2],np.eye(2))
      expected_head=transformed(head,matrix);pm=Image.fromarray((protected*255).astype('uint8'),'L')
      protected_target=np.asarray(transformed(Image.merge('RGBA',(pm,pm,pm,pm)),matrix))[:,:,3]>=250
      gg=transformed(image(RIG/'skins/ski_a/goggles.png'),matrix)
      protected_target&=np.asarray(gg)[:,:,3]==0
      assert np.array_equal(np.asarray(im)[protected_target,:3],np.asarray(expected_head)[protected_target,:3]),(key,i,'rigid head resampling drift')
      assert report['head_and_expression_same_rigid_matrix']
     else:assert np.array_equal(np.asarray(im)[ys+hy,xs+hx,:3],hp[ys,xs,:3]),(key,i,'face/cap RGB drift')
     assert report['no_clipping']
     for contact in report['boot_board_contacts'].values():
      overlap=contact['actual_boot_board_overlap_pixels'];assert overlap>0 and contact['same_parent_transform']
      contacts+=1;minimum_boot_overlap=min(minimum_boot_overlap,overlap)
     for grip in report['mitten_pole_contacts'].values():
      overlap=grip['actual_mitten_pole_overlap_pixels'];assert overlap>0;grips+=1;minimum_grip_overlap=min(minimum_grip_overlap,overlap)
    else:assert set(np.unique(np.asarray(im)[:,:,3]))=={0,255}
   if field!='masters':assert len(set().union(*[set(map(tuple,np.asarray(f).reshape(-1,4))) for f in frames]))<=64
   collections[field]=frames
  if key[1] not in ('straight','lean_left','lean_right'):
   assert np.array_equal(np.asarray(collections['runtime_frames'][0]),np.asarray(collections['runtime_frames'][-1]))
  if key[1] in ('lean_left','lean_right','jump','fall','finish'):
   assert np.array_equal(np.asarray(collections['runtime_frames'][0]),np.asarray(image(ART/entries[key[0],'straight']['runtime_frames'][0])))
  checks.append(dict(skin=key[0],name=key[1],count=count,passed=True,
   retained_face_cap_rgb_exact_without_resampling=key[1]!='fall',rigid_positive_determinant_head=key[1]=='fall'))
 for skin,s in r['skins'].items():
  assert sha(ART/s['source'])==s['source_sha256'];original=image(RIG/(skin+'-normalized-clothes.png'))
  for part in s['parts'].values():
   actual=image(ART/part['raster']);target=original.copy();target.putalpha(ImageChops.multiply(original.getchannel('A'),Image.open(ART/part['mask'])))
   assert np.array_equal(np.asarray(actual),np.asarray(target))
   node=ET.parse(ART/part['svg']).find('{http://www.w3.org/2000/svg}image')
   embedded=image(io.BytesIO(base64.b64decode(node.attrib['href'].split(',')[1])))
   assert np.array_equal(np.asarray(embedded),np.asarray(actual))
 for a in m['assets']:
  assert sha(ART/a['path'])==a['sha256'] and list(image(ART/a['path']).size)==a['size'];ET.parse(ART/a['source_svg'])
  if a.get('shared_source'):
   shared=json.loads((ART/a['shared_manifest']).read_text('utf-8'))
   match=next(x for x in shared['assets'] if x['path']==a['path']);assert match['sha256']==a['sha256']
 result=dict(passed=True,clips=len(checks),character_frames=sum(c['count'] for c in checks),checks=checks,
  verified_boot_board_contacts=contacts,minimum_actual_boot_board_overlap=minimum_boot_overlap,
  verified_mitten_pole_contacts=grips,minimum_actual_mitten_pole_overlap=minimum_grip_overlap,
  retained_source_identity_rgb_exact=True,fall_head_rigid_rotation_with_bicubic_resampling=True,shared_snow_hashes_match=True,
  boundary='Source identity pixels are unchanged. Non-fall masters preserve core RGB; fall rigidly rotates the same head and expression with explicit resampling. Quantized delivery/runtime is lossy; contacts are host artwork evidence, not gameplay/hardware acceptance.')
 (PREVIEW/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))


if __name__=='__main__':main()
