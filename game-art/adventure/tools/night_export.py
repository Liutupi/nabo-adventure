"""NIGHT fixed-scale export and inspectable native-pixel motion previews."""
import hashlib
import json
import numpy as np
from PIL import Image,ImageDraw
from night_config import ART,PREVIEW,FOREST,ANCHOR
from rig_preview import quantize,font


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n','utf-8')


def save_frames(folder,frames):
    folder.mkdir(parents=True,exist_ok=True);paths=[];hashes=[]
    for i,im in enumerate(frames):
        path=folder/f'{i:03d}.png';im.save(path)
        paths.append(path.relative_to(ART).as_posix());hashes.append(sha(path))
    return paths,hashes


def export_group(clips,height):
    images=[f for c in clips.values() for f in c['raw']]
    boxes=[f.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox() for f in images]
    bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),224]
    scale=height/(bbox[3]-bbox[1]);width=round((bbox[2]-bbox[0])*scale)
    sampled=[f.crop(bbox).resize((width,height),Image.Resampling.LANCZOS) for f in images]
    output,report=quantize(sampled,63,round(height*.53))
    report.update(global_source_bbox=bbox,scale=scale,canvas=[width,height],
                  anchor=[round((ANCHOR[0]-bbox[0])*scale),height],
                  policy='One crop, scale, palette and anchor per skin/height; no frame recentering')
    cursor=0
    for clip in clips.values():
        clip['runtime']=output[cursor:cursor+len(clip['raw'])];clip['runtime_report']=report
        cursor+=len(clip['raw'])
    return report


def durations(count):return [round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(count)]


def gif(path,frames):
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations(len(frames)),loop=0,disposal=2)


def preview_clip(skin,name,clip):
    frames=clip['runtime'];cw=max(150,frames[0].width*3+20);ch=340
    contact=Image.new('RGB',(cw*len(frames),ch),'white');d=ImageDraw.Draw(contact)
    for i,im in enumerate(frames):
        x=i*cw;d.rectangle((x,0,x+cw,ch),fill=FOREST)
        d.text((x+5,5),f'{skin} {name} {i:02d}',fill='#e9e3d2',font=font(12))
        contact.paste(im,(x+(cw-im.width)//2,26),im)
        large=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
        contact.paste(large,(x+(cw-large.width)//2,105),large)
    path=PREVIEW/f'{skin}-{name}-contact.png';contact.save(path)
    frames_gif=[];masters=[]
    for im,raw in zip(frames,clip['raw']):
        bg=Image.new('RGB',(cw,250),FOREST);large=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
        bg.paste(large,((cw-large.width)//2,230-large.height),large);frames_gif.append(bg)
        tech=Image.new('RGBA',(256,256),FOREST);tech.alpha_composite(raw);masters.append(tech.convert('RGB'))
    gif(PREVIEW/f'{skin}-{name}.gif',frames_gif)
    gif(PREVIEW/f'{skin}-{name}-rig.gif',masters)
    return path.relative_to(ART).as_posix()


def continuity(skin,clips):
    report={};screens=[];order=['move_left','move_right','catch','lift_jar','yawn']
    count=8+max(len(clips[n]['runtime']) for n in order)+8
    for tick in range(count):
        screen=Image.new('RGB',(320*len(order),260),FOREST);d=ImageDraw.Draw(screen)
        for col,name in enumerate(order):
            idle=clips['seat_idle']['runtime'];act=clips[name]['runtime']
            if tick<8:im=idle[tick];label='idle'
            elif tick<8+len(act):im=act[tick-8];label=name
            else:im=idle[(tick-8-len(act))%len(idle)];label='idle'
            dx=0
            if name.startswith('move_'):
                t=max(0,min(1,(tick-8)/max(1,len(act)-1)))
                dx=12*(3*t*t-2*t*t*t)*(-1 if name=='move_left' else 1)
            anchor=clips['seat_idle']['runtime_report']['anchor'];large=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
            screen.paste(large,(round(col*320+160+dx*3-anchor[0]*3),220-anchor[1]*3),large)
            d.text((col*320+6,8),skin+' / '+name,fill='white',font=font(15))
            d.text((col*320+6,30),label+' @ 56px shown 3x',fill='white',font=font(13))
            d.line((col*320+5,220,col*320+315,220),fill='#41645b')
        screens.append(screen)
    gif(PREVIEW/f'{skin}-continuity.gif',screens)
    screens[10].save(PREVIEW/f'{skin}-continuity.png')
    for name in order:
        action=clips[name]['runtime'];idle=clips['seat_idle']['runtime'][0]
        first,last=[float(np.abs(np.asarray(f).astype(float)-np.asarray(idle).astype(float)).mean()) for f in (action[0],action[-1])]
        metrics=[]
        for f in action:
            a=np.asarray(f);y,x=np.where(a[:,:,3]>0)
            metrics.append({'bbox':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],
                            'centroid':[float(x.mean()),float(y.mean())],'sole_y':int(y.max()+1)})
        assert first==0 and last==0,(skin,name,first,last)
        report[name]={'boundary_first_last_rgba_mae':[first,last],'runtime_metrics':metrics,
                      'root_translation_policy':'program applies eased 12px seated scoot' if name.startswith('move_') else 'fixed root',
                      'body_face_policy':'rigid original head; source views registered then blended during 4-frame scoot' if name.startswith('move_') else 'single original head slice, no per-frame redraw'}
    return report
