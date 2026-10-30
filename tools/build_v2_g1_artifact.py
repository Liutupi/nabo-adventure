#!/usr/bin/env python3
"""Bundle the SKY / CLIMB / POST V2 G1 prototype into one self-contained page (sprites as data URIs).

Usage: python3 tools/build_v2_g1_artifact.py sky|climb|post [out.html]
Default output private/<game>_v2_artifact.html (not committed).
"""
import base64, json, re, sys
from pathlib import Path

ADV = Path(__file__).resolve().parents[1] / 'game-art/adventure'
GAMES = {
    'sky': dict(html='sky_v2.html', manifest='sky-manifest.json', var='SKY_SPRITES', skin='sky_a', extra_clips={'bird'},
                scripts=['adv_sky_v2.js', 'adv_sky_v2_draw.js'],
                extra=['space-v2/bg-cloud-far.png', 'space-v2/bg-cirrus.png', 'space-v2/bg-cloud-a.png', 'space-v2/bg-cloud-b.png', 'space-v2/bg-launch-far.png']),
    'post': dict(html='post_v2.html', manifest='post-manifest.json', var='POST_SPRITES', skin='post_a', extra_clips=set(), extra_skins={'post_props'},
                 scripts=['adv_post_v2.js', 'adv_post_v2_draw.js'], extra=['space-v2/bg-cloud-far.png', 'space-v2/bg-cirrus.png']),
    'climb': dict(html='climb_v2.html', manifest='climb-manifest.json', var='CLIMB_SPRITES', skin='climb_a', extra_clips=set(),
                  scripts=['adv_climb_v2.js', 'adv_climb_v2_draw.js'],
                  extra=['space-v2/bg-cloud-far.png', 'space-v2/bg-cirrus.png']),
}
game = sys.argv[1] if len(sys.argv) > 1 else 'sky'
cfg = GAMES[game]
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ADV.parents[1] / f'private/{game}_v2_artifact.html'
html = (ADV / 'prototype' / cfg['html']).read_text('utf-8')
manifest = json.loads((ADV / 'art' / cfg['manifest']).read_text('utf-8'))
clips = [c for c in manifest['animations'] if c.get('skin') == cfg['skin'] or c.get('skin') in cfg.get('extra_skins', ()) or c['name'] in cfg['extra_clips']]
assets = manifest['assets']
frames = lambda c: c.get('runtime_frames') or c['frames']
paths = {p for c in clips for p in frames(c)} | {a['path'] for a in assets} | set(cfg['extra'])
files = {p: 'data:image/png;base64,' + base64.b64encode((ADV / 'art' / p).read_bytes()).decode() for p in sorted(paths)}
slim = {'animations': [{k: c[k] for k in ('skin', 'name', 'runtime_frames', 'runtime_anchor', 'frames') if k in c} for c in clips],
        'assets': [{k: a[k] for k in ('id', 'path', 'anchor') if k in a} for a in assets]}
sprites = f'window.{cfg["var"]}=' + json.dumps({'manifest': slim, 'files': files}, separators=(',', ':')) + ';'
for tag in (r'<!doctype html>\s*', r'<html[^>]*>\s*', r'</?head>\s*', r'</?body>\s*', r'</html>\s*', r'<meta charset[^>]*>\s*', r'<meta name="viewport"[^>]*>\s*'):
    html = re.sub(tag, '', html, flags=re.I)
html = html.replace('<title>', '<meta name="claude:viewport-fit-sides" content="cover">\n<title>', 1)
inline = lambda name: '<script>\n' + (ADV / 'prototype' / name).read_text('utf-8').replace('</script', '<\\/script') + '\n</script>'
rules, draw = cfg['scripts']
html = html.replace(f'<script src="{rules}"></script>', '<script>' + sprites + '</script>\n' + inline(rules))
html = html.replace(f'<script src="{draw}"></script>', inline(draw))
html = html.replace('<script src="adv_v2_ui.js"></script>', inline('adv_v2_ui.js'))
assert 'src="adv_' not in html
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, 'utf-8'); print(out, len(html))
