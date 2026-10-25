"""Build SKY action/rope/environment layers with explicit compatible runtime contracts."""
import json
import numpy as np
from PIL import Image,ImageDraw
from sky_config import ART,RIG,GAME,PREVIEW,SOURCES,ANIMS,SKIN_ANIMS,SKY
from sky_rig import build,dump,sha,svg
from sky_render import render,rope_frame
from sky_props import static_assets
from sky_export import save_frames,geometry,export_group,preview_clip,scene,gif
from rig_preview import quantize,font


def main():
    PREVIEW.mkdir(parents=True,exist_ok=True);rig=build();clips={};assets,birds=static_assets()
    birdpaths,birdhash=save_frames(GAME/'bird',birds)
    for i,im in enumerate(birds):(GAME/f'bird/{i:03d}.svg').write_text(svg(im,'bird',{'native_object':True,'frame':i}),'utf-8')
    for skin,names in SKIN_ANIMS.items():
        clips[skin]={}
        for name in names:
            spec=ANIMS[name];raw=[];reports=[]
            for i in range(spec['count']):
                frame,report=render(rig,skin,name,i,spec['count']);raw.append(frame);reports.append(report)
            clips[skin][name]={'raw':raw,'reports':reports,**spec}
    geometries={h:geometry([c for cs in clips.values() for c in cs.values() if c['height']==h],h) for h in [40,72]}
    for skin,cs in clips.items():
        for h in [40,72]:export_group([c for c in cs.values() if c['height']==h],geometries[h])
    manifest={'version':1,'package':'round10-sky','rig':'rig/sky/rig.json','status':'host artwork, user/device acceptance pending',
              'animations':[],'assets':[],'budget_bytes':260*1024,'identity':'Original white NABO cap retained; frozen common head/expression reused. Flying theme is clothing/scarf only.',
              'second_skin':'sky_b common idle loop and settlement cheer only; other gameplay clips use sky_a as ART_BRIEF permits',
              'environment':'Envelope, burner, controls, basket back/front, bird, stamp and clouds are separate layers; engine owns brightness, ascent, glow and stamp flight'}
    quality={'geometry':geometries,'skins':{},'repairs':['Pants edge was incorrectly attached to a raised wrist. Only original skin/cuff coverage follows hands; pants stay with legs.',
               'Scarf-root colors entered sleeve overlap circles. Local source-color exclusion now keeps the scarf off moving sleeves; frozen head is unchanged.']}
    for skin,cs in clips.items():
        quality['skins'][skin]={}
        for name,c in cs.items():
            formal,q=quantize(c['raw'],63,104);frames,fh=save_frames(ART/f'frames/sky/{skin}/{name}',formal)
            masters,mh=save_frames(ART/f'frames/sky/masters/{skin}/{name}',c['raw'])
            runtime,rh=save_frames(ART/f'frames/sky/runtime/{skin}/{name}',c['runtime'])
            geom=geometries[c['height']];box=geom['bbox'];scale=geom['scale']
            palms=[{side:[round((v[0]-box[0])*scale,3),round((v[1]-box[1])*scale,3)] for side,v in r['palms'].items()} for r in c['reports']]
            entry={'name':name,'skin':skin,'facing':'front','fps':12,'loop':c['loop'],'frames':frames,'frame_sha256':fh,
                'masters':masters,'master_sha256':mh,'runtime_frames':runtime,'runtime_sha256':rh,
                'canvas':[256,256],'anchor':[128,224 if c['height']==72 else 160],
                'target_height_px':c['height'],'runtime_canvas':geom['canvas'],'runtime_anchor':geom['anchor'],
                'runtime_hand_contacts':palms,'color_limit':64,'formal_quantization':q,'runtime_quantization':c['runtime_report'],
                'runtime_group':skin+str(c['height']),'hitbox':[round((104-box[0])*scale),round((102-box[1])*scale),round(50*scale),round(58*scale)]}
            manifest['animations'].append(entry);preview_clip(skin,name,c)
            quality['skins'][skin][name]={'reports':c['reports'],'runtime_contacts':palms}
    geom=geometries[40];neutral_report=clips['sky_a']['idle']['reports'][0]
    neutral,neutral_points=rope_frame(neutral_report,geom)
    neutral.save(GAME/'props/controls_idle.png');(GAME/'props/controls_idle.svg').write_text(svg(neutral,'idle controls',{'engine_layer':'control rope','grips':neutral_points}),'utf-8')
    assets.append(('controls_idle',neutral,geom['anchor'],8))
    rope_clips={}
    for name in ['heat','vent']:
        frames=[];points=[]
        for report in clips['sky_a'][name]['reports']:
            im,contacts=rope_frame(report,geom);frames.append(im);points.append(contacts)
        paths,hashes=save_frames(GAME/f'controls/{name}',frames);rope_clips[name]=frames
        manifest['animations'].append({'name':name+'_controls','skin':'sky_props','fps':12,'loop':False,
                'runtime_frames':paths,'runtime_sha256':hashes,'runtime_canvas':geom['canvas'],'runtime_anchor':geom['anchor'],
                'control_points':points,'color_limit':8,'must_play_with':'sky_a/'+name})
    manifest['animations'].append({'name':'bird','skin':'sky_props','fps':12,'loop':True,'runtime_frames':birdpaths,
        'runtime_sha256':birdhash,'runtime_canvas':[24,20],'runtime_anchor':[12,12],'color_limit':8})
    for name,im,anchor,limit in assets:
        path=GAME/('tiles' if name.startswith('cloud') else 'props')/(name+'.png')
        manifest['assets'].append({'id':'sky/'+name,'path':path.relative_to(ART).as_posix(),'sha256':sha(path),
            'size':list(im.size),'anchor':anchor,'color_limit':limit,'source_svg':path.with_suffix('.svg').relative_to(ART).as_posix()})
    sequences={};continuity={}
    for name in ['heat','vent','hit','receive_stamp']:
        c=clips['sky_a'][name];sequence=clips['sky_a']['idle']['runtime']+c['runtime']+clips['sky_a']['idle']['runtime']
        idle=c['runtime'][0];start=np.asarray(clips['sky_a']['idle']['runtime'][0])
        diffs=[float(np.abs(np.asarray(c['runtime'][i]).astype(float)-start).mean()) for i in [0,-1]]
        assert diffs==[0,0],(name,diffs)
        continuity[name]={'boundary_runtime_rgba_mae':diffs,'geometry_palette_anchor_shared_with_idle':True}
        frames=[]
        for i,character in enumerate(sequence):
            phase=i-6;ropes=rope_clips[name][phase] if name in rope_clips and 0<=phase<len(c['runtime']) else neutral
            stamp_at=None
            if name=='receive_stamp' and phase in [1,2]:
                palm=quality['skins']['sky_a'][name]['runtime_contacts'][phase]['l']
                stamp_at=[80-geom['anchor'][0]+palm[0]-4,248-geom['anchor'][1]+palm[1]-8]
            frames.append(scene(character,geom['anchor'],ropes,stamp_at,i%4))
        gif(PREVIEW/f'continuity-{name}.gif',frames);sequences[name]=frames
    paired=[]
    for i in range(max(len(v) for v in sequences.values())):
        screen=Image.new('RGB',(960,344),SKY);d=ImageDraw.Draw(screen)
        for col,(name,frames) in enumerate(sequences.items()):
            screen.paste(frames[min(i,len(frames)-1)],(col*240,24));d.text((col*240+4,4),name+' idle > action > idle',font=font(12),fill='#253e4d')
        paired.append(screen)
    gif(PREVIEW/'same-screen-continuity.gif',paired);paired[8].save(PREVIEW/'same-screen-continuity.png')
    for name,frames in sequences.items():
        strip=Image.new('RGB',(240*len(frames),320),SKY)
        for i,frame in enumerate(frames):strip.paste(frame,(i*240,0))
        strip.save(PREVIEW/f'scene-{name}-contact.png')
    scene(clips['sky_b']['idle']['runtime'][0],geom['anchor'],neutral).save(PREVIEW/'sky_b-scene.png')
    quality['continuity']=continuity;quality['engine_scene_anchor']=[80,248]
    dump(ART/'sky-manifest.json',manifest);dump(PREVIEW/'motion-quality.json',quality)
    print(json.dumps({'character_clips':sum(len(x) for x in clips.values()),'character_frames':sum(len(c['raw']) for cs in clips.values() for c in cs.values()),
                      'manifest_sha256':sha(ART/'sky-manifest.json'),'geometry':geometries}))


if __name__=='__main__':main()
