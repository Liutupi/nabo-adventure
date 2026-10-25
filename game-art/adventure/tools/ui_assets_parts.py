"""Editable passport-paper components, logos, labels and native digit glyphs."""
from PIL import Image, ImageDraw
from ui_assets_common import COLORS, OUT, image, rgba, stamp_card, split_nine, render_nine, check_nine, lock_icon, medal

GAMES = [('jump', 'JUMP', '跳一跳'), ('dive', 'DIVE', '深潜'), ('post', 'POST', '小火车'),
         ('night', 'NIGHT', '萤火虫'), ('climb', 'CLIMB', '登山'), ('ski', 'SKI', '滑雪'),
         ('sky', 'SKY', '热气球'), ('space', 'SPACE', '太空')]


def build_cards(assets):
    families = [('menu', 'normal', 12), ('menu', 'selected', 12), ('menu', 'disabled', 12),
                ('info', 'normal', 12), ('info', 'current', 12), ('popup', 'normal', 16)]
    manifest = []
    for family, state, corner in families:
        atlas = stamp_card((corner*2+8, corner*2+8), state in ('selected', 'current'), state == 'disabled')
        stem = f'cards/{family}/{state}'
        assets.save(stem+'/atlas.png', atlas, pack=False, role='editable-nine-slice-atlas')
        pieces = split_nine(atlas, corner)
        for name, piece in pieces.items(): assets.save(stem+'/'+name+'.png', piece)
        for size in ((48, 32), (240, 120)):
            rendered = render_nine(pieces, size, corner)
            check_nine(pieces, rendered, corner)
            folder = OUT / 'preview/nine-slice'; folder.mkdir(parents=True, exist_ok=True)
            rendered.save(folder / f'{family}-{state}-{size[0]}x{size[1]}.png')
        manifest.append({'family': family, 'state': state, 'corner_px': corner, 'center_tile': [8, 8],
                         'path': stem, 'edges': 'tile without rescaling', 'tested_sizes': [[48, 32], [240, 120]]})
    return manifest


def build_bars(assets):
    for name, height in (('top', 32), ('bottom', 30)):
        out = image((240, height), 'ink'); d = ImageDraw.Draw(out)
        if name=='top':d.rectangle((8,8,11,23),fill=rgba('accent'))
        assets.save(f'bars/{name}.png', out)
    frame = image((128, 10)); d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, 127, 9), fill=rgba('paper'), outline=rgba('ink'), width=2)
    assets.save('resources/bar-frame.png', frame, content_rect=[2, 2, 126, 8])
    for name, color in (('fill', 'teal'), ('low-fill', 'accent')):
        tile = image((8, 6), color)
        assets.save(f'resources/{name}.png', tile, tile_x=True)
        for side in ('left', 'right'):
            cap = image((3, 10), 'paper'); dd = ImageDraw.Draw(cap)
            dd.rectangle((0 if side == 'left' else 1, 0, 1 if side == 'left' else 2, 9), fill=rgba('ink'))
            dd.rectangle((0, 0, 2, 1), fill=rgba('ink')); dd.rectangle((0, 8, 2, 9), fill=rgba('ink'))
            assets.save(f'resources/{name}-{side}-cap.png', cap)


def build_passport(assets, fonts):
    tile = image((32, 32), 'paper')
    assets.save('passport/page-tile.png', tile, limit=8, tile_x=True, tile_y=True)
    for state in ('normal', 'current'):
        frame = stamp_card((104, 52), state == 'current')
        assets.save(f'passport/grid-{state}.png', frame, text_rect=[8,8,96,44],
                    text_color='white' if state=='current' else 'ink',stamps='program draws earned stamps; no duplicate baked placeholders')
    mask = image((104, 52)); d = ImageDraw.Draw(mask)
    mask.alpha_composite(lock_icon(), (80,29))
    assets.save('passport/locked-mask.png', mask,note='Symbol only; render 未解锁 dynamically at (8,30), cream if selected')
    header = image((216,24))
    fonts.text(header,(0,0),'我的旅途印记',22)
    assets.save('passport/header.png', header)


def build_numbers(assets, fonts):
    metrics = {}
    for height in (36, 20):
        point=height
        while max(fonts.get(point+1,'latin').getbbox(c)[3]-fonts.get(point+1,'latin').getbbox(c)[1] for c in '0123456789m+')<=height:point+=1
        glyphs = {}
        for label in '0123456789m+':
            font = fonts.get(point,'latin'); box = font.getbbox(label)
            width, ink_height = box[2]-box[0], box[3]-box[1]
            assert ink_height <= height
            bitmap = image((width+4, height))
            fonts.text(bitmap, (2, (height-ink_height)//2), label, point,family='latin')
            name = 'plus' if label == '+' else label
            assets.save(f'numbers/{height}/{name}.png', bitmap, limit=8, advance=width+3,
                        font_source='verified Montserrat Bold 700', native_raster=True,matte='white paper')
            glyphs[label] = {'path': f'numbers/{height}/{name}.png', 'advance': width+3, 'ink_height': ink_height}
        metrics[str(height)] = glyphs
    return metrics


def build_labels(assets, fonts):
    for name, label, width, color, ink in (
            ('new-record', '新纪录', 72, 'accent', 'white'),
            ('test-no-record', '测试不记录', 96, 'ink', 'white'),
            ('placeholder', '占位关卡', 88, 'surface', 'muted')):
        out = image((width, 24), color)
        fonts.text(out, (width//2, 5), label, 12, ink, 'center',family='bold')
        assets.save(f'labels/{name}.png', out, text=label)
    out = image((220,24));fonts.text(out,(110,0),'NABO,陪你冒险',12,align='center')
    assets.save('labels/boot-caption.png', out, text='NABO,陪你冒险')
    button = image((208,34),'ink')
    fonts.text(button,(104,8),'按 OK 出发',16,'white',align='center')
    assets.save('labels/press-start.png', button, text='按 OK 出发')


def build_map_ui(assets):
    for state in ('unlocked', 'locked', 'current'):
        out = image((48, 40)); d = ImageDraw.Draw(out)
        color = 'surface' if state == 'locked' else 'paper'
        d.ellipse((2,14,45,34),fill=rgba('line'))
        d.ellipse((2,6,45,29),fill=rgba(color),outline=rgba('accent' if state=='current' else 'muted'),width=2)
        if state == 'current':
            d.rectangle((1,12,3,24),fill=rgba('accent'));d.rectangle((44,12,46,24),fill=rgba('accent'))
        assets.save(f'map/station-{state}.png', out, anchor=[24, 24])
    foot = image((10, 10)); d = ImageDraw.Draw(foot)
    d.ellipse((0, 0, 4, 4), fill=rgba('accent')); d.ellipse((4, 5, 8, 9), fill=rgba('accent'))
    assets.save('map/footprints-forward.png', foot)
    assets.save('map/footprints-backward.png', foot.transpose(Image.Transpose.ROTATE_180))
    assets.save('map/lock.png', lock_icon())
    for tier, name in enumerate(('bronze', 'silver', 'gold')):
        assets.save(f'map/stamp-{name}.png', medal(tier))
    assets.save('map/stamp-empty.png', medal(earned=False))
    marker = image((32, 20), 'paper'); d = ImageDraw.Draw(marker)
    d.rectangle((0, 0, 31, 19), outline=rgba('accent'), width=2)
    d.polygon(((12, 15), (20, 15), (16, 19)), fill=rgba('accent'))
    assets.save('map/temporary-position-marker.png', marker, temporary=True,
                note='Unused when the real NABO sprite is available; no character drawing')
    ink = image((64, 64)); d = ImageDraw.Draw(ink)
    d.ellipse((2, 2, 61, 61), fill=rgba('accent'), outline=rgba('bronze'), width=3)
    assets.save('stamps/ink-pad.png', ink)


def build_wordmarks(assets, fonts):
    collection=image((220,90));d=ImageDraw.Draw(collection)
    fonts.text(collection,(6,0),'NABO',38,family='latin')
    fonts.text(collection,(8,36),'ADVENTURE',12,family='latin',tracking=2)
    fonts.text(collection,(4,60),'NABO 的冒险之旅',26)
    d.rectangle((197,5,198,39),fill=rgba('ink'))
    d.polygon([(199,6),(216,9),(211,16),(216,23),(199,20)],fill=rgba('accent'))
    assets.save('wordmarks/collection.png', collection, group='wordmarks', limit=16,
                text=['NABO ADVENTURE', 'NABO 的冒险之旅'])
    for _, english, chinese in GAMES:
        out=image((200,80),'paper')
        fonts.text(out,(100,8),chinese,26,align='center')
        fonts.text(out,(100,51),english,14,'accent','center',family='latin',tracking=2)
        assets.save(f'wordmarks/{english.lower()}.png', out, group='wordmarks', limit=16, text=[english, chinese])
