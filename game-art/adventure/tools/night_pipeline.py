"""Build both NIGHT skins without mutating the frozen shared skeleton or firmware."""
import json
import numpy as np
from PIL import Image
from night_config import ART,RIG,GAME,PREVIEW,SOURCE,ANIMS,ANCHOR
from night_source import build,svg
from night_render import render
from night_props import static_assets,glass_jar
from night_export import sha,write_json,save_frames,export_group,preview_clip,continuity
from rig_preview import quantize
from rig_render import transformed,translate
from travel_transitions import premultiplied_blend


def scoot(rig,skin,side,index,count):
    weight=[0,.7,.7,0][index];bodies=[];heads=[];reports=[]
    eye={'front':(128,119),'left':(125,119),'right':(131,119)}
    for view in ['front',side]:
        frame,report,layers=render(rig,skin,view,'move_'+side,index,count,True)
        body=Image.new('RGBA',(256,256));head=Image.new('RGBA',(256,256))
        for name,layer in layers:
            (head if name in ['head','expression'] else body).alpha_composite(layer,(0,report['ground_compensation_y']))
        bodies.append(body);heads.append(head);reports.append(report)
    eyes=[np.array(r['head_matrix'])@np.array([*eye[v],1.]) for r,v in zip(reports,['front',side])]
    target=(1-weight)*eyes[0]+weight*eyes[1]
    for i in range(2):
        shift=target[:2]-eyes[i][:2]
        heads[i]=transformed(heads[i],translate(*shift))
    out=premultiplied_blend(bodies[0],bodies[1],weight)
    out.alpha_composite(premultiplied_blend(heads[0],heads[1],weight))
    if index in [0,count-1]:out=render(rig,skin,'front','seat_idle',0,8)[0]
    record=reports[0];record.update(facing_weight=weight,independent_facing_source=side,
           eye_midpoint_registration=True,mirrored=False,
           jar_opening=((1-weight)*np.array(reports[0]['jar_opening'])+weight*np.array(reports[1]['jar_opening'])).tolist())
    return out,record


def provenance():
    records=[]
    for skin,info in SOURCE.items():
        im=Image.open(GAME/f'source/{skin}-source.png').convert('RGBA');alpha=np.asarray(im)[:,:,3]
        records.append({'skin':skin,'source_sha256':info['sha256'],'canvas':list(im.size),
            'prompt':f'games/night/source/{skin}-prompt.txt','generator':'built-in image_gen image edit',
            'references':['reference/nabo-idle-original.png','design/round1/v2/01-hiker-design-board.png'],
            'alpha_zero_pixels':int((alpha==0).sum()),'alpha_1_to_15_pixels':int(((alpha>0)&(alpha<16)).sum()),
            'source_png_preserved':True,'generated_head_discarded':True,
            'final_head':'read-only common facing head + neutral expression; local collar exclusion only',
            'animation':'deterministic source-pixel SVG layer transforms; no AI frame generation'})
    write_json(GAME/'source/generation.json',{'calls':records,'identity_acceptance':'no new user identity approval claimed; final heads reuse frozen approved common rig'})


def main():
    PREVIEW.mkdir(parents=True,exist_ok=True);rig=build();provenance()
    manifest={'version':1,'package':'round7-night','rig':'rig/night/rig.json',
       'status':'host-rendered and independently C-decoded; user artwork/device acceptance pending',
       'animations':[],'assets':[],'identity':'immutable common head source, locally excluded garment collar; original head RGB not recolored before target quantization',
       'head_alpha_policy':'source alpha<16 discarded; final delivery/runtime binary alpha threshold128',
       'budget_bytes':260*1024,'palette_limit':64,'second_skin_policy':'both skins full set, subject to measured package budget'}
    quality={'skins':{},'known_limits':['Seated scoot uses 4 source-view blended frames; full-size mid-turn softness is disclosed.',
       'Catch uses a 35 degree whole-upper-body lean to place the jar opening above the cap without stretching arm pixels.',
       'Yawn is a hand-to-mouth/head-nod gesture with the immutable neutral mouth, not a redrawn open-mouth expression.',
       'Occluded garment underlays copy adjacent original clothing pixels; they are technical completion, not ground-truth hidden anatomy.']}
    for skin in SOURCE:
        clips={}
        for name,config in ANIMS.items():
            raw=[];reports=[]
            for i in range(config['count']):
                frame,report=(scoot(rig,skin,config['facing'],i,config['count']) if name.startswith('move_') else
                              render(rig,skin,config['facing'],name,i,config['count']))
                raw.append(frame);reports.append(report)
            clips[name]={'raw':raw,'reports':reports,**config}
        for height in [56,72]:export_group({n:c for n,c in clips.items() if c['height']==height},height)
        for name,clip in clips.items():
            formal,q=quantize(clip['raw'],63,148)
            masters,mhash=save_frames(ART/f'frames/night/masters/{skin}/{name}',clip['raw'])
            frames,fhash=save_frames(ART/f'frames/night/{skin}/{name}',formal)
            runtime,rhash=save_frames(ART/f'frames/night/runtime/{skin}/{name}',clip['runtime'])
            report=clip['runtime_report'];bbox=report['global_source_bbox'];scale=report['scale']
            entry={'name':name,'skin':skin,'facing':clip['facing'],'fps':12,'loop':clip['loop'],
                'frames':frames,'frame_sha256':fhash,'masters':masters,'master_sha256':mhash,
                'runtime_frames':runtime,'runtime_sha256':rhash,'canvas':[256,256],'anchor':list(ANCHOR),
                'target_height_px':clip['height'],'runtime_canvas':report['canvas'],'runtime_anchor':report['anchor'],
                'runtime_group':skin+str(clip['height']),'color_limit':64,'formal_quantization':q,'runtime_quantization':report,
                'runtime_jar_opening':[[round((r['jar_opening'][0]-bbox[0])*scale,3),round((r['jar_opening'][1]-bbox[1])*scale,3)] for r in clip['reports']],
                'hitbox':[round((95-bbox[0])*scale),round((144-bbox[1])*scale),round(66*scale),round(80*scale)]}
            manifest['animations'].append(entry)
            clip['contact']=preview_clip(skin,name,clip)
        quality['skins'][skin]={'motions':{n:{'reports':c['reports'],'contact':c['contact']} for n,c in clips.items()},
                                 'continuity':continuity(skin,clips)}
    assets,moths=static_assets()
    jar=glass_jar().crop((110,171,129,208));jar.save(GAME/'props/glass_jar.png')
    (GAME/'props/glass_jar.svg').write_text(svg(jar,'glass_jar',{'kind':'native transparent glass prop, independent from character'}),'utf-8')
    assets.append(('glass_jar',jar,'props',[9,37],8))
    for id,im,folder,anchor,limit in assets:
        path=GAME/f'{folder}/{id}.png'
        manifest['assets'].append({'id':'night/'+id,'path':path.relative_to(ART).as_posix(),'sha256':sha(path),
                                  'size':list(im.size),'anchor':anchor,'color_limit':limit})
    mothpaths,mothhash=save_frames(GAME/'moth',moths)
    for i,im in enumerate(moths):(GAME/f'moth/{i:03d}.svg').write_text(svg(im,'moth',{'kind':'native 4-frame insect wing cycle'}),'utf-8')
    manifest['animations'].append({'name':'moth','skin':'night_shared','fps':12,'loop':True,
        'runtime_frames':mothpaths,'runtime_sha256':mothhash,'runtime_canvas':[16,16],'runtime_anchor':[8,13],'color_limit':8})
    write_json(ART/'night-manifest.json',manifest);write_json(PREVIEW/'motion-quality.json',quality)
    print(json.dumps({'animations':len(manifest['animations']),'assets':len(manifest['assets']),
                      'character_frames':sum(len(a['frames']) for a in manifest['animations'] if 'frames' in a),
                      'manifest_sha256':sha(ART/'night-manifest.json')}))


if __name__=='__main__':main()
