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
    background=image((240,320),'paper');d=ImageDraw.Draw(background);sources=[]
    d.polygon([(16,226),(43,222),(82,234),(89,262),(16,262)],fill=rgba('blue'))
    d.line([(17,236),(30,232),(44,236),(58,231)],fill=rgba('paper'),width=2)
    d.line([(20,251),(34,246),(49,249)],fill=rgba('paper'),width=2)
    for path,xy in [('map/tiles/mountain/snowcap-rock.png',(20,163)),('map/tiles/town/red-roof.png',(180,218))]:
        bitmap=Image.open(ART/path).convert('RGBA');background.alpha_composite(bitmap,xy)
        sources.append({'path':path,'sha256':sha(ART/path)})
    d.ellipse((185,151,209,175),fill=rgba('ink'))
    d.arc((180,158,215,168),0,330,fill=rgba('gold'),width=2)
    d.rectangle((216,145,218,147),fill=rgba('gold'));d.rectangle((175,180,177,182),fill=rgba('accent'))
    d.rectangle((0,270,239,319),fill=rgba('paper'))
    assets.save('cover-background.png',background,group='cover',limit=64,pack=False,
        contains_character=False,source_art=sources,reserved_logo=[10,12,230,102],
        reserved_character=[78,138,162,266],reserved_footer=[0,270,240,320])
    assets.save('cover-background-top.png',background.crop((0,0,240,256)),group='cover',limit=64,draw_offset=[0,0])
    assets.save('cover-background-bottom.png',background.crop((0,256,240,320)),group='cover',limit=64,draw_offset=[0,256])
    if not character_path:
        character_path=ART/'frames/travel/runtime/welcome/000.png';character_anchor=(31,120)
    character_path=Path(character_path).resolve();hero=Image.open(character_path).convert('RGBA')
    assert character_anchor is not None and len({p[:3] for p in pixels(hero) if p[3]})<=48
    assert {p[3] for p in pixels(hero)}<={0,255}
    anchor=character_anchor;layer=image((240,320));xy=(120-anchor[0],266-anchor[1]);layer.alpha_composite(hero,xy)
    assets.save('cover-character.png',layer,group='character',limit=64,pack=False,
        source=str(character_path.relative_to(ART)),source_sha256=sha(character_path),source_anchor=list(anchor),
        note='Reference only; separate animation is counted in the combined UI+boot budget')
    assets.save('cover-character-sprite.png',hero,group='character',limit=64,pack=False,draw_offset=list(xy),
        note='Unmodified approved runtime pixels; no rescale/recolor')
    composed=background.copy();composed.alpha_composite(assets.load('wordmarks/collection.png'),(10,12));composed.alpha_composite(layer)
    assets.save('cover-illustration.png',composed,group='cover',limit=64,pack=False,
        composition=['cover-background.png','wordmarks/collection.png@10,12','cover-character.png'],reserved_footer=[0,270,240,320])
    preview=composed.copy();preview.alpha_composite(assets.load('labels/boot-caption.png'),(10,270))
    preview.alpha_composite(assets.load('labels/press-start.png'),(16,284))
    target=OUT/'preview';target.mkdir(parents=True,exist_ok=True);preview.save(target/'cover.png',optimize=True)
    return {'background':'cover-background.png','character':'cover-character.png','flattened_reference':'cover-illustration.png',
        'logo':'wordmarks/collection.png','logo_offset':[10,12],'character_foot_anchor':[120,266],'character_height':120,
        'character_source':str(character_path.relative_to(ART)),'character_source_sha256':sha(character_path),
        'character_source_anchor':list(anchor),'caption':{'text':'NABO,陪你冒险','path':'labels/boot-caption.png','offset':[10,270]},
        'start_button':{'path':'labels/press-start.png','offset':[16,284]},'layer_assembly':'exact; verify_ui_assets.py',
        'source_art':sources,'character_budget_policy':'include welcome animation with UI; do not hide it in travel group'}
