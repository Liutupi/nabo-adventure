"""Normalize real wardrobe edits and wrap original clothing/head pixels as SVG layers."""
import base64
import hashlib
import html
import io
import json
import numpy as np
from PIL import Image,ImageDraw,ImageChops
from sky_config import ART,GAME,RIG,SOURCES,POLYS,PIVOTS,ORDER,CANVAS,HEAD_LOCKS


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n','utf-8')


def mask(points):
    out=Image.new('L',CANVAS);ImageDraw.Draw(out).polygon(points,fill=255);return out


def svg(image,name,metadata):
    stream=io.BytesIO();image.save(stream,'PNG');w,h=image.size
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        '<title>'+html.escape(name)+'</title><metadata>'+html.escape(json.dumps(metadata))+'</metadata>'
        f'<image width="{w}" height="{h}" href="data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()+'"/></svg>\n')


def build():
    RIG.mkdir(parents=True,exist_ok=True)
    rig={'canvas':list(CANVAS),'half_anchor':[128,160],'full_anchor':[128,224],'order':ORDER,'skins':{},
         'identity':'Frozen common front head + expression; no generated head or replacement flying hat is used.',
         'representation':'SVG wrappers of source-pixel slices with inspectable alpha masks, not drawn vector characters'}
    heads={};headmask=Image.new('L',CANVAS);d=ImageDraw.Draw(headmask)
    d.rectangle((0,0,255,93),fill=255);d.rectangle((121,94,137,100),fill=255)
    headmask.save(RIG/'local-head-garment-exclusion.png')
    for name,file in [('head','head'),('expression','expression_neutral')]:
        path=ART/f'rig/common/front/{file}.png';im=Image.open(path).convert('RGBA')
        assert sha(path)==HEAD_LOCKS[file],'Frozen shared identity pixels changed'
        im.putalpha(ImageChops.multiply(im.getchannel('A'),headmask));heads[name]=im
        im.save(RIG/f'{name}.png');(RIG/f'{name}.svg').write_text(svg(im,name,{'immutable_source':str(path.relative_to(ART)),
           'source_sha256':sha(path),'local_alpha_mask':'rig/sky/local-head-garment-exclusion.png','RGB':'original unchanged'}),'utf-8')
    for skin,info in SOURCES.items():
        source=GAME/f'source/{skin}-source.png';assert sha(source)==info['sha256']
        raw=Image.open(source).convert('RGBA');rawalpha=raw.getchannel('A');data=np.asarray(rawalpha)
        raw.putalpha(rawalpha.point(lambda a:a if a>=16 else 0))
        nx,ny=info['neck'];sx=91/info['head_width'];sy=126/(info['foot']-ny)
        sampled=raw.transform(CANVAS,Image.Transform.AFFINE,(1/sx,0,nx-128/sx,0,1/sy,ny-98/sy),Image.Resampling.BICUBIC)
        samplemask=mask([(0,94),(256,94),(256,256),(0,256)])
        sampled.putalpha(ImageChops.multiply(sampled.getchannel('A'),samplemask))
        folder=RIG/skin;folder.mkdir(exist_ok=True);sampled.save(folder/'wardrobe.png')
        whole=sampled.copy();whole.alpha_composite(heads['head']);whole.alpha_composite(heads['expression']);whole.save(folder/'normalized.png')
        remaining=samplemask.copy();parts={}
        names=['scarf','collar']+[n for n in POLYS if n not in ['scarf','collar']]
        for name in names:
            points=POLYS[name]
            region=ImageChops.multiply(mask(points),remaining);remaining=ImageChops.subtract(remaining,region)
            if name=='scarf':
                a=np.asarray(sampled).astype(float)
                colour=((a[:,:,0]>a[:,:,1]*1.3)&(a[:,:,0]>a[:,:,2]*1.15) if skin=='sky_a' else
                        (a[:,:,1]>a[:,:,0]*1.1)&(a[:,:,2]>a[:,:,0]*1.12))
                selected=ImageChops.multiply(region,Image.fromarray(np.where(colour,255,0).astype('uint8')))
                remaining=ImageChops.lighter(remaining,ImageChops.subtract(region,selected));region=selected
            # Lowered hands must not carry navy trousers when a rope is pulled.
            if name.startswith('forearm'):
                a=np.asarray(sampled).astype(float);skinpix=(a[:,:,0]>a[:,:,1]*1.1)&(a[:,:,1]>a[:,:,2]*1.04)&(a[:,:,0]>110)
                yy,xx=np.indices((256,256));side=xx<112 if name.endswith('_l') else xx>149
                extra=(yy>=153)&(yy<=177)&side&skinpix
                region=ImageChops.lighter(region,Image.fromarray(np.where(extra,255,0).astype('uint8')))
                outer=((xx<105) if name.endswith('_l') else (xx>152))&(yy<=160)
                keep=np.where((yy>=155)&~(skinpix|outer),0,255).astype('uint8')
                rejected=ImageChops.subtract(region,ImageChops.multiply(region,Image.fromarray(keep)))
                remaining=ImageChops.lighter(remaining,rejected);region=ImageChops.multiply(region,Image.fromarray(keep))
                remaining=ImageChops.subtract(remaining,region)
            if name.startswith('upper') and skin=='sky_a':
                a=np.asarray(sampled).astype(float);scarf=(a[:,:,0]>a[:,:,1]*1.3)&(a[:,:,0]>a[:,:,2]*1.15)
                keep=Image.fromarray(np.where(scarf,0,255).astype('uint8'))
                rejected=ImageChops.subtract(region,ImageChops.multiply(region,keep))
                remaining=ImageChops.lighter(remaining,rejected);region=ImageChops.multiply(region,keep)
            if name.startswith(('upper','forearm')):
                x,y=PIVOTS[name];ImageDraw.Draw(region).ellipse((x-6,y-6,x+6,y+6),fill=255)
            if name.startswith('upper'):
                a=np.asarray(sampled).astype(float)
                scarf=((a[:,:,0]>a[:,:,1]*1.3)&(a[:,:,0]>a[:,:,2]*1.15) if skin=='sky_a' else
                       (a[:,:,1]>a[:,:,0]*1.1)&(a[:,:,2]>a[:,:,0]*1.12))
                region=ImageChops.multiply(region,Image.fromarray(np.where(scarf,0,255).astype('uint8')))
            im=sampled.copy();im.putalpha(ImageChops.multiply(sampled.getchannel('A'),region));parts[name]=(im,region)
        torso=sampled.copy();torso.putalpha(ImageChops.multiply(sampled.getchannel('A'),remaining));parts['torso']=(torso,remaining)
        contract={'source':source.relative_to(ART).as_posix(),'source_sha256':sha(source),'neck_source':[nx,ny],
                  'target_neck':[128,98],'scale':[sx,sy],'source_alpha_discard_below':16,
                  'discarded_low_alpha_pixels':int(((data>0)&(data<16)).sum()),'source_generated_head_discarded':True}
        nodes={}
        for name,(im,region) in parts.items():
            p=folder/f'{name}.png';mp=folder/f'{name}-mask.png';im.save(p);region.save(mp)
            meta={**contract,'part':name,'polygon':POLYS.get(name),'pivot':PIVOTS.get(name,[128,155]),'mask':mp.relative_to(ART).as_posix()}
            p.with_suffix('.svg').write_text(svg(im,name,meta),'utf-8')
            nodes[name]={'raster':p.relative_to(ART).as_posix(),'svg':p.with_suffix('.svg').relative_to(ART).as_posix(),
                         'mask':mp.relative_to(ART).as_posix(),'sha256':sha(p),'pivot':meta['pivot']}
        for name in heads:nodes[name]={'raster':f'rig/sky/{name}.png','sha256':sha(RIG/f'{name}.png')}
        rig['skins'][skin]={'contract':contract,'parts':nodes}
    dump(RIG/'rig.json',rig)
    dump(GAME/'source/generation.json',{'calls':[{'skin':s,**i,'prompt':f'games/sky/source/{s}-prompt.txt',
        'generator':'built-in image_gen edit','source_refs':['reference/nabo-idle-original.png','design/round1/v2/01-hiker-design-board.png'],
        'reference_sha256':{'original':sha(ART/'reference/nabo-idle-original.png'),
                            'approved_hiker':sha(ART/'design/round1/v2/01-hiker-design-board.png')},
        'source_preserved':True,'no_ai_animation_frames':True} for s,i in SOURCES.items()],
        'head_acceptance':'Final rig discards edited heads and reuses frozen approved common identity, no new human approval claimed'})
    return rig


if __name__=='__main__':build()
