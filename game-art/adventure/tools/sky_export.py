"""Stable half/full SKY target sampling and actual-size preview compositions."""
import numpy as np
from PIL import Image,ImageDraw
from sky_config import ART,PREVIEW,SKY,GAME
from sky_rig import sha
from rig_preview import quantize,font


def save_frames(folder,frames):
    folder.mkdir(parents=True,exist_ok=True);paths=[];hashes=[]
    for i,im in enumerate(frames):
        p=folder/f'{i:03d}.png';im.save(p);paths.append(p.relative_to(ART).as_posix());hashes.append(sha(p))
    return paths,hashes


def geometry(clips,height):
    boxes=[f.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox() for c in clips for f in c['raw']]
    floor=224 if height==72 else 160
    bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),floor]
    if height==40:bbox[0]=min(bbox[0],65);bbox[2]=max(bbox[2],199)
    scale=height/(floor-bbox[1]);width=round((bbox[2]-bbox[0])*scale)
    return {'bbox':bbox,'scale':scale,'canvas':[width,height],'anchor':[round((128-bbox[0])*scale),height]}


def export_group(clips,geom):
    raw=[f for c in clips for f in c['raw']]
    resized=[f.crop(geom['bbox']).resize(tuple(geom['canvas']),Image.Resampling.LANCZOS) for f in raw]
    frames,report=quantize(resized,63,round(geom['canvas'][1]*(.63 if geom['canvas'][1]==40 else .43)))
    report.update(geometry=geom,height_policy='One union silhouette envelope and scale for all skins at target height; animation pose extent may be shorter')
    cursor=0
    for c in clips:
        n=len(c['raw']);c['runtime']=frames[cursor:cursor+n];c['runtime_report']=report;cursor+=n


def durations(n):return [round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(n)]


def gif(path,frames):
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations(len(frames)),loop=0,disposal=2)


def preview_clip(skin,name,clip):
    frames=clip['runtime'];cw=max(180,frames[0].width*3+20);ch=340
    out=Image.new('RGB',(cw*len(frames),ch),SKY);d=ImageDraw.Draw(out);gifs=[];rigs=[]
    for i,(im,master) in enumerate(zip(frames,clip['raw'])):
        x=i*cw;d.text((x+4,4),f'{skin} {name} {i:02d}',font=font(12),fill='#243f4e')
        out.paste(im,(x+18,25),im);large=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
        out.paste(large,(x+18,110),large)
        fg=Image.new('RGB',(cw,250),SKY);fg.paste(large,((cw-large.width)//2,240-large.height),large);gifs.append(fg)
        bg=Image.new('RGBA',(256,256),SKY);bg.alpha_composite(master);rigs.append(bg.convert('RGB'))
    out.save(PREVIEW/f'{skin}-{name}-contact.png');gif(PREVIEW/f'{skin}-{name}.gif',gifs)
    gif(PREVIEW/f'{skin}-{name}-rig.gif',rigs)


def scene(character,anchor,ropes=None,stamp_at=None,bird_index=0):
    out=Image.new('RGBA',(240,320),SKY)
    for i,xy in enumerate([(150,62),(12,151),(174,207),(128,281)]):
        im=Image.open(GAME/f'tiles/cloud_{i:02d}.png').convert('RGBA');out.alpha_composite(im,xy)
    out.alpha_composite(Image.open(GAME/'props/envelope.png').convert('RGBA'),(32,60))
    d=ImageDraw.Draw(out)
    for start,end in [((69,151),(50,242)),((91,151),(110,242))]:d.line((*start,*end),fill='#654f3f',width=1)
    # Controls and burner are behind the character; the original white cap stays clear.
    starts=[64,99]
    if ropes is not None:
        ink=np.asarray(ropes)[0];starts=[80-anchor[0]+int(np.where((ink[:,:3]==rgb).all(axis=1)&(ink[:,3]>0))[0][0])
                                       for rgb in [(116,91,68),(64,91,103)]]
    d.line((73,151,starts[0],248-anchor[1]),fill='#745b44',width=1)
    d.line((88,151,starts[1],248-anchor[1]),fill='#405b67',width=1)
    out.alpha_composite(Image.open(GAME/'props/burner.png').convert('RGBA'),(72,184))
    out.alpha_composite(Image.open(GAME/'props/basket_back.png').convert('RGBA'),(48,240))
    if ropes is not None:out.alpha_composite(ropes,(80-anchor[0],248-anchor[1]))
    out.alpha_composite(character,(80-anchor[0],248-anchor[1]))
    out.alpha_composite(Image.open(GAME/'props/basket_front.png').convert('RGBA'),(48,240))
    bird=Image.open(GAME/f'bird/{bird_index%4:03d}.png').convert('RGBA');out.alpha_composite(bird,(174,134))
    out.alpha_composite(Image.open(GAME/'props/thundercloud.png').convert('RGBA'),(160,28))
    if stamp_at:
        stamp=Image.open(GAME/'props/stamp.png').convert('RGBA')
        out.alpha_composite(stamp,(round(stamp_at[0]-8),round(stamp_at[1]-10)))
    return out.convert('RGB')
