"""Native 240x320 pixel UI components. No character drawing lives here."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

THEMES = {
    '01-passport': {
        'name': '复古护照手账', 'mode': 'paper',
        'bg': '#e7d5ad', 'paper': '#fff0cd', 'ink': '#203849',
        'muted': '#756b55', 'line': '#a89269', 'shadow': '#c7b389',
        'bar': '#203849', 'bar_text': '#fff0cd', 'accent': '#b64c43',
        'select': '#f3d88a', 'teal': '#3f817b', 'blue': '#477191',
        'bronze': '#b9703d', 'silver': '#9ca8a7', 'gold': '#d1a43f',
        'white': '#fffaf0', 'seal': '#ddc7a0',
    },
    '02-sticker': {
        'name': '明亮童趣贴纸', 'mode': 'sticker',
        'bg': '#b8e5ed', 'paper': '#fffdf0', 'ink': '#24364b',
        'muted': '#627b8c', 'line': '#76b6c5', 'shadow': '#74bfce',
        'bar': '#2d6b9d', 'bar_text': '#fffdf0', 'accent': '#e5754e',
        'select': '#ffda63', 'teal': '#45a292', 'blue': '#4c95ce',
        'bronze': '#bd783f', 'silver': '#aab6c3', 'gold': '#e7b635',
        'white': '#ffffff', 'seal': '#d9dfe1',
    },
    '03-star-chart': {
        'name': '星图夜航', 'mode': 'stars',
        'bg': '#142238', 'paper': '#22394e', 'ink': '#f4e7c5',
        'muted': '#9bafbb', 'line': '#657b8b', 'shadow': '#0c1729',
        'bar': '#0c1729', 'bar_text': '#f4e7c5', 'accent': '#e5b85d',
        'select': '#3c4e5a', 'teal': '#72afa6', 'blue': '#638fae',
        'bronze': '#bc875b', 'silver': '#aabac8', 'gold': '#e5b85d',
        'white': '#fff7df', 'seal': '#34485b',
    },
}


class Board:
    def __init__(self, theme, font_path):
        self.theme = theme
        self.c = {k: v for k, v in theme.items() if v.startswith('#')}
        self.mode = theme['mode']
        self.image = Image.new('RGB', (240, 320), self.c['bg'])
        self.draw = ImageDraw.Draw(self.image)
        self.fonts = {n: ImageFont.truetype(str(font_path), n) for n in (12, 16, 18)}
        self.text_boxes = []
        self.character_places = []

    def rect(self, box, fill, outline=None, width=2, radius=0):
        kwargs = {'fill': self.c[fill] if fill else None,
                  'outline': self.c[outline] if outline else None, 'width': width}
        if radius:
            self.draw.rounded_rectangle(box, radius, **kwargs)
        else:
            self.draw.rectangle(box, **kwargs)

    def line(self, points, color='line', width=2):
        self.draw.line(points, fill=self.c[color], width=width)

    def ellipse(self, box, fill, outline=None, width=2):
        self.draw.ellipse(box, self.c[fill] if fill else None,
                          self.c[outline] if outline else None, width)

    def poly(self, points, fill, outline=None):
        self.draw.polygon(points, fill=self.c[fill], outline=self.c[outline] if outline else None)

    def text(self, x, y, label, size=12, color='ink', align='left', within=None):
        """Rasterize at the requested native size, using exact palette ink."""
        font = self.fonts[size]
        box = font.getbbox(label)
        width, height = box[2] - box[0], box[3] - box[1]
        if align == 'center': x -= width // 2
        if align == 'right': x -= width
        extent = [int(x), int(y), int(x + width), int(y + height)]
        if within:
            assert extent[0] >= within[0] and extent[1] >= within[1], (label, extent, within)
            assert extent[2] <= within[2] and extent[3] <= within[3], (label, extent, within)
        assert 0 <= x and 0 <= y and x + width <= 240 and y + height <= 320, (label, extent)
        mask = Image.new('L', (max(1, width), max(1, height)))
        ImageDraw.Draw(mask).text((-box[0], -box[1]), label, font=font, fill=255)
        mask = mask.point(lambda alpha: 255 if alpha >= 112 else 0)
        self.image.paste(self.c[color], (int(x), int(y)), mask)
        self.text_boxes.append({'text': label, 'font_px': size, 'box': extent})

    def star(self, x, y, radius=5, color='accent'):
        self.poly([(x, y-radius), (x+2, y-2), (x+radius, y), (x+2, y+2),
                   (x, y+radius), (x-2, y+2), (x-radius, y), (x-2, y-2)], color)

    def background(self):
        if self.mode == 'paper':
            self.line([(7, 36), (7, 286)], 'line')
            self.line([(12, 36), (12, 286)], 'paper')
            for y in range(48, 280, 28):
                self.ellipse((3, y, 9, y+6), 'shadow', 'line', 1)
            self.line([(224, 44), (232, 44), (232, 278), (225, 278)], 'line')
        elif self.mode == 'sticker':
            for x, y in ((20, 49), (214, 62), (24, 271), (216, 268)):
                self.star(x, y, 7, 'white')
                self.star(x, y, 4, 'gold')
            self.line([(0, 102), (13, 102), (20, 95), (32, 95)], 'white', 3)
            self.line([(208, 226), (222, 226), (230, 219), (239, 219)], 'white', 3)
        else:
            points = [(18, 54), (48, 72), (68, 46), (197, 55), (220, 88),
                      (17, 257), (46, 274), (197, 272), (220, 242)]
            self.line(points[:3], 'line')
            self.line(points[3:5], 'line')
            self.line(points[5:7], 'line')
            self.line(points[7:], 'line')
            for x, y in points: self.star(x, y, 3, 'accent')

    def bars(self, title, footer, count='章 1/24'):
        self.rect((0, 0, 239, 31), 'bar')
        self.rect((0, 290, 239, 319), 'bar')
        self.line([(0, 30), (239, 30)], 'accent')
        self.line([(0, 290), (239, 290)], 'accent')
        self.text(12, 8, title, 16, 'bar_text')
        self.text(228, 11, count, 12, 'bar_text', 'right')
        self.text(120, 300, footer, 12, 'bar_text', 'center')

    def card(self, x, y, w, h, selected=False, ticket=False):
        color = 'select' if selected else 'paper'
        self.rect((x+3, y+4, x+w+2, y+h+3), 'shadow', radius=4)
        if self.mode == 'sticker':
            self.rect((x-2, y-2, x+w+1, y+h+1), 'white', radius=9)
            self.rect((x, y, x+w-1, y+h-1), color, 'ink', 3 if selected else 2, 7)
            if selected: self.star(x+w-9, y+8, 5, 'accent')
        elif self.mode == 'stars':
            self.rect((x, y, x+w-1, y+h-1), color, 'accent' if selected else 'line')
            for sx, sy in ((x, y), (x+w-9, y), (x, y+h-9), (x+w-9, y+h-9)):
                self.line([(sx, sy+7), (sx, sy), (sx+7, sy)], 'accent')
        else:
            self.rect((x, y, x+w-1, y+h-1), color, 'ink' if selected else 'line', 2)
            if selected:
                self.rect((x+3, y+3, x+w-4, y+h-4), None, 'accent', 1)
            if ticket:
                for tx in range(x+4, x+w-3, 8):
                    self.rect((tx, y+h-2, tx+3, y+h+1), 'bg')
        return (x+8, y+8, x+w-8, y+h-8)

    def envelope(self, x, y, w=22, h=16, color='paper'):
        self.rect((x, y, x+w-1, y+h-1), color, 'ink')
        self.line([(x+2, y+2), (x+w//2, y+h//2+2), (x+w-3, y+2)], 'ink')

    def lock(self, x, y):
        self.ellipse((x+3, y, x+11, y+10), None, 'muted')
        self.rect((x, y+7, x+14, y+17), 'seal', 'muted')
        self.rect((x+6, y+11, x+8, y+14), 'muted')

    def medal(self, x, y, tier=0, earned=True, r=7):
        color = ('bronze', 'silver', 'gold')[tier] if earned else 'paper'
        self.ellipse((x-r, y-r, x+r, y+r), color, 'ink' if earned else 'line')
        if earned: self.star(x, y, max(3, r-3), 'paper')

    def train(self, x, y, color='teal', scale=1):
        s = scale
        self.rect((x, y+12*s, x+41*s, y+31*s), color, 'ink')
        self.rect((x+25*s, y, x+47*s, y+31*s), color, 'ink')
        self.rect((x+30*s, y+5*s, x+42*s, y+15*s), 'paper', 'ink')
        self.rect((x+6*s, y+5*s, x+13*s, y+14*s), 'accent', 'ink')
        self.rect((x+20*s, y-3*s, x+50*s, y+1*s), 'accent', 'ink')
        for xx in (x+10*s, x+35*s):
            self.ellipse((xx-6*s, y+26*s, xx+6*s, y+38*s), 'ink')
            self.ellipse((xx-2*s, y+30*s, xx+2*s, y+34*s), 'gold')

    def node(self, x, y, state='open', icon='post'):
        fill = 'select' if state == 'current' else 'seal' if state == 'locked' else 'paper'
        self.ellipse((x-23, y-7, x+23, y+16), 'shadow', 'ink')
        self.ellipse((x-23, y-15, x+23, y+8), fill,
                     'accent' if state == 'current' else 'line', 3 if state == 'current' else 2)
        if state == 'current':
            self.line([(x-27, y-8), (x-27, y+10)], 'accent', 3)
            self.line([(x+27, y-8), (x+27, y+10)], 'accent', 3)
        if state == 'locked': self.lock(x-7, y-10)
        elif icon == 'kiosk': self.envelope(x-10, y-9, 21, 15)

    def footsteps(self, points):
        for a, b in zip(points, points[1:]):
            distance = math.hypot(b[0]-a[0], b[1]-a[1])
            for i in range(max(1, int(distance//14))):
                t = (i+.5)/max(1, int(distance//14))
                x, y = round(a[0]+(b[0]-a[0])*t), round(a[1]+(b[1]-a[1])*t)
                self.ellipse((x-3, y-2, x+2, y+2), 'accent')

    def character(self, x, foot_y, height):
        self.character_places.append({'x_center': x, 'foot_y': foot_y, 'height': height})
