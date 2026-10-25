"""SKI fall-only rigid tumble, articulated recovery and contact-based landing key."""
import numpy as np
from PIL import Image
from rig_render import translate,turn,transformed

PITCH=[0,12,36,62,62,36,12,0]
ENVELOPE=[0,.2,.6,1,1,.6,.2,0]


def pose(index):
    v=ENVELOPE[index];pitch=PITCH[index]
    angles={'torso':0,'thigh_l':-166*v,'thigh_r':90*v,
            # Keep each board attached to its boot, with folded knees. The far
            # board rises during impact rather than pinning both to the snow.
            'shin_foot_l':-pitch+166*v,'shin_foot_r':-pitch-115*v,
            'upper_arm_l':20*v,'forearm_hand_l':-12*v,
            'upper_arm_r':-48*v,'forearm_hand_r':-10*v,
            'secondary':16*v+3*np.sin(.4)}
    return {'angles':angles,'lift':0,'torso_slump':0,'skis':True,'poles':True,
            'fall_pitch':pitch,'fall_envelope':v,'fall_phase':['neutral','lose-balance','tumble','snow-contact','snow-contact','push-up','regain-balance','neutral'][index]}


def root(rig,skin,key,art):
    # The contact solution is derived once from the peak right mitten pixels,
    # then eased by explicit keyframes. It is not per-frame bbox recentering.
    part=rig['skins'][skin]['parts']['forearm_hand_r']
    source=Image.open(art/part['raster']).convert('RGBA');pixels=np.asarray(source).copy();pixels[:150,:,3]=0
    peak=turn(62,(122,154))@turn(-48,(136,114))@turn(-10,(150,136))
    alpha=np.asarray(transformed(Image.fromarray(pixels),peak))[:,:,3]>=128
    ys,xs=np.where(alpha);dy=234-int(ys.max()+1)
    v=key['fall_envelope'];shift=[round(-20*v),round(dy*v)]
    matrix=translate(*shift)@turn(key['fall_pitch'],(122,154))
    return matrix,{'peak_ground_edge_y':234,'peak_contact_y_translation':dy,'root_shift':shift,
                   'rigid_pitch_degrees':key['fall_pitch'],'rigid_determinant':float(np.linalg.det(matrix[:2,:2]))}


def runtime_contact(rig,skin,index,box,size):
    from ski_render import render
    frame,report,layers,gear=render(rig,skin,'fall',index,True)
    mitten=layers['forearm_hand_r'].crop(box).resize(tuple(size),Image.Resampling.LANCZOS)
    data=np.asarray(mitten)[:,:,3];ys,xs=np.where(data>=128);bottom=int(ys.max())
    gears={n:np.asarray(im.crop(box).resize(tuple(size),Image.Resampling.LANCZOS))[:,:,3] for n,im in gear.items()}
    candidates=[int(x) for x in xs[ys==bottom] if all(a[bottom,x]<128 for a in gears.values())]
    if not candidates:raise ValueError('Snow contact would land on gear rather than the exposed mitten')
    x=candidates[0]
    return {'runtime_contact_edge':[x,bottom+1],'runtime_sample_pixel':[x,bottom],
            'runtime_mitten_alpha':int(data[bottom,x]),'runtime_gear_alpha':{n:int(a[bottom,x]) for n,a in gears.items()},
            'contact_policy':'bottom edge of saved-size glove alpha>=128, gear core absent; no projected-source-point guess'}
