"""Every-frame contact sheets, real 1x scenery and loop/transition review."""
import html
from PIL import Image, ImageDraw
from climb_rig import ART
from rig_preview import font
from travel_export import durations

BACKGROUNDS={'cold-rock':'#b4c3cc','snow':'#e9edf0'}


def scene(c,frame_index=0,snow=False):
    screen=Image.new('RGBA',(240,320),'#d3dce3' if snow else '#8e9ba8')
    for side in (0,208):
        for y in range(32,290,32):
            tile=Image.open(ART/f'games/climb/tiles/{"snow" if snow else "cold"}-{(y//32)%2}.png').convert('RGBA')
            screen.alpha_composite(tile,(side,y))
    for x,y,kind in [(25,77,'normal'),(191,103,'ice'),(24,224,'fragile'),(191,244,'normal')]:
        screen.alpha_composite(Image.open(ART/f'games/climb/props/hold-{kind}.png').convert('RGBA'),(x,y))
    if snow:
        for x in (0,208):screen.alpha_composite(Image.open(ART/'map/tiles/ski/snow-mound.png').convert('RGBA'),(x,270))
    frame=c['runtime'][frame_index];a=c['runtime_palette']['anchor']
    root=(56,181) if c['facing']=='left' else (184,181) if c['facing']=='right' else (120,252)
    if c['facing'] in ('left','right'):
        contact=c['contacts']['per_frame'][frame_index]
        for point,kind in [(contact['grip_contact'],'normal'),(contact['foot_contact'],'normal')]:
            x=root[0]+point[0]-a[0];y=root[1]+point[1]-a[1]
            # The rock's upper lip receives fingertips/sole; its rear overlaps
            # the visible wall, so neither NABO nor the support floats.
            dx=14 if c['facing']=='left' else 10
            screen.alpha_composite(Image.open(ART/f'games/climb/props/hold-{kind}.png').convert('RGBA'),(x-dx,y-4))
    screen.alpha_composite(frame,(root[0]-a[0],root[1]-a[1]))
    d=ImageDraw.Draw(screen);d.rectangle((0,0,239,31),fill='#24354b')
    d.text((8,9),'CLIMB   148 m',fill='#f5f1dc',font=font(14))
    d.rectangle((0,290,239,319),fill='#24354b');d.text((8,299),'OK  switch / hold to charge',fill='#f5f1dc',font=font(12))
    return screen.convert('RGB')


def preview(clips):
    folder=ART/'preview/climb';folder.mkdir(parents=True,exist_ok=True)
    overview=Image.new('RGB',(720,320),'#24354b')
    htmlrows=[]
    for ci,((skin,name),c) in enumerate(clips.items()):
        count=len(c['frames']);cw=max(150,c['runtime'][0].width*3+12);ch=max(328,c['runtime'][0].height*3+140)
        contact=Image.new('RGB',(cw*count,ch*2),'#b4c3cc');d=ImageDraw.Draw(contact)
        for row,(world,color) in enumerate(BACKGROUNDS.items()):
            d.rectangle((0,row*ch,contact.width,(row+1)*ch),fill=color)
            d.text((8,row*ch+4),f'{skin}/{name} / 1x + 3x / {world}',fill='#24354b',font=font(13))
            for i,f in enumerate(c['runtime']):
                contact.paste(f,(i*cw+(cw-f.width)//2,row*ch+30),f)
                zoom=f.resize((f.width*3,f.height*3),Image.Resampling.NEAREST)
                contact.paste(zoom,(i*cw+(cw-zoom.width)//2,row*ch+112),zoom)
                d.text((i*cw+5,row*ch+ch-18),f'{i:03d}',fill='#24354b',font=font(12))
        contact.save(folder/f'{skin}-{name}-contact.png')
        gif=[]
        for frame in c['runtime']:
            im=Image.new('RGB',(240,240),'#b4c3cc');big=frame.resize((frame.width*3,frame.height*3),Image.Resampling.NEAREST)
            im.paste(big,((240-big.width)//2,12),big);gif.append(im)
        options={'loop':0} if c['loop'] else {}
        gif[0].save(folder/f'{skin}-{name}.gif',save_all=True,append_images=gif[1:],duration=durations(count),disposal=2,**options)
        htmlrows.append(f'<section><h2>{html.escape(skin+" / "+name)}</h2><img src="{skin}-{name}.gif"><p>{count} frames, 12fps, loop={c["loop"]}</p><img style="max-width:100%" src="{skin}-{name}-contact.png"></section>')
    for col,key in enumerate([('climb_a','grip_idle_left'),('climb_a','grip_idle_right'),('climb_b','grip_idle_left')]):
        c=clips[key];image=scene(c,snow=col==2);image.save(folder/f'{key[0]}-{key[1]}-scene-1x.png');overview.paste(image,(col*240,0))
    overview.save(folder/'overview-1x.png')
    image=scene(clips[('climb_a','settlement_cheer')],3,True);image.save(folder/'settlement-1x.png')
    tiles=[Image.open(ART/a) for a in ['games/climb/tiles/grey-0.png','games/climb/tiles/grey-1.png',
        'games/climb/tiles/cold-0.png','games/climb/tiles/cold-1.png','games/climb/tiles/snow-0.png','games/climb/tiles/snow-1.png',
        'games/climb/props/hold-normal.png','games/climb/props/hold-fragile.png','games/climb/props/hold-ice.png',
        'games/climb/props/falling-rock.png','games/climb/props/canteen.png','map/tiles/ski/snow-mound.png']]
    static=Image.new('RGBA',(96*6,120*2),'#24354b')
    for i,t in enumerate(tiles):static.alpha_composite(t.resize((t.width*3,t.height*3),Image.Resampling.NEAREST),((i%6)*96,(i//6)*120))
    static.convert('RGB').save(folder/'static-contact.png')
    (folder/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>CLIMB source-pixel review</title><style>body{background:#d3dce3;color:#24354b;font-family:Arial}img{image-rendering:pixelated}section{margin:24px 0;border-top:1px solid}</style><h1>CLIMB: 100 frames / 16 clips</h1><p>Shared original head pixels, independent left/right views. GIF is a centisecond approximation; PNGs/manifest are exact 12fps.</p><img src="overview-1x.png">'+''.join(htmlrows),'utf-8')
