"""Formal 256px/target 56px exports, attachment metadata and independent manifest."""
import numpy as np
from PIL import Image
from space_rig import ART,RIG,digest,write_json
from rig_preview import quantize

CROP=(16,4,240,228)
BODY_ENVELOPE=220


def export(clips,rig,assets):
    entries=[];qa=[]
    for skin in ('space_a','space_b'):
        group=[c for (s,n),c in clips.items() if s==skin]
        formal,fp=quantize([f for c in group for f in c['frames']],protect_head=True)
        for height in (56,72):
            subset=[c for c in group if c['height']==height];scale=height/BODY_ENVELOPE
            size=(round(224*scale),round(224*scale));anchor=[round(112*scale),round(220*scale)]
            samples=[f.crop(CROP).resize(size,Image.Resampling.LANCZOS) for c in subset for f in c['frames']]
            runtime,rp=quantize(samples,protect_head=round(100*scale));rp.update({'scale':scale,'canvas':size,'anchor':anchor,
                'source_crop':CROP,'body_envelope_px':BODY_ENVELOPE,
                'policy':'one crop/scale/palette per skin and target group, dome included; never per-frame recentering'})
            offset=0
            for c in subset:
                c['runtime']=runtime[offset:offset+len(c['frames'])];c['runtime_palette']=rp;offset+=len(c['frames'])
        offset=0
        for c in group:
            count=len(c['frames']);delivery=formal[offset:offset+count];offset+=count;c['formal']=delivery
            paths={field:[] for field in ('frames','masters','runtime_frames')}
            for i,(master,frame,rf) in enumerate(zip(c['frames'],delivery,c['runtime'])):
                for field,sub,image in [('frames','',frame),('masters','masters/',master),('runtime_frames','runtime/',rf)]:
                    path=ART/f'frames/space/{sub}{skin}/{c["name"]}/{i:03d}.png';path.parent.mkdir(parents=True,exist_ok=True)
                    image.save(path);paths[field].append(path.relative_to(ART).as_posix())
            rp=c['runtime_palette'];contacts=[]
            for i,report in enumerate(c['reports']):
                hands={k:[round((p[0]-CROP[0])*rp['scale']),round((p[1]-CROP[1])*rp['scale'])] for k,p in report['hand_contacts'].items()}
                contacts.append({'frame':i,'runtime_hands':hands,'formal_hands':report['hand_contacts']})
            attachments=[]
            if c['name']=='plant_flag':
                grip=[2,10];touchdown=5
                planted=[contacts[touchdown]['runtime_hands']['r'][0]-grip[0],rp['anchor'][1]-28]
                if contacts[touchdown]['runtime_hands']['r'][1]-grip[1]!=planted[1]:
                    raise ValueError('Glove must lower the pole to the world ground before releasing')
                for i,contact in enumerate(contacts):
                    hand=contact['runtime_hands']['r']
                    attachments.append({'frame':i,'visible':i>=2,'asset_id':'game/space/props/flag',
                        'top_left':[hand[0]-grip[0],hand[1]-grip[1]] if i<=touchdown else planted,
                        'phase':'stored' if i<2 else 'carried' if i<touchdown else 'touchdown-held' if i==touchdown else 'planted',
                        'hand_attached':2<=i<=touchdown,'grip_asset_point':grip,
                        'world_latch':i==touchdown,'release':i==touchdown+1,
                        'layer':'behind crew; source glove stays foreground'})
            entry={'name':c['name'],'skin':skin,'group':'space','facing':'front','fps':12,'loop':c['loop'],**paths,
                'frame_sha256':[digest(ART/p) for p in paths['frames']],
                'master_sha256':[digest(ART/p) for p in paths['masters']],
                'runtime_sha256':[digest(ART/p) for p in paths['runtime_frames']],
                'canvas':[256,256],'anchor':[128,224],'target_height_px':c['height'],
                'runtime_canvas':rp['canvas'],'runtime_anchor':rp['anchor'],'hitbox':[75,5,183,225],
                'formal_palette':fp,'runtime_palette':rp,'color_limit':64,'mirror':False,
                'contacts':{'space':'runtime canvas; world=root+point-runtime_anchor','per_frame':contacts},
                'attachments':{'flag':attachments,'space':'runtime canvas top-left; same translation as sprite root'},
                'rig':'rig/space/rig.json','acceptance':'agent visual + host validation; human/device acceptance not claimed'}
            c['contacts']=entry['contacts'];c['attachments']=entry['attachments'];entries.append(entry)
            raw=[np.array(f).astype(np.int16) for f in c['frames']]
            diffs=[float(np.abs(raw[(i+1)%count]-raw[i]).mean()) for i in range(count)]
            if c['loop'] and diffs[-1]>max(diffs[:-1])*1.6:raise ValueError('SPACE loop wrap jumps')
            for frame in c['frames']:
                box=frame.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
                if box[0]<CROP[0] or box[1]<CROP[1] or box[2]>CROP[2] or box[3]>CROP[3]:raise ValueError('SPACE runtime crop clips pose')
            qa.append({'skin':skin,'name':c['name'],'count':count,'frame_reports':c['reports'],'adjacent_master_mae':diffs,
                       'loop_wrap_mae':diffs[-1] if c['loop'] else None})
    lander={'canvas':[96,96],'anchor':[48,92],'layers':['game/space/lander/back','crew','game/space/lander/front'],
            'crew_root':[48,70],'crew_target_height':56,'crew_policy':'no second scale; position with runtime_anchor',
            'main_nozzle':{'position':[48,90],'direction':[0,1]},'side_nozzles':[[9,65],[86,65]],
            'landing_feet':[[9,92],[86,92]],'coordinates':'lander canvas pixels; y92 is sole bottom edge',
            'flame_and_star_policy':'engine only; no painted source particles'}
    manifest={'version':1,'game':'space','fps':12,'animations':entries,'assets':assets,'lander':lander,
              'skin_b_inherits':{'from':'space_a','actions':['land','hard_land','plant_flag'],'policy':'light second skin per ART_BRIEF3.2'},
              'flag_contract':'independent prop layer attached via each frame; last planted pose persists in world after body returns to idle',
              'flag_lifecycle':{'touchdown_frame':5,'release_frame':6,'stored_frames':[0,1],
                  'carried_frames':[2,3,4,5],'grip_asset_point':[2,10],
                  'latch_world_top_left_at_touchdown':'sprite_world_root + flag.top_left - sprite.runtime_anchor',
                  'after_clip':'retain the latched world prop independently of the crew animation/root'},
              'helmet_policy':rig['helmet_policy'],'head_policy':rig['head_policy'],
              'not_claimed':['human animation acceptance','device gameplay integration','final linked firmware bytes']}
    write_json(ART/'space-manifest.json',manifest)
    write_json(RIG/'keyframes.json',{'fps':12,'skins':{s:{c['name']:c['keyframes'] for c in clips.values() if c['skin']==s} for s in ('space_a','space_b')}})
    write_json(ART/'preview/space/validation.json',{'formal_frames':58,'clips':qa,'alpha':[0,255],
        'palette_policy':'shared per skin formal, per skin + size runtime','helmet':'binary clear-interior equipment layers'})
    return manifest
