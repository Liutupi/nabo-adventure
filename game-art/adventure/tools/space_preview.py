"""SPACE 1x crew/lander/planet composite, all-frame contacts and prop playback."""
import html
from PIL import Image,ImageDraw
from space_rig import ART
from rig_preview import font
from travel_export import durations

WORLD='#131b36'


def crew_image(c,index,persistent_flag=None):
    f=c['runtime'][index];canvas=Image.new('RGBA',(96,96));a=c['runtime_palette']['anchor'];root=(48,78)
    if c['name']=='plant_flag' or persistent_flag is not None:
        info=c['attachments']['flag'][index] if persistent_flag is None else persistent_flag
        if info['visible']:
            x,y=info['top_left'];canvas.alpha_composite(Image.open(ART/'games/space/props/flag.png').convert('RGBA'),(root[0]-a[0]+x,root[1]-a[1]+y))
    canvas.alpha_composite(f,(root[0]-a[0],root[1]-a[1]));return canvas


def compose_lander(c,index):
    back=Image.open(ART/'games/space/lander/back.png').convert('RGBA');front=Image.open(ART/'games/space/lander/front.png').convert('RGBA')
    a=c['runtime_palette']['anchor'];f=c['runtime'][index]
    back.alpha_composite(f,(48-a[0],70-a[1]));back.alpha_composite(front);return back


def scene(c,index=0,landed=True,flag=False,persistent_flag=None):
    im=Image.new('RGBA',(240,320),WORLD)
    for x in range(0,240,32):
        for y in (286,318):im.alpha_composite(Image.open(ART/f'games/space/tiles/lunar-{(x//32)%3}.png').convert('RGBA'),(x,y))
    pad=Image.open(ART/'games/space/props/landing-pad.png').convert('RGBA')
    if not flag:im.alpha_composite(pad,(72,270))
    if flag:
        f=crew_image(c,index,persistent_flag);im.alpha_composite(f,(65,208))
    else:
        lander=compose_lander(c,index);root=(120,278 if landed else 217)
        im.alpha_composite(lander,(root[0]-48,root[1]-92))
    # A displayed fuel can/asteroid, no fake program-drawn star/flame source.
    im.alpha_composite(Image.open(ART/'games/space/props/fuel-can.png').convert('RGBA'),(200,76))
    im.alpha_composite(Image.open(ART/'games/space/props/asteroid.png').convert('RGBA'),(24,58))
    d=ImageDraw.Draw(im);d.rectangle((0,0,239,31),fill='#24354b')
    d.text((8,9),'SPACE   760',fill='#f5f1dc',font=font(14));d.rectangle((0,290,239,319),fill='#24354b')
    d.text((8,299),'OK thrust    UP / DOWN tilt',fill='#f5f1dc',font=font(12))
    return im.convert('RGB')


def preview(clips):
    folder=ART/'preview/space';folder.mkdir(parents=True,exist_ok=True);sections=[]
    for (skin,name),c in clips.items():
        count=len(c['frames']);cw=240;ch=410;sheet=Image.new('RGB',(cw*count,ch*2),WORLD);d=ImageDraw.Draw(sheet)
        for row,color in enumerate((WORLD,'#758194')):
            d.rectangle((0,row*ch,sheet.width,(row+1)*ch),fill=color)
            d.text((6,row*ch+5),f'{skin}/{name}: 1x + 3x; dome clear, original face',fill='#f5f1dc',font=font(14))
            for i in range(count):
                composite=crew_image(c,i);sheet.paste(composite,(i*cw+72,row*ch+28),composite)
                crop=composite.crop((0,0,96,96));zoom=crop.resize((288,288),Image.Resampling.NEAREST)
                # Crop transparent side margins equally; visible glyphs stay inside.
                zoom=zoom.crop((24,0,264,288));sheet.paste(zoom,(i*cw,row*ch+114),zoom)
        sheet.save(folder/f'{skin}-{name}-contact.png')
        frames=[]
        for i in range(count):
            canvas=Image.new('RGB',(288,288),WORLD);part=crew_image(c,i).resize((288,288),Image.Resampling.NEAREST);canvas.paste(part,(0,0),part);frames.append(canvas)
        options={'loop':0} if c['loop'] else {}
        frames[0].save(folder/f'{skin}-{name}.gif',save_all=True,append_images=frames[1:],duration=durations(count),disposal=2,**options)
        sections.append(f'<section><h2>{html.escape(skin+"/"+name)}</h2><img src="{skin}-{name}.gif"><p>{count} frames / 12fps / loop={c["loop"]}</p><img style="max-width:100%" src="{skin}-{name}-contact.png"></section>')
    overview=Image.new('RGB',(960,320),WORLD)
    for col,(key,landed,flag,i) in enumerate([(('space_a','cabin_idle'),False,False,0),(('space_a','land'),True,False,5),
        (('space_a','plant_flag'),True,True,6),(('space_b','cabin_idle'),True,False,0)]):
        image=scene(clips[key],i,landed,flag);overview.paste(image,(col*240,0));image.save(folder/f'scene-{col}-1x.png')
    overview.save(folder/'overview-1x.png')
    parts=[Image.open(ART/p).convert('RGBA') for p in ['games/space/lander/back.png','games/space/lander/front.png',
        'games/space/props/landing-pad.png','games/space/props/fuel-can.png','games/space/props/asteroid.png','games/space/props/flag.png',
        'games/space/tiles/lunar-0.png','games/space/tiles/lunar-1.png','games/space/tiles/lunar-2.png']]
    static=Image.new('RGBA',(600,600),WORLD)
    for i,p in enumerate(parts):static.alpha_composite(p.resize((p.width*2,p.height*2),Image.Resampling.NEAREST),((i%3)*200,(i//3)*200))
    # Large lander parts receive a separate fully uncropped layer sheet below.
    static.convert('RGB').save(folder/'static-contact.png')
    layers=Image.new('RGBA',(96*3,96),WORLD)
    for i,p in enumerate([parts[0],compose_lander(clips[('space_a','cabin_idle')],0),parts[1]]):layers.alpha_composite(p,(i*96,0))
    layers.convert('RGB').save(folder/'lander-layers-1x.png')
    flag_continuity(clips,folder)
    (folder/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>SPACE review</title><style>body{background:#131b36;color:#f5f1dc;font-family:Arial}img{image-rendering:pixelated}section{border-top:1px solid;margin:24px 0}</style><h1>SPACE: 58 frames / 9 clips</h1><p>56px crew including clear binary dome; 72px settlement. Independent source-pixel NABO head. Flag is a separate prop layer with explicit per-frame attachment.</p><img src="overview-1x.png"><p>Lander back / crew composite / front</p><img src="lander-layers-1x.png">'+''.join(sections),'utf-8')


def flag_continuity(clips,folder):
    """Show real 56px placement, touchdown before release, and latched world prop."""
    flag=clips[('space_a','plant_flag')];idle=clips[('space_a','cabin_idle')]
    latched=flag['attachments']['flag'][5];frames=[];labels=[]
    stages=[(idle,i,None,'idle / flag stored') for i in range(6)]
    stages += [(flag,i,None,flag['attachments']['flag'][i]['phase']) for i in range(8)]
    stages += [(idle,i,latched,'idle / planted world flag retained') for i in range(6)]
    for c,i,held,label in stages:
        frame=scene(c,i,True,True,held);d=ImageDraw.Draw(frame)
        d.text((6,36),label,fill='#f5f1dc',font=font(11));frames.append(frame);labels.append(label)
    frames[0].save(folder/'plant-flag-persist.gif',save_all=True,append_images=frames[1:],
                   duration=durations(len(frames)),loop=0,disposal=2)
    sheet=Image.new('RGB',(240*5,320*4),WORLD)
    for j,frame in enumerate(frames):sheet.paste(frame,((j%5)*240,(j//5)*320))
    sheet.save(folder/'plant-flag-persist-contact.png')
    contact=Image.new('RGB',(240*8,390),WORLD);d=ImageDraw.Draw(contact)
    for i in range(8):
        part=crew_image(flag,i);d.text((i*240+4,4),f'{i}: '+flag['attachments']['flag'][i]['phase'],fill='#f5f1dc',font=font(12))
        ImageDraw.Draw(part).line((0,78,95,78),fill='#8e9ba8',width=1)
        contact.paste(part,(i*240+72,24),part)
        big=part.resize((288,288),Image.Resampling.NEAREST).crop((24,0,264,288))
        contact.paste(big,(i*240,100),big)
    contact.save(folder/'flag-ground-contact.png')
