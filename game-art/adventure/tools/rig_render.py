"""Deterministic hierarchical cutout animation of immutable source pixel layers."""
import math
from pathlib import Path
import numpy as np
from PIL import Image


def translate(x, y):
    return np.array([[1., 0., x], [0., 1., y], [0., 0., 1.]])


def turn(angle, pivot):
    a = math.radians(angle)
    r = np.array([[math.cos(a), -math.sin(a), 0.], [math.sin(a), math.cos(a), 0.], [0., 0., 1.]])
    x, y = pivot
    return translate(x, y) @ r @ translate(-x, -y)


def pose(anim, frame, count=8):
    phase = 2 * math.pi * frame / count
    s, c = math.sin(phase), math.cos(phase)
    angles = {}
    if anim == 'idle':
        angles.update(torso=0.35*s, upper_arm_l=0.8*s, upper_arm_r=-0.8*s,
                      jacket_flap=1.5*math.sin(phase+0.5), satchel=0.7*math.sin(phase+0.3))
        bob = 0
    elif anim.startswith('walk'):
        angles.update(thigh_l=10*s, thigh_r=-10*s,
                      shin_foot_l=-5*s+5*max(0., -s)**2, shin_foot_r=5*s+5*max(0., s)**2,
                      upper_arm_l=-7*s, forearm_hand_l=-3*s,
                      # The satchel occludes this arm: keep its swing inside the
                      # available source cuff overlap instead of inventing hidden pixels.
                      upper_arm_r=3*s, forearm_hand_r=1.5*s,
                      torso=0.6*s, jacket_flap=3*math.sin(phase+0.6),
                      satchel=2*math.sin(phase-0.4), collar=0.5*s)
        bob = -round(1-math.cos(2*phase))
    elif anim == 'cheer':
        lift = [0,.25,.72,1,.95,.6,.18,0][frame]
        angles.update(upper_arm_l=58*lift,forearm_hand_l=70*lift,
                      upper_arm_r=-7*lift,forearm_hand_r=-5*lift,
                      torso=-1.4*lift,jacket_flap=1.5*math.sin(.5)-3*lift,satchel=.7*math.sin(.3)+2*lift)
        bob=0
    elif anim == 'sad':
        slump=[0,.28,.75,1,.55,0][frame]
        angles.update(torso=2.5*slump,upper_arm_l=-4*slump,upper_arm_r=2*slump,
                      forearm_hand_l=-3*slump,jacket_flap=1.5*math.sin(.5)+slump,satchel=.7*math.sin(.3)-slump)
        bob=0
    elif anim == 'welcome':
        invitation=(1-c)/2
        angles.update(upper_arm_l=12*invitation,forearm_hand_l=19*invitation,
                      upper_arm_r=-1.3*invitation,torso=-.7*invitation,
                      jacket_flap=1.5*math.sin(.5)+1.3*s,satchel=.7*math.sin(.3)+.8*s)
        bob=0
    else:
        raise ValueError('unknown animation '+anim)
    return angles, bob


def pose_data(anim,frame,count):
    angles,bob=pose(anim,frame,count)
    key={'frame':frame,'phase':frame/count,'angles_degrees':angles,'root_bob_y':bob,
         'head_offset_y':0,'ground_lift':0}
    if anim=='cheer':
        # The whole body already hops. Separate upward head offsets exposed a
        # neck gap in attempt 1, so keep the intact head attached to the collar.
        key['head_offset_y']=0
        key['ground_lift']=[0,1,3,4,3,1,0,0][frame]
    elif anim=='sad':
        key['head_offset_y']=[0,1,4,6,4,0][frame]
    elif anim=='welcome':
        key['head_offset_y']=round(2*(1-math.cos(2*math.pi*frame/count))/2)
    return key


def transformed(layer, matrix):
    # Rigid integral translation avoids any internal head/face resampling or drift.
    if np.allclose(matrix[:2, :2], np.eye(2)) and np.allclose(matrix[:2, 2], np.round(matrix[:2, 2])):
        dest = Image.new('RGBA', layer.size)
        dest.alpha_composite(layer, tuple(np.round(matrix[:2, 2]).astype(int)))
        return dest
    inverse = np.linalg.inv(matrix)
    return layer.transform(layer.size, Image.Transform.AFFINE, tuple(inverse[:2].flatten()),
                           resample=Image.Resampling.BICUBIC)


def render_frame(rig, rigroot, facing, anim, index, include_head=True):
    view = rig['views'][facing]
    parts = view['parts']
    key = rig['animations'][anim]['keyframes'][index]
    angles, bob = key['angles_degrees'], key['root_bob_y']
    matrices = {'root': translate(0, bob)}

    def matrix(name):
        if name not in matrices:
            p = parts[name]
            matrices[name] = matrix(p['parent']) @ turn(angles.get(name, 0.), p['pivot'])
            if name=='head':
                matrices[name]=matrices[name] @ translate(0,key.get('head_offset_y',0))
        return matrices[name]

    layers = {}
    canvas = Image.new('RGBA', tuple(rig['canvas']))
    for name in rig['draw_order']:
        layer = Image.open(Path(rigroot) / parts[name]['raster']).convert('RGBA')
        layers[name] = transformed(layer, matrix(name))
        if include_head or name not in ('head','expression_neutral'):
            canvas.alpha_composite(layers[name])
    # Keep the lowest substantial sole on the contractual ground line. This is
    # explicit deterministic root compensation, not independent per-part recentering.
    core = canvas.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
    dy = rig['anchor'][1] - key.get('ground_lift',0) - core[3]
    final = Image.new('RGBA', canvas.size)
    final.alpha_composite(canvas, (0, dy))
    head = layers['head']
    neutral = layers['expression_neutral']
    # Head geometry can translate as one piece; eye/mouth layers have exactly the
    # same transform and all shared face RGB is sampled from the same reference.
    hm, em = matrix('head'), matrix('expression_neutral')
    if not np.array_equal(hm, em) or not np.allclose(hm[:2, :2], np.eye(2)):
        raise ValueError('Face transform drift or head deformation')
    orig_head = Image.open(Path(rigroot) / parts['head']['raster']).convert('RGBA')
    same = transformed(orig_head, hm)
    if not np.array_equal(np.asarray(same), np.asarray(head)):
        raise ValueError('Head source pixels changed')
    report = {'index': index, 'pose_degrees': angles, 'root_bob': bob, 'ground_compensation_y': dy,
              'head_translation': [int(hm[0, 2]), int(hm[1, 2])+dy],
              'head_rigid_translation_only': True, 'expression_transform_matches_head': True,
              'head_source_rgba_sha256': parts['head']['rgba_sha256'],
              'alpha_bbox': final.getchannel('A').getbbox(), 'core_bbox': final.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()}
    return final, report
