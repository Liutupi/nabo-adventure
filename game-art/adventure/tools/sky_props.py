"""Native flat-color SKY environment and props; never draw character pixels."""
import math
from PIL import Image,ImageDraw,ImageChops
from sky_config import GAME
from sky_rig import svg


def envelope():
    im=Image.new('RGBA',(96,96));shape=Image.new('L',im.size);d=ImageDraw.Draw(shape)
    d.ellipse((4,1,91,73),fill=255);d.polygon([(13,58),(82,58),(61,94),(35,94)],fill=255)
    # Discrete fabric gores: only solid tones, engine owns brightness/lighting.
    colour=Image.new('RGBA',im.size,'#354e54');d=ImageDraw.Draw(colour)
    d.ellipse((7,3,88,74),fill='#cf8a65');d.polygon([(16,57),(79,57),(59,91),(37,91)],fill='#b96f54')
    d.ellipse((19,3,76,76),fill='#e9d9b5');d.polygon([(26,56),(69,56),(56,92),(40,92)],fill='#d6c098')
    d.ellipse((33,3,62,76),fill='#4b7a80');d.polygon([(36,56),(59,56),(52,92),(44,92)],fill='#355e66')
    d.arc((7,3,88,74),190,290,fill='#f0d8b1',width=2)
    d.line((35,92,61,92),fill='#31474d',width=3)
    im.paste(colour,(0,0),shape)
    return im


def basket():
    front=Image.new('RGBA',(64,28));d=ImageDraw.Draw(front)
    d.rounded_rectangle((1,1,62,26),radius=4,fill='#956943',outline='#473f36',width=2)
    d.rectangle((3,4,60,8),fill='#c09862');d.line((4,10,59,10),fill='#6f5039',width=1)
    for y in [13,17,21]:
        d.line((5,y,58,y),fill='#b88956',width=1)
        for x in range(7+(y%3)*3,59,9):d.line((x,y-2,x,y+1),fill='#634b37',width=1)
    d.line((8,25,55,25),fill='#473f36',width=2)
    back=Image.new('RGBA',(64,10));d=ImageDraw.Draw(back)
    d.rounded_rectangle((1,1,62,9),radius=4,fill='#594532',outline='#3d3e35',width=2)
    d.line((6,2,57,2),fill='#b18a58',width=2)
    return front,back


def static_assets():
    front,back=basket();result=[('envelope',envelope(),[48,94],16),('basket_front',front,[32,2],16),('basket_back',back,[32,2],8)]
    for i in range(4):
        im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
        for box in [(1,16-i,19,27-i),(9,10-i,27,27-i),(18,16-i,31,26-i)]:d.ellipse(box,fill='#eaf1ec')
        d.rectangle((8,19-i,27,27-i),fill='#eaf1ec');d.line((5,27-i,27,27-i),fill='#b6d4e4',width=2)
        if i%2:d.ellipse((13,10-i,24,19-i),fill='#f7f5e9')
        result.append((f'cloud_{i:02d}',im,[16,26-i],8))
    cloud=Image.new('RGBA',(48,32));d=ImageDraw.Draw(cloud)
    for box in [(1,11,24,29),(11,2,36,28),(25,9,47,29)]:d.ellipse(box,fill='#4c6475')
    d.rectangle((11,15,38,27),fill='#4c6475');d.line((7,27,41,27),fill='#344958',width=3)
    d.polygon([(24,14),(20,23),(25,23),(22,31),(33,20),(27,20),(30,14)],fill='#ead08a')
    result.append(('thundercloud',cloud,[24,29],8))
    stamp=Image.new('RGBA',(16,20));d=ImageDraw.Draw(stamp)
    d.rectangle((1,1,14,18),fill='#e9d9b5',outline='#624e3e',width=1)
    for x in range(2,15,3):d.point((x,0),fill='#e9d9b5');d.point((x,19),fill='#e9d9b5')
    for y in range(2,19,3):d.point((0,y),fill='#e9d9b5');d.point((15,y),fill='#e9d9b5')
    d.rectangle((3,3,12,15),outline='#9f6753',width=1);d.ellipse((5,5,10,10),fill='#47777d')
    d.line((6,10,7,13),fill='#624e3e',width=1);d.line((9,10,8,13),fill='#624e3e',width=1)
    d.rectangle((7,12,8,14),fill='#9f6753');result.append(('stamp',stamp,[8,10],8))
    burner=Image.new('RGBA',(16,12));d=ImageDraw.Draw(burner)
    d.rectangle((3,4,12,9),fill='#43545a',outline='#2c3e47',width=1)
    d.line((4,3,11,3),fill='#b18a58',width=2);d.rectangle((6,0,9,3),fill='#d5b785')
    result.append(('burner',burner,[8,6],8))
    for name,im,anchor,limit in result:
        folder=GAME/('tiles' if name.startswith('cloud') else 'props');folder.mkdir(parents=True,exist_ok=True)
        im.save(folder/f'{name}.png');(folder/f'{name}.svg').write_text(svg(im,name,{'native_prop':True,'no_character_redraw':True,'anchor':anchor}),'utf-8')
    birds=[]
    for i in range(4):
        im=Image.new('RGBA',(24,20));d=ImageDraw.Draw(im)
        d.ellipse((7,8,18,14),fill='#ded3b9',outline='#435b65',width=1)
        wings=[[(11,10),(3,0),(4,8),(12,13)],[(11,10),(0,8),(4,12),(13,12)],
               [(11,9),(3,18),(8,16),(14,11)],[(11,10),(2,5),(4,10),(13,12)]][i]
        d.polygon(wings,fill='#7d9399');d.line(wings[:3],fill='#435b65',width=1)
        d.polygon([(18,10),(23,11),(18,12)],fill='#b78155');d.point((17,9),fill='#293e48')
        d.polygon([(8,11),(3,13),(8,13)],fill='#435b65');birds.append(im)
    return result,birds
