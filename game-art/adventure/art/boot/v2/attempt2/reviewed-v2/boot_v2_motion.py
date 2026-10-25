"""Five one-shot acting beats, not a larger periodic forearm wave."""
import math
import numpy as np

# Poses are unique exposures on a 12fps clock; holds total 53 ticks = 4.416667s.
# Right is screen-right, i.e. NABO's anatomical left, matching the reused palm.
KEYS=[
 (0,'ready',[162,153],0,0,0,'open',False,0),
 (2,'bag-approach',[158,145],-1,-2,0,'open',False,0),
 (4,'take-strap',[151,133],-2,-3,1,'half',False,0),
 (7,'bag-anticipation',[151,130],-2,-3,1,'closed',False,0),
 (9,'look-up',[155,135],-1,-1,0,'half',False,0),
 (10,'raise-to-hat',[173,107],0,2,0,'open',False,0),
 (12,'touch-brim',[170,62],0,6,4,'open',False,0),
 (14,'hat-tip',[170,62],0,6,4,'half',False,0),
 (16,'release-hat',[180,80],0,3,1,'open',False,0),
 (17,'open-palm',[187,94],0,2,0,'open',True,-4),
 (19,'wave-out',[190,94],.6,4,0,'open',True,-14),
 (21,'wave-in',[190,94],0,-2,0,'half',True,14),
 (22,'warm-blink',[190,94],-.5,-4,1,'closed',True,-10),
 (23,'wave-return',[190,94],0,-3,0,'half',True,10),
 (24,'greet-open',[190,94],0,0,0,'open',True,-5),
 (26,'lower-wave',[186,98],0,2,0,'open',True,0),
 (28,'offer-hand',[185,115],-1,0,0,'open',True,45),
 (30,'invite',[181,128],-2,-4,1,'open',True,78),
 (33,'invite-hold',[178,130],-2,-5,1,'half',True,80),
 (35,'invite-nod',[178,130],-2,-5,2,'closed',True,80),
 (36,'invite-rise',[178,130],-1,-3,1,'half',True,76),
 (37,'invitation-settle',[178,130],-1,-3,0,'open',True,76),
 (39,'withdraw',[165,140],0,0,0,'open',True,35),
 (41,'return-to-cuff',[159,148],0,1,0,'open',False,0),
 (43,'toe-to-route',[162,153],1,4,0,'open',False,0),
 (45,'departure-nod',[162,153],1,4,3,'half',False,0),
 (47,'steady',[162,153],.4,1,1,'open',False,0),
 (49,'idle-arrival',[162,153],0,0,0,'open',False,0),
 (51,'idle-hold',[162,153],0,0,0,'open',False,0),
]


def normalized(angle):return (angle+180)%360-180


def solve(shoulder,elbow,wrist,goal,parent):
 local=np.linalg.inv(parent)@np.array([*goal,1]);target=local[:2]-shoulder
 l1=np.linalg.norm(np.array(elbow)-shoulder);l2=np.linalg.norm(np.array(wrist)-elbow)
 distance=min(float(np.linalg.norm(target)),l1+l2-.08);direction=math.atan2(target[1],target[0])
 spread=math.acos(max(-1,min(1,(distance*distance+l1*l1-l2*l2)/(2*distance*l1))))
 base1=math.atan2(elbow[1]-shoulder[1],elbow[0]-shoulder[0]);base2=math.atan2(wrist[1]-elbow[1],wrist[0]-elbow[0])
 choices=[]
 for theta in (direction+spread,direction-spread):
  ep=np.array(shoulder)+l1*np.array([math.cos(theta),math.sin(theta)])
  fore=math.atan2(local[1]-ep[1],local[0]-ep[0]);a=normalized(math.degrees(theta-base1));b=normalized(math.degrees(fore-base2)-a)
  choices.append((ep[0],a,b))
 _,a,b=max(choices)
 return a,b


def keyframe(index):
 tick,label,goal,torso,head,dy,expression,palm,wave=KEYS[index]
 duration=(KEYS[index+1][0] if index+1<len(KEYS) else 53)-tick
 toe=7 if tick in (43,45) else 3 if tick==47 else 0
 return dict(index=index,tick=tick,duration_ticks=duration,label=label,goal=goal,
  torso_angle=torso,head_angle=head,head_dy=dy,expression=expression,palm=palm,palm_world_angle=wave,toe_angle=toe)
