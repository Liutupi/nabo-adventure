#!/usr/bin/env python3
"""Round-one static costume studies. Read existing NABO vectors; write only here."""
from pathlib import Path
import copy
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
RIG = ROOT / 'game-art/dive/rig/common'
NODE = Path('C:/Users/pc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
INK, PAPER, WHITE = '#1D2938', '#F5F0E6', '#FFFCF5'
TOWN, SEA = '#F6E2B4', '#0B2A4A'
FACES = ('front', 'three-quarter-left', 'three-quarter-right')
STYLES = {
    '01-hiker': dict(name='轻便徒步', en='THE EVERYDAY EXPLORER', main='#3E8B80', mid='#2A6D67',
        dark='#194B4B', pants='#D9C591', pmid='#B19C6B', pdark='#897451', accent='#D76948',
        bag='#E5B76F', bmid='#BD8A4C', bdark='#855B39', secondary='短围巾 / 外套下摆',
        caption='短外套 · 斜挎包 · 轻便步鞋', note='轻装出发，每一站都能走得轻快。'),
    '02-explorer': dict(name='复古探险', en='THE FIELD NOTE COLLECTOR', main='#BD9253', mid='#92703D',
        dark='#684D2D', pants='#647B66', pmid='#455B4E', pdark='#314238', accent='#B9583C',
        bag='#9B6240', bmid='#75452F', bdark='#4E3125', secondary='红棕领巾 / 背包带',
        caption='探险马甲 · 工装裤 · 皮质背包', note='把沿途的发现，装进一本冒险手账。'),
    '03-post-traveler': dict(name='邮差旅人', en='THE PASSPORT COURIER', main='#3E6688', mid='#2B4C6C',
        dark='#1E354E', pants='#B37854', pmid='#8D593D', pdark='#65402E', accent='#D5944D',
        bag='#C88A50', bmid='#A36538', bdark='#774629', secondary='短斗篷后摆 / 围巾尾',
        caption='短斗篷 · 邮差包 · 系带短靴', note='带着一封信出发，带着满页印章回家。'),
}
COLOR_INKS = {'#654533':'#3F322A', '#E7D6AB':'#897451'}
for spec in STYLES.values():
    for base, mid, dark in (('main','mid','dark'), ('pants','pmid','pdark'), ('bag','bmid','bdark')):
        COLOR_INKS[spec[base]] = COLOR_INKS[spec[mid]] = spec[dark]
    COLOR_INKS[spec['accent']] = spec['bdark']


def node(tag, **attrs):
    return ET.Element(f'{{{NS}}}{tag}', {key.replace('_', '-'): str(value) for key, value in attrs.items()})


def group(parent, name, transform=None):
    attrs = dict(id=name, data_part=name)
    if transform: attrs['transform'] = transform
    out = node('g', **attrs); parent.append(out)
    return out


def path(parent, d, fill, stroke=None, width=2.8):
    if stroke is None: stroke = COLOR_INKS.get(fill, INK)
    out = node('path', d=d, fill=fill, stroke=stroke, stroke_width=width,
               stroke_linejoin='round', stroke_linecap='round')
    parent.append(out); return out


def ellipse(parent, x, y, rx, ry, fill, stroke=INK, width=2.8):
    parent.append(node('ellipse', cx=x, cy=y, rx=rx, ry=ry, fill=fill, stroke=stroke, stroke_width=width))


def rect(parent, x, y, w, h, fill, radius=2, stroke=INK, width=2):
    parent.append(node('rect', x=x, y=y, width=w, height=h, rx=radius, fill=fill,
                       stroke=stroke, stroke_width=width))


def copy_parts(parent, source):
    root = ET.parse(source).getroot()
    for child in root:
        if child.tag.rsplit('}', 1)[-1] not in ('title', 'desc'):
            parent.append(copy.deepcopy(child))


def identity_head(parent, facing):
    out = group(parent, 'identity-head-' + facing)
    if facing == 'front':
        for name in ('head', 'eyes_neutral', 'mouth_neutral'):
            copy_parts(out, RIG / 'front' / (name + '.svg'))
        return out
    source = ET.parse(RIG / 'head.svg').getroot()
    head = copy.deepcopy(next(child for child in source if child.tag.endswith('g')))
    cap = next(child for child in head if child.get('id') == 'cap')
    brand = next(child for child in cap if child.tag.endswith('g'))
    cap.remove(brand)
    geometry = group(out, 'original-head-geometry',
                     'translate(256 0) scale(-1 1)' if facing.endswith('right') else None)
    geometry.append(head)
    for name in ('eyes_neutral', 'mouth_neutral'):
        copy_parts(geometry, RIG / (name + '.svg'))
    # Crown and lettering are independent of the mirrored non-brand geometry.
    right = facing.endswith('right'); center = 134 if right else 122
    mark = group(out, 'cap-brand-forward', f'rotate({4 if right else -4} {center} 30)')
    crown = copy.deepcopy(next(child for child in brand if child.tag.endswith('path')))
    if right: crown.set('transform', 'translate(12 0)')
    mark.append(crown)
    word = copy.deepcopy(ET.parse(RIG / 'front/head.svg').getroot().find(f'.//*[@id="nabo-wordmark"]'))
    word.set('transform', f'translate({14.86 if right else 2.86} 0) scale(.92 1)')
    mark.append(word)
    return out


def trousers(parent, style, facing):
    legs = group(parent, 'trousers-and-boots')
    q = 0 if facing == 'front' else (-3 if facing.endswith('left') else 3)
    for side, x in enumerate((107 + q, 131 + q)):
        path(legs, f'M{x} 158Q{x+10} 155 {x+20} 161L{x+18} 201L{x+1} 203Z', style['pants'])
        path(legs, f'M{x+2} 171L{x+7} 171L{x+6} 196L{x+17} 199L{x+17} 203L{x+1} 203Z', style['pmid'], 'none', 0)
        path(legs, f'M{x+3} 190L{x+7} 195L{x+17} 197L{x+17} 202L{x+2} 202Z', style['pdark'], 'none', 0)
        if 'explorer' in style['id']:
            rect(legs, x+1, 175, 15, 13, style['pmid'], 1, style['pdark'], 1.6)
            path(legs, f'M{x+1} 178L{x+16} 178', 'none', style['pdark'], 1.5)
        path(legs, f'M{x+1} 199L{x+18} 199L{x+18} 213Q{x+22} 215 {x+22} 220L{x-3} 222L{x-5} 218L{x-3} 208Z', '#654533')
        path(legs, f'M{x-4} 217L{x+22} 216L{x+22} 220L{x-3} 222Z', '#3F322A', 'none', 0)
        path(legs, f'M{x+1} 203L{x+13} 203M{x} 208L{x+12} 208', 'none', '#BFA47B', 1.7)


def arms(parent, style, facing):
    arms = group(parent, 'arms-and-hands')
    quarter = facing != 'front'; left = facing.endswith('left')
    for side, x in enumerate((97, 151)):
        dx = (-1 if left else 1) * (2 if side == 0 else 3) if quarter else 0
        x += dx
        cloth = '#E7D6AB' if 'explorer' in style['id'] else style['main']
        shade = '#BAA47C' if 'explorer' in style['id'] else style['mid']
        path(arms, f'M{x+10} 115Q{x-1} 116 {x-4} 131L{x-1} 163L{x+13} 162L{x+16} 129Z', cloth)
        path(arms, f'M{x-3} 131L{x+2} 130L{x+5} 158L{x+12} 160L{x-1} 163Z', shade, 'none', 0)
        path(arms, f'M{x} 159L{x+13} 158L{x+13} 166L{x+1} 167Z', shade)
        ellipse(arms, x+7, 171, 7.5, 9, '#F5C394')
        path(arms, f'M{x+10} 168Q{x+16} 175 {x+9} 179', 'none', '#DFA072', 2)


def outfit(parent, style, facing):
    quarter = facing != 'front'; direction = -1 if facing.endswith('left') else 1
    # Clothes have positive-scale, independently drawn quarter projections.
    body = group(parent, 'costume-' + style['id'],
                 f'translate({128*(1-.88)+direction*2:.2f} 0) scale(.88 1)' if quarter else None)
    if 'explorer' in style['id']:
        pack = group(body, 'leather-backpack')
        x = 143 if direction < 0 and quarter else 87
        rect(pack, x, 117, 31, 48, style['bag'], 10)
        rect(pack, x+3, 120, 25, 19, style['bmid'], 7)
        path(pack, f'M{x+10} 125L{x+10} 152L{x+16} 156L{x+16} 126', 'none', style['bdark'], 3)
        rect(pack, x+9, 143, 15, 15, style['bmid'], 3)
    if 'post' in style['id']:
        cape = group(body, 'secondary-cape-back')
        path(cape, 'M111 114Q128 106 145 114L167 171L147 168L140 179L123 170L106 175L91 164Z', style['mid'])
        path(cape, 'M145 119L163 166L145 163L139 176L134 163Z', style['dark'], 'none', 0)
    trousers(body, style, facing)
    arms(body, style, facing)
    copy_parts(group(body, 'neck'), RIG / 'front/neck.svg')
    torso = group(body, 'torso')
    path(torso, 'M110 111Q128 119 146 111L152 128L149 169Q128 176 107 169L104 128Z',
         '#E7D6AB' if 'explorer' in style['id'] else style['main'])
    path(torso, 'M143 119L151 129L148 169L137 172L140 151Z', style['mid'], 'none', 0)
    path(torso, 'M146 143L149 146L148 169L137 172L141 163Z', style['dark'], 'none', 0)
    if 'explorer' in style['id']:
        path(torso, 'M110 113L124 124L120 171L106 168L104 128Z', style['main'])
        path(torso, 'M146 113L132 124L136 171L150 168L152 128Z', style['main'])
        for x in (109, 136): rect(torso, x, 143, 12, 14, style['mid'], 2, style['dark'], 1.7)
        path(torso, 'M112 120L116 141M143 120L140 140', 'none', style['bdark'], 3.7)
    elif 'post' in style['id']:
        path(torso, 'M112 112Q128 117 144 112L157 145L142 143L129 153L114 143L100 146Z', style['main'])
        path(torso, 'M142 116L155 142L142 140L130 149L131 134Z', style['mid'], 'none', 0)
        path(torso, 'M110 115L128 129L146 115', 'none', style['accent'], 4)
        ellipse(torso, 128, 132, 4, 4, style['accent'], style['dark'], 1.5)
    else:
        path(torso, 'M110 112L122 124L117 135L106 122Z', style['mid'])
        path(torso, 'M146 112L134 124L139 135L150 122Z', style['mid'])
        path(torso, 'M128 124L128 171', 'none', style['dark'], 2)
        for x in (109, 136): rect(torso, x, 145, 12, 10, style['mid'], 2, style['dark'], 1.6)
    scarf = group(body, 'secondary-scarf')
    path(scarf, 'M118 111L137 111L143 119L129 124L115 119Z', style['accent'])
    if 'post' in style['id']:
        path(scarf, 'M138 115Q151 113 160 120L150 124L158 131L141 125Z', style['accent'])
    elif 'explorer' in style['id']:
        path(scarf, 'M126 120L138 121L133 139L126 132Z', style['accent'])
    else:
        path(scarf, 'M115 117L124 121L116 136L108 132Z', style['accent'])
    if 'explorer' not in style['id']:
        bag = group(body, 'satchel-and-strap')
        x = 139 if not quarter or direction > 0 else 91
        strap = 'M146 114L105 155' if x == 91 else 'M110 114L147 155'
        path(bag, strap, 'none', style['bdark'], 7)
        path(bag, strap, 'none', style['bag'], 3)
        rect(bag, x, 151, 29, 27, style['bag'], 5)
        path(bag, f'M{x} 153L{x+29} 153L{x+26} 164L{x+15} 168L{x+3} 164Z', style['bmid'])
        rect(bag, x+12, 158, 6, 11, style['accent'], 1, style['bdark'], 1.5)
    return body


def make_svg(style, facing):
    svg = node('svg', width=256, height=256, viewBox='0 0 256 256')
    title = node('title'); title.text = f'NABO travel study {style["id"]} / {facing}'; svg.append(title)
    desc = node('desc'); desc.text = 'Static round-one candidate; feet anchor 128,224; NABO identity copied from existing dive vectors; no whole-character mirroring.'; svg.append(desc)
    outfit(svg, style, facing)
    identity_head(svg, facing)
    return svg


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('msyhbd.ttc' if bold else 'msyh.ttc'), size)


def text(draw, xy, message, size, color=INK, bold=False, anchor=None):
    draw.text(xy, message, font=font(size, bold), fill=color, anchor=anchor)


def rgb565(image):
    return image.point([int(round((i >> (3 if c != 1 else 2)) * 255 / (31 if c != 1 else 63)))
                        for c in range(3) for i in range(256)])


def target48(image):
    bbox = image.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    scale = 48 / (224 - bbox[1])
    crop = image.crop((bbox[0], bbox[1], bbox[2], 224))
    crop = crop.resize((round(crop.width*scale), 48), Image.Resampling.LANCZOS)
    target = Image.new('RGBA', (64, 64))
    target.alpha_composite(crop, (32 + round((bbox[0]-128)*scale), 8))
    return target.quantize(colors=64, method=Image.Quantize.FASTOCTREE).convert('RGBA')


def render_boards(images, qa):
    overview = Image.new('RGB', (1600, 950), PAPER); od = ImageDraw.Draw(overview)
    text(od, (64, 45), 'NABO 的冒险之旅', 48, bold=True)
    text(od, (66, 118), '第 1 轮 · 基础旅行服造型 / 三个候选，等你选定', 25, '#58616A')
    for column, (key, style) in enumerate(STYLES.items()):
        x = 56 + column*510
        od.rounded_rectangle((x, 188, x+488, 890), 25, WHITE)
        text(od, (x+30, 214), f'0{column+1}  {style["name"]}', 32, bold=True)
        image = images[key, 'front'].resize((430, 430), Image.Resampling.LANCZOS)
        overview.paste(image, (x+29, 266), image)
        text(od, (x+244, 724), style['caption'], 19, anchor='mm')
        for j, color in enumerate((TOWN, SEA)):
            tile = Image.new('RGB', (208, 104), color); d = ImageDraw.Draw(tile)
            tiny = target48(images[key, 'front']); tile.paste(tiny, (72, 16), tiny)
            text(d, (104, 89), '48 px · 1×', 12, INK if j == 0 else '#E4E8E5', anchor='mm')
            overview.paste(tile, (x+28+j*224, 766))
    overview.save(BASE / 'round1-overview.png')
    for index, (key, style) in enumerate(STYLES.items()):
        board = Image.new('RGB', (1600, 1640), PAPER); d = ImageDraw.Draw(board)
        text(d, (64, 34), 'NABO / ADVENTURE WARDROBE', 22, '#69716D', True)
        text(d, (62, 82), f'0{index+1}  {style["name"]}', 58, bold=True)
        text(d, (67, 162), style['caption'] + '  /  ' + style['en'], 22, '#58616A')
        for col, facing in enumerate(FACES):
            x = 64+col*500
            d.rounded_rectangle((x, 220, x+472, 806), 22, WHITE)
            text(d, (x+236, 250), ['正面 / FRONT', '3/4 左 / LEFT', '3/4 右 / RIGHT'][col], 20, '#58616A', anchor='mm')
            image = images[key, facing].resize((450,450), Image.Resampling.LANCZOS)
            board.paste(image, (x+11, 293), image)
            text(d, (x+236, 770), '256 × 256 RGBA · 脚底锚点 (128, 224)', 15, '#69716D', anchor='mm')
        text(d, (65, 846), style['note'], 24, bold=True)
        text(d, (65, 890), '48 PX 目标高度 / 两种世界底色 · 64 色量化后模拟 RGB565', 22, '#58616A')
        for world, bg in enumerate((TOWN, SEA)):
            x = 64+world*750; fg = INK if world == 0 else '#E4EBEA'
            d.rounded_rectangle((x, 940, x+722, 1514), 20, bg)
            text(d, (x+24, 958), ['小镇米黄 / TOWN', '深海蓝 / DEEP SEA'][world], 22, fg, True)
            text(d, (x+24, 1000), '1× 实际像素', 17, fg)
            for col, facing in enumerate(FACES):
                tiny = target48(images[key, facing]); tile = Image.new('RGB', tiny.size, bg); tile.paste(tiny, (0,0), tiny)
                tile = rgb565(tile.quantize(colors=64, method=Image.Quantize.MEDIANCUT).convert('RGB'))
                tile.save(BASE / 'previews' / f'{key}-{facing}-{world}-48px.png')
                board.paste(tile, (x+106+col*220, 1032))
                board.paste(tile.resize((192,192), Image.Resampling.NEAREST), (x+39+col*224, 1170))
                text(d, (x+135+col*224, 1402), ['正面', '3/4 左', '3/4 右'][col], 17, fg, anchor='mm')
            text(d, (x+24, 1458), '下方放大 3×，仅便于检查；上方为真实 1× 像素', 16, fg)
        text(d, (65, 1555), '次级动画部件：'+style['secondary']+'     /     白帽、帽标、脸、眼镜沿用原始矢量', 19, '#58616A')
        text(d, (65, 1591), '静态造型候选 · 待用户选定后进入第 2 轮骨骼与动作', 16, '#69716D')
        board.save(BASE / f'{key}-design-board.png')


def main():
    for folder in ('sources', 'characters', 'targets', 'previews'): (BASE / folder).mkdir(exist_ok=True)
    images, qa, source_paths, heads = {}, {}, [], {}
    for key, style in STYLES.items():
        style['id'] = key
        for facing in FACES:
            path_out = BASE / 'sources' / f'{key}-{facing}.svg'
            ET.ElementTree(make_svg(style, facing)).write(path_out, encoding='utf-8', xml_declaration=True)
            source_paths.append(path_out)
    subprocess.run([str(NODE), str(BASE / 'rasterize.cjs'), *map(str, source_paths)], check=True)
    for file in source_paths:
        key = next(key for key in STYLES if file.stem.startswith(key))
        facing = file.stem[len(key)+1:]
        image = Image.open(file.with_name(file.stem+'-4x.png')).convert('RGBA').resize((256,256), Image.Resampling.LANCZOS)
        # Suppress only sub-pixel filter ringing below the fixed sole baseline.
        image.paste((0,0,0,0), (0,224,256,256))
        image.save(BASE / 'characters' / (file.stem+'.png')); images[key,facing] = image
        tiny = target48(image); tiny.save(BASE / 'targets' / (file.stem+'-48px.png'))
        colors = sorted(set(re.findall(r'#[0-9A-Fa-f]{6}', file.read_text('utf-8'))))
        qa[file.stem] = dict(size=list(image.size), mode=image.mode, bbox=list(image.getbbox()),
            feet_anchor=[128,224], target_height_px=48, source_color_count=len(colors), source_colors=colors,
            target_rgba_color_count=len(tiny.getcolors(maxcolors=65536)),
            whole_character_mirror=False, wordmark_forward=True,
            png_sha256=hashlib.sha256((BASE / 'characters' / (file.stem+'.png')).read_bytes()).hexdigest())
        svg = ET.parse(file).getroot(); head = svg.find(f'.//*[@id="identity-head-{facing}"]')
        signature = hashlib.sha256(ET.tostring(head)).hexdigest()
        assert facing not in heads or heads[facing] == signature
        heads[facing] = signature
        word = svg.find('.//*[@id="nabo-wordmark"]')
        assert word.get('d') == ET.parse(RIG / 'front/head.svg').getroot().find('.//*[@id="nabo-wordmark"]').get('d')
        ancestors = {child:parent for parent in svg.iter() for child in parent}
        cursor = word
        while cursor in ancestors:
            assert 'scale(-1' not in cursor.get('transform','')
            cursor = ancestors[cursor]
        assert len(colors) <= 64 and image.getbbox()[3] <= 224 and qa[file.stem]['target_rgba_color_count'] <= 64, qa[file.stem]
    render_boards(images, qa)
    palette = Image.new('RGB', (1600,540), PAPER); pd = ImageDraw.Draw(palette)
    text(pd,(64,24),'NABO / ROUND 1 · 源矢量调色板',32,bold=True)
    for row,key in enumerate(STYLES):
        colors = qa[key+'-front']['source_colors']
        text(pd,(64,90+row*145),STYLES[key]['name']+f' / {len(colors)} 色',20,bold=True)
        for col,color in enumerate(colors):
            x,y = 64+col*58,126+row*145
            pd.rectangle((x,y,x+46,y+38),fill=color)
            text(pd,(x,y+47),color[1:],9,'#58616A')
    palette.save(BASE/'palette.png')
    source_files = list((RIG / 'front').glob('*.svg')) + [RIG / (n+'.svg') for n in ('head','eyes_neutral','mouth_neutral')]
    provenance = {str(file.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(file.read_bytes()).hexdigest() for file in source_files}
    (BASE / 'provenance.json').write_text(json.dumps(dict(generated_by='build_designs.py + bundled sharp/librsvg + Pillow',
        source_sha256=provenance, head_group_sha256=heads, board_font='Windows Microsoft YaHei; branding is outlined SVG geometry', head_policy='Front exact source geometry; left uses original quarter head; right projects non-brand head geometry only, crown and NABO outlined lettering independently forward.',
        generations_used=False, selection='awaiting user', scope='round-one static studies only'), indent=2)+'\n', 'utf-8')
    (BASE / 'palette-and-qa.json').write_text(json.dumps(dict(characters=qa, target_preview='48px visible character on 64px tile; palette <=64 then RGB565; not production sprite pack',
        target_anchor=[32,56], preview_backgrounds=dict(town=TOWN,deep_sea=SEA)), indent=2)+'\n', 'utf-8')
    print('Rendered nine independent SVG studies, three design boards and 48px world previews.')


if __name__ == '__main__': main()
