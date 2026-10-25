"""Fixed anchor, shared-palette formal/runtime exports for the CLIMB game pack."""
import numpy as np
from PIL import Image
from climb_rig import ART, RIG, digest, write_json
from rig_preview import quantize

CROP=(24,8,232,232)


def export(clips,rig,assets):
    entries=[];qa=[]
    for skin in ('climb_a','climb_b'):
        group=[c for (s,n),c in clips.items() if s==skin]
        allframes=[f for c in group for f in c['frames']]
        formal,fp=quantize(allframes,protect_head=True)
        # One formal palette per skin, not per frame or action. Palette indices
        # may change between skins, but every clip is <=64 RGBA colors.
        formaloff=0
        for height in (60,72):
            runtimegroup=[c for c in group if c['height']==height]
            size=(round(208*height/208),round(224*height/208))
            sampled=[f.crop(CROP).resize(size,Image.Resampling.LANCZOS) for c in runtimegroup for f in c['frames']]
            ready,rp=quantize(sampled,protect_head=round(96*height/208))
            rp.update({'source_crop':CROP,'scale':height/208,'canvas':size,
                       'anchor':[round((128-CROP[0])*height/208),round((224-CROP[1])*height/208)],
                       'policy':'fixed crop/scale/anchor for the complete skin + target-size group'})
            off=0
            for c in runtimegroup:
                c['runtime']=ready[off:off+len(c['frames'])];c['runtime_palette']=rp;off+=len(c['frames'])
        for c in group:
            count=len(c['frames']);formalframes=formal[formaloff:formaloff+count];formaloff+=count
            c['formal']=formalframes;paths={kind:[] for kind in ('frames','masters','runtime_frames')}
            for i,(master,frame,runtime) in enumerate(zip(c['frames'],formalframes,c['runtime'])):
                for field,sub,im in [('frames','',frame),('masters','masters/',master),('runtime_frames','runtime/',runtime)]:
                    path=ART/f'frames/climb/{sub}{skin}/{c["name"]}/{i:03d}.png'
                    path.parent.mkdir(parents=True,exist_ok=True);im.save(path);paths[field].append(path.relative_to(ART).as_posix())
            rp=c['runtime_palette'];name=c['name'];facing=c['facing']
            entry={'name':name,'skin':skin,'group':'climb','facing':facing,'fps':12,'loop':c['loop'],
                   **paths,'frame_sha256':[digest(ART/p) for p in paths['frames']],
                   'master_sha256':[digest(ART/p) for p in paths['masters']],
                   'runtime_sha256':[digest(ART/p) for p in paths['runtime_frames']],
                   'canvas':[256,256],'anchor':[128,224],'runtime_canvas':rp['canvas'],'runtime_anchor':rp['anchor'],
                   'target_height_px':c['height'],'height_policy':'neutral body is 60/72px; joint poses stay at fixed world root',
                   'hitbox':[42,16,214,224],'color_limit':64,'formal_palette':fp,'runtime_palette':rp,
                   'mirror':False,'rig':'rig/climb/rig.json','visual_acceptance':'technical and agent visual QA; user acceptance not claimed'}
            contacts=[]
            for i,report in enumerate(c['reports']):
                def runtime_point(p):return [round((p[0]-CROP[0])*rp['scale']),round((p[1]-CROP[1])*rp['scale'])]
                h=report['hand_contacts'];f=report['foot_contacts'];primary='l' if report['view']=='left' else 'r'
                contacts.append({'frame':i,'formal_hand':h,'formal_foot':f,
                    'runtime_hand':{k:runtime_point(p) for k,p in h.items()},
                    'runtime_foot':{k:runtime_point(p) for k,p in f.items()},
                    'grip_contact':runtime_point(h[primary]),'foot_contact':runtime_point(f[primary]),
                    'wall':report['view'] if report['view'] in ('left','right') else None,
                    'support_state':'grip' if c['action'] in ('grip_idle','charge') or (c['action'] in ('jump','switch_grab','slide') and i in (0,count-1)) else 'pose-only'})
            entry['contacts']={'space':'runtime canvas pixels; world = world_root + contact - runtime_anchor',
                'formal_space':'256x256 source frame; foot root remains (128,224)',
                'grip_contact':contacts[0]['grip_contact'],'foot_contact':contacts[0]['foot_contact'],'per_frame':contacts}
            c['contacts']=entry['contacts']
            entries.append(entry)
            raw=[np.array(f).astype(np.int16) for f in c['frames']]
            diff=[float(np.abs(raw[(i+1)%count]-raw[i]).mean()) for i in range(count)]
            if c['loop'] and diff[-1]>max(diff[:-1])*1.6:raise ValueError('Idle wrap jumps')
            for frame in c['frames']:
                b=frame.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
                if b[0]<CROP[0] or b[1]<CROP[1] or b[2]>CROP[2] or b[3]>CROP[3]:raise ValueError('Fixed runtime crop clips a pose')
            qa.append({'skin':skin,'name':name,'frames':count,'master_adjacent_rgba_mae':diff,
                       'loop_wrap_mae':diff[-1] if c['loop'] else None,'frame_reports':c['reports']})
    keyframes={skin:{c['name']:c['keyframes'] for c in clips.values() if c['skin']==skin} for skin in ('climb_a','climb_b')}
    write_json(RIG/'keyframes.json',{'fps':12,'root_translation':'game engine, not baked into sprite motion','skins':keyframes})
    manifest={'version':1,'game':'climb','fps':12,'rig':'rig/climb/rig.json',
              'identity':'frozen shared independent front/left/right head and expression pixels; no mirrored head or new face',
              'animations':entries,'assets':assets,
              'skin_b_inherits':{'from':'climb_a','actions':['switch_grab','charge','jump','slide','summit_cheer'],
                                 'policy':'light second skin per ART_BRIEF3.2; do not claim red outfit frames for inherited actions'},
              'shared_snow':'assets reference frozen mountain/snow-drift and ski/snow-mound directly',
              'not_claimed':['human animation acceptance','device gameplay integration','linked firmware flash footprint']}
    write_json(ART/'climb-manifest.json',manifest)
    write_json(ART/'preview/climb/validation.json',{'clips':qa,'formal_frames':sum(len(c['frames']) for c in clips.values()),
               'alpha':[0,255],'palette_policy':'shared per skin formal and per skin + size runtime',
               'source_sha256':{s:v['master_sha256'] for s,v in rig['skins'].items()}})
    return manifest
