"""Native UI resource symbols and layered cover assembled from approved art."""
from pathlib import Path
from PIL import Image, ImageDraw
from ui_assets_common import ART, OUT, image, rgba, pixels, tiled_paste, sha


def build_resource_icons(assets):
    for name in ('stamina', 'oxygen', 'steam', 'spirit', 'temperature', 'hot-air', 'fuel'):
        out = image((16, 16)); d = ImageDraw.Draw(out)
        if name == 'stamina':
            d.polygon(((1, 3), (4, 1), (8, 4), (12, 1), (15, 3), (15, 8), (8, 15), (1, 8)), fill=rgba('accent'), outline=rgba('ink'))
            d.rectangle((3, 3, 5, 5), fill=rgba('select'))
        elif name == 'oxygen':
            d.rectangle((6, 0, 10, 3), fill=rgba('ink'))
            d.rounded_rectangle((3, 3, 13, 15), 3, fill=rgba('blue'), outline=rgba('ink'), width=2)
            d.rectangle((6, 6, 10, 10), fill=rgba('paper'))
        elif name == 'steam':
            d.rectangle((2, 10, 13, 15), fill=rgba('teal'), outline=rgba('ink'), width=2)
            for x in (3, 8, 12): d.line(((x, 7), (x-1, 4), (x+1, 1)), fill=rgba('muted'), width=2)
        elif name == 'spirit':
            d.ellipse((1, 1, 14, 14), fill=rgba('gold'), outline=rgba('ink'), width=2)
            d.ellipse((7, 0, 16, 10), fill=(0, 0, 0, 0))
            d.rectangle((11, 9, 13, 11), fill=rgba('accent'))
        elif name == 'temperature':
            d.rounded_rectangle((5, 0, 10, 12), 2, fill=rgba('paper'), outline=rgba('ink'), width=2)
            d.ellipse((3, 8, 12, 15), fill=rgba('accent'), outline=rgba('ink'), width=2)
            d.rectangle((7, 4, 8, 11), fill=rgba('accent'))
        elif name == 'hot-air':
            d.polygon(((8, 0), (11, 5), (12, 3), (15, 10), (13, 14), (8, 15), (2, 12), (2, 8), (6, 3), (6, 7)), fill=rgba('accent'), outline=rgba('ink'))
            d.polygon(((8, 7), (11, 12), (8, 14), (5, 12)), fill=rgba('select'))
        else:
            d.rectangle((4, 0, 10, 3), fill=rgba('ink'))
            d.polygon(((3, 3), (12, 3), (14, 6), (14, 15), (2, 15), (2, 5)), fill=rgba('gold'), outline=rgba('ink'))
            d.line(((5, 7), (11, 13)), fill=rgba('ink'), width=2)
            d.line(((11, 7), (5, 13)), fill=rgba('ink'), width=2)
        assets.save(f'resources/icons/{name}.png', out)


def world_tile(world):
    folder = ART / 'map/tiles' / world
    paths = sorted(folder.glob('*.png'))
    preferred = next((p for p in paths if any(word in p.stem for word in ('ground', 'base', 'water', 'terrain'))), None)
    path = preferred or (paths[0] if paths else None)
    if not path: raise FileNotFoundError(f'Map world tiles not yet ready: {world}')
    tile = Image.open(path).convert('RGBA')
    assert tile.size == (32, 32)
    return tile, path


def source_character(path, height=120, colors=48):
    """Only crop/resample/quantize existing pixels; no character geometry is drawn."""
    original = Image.open(path).convert('RGBA')
    mask = original.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
    source = original.crop(mask.getbbox())
    scaled = source.resize((round(source.width*height/source.height), height), Image.Resampling.LANCZOS)
    rgb = scaled.convert('RGB').quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                                        dither=Image.Dither.NONE).convert('RGB')
    output = rgb.convert('RGBA')
    output.putalpha(scaled.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
    return output


def build_cover(assets, fonts, character_path=None, character_anchor=None):
    background = image((240, 320), 'paper'); d = ImageDraw.Draw(background)
    # The cover is a travel scrapbook: four native-size map vignettes, not a
    # scaled screenshot. The middle vertical corridor leaves room for NABO.
    d.rectangle((5, 5, 234, 267), outline=rgba('line'), width=2)
    for y in range(15, 261, 20):
        d.ellipse((2, y, 8, y+6), fill=rgba('shadow'), outline=rgba('line'), width=1)
    sources = []
    worlds = [('space', '太空', (14, 105, 88, 173)), ('mountain', '雪山', (152, 105, 226, 173)),
              ('town', '小镇', (14, 185, 88, 257)), ('deep-sea', '深海', (152, 185, 226, 257))]
    for world, label, box in worlds:
        tile, path = world_tile(world)
        sources.append({'path': str(path.relative_to(ART)), 'sha256': sha(path)})
        base = {'space': 'ink', 'mountain': 'paper', 'town': 'bg', 'deep-sea': 'blue'}[world]
        d.rectangle((box[0], box[1], box[2]-1, box[3]-1), fill=rgba(base))
        tiled_paste(background, tile, box)
        d.rectangle((box[0], box[1], box[2]-1, box[3]-1), outline=rgba('ink'), width=2)
        # Native 96px landmarks are clipped by the postcard window, never scaled.
        landmark_name = {'deep-sea': 'dive', 'town': 'kiosk', 'mountain': 'climb', 'space': 'space'}[world]
        landmark_path = ART / f'map/landmarks/{landmark_name}.png'
        if landmark_path.exists():
            landmark = Image.open(landmark_path).convert('RGBA')
            crop_x = (96-(box[2]-box[0]))//2
            crop = landmark.crop((crop_x, 96-(box[3]-box[1]), crop_x+box[2]-box[0], 96))
            background.alpha_composite(crop, (box[0], box[1]))
            sources.append({'path': str(landmark_path.relative_to(ART)), 'sha256': sha(landmark_path)})
        tag = image((34, 18), 'paper'); fonts.text(tag, (17, 2), label, 12, align='center')
        background.alpha_composite(tag, (box[0]+4, box[1]+4))
    # These are footer *layout slots*. No character, logo or caption is baked in.
    d.rectangle((0, 270, 239, 319), fill=rgba('paper'))
    assets.save('cover-background.png', background, group='cover', limit=64, pack=False,
                contains_character=False, source_art=sources, reserved_logo=[10, 8, 230, 98],
                reserved_character=[78, 138, 162, 266], reserved_footer=[0, 270, 240, 320])
    assets.save('cover-background-top.png', background.crop((0, 0, 240, 256)), group='cover', limit=64,
                draw_offset=[0, 0])
    assets.save('cover-background-bottom.png', background.crop((0, 256, 240, 320)), group='cover', limit=64,
                draw_offset=[0, 256])
    if character_path:
        character_path = Path(character_path).resolve()
        hero = Image.open(character_path).convert('RGBA')
        assert character_anchor is not None, 'Approved runtime frame requires its documented anchor'
        assert len({p[:3] for p in pixels(hero) if p[3]}) <= 48
        assert {p[3] for p in pixels(hero)} <= {0, 255}
        anchor = character_anchor
    else:
        character_path = ART / 'frames/travel/masters/idle/000.png'
        hero = source_character(character_path, 120, 48)
        anchor = (hero.width//2, hero.height)
    layer = image((240, 320))
    xy = (120-anchor[0], 266-anchor[1])
    layer.alpha_composite(hero, xy)
    assets.save('cover-character.png', layer, group='character', limit=64, pack=False,
                source=str(character_path.relative_to(ART)), source_sha256=sha(character_path),
                source_anchor=list(anchor),
                note='Static composition reference; firmware may use the separate welcome120 animation')
    assets.save('cover-character-sprite.png', hero, group='character', limit=64, pack=False, draw_offset=list(xy),
                note='Reference only; use manifest travel/welcome animation in firmware')
    logo = assets.load('wordmarks/collection.png')
    composed = background.copy(); composed.alpha_composite(logo, (10, 8)); composed.alpha_composite(layer)
    assets.save('cover-illustration.png', composed, group='cover', limit=64, pack=False,
                composition=['cover-background.png', 'wordmarks/collection.png@10,8', 'cover-character.png'],
                reserved_footer=[0, 270, 240, 320])
    preview = composed.copy()
    preview.alpha_composite(assets.load('labels/boot-caption.png'), (10, 270))
    preview.alpha_composite(assets.load('labels/press-start.png'), (36, 292))
    target = OUT / 'preview'; target.mkdir(parents=True, exist_ok=True)
    preview.save(target / 'cover.png', optimize=True)
    return {'background': 'cover-background.png', 'character': 'cover-character.png',
            'flattened_reference': 'cover-illustration.png', 'logo': 'wordmarks/collection.png',
            'logo_offset': [10, 8], 'character_foot_anchor': [120, 266], 'character_height': 120,
            'character_source': str(character_path.relative_to(ART)), 'character_source_sha256': sha(character_path),
            'character_source_anchor': list(anchor),
            'caption': {'text': 'NABO,陪你冒险', 'path': 'labels/boot-caption.png', 'offset': [10, 270]},
            'start_button': {'path': 'labels/press-start.png', 'offset': [36, 292]},
            'layer_assembly': 'exact; see verify_ui_assets.py', 'source_art': sources}
