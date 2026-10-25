"""SPACE source-pixel costume rig with empty binary glass equipment layers."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageChops
from climb_rig import ART, digest, write_json, svg, shared_head, trim_detached_cloth
from rig_render import translate, turn, transformed

RIG=ART/'rig/space';SIZE=(256,256)
LOCKS={'space_a':'092e8abdd4a653918366585e5134d0d70012d4e21f513a867a9d9df072e8c44a',
       'space_b':'857f9504c3ca413830565a3c516834c30324562f6ec83522a8cbd33199efebcb'}
WINDOWS={'front':(130,0,620,887),'left':(640,0,1140,887),'right':(1180,0,1680,887)}
NECK_Y={'space_a':365,'space_b':338}
PARTS={
 'forearm_hand_l':('upper_arm_l',(96,138),[(80,131),(108,131),(110,167),(96,180),(80,170)]),
 'forearm_hand_r':('upper_arm_r',(160,138),[(148,131),(177,131),(178,171),(158,180),(147,156)]),
 'upper_arm_l':('torso',(106,107),[(92,100),(115,105),(110,142),(82,148),(82,125)]),
 'upper_arm_r':('torso',(150,107),[(141,105),(165,100),(177,125),(180,148),(150,143)]),
 'shin_foot_l':('thigh_l',(115,188),[(0,183),(129,183),(129,256),(0,256)]),
 'shin_foot_r':('thigh_r',(141,188),[(126,183),(256,183),(256,256),(126,256)]),
 'thigh_l':('root',(116,151),[(0,147),(129,147),(129,196),(0,196)]),
 'thigh_r':('root',(140,151),[(126,147),(256,147),(256,196),(126,196)]),
 'utility_hose':('torso',(139,126),[(137,125),(147,128),(153,139),(150,152),(142,149),(139,139)]),
 'torso':('root',(128,151),None),
}
ORDER=['helmet_back','thigh_l','shin_foot_l','thigh_r','shin_foot_r','upper_arm_l','forearm_hand_l',
       'upper_arm_r','forearm_hand_r','torso','utility_hose','head','expression_neutral','helmet_front']


def suit_sample(source,skin,view):
    window=WINDOWS[view];tile=source.crop(window);a=np.array(tile.getchannel('A'));a[a<16]=0
    tile.putalpha(Image.fromarray(a));neck=NECK_Y[skin]
    core=a>128;ys=np.flatnonzero(core.sum(axis=1)>20);bottom=int(ys[-1])+1
    band=core[neck:neck+18];_,xs=np.where(band)
    center=(int(xs.min())+int(xs.max()))/2
    # Align collar to shared neck and soles to root, independently of generated
    # bubble size. Generated hat/face/glass pixels never enter the rig.
    scale=128/(bottom-neck);w=round(tile.width*scale);h=round(tile.height*scale)
    resized=tile.resize((w,h),Image.Resampling.LANCZOS)
    xy=(128-round(center*scale),96-round(neck*scale))
    canvas=Image.new('RGBA',SIZE);canvas.alpha_composite(resized,xy)
    pixels=np.array(canvas);pixels[:96,:,3]=0;canvas=Image.fromarray(pixels)
    sole=canvas.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()[3]
    dy=224-sole
    if dy:
        fixed=Image.new('RGBA',SIZE);fixed.alpha_composite(canvas,(0,dy));canvas=fixed
    return canvas,{'window':window,'source_neck_row':neck,'source_sole_row':bottom,
                   'scale':scale,'source_neck_center_x':center,'paste':xy,'target_neck':96,'target_sole':224,
                   'once_per_view_source_sole_compensation_y':dy}


def helmet_layers():
    back=Image.new('RGBA',SIZE);front=Image.new('RGBA',SIZE)
    d=ImageDraw.Draw(back)
    d.ellipse((74,4,183,106),outline='#52758e',width=4)
    d.arc((78,8,179,102),192,280,fill='#d4e4e9',width=2)
    d.arc((77,7,180,104),20,84,fill='#8da9b9',width=2)
    d=ImageDraw.Draw(front)
    d.arc((77,7,181,104),297,342,fill='#d4e4e9',width=2)
    d.arc((79,9,179,102),302,326,fill='#f5f1dc',width=1)
    # No filled pane: all face/hat pixels remain visible in their own layer.
    return back,front


def build():
    result={'version':1,'canvas':[256,256],'anchor':[128,224],'draw_order':ORDER,'skins':{},'mirror_allowed':False,
            'helmet_policy':'separate binary line/highlight equipment layers, clear interior; no tinted or semitransparent full glass pane',
            'head_policy':'frozen common front/left/right head and expression source pixels, integral translation only'}
    for skin,lock in LOCKS.items():
        path=ART/f'games/space/masters/{skin}-three-views.png'
        if digest(path)!=lock:raise ValueError('SPACE master changed')
        source=Image.open(path).convert('RGBA');views={}
        for view in WINDOWS:
            image,sampling=suit_sample(source,skin,view);remaining=Image.new('L',SIZE,255);parts={}
            folder=RIG/skin/view;folder.mkdir(parents=True,exist_ok=True);image.save(folder/'costume-sampled.png')
            for name,(parent,pivot,poly) in PARTS.items():
                region=Image.new('L',SIZE)
                if poly:ImageDraw.Draw(region).polygon(poly,fill=255)
                else:region=remaining.copy()
                mask=ImageChops.multiply(region,remaining);remaining=ImageChops.subtract(remaining,mask);d=ImageDraw.Draw(mask)
                if name.startswith(('upper_arm','forearm')):
                    x,y=(96,138) if name.endswith('_l') else (160,138);d.ellipse((x-9,y-9,x+9,y+9),fill=255)
                if name.startswith(('thigh','shin')):
                    x,y=(115,188) if name.endswith('_l') else (141,188);d.ellipse((x-12,y-12,x+12,y+12),fill=255)
                if name=='torso':
                    for x,y in [(106,107),(150,107),(116,151),(140,151)]:d.ellipse((x-10,y-10,x+10,y+10),fill=255)
                layer=image.copy();layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
                png=folder/f'{name}.png';layer.save(png);mask.save(folder/f'{name}-mask.png')
                meta={'parent':parent,'pivot':pivot,'polygon':poly,'master_sha256':lock,'view':view,'part':name}
                (folder/f'{name}.svg').write_text(svg(layer,name,meta),'utf-8')
                parts[name]={**meta,'path':png.relative_to(RIG).as_posix(),'sha256':digest(png)}
            head,expr,provenance=shared_head(view);back,front=helmet_layers()
            for name,layer,parent in [('head',head,'root'),('expression_neutral',expr,'head'),
                                       ('helmet_back',back,'head'),('helmet_front',front,'head')]:
                png=folder/f'{name}.png';layer.save(png)
                meta={'parent':parent,'pivot':[128,97],'part':name,'view':view,**provenance}
                (folder/f'{name}.svg').write_text(svg(layer,name,meta),'utf-8')
                parts[name]={**meta,'path':png.relative_to(RIG).as_posix(),'sha256':digest(png)}
            views[view]={'parts':parts,'sampling':sampling}
        result['skins'][skin]={'master':path.relative_to(ART).as_posix(),'master_sha256':lock,'views':views}
    write_json(RIG/'rig.json',result)
    write_json(ART/'games/space/masters/generation.json',{'method':'actual built-in imagegen costume edits, then immutable common-head rig',
        'references':[{'path':p,'sha256':digest(ART/p)} for p in ['reference/nabo-idle-original.png','design/round1/v2/01-hiker-design-board.png']],
        'outputs':[{'skin':s,'path':v['master'],'sha256':v['master_sha256'],'prompt':f'games/space/masters/{s}-prompt.txt',
                    'prompt_sha256':digest(ART/f'games/space/masters/{s}-prompt.txt')} for s,v in result['skins'].items()],
        'generated_head_usage':'discarded; shared approved head is the animation identity source','user_acceptance':'not claimed'})
    return result


def render(rig,skin,view,angles):
    parts=rig['skins'][skin]['views'][view]['parts'];matrices={'root':translate(0,0)}
    def mat(name):
        if name not in matrices:
            p=parts[name];matrices[name]=mat(p['parent'])@turn(angles.get(name,0),p['pivot'])
        return matrices[name]
    result=Image.new('RGBA',SIZE);contacts={}
    for name in ORDER:
        source=Image.open(RIG/parts[name]['path']).convert('RGBA');moved=transformed(source,mat(name));result.alpha_composite(moved)
        if name.startswith('forearm_hand'):
            p=np.array(source);p[:157,:,3]=0;a=np.array(transformed(Image.fromarray(p),mat(name)))[:,:,3]>=128
            ys,xs=np.where(a);contacts[name[-1]]=[round(float(xs.mean())),round(float(ys.mean()))]
    if not np.array_equal(mat('head'),mat('expression_neutral')) or not np.array_equal(mat('head')[:2,:2],np.eye(2)):
        raise ValueError('SPACE head geometry drift')
    result,removed=trim_detached_cloth(result)
    return result,{'view':view,'angles':angles,'head_rigid':True,'head_translation':[0,0],
                   'frozen_head_sha256':parts['head']['frozen_head_sha256'],'alpha_only_detached_cloth_pixels_removed':removed,
                   'hand_contacts':contacts,'alpha_bbox':result.getchannel('A').getbbox()}
