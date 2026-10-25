#!/usr/bin/env python3
"""Validate manifest-declared art, reuse row-RLE v1, then publish owned generated C."""
import argparse
import json
from pathlib import Path
import tempfile
from adventure_assets_manifest import load_resources, verify_sources_unchanged, GAME_GROUPS
from adventure_assets_emit import emit_sprites, emit_catalog
from adventure_assets_verify import verify_c

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ART = ROOT/'game-art/adventure/art'
DEFAULT_OUTPUT = ROOT/'firmware/main/generated'
OWNERSHIP = 'adv_assets_generated.json'
UI_LIMIT = 160*1024
GAME_LIMIT = 260*1024


def budgets(resources, pieces, ui, catalog):
    groups = {}
    for resource in resources:
        item = groups.setdefault(resource.group, {'rle_bytes': 0, 'table_bytes': 0, 'descriptor_catalog_estimate_c3': 0,
                                                  'resources': 0, 'pieces': 0, 'frames': 0})
        item['resources'] += 1
        item['descriptor_catalog_estimate_c3'] += 24+len(resource.id.encode('utf-8'))+1
    for piece in pieces:
        item = groups[piece['resource'].group]; report = piece['report']
        item['rle_bytes'] += report['data_bytes']; item['table_bytes'] += report['table_bytes']
        item['descriptor_catalog_estimate_c3'] += 32+8
        item['pieces'] += 1; item['frames'] += report['verified_frames']
    if ui:
        groups['ui']['descriptor_catalog_estimate_c3'] += len(catalog['patches'])*36 + sum(
            len(glyphs)*12 for glyphs in ui['digit_metrics'].values()) + len(catalog['shared_ui_palette_rgb565'])*2 + 8
    for item in groups.values():
        item['static_bytes_estimate_c3'] = item['rle_bytes']+item['table_bytes']+item['descriptor_catalog_estimate_c3']
    return groups


def owned_files(output):
    path = output/OWNERSHIP
    if not path.exists(): return set()
    old = json.loads(path.read_text('utf-8'))
    if old.get('schema') != 'adventure-assets-package-v1': raise ValueError('Unrecognized generated ownership manifest')
    names = set(old['files'])
    for name in names:
        if Path(name).name != name or not name.startswith('adv_assets_') or Path(name).suffix not in ('.c', '.h', '.json'):
            raise ValueError('Unsafe ownership filename; refusing cleanup')
    return names


def build(art=DEFAULT_ART, output=DEFAULT_OUTPUT, groups=('travel', 'ui', 'static'), check_c=False, ui_limit=UI_LIMIT):
    if not 0 < ui_limit <= UI_LIMIT: raise ValueError('UI limit may not exceed the required 160 KiB')
    art, output = Path(art).resolve(), Path(output).resolve()
    groups = tuple(sorted(set(groups)))
    if not groups or not set(groups) <= {'travel', 'ui', 'static', *GAME_GROUPS}:
        raise ValueError('Unknown/empty asset group selection')
    # Complete source/header/hash/dimension/alpha/palette validation precedes writes.
    resources, manifests, ui = load_resources(art, groups)
    if not resources: raise ValueError('No explicitly declared resources to pack')
    previous = owned_files(output)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.adv-assets-stage-', dir=output) as tmp:
        stage = Path(tmp)
        pieces = emit_sprites(resources, stage)
        catalog = emit_catalog(resources, pieces, stage, ui)
        totals = budgets(resources, pieces, ui, catalog)
        if totals.get('ui', {}).get('static_bytes_estimate_c3', 0) > ui_limit:
            raise ValueError('UI actual RLE/tables/descriptors estimate exceeds budget; valid package left unchanged')
        for group in GAME_GROUPS:
            if totals.get(group, {}).get('static_bytes_estimate_c3', 0) > GAME_LIMIT:
                raise ValueError(f'{group} actual RLE/tables/descriptors estimate exceeds the 260 KiB game budget')
        c_check = verify_c(resources, pieces, catalog, stage) if check_c else None
        verify_sources_unchanged(art, resources, manifests)
        filenames = sorted(p.name for p in stage.glob('adv_assets_*') if p.is_file()) + [OWNERSHIP]
        if len(set(filenames)) != len(filenames): raise ValueError('Duplicate generated filename')
        for name in filenames:
            if (output/name).exists() and name not in previous: raise ValueError(f'Refusing to overwrite unowned file: {name}')
        report = {'schema': 'adventure-assets-package-v1', 'format': 'adv-row-rle-v1', 'groups': totals,
                  'files': filenames, 'source_manifests_sha256': manifests,
                  'source_frames': [{'id': r.id, 'sources': [{'path': str(p.relative_to(art)), 'sha256': h}
                                                           for p, h in zip(r.paths, r.hashes)],
                                     'canvas': list(r.size), 'anchor': list(r.anchor), 'fps': r.fps, 'loop': r.loop,
                                     'pieces': [{'symbol': p['symbol'], 'offset': list(p['offset']), 'size': list(p['images'][0].size)}
                                                for p in pieces if p['resource'] is r]} for r in resources],
                  'python_verified_frames': sum(p['report']['verified_frames'] for p in pieces), 'production_c': c_check,
                  'catalog': catalog, 'ui_limit_bytes': ui_limit,
                  'linker_alignment_and_final_elf_measurement': 'pending; RLE/tables exact, C3 descriptor estimates exclude linker padding/deduplication',
                  'acceptance': 'host packing validation only; no device/physical artwork acceptance implied'}
        (stage/OWNERSHIP).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf-8')
        # Only our explicit former ownership list may be removed. Handwritten files
        # and every other generated prefix remain untouched.
        for name in filenames: (stage/name).replace(output/name)
        for name in previous-set(filenames): (output/name).unlink(missing_ok=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--art', type=Path, default=DEFAULT_ART)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--group', choices=('travel', 'ui', 'static', *GAME_GROUPS), action='append')
    parser.add_argument('--verify-c', action='store_true')
    args = parser.parse_args()
    if any(group in GAME_GROUPS for group in args.group or ()) and args.output.resolve() == DEFAULT_OUTPUT.resolve():
        parser.error('New game art requires --output to a separate delivery directory until gameplay integration')
    try:
        report = build(args.art, args.output, args.group or ('travel', 'ui', 'static'), args.verify_c)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({'groups': report['groups'], 'python_verified_frames': report['python_verified_frames'],
                      'production_c': report['production_c']}, indent=2))


if __name__ == '__main__':
    main()
