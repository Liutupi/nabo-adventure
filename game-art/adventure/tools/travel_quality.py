"""Explicit self-repair evidence and bounded technical motion gates, not automatic art approval."""
import json
import numpy as np
from PIL import Image
from build_travel_rig import ART


def write(entries,continuity):
    oldpath=ART/'preview/travel/revisions/cheer-attempt1-neck-gap.png'
    old=Image.open(oldpath).convert('RGBA')
    new=Image.open(ART/'frames/travel/masters/cheer/003.png').convert('RGBA')
    old_holes=int((np.asarray(old)[96:98,123:133,3]<128).sum())
    new_holes=int((np.asarray(new)[96:98,123:133,3]<128).sum())
    assert new_holes==0
    comparison=Image.new('RGB',(512,280),'#24354b')
    comparison.paste(old,(0,20),old);comparison.paste(new,(256,20),new)
    comparison.save(ART/'preview/travel/revisions/cheer-neck-before-after.png')
    refs={e['name']:e for e in entries}
    idle=Image.open(ART/refs['idle']['masters'][0]).convert('RGBA')
    endpoints={}
    for name in ['cheer','sad']:
        endpoints[name]=[]
        for index in [0,-1]:
            frame=Image.open(ART/refs[name]['masters'][index]).convert('RGBA')
            identical=bool(np.array_equal(np.asarray(frame),np.asarray(idle)))
            assert identical,(name,index)
            endpoints[name].append(identical)
    report={'self_repairs':[
        {'issue':'Cheer independent head lift exposed a 2-row neck gap.',
         'evidence_before':'revisions/cheer-attempt1-neck-gap.png','core_neck_empty_pixels_before':old_holes,
         'fix':'Use whole-body hop; keep original head attached to the collar. No hidden anatomy drawn.',
         'core_neck_empty_pixels_after':new_holes,'comparison':'revisions/cheer-neck-before-after.png'},
        {'issue':'Initial low celebration arm looked more like a flat sideways indication.',
         'fix':'Raised existing near upper arm 58 degrees and source forearm 70 degrees; retained source overlap at shoulder/elbow.',
         'evidence':'revisions/cheer-attempt2-raised-arm.png'},
        {'issue':'Independent per-action runtime crop/palette could pop scale, origin and clothing colors at facing switches.',
         'fix':'One shared crop/scale/palette for every 48px idle/walk/sad/turn; four 6-frame registered facing-source turns with exact endpoint reuse.'}],
        'continuity_summary':{side:{k:q[k] for k in ['max_boundary_centroid_delta_px','max_boundary_sole_delta_px',
             'hard_cut_head_rgba_mae','registered_turn_adjacent_head_rgba_mae','registered_turn_max_vs_hard_cut_ratio']} for side,q in continuity.items()},
        'nonloop_neutral_endpoints_match_idle_master':endpoints,
        'grok_needed_for_current_clips':False,
        'known_visual_limits':['Turn midposes are registered source dissolves, not newly drawn 3D yaw angles; slight full-size blending remains.',
            'Sad uses a head/shoulder slump and withdrawn arms with the original neutral face; no new frown was invented.',
            'Cheer is a near-arm celebration and small hop. The satchel-occluded far arm remains restrained.',
            'Welcome preserves the original neutral mouth; voice is synchronized narration, not phoneme lip sync.',
            '64-color large deliverables posterize smooth source shading. Lossless masters and true final-size previews preserve the comparison.'],
        'review_boundary':'Technical gates and self-repair evidence do not claim user or on-device animation acceptance.'}
    (ART/'preview/travel/motion-quality.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
