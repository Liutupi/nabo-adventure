"""Rear-three-quarter ski cutout, unchanged look-back head, 56px body contract."""
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];ART=BASE/'art';ROOT=BASE.parents[1]
GAME=ART/'games/ski';RIG=ART/'rig/ski';PREVIEW=ART/'preview/ski';CANVAS=(256,256);ANCHOR=[128,224]
LOCKS={'ski_a':'1d9ee3833e9a34c6c3513e6ed3d7db6cf02c840d94bca4fd45f9fa6268ee1a46',
 'ski_b':'6812f66d3094966da07d1c7d8bab490a12147955d880d88b1bbdd53a43f20942'}
PARTS={
 'secondary':dict(parent='torso',pivot=[130,102],poly=[(128,97),(145,95),(176,111),(169,119),(139,111)]),
 'upper_arm_l':dict(parent='torso',pivot=[96,111],poly=[(84,105),(102,109),(94,133),(88,143),(73,140),(76,125)]),
 'forearm_hand_l':dict(parent='upper_arm_l',pivot=[83,137],poly=[(73,129),(95,136),(88,159),(81,171),(60,172),(59,153)]),
 'upper_arm_r':dict(parent='torso',pivot=[136,114],poly=[(129,109),(143,111),(159,131),(164,142),(148,147),(138,132)]),
 'forearm_hand_r':dict(parent='upper_arm_r',pivot=[150,136],poly=[(145,130),(166,134),(172,151),(165,165),(146,162),(140,148)]),
 'thigh_l':dict(parent='root',pivot=[111,154],poly=[(0,151),(132,151),(132,192),(0,192)]),
 'shin_foot_l':dict(parent='thigh_l',pivot=[108,184],poly=[(0,181),(132,181),(132,256),(0,256)]),
 'thigh_r':dict(parent='root',pivot=[135,155],poly=[(131,150),(256,150),(256,187),(131,187)]),
 'shin_foot_r':dict(parent='thigh_r',pivot=[143,181],poly=[(131,178),(256,178),(256,256),(131,256)]),
 'torso':dict(parent='root',pivot=[122,154],poly=None),
}
ORDER=['thigh_l','shin_foot_l','thigh_r','shin_foot_r','upper_arm_l','forearm_hand_l',
 'upper_arm_r','forearm_hand_r','torso','secondary','head','goggles']
SPECS={'straight':dict(count=6,loop=True,target=56),'lean_left':dict(count=4,loop=False,target=56),
 'lean_right':dict(count=4,loop=False,target=56),'jump':dict(count=6,loop=False,target=56),
 'fall':dict(count=8,loop=False,target=56),'finish':dict(count=6,loop=False,target=56),
 'settlement_cheer':dict(count=8,loop=False,target=72)}
ANIMS={'ski_a':list(SPECS),'ski_b':['straight','settlement_cheer']}


def pose(name,i):
 import math
 a={};lift=0;slump=0;ski=True;poles=True
 if name=='straight':
  s=math.sin(i*2*math.pi/6);a={'torso':.5*s,'upper_arm_l':1.4*s,'upper_arm_r':-1.3*s,'secondary':3*math.sin(i*2*math.pi/6+.4)}
 elif name in ('lean_left','lean_right'):
  sign=-1 if name.endswith('left') else 1;v=[0,.4,.8,1][i]
  a={'torso':sign*7*v,'thigh_l':sign*5*v,'thigh_r':sign*5*v,'shin_foot_l':-sign*4*v,
     'shin_foot_r':-sign*4*v,'upper_arm_l':sign*7*v,'upper_arm_r':sign*7*v,'secondary':-sign*8*v}
 elif name=='jump':
  v=[0,.4,1,.85,.3,0][i];lift=round(13*v)
  a={'thigh_l':7*v,'thigh_r':-5*v,'shin_foot_l':-9*v,'shin_foot_r':7*v,
     'upper_arm_l':-8*v,'upper_arm_r':8*v,'secondary':-8*v}
 elif name=='fall':
  from ski_fall import pose as fall_pose
  return fall_pose(i)
 elif name in ('finish','settlement_cheer'):
  v=([0,.45,1,.75,.3,0] if name=='finish' else [0,.3,.75,1,.9,.55,.2,0])[i]
  a={'upper_arm_l':53*v,'forearm_hand_l':68*v,'upper_arm_r':-12*v,'secondary':-8*v}
  if name=='settlement_cheer':lift=round(3*v);ski=False;poles=False
 else:raise ValueError(name)
 if name!='straight':a['secondary']=a.get('secondary',0)+3*math.sin(.4)
 return dict(angles=a,lift=lift,torso_slump=slump,skis=ski,poles=poles)
