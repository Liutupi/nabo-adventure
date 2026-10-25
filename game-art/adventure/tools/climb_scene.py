"""Native 1x rock-wall tiles and gameplay props, with frozen shared snow reuse."""
from PIL import Image, ImageDraw
from climb_rig import ART, digest

COLORS={'ink':'#24354b','dark':'#46596b','slate':'#728293','stone':'#9da9b3','light':'#c9d3db',
        'snow':'#f5f1dc','ice':'#9ed0dc','deep':'#638caa','red':'#b64a44','gold':'#cfab68','green':'#637e63'}


def tile(theme,variant):
    sets={'grey':('slate','stone','dark','light'),'cold':('deep','light','dark','ice'),
          'snow':('light','snow','slate','ice')}
    base,face,shadow,edge=[COLORS[n] for n in sets[theme]]
    im=Image.new('RGBA',(32,32),base);d=ImageDraw.Draw(im)
    if variant==0:
        d.polygon([(0,0),(21,0),(23,7),(17,16),(0,19)],fill=face)
        d.polygon([(23,0),(31,0),(31,25),(20,29),(17,17),(24,7)],fill=shadow)
        d.line([(0,20),(16,17),(21,30),(31,26)],fill=COLORS['ink'])
        d.line([(20,0),(22,7),(17,16)],fill=edge)
        d.line([(3,4),(13,3),(17,5)],fill=edge)
        d.line([(3,28),(11,25),(15,26)],fill=shadow)
    else:
        d.polygon([(0,0),(8,0),(14,11),(8,19),(0,17)],fill=shadow)
        d.polygon([(10,0),(31,0),(31,14),(16,12)],fill=face)
        d.polygon([(10,20),(18,15),(31,17),(31,31),(13,31)],fill=face)
        d.line([(7,0),(13,12),(8,19),(12,31)],fill=COLORS['ink'])
        d.line([(14,12),(31,15)],fill=COLORS['ink'])
        d.line([(18,20),(26,19),(29,22)],fill=edge)
    if theme=='snow':
        d.polygon([(0,0),(31,0),(31,4),(25,5),(22,3),(17,5),(10,4),(7,7),(0,5)],fill=COLORS['snow'])
        d.line([(0,6),(7,8),(11,5),(18,6)],fill=COLORS['ice'])
    return im


def hold(kind):
    im=Image.new('RGBA',(24,20));d=ImageDraw.Draw(im)
    d.polygon([(2,8),(7,3),(18,2),(22,7),(20,15),(8,18),(2,14)],fill=COLORS['ink'])
    d.polygon([(4,8),(8,5),(17,4),(20,7),(17,12),(7,14),(4,12)],fill=COLORS['stone'])
    d.line([(6,7),(12,6),(17,6)],fill=COLORS['snow'],width=2)
    d.line([(5,15),(12,15),(19,12)],fill=COLORS['dark'],width=2)
    if kind=='fragile':
        d.line([(12,4),(10,9),(14,11),(11,16)],fill=COLORS['ink'],width=2)
        d.line([(10,9),(6,10)],fill=COLORS['ink'])
        d.point((20,17),fill=COLORS['stone']);d.point((2,18),fill=COLORS['stone'])
    elif kind=='ice':
        d.polygon([(3,8),(8,3),(18,3),(21,7),(18,12),(7,14)],fill=COLORS['ice'])
        d.line([(7,5),(16,5),(18,7)],fill=COLORS['snow'],width=2)
        d.polygon([(6,13),(9,13),(8,19)],fill=COLORS['ice'])
        d.polygon([(16,11),(19,11),(18,17)],fill=COLORS['ice'])
    return im


def props():
    rock=Image.new('RGBA',(24,24));d=ImageDraw.Draw(rock)
    d.polygon([(4,6),(12,2),(20,6),(22,17),(14,22),(4,18),(1,12)],fill=COLORS['ink'])
    d.polygon([(5,7),(12,4),(18,7),(12,12),(4,11)],fill=COLORS['light'])
    d.polygon([(4,12),(12,13),(14,20),(5,17)],fill=COLORS['slate'])
    d.polygon([(14,12),(19,8),(20,16),(16,19)],fill=COLORS['dark'])
    bottle=Image.new('RGBA',(16,24));d=ImageDraw.Draw(bottle)
    d.line([(2,7),(2,17),(5,21)],fill=COLORS['dark'],width=2)
    d.rounded_rectangle((4,6,14,22),radius=4,fill=COLORS['ink'])
    d.rounded_rectangle((6,8,12,20),radius=2,fill=COLORS['green'])
    d.rectangle((6,3,11,7),fill=COLORS['ink']);d.rectangle((7,2,10,4),fill=COLORS['gold'])
    d.line([(7,10),(7,16)],fill=COLORS['light']);d.rectangle((8,13,10,15),fill=COLORS['snow'])
    return {'falling-rock':rock,'canteen':bottle}


def build_scene():
    assets=[]
    def save(relative,image,anchor,limit=16):
        path=ART/'games/climb'/relative;path.parent.mkdir(parents=True,exist_ok=True);image.save(path)
        assets.append({'id':'climb/'+relative[:-4],'path':path.relative_to(ART).as_posix(),
                       'sha256':digest(path),'size':list(image.size),'anchor':anchor,'color_limit':limit})
    for theme in ('grey','cold','snow'):
        for i in range(2):save(f'tiles/{theme}-{i}.png',tile(theme,i),[0,0])
    for kind in ('normal','fragile','ice'):save(f'props/hold-{kind}.png',hold(kind),[12,9])
    for name,image in props().items():save('props/'+name+'.png',image,[image.width//2,image.height])
    for name,path in [('snow-drift','map/tiles/mountain/snow-drift.png'),('snow-mound','map/tiles/ski/snow-mound.png')]:
        image=Image.open(ART/path)
        assets.append({'id':'climb/shared/'+name,'path':path,'sha256':digest(ART/path),
                       'size':list(image.size),'anchor':[0,0],'color_limit':16,'shared_with':['climb','ski'],
                       'policy':'frozen shared source reference; not copied or regenerated'})
    return assets
