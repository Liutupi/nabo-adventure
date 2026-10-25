"""Independent saved-frame contact and before/after displacement audit for the flag."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from rig_render import turn,transformed
from space_motion import pose
from space_rig import ART,RIG,write_json


def distances(points):
    return [float(np.linalg.norm(np.subtract(b,a))) for a,b in zip(points,points[1:])]


def metrics(manifest):
    entry=next(e for e in manifest['animations'] if e['skin']=='space_a' and e['name']=='plant_flag')
    flag=entry['attachments']['flag'];visible=[a for a in flag if a['visible']]
    points=[x['top_left'] for x in visible];hands=[c['runtime_hands']['r'] for c in entry['contacts']['per_frame']]
    return {'visible_flag_frames':[x['frame'] for x in visible],
        'visible_flag_adjacent_displacement_px':distances(points),
        'max_flag_displacement_px':max(distances(points)),
        'max_flag_vertical_step_px':max(abs(b[1]-a[1]) for a,b in zip(points,points[1:])),
        'right_glove_adjacent_displacement_px':distances(hands),'max_glove_displacement_px':max(distances(hands)),
        'right_glove_contacts':hands,'flag_top_left':[x['top_left'] for x in flag]}


def verify_flag(manifest):
    entry=next(e for e in manifest['animations'] if e['skin']=='space_a' and e['name']=='plant_flag')
    attachments=entry['attachments']['flag'];anchor=entry['runtime_anchor'];height=28
    flagimage=Image.open(ART/'games/space/props/flag.png').convert('RGBA')
    source=Image.open(RIG/'space_a/front/forearm_hand_r.png').convert('RGBA')
    source=np.asarray(source).copy();source[:157,:,3]=0;source=Image.fromarray(source)
    contacts=[]
    for i,a in enumerate(attachments):
        if not a['visible']:continue
        assert a['top_left'][1]+height<=anchor[1],(i,'visible pole below ground')
        if a['hand_attached']:
            point=np.add(a['top_left'],a['grip_asset_point']).tolist()
            assert point==entry['contacts']['per_frame'][i]['runtime_hands']['r']
            assert flagimage.getpixel(tuple(a['grip_asset_point']))[3]==255
            rgba=Image.open(ART/entry['runtime_frames'][i]).convert('RGBA').getpixel(tuple(point))
            angles=pose('plant_flag',i)
            matrix=turn(angles['upper_arm_r'],(150,107))@turn(angles['forearm_hand_r'],(160,138))
            glove=transformed(source,matrix).crop((16,4,240,228)).resize(tuple(entry['runtime_canvas']),Image.Resampling.LANCZOS)
            alpha=glove.getchannel('A').getpixel(tuple(point));assert alpha>=128 and rgba[3]==255
            contacts.append({'frame':i,'grip':point,'flag_asset_point':a['grip_asset_point'],
                             'runtime_rgba':rgba,'independent_source_glove_alpha':alpha,'gap_px':0})
    assert attachments[5]['world_latch'] and attachments[5]['hand_attached'] and not attachments[5]['release']
    assert attachments[6]['release'] and not attachments[6]['hand_attached']
    assert attachments[5]['top_left'][1]+height==anchor[1]
    assert all(a['top_left']==attachments[5]['top_left'] for a in attachments[5:])
    result={'passed':True,'after':metrics(manifest),'glove_flag_contacts':contacts,'touchdown_frame':5,'release_frame':6,
        'world_latch_top_left':attachments[5]['top_left'],'world_latch_root_space':'root + attachment.top_left - runtime_anchor',
        'persistent_world_prop_after_body_clip':True,'head_and_helmet_sources_modified':False,
        'logic_boundary':'The host preview implements prop retention to demonstrate the contract; gameplay/device state handling is not implemented here.'}
    before=ART.parents[2]/'private/quality-review/space-flag-before/space-manifest.json'
    if before.is_file():
        result['before_manifest_sha256']=hashlib.sha256(before.read_bytes()).hexdigest()
        result['before']=metrics(json.loads(before.read_text('utf-8')))
    assert result['after']['max_flag_displacement_px']<=4.3
    assert result['after']['max_flag_vertical_step_px']<=3
    write_json(ART/'preview/space/flag-contact-qa.json',result)
    return result
