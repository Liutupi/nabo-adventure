"""NIGHT wardrobe sampling + immutable shared-head overlay, with inspectable local masks."""
import base64
import hashlib
import io
import json
import html
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import numpy as np
from night_config import ART,RIG,GAME,PREVIEW,SOURCE,FACING,ANCHOR,HEAD_SHIFT,POLYS,PIVOTS,ORDER


def reassign_torso_islands(parts):
    """Return garment islands to their limb/base instead of rotating loose scraps."""
    data=np.asarray(parts['torso']).copy();core=data[:,:,3]>=64
    visited=np.zeros(core.shape,bool);components=[]
    for y,x in zip(*np.where(core)):
        if visited[y,x]:continue
        queue=[(int(y),int(x))];visited[y,x]=True;component=[]
        while queue:
            yy,xx=queue.pop();component.append((yy,xx))
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<256 and 0<=nx<256 and core[ny,nx] and not visited[ny,nx]:
                        visited[ny,nx]=True;queue.append((ny,nx))
        components.append(component)
    components.sort(key=len,reverse=True);record=[]
    for component in components[1:]:
        ys,xs=zip(*component);x0,x1=max(0,min(xs)-1),min(256,max(xs)+2);y0,y1=max(0,min(ys)-1),min(256,max(ys)+2)
        destination='legs' if np.mean(ys)>=189 else 'upper_l' if np.mean(xs)<128 else 'upper_r'
        fragment=np.zeros_like(data);fragment[y0:y1,x0:x1]=data[y0:y1,x0:x1]
        parts[destination].alpha_composite(Image.fromarray(fragment,'RGBA'))
        data[y0:y1,x0:x1,3]=0
        record.append({'source_bbox':[x0,y0,x1,y1],'destination':destination,'core_pixels':len(component)})
    parts['torso']=Image.fromarray(data,'RGBA')
    return record


def complete_knee(parts,body):
    """Reveal same-source trousers below the resting hand when it covers a yawn."""
    data=np.asarray(body);best=None
    for y in range(196,209):
      for x in range(137,157):
        sample=data[y:y+5,x:x+5]
        if np.any(sample[:,:,3]<200) or sample[:,:,:3].mean()>130:continue
        score=float(sample[:,:,:3].astype(float).var(axis=(0,1)).mean())
        if best is None or score<best[0]:best=(score,x,y)
    if best is None:raise ValueError('No original trouser patch available for hand occlusion underlay')
    _,x,y=best;patch=body.crop((x,y,x+5,y+5)).resize((28,24),Image.Resampling.BICUBIC)
    colour=Image.new('RGBA',(256,256));colour.alpha_composite(patch,(154,184))
    skin=(data[:,:,0]>data[:,:,1]*1.10)&(data[:,:,1]>data[:,:,2]*1.04)&(data[:,:,0]>110)
    region=np.zeros((256,256),np.uint8);region[190:208,154:182]=np.where(skin[190:208,154:182],255,0)
    coverage=Image.fromarray(region,'L').filter(ImageFilter.MaxFilter(3))
    coverage=ImageChops.multiply(coverage,mask([(154,190),(182,190),(182,208),(154,208)]))
    colour.putalpha(ImageChops.multiply(colour.getchannel('A'),coverage))
    parts['legs'].alpha_composite(colour)
    return {'source_rect':[x,y,x+5,y+5],'target_area':[154,190,182,208],
            'mask':'original resting-hand skin coverage dilated one pixel; same-source low-variance trousers only'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def mask(points):
    m=Image.new('L',(256,256));ImageDraw.Draw(m).polygon(points,fill=255);return m


def svg(image,name,contract):
    buffer=io.BytesIO();image.save(buffer,'PNG')
    w,h=image.size
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
       f'<title>{name}: immutable source pixel slice, not vector character drawing</title>'
       '<metadata>'+html.escape(json.dumps(contract))+f'</metadata><image width="{w}" height="{h}" xlink:href="data:image/png;base64,'+
       base64.b64encode(buffer.getvalue()).decode('ascii')+'"/></svg>\n')


def normalized(skin,facing):
    info=SOURCE[skin];path=GAME/f'source/{skin}-source.png'
    assert sha(path)==info['sha256']
    source=Image.open(path).convert('RGBA')
    x0,x1=FACING[facing];nx,ny=info['necks'][facing]
    alpha=source.getchannel('A').point(lambda a:a if a>=16 else 0);source.putalpha(alpha)
    a=np.asarray(alpha)
    ys,xs=np.where((a[:,x0:x1]>=128)&(np.indices(a[:,x0:x1].shape)[0]>=ny))
    foot=int(ys.max()+1)
    sx=91/info['head_widths'][facing];sy=84/(foot-ny)
    window=Image.new('L',source.size);ImageDraw.Draw(window).rectangle((x0,ny-2,x1-1,source.height-1),fill=255)
    source.putalpha(ImageChops.multiply(alpha,window))
    # Inverse affine copies wardrobe below the neck only, with stable seated hips.
    sampled=source.transform((256,256),Image.Transform.AFFINE,
            (1/sx,0,nx-128/sx,0,1/sy,ny-140/sy),resample=Image.Resampling.BICUBIC)
    sampled.putalpha(ImageChops.multiply(sampled.getchannel('A'),mask([(0,138),(256,138),(256,256),(0,256)])))
    common=ART/f'rig/common/{facing}'
    head=Image.open(common/'head.png').convert('RGBA')
    expression=Image.open(common/'expression_neutral.png').convert('RGBA')
    # Local garment exclusion only. All face/hair/cap/eyewear RGB stays copied.
    trim=mask([(0,0),(256,0),(256,93),(137,93),(137,100),(121,100),(121,93),(0,93)])
    head.putalpha(ImageChops.multiply(head.getchannel('A'),trim))
    head_layer=Image.new('RGBA',(256,256));head_layer.alpha_composite(head,HEAD_SHIFT)
    exp_layer=Image.new('RGBA',(256,256));exp_layer.alpha_composite(expression,HEAD_SHIFT)
    whole=sampled.copy();whole.alpha_composite(head_layer);whole.alpha_composite(exp_layer)
    contract={'source_file':path.relative_to(ART).as_posix(),'source_sha256':sha(path),'neck_source':[nx,ny],
       'source_foot_bottom':foot,'wardrobe_scale':[sx,sy],'wardrobe_target_neck':[128,140],
       'source_view_window':[x0,ny-2,x1,source.height],
       'alpha_discard_below':16,'head_common':(common/'head.png').relative_to(ART).as_posix(),
       'head_sha256':sha(common/'head.png'),'head_offset':HEAD_SHIFT,
       'local_garment_exclusion':'y<94 retained; rows94..100 retain only neck x121..137; original RGB unmodified',
       'source_generated_head_discarded':True}
    return sampled,head_layer,exp_layer,whole,contract


def build():
    record={'skin_sources':SOURCE,'canvas':[256,256],'anchor':ANCHOR,'head_shift':HEAD_SHIFT,'views':{},'order':ORDER}
    for skin in SOURCE:
      record['views'][skin]={}
      for facing in FACING:
        folder=RIG/skin/facing;folder.mkdir(parents=True,exist_ok=True)
        body,head,expr,whole,contract=normalized(skin,facing)
        whole.save(folder/'normalized.png')
        body.save(folder/'wardrobe-before-underlay.png')
        # Source jar occludes cloth. Complete only that hidden garment region by
        # copying a same-source adjacent fabric patch, never touching head/skin RGB.
        underlay=body.copy();patch=body.crop((131,171,152,205)).resize((21,34),Image.Resampling.BICUBIC)
        underlay.alpha_composite(patch,(108,171))
        underlay.save(folder/'wardrobe-underlay.png')
        remaining=Image.new('L',(256,256),255);parts={}
        for name,points in POLYS.items():
            region=mask(points);region=ImageChops.multiply(region,remaining)
            remaining=ImageChops.subtract(remaining,region)
            layer=body.copy();layer.putalpha(ImageChops.multiply(body.getchannel('A'),region))
            parts[name]=layer
        torso=underlay.copy();torso.putalpha(ImageChops.multiply(underlay.getchannel('A'),remaining))
        # The completed fabric patch is behind a moving jar, irrespective of its partition.
        torso.alpha_composite(patch,(108,171))
        torso.putalpha(ImageChops.multiply(torso.getchannel('A'),mask([(0,0),(256,0),(256,198),(0,198)])))
        parts.update(torso=torso,head=head,expression=expr)
        # Reclaim original gripping-finger pixels from the jar partition, and use a
        # separate native glass object so lifted glass has no baked lap texture.
        data=np.asarray(body);skin_pixels=((data[:,:,0]>data[:,:,1]*1.10)&(data[:,:,1]>data[:,:,2]*1.04)&(data[:,:,0]>110))
        skin_pixels[:176]=False;skin_pixels[199:]=False;skin_pixels[:,:101]=False;skin_pixels[:,120:]=False
        fingers=body.copy();fingers.putalpha(Image.fromarray(np.where(skin_pixels,data[:,:,3],0).astype('uint8')))
        parts['forearm_l'].alpha_composite(fingers)
        # Never carry a patch of crossed trousers with a moving hand. Below each
        # cuff the original skin pixels alone belong to the forearm/hand layer.
        for name,row,box in [('forearm_l',184,(94,120)),('forearm_r',187,(153,182))]:
            part=np.asarray(parts[name]).copy()
            local_skin=(part[:,:,0]>part[:,:,1]*1.10)&(part[:,:,1]>part[:,:,2]*1.04)&(part[:,:,0]>110)
            keep=np.ones((256,256),dtype=bool);keep[row:]=local_skin[row:]
            residual=part.copy();residual[:,:,3]=np.where(~keep,part[:,:,3],0)
            lower=residual.copy();lower[:190,:,3]=0
            parts['legs'].alpha_composite(Image.fromarray(lower,'RGBA'))
            part[:,:,3]=np.where(keep,part[:,:,3],0)
            parts[name]=Image.fromarray(part,'RGBA')
        from night_props import glass_jar
        parts['jar']=glass_jar()
        # Source-pixel joint overlaps connect independently rotating sleeve pieces.
        for name,pivot in [('upper_l',PIVOTS['forearm_l']),('forearm_l',PIVOTS['forearm_l']),
                           ('upper_r',PIVOTS['forearm_r']),('forearm_r',PIVOTS['forearm_r'])]:
            circle=Image.new('L',(256,256));x,y=pivot;ImageDraw.Draw(circle).ellipse((x-5,y-5,x+5,y+5),fill=255)
            joint=body.copy();joint.putalpha(ImageChops.multiply(body.getchannel('A'),circle))
            parts[name].alpha_composite(joint)
        reassigned=reassign_torso_islands(parts)
        contract['garment_island_reassignment']=reassigned
        contract['knee_below_resting_hand']=complete_knee(parts,body)
        nodes={}
        for name,layer in parts.items():
            png=folder/f'{name}.png';layer.save(png)
            m={'part':name,**contract,'pivot':PIVOTS.get(name,(128,137)),
               'underlay_copy':{'source_rect':[131,171,152,205],'target_rect':[108,171,129,205]} if name=='torso' else None}
            (folder/f'{name}.svg').write_text(svg(layer,name,m),'utf-8')
            nodes[name]={'raster':png.relative_to(ART).as_posix(),'sha256':sha(png),'pivot':PIVOTS.get(name,(128,137)),
                         'mask_polygon':POLYS.get(name),'alpha_bbox':layer.getchannel('A').getbbox()}
        record['views'][skin][facing]={'contract':contract,'parts':nodes}
    (RIG/'rig.json').write_text(json.dumps(record,indent=2)+'\n','utf-8')
    return record


if __name__=='__main__':build()
