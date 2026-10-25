"""Independent boot acting rig; source parts stay frozen, head and expression rotate together."""
import json
import math
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from rig_render import translate,turn,transformed
from boot_v2_sources import ART,OUT,SRC,PREVIEW,build as build_sources,sha,svg
from boot_v2_motion import KEYS,keyframe,solve


def prepare():
 sources=build_sources();rig=json.loads((ART/'rig/rig.json').read_text('utf-8'));parts=rig['views']['front']['parts']
 folder=OUT/'rig';folder.mkdir(parents=True,exist_ok=True);layers={};records={}
 for name,p in parts.items():
  if name in ('head','expression_neutral'):continue
  layers[name]=Image.open(ART/'rig'/p['raster']).convert('RGBA');records[name]=dict(path='rig/'+p['raster'],sha256=p['rgba_sha256'],operation='read-only source part')
 # The right sleeve is occluded by the original satchel. Complete it from the
 # same jacket's intact left sleeve only; no head, face, cap or lettering is mirrored.
 for name in ('upper_arm_r','forearm_hand_r'):
  other=name[:-1]+'l';mirrored=layers[other].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  complete=Image.new('RGBA',(256,256));complete.alpha_composite(mirrored,(1,0));layers[name]=complete
  records[name]=dict(source=records[other],operation='isolated same-costume sleeve mirror x=128; body/face/hat never mirrored')
 # Remove the old rest-arm residue from static layers, never from the bag itself.
 for name in ('torso','collar','jacket_flap'):
  alpha=layers[name].getchannel('A');ImageDraw.Draw(alpha).rectangle((162,151,255,175),fill=0);layers[name].putalpha(alpha)
 for name,im in layers.items():
  path=folder/(name+'.png');im.save(path);path.with_suffix('.svg').write_text(svg(im,name,records[name]),'utf-8')
 closed=layers['forearm_hand_r'].copy();cm=closed.getchannel('A');ImageDraw.Draw(cm).rectangle((0,0,255,155),fill=0);closed.putalpha(cm)
 cuff=layers['forearm_hand_r'].copy();cm=cuff.getchannel('A');ImageDraw.Draw(cm).rectangle((0,156,255,255),fill=0);cuff.putalpha(cm)
 palms={}
 for state,record in (('open',sources['palm']),('half',sources['half_palm'])):
  palm=Image.new('RGBA',(256,256));anchor=record['wrist_anchor']
  palm.alpha_composite(Image.open(ART/record['path']),(160-anchor[0],154-anchor[1]));palms[state]=palm
 for name,im in (('closed-hand',closed),('cuff',cuff),('open-palm',palms['open']),('half-palm',palms['half'])):
  source=sources['palm'] if name=='open-palm' else sources['half_palm'] if name=='half-palm' else records['forearm_hand_r']
  im.save(folder/(name+'.png'));(folder/(name+'.svg')).write_text(svg(im,name,dict(source=source,wrist=[160,154])),'utf-8')
 (folder/'recipe.json').write_text(json.dumps(dict(sources=sources,parts=records,policy='Only the isolated jacket sleeve is mirrored; no face/hat/lettering mirrored'),ensure_ascii=False,indent=2)+'\n','utf-8')
 return rig,layers,closed,cuff,palms,sources


def render(prepared,index,*,attempt=1):
 rig,layers,closed,cuff,palms,sources=prepared;key=keyframe(index);p=rig['views']['front']['parts']
 torso=turn(key['torso_angle'],[128,155]);right_shoulder=[151,106];right_elbow=[158,134];right_wrist=[160,154]
 a,b=solve(right_shoulder,right_elbow,right_wrist,key['goal'],torso)
 angles={'upper_arm_r':a,'forearm_hand_r':b,'shin_foot_r':-key['toe_angle'],
  'jacket_flap':1.5*math.sin(.5)+key['head_angle']*.2,'satchel':.7*math.sin(.3)+(-2 if 'bag' in key['label'] else 0)}
 matrices={'root':translate(0,0),'torso':torso}
 def matrix(name):
  if name not in matrices:
   parent=p[name]['parent'];pivot=p[name]['pivot']
   if name=='upper_arm_r':parent='torso';pivot=right_shoulder
   if name=='forearm_hand_r':parent='upper_arm_r';pivot=right_elbow
   matrices[name]=matrix(parent)@turn(angles.get(name,0),pivot)
  return matrices[name]
 posed={name:transformed(layer,matrix(name)) for name,layer in layers.items()}
 posed['forearm_hand_r']=transformed(cuff,matrix('forearm_hand_r'))
 hand=transformed(closed,matrix('forearm_hand_r'))
 wrist=matrix('forearm_hand_r')@np.array([*right_wrist,1])
 if key['palm']:
  hand_matrix=translate(wrist[0]-160,wrist[1]-154)@turn(key['palm_world_angle'],right_wrist)
  hand=transformed(palms[key['palm_state']],hand_matrix)
 # Whole official native expression heads share one rigid transform; no isolated
 # eye/mouth fragment is pasted into a different head, and the old coat is masked.
 hm=torso@translate(0,key['head_dy'])@turn(key['head_angle'],[128,97])
 head=transformed(Image.open(SRC/('head-'+key['expression']+'.png')).convert('RGBA'),hm)
 canvas=Image.new('RGBA',(256,256))
 order=['thigh_l','shin_foot_l','thigh_r','shin_foot_r','upper_arm_l','forearm_hand_l',
  'upper_arm_r','torso','jacket_flap','satchel','collar','forearm_hand_r']
 for name in order:canvas.alpha_composite(posed[name])
 canvas.alpha_composite(head);canvas.alpha_composite(hand)
 box=canvas.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
 report={**key,'upper_arm_r_degrees':a,'forearm_r_degrees':b,'world_wrist':[float(v) for v in wrist[:2]],
  'head_matrix':hm.tolist(),'head_rotation_degrees':key['head_angle']+key['torso_angle'],
  'head_det':float(np.linalg.det(hm[:2,:2])),'head_orthogonal_error':float(np.max(np.abs(hm[:2,:2].T@hm[:2,:2]-np.eye(2)))),
  'head_resampler':'BICUBIC rigid rotation and translation; no claim of per-pixel preservation after resampling',
  'bbox':list(box),'frame_root_translation':[0,0]}
 return canvas,report
