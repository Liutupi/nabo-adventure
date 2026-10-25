"""Emit stable immutable row-RLE sprite/patch/catalog symbols."""
import hashlib
import json
from pathlib import Path
import re
from PIL import Image
from generate_adv_sprites import generate, index_frames, pack, decode, rgb565


def fragments(resource):
    w, h = resource.size
    for y in range(0, h, 256):
        for x in range(0, w, 256):
            box = (x, y, min(x+256, w), min(y+256, h))
            yield x+resource.offset[0], y+resource.offset[1], [im.crop(box) for im in resource.images]


def emit_sprites(resources, folder):
    pieces, interned = [], {}
    for resource in resources:
        for piece_index, (x, y, images) in enumerate(fragments(resource)):
            logical_symbol = f'{resource.symbol}__p{piece_index}'
            # Exact RGBA, dimensions and ordered frames, within one cost group.
            # Anchors/fps/offsets belong to logical catalog records, not sprites.
            signature = (resource.group, images[0].size, len(images),
                         tuple(hashlib.sha256(im.tobytes()).digest() for im in images))
            candidates = interned.setdefault(signature, [])
            canonical = next((p for p in candidates if all(a.tobytes() == b.tobytes()
                              for a, b in zip(images, p['images']))), None)
            palette, indexed = index_frames(images)
            if canonical is not None:
                if palette != canonical['palette'] or indexed != canonical['frames']:
                    raise ValueError('Identical RGBA sprite produced different indexed frames')
                canonical['report']['logical_uses'].append({'resource_id': resource.id,
                                                           'logical_symbol': logical_symbol, 'offset': [x, y]})
                pieces.append({'resource': resource, 'symbol': canonical['symbol'], 'logical_symbol': logical_symbol,
                               'offset': (x, y), 'images': images, 'palette': palette, 'frames': indexed,
                               'report': canonical['report']})
                continue
            symbol = logical_symbol
            paths = []
            snapshots = folder / '_inputs' / symbol
            snapshots.mkdir(parents=True)
            for frame, bitmap in enumerate(images):
                path = snapshots / f'{frame:05}.png'; bitmap.save(path); paths.append(path)
            encoded = pack(images[0].width, images[0].height, indexed)
            if any(decode(encoded, f) != frame for f, frame in enumerate(indexed)):
                raise ValueError('Python RLE decode differs from reference')
            report = generate(paths, folder/symbol, symbol)
            if report['frame_sha256'] != [hashlib.sha256(frame).hexdigest() for frame in indexed]:
                raise ValueError('Generator input/reference mismatch')
            # Actual C3 adv_sprite_t layout: 4*u16 + 2*u32 + 4 pointers = 32 bytes.
            report.update(resource_id=resource.id, group=resource.group, symbol=symbol,
                          offset=[x, y], original_sources=[{'path': str(p), 'sha256': s}
                                                         for p, s in zip(resource.paths, resource.hashes)],
                          descriptor_bytes_c3=32,
                          logical_uses=[{'resource_id': resource.id, 'logical_symbol': logical_symbol, 'offset': [x, y]}])
            piece = {'resource': resource, 'symbol': symbol, 'logical_symbol': logical_symbol,
                     'offset': (x, y), 'images': images, 'palette': palette, 'frames': indexed, 'report': report}
            pieces.append(piece); candidates.append(piece)
    for candidates in interned.values():
        for physical in candidates:
            (folder/f'{physical["symbol"]}.json').write_text(json.dumps(physical['report'], indent=2)+'\n', 'utf-8', newline='\r\n')
    return pieces


HEADER = '''#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "adv_sprite.h"
#include "adv_ninepatch.h"
typedef struct { const adv_sprite_t *sprite; int16_t x, y; } adv_asset_piece_t;
typedef struct {
    const char *id;
    const adv_asset_piece_t *pieces;
    uint16_t piece_count, width, height;
    int16_t anchor_x, anchor_y;
    uint16_t fps;
    bool loop;
} adv_asset_record_t;
typedef struct { uint8_t glyph; const adv_asset_record_t *asset; uint16_t advance; } adv_asset_digit_t;
extern const adv_asset_record_t adv_assets_catalog[];
extern const size_t adv_assets_catalog_count;
const adv_asset_record_t *adv_assets_find(const char *id);
extern const uint16_t adv_assets_ui_palette[];
extern const size_t adv_assets_ui_palette_count;
'''


def emit_catalog(resources, pieces, folder, ui):
    sources, header = ['#include "adv_assets_catalog.h"', '#include <string.h>'], [HEADER]
    for symbol in dict.fromkeys(piece['symbol'] for piece in pieces): sources.append(f'#include "{symbol}.h"')
    by_resource = {r.id: [p for p in pieces if p['resource'] is r] for r in resources}
    for resource in resources:
        sources.append(f'static const adv_asset_piece_t {resource.symbol}__pieces[] = {{')
        for piece in by_resource[resource.id]:
            x, y = piece['offset']; sources.append(f'    {{&{piece["symbol"]}, {x}, {y}}},')
        sources.append('};')
    sources.append('const adv_asset_record_t adv_assets_catalog[] = {')
    for resource in resources:
        w, h = resource.size; x, y = resource.anchor
        sources.append(f'    {{{json.dumps(resource.id)}, {resource.symbol}__pieces, {len(by_resource[resource.id])}, '
                       f'{w}, {h}, {x}, {y}, {resource.fps}, {str(resource.loop).lower()}}},')
    sources += ['};', 'const size_t adv_assets_catalog_count = sizeof(adv_assets_catalog)/sizeof(adv_assets_catalog[0]);',
                'const adv_asset_record_t *adv_assets_find(const char *id) {', '    if (!id) return NULL;',
                '    for (size_t i=0; i<adv_assets_catalog_count; i++)',
                '        if (!strcmp(id, adv_assets_catalog[i].id)) return &adv_assets_catalog[i];', '    return NULL;', '}']
    patches, metrics = [], {}
    if ui:
        names = ('top-left', 'top', 'top-right', 'left', 'center', 'right', 'bottom-left', 'bottom', 'bottom-right')
        for patch in ui['nine_slice']:
            symbol = f'adv_assets_patch_{patch["family"]}_{patch["state"]}'
            tiles = []
            for name in names:
                resource_id = 'ui/'+patch['path']+'/'+name
                tile = by_resource.get(resource_id)
                if not tile or len(tile) != 1 or tile[0]['resource'].fps: raise ValueError('Nine-slice requires nine declared static single-piece assets')
                tiles.append('&'+tile[0]['symbol'])
            sources.append(f'const adv_ninepatch_t {symbol} = {{{{{", ".join(tiles)}}}}};')
            header.append(f'extern const adv_ninepatch_t {symbol};')
            patches.append({'name': symbol, 'id': patch['family']+'/'+patch['state'], 'corner_px': patch['corner_px']})
        index = {r.id: i for i, r in enumerate(resources)}
        for height, glyphs in ui['digit_metrics'].items():
            symbol = 'adv_assets_digits_'+height
            sources.append(f'const adv_asset_digit_t {symbol}[] = {{')
            for glyph, metric in glyphs.items():
                resource_id = 'ui/'+Path(metric['path']).with_suffix('').as_posix()
                if resource_id not in index: raise ValueError('Digit metric references a missing packed asset')
                sources.append(f'    {{{ord(glyph)}, &adv_assets_catalog[{index[resource_id]}], {metric["advance"]}}},')
            sources.append('};'); header.append(f'extern const adv_asset_digit_t {symbol}[{len(glyphs)}];')
            metrics[height] = symbol
        colors = sorted({rgb565(tuple(bytes.fromhex(c[1:]))) for c in ui['palette_values'].values()})
        for name, color in ui['palette_values'].items():
            value = rgb565(tuple(bytes.fromhex(color[1:])))
            header.append(f'#define ADV_ASSETS_UI_{re.sub("[^A-Za-z0-9]", "_", name).upper()} ((uint16_t)0x{value:04x})')
    else: colors = []
    sources.append('const uint16_t adv_assets_ui_palette[] = {'+', '.join(str(c) for c in colors or [0])+'};')
    sources.append(f'const size_t adv_assets_ui_palette_count = {len(colors)};')
    (folder/'adv_assets_catalog.h').write_text('\n'.join(header)+'\n', 'utf-8', newline='\r\n')
    (folder/'adv_assets_catalog.c').write_text('\n'.join(sources)+'\n', 'utf-8', newline='\r\n')
    return {'patches': patches, 'digit_tables': metrics, 'shared_ui_palette_rgb565': colors}
