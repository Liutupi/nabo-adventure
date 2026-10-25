#!/usr/bin/env python3
"""Build selected vintage-passport UI assets at native pixels; no firmware edits."""
import argparse
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw
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
    nine = build_cards(assets)
    build_bars(assets); build_passport(assets, fonts); numbers = build_numbers(assets, fonts)
    build_labels(assets, fonts); build_map_ui(assets); build_wordmarks(assets, fonts)
    build_resource_icons(assets)
    cover = None if args.parts_only else build_cover(assets, fonts, args.character, args.character_anchor)
    previews = build_previews(assets, fonts)
    board=Image.new('RGBA',(960,1280),rgba('paper'))
    all_names=(['cover'] if cover else [])+previews
    for i,name in enumerate(all_names):board.alpha_composite(Image.open(OUT/f'preview/{name}.png').convert('RGBA'),((i%4)*240,(i//4)*320))
    board.save(OUT/'preview/all-13-1x.png')
    core=Image.new('RGBA',(720,320),rgba('paper'))
    for i,name in enumerate(('cover','map','passport')):
        if (OUT/f'preview/{name}.png').exists():core.alpha_composite(Image.open(OUT/f'preview/{name}.png').convert('RGBA'),(i*240,0))
    core.save(OUT/'preview/core-3-1x.png')
    corners=Image.new('RGBA',(320,6*164),rgba('paper'));draw=ImageDraw.Draw(corners)
    for i,item in enumerate(nine):
        stem=f'{item["family"]}-{item["state"]}'
        draw.text((4,i*164+2),stem,font=fonts.get(12),fill=rgba('ink'))
        for size,xy in [((48,32),(4,i*164+30)),((240,120),(76,i*164+30))]:
            corners.alpha_composite(Image.open(OUT/f'preview/nine-slice/{stem}-{size[0]}x{size[1]}.png').convert('RGBA'),xy)
    corners.save(OUT/'preview/nine-slice/contact.png')
    (OUT / 'palette.json').write_text(json.dumps(COLORS, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    unique = {}
    for entry in assets.entries:
        if entry['pack']:
            bitmap = assets.load(entry['path'])
            entry['row_rle_estimate_bytes'] = rle_estimate(bitmap)
            unique.setdefault(entry['sha256'], entry['row_rle_estimate_bytes'])
    estimate = sum(unique.values())
    manifest = {'schema': 'nabo-ui-assets-v1', 'theme': 'selected round3 option 01 vintage passport journal',
                'status': 'v2 production assets pending C integration and device acceptance', 'native_scale': 1,
                'font': {'path':str(fonts.path),'sha256':sha(fonts.path),'chinese_sizes_px':[12],'role':'body'},
                'fonts':fonts.sources,'typography':'16/18 Noto Sans SC Bold700, 12 SourceHan Medium500; fixed English Montserrat Bold700',
                'selected_dynamic_text':'#fffaf0',
                'shared_ui_palette': {'path': 'palette.json', 'visible_colors': len({rgba(c) for c in COLORS}),
                                      'sha256':sha(OUT/'palette.json'),
                                      'limit_including_transparent': 32},
                'nine_slice': nine, 'digit_metrics': numbers, 'cover': cover,
                'preview_screens': previews, 'assets': assets.entries,
                'budget': {'limit_bytes': 160*1024, 'row_rle_estimate_bytes_deduplicated': estimate,
                           'estimate_below_limit': estimate <= 160*1024,
                           'final_firmware_rle_measurement': 'pending main-task integration; PNG size is not firmware size'},
                'notes': ['No approved character pixels are redrawn.','No hand-written firmware is modified; UI assets rebuilt after checkpoint899d275.',
                          'design/round3 originals are preserved.', 'Dynamic scores/names/hints remain font-rendered by firmware.']}
    (OUT / 'ui-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', 'utf-8')
    # Measure every declared packed resource, including duplicate-looking pieces.
    # This matches the codec tables; compilation with the real C decoder remains
    # a separate gate owned by integration, never inferred from this measurement.
    sys.path.insert(0,str(OUT.parents[3]/'tools'))
    from adventure_assets_manifest import load_resources
    from generate_adv_sprites import index_frames,pack,decode
    resources,_,_=load_resources(OUT.parent,['ui']);rle=tables=descriptor=frames=0
    for resource in resources:
        palette,indexed=index_frames(resource.images);encoded=pack(*resource.size,indexed)
        assert all(decode(encoded,i)==f for i,f in enumerate(indexed))
        rle+=len(encoded['data']);tables+=len(palette)*2+len(encoded['keys'])*2+len(encoded['rows'])*4
        descriptor+=24+len(resource.id.encode())+1+40;frames+=len(indexed)
    descriptor+=len(nine)*36+sum(len(g)*12 for g in numbers.values())+len({rgba(c) for c in COLORS})*2+8
    total=rle+tables+descriptor
    welcome_path=OUT.parents[3]/'firmware/main/generated/adv_assets_travel_welcome__p0.json'
    welcome=json.loads(welcome_path.read_text('utf-8'));welcome_bytes=welcome['data_bytes']+welcome['table_bytes']+32
    assert total+welcome_bytes<=160*1024, 'UI + actual current welcome exceed 160KiB; do not hide character costs in travel'
    manifest['budget'].update(actual_python_rle_bytes=rle,actual_python_table_bytes=tables,
        descriptor_catalog_estimate_c3=descriptor,actual_static_estimate_c3=total,
        current_boot_welcome_bytes=welcome_bytes,ui_plus_current_boot_estimate=total+welcome_bytes,
        character_budget_allowance=160*1024-total,
        actual_production_c_validation='pending root integration; Python lossless index roundtrip only',
        new_boot_v2='replace current welcome cost with measured final v2 cost before acceptance')
    (OUT/'ui-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    fontdir=OUT/'fonts';fontdir.mkdir(exist_ok=True)
    for size in (16,18):
        chars=sorted({c for run in fonts.runs if run['font']=='bold' and run['size']==size for c in run['text'] if not c.isspace()})
        (fontdir/f'bold{size}-subset.txt').write_text(''.join(chars)+'\n','utf-8')
    (fontdir/'sources.json').write_text(json.dumps(fonts.sources,ensure_ascii=False,indent=2)+'\n','utf-8')
    license_dir=OUT/'licenses';license_dir.mkdir(exist_ok=True)
    for path in (OUT/'design/refinement-v2/licenses').glob('*.txt'):(license_dir/path.name).write_bytes(path.read_bytes())
    tokens=json.loads((OUT/'design/refinement-v2/layout-tokens.json').read_text('utf-8'))
    tokens['cover']['wordmark_size']=[220,90];tokens['cover']['button']=[16,284,208,34]
    tokens['passport']={'header_xy':[12,40],'grid_size':[104,52],'grid_x':[12,124],
        'grid_y':[70,124,178,232],'title_ink_relative':[8,8],'meta_ink_relative':[8,30],
        'best_right_relative':96,'selected_text':'#fffaf0','locked_mask':'icon only; draw 未解锁 dynamically, cream if selected'}
    tokens['title_pages']={'wordmark_xy':[20,42],'wordmark_size':[200,80]}
    tokens['page_layouts']={name:f'preview/{name}.layout.json' for name in previews}
    (OUT/'integration-tokens.json').write_text(json.dumps(tokens,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'assets': len(assets.entries), 'shared_ui_visible_colors': manifest['shared_ui_palette']['visible_colors'],
                      'actual_static_estimate_c3':total,'ui_plus_boot':total+welcome_bytes,'cover_ready':cover is not None},ensure_ascii=False))


if __name__ == '__main__':
    main()
