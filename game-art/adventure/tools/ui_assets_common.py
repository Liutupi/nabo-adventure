"""Shared native-pixel UI asset helpers; this module never draws a character."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'game-art/adventure/art'
OUT = ART / 'ui'
PALETTE_PATH = OUT / 'design/round3/01-passport/palette.json'
COLORS = json.loads(PALETTE_PATH.read_text('utf-8'))
FONT_SHA = 'a94e558a2fe972bee4f46bce0843abff37063fd68c33f1e7d9058f6f09432b01'
FONT_PATHS = [ROOT.parent / f'{project}/tools/fonts/SourceHanSansCN-Medium.otf'
              for project in ('nabo-fortune', 'nabo-sound-lab')]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgba(name): return tuple(bytes.fromhex(COLORS.get(name, name)[1:])) + (255,)
def pixels(image):
    return image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata()


def image(size, color=None):
    return Image.new('RGBA', size, rgba(color) if color else (0, 0, 0, 0))


class Fonts:
    def __init__(self, path=None):
        self.path = Path(path) if path else next((p for p in FONT_PATHS if p.exists()), None)
        if not self.path or sha(self.path) != FONT_SHA:
            raise ValueError('The verified SourceHanSansCN-Medium.otf is required; no font substitution.')
        self.cache = {}

    def get(self, size):
        if size not in self.cache: self.cache[size] = ImageFont.truetype(str(self.path), size)
        return self.cache[size]

    def text(self, target, xy, text, size=12, color='ink', align='left'):
        font = self.get(size)
        box = font.getbbox(text)
        width, height = box[2]-box[0], box[3]-box[1]
        x, y = xy
        if align == 'center': x -= width//2
        elif align == 'right': x -= width
        assert x >= 0 and y >= 0 and x+width <= target.width and y+height <= target.height, (text, xy, box, target.size)
        mask = Image.new('L', (max(1, width), max(1, height)))
        ImageDraw.Draw(mask).text((-box[0], -box[1]), text, font=font, fill=255)
        mask = mask.point(lambda a: 255 if a >= 112 else 0)
        target.paste(rgba(color), (x, y), mask)
        return (x, y, x+width, y+height)


class Assets:
    def __init__(self):
        self.entries = []

    def save(self, relative, bitmap, *, group='shared', limit=32, pack=True, **metadata):
        path = OUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        bitmap = bitmap.convert('RGBA')
        visible = {p[:3] for p in pixels(bitmap) if p[3]}
        alpha = {p[3] for p in pixels(bitmap)}
        assert alpha <= {0, 255}, (relative, 'partial alpha')
        assert len(visible) + int(0 in alpha) <= limit, (relative, len(visible), limit)
        if group == 'shared':
            assert visible <= {rgba(c)[:3] for c in COLORS}, (relative, 'outside shared palette')
        bitmap.save(path, optimize=True)
        self.entries.append({'name': Path(relative).with_suffix('').as_posix().replace('/', '_').replace('-', '_'),
                             'path': relative, 'size': list(bitmap.size), 'width': bitmap.width, 'height': bitmap.height,
                             'palette': ['#%02x%02x%02x' % color for color in sorted(visible)],
                             'palette_has_transparent': 0 in alpha,
                             'palette_group': group, 'colors_with_transparency': len(visible)+int(0 in alpha),
                             'color_limit': limit, 'pack': pack, 'sha256': sha(path), **metadata})
        return bitmap

    def load(self, path): return Image.open(OUT / path).convert('RGBA')


def stamp_card(size, selected=False, disabled=False):
    result = image(size)
    w, h = size
    d = ImageDraw.Draw(result)
    fill = 'seal' if disabled else 'select' if selected else 'paper'
    border = 'muted' if disabled else 'ink' if selected else 'line'
    d.rectangle((0, 0, w-1, h-1), fill=rgba(fill), outline=rgba(border), width=2)
    # Four tiny corner cuts give paper its silhouette without stretching details.
    for box in ((0, 0, 1, 1), (w-2, 0, w-1, 1), (0, h-2, 1, h-1), (w-2, h-2, w-1, h-1)):
        d.rectangle(box, fill=(0, 0, 0, 0))
    if selected:
        d.rectangle((4, 4, w-5, h-5), outline=rgba('accent'), width=1)
    return result


SLICE_NAMES = ('top-left', 'top', 'top-right', 'left', 'center', 'right', 'bottom-left', 'bottom', 'bottom-right')


def split_nine(atlas, corner):
    w, h = atlas.size
    xs, ys = (0, corner, w-corner, w), (0, corner, h-corner, h)
    return {name: atlas.crop((xs[i % 3], ys[i//3], xs[i % 3+1], ys[i//3+1]))
            for i, name in enumerate(SLICE_NAMES)}


def tiled_paste(target, tile, box):
    x0, y0, x1, y1 = box
    for y in range(y0, y1, tile.height):
        for x in range(x0, x1, tile.width):
            piece = tile.crop((0, 0, min(tile.width, x1-x), min(tile.height, y1-y)))
            target.alpha_composite(piece, (x, y))


def render_nine(pieces, size, corner):
    w, h = size
    assert w >= 2*corner and h >= 2*corner
    out = image(size)
    tiled_paste(out, pieces['center'], (corner, corner, w-corner, h-corner))
    tiled_paste(out, pieces['top'], (corner, 0, w-corner, corner))
    tiled_paste(out, pieces['bottom'], (corner, h-corner, w-corner, h))
    tiled_paste(out, pieces['left'], (0, corner, corner, h-corner))
    tiled_paste(out, pieces['right'], (w-corner, corner, w, h-corner))
    for name, xy in (('top-left', (0, 0)), ('top-right', (w-corner, 0)),
                     ('bottom-left', (0, h-corner)), ('bottom-right', (w-corner, h-corner))):
        out.paste(pieces[name], xy)
    return out


def check_nine(pieces, rendered, corner):
    w, h = rendered.size
    for name, box in (('top-left', (0, 0, corner, corner)), ('top-right', (w-corner, 0, w, corner)),
                      ('bottom-left', (0, h-corner, corner, h)), ('bottom-right', (w-corner, h-corner, w, h))):
        difference = ImageChops.difference(pieces[name], rendered.crop(box))
        assert not any(high for _, high in difference.getextrema())
    interior = rendered.getchannel('A').crop((2, 2, w-2, h-2))
    assert interior.getextrema() == (255, 255), 'Nine-slice interior seam/gap'


def lock_icon():
    result = image((16, 16)); d = ImageDraw.Draw(result)
    d.arc((4, 0, 11, 10), 180, 360, fill=rgba('muted'), width=2)
    d.rectangle((2, 6, 13, 15), fill=rgba('seal'), outline=rgba('ink'), width=2)
    d.rectangle((7, 10, 8, 13), fill=rgba('ink'))
    return result


def medal(tier=0, earned=True, size=16):
    out = image((size, size)); d = ImageDraw.Draw(out)
    color = ('bronze', 'silver', 'gold')[tier] if earned else 'paper'
    d.ellipse((1, 1, size-2, size-2), fill=rgba(color), outline=rgba('ink' if earned else 'line'), width=2)
    if earned:
        c = size//2
        d.polygon(((c, 3), (c+2, c-2), (size-4, c), (c+2, c+2), (c, size-4), (c-2, c+2), (3, c), (c-2, c-2)), fill=rgba('paper'))
    return out


def rle_estimate(bitmap):
    """Unpacked-file estimate: 2-byte count/index runs plus row offsets/palette/header."""
    bitmap = bitmap.convert('RGBA')
    data = list(pixels(bitmap)); run_count = 0
    for y in range(bitmap.height):
        row = data[y*bitmap.width:(y+1)*bitmap.width]
        last, run = None, 0
        for p in row:
            value = p if p[3] else (0, 0, 0, 0)
            if value != last or run == 255:
                run_count += 1; run = 1; last = value
            else: run += 1
    colors = len(set(data))
    return run_count*2 + (bitmap.height+1)*4 + colors*2 + 24
