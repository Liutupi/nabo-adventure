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
        y = height-2 if name == 'top' else 0
        d.rectangle((0, y, 239, y+1), fill=rgba('accent'))
        for x in (6, 230): d.rectangle((x, height//2-3, x+3, height//2+2), fill=rgba('line'))
        assets.save(f'bars/{name}.png', out)
    frame = image((128, 10)); d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, 127, 9), fill=rgba('paper'), outline=rgba('ink'), width=2)
    assets.save('resources/bar-frame.png', frame, content_rect=[2, 2, 126, 8])
    for name, color in (('fill', 'teal'), ('low-fill', 'accent')):
        tile = image((8, 6), color)
        ImageDraw.Draw(tile).rectangle((0, 0, 7, 1), fill=rgba('select' if name == 'fill' else 'bronze'))
        assets.save(f'resources/{name}.png', tile, tile_x=True)
        for side in ('left', 'right'):
            cap = image((3, 10), 'paper'); dd = ImageDraw.Draw(cap)
            dd.rectangle((0 if side == 'left' else 1, 0, 1 if side == 'left' else 2, 9), fill=rgba('ink'))
            dd.rectangle((0, 0, 2, 1), fill=rgba('ink')); dd.rectangle((0, 8, 2, 9), fill=rgba('ink'))
            assets.save(f'resources/{name}-{side}-cap.png', cap)


def build_passport(assets, fonts):
    tile = image((32, 32), 'paper'); d = ImageDraw.Draw(tile)
    for y in (0, 16): d.rectangle((0, y, 31, y+1), fill=rgba('seal'))
    for x, y in ((8, 8), (24, 24)):
        d.rectangle((x-2, y, x+3, y+1), fill=rgba('seal'))
        d.rectangle((x, y-2, x+1, y+3), fill=rgba('seal'))
    assets.save('passport/page-tile.png', tile, limit=8, tile_x=True, tile_y=True)
    for state in ('normal', 'current'):
        frame = stamp_card((104, 52), state == 'current'); d = ImageDraw.Draw(frame)
        d.rectangle((4, 8, 5, 43), fill=rgba('teal'))
        for x in (20, 40, 60): frame.alpha_composite(medal(earned=False, size=12), (x-6, 34))
        assets.save(f'passport/grid-{state}.png', frame, text_rect=[12, 8, 96, 30])
    mask = image((104, 52)); d = ImageDraw.Draw(mask)
    d.rectangle((6, 25, 97, 45), fill=rgba('seal'))
    fonts.text(mask, (14, 29), '未解锁', 12, 'muted')
    mask.alpha_composite(lock_icon(), (78, 8))
    assets.save('passport/locked-mask.png', mask)
    header = image((216, 24)); d = ImageDraw.Draw(header)
    d.rectangle((0, 0, 215, 1), fill=rgba('line'))
    d.rectangle((107, 0, 108, 23), fill=rgba('line'))
    fonts.text(header, (10, 6), '旅行护照', 12)
    assets.save('passport/header.png', header)


def build_numbers(assets, fonts):
    metrics = {}
    for height in (36, 20):
        point = 44 if height == 36 else 24
        glyphs = {}
        for label in '0123456789m+':
            font = fonts.get(point); box = font.getbbox(label)
            width, ink_height = box[2]-box[0], box[3]-box[1]
            assert ink_height <= height
            bitmap = image((width+4, height))
            fonts.text(bitmap, (2, (height-ink_height)//2), label, point)
            name = 'plus' if label == '+' else label
            assets.save(f'numbers/{height}/{name}.png', bitmap, limit=8, advance=width+3,
                        font_source='verified SourceHanSansCN-Medium', native_raster=True)
            glyphs[label] = {'path': f'numbers/{height}/{name}.png', 'advance': width+3, 'ink_height': ink_height}
        metrics[str(height)] = glyphs
    return metrics


def build_labels(assets, fonts):
    for name, label, width, color, ink in (
            ('new-record', '新纪录', 72, 'accent', 'paper'),
            ('test-no-record', '测试不记录', 96, 'ink', 'paper'),
            ('placeholder', '占位关卡', 88, 'seal', 'muted')):
        out = image((width, 24), color); d = ImageDraw.Draw(out)
        d.rectangle((0, 0, width-1, 23), outline=rgba('ink'), width=2)
        fonts.text(out, (width//2, 5), label, 12, ink, 'center')
        assets.save(f'labels/{name}.png', out, text=label)
    out = image((220, 24)); fonts.text(out, (110, 3), 'NABO,陪你冒险', 16, align='center')
    assets.save('labels/boot-caption.png', out, text='NABO,陪你冒险')
    button = stamp_card((168, 28), selected=True)
    fonts.text(button, (84, 5), '按 OK 出发', 16, align='center')
    assets.save('labels/press-start.png', button, text='按 OK 出发')


def build_map_ui(assets):
    for state in ('unlocked', 'locked', 'current'):
        out = image((48, 40)); d = ImageDraw.Draw(out)
        color = 'select' if state == 'current' else 'seal' if state == 'locked' else 'paper'
        d.ellipse((2, 14, 45, 37), fill=rgba('shadow'), outline=rgba('ink'), width=2)
        d.ellipse((2, 6, 45, 29), fill=rgba(color), outline=rgba('accent' if state == 'current' else 'line'), width=3 if state == 'current' else 2)
        if state == 'current':
            d.rectangle((0, 11, 2, 28), fill=rgba('accent')); d.rectangle((45, 11, 47, 28), fill=rgba('accent'))
        assets.save(f'map/station-{state}.png', out, anchor=[24, 24])
    foot = image((10, 10)); d = ImageDraw.Draw(foot)
    d.ellipse((0, 0, 4, 4), fill=rgba('accent')); d.ellipse((4, 5, 8, 9), fill=rgba('accent'))
    assets.save('map/footprints-forward.png', foot)
    assets.save('map/footprints-backward.png', foot.transpose(Image.Transpose.ROTATE_180))
    assets.save('map/lock.png', lock_icon())
    for tier, name in enumerate(('bronze', 'silver', 'gold')):
        assets.save(f'map/stamp-{name}.png', medal(tier))
    assets.save('map/stamp-empty.png', medal(earned=False))
    marker = image((32, 20), 'select'); d = ImageDraw.Draw(marker)
    d.rectangle((0, 0, 31, 19), outline=rgba('accent'), width=2)
    d.polygon(((12, 15), (20, 15), (16, 19)), fill=rgba('accent'))
    assets.save('map/temporary-position-marker.png', marker, temporary=True,
                note='Unused when the real NABO sprite is available; no character drawing')
    ink = image((64, 64)); d = ImageDraw.Draw(ink)
    d.ellipse((2, 2, 61, 61), fill=rgba('accent'), outline=rgba('bronze'), width=3)
    for y in range(10, 55, 8):
        for x in range(10, 55, 8):
            if (x-32)**2+(y-32)**2 < 22**2: d.rectangle((x, y, x+1, y+1), fill=rgba('bronze'))
    assets.save('stamps/ink-pad.png', ink)


def build_wordmarks(assets, fonts):
    collection = stamp_card((220, 90)); d = ImageDraw.Draw(collection)
    fonts.text(collection, (110, 13), 'NABO ADVENTURE', 18, 'accent', 'center')
    fonts.text(collection, (110, 43), 'NABO 的冒险之旅', 18, align='center')
    d.rectangle((22, 72, 197, 73), fill=rgba('line'))
    assets.save('wordmarks/collection.png', collection, group='wordmarks', limit=16,
                text=['NABO ADVENTURE', 'NABO 的冒险之旅'])
    for _, english, chinese in GAMES:
        out = image((200, 80)); d = ImageDraw.Draw(out)
        d.rectangle((3, 3, 196, 76), fill=rgba('paper'), outline=rgba('line'), width=2)
        for x in range(8, 193, 8):
            d.rectangle((x, 0, x+3, 3), fill=rgba('paper'))
            d.rectangle((x, 76, x+3, 79), fill=rgba('paper'))
        fonts.text(out, (100, 13), english, 18, 'accent', 'center')
        fonts.text(out, (100, 43), chinese, 18, align='center')
        assets.save(f'wordmarks/{english.lower()}.png', out, group='wordmarks', limit=16, text=[english, chinese])
