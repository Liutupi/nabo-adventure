"""Six A and three light-B clips. Prop attachments remain explicit layers."""
import math
from space_rig import render

COUNTS={'cabin_idle':6,'jet':4,'land':6,'hard_land':8,'plant_flag':8,'settlement_cheer':8}


def pose(name,index):
    count=COUNTS[name];t=index/(count-1);s=math.sin(math.pi*t);angles={}
    if name=='cabin_idle':
        p=2*math.pi*index/count
        angles={'upper_arm_l':1.2*math.sin(p),'upper_arm_r':-1.0*math.sin(p),
                'utility_hose':1.8*math.sin(p),'forearm_hand_r':.8*(math.cos(p)-1)}
    elif name=='jet':
        p=2*math.pi*index/count
        # Neutral phase0 permits exact idle->jet->idle body continuity.
        angles={'upper_arm_l':5*math.sin(p),'upper_arm_r':-5*math.sin(p),
                'forearm_hand_l':8*math.sin(p),'forearm_hand_r':-8*math.sin(p),
                'utility_hose':4*math.sin(p)}
    elif name=='land':
        angles={'thigh_l':10*s,'shin_foot_l':-16*s,'thigh_r':-10*s,'shin_foot_r':16*s,
                'upper_arm_l':8*s,'upper_arm_r':-8*s,'utility_hose':3*s}
    elif name=='hard_land':
        impact=[0,.5,1,.72,.42,.2,.07,0][index]
        angles={'thigh_l':18*impact,'shin_foot_l':-30*impact,'thigh_r':-18*impact,'shin_foot_r':30*impact,
                'upper_arm_l':48*impact,'forearm_hand_l':32*impact,'upper_arm_r':-40*impact,
                'forearm_hand_r':-22*impact,'utility_hose':8*impact}
    elif name=='plant_flag':
        # Reach out, lower the same pole with the glove, touch down, then let go.
        # A single reach envelope lifted the pole and teleported it down 8px at
        # the attachment switch. Explicit lowering frames keep the grip physical.
        reach=[0,.25,.6,1,1,.65,.3,0][index]
        angles={'upper_arm_r':[0,-9.5,-22.8,-38,-33,-24,-11.4,0][index],
                'forearm_hand_r':[0,-3.75,-9,-15,-8,0,-4.5,0][index],'upper_arm_l':4*reach,
                'utility_hose':-3*reach}
    elif name=='settlement_cheer':
        lift=[0,.25,.65,1,.95,.6,.2,0][index]
        angles={'upper_arm_l':112*lift,'forearm_hand_l':36*lift,'upper_arm_r':-68*lift,
                'forearm_hand_r':-25*lift,'utility_hose':4*lift}
    return angles


def clips(rig):
    result={}
    for skin in ('space_a','space_b'):
        names=list(COUNTS) if skin=='space_a' else ['cabin_idle','jet','settlement_cheer']
        for name in names:
            frames=[];reports=[];keys=[]
            for i in range(COUNTS[name]):
                angles=pose(name,i);frame,report=render(rig,skin,'front',angles)
                frames.append(frame);reports.append(report);keys.append({'frame':i,'view':'front','angles':angles})
            result[(skin,name)]={'skin':skin,'name':name,'frames':frames,'reports':reports,'keyframes':keys,
                                'facing':'front','height':72 if name=='settlement_cheer' else 56,
                                'loop':name in ('cabin_idle','jet')}
    return result
