"""Native cab assembly: a fixed ceiling cord, source-hand contact and 1x proof."""
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from shared_static_canvas import Canvas
from post_config import ART,GAME,PREVIEW,ROOT
from post_rig import sha


def load(path):return Image.open(path).convert('RGBA')


def hand_in_cab(grip,entry,cab):
    rr=entry['runtime_quantization'];box=rr['source_bbox'];scale=rr['scale']
    origin=[cab['driver_chest'][i]-entry['runtime_anchor'][i] for i in range(2)]
    point=[round(origin[i]+(grip[i]-box[i])*scale) for i in range(2)]
    # The neutral grip lies one source pixel below the half-body cut. The cord
    # rests against the last visible glove pixel, never below the cab sill.
    point[1]=min(point[1],cab['driver_chest'][1]-1)
    return point


def build_cord(entry,reports,cab):
    colors=json.loads((ART/'ui/design/round3/01-passport/palette.json').read_text('utf-8'))
    paths=[];svg=[];contacts=[];roof=cab['whistle_roof_anchor']
    for i,report in enumerate(reports):
        hand=hand_in_cab(report['grip_xy'],entry,cab);x,y=hand;rx,ry=roof
        c=Canvas(96,colors);c.layer('roof-fixed-whistle-cord')
        c.line([roof,hand],'ink',3);c.line([roof,hand],'gold',1)
        c.ellipse((x-2,y-2,x+2,y+2),'bronze',width=1)
        c.layer('fixed-ceiling-pulley')
        c.ellipse((rx-2,ry-2,rx+2,ry+2),'bronze',width=1)
        c.ellipse((rx,ry,rx,ry),'gold',None)
        c.image=c.image.crop((0,0,96,88));c.root.set('height','88');c.root.set('viewBox','0 0 96 88')
        path=GAME/'props/whistle-cord'/f'{i:03d}.png';c.save(path)
        paths.append(path.relative_to(ART).as_posix());svg.append(path.with_suffix('.svg').relative_to(ART).as_posix())
        contacts.append(dict(frame=i,source_grip_xy=report['grip_xy'],roof_anchor=roof,hand_contact=hand,
                             state='grasp' if i==2 else 'pull' if i==3 else 'approach' if i==1 else 'release' if i==4 else 'rest'))
    return dict(name='whistle-cord',skin='post_props',facing='right',fps=12,loop=False,
                frames=paths,runtime_frames=paths,canvas=[96,88],runtime_canvas=[96,88],
                anchor=[48,81],runtime_anchor=[48,81],color_limit=16,
                source_svg=svg,source_sha256=[sha(ART/p) for p in svg],
                coordinate_space='locomotive native top-left; same canvas/anchor as body, before actor and foreground',
                owner_animation='post_a/whistle',idle_frame=0,default_when_not_whistling=0,contacts=contacts,
                endpoint_policy='Ceiling pulley fixed at every frame; lower endpoint follows transformed glove. Neutral grip is clipped at the visible half-body boundary.' )


def compose_cab(entry,cab,index,cord=None,background=(148,202,106)):
    canvas=Image.new('RGBA',(96,88),background)
    canvas.alpha_composite(load(GAME/f'props/wheel-{index%4:03d}.png'))
    canvas.alpha_composite(load(ART/cab['path']))
    if cord:canvas.alpha_composite(load(ART/cord['runtime_frames'][index]))
    frame=load(ART/entry['runtime_frames'][index%len(entry['runtime_frames'])])
    origin=tuple(cab['driver_chest'][i]-entry['runtime_anchor'][i] for i in range(2))
    canvas.alpha_composite(frame,origin);canvas.alpha_composite(load(GAME/'props/cab-foreground.png'))
    return canvas


def preview_cord(entry,cab,cord,bg):
    frames=[compose_cab(entry,cab,i,cord,bg) for i in range(6)]
    board=Image.new('RGB',(6*304,412),'#e7d5ad');d=ImageDraw.Draw(board)
    font=ImageFont.truetype(str(ROOT.parent/'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf'),12)
    for i,frame in enumerate(frames):
        x=i*304;board.paste(frame,(x+104,24));board.paste(frame.resize((288,264),Image.Resampling.NEAREST),(x+8,128))
        d.text((x+8,3),f'{i:03d} / 40px driver / native + 3x',font=font,fill='#203849')
        frame.save(PREVIEW/f'post_a-whistle-cab-{i:03d}.png')
    board.save(PREVIEW/'whistle-cab-contact.png')
    # Frame durations telescope to exactly 500 ms at 12 fps (GIF 10 ms ticks).
    durations=[round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(6)]
    frames[0].convert('RGB').save(PREVIEW/'post_a-whistle-cab.gif',save_all=True,
        append_images=[f.convert('RGB') for f in frames[1:]],duration=durations,disposal=2)
