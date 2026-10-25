"""Native-pixel drawing with an editable, named-layer SVG companion."""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


class Canvas:
    def __init__(self, size, colors):
        self.size, self.colors = size, colors
        self.image = Image.new('RGBA', (size, size))
        self.draw = ImageDraw.Draw(self.image)
        self.root = ET.Element('{' + NS + '}svg', width=str(size), height=str(size),
                               viewBox=f'0 0 {size} {size}', **{'shape-rendering':'crispEdges'})
        self.layer('art')

    def color(self, value):
        return self.colors.get(value, value) if value else None

    def layer(self, name):
        self.group = ET.SubElement(self.root, '{'+NS+'}g', id=name)

    def svg(self, tag, **values):
        ET.SubElement(self.group, '{'+NS+'}'+tag,
                      {k.replace('_','-'):str(v) for k,v in values.items()})

    def rect(self, box, fill=None, outline='ink', width=2, radius=0):
        color, ink = self.color(fill), self.color(outline)
        kwargs = dict(fill=color, outline=ink, width=width)
        if radius: self.draw.rounded_rectangle(box, radius, **kwargs)
        else: self.draw.rectangle(box, **kwargs)
        x,y,r,b = box; inset = width/2 if ink else 0
        self.svg('rect', x=x+inset, y=y+inset, width=r-x+1-inset*2, height=b-y+1-inset*2,
                 rx=radius, fill=color or 'none', stroke=ink or 'none', stroke_width=width)

    def ellipse(self, box, fill=None, outline='ink', width=2):
        color, ink = self.color(fill), self.color(outline)
        self.draw.ellipse(box, color, ink, width)
        x,y,r,b=box; inset=width/2 if ink else 0
        self.svg('ellipse', cx=(x+r+1)/2, cy=(y+b+1)/2, rx=(r-x+1)/2-inset,
                 ry=(b-y+1)/2-inset, fill=color or 'none', stroke=ink or 'none', stroke_width=width)

    def line(self, points, color='ink', width=2):
        color=self.color(color)
        self.draw.line(points, color, width, joint='curve')
        self.svg('polyline', points=' '.join(f'{x},{y}' for x,y in points), fill='none',
                 stroke=color, stroke_width=width, stroke_linejoin='round')

    def poly(self, points, fill=None, outline='ink', width=2):
        color, ink=self.color(fill),self.color(outline)
        if color:self.draw.polygon(points, color)
        if ink: self.draw.line(points+[points[0]], ink, width, joint='curve')
        self.svg('polygon', points=' '.join(f'{x},{y}' for x,y in points), fill=color or 'none',
                 stroke=ink or 'none', stroke_width=width, stroke_linejoin='round')

    def arc(self, box, start, end, color='ink', width=2):
        x,y,r,b=box
        points=[(round((x+r)/2+(r-x)/2*math.cos(math.radians(a))),
                 round((y+b)/2+(b-y)/2*math.sin(math.radians(a))))
                for a in range(start,end+1,3)]
        self.line(points,color,width)

    def star(self, x,y,r=4,fill='gold',outline='ink',width=1):
        q=max(1,r//3)
        self.poly([(x,y-r),(x+q,y-q),(x+r,y),(x+q,y+q),(x,y+r),
                   (x-q,y+q),(x-r,y),(x-q,y-q)],fill,outline,width)

    def save(self, path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        self.image.save(path)
        ET.ElementTree(self.root).write(path.with_suffix('.svg'),encoding='utf-8',xml_declaration=True)


def locomotive(c,x,y,scale=1, color='teal', line_only=False):
    """A compact engine glyph shared by the station sign and POST seal."""
    def box(a,b,d,e):return (x+a*scale,y+b*scale,x+d*scale,y+e*scale)
    fill=None if line_only else color
    c.rect(box(2,6,25,17),fill,radius=2)
    c.rect(box(16,0,28,17),fill)
    c.rect(box(19,3,25,8),None if line_only else 'paper',width=1)
    c.rect(box(4,1,8,6),None if line_only else 'accent',width=1)
    c.poly([(x+25*scale,y+17*scale),(x+32*scale,y+17*scale),(x+35*scale,y+21*scale),
            (x+25*scale,y+21*scale)],None if line_only else 'line')
    for a in (7,23):c.ellipse(box(a-4,15,a+4,23),None if line_only else 'ink')


def pine(c,x,y,height=25,snow=False):
    w=height//3
    c.rect((x-2,y+height-7,x+2,y+height),'bronze',width=1)
    c.poly([(x,y),(x-w,y+height//2),(x-w//2,y+height//2),(x-w-2,y+height-6),
            (x+w+2,y+height-6),(x+w//2,y+height//2),(x+w,y+height//2)],'teal',width=1)
    if snow:
        c.poly([(x,y+1),(x-w+2,y+height//2-1),(x,y+height//2-4),
                (x+w-2,y+height//2-1)],'white',None)


def mountain(c,x,y,w,h,flag=False):
    c.poly([(x,y+h),(x+w//2,y),(x+w,y+h)],'blue')
    c.poly([(x+w//2,y),(x+w//2+2,y+h),(x+w,y+h)],'ink',None)
    c.poly([(x+w//2,y),(x+w//2-10,y+18),(x+w//2-2,y+15),
            (x+w//2+3,y+20),(x+w//2+11,y+18)],'white',None)
    if flag:
        c.line([(x+w//2,y+3),(x+w//2,y-17)],'ink',2)
        c.poly([(x+w//2+1,y-17),(x+w//2+17,y-14),(x+w//2+13,y-7),
                (x+w//2+1,y-8)],'accent',width=1)
