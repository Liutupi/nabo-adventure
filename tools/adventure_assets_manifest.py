"""Strict readers for the three explicit adventure-art runtime manifests."""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from PIL import Image

GAME_GROUPS = ('post', 'night', 'climb', 'ski', 'sky', 'space')


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def data_of(image):
    return image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata()


@dataclass
class Resource:
    id: str
    group: str
    paths: list
    hashes: list
    size: tuple
    anchor: tuple = (0, 0)
    offset: tuple = (0, 0)
    fps: int = 0
    loop: bool = False
    color_limit: int = 64
    palette_group: str = ''
    startup: bool = False
    presentation_bytes: int = 0
    images: list = field(default_factory=list)

    @property
    def symbol(self): return 'adv_assets_' + re.sub('[^A-Za-z0-9_]', '_', self.id)


def scoped(base, relative):
    path = Path(relative)
    if path.is_absolute(): raise ValueError('Manifest paths must be relative')
    resolved = (base / path).resolve()
    if not resolved.is_relative_to(base.resolve()): raise ValueError('Manifest path escapes its source directory')
    if not resolved.is_file(): raise ValueError(f'Missing declared source: {resolved}')
    return resolved


def pair(value, field_name, *, positive=False):
    if not isinstance(value, list) or len(value) != 2 or any(type(v) is not int for v in value):
        raise ValueError(f'{field_name} must explicitly contain two integers')
    if positive and any(v <= 0 for v in value): raise ValueError(f'{field_name} must be positive')
    return tuple(value)


def validate(resource):
    resource.images.clear()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_/-]*', resource.id): raise ValueError('Invalid stable resource id')
    if not resource.paths or len(resource.paths) != len(resource.hashes): raise ValueError('Explicit source/hash counts differ')
    if any(not 1 <= v <= 65535 for v in resource.size): raise ValueError('Canvas exceeds the C catalog size range')
    if len(resource.paths) > 65535 or resource.size[0]*resource.size[1]*len(resource.paths) > 16*1024*1024:
        raise ValueError('Resource exceeds the codec frame/pixel budget')
    if type(resource.color_limit) is not int or not 1 <= resource.color_limit <= 64: raise ValueError('Invalid color_limit')
    visible, transparent = set(), False
    for path, expected in zip(resource.paths, resource.hashes):
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected) or digest(path) != expected:
            raise ValueError(f'SHA256 mismatch: {path}')
        with Image.open(path) as source: bitmap = source.convert('RGBA')
        if bitmap.size != resource.size: raise ValueError(f'Target canvas mismatch: {path}')
        for r, g, b, a in data_of(bitmap):
            if a not in (0, 255): raise ValueError(f'Nonbinary alpha: {path}')
            if a: visible.add((r, g, b))
            else: transparent = True
        resource.images.append(bitmap)
    if len(visible)+int(transparent) > resource.color_limit:
        raise ValueError(f'{resource.id}: original shared palette exceeds color_limit {resource.color_limit}')
    if len(visible) > 63:
        raise ValueError(f'{resource.id}: codec reserves index zero, so at most 63 visible colors are allowed')
    if any(not -32768 <= v <= 32767 for v in (*resource.anchor, *resource.offset)):
        raise ValueError('Anchor/offset exceeds the C catalog range')
    if any(resource.offset[i] + ((resource.size[i]-1)//256)*256 > 32767 for i in (0, 1)):
        raise ValueError('Fragment offset exceeds the C catalog range')
    return visible


def load_resources(art, groups, include_b_skins=False):
    art = Path(art).resolve()
    resources, manifests, ui = [], {}, None
    for group in groups:
        relative = f'{group}-manifest.json' if group in GAME_GROUPS else {
            'travel': 'manifest.json', 'ui': 'ui/ui-manifest.json', 'static': 'shared-static-manifest.json'}[group]
        path = scoped(art, relative)
        manifest = json.loads(path.read_text('utf-8'))
        manifests[relative] = digest(path)
        if group == 'travel' or group in GAME_GROUPS:
            for animation in manifest['animations']:
                # Second (silver) skins stay in the repo but are packed only once their switch exists.
                if group in GAME_GROUPS and not include_b_skins and str(animation['skin']).endswith('_b'):
                    continue
                # Deliberately no fallback to 256px delivery/masters or guessed paths.
                paths = [scoped(art, p) for p in animation['runtime_frames']]
                size = pair(animation['runtime_canvas'], 'runtime_canvas', positive=True)
                anchor = pair(animation['runtime_anchor'], 'runtime_anchor')
                if any(not 0 <= v <= size[i] for i, v in enumerate(anchor)): raise ValueError('Anchor outside runtime canvas')
                fps, loop = animation['fps'], animation['loop']
                if type(fps) is not int or not 1 <= fps <= 120 or type(loop) is not bool:
                    raise ValueError('Invalid explicit animation fps/loop')
                startup = animation.get('startup', group == 'travel' and animation['name'] in ('welcome', 'welcome_v2'))
                if type(startup) is not bool: raise ValueError('startup role must be boolean')
                resources.append(Resource(f'{animation["skin"]}/{animation["name"]}', group, paths,
                                          animation['runtime_sha256'], size, anchor, fps=fps, loop=loop, startup=startup))
            if group in GAME_GROUPS:
                for entry in manifest.get('assets', []):
                    resources.append(Resource('game/'+entry['id'], group, [scoped(art, entry['path'])], [entry['sha256']],
                                              pair(entry['size'], 'game static size', positive=True),
                                              pair(entry['anchor'], 'game static anchor'), color_limit=entry['color_limit']))
            if group == 'space' and (art/'space-v2-manifest.json').is_file():
                extra_path=scoped(art,'space-v2-manifest.json')
                extra=json.loads(extra_path.read_text('utf-8'))
                if extra.get('schema')!='space-v2-painted-v1':raise ValueError('Unsupported SPACE V2 painted manifest')
                manifests['space-v2-manifest.json']=digest(extra_path)
                for entry in extra['assets']:
                    resources.append(Resource('game/'+entry['id'],group,[scoped(art,entry['path'])],[entry['sha256']],
                                              pair(entry['size'],'SPACE V2 size',positive=True),
                                              pair(entry['anchor'],'SPACE V2 anchor'),color_limit=entry['color_limit']))
        elif group == 'ui':
            ui = manifest
            for entry in manifest['assets']:
                if type(entry.get('pack')) is not bool: raise ValueError('UI asset requires an explicit pack boolean')
                if not entry['pack']: continue
                resource_id = 'ui/' + Path(entry['path']).with_suffix('').as_posix()
                resources.append(Resource(resource_id, group, [scoped(art / 'ui', entry['path'])], [entry['sha256']],
                                          pair(entry['size'], 'UI size', positive=True),
                                          pair(entry.get('anchor', [0, 0]), 'UI anchor'),
                                          pair(entry.get('draw_offset', [0, 0]), 'UI draw_offset'),
                                          color_limit=entry['color_limit'], palette_group=entry['palette_group']))
        else:
            for entry in manifest['assets']:
                resources.append(Resource('static/'+entry['id'], group, [scoped(art, entry['path'])], [entry['sha256']],
                                          pair(entry['size'], 'static size', positive=True),
                                          pair(entry['anchor'], 'static anchor'), color_limit=entry['color_limit']))
    if 'travel' in groups:
        from generate_boot_presentation import read_presentation
        from generate_boot_video import read_video
        selected = read_presentation(art)
        video=read_video(art)
        if selected or video:
            previous = [r for r in resources if r.group == 'travel' and r.startup and
                        r.id.rsplit('/', 1)[-1] in ('welcome', 'welcome_v2')]
            if len(previous) != 1: raise ValueError('Boot selection requires exactly one old startup welcome')
            resources.remove(previous[0])
            if selected:resources.append(selected.resource)
            manifests.update(selected.dependencies if selected else video['dependencies'])
        if video:
            obsolete={'ui/cover-background-top','ui/cover-background-bottom','ui/wordmarks/collection','ui/labels/boot-caption','ui/labels/press-start'}
            resources=[r for r in resources if r.id not in obsolete]
    ids, symbols, shared = set(), set(), set()
    for resource in resources:
        if resource.id in ids or resource.symbol in symbols: raise ValueError('Duplicate id or C symbol collision')
        ids.add(resource.id); symbols.add(resource.symbol)
        visible = validate(resource)
        if resource.group == 'ui' and resource.palette_group == 'shared': shared |= visible
    if len(shared)+1 > 32: raise ValueError('Combined shared UI palette exceeds 32 including transparency')
    if ui:
        for patch in ui['nine_slice']:
            if patch['family'] not in ('menu', 'info', 'popup') or not re.fullmatch('[a-z][a-z0-9_]*', patch['state']):
                raise ValueError('Invalid nine-slice family/state identifier')
            if patch['corner_px'] != (16 if patch['family'] == 'popup' else 12):
                raise ValueError('Nine-slice corner contract differs')
        for height, glyphs in ui['digit_metrics'].items():
            if height not in ('20', '36'): raise ValueError('Unsupported digit height contract')
            for glyph, metric in glyphs.items():
                if glyph not in tuple('0123456789m+') or type(metric['advance']) is not int or not 1 <= metric['advance'] <= 65535:
                    raise ValueError('Invalid digit metric')
        palette_path = scoped(art/'ui', ui['shared_ui_palette']['path'])
        declared = json.loads(palette_path.read_text('utf-8'))
        declared_colors = {tuple(bytes.fromhex(value.lstrip('#'))) for value in declared.values()}
        if len(declared_colors)+1 > 32 or not shared <= declared_colors: raise ValueError('Shared UI pixels differ from declared palette')
        manifests['ui/'+ui['shared_ui_palette']['path']] = digest(palette_path)
        ui = {**ui, 'palette_values': declared}
    return sorted(resources, key=lambda r: r.id), manifests, ui


def verify_sources_unchanged(art, resources, manifests):
    for resource in resources:
        for path, expected in zip(resource.paths, resource.hashes):
            if digest(path) != expected: raise ValueError(f'Source changed during packing: {path}')
    for relative, expected in manifests.items():
        if digest(Path(art)/relative) != expected: raise ValueError(f'Manifest changed during packing: {relative}')
