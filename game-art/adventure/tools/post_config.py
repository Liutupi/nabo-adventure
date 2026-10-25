"""POST-only identity locks, source-pixel regions and deterministic motion contract."""
from pathlib import Path

BASE=Path(__file__).resolve().parents[1];ART=BASE/'art';ROOT=BASE.parents[1]
GAME=ART/'games/post';RIG=ART/'rig/post';PREVIEW=ART/'preview/post'
CANVAS=(256,256);FULL_ANCHOR=(128,224);HALF_ANCHOR=(128,160)
SOURCES={'post_a':'post-a-master.png','post_b':'post-b-master.png'}
SOURCE_LOCKS={'post_a':'a533a3976c3e2cae31b9e860860e1b0bd81b9b1488eaff5e70fded85bfac3f93',
 'post_b':'5adbe4af4f2d8532b066138576382b179e8daec6ea4099f985233ce3db14d899'}
HEAD_FILES=['rig/common/front/head.png','rig/common/front/expression_neutral.png']
PARTS={
 'upper_arm_l':dict(parent='torso',pivot=[111,108],poly=[(104,103),(118,105),(111,128),(104,147),(85,145),(88,120)]),
 'forearm_hand_l':dict(parent='upper_arm_l',pivot=[98,140],poly=[(84,134),(106,134),(108,153),(105,173),(84,173),(82,149)]),
 'upper_arm_r':dict(parent='torso',pivot=[148,108],poly=[(141,104),(154,101),(172,121),(174,146),(153,147),(144,126)]),
 'forearm_hand_r':dict(parent='upper_arm_r',pivot=[161,140],poly=[(153,135),(177,133),(178,155),(175,174),(153,174),(151,149)]),
 'thigh_l':dict(parent='root',pivot=[115,157],poly=[(0,153),(128,153),(128,188),(0,188)]),
 'shin_foot_l':dict(parent='thigh_l',pivot=[115,183],poly=[(0,180),(128,180),(128,256),(0,256)]),
 'thigh_r':dict(parent='root',pivot=[141,157],poly=[(127,153),(256,153),(256,188),(127,188)]),
 'shin_foot_r':dict(parent='thigh_r',pivot=[141,183],poly=[(127,180),(256,180),(256,256),(127,256)]),
 'torso':dict(parent='root',pivot=[128,155],poly=None),
 'secondary':dict(parent='torso',pivot=[136,110],poly=[(130,108),(138,109),(143,124),(136,122)]),
 'collar':dict(parent='torso',pivot=[128,103],poly=[(118,98),(138,98),(144,111),(134,116),(115,111)]),
}
DRAW_ORDER=['thigh_l','shin_foot_l','thigh_r','shin_foot_r','upper_arm_l','forearm_hand_l',
 'upper_arm_r','forearm_hand_r','torso','secondary','collar','head']
SPECS={
 'idle':dict(count=6,loop=True,target=40),
 'whistle':dict(count=6,loop=False,target=40),
 'throw':dict(count=6,loop=False,target=40),
 'hit':dict(count=6,loop=False,target=40),
 'delivered':dict(count=6,loop=False,target=40),
 'settlement_cheer':dict(count=8,loop=False,target=72),
}
SKIN_ANIMS={'post_a':list(SPECS),'post_b':['idle','delivered']}


def pose(name,index):
 import math
 phase=2*math.pi*index/6;beat=[0,.45,1,.72,.26,0][index] if index<6 else 0
 angles={};shift=[0,0];head=[0,0];envelope=False;rope=False
 if name=='idle':
  angles={'upper_arm_l':.7*math.sin(phase),'upper_arm_r':-.6*math.sin(phase),
          'secondary':2*math.sin(phase+.4)}
 elif name=='whistle':
  # Raise, grasp, pull and return. The rope is a held accessory, never a glow/trail.
  angles={'upper_arm_l':28*beat,'forearm_hand_l':110*beat,'secondary':-4*beat}
  rope=index in (1,2,3,4)
 elif name=='throw':
  angles={'upper_arm_l':[0,-10,15,70,25,0][index],
          'forearm_hand_l':[0,20,40,-45,-10,0][index],'secondary':5*beat}
  envelope=index<3
 elif name=='hit':
  recoil=[0,-1,1,-.6,.2,0][index]
  angles={'torso':6*recoil,'upper_arm_l':-10*recoil,'upper_arm_r':8*recoil,
          'forearm_hand_l':-6*recoil,'secondary':10*recoil}
 elif name=='delivered':
  angles={'upper_arm_l':65*beat,'forearm_hand_l':105*beat,'upper_arm_r':-2*beat,'secondary':-6*beat}
 elif name=='settlement_cheer':
  lift=[0,.28,.76,1,.9,.55,.16,0][index]
  angles={'upper_arm_l':70*lift,'forearm_hand_l':110*lift,'upper_arm_r':-18*lift,
          'forearm_hand_r':-30*lift,'secondary':-6*lift}
  shift=[0,-[0,1,3,4,3,1,0,0][index]]
 else:raise ValueError(name)
 if name!='idle':angles['secondary']=angles.get('secondary',0)+2*math.sin(.4)
 return dict(angles=angles,shift=shift,head_offset=head,envelope=envelope,rope=rope)
