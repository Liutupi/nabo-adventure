"""Pose source-pixel bones while holding the shared NABO head rigid and readable."""
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from rig_render import translate,turn,transformed
from post_config import ART,CANVAS,SPECS,pose


def render(rig,skin,anim,index):
 parts=rig['skins'][skin]['parts'];key=pose(anim,index);angles=key['angles']
 matrices={'root':translate(*key['shift'])}
 def matrix(name):
  if name not in matrices:
   spec=parts[name];matrices[name]=matrix(spec['parent'])@turn(angles.get(name,0),spec['pivot'])
  return matrices[name]
 layers={name:transformed(Image.open(ART/spec['raster']).convert('RGBA'),matrix(name)) for name,spec in parts.items()}
 # The collar may rock, but the whole shared head only translates by integral pixels.
 p=matrix('torso')@np.array([128,97,1]);hx,hy=map(int,np.rint(p[:2]-[128,97]))
 head_matrix=translate(hx,hy)
 head=Image.new('RGBA',CANVAS)
 for source in rig['common_head']:
  source_pixels=Image.open(ART/source['path']).convert('RGBA')
  source_pixels.putalpha(ImageChops.multiply(source_pixels.getchannel('A'),Image.open(ART/source['local_alpha_mask'])))
  head.alpha_composite(transformed(source_pixels,head_matrix))
 layers['head']=head
 canvas=Image.new('RGBA',CANVAS);accessory=Image.new('RGBA',CANVAS)
 grip=matrix('forearm_hand_l')@np.array([*parts['forearm_hand_l']['grip_point'],1]);gx,gy=map(int,np.rint(grip[:2]))
 if key['envelope']:
  letter=Image.open(ART/'games/post/props/envelope-red.png').convert('RGBA').resize((22,17),Image.Resampling.LANCZOS)
  accessory.alpha_composite(letter,(gx-18,gy-15))
 # The whistle cord belongs to the cab, not to a hand-following character layer.
 # post_cab exports its fixed roof endpoint and the transformed hand endpoint.
 for name in rig['draw_order']:
  if name=='forearm_hand_l':canvas.alpha_composite(accessory)
  canvas.alpha_composite(layers[name])
 if SPECS[anim]['target']==40:
  mask=canvas.getchannel('A');ImageDraw.Draw(mask).rectangle((0,160,255,255),fill=0);canvas.putalpha(mask)
 # Quantization happens after the immutable high-color masters have been saved.
 overlaps={}
 for child,parent in (('upper_arm_l','torso'),('upper_arm_r','torso'),
                       ('forearm_hand_l','upper_arm_l'),('forearm_hand_r','upper_arm_r')):
  pivot=matrix(child)@np.array([*parts[child]['pivot'],1]);x,y=map(int,np.rint(pivot[:2]))
  a=np.asarray(layers[child].getchannel('A'))>=128;b=np.asarray(layers[parent].getchannel('A'))>=128
  box=(slice(max(0,y-8),min(256,y+9)),slice(max(0,x-8),min(256,x+9)))
  overlaps[child+'/'+parent]=int(np.count_nonzero(a[box]&b[box]))
 report=dict(frame=index,keyframe=key,head_translation=[hx,hy],head_rotation_degrees=0,
  head_rigid_integer_translation=True,head_source_sha256=[x['sha256'] for x in rig['common_head']],
  joint_overlap_pixels=overlaps,grip_xy=[gx,gy],bbox=canvas.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox())
 return canvas,report
