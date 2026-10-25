#!/usr/bin/env python3
"""Rebuild the three review boards; deterministic UI, sampled approved NABO layer."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
from ui_primitives import Board, THEMES
from ui_scenes import SCENES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
FONT_SHA = 'a94e558a2fe972bee4f46bce0843abff37063fd68c33f1e7d9058f6f09432b01'
FONT_CANDIDATES = [ROOT.parent / 'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf',
                   ROOT.parent / 'nabo-sound-lab/tools/fonts/SourceHanSansCN-Medium.otf']
CHARACTER = ROOT / 'game-art/adventure/art/frames/travel/masters/idle/000.png'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export_palette(theme, folder):
    colors = {key: value for key, value in theme.items() if value.startswith('#')}
    assert len(set(colors.values())) <= 32
    (folder / 'palette.json').write_text(json.dumps(colors, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    palette = Image.new('RGB', (240, 52), theme['bg'])
    draw = ImageDraw.Draw(palette)
    for i, color in enumerate(dict.fromkeys(colors.values())):
        x, y = (i % 10)*24, (i//10)*26
        draw.rectangle((x+2, y+2, x+21, y+23), fill=color)
    palette.save(folder / 'palette.png')
    return list(dict.fromkeys(colors.values()))


def character_assets(path):
    source = Image.open(path).convert('RGBA')
    alpha = source.getchannel('A')
    bbox = alpha.point(lambda a: 255 if a >= 128 else 0).getbbox()
    assert bbox
    source = source.crop(bbox)
    height = 72
    reference = source.resize((round(source.width * height/source.height), height), Image.Resampling.LANCZOS)
    q = reference.convert('RGB').quantize(colors=63, method=Image.Quantize.MEDIANCUT)
    palette = [0, 0, 0] + q.getpalette()[:63*3]
    palette += [0] * (768-len(palette))
    result = {}
    for height in (48, 56, 72):
        small = source.resize((round(source.width * height/source.height), height), Image.Resampling.LANCZOS)
        quantized = small.convert('RGB').quantize(palette=q, dither=Image.Dither.NONE)
        colors = list(quantized.get_flattened_data())
        assert max(colors) < 63
        indices = Image.new('P', small.size)
        indices.putpalette(palette)
        alphas = list(small.getchannel('A').get_flattened_data())
        indices.putdata([color+1 if a >= 128 else 0 for color, a in zip(colors, alphas)])
        indices.info['transparency'] = 0
        indices.save(HERE / f'nabo-travel-{height}px-64color.png', transparency=0, optimize=True)
        result[height] = indices.convert('RGBA')
    return result, bbox, palette[:192]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path)
    parser.add_argument('--character', type=Path, default=CHARACTER)
    args = parser.parse_args()
    font = args.font or next((p for p in FONT_CANDIDATES if p.exists()), None)
    if not font or sha(font) != FONT_SHA:
        raise SystemExit('Verified SourceHanSansCN-Medium.otf is required; no substitute font is allowed.')
    sprites, bbox, sprite_palette = character_assets(args.character)
    report = {'status': 'review_candidates_not_user_selected', 'screen_size': [240, 320], 'native_scale': 1,
              'future_boot_request': {'status': 'recorded_for_round5_not_implemented',
                                      'character': 'selected option 01 hiker NABO',
                                      'exact_av_text': 'NABO,陪你冒险',
                                      'audio_provenance': 'existing-series source review pending; no new audio in round3'},
              'font': {'path': str(font), 'sha256': sha(font), 'sizes_px': [12, 16, 18]},
              'character': {'source': str(args.character), 'sha256': sha(args.character), 'crop_bbox': bbox,
                            'source_identity': 'selected round1/v2 option 01 hiker; sampled idle front',
                            'palette_entries_including_transparent': 64, 'alpha_threshold': 128,
                            'ui_palette_separate': True, 'palette_rgb': sprite_palette}, 'directions': {}}
    all_boards = Image.new('RGB', (960, 960), THEMES['01-passport']['bg'])
    for row, (key, theme) in enumerate(THEMES.items()):
        folder = HERE / key
        folder.mkdir(exist_ok=True)
        colors = export_palette(theme, folder)
        contact = Image.new('RGB', (960, 320))
        screens = {}
        for column, (scene_name, render) in enumerate(SCENES.items()):
            board = Board(theme, font)
            render(board)
            used = len(board.image.getcolors(100000) or [])
            assert used <= 32, (key, scene_name, used)
            board.image.save(folder / f'{scene_name}-ui-layer.png', optimize=True)
            character = Image.new('RGBA', (240, 320))
            for placement in board.character_places:
                sprite = sprites[placement['height']]
                xy = (placement['x_center']-sprite.width//2, placement['foot_y']-sprite.height)
                character.alpha_composite(sprite, xy)
            character.save(folder / f'{scene_name}-character-layer.png', optimize=True)
            composite = Image.alpha_composite(board.image.convert('RGBA'), character).convert('RGB')
            composite.save(folder / f'{scene_name}.png', optimize=True)
            contact.paste(composite, (column*240, 0))
            screens[scene_name] = {'ui_colors': used, 'size': [240, 320],
                                    'text': board.text_boxes, 'character_placements': board.character_places}
        contact.save(folder / 'board.png', optimize=True)
        all_boards.paste(contact, (0, row*320))
        (folder / 'layout.json').write_text(json.dumps(screens, ensure_ascii=False, indent=2)+'\n', 'utf-8')
        report['directions'][key] = {'name': theme['name'], 'ui_shared_palette_count': len(colors),
                                      'future_boot': 'NABO in approved travel outfit with exact audiovisual line: NABO,陪你冒险',
                                      'screens': {n: {'ui_colors': s['ui_colors']} for n, s in screens.items()}}
    all_boards.save(HERE / 'all-directions-1x.png', optimize=True)
    (HERE / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    print(json.dumps({key: value['ui_shared_palette_count'] for key, value in report['directions'].items()}))


if __name__ == '__main__':
    main()
