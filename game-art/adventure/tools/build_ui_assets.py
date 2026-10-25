#!/usr/bin/env python3
"""Build selected vintage-passport UI assets at native pixels; no firmware edits."""
import argparse
import json
from pathlib import Path
from ui_assets_common import Assets, Fonts, OUT, COLORS, rgba, sha, rle_estimate
from ui_assets_parts import (build_cards, build_bars, build_passport, build_numbers, build_labels,
                            build_map_ui, build_wordmarks)
from ui_assets_art import build_resource_icons, build_cover
from ui_assets_previews import build_previews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path)
    parser.add_argument('--parts-only', action='store_true', help='Do not consume map/world art still under production')
    parser.add_argument('--character', type=Path, help='Approved welcome120 runtime frame; no head/face is redrawn')
    parser.add_argument('--character-anchor', type=int, nargs=2, help='Unmodified runtime frame foot anchor x y')
    args = parser.parse_args()
    fonts, assets = Fonts(args.font), Assets()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'palette.json').write_text(json.dumps(COLORS, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    nine = build_cards(assets)
    build_bars(assets); build_passport(assets, fonts); numbers = build_numbers(assets, fonts)
    build_labels(assets, fonts); build_map_ui(assets); build_wordmarks(assets, fonts)
    build_resource_icons(assets)
    cover = None if args.parts_only else build_cover(assets, fonts, args.character, args.character_anchor)
    previews = build_previews(assets, fonts)
    unique = {}
    for entry in assets.entries:
        if entry['pack']:
            bitmap = assets.load(entry['path'])
            entry['row_rle_estimate_bytes'] = rle_estimate(bitmap)
            unique.setdefault(entry['sha256'], entry['row_rle_estimate_bytes'])
    estimate = sum(unique.values())
    manifest = {'schema': 'nabo-ui-assets-v1', 'theme': 'selected round3 option 01 vintage passport journal',
                'status': 'generated_for_review_not_firmware_or_device_acceptance', 'native_scale': 1,
                'font': {'path': str(fonts.path), 'sha256': sha(fonts.path), 'chinese_sizes_px': [12, 16, 18]},
                'shared_ui_palette': {'path': 'palette.json', 'visible_colors': len({rgba(c) for c in COLORS}),
                                      'limit_including_transparent': 32},
                'nine_slice': nine, 'digit_metrics': numbers, 'cover': cover,
                'preview_screens': previews, 'assets': assets.entries,
                'budget': {'limit_bytes': 160*1024, 'row_rle_estimate_bytes_deduplicated': estimate,
                           'estimate_below_limit': estimate <= 160*1024,
                           'final_firmware_rle_measurement': 'pending main-task integration; PNG size is not firmware size'},
                'notes': ['No approved character pixels are redrawn.', 'No existing firmware/UI code is modified.',
                          'design/round3 originals are preserved.', 'Dynamic scores/names/hints remain font-rendered by firmware.']}
    (OUT / 'ui-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    print(json.dumps({'assets': len(assets.entries), 'shared_ui_visible_colors': manifest['shared_ui_palette']['visible_colors'],
                      'row_rle_estimate_bytes': estimate, 'cover_ready': cover is not None}, ensure_ascii=False))


if __name__ == '__main__':
    main()
