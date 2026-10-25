"""Native layered 96px lander and 1x surface props; no flames or star particles."""
from PIL import Image,ImageDraw
from space_rig import ART,digest

P={'ink':'#24354b','deep':'#131b36','slate':'#52677f','steel':'#8eacba','ice':'#c9dce2',
   'paper':'#f5f1dc','gold':'#cfab68','darkgold':'#8f7041','teal':'#5daeb1','red':'#b64a44','lunar':'#758194'}


def lander():
    back=Image.new('RGBA',(96,96));d=ImageDraw.Draw(back)
    # Cabin opening is intentionally transparent: insert crew before front rim.
    d.polygon([(17,63),(79,63),(88,76),(72,81),(24,81),(8,76)],fill=P['ink'])
    d.polygon([(19,64),(77,64),(82,74),(69,77),(27,77),(14,74)],fill=P['slate'])
    for flip in (False,True):
        def pt(x,y):return (95-x,y) if flip else (x,y)
        d.polygon([pt(x,y) for x,y in [(16,54),(23,61),(14,85),(7,89),(4,85)]],fill=P['ink'])
        d.polygon([pt(x,y) for x,y in [(17,59),(20,62),(12,84),(8,85)]],fill=P['steel'])
        d.polygon([pt(x,y) for x,y in [(2,87),(16,87),(19,91),(1,91)]],fill=P['ink'])
        d.line([pt(3,88),pt(15,88)],fill=P['gold'],width=2)
    d.polygon([(38,76),(58,76),(62,88),(34,88)],fill=P['ink'])
    d.polygon([(41,78),(55,78),(58,85),(38,85)],fill=P['steel'])
    d.rectangle((38,86,57,89),fill=P['ink']);d.line((40,87,55,87),fill=P['slate'])
    d.arc((14,2,81,73),180,360,fill=P['ink'],width=4)
    d.line((15,35,15,65),fill=P['ink'],width=4);d.line((80,35,80,65),fill=P['ink'],width=4)
    d.arc((17,5,78,70),185,355,fill=P['steel'],width=2)
    # Side fuel modules, couplings and landing struts remain behind crew.
    for x in (5,82):
        d.rounded_rectangle((x,36,x+8,64),radius=3,fill=P['ink'])
        d.rectangle((x+2,40,x+6,59),fill=P['ice']);d.rectangle((x+2,47,x+6,50),fill=P['teal'])
    front=Image.new('RGBA',(96,96));d=ImageDraw.Draw(front)
    d.polygon([(17,61),(79,61),(83,72),(69,80),(27,80),(13,72)],fill=P['ink'])
    d.polygon([(20,63),(76,63),(78,70),(67,76),(29,76),(18,70)],fill=P['steel'])
    d.polygon([(30,64),(66,64),(64,70),(32,70)],fill=P['slate'])
    d.rectangle((40,65,55,68),fill=P['teal']);d.rectangle((28,65,31,68),fill=P['gold'])
    d.rectangle((64,65,67,68),fill=P['gold']);d.line((26,74,68,74),fill=P['paper'])
    d.line((16,35,16,60),fill=P['ice']);d.line((79,35,79,60),fill=P['ice'])
    return back,front


def surface(index):
    im=Image.new('RGBA',(32,32),P['lunar']);d=ImageDraw.Draw(im)
    if index==0:
        d.ellipse((3,7,18,19),fill=P['slate']);d.arc((3,7,18,19),190,350,fill=P['ice'])
        d.ellipse((7,10,16,17),fill=P['steel']);d.ellipse((23,22,29,26),fill=P['slate'])
        d.point((3,26),fill=P['ice']);d.line((24,4,29,5),fill=P['steel'])
    elif index==1:
        d.polygon([(0,18),(9,13),(18,16),(26,12),(31,15),(31,20),(22,18),(14,22),(4,21)],fill=P['slate'])
        d.line([(0,17),(9,12),(18,15),(26,11),(31,14)],fill=P['ice'])
        d.ellipse((17,24,26,30),fill=P['steel']);d.arc((17,24,26,30),0,165,fill=P['slate'])
    else:
        d.polygon([(2,12),(10,4),(17,7),(23,17),(19,23),(5,24)],fill=P['ink'])
        d.polygon([(4,12),(10,6),(16,9),(18,16),(6,17)],fill=P['steel'])
        d.polygon([(7,19),(18,17),(20,20),(17,22),(7,22)],fill=P['slate'])
    return im


def props():
    pad=Image.new('RGBA',(96,24));d=ImageDraw.Draw(pad)
    d.polygon([(7,5),(89,5),(95,11),(91,20),(5,20),(0,11)],fill=P['ink'])
    d.rectangle((8,7,87,13),fill=P['steel']);d.rectangle((10,8,85,10),fill=P['paper'])
    d.line((9,16,86,16),fill=P['slate']);d.rectangle((44,7,51,12),fill=P['gold'])
    for x in (9,83):d.rectangle((x,2,x+3,7),fill=P['teal'])
    fuel=Image.new('RGBA',(16,24));d=ImageDraw.Draw(fuel)
    d.rectangle((4,0,11,3),fill=P['ink']);d.rounded_rectangle((2,3,13,22),radius=4,fill=P['ink'])
    d.rounded_rectangle((4,5,11,20),radius=2,fill=P['steel']);d.rectangle((4,9,11,15),fill=P['gold'])
    d.line((5,6,5,8),fill=P['paper']);d.rectangle((6,10,9,13),fill=P['slate'])
    rock=Image.new('RGBA',(32,28));d=ImageDraw.Draw(rock)
    d.polygon([(3,8),(12,1),(24,4),(30,14),(24,25),(10,27),(1,20)],fill=P['ink'])
    d.polygon([(5,9),(13,3),(22,6),(24,12),(13,17),(3,18)],fill=P['steel'])
    d.polygon([(13,18),(26,13),(27,19),(23,23),(12,25)],fill=P['slate'])
    d.ellipse((8,8,15,14),fill=P['slate']);d.arc((8,8,15,14),180,320,fill=P['ice'])
    flag=Image.new('RGBA',(16,28));d=ImageDraw.Draw(flag)
    d.line((2,0,2,27),fill=P['ink'],width=2);d.line((3,0,3,27),fill=P['steel'])
    d.polygon([(4,1),(14,2),(13,7),(15,11),(4,10)],fill=P['ink'])
    d.polygon([(5,2),(13,3),(12,7),(13,9),(5,8)],fill=P['teal'])
    d.line([(6,6),(8,4),(10,7),(11,5)],fill=P['paper'])
    return {'landing-pad':pad,'fuel-can':fuel,'asteroid':rock,'flag':flag}


def build_scene():
    assets=[]
    def save(name,im,anchor,limit=16):
        p=ART/'games/space'/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
        assets.append({'id':'space/'+name[:-4],'path':p.relative_to(ART).as_posix(),'sha256':digest(p),
                       'size':list(im.size),'anchor':anchor,'color_limit':limit})
    back,front=lander();save('lander/back.png',back,[48,92]);save('lander/front.png',front,[48,92])
    for i in range(3):save(f'tiles/lunar-{i}.png',surface(i),[0,0])
    for name,im in props().items():save('props/'+name+'.png',im,[2,28] if name=='flag' else [im.width//2,im.height])
    return assets
