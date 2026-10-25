"""NIGHT native vector-style props only; no face or character is procedurally drawn."""
import json
from PIL import Image,ImageDraw
from night_config import GAME


def glass_jar():
    im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
    # Upright firefly jar. Its empty glass interior remains transparent; glow is separate.
    d.rounded_rectangle((110,173,128,207),radius=4,outline='#8ca5ac',width=2)
    d.ellipse((110,171,128,177),outline='#e9e4d2',width=2)
    d.line((112,177,112,200),fill='#dddccf',width=1)
    d.line((125,183,125,201),fill='#a7c4ca',width=1)
    d.arc((112,200,127,207),0,180,fill='#e9e4d2',width=1)
    return im


def static_assets():
    paths=[]
    for i in range(4):
        im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
        for j,(x,h) in enumerate([(4,10),(10,19),(16,15),(23,22),(28,12)]):
            y=31;h=max(5,h+(i*3+j*2)%7-3)
            d.polygon([(x-2,y),(x-5,31-h),(x,31-h+7),(x+3,31-h-3),(x+3,y)],fill=['#1d463d','#285346','#355f4b'][j%3])
        paths.append((f'grass_{i:02d}',im,'tiles',[16,31],8))
    for i in range(4):
        im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
        x=13+i
        d.polygon([(x-3,31),(x+3,31),(x+2,3),(x-1,0)],fill='#10252c')
        d.line((x,15,x-10,7),fill='#18323a',width=3)
        d.line((x,22,x+13,10),fill='#18323a',width=3)
        d.polygon([(0,11),(7,3),(15,8),(24,1),(32,9),(30,17),(18,13),(7,18)],fill='#1b3940')
        paths.append((f'tree_shadow_{i:02d}',im,'tiles',[16,31],8))
    glow=Image.new('RGBA',(32,32));d=ImageDraw.Draw(glow)
    d.ellipse((5,5,27,27),outline='white',width=1)
    for x,y in [(16,2),(16,30),(2,16),(30,16),(6,6),(26,26)]:d.point((x,y),fill='white')
    paths.append(('jar_glow',glow,'props',[16,16],2))
    moths=[]
    for i,width in enumerate([6,4,2,4]):
        im=Image.new('RGBA',(16,16));d=ImageDraw.Draw(im)
        d.ellipse((7-width,3,8,12),fill='#b8ab94',outline='#554e45',width=1)
        d.ellipse((7,3,8+width,12),fill='#b8ab94',outline='#554e45',width=1)
        d.line((7,5,7,13),fill='#342f2c',width=2)
        d.line((7,5,4,2),fill='#d5c7aa',width=1);d.line((8,5,11,2),fill='#d5c7aa',width=1)
        moths.append(im)
    for id,im,folder,anchor,limit in paths:
        dest=GAME/folder;dest.mkdir(parents=True,exist_ok=True);im.save(dest/f'{id}.png')
        # Native prop SVG wraps these deterministic object pixels, not a character redraw.
        from night_source import svg
        (dest/f'{id}.svg').write_text(svg(im,id,{'kind':'static native object','canvas':im.size,'not_character_art':True}),'utf-8')
    return paths,moths
