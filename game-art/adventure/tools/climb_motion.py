"""Explicit 12fps CLIMB poses and endpoints; engine handles game translation."""
import math
from climb_rig import render

COUNTS={'grip_idle':6,'switch_grab':6,'charge':4,'jump':6,'slide':6,'summit_cheer':8,'settlement_cheer':8}


def grip(side):
    if side=='left':return {'upper_arm_l':104,'forearm_hand_l':24,'upper_arm_r':67,'forearm_hand_r':26,
                            'thigh_l':26,'shin_foot_l':-42,'thigh_r':-12,'shin_foot_r':24,'jacket_flap':-3}
    return {'upper_arm_l':-67,'forearm_hand_l':-26,'upper_arm_r':-104,'forearm_hand_r':-24,
            'thigh_l':12,'shin_foot_l':-24,'thigh_r':-26,'shin_foot_r':42,'jacket_flap':3}


def blend(a,b,t):return {key:a.get(key,0)*(1-t)+b.get(key,0)*t for key in set(a)|set(b)}
def smooth(t):return t*t*(3-2*t)


def key(anim,side,index):
    count=COUNTS[anim];t=index/(count-1);s=math.sin(math.pi*t);target='right' if side=='left' else 'left'
    base=grip(side);view=side;offset=(0,0)
    if anim=='grip_idle':
        phase=2*math.pi*index/count
        base['forearm_hand_l']+=1.2*math.sin(phase);base['forearm_hand_r']-=1.2*math.sin(phase)
        base['jacket_flap']+=2*math.sin(phase)
    elif anim=='switch_grab':
        base=blend(base,grip(target),smooth(t));view=side if index<2 else 'front' if index<4 else target
        base['shin_foot_l']-=18*s;base['shin_foot_r']+=18*s
    elif anim=='charge':
        base['thigh_l']+=12*smooth(t);base['shin_foot_l']-=18*smooth(t)
        base['thigh_r']-=12*smooth(t);base['shin_foot_r']+=18*smooth(t)
        base['forearm_hand_l']+=8*smooth(t);base['forearm_hand_r']-=8*smooth(t)
        base['jacket_flap']+=4*smooth(t)
    elif anim=='jump':
        charged,_,_=key('charge',side,3);base=blend(charged,grip(side),smooth(t))
        base['thigh_l']-=16*s;base['thigh_r']+=16*s
        base['forearm_hand_l']+=12*s;base['forearm_hand_r']-=12*s
        base['jacket_flap']-=6*s
    elif anim=='slide':
        base['upper_arm_l']-=18*s;base['upper_arm_r']+=18*s
        base['shin_foot_l']-=22*s;base['shin_foot_r']+=22*s
        base['jacket_flap']+=8*s
    elif anim=='summit_cheer':
        neutral={};base=blend(grip(side),neutral,smooth(min(1,t*2)))
        lift=math.sin(math.pi*max(0,(t-.25)/.75)) if t>.25 else 0
        base['upper_arm_l']=base.get('upper_arm_l',0)+115*lift
        base['forearm_hand_l']=base.get('forearm_hand_l',0)+40*lift
        base['upper_arm_r']=base.get('upper_arm_r',0)-70*lift
        base['jacket_flap']=base.get('jacket_flap',0)+5*s
    elif anim=='settlement_cheer':
        view='front';lift=[0,.25,.65,1,.95,.6,.2,0][index]
        base={'upper_arm_l':115*lift,'forearm_hand_l':40*lift,'upper_arm_r':-65*lift,
              'forearm_hand_r':-25*lift,'jacket_flap':5*lift}
    else:raise ValueError(anim)
    return base,view,offset


def clips(rig):
    result={}
    for skin in ('climb_a','climb_b'):
        names=list(COUNTS) if skin=='climb_a' else ['grip_idle','settlement_cheer']
        for anim in names:
            for side in ('front',) if anim=='settlement_cheer' else ('left','right'):
                name=anim if side=='front' else anim+'_'+side
                frames=[];reports=[];keys=[]
                for i in range(COUNTS[anim]):
                    angles,view,offset=key(anim,side,i);frame,report=render(rig,skin,view,angles,offset)
                    frames.append(frame);reports.append(report);keys.append({'angles':angles,'view':view,'offset':offset})
                result[(skin,name)]={'skin':skin,'name':name,'action':anim,'facing':side,'frames':frames,'reports':reports,
                                     'keyframes':keys,'height':72 if side=='front' else 60,'loop':anim=='grip_idle'}
    return result
