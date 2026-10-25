#!/usr/bin/env python3
"""Index all eleven art rounds only after current manifest/C reports agree."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from adventure_assets_manifest import GAME_GROUPS, load_resources, digest
from build_adventure_assets import proof_tools, INTEGRATED_GAMES

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'game-art/adventure/art'


def evidence(path, expected, resources, art=ART, ui=None):
    report = json.loads(path.read_text('utf-8'))
    proof = report.get('production_c')
    if report.get('schema') != 'adventure-assets-package-v1' or not isinstance(proof, dict):
        raise ValueError(f'Missing actual production C validation: {path}')
    if report.get('tools_sha256') != proof_tools():
        raise ValueError('Stale or absent packer/decoder source hashes; rebuild the C package')
    code = report.get('generated_code_sha256')
    if not isinstance(code, dict) or not code:
        raise ValueError('Missing generated C/header hashes')
    if set(code) != {name for name in report.get('files', []) if Path(name).suffix in ('.c', '.h')}:
        raise ValueError('Generated code hash set differs from package ownership')
    for name, sha in code.items():
        if Path(name).name != name or not name.startswith('adv_assets_') or Path(name).suffix not in ('.c', '.h'):
            raise ValueError('Invalid generated code filename')
        if digest(path.parent/name) != sha:
            raise ValueError('Generated C/header changed after verification')
    if set(report.get('source_manifests_sha256', {})) != set(expected):
        raise ValueError('Packing report manifest set differs')
    for name in expected:
        if report['source_manifests_sha256'].get(name) != digest(art / name):
            raise ValueError(f'Stale packing evidence for {name}; rebuild its C package')
    listed = report.get('source_frames', [])
    source_rows = {r['id']: r for r in listed}
    if len(listed) != len(resources) or len(source_rows) != len(resources) or set(source_rows) != {r.id for r in resources}:
        raise ValueError('Packing report resource IDs/count differ')
    groups, frames, rows = {}, 0, 0
    for resource in resources:
        entry = source_rows[resource.id]
        sources = [{'path': p.relative_to(art).as_posix(), 'sha256': sha} for p, sha in zip(resource.paths, resource.hashes)]
        if (entry['sources'] != sources or entry['canvas'] != list(resource.size) or entry['anchor'] != list(resource.anchor) or
                entry['fps'] != resource.fps or entry['loop'] != resource.loop):
            raise ValueError('Packing report runtime sources/geometry differ')
        w, h = resource.size
        pieces = ((w+255)//256)*((h+255)//256)
        count = pieces*len(resource.paths)
        frames += count; rows += ((w+255)//256)*h*len(resource.paths)
        group = groups.setdefault(resource.group, {'resources': 0, 'pieces': 0, 'frames': 0})
        group['resources'] += 1; group['pieces'] += pieces; group['frames'] += count
    if set(report.get('groups', {})) != set(groups):
        raise ValueError('Packing report groups differ')
    for name, counts in groups.items():
        if any(report['groups'][name].get(k) != v for k, v in counts.items()):
            raise ValueError('Packing report group counts differ')
    patch_rows = len(ui['nine_slice'])*152 if ui else 0
    if (report.get('python_verified_frames') != frames or proof.get('verified_frames') != frames or
            proof.get('verified_sprite_rows') != rows or proof.get('verified_ninepatch_rows') != patch_rows):
        raise ValueError('C/Python validation counts differ from manifest geometry')
    return {key: report[key] for key in ('groups', 'python_verified_frames', 'production_c')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-sha256', help='Optional tested common-firmware association; never inferred from a fresh build')
    args = parser.parse_args()
    if args.candidate_sha256 and not re.fullmatch('[0-9a-f]{64}', args.candidate_sha256):
        parser.error('--candidate-sha256 must contain 64 lowercase hexadecimal digits')
    # The loader verifies explicit paths, hashes, dimensions, alpha and palettes.
    groups = ('travel', 'ui', 'static', *GAME_GROUPS)
    resources, manifests, ui = load_resources(ART, groups)
    common_report=json.loads((ROOT/'firmware/main/generated/adv_assets_generated.json').read_text('utf-8'))
    common_groups=set(common_report['groups']);base={'travel','ui','static'}
    if not base<=common_groups or not common_groups<=base|set(INTEGRATED_GAMES):
        raise ValueError('Production package declares unsupported gameplay integration')
    integrated=sorted(common_groups-base)
    common_dependencies = {name: sha for name, sha in manifests.items() if name not in
                           {f'{game}-manifest.json' for game in GAME_GROUPS if game not in integrated}}
    common = evidence(ROOT / 'firmware/main/generated/adv_assets_generated.json',
                      common_dependencies,
                      [r for r in resources if r.group in common_groups], ui=ui)
    games = {game: evidence(ROOT / 'private/game-art-c' / game / 'adv_assets_generated.json',
                            (f'{game}-manifest.json',), [r for r in resources if r.group == game]) for game in GAME_GROUPS}
    source = ART / 'reference/nabo-idle-original.png'
    from generate_boot_video import read_video
    video=read_video(ART)
    catalog = {
        'schema': 'nabo-adventure-art-catalog-v1',
        'scope': 'eleven art rounds; gameplay integration is listed separately',
        'identity': {'path': source.relative_to(ART).as_posix(), 'sha256': digest(source)},
        'selected_travel_design': 'design/round1/v2/01-hiker-design-board.png',
        'selected_ui_theme': 'ui/design/round3/01-passport',
        'boot_video': None if not video else {'task':'BOOT-V3-01','movie_frames':73,'poster_frames':1,
            'logical_fps':12,'runtime_canvas':[208,272],'display_canvas':[240,320],
            'media_bytes':video['bytes'],'validation':'Separate production video/renderer tests; excluded from row-RLE frame totals',
            'manifest':'boot/v3/runtime/manifest.json'},
        'source_manifests_sha256': manifests,
        'counts': {'resources': len(resources),
                   'frames_including_static': sum(len(r.paths) for r in resources)},
        'resources': [{'id': r.id, 'group': r.group, 'canvas': list(r.size),
                       'anchor': list(r.anchor), 'fps': r.fps, 'loop': r.loop,
                       'frame_count': len(r.paths)} for r in resources],
        'production_c_evidence': {'common': common, **games},
        'device': {'common_candidate_sha256': args.candidate_sha256,
                   'new_game_art_embedded_in_this_candidate': bool(integrated),
                   'integrated_game_groups': integrated,
                   'reason': 'Only explicitly integrated games are embedded; physical factory is 2,031,616 bytes.'},
        'acceptance': 'Source integrity and actual C decoder checks; visual/device checks are recorded separately in ART_PROGRESS and VALIDATION.',
    }
    target = ART / 'catalog.json'
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', 'utf-8', newline='\n')
    temporary.replace(target)
    print(json.dumps({'catalog': target.relative_to(ROOT).as_posix(), **catalog['counts'],
                      'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
