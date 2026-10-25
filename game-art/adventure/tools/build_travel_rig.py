"""Wrap approved raster slices in independent SVG layers; no character paths are drawn."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
from rig_config import CANVAS, ANCHOR, BODY_HEIGHT, VIEWS, PARTS, OVERLAPS, DRAW_ORDER, ANIMS, ANIMATION_SPECS

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art'
RIG = ART / 'rig'
SOURCE = RIG / 'source/travel-three-views.png'
EXPECTED_SOURCE = 'c4526e8e1562c5f43053556fc6e8605d74db261dca1f095ec429a2492d702c9b'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def polygon(points):
    mask = Image.new('L', CANVAS)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def svg_wrapper(image, name, metadata):
    buf = io.BytesIO()
    image.save(buf, 'PNG')
    data = base64.b64encode(buf.getvalue()).decode('ascii')
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="256" height="256" viewBox="0 0 256 256">\n'
            f'<title>{name}: approved raster slice, not hand-drawn vector artwork</title>\n'
            '<metadata>' + json.dumps(metadata) + '</metadata>\n'
            f'<image width="256" height="256" xlink:href="data:image/png;base64,{data}"/>\n</svg>\n')


def normalize(source, view):
    window = VIEWS[view]['window']
    tile = source.crop(window)
    # Root approved a documented alpha-only discard of generator fringe noise.
    # RGB channels and the source file remain untouched, including every face pixel.
    tile.putalpha(tile.getchannel('A').point(lambda a: a if a >= 16 else 0))
    core = tile.getchannel('A').point(lambda a: 255 if a > 128 else 0).getbbox()
    if not core:
        raise ValueError(f'{view}: no opaque character')
    # Keep two source pixels of antialiasing. Crop is not color-key extraction.
    x0, y0, x1, y1 = core
    box = [max(0, x0 - 2), max(0, y0 - 2), min(tile.width, x1 + 2), min(tile.height, y1 + 2)]
    cut = tile.crop(box)
    scale = BODY_HEIGHT / (y1 - y0)
    size = (round(cut.width * scale), round(cut.height * scale))
    sampled = cut.resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', CANVAS)
    left = ANCHOR[0] - round((x1 + x0 - 2 * box[0]) * scale / 2)
    top = ANCHOR[1] - round((y1 - box[1]) * scale)
    canvas.alpha_composite(sampled, (left, top))
    contract = {'source_window': window, 'source_core_bbox_in_window': list(core),
                'source_sampling_bbox_in_window': box, 'scale': scale,
                'sampled_size': list(size), 'paste_xy': [left, top],
                'core_height': BODY_HEIGHT, 'anchor': list(ANCHOR)}
    return canvas, contract


def build():
    if not SOURCE.exists():
        raise FileNotFoundError('Transparent source must arrive before building the rig')
    source = Image.open(SOURCE).convert('RGBA')
    if digest(SOURCE) != EXPECTED_SOURCE:
        raise ValueError('Source changed: review identity/alpha and update the explicit SHA lock first')
    alpha = source.getchannel('A')
    hist = alpha.histogram()
    if hist[0] < source.width * source.height // 4 or sum(hist[129:]) < 100000:
        raise ValueError('Source alpha lacks transparent surroundings or a substantial opaque subject')
    result = {'version': 1, 'skin': 'travel', 'selected_design': 'round1/v2 option 1 light hiking',
              'canvas': list(CANVAS), 'anchor': list(ANCHOR), 'fps': 12,
              'source': 'source/travel-three-views.png', 'source_sha256': digest(SOURCE),
              'source_generation_record': 'source/travel-three-views-generation.json',
              'source_alpha_record': 'source/travel-three-views-qa.json',
              'source_edit_boundary': 'Background extraction slightly re-rendered the approved board. This rig does not redraw any source head/face pixels.',
              'representation': 'independent SVG wrappers of approved source pixel slices; not hand-drawn paths',
              'source_alpha': {'zero_pixels': hist[0], 'low_alpha_1_to_7_pixels': sum(hist[1:8]),
                               'core_over_128_pixels': sum(hist[129:]), 'opaque_255_pixels': hist[255]},
              'mirror_allowed': False, 'part_side_convention': 'screen-left/right within each separately supplied view',
              'alpha_policy': {'discard_below': 16, 'operation': 'alpha-only; original RGB and source file unchanged',
                               'reason': 'non-character low-alpha generator specks; explicitly authorized by root',
                               'core_sampling_bbox_threshold': 128},
              'draw_order': DRAW_ORDER, 'views': {}}
    from rig_render import pose_data
    result['animations'] = {}
    for anim, facing in ANIMS:
        keyframes = []
        spec=ANIMATION_SPECS[anim]
        for i in range(spec['count']):
            keyframes.append(pose_data(anim,i,spec['count']))
        result['animations'][anim] = {'facing': facing, 'fps': 12, 'loop': spec['loop'],
            'easing': 'periodic sine/cosine sampled uniformly; no endpoint duplication',
            'keyframes': keyframes}
    for view in VIEWS:
        original, sampling = normalize(source, view)
        common = RIG / 'common' / view
        skin = RIG / 'skins/travel' / view
        common.mkdir(parents=True, exist_ok=True)
        skin.mkdir(parents=True, exist_ok=True)
        original.save(common / 'sampled-reference.png')
        remaining = Image.new('L', CANVAS, 255)
        masks, parts = {}, {}
        for name, spec in PARTS.items():
            points = spec['poly']
            if name == 'satchel':
                points = [[x + VIEWS[view]['side_bag_dx'], y] for x, y in points]
            region = polygon(points) if points else remaining.copy()
            mask = region if spec.get('overlay') else ImageChops.multiply(region, remaining)
            if not spec.get('overlay'):
                remaining = ImageChops.subtract(remaining, mask)
            for (x, y), radius in OVERLAPS.get(name, []):
                ImageDraw.Draw(mask).ellipse((x-radius, y-radius, x+radius, y+radius), fill=255)
            masks[name] = mask
            layer = original.copy()
            layer.putalpha(ImageChops.multiply(original.getchannel('A'), mask))
            dest = common if spec.get('common') else skin
            png, svg, maskfile = dest / f'{name}.png', dest / f'{name}.svg', dest / f'{name}-mask.png'
            layer.save(png)
            mask.save(maskfile)
            metadata = {'source_sha256': result['source_sha256'], 'facing': view, 'part': name,
                        'pivot': spec['pivot'], 'polygon': points, 'overlap_source_circles': OVERLAPS.get(name, []),
                        'pixel_policy': 'original normalized RGBA copied under explicit binary mask only'}
            svg.write_text(svg_wrapper(layer, name, metadata), 'utf-8')
            parts[name] = {**metadata, 'parent': spec['parent'], 'raster': png.relative_to(RIG).as_posix(),
                           'svg': svg.relative_to(RIG).as_posix(), 'mask': maskfile.relative_to(RIG).as_posix(),
                           'alpha_bbox': layer.getchannel('A').getbbox(), 'rgba_sha256': digest(png),
                           'overlay': bool(spec.get('overlay'))}
        result['views'][view] = {'sampling': sampling, 'reference': (common / 'sampled-reference.png').relative_to(RIG).as_posix(),
                                'parts': parts}
    (RIG / 'rig.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    return result


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps({'rig': str(RIG / 'rig.json'), 'source_sha256': build()['source_sha256']}))
