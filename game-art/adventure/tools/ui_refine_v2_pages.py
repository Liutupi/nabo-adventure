"""Three native 240x320 typography explorations; frozen production assets read-only."""
import json
from PIL import Image,ImageDraw
from ui_refine_v2_fonts import ART,P,color,Type


def blank():return Image.new('RGBA',(240,320),color('white'))
def paste(canvas,path,xy,size=None):
    im=Image.open(ART/path).convert('RGBA')
    if size:im=im.resize(size,Image.Resampling.NEAREST)
    canvas.alpha_composite(im,xy)


def character(canvas,name,root):
    m=json.loads((ART/'manifest.json').read_text('utf-8'));e=next(e for e in m['animations'] if e['skin']=='travel' and e['name']==name)
    path=e['runtime_frames'][0];a=e['runtime_anchor'];paste(canvas,path,(root[0]-a[0],root[1]-a[1]))
    return {'path':path,'sha256':e['runtime_sha256'][0],'anchor':a,'root':root,'operation':'unchanged PNG; no resize/recolor/head redraw'}


def bars(im,t,title,left,right):
    d=ImageDraw.Draw(im);d.rectangle((0,0,239,31),fill=color('ink'));d.rectangle((8,8,11,23),fill=color('accent'))
    t.draw(im,(20,8),title,18,ink='white',paper='ink')
    t.draw(im,(224,11),right,12,'latin',ink='white',paper='ink',align='right')
    d.rectangle((0,290,239,319),fill=color('ink'))
    t.draw(im,(16,300),left,12,'medium',ink='white',paper='ink')
    t.draw(im,(224,300),'OK 进入' if title=='冒险地图' else 'OK 返回',12,'bold',ink='white',paper='ink',align='right')


def cover(t):
    im=blank();d=ImageDraw.Draw(im)
    t.draw(im,(16,12),'NABO',38,'latin')
    t.draw(im,(18,48),'ADVENTURE',12,'latin',tracking=2)
    t.draw(im,(14,72),'NABO 的冒险之旅',26)
    t.draw(im,(17,110),'每一站，都有新的故事',12,'medium')
    # A travel pennant replaces the meaningless numbered cover badge.
    d.rectangle((207,17,208,51),fill=color('ink'))
    d.polygon([(209,18),(226,21),(221,28),(226,35),(209,32)],fill=color('accent'))
    # Four small, free-standing map vignettes retain the approved journey theme.
    d.polygon([(16,226),(43,222),(82,234),(89,262),(16,262)],fill=color('blue'))
    d.line([(17,236),(30,232),(44,236),(58,231)],fill=color('white'),width=2)
    d.line([(20,251),(34,246),(49,249)],fill=color('paper'),width=2)
    paste(im,'map/tiles/mountain/snowcap-rock.png',(20,163))
    paste(im,'map/tiles/town/red-roof.png',(180,218))
    d.ellipse((185,151,209,175),fill=color('ink'));d.arc((180,158,215,168),0,330,fill=color('gold'),width=2)
    d.rectangle((216,145,218,147),fill=color('gold'));d.rectangle((175,180,177,182),fill=color('accent'))
    before=im.copy();source=character(im,'welcome',(120,266))
    t.draw(im,(120,270),'NABO,陪你冒险',12,'medium',align='center')
    d=ImageDraw.Draw(im);d.rectangle((16,284,223,317),fill=color('ink'))
    t.draw(im,(120,292),'按 OK 出发',16,ink='white',paper='ink',align='center',slot=[16,284,224,318])
    return im,before,source


def map_page(t):
    im=blank();d=ImageDraw.Draw(im);bars(im,t,'冒险地图','上 / 下移动','01 / 24')
    t.draw(im,(16,48),'下一站',12,'medium',ink='coolgray')
    t.draw(im,(16,69),'深潜',24)
    t.draw(im,(78,78),'已解锁',12,'medium',ink='teal')
    d.line((16,105,223,105),fill=color('rule'))
    # Clear path hierarchy and one solid current-station card.
    for y in (127,143,159):paste(im,'ui/map/footprints-forward.png',(47,y))
    paste(im,'map/landmarks/dive.png',(34,114),(36,36))
    d.ellipse((31,209,76,224),fill=color('paper'));d.ellipse((34,211,73,221),outline=color('accent'),width=2)
    paste(im,'map/landmarks/jump.png',(29,177),(48,48))
    before=im.copy();source=character(im,'idle',(54,211))
    rect=[96,132,224,228];d=ImageDraw.Draw(im);d.rectangle((96,132,223,227),fill=color('ink'))
    d.rectangle((96,132,99,227),fill=color('accent'))
    t.draw(im,(108,144),'跳一跳',18,ink='white',paper='ink',slot=rect)
    t.draw(im,(108,173),'12',30,'latin',ink='white',paper='ink',slot=rect)
    t.draw(im,(164,186),'最佳',12,'medium',ink='white',paper='ink',slot=rect)
    for i,c in enumerate(('bronze','silver','gold')):
        d.ellipse((109+i*19,210,117+i*19,218),fill=color(c) if i==0 else color('ink'),outline=color(c),width=1)
    t.draw(im,(16,250),'距银章还差 13',16)
    t.draw(im,(16,273),'护照亭 · 继续收集旅途印记',12,'medium',ink='coolgray')
    return im,before,source


def passport(t):
    im=blank();d=ImageDraw.Draw(im);bars(im,t,'冒险护照','上 / 下翻阅','PASSPORT')
    t.draw(im,(16,48),'我的旅途印记',22)
    t.draw(im,(224,77),'01 / 24',12,'latin',align='right',ink='coolgray')
    names=['跳一跳','深潜','小火车','萤火虫','登山','滑雪','热气球','太空']
    for i,name in enumerate(names):
        x=16+(i%2)*110;y=88+(i//2)*50;rect=[x,y,x+98,y+48]
        selected=i==0;paper='ink' if selected else 'surface';d.rectangle((x,y,x+97,y+47),fill=color(paper))
        if selected:d.rectangle((x,y,x+3,y+47),fill=color('accent'))
        t.draw(im,(x+8,y+8),name,16,ink='white' if selected else 'ink',paper=paper,slot=rect)
        if i<=1:
            for n,c in enumerate(('bronze','silver','gold')):
                d.ellipse((x+8+n*16,y+28,x+14+n*16,y+34),fill=color(c) if selected and n==0 else color(paper),outline=color(c),width=1)
            t.draw(im,(x+90,y+26),'12' if selected else '0',12,'latin',ink='white' if selected else 'ink',paper=paper,align='right',slot=rect)
        else:t.draw(im,(x+8,y+26),'未解锁',12,'medium',ink='coolgray',paper=paper,slot=rect)
    return im,None,None
