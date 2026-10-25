#!/usr/bin/env python3
"""Inspect actual exported pixels, layer reconstruction and 9-slice contracts."""
import json
from PIL import Image, ImageChops
from ui_assets_common import OUT, COLORS, rgba, pixels, sha, SLICE_NAMES, render_nine, check_nine, rle_estimate


def equal(first, second):
    diff = ImageChops.difference(first.convert('RGBA'), second.convert('RGBA'))
    return not any(high for _, high in diff.getextrema())


def main():
    manifest = json.loads((OUT / 'ui-manifest.json').read_text('utf-8'))
    declared=json.loads((OUT/manifest['shared_ui_palette']['path']).read_text('utf-8'))
    palette_values={tuple(bytes.fromhex(value.lstrip('#'))) for value in declared.values()}
    assert len(palette_values)+1<=32
    seen, shared, unique = set(), set(), {}
    for entry in manifest['assets']:
        path = OUT / entry['path']
        assert path.resolve().is_relative_to(OUT.resolve())
        assert entry['name'] not in seen, entry['name']
        seen.add(entry['name'])
        assert sha(path) == entry['sha256'], entry['path']
        bitmap = Image.open(path).convert('RGBA')
        assert list(bitmap.size) == entry['size']
        values = set(pixels(bitmap)); alpha = {p[3] for p in values}
        assert alpha <= {0, 255}
        visible = {p[:3] for p in values if p[3]}
        assert len(visible)+int(0 in alpha) <= entry['color_limit']
        assert ['#%02x%02x%02x' % color for color in sorted(visible)] == entry['palette']
        if entry['palette_group'] == 'shared': shared |= visible
        if entry['pack']:
            assert max(bitmap.size) <= 256, f'Split large assets for the actual sprite packer: {entry["path"]}'
            unique.setdefault(entry['sha256'], rle_estimate(bitmap))
    assert shared <= palette_values
    assert len(shared)+1 <= 32
    for component in manifest['nine_slice']:
        folder = OUT / component['path']; corner = component['corner_px']
        assert corner == (16 if component['family'] == 'popup' else 12)
        pieces = {name: Image.open(folder / f'{name}.png').convert('RGBA') for name in SLICE_NAMES}
        for size in ((48, 32), (240, 120)):
            render = render_nine(pieces, size, corner); check_nine(pieces, render, corner)
            proof = Image.open(OUT / f'preview/nine-slice/{component["family"]}-{component["state"]}-{size[0]}x{size[1]}.png')
            assert equal(render, proof)
    for name in manifest['preview_screens']:
        assert Image.open(OUT / f'preview/{name}.png').size == (240, 320)
    tile = Image.open(OUT / 'passport/page-tile.png')
    assert tile.size == (32, 32) and len(set(pixels(tile.convert('RGBA')))) <= 8
    for height in (20, 36):
        for glyph in '0123456789m+':
            name = 'plus' if glyph == '+' else glyph
            assert Image.open(OUT / f'numbers/{height}/{name}.png').height == height
    for name in ('new-record', 'test-no-record', 'placeholder'):
        bitmap = Image.open(OUT / f'labels/{name}.png')
        assert bitmap.width <= 100 and bitmap.height <= 24
    for name, max_size in (('map/lock.png', 16), ('map/footprints-forward.png', 10),
                           ('map/footprints-backward.png', 10), ('stamps/ink-pad.png', 64)):
        assert max(Image.open(OUT / name).size) <= max_size
    cover = manifest.get('cover')
    if cover:
        background = Image.open(OUT / cover['background']).convert('RGBA')
        hero = Image.open(OUT / cover['character']).convert('RGBA')
        combined = background.copy()
        combined.alpha_composite(Image.open(OUT / cover['logo']).convert('RGBA'), tuple(cover['logo_offset']))
        combined.alpha_composite(hero)
        reference = Image.open(OUT / cover['flattened_reference']).convert('RGBA')
        assert equal(combined, reference), 'Cover layers differ from flattened reference'
        assert len(set(pixels(reference))) <= 64
        assert equal(Image.open(OUT/'cover-character-sprite.png'),Image.open(OUT.parent/cover['character_source'])), 'Cover role pixels changed'
        assert set(pixels(background.crop((0, 270, 240, 320)))) == {rgba('paper')}
        for key in ('caption', 'start_button'):
            component = cover[key]
            combined.alpha_composite(Image.open(OUT / component['path']).convert('RGBA'), tuple(component['offset']))
        assert equal(combined, Image.open(OUT / 'preview/cover.png')), 'Cover preview does not reconstruct exactly'
    estimate = sum(unique.values())
    assert estimate <= 160*1024
    report = {'status': 'PASS: EXPORTED PIXEL AND STRUCTURAL CHECKS', 'firmware_or_device_acceptance': False,
              'assets': len(manifest['assets']), 'shared_ui_visible_colors': len(shared),
              'nine_slice': '6 families/states; 48x32 and 240x120; original corners, no interior gaps',
              'font': manifest['font'], 'cover_layer_assembly': 'pixel_equal' if cover else 'pending map/character art',
              'fonts':manifest.get('fonts'), 'selected_dynamic_text':manifest.get('selected_dynamic_text'),
              'preview_screen_count': len(manifest['preview_screens'])+bool(cover),
              'row_rle_estimate_bytes_deduplicated': estimate, 'packed_limit_bytes': 160*1024,
              'actual_python_codec_measurement':manifest['budget'],
              'actual_firmware_pack_measurement':'pending root C integration; Python streams/tables measured, no C pass inferred'}
    (OUT / 'ui-qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    print(json.dumps({'status':report['status'],'assets':report['assets'],'shared_ui_visible_colors':len(shared),
        'preview_screen_count':report['preview_screen_count'],'cover_layer_assembly':report['cover_layer_assembly'],
        'ui_plus_current_boot_estimate':manifest['budget']['ui_plus_current_boot_estimate']},ensure_ascii=True))


if __name__ == '__main__':
    main()
