"""Formal 256RGBA delivery plus explicitly grouped final-size runtime sprites."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from build_travel_rig import ART,digest
from rig_preview import quantize,font
from rig_config import WORLDS


def union_box(frames):
    mask=np.maximum.reduce([np.asarray(f)[:,:,3]>=128 for f in frames])
    y,x=np.where(mask)
    return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]


def durations(count):
    # Accumulated GIF centiseconds closely follow the exact PNG 12fps clock.
    return [round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(count)]


def save_gif(path,frames,loop,background='#24354b',zoom=1):
    screens=[]
    for frame in frames:
        if zoom!=1:frame=frame.resize((frame.width*zoom,frame.height*zoom),Image.Resampling.NEAREST)
        screen=Image.new('RGBA',(max(160,frame.width+24),max(180,frame.height+24)),background)
        screen.alpha_composite(frame,((screen.width-frame.width)//2,screen.height-frame.height-12))
        screens.append(screen.convert('RGB'))
    options={'loop':0} if loop else {}
    screens[0].save(path,save_all=True,append_images=screens[1:],duration=durations(len(frames)),
                    disposal=2,**options)


def compare_masters(name,masters,formal):
    indices=sorted(set([0,len(masters)//3,2*len(masters)//3,len(masters)-1]))
    canvas=Image.new('RGB',(1024,596),'#24354b')
    d=ImageDraw.Draw(canvas)
    d.text((10,5),f'{name}: master top / shared 64-colour delivery bottom',fill='white',font=font(18))
    for column,i in enumerate(indices):
        canvas.paste(masters[i],(column*256,35),masters[i])
        canvas.paste(formal[i],(column*256,325),formal[i])
    canvas.save(ART/f'preview/travel/{name}-master-vs-64.png')


def preview(name,clip,runtime,report,formal):
    folder=ART/'preview/travel'
    count=len(runtime); height=runtime[0].height
    zoom=3 if height<=72 else 1
    cw=max(108,runtime[0].width*zoom+8); ch=height*(zoom+1)+62
    sheet=Image.new('RGB',(cw*count,ch*2),'white')
    d=ImageDraw.Draw(sheet)
    gifs=[]
    for row,(world,colour) in enumerate(WORLDS.items()):
        d.rectangle((0,row*ch,sheet.width,(row+1)*ch),fill=colour)
        d.text((7,row*ch+4),f'{name} / {height}px / {world} / actual + {zoom}x',fill='white' if row else '#182439',font=font(13))
        for i,frame in enumerate(runtime):
            x,y=i*cw,row*ch
            sheet.paste(frame,(x+(cw-frame.width)//2,y+30),frame)
            big=frame.resize((frame.width*zoom,frame.height*zoom),Image.Resampling.NEAREST)
            sheet.paste(big,(x+(cw-big.width)//2,y+height+44),big)
        path=folder/f'{name}-{world}.gif'
        save_gif(path,runtime,clip['loop'],colour,zoom)
        gifs.append(path.relative_to(ART).as_posix())
    path=folder/f'{name}-contact.png'; sheet.save(path)
    save_gif(folder/f'{name}-rig.gif',clip['frames'],clip['loop'])
    save_gif(folder/f'{name}-delivery.gif',formal,clip['loop'])
    compare_masters(name,clip['frames'],formal)
    return {'contact_sheet':path.relative_to(ART).as_posix(),'world_gifs':gifs,
            'technical_gif':f'preview/travel/{name}-rig.gif','delivery_gif':f'preview/travel/{name}-delivery.gif',
            'world_colours':WORLDS,'runtime_quantization':report,
            'gif_duration_ms':sum(durations(count)),'exact_png_fps':12,
            'gif_note':'centisecond approximation of 12fps; contacts show every pose'}


def runtime_assets(clips):
    groups={}
    for name,clip in clips.items():
        key='locomotion48' if clip['height']==48 else name
        groups.setdefault(key,[]).append(name)
    result={}
    for group,names in groups.items():
        masters=[f for n in names for f in clips[n]['frames']]
        box=union_box(masters); height=clips[names[0]]['height']
        scale=height/(box[3]-box[1]); size=(round((box[2]-box[0])*scale),height)
        sampled=[f.crop(box).resize(size,Image.Resampling.LANCZOS) for f in masters]
        colours=clips[names[0]].get('runtime_visible_colours',63)
        ready,report=quantize(sampled,colours=colours,protect_head=round(height*.45))
        report.update({'group':group,'shared_across':names,'source_bbox':box,'scale':scale,'canvas':size,
                       'anchor':[round((128-box[0])*scale),round((224-box[1])*scale)],
                       'height_policy':'one union crop/scale/palette per group; never per-frame recentering'})
        offset=0
        for name in names:
            count=len(clips[name]['frames']); frames=ready[offset:offset+count]; offset+=count
            result[name]=(frames,report)
    return result


def export(clips,rig):
    folder=ART/'preview/travel';folder.mkdir(parents=True,exist_ok=True)
    runtime=runtime_assets(clips); entries=[]; qa=[]
    for name,clip in clips.items():
        masters=clip['frames']; count=len(masters)
        mdir=ART/f'frames/travel/masters/{name}';fdir=ART/f'frames/travel/{name}';rdir=ART/f'frames/travel/runtime/{name}'
        for p in [mdir,fdir,rdir]:p.mkdir(parents=True,exist_ok=True)
        formal,colour_report=quantize(masters,protect_head=True)
        rframes,rreport=runtime[name]
        for i,(master,frame,rframe) in enumerate(zip(masters,formal,rframes)):
            master.save(mdir/f'{i:03d}.png');frame.save(fdir/f'{i:03d}.png');rframe.save(rdir/f'{i:03d}.png')
        arrays=[np.asarray(f).astype(float) for f in masters]
        differences=[float(np.abs(arrays[(i+1)%count]-arrays[i]).mean()) for i in range(count)]
        colours=len(set().union(*(set(map(tuple,np.asarray(f).reshape((-1,4)))) for f in formal)))
        rcolours=len(set().union(*(set(map(tuple,np.asarray(f).reshape((-1,4)))) for f in rframes)))
        assert colours<=64 and rcolours<=64
        assert max(differences)>0
        if clip['loop']:assert differences[-1]<=max(differences[:-1])*1.6
        entry={'name':name,'skin':'travel','group':'shared/travel','facing':clip['facing'],'fps':12,'loop':clip['loop'],
               'frames':[f'frames/travel/{name}/{i:03d}.png' for i in range(count)],
               'masters':[f'frames/travel/masters/{name}/{i:03d}.png' for i in range(count)],
               'runtime_frames':[f'frames/travel/runtime/{name}/{i:03d}.png' for i in range(count)],
               'runtime_anchor':rreport['anchor'],'runtime_canvas':rreport['canvas'],'runtime_group':rreport['group'],
               'anchor':[128,224],'canvas':[256,256],'target_height_px':clip['height'],'hitbox':union_box(masters),
               'frame_sha256':[digest(fdir/f'{i:03d}.png') for i in range(count)],
               'master_sha256':[digest(mdir/f'{i:03d}.png') for i in range(count)],
               'runtime_sha256':[digest(rdir/f'{i:03d}.png') for i in range(count)],
               'delivered_shared_rgba_colours':colours,'runtime_shared_rgba_colours':rcolours,
               'delivery_quantization':colour_report,'runtime_quantization':rreport,
               'visual_status':'reviewed technically and through source-pixel pose/contact comparisons; human animation acceptance not implied'}
        for key in ['transition_from','transition_to','registered_head']:
            if key in clip:entry[key]=clip[key]
        entry['target_preview']=preview(name,clip,rframes,rreport,formal)
        if name=='welcome':
            entry['voice_sync']={'voice_start_s':1.4,'voice_duration_s':2.690625,'voice_end_s':4.090625,
               'clip_seconds':count/12,'recommended_cycles':2,'post_cycles_hold_s':2.690625-2*count/12,
               'text':'NABO,陪你冒险','mouth_policy':'original neutral mouth retained; voice-over with nod/invitation timing, not invented lip sync',
               'entry_translation':'performed by firmware; source frames remain at a fixed anchor'}
        entries.append(entry)
        qa.append({'name':name,'frame_count':count,'frame_reports':clip['reports'],'master_adjacent_rgba_mae':differences,
                   'periodic_wrap_rgba_mae':differences[-1] if clip['loop'] else None,
                   'formal_colours':colours,'runtime_colours':rcolours,'formal_alpha':[0,255],'runtime_alpha':[0,255],
                   'runtime_canvas':rreport['canvas'],'runtime_anchor':rreport['anchor'],
                   'source_head_policy':'rigid source slice; registered two-source blend only in explicit turn clips'})
    old=json.loads((ART/'manifest.json').read_text('utf-8')) if (ART/'manifest.json').exists() else {}
    names={e['name'] for e in entries}
    preserved=[e for e in old.get('animations',[]) if e.get('skin')!='travel' or e['name'] not in names]
    manifest={**old,'version':2,'selected_design':'user-selected v2 option 1 light hiking','rig':'rig/rig.json',
              'rig_source_sha256':rig['source_sha256'],'status':'deterministic source-pixel animation, explicit runtime contracts',
              'animations':preserved+entries}
    if (ART/'shared-static-manifest.json').exists():
        manifest['shared_static_manifest']={'path':'shared-static-manifest.json','sha256':digest(ART/'shared-static-manifest.json')}
    (ART/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    (folder/'validation.json').write_text(json.dumps({'source_sha256':rig['source_sha256'],'checks':qa,
        'alpha_policy':rig['alpha_policy'],'identity_boundary':'background extraction was slightly re-rendered; this pipeline reuses those immutable pixels',
        'not_claimed':['human visual acceptance','new painted expressions','vector-character paths','hardware C decoder or on-device acceptance']},ensure_ascii=False,indent=2)+'\n','utf-8')
    return entries
