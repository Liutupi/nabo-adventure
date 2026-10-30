#!/usr/bin/env python3
"""Bundle the SKI V2 G1 prototype into one self-contained page (sprites as data URIs).

Output goes to the path given (default private/ski_v2_artifact.html, not committed).
"""
import base64, json, re, sys
from pathlib import Path

ADV = Path(__file__).resolve().parents[1] / 'game-art/adventure'
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ADV.parents[1] / 'private/ski_v2_artifact.html'
html = (ADV / 'prototype/ski.html').read_text('utf-8')
manifest = json.loads((ADV / 'art/ski-manifest.json').read_text('utf-8'))
clips = [c for c in manifest['animations'] if c['skin'] == 'ski_a']
assets = manifest['assets']
paths = {p for c in clips for p in c['runtime_frames']} | {a['path'] for a in assets}
files = {p: 'data:image/png;base64,' + base64.b64encode((ADV / 'art' / p).read_bytes()).decode() for p in sorted(paths)}
slim = {'animations': [{k: c[k] for k in ('skin', 'name', 'runtime_frames', 'runtime_anchor')} for c in clips],
        'assets': [{k: a[k] for k in ('id', 'path', 'anchor') if k in a} for a in assets]}
sprites = 'window.SKI_SPRITES=' + json.dumps({'manifest': slim, 'files': files}, separators=(',', ':')) + ';'
for tag in (r'<!doctype html>\s*', r'<html[^>]*>\s*', r'</?head>\s*', r'</?body>\s*', r'</html>\s*', r'<meta charset[^>]*>\s*', r'<meta name="viewport"[^>]*>\s*'):
    html = re.sub(tag, '', html, flags=re.I)
html = html.replace('<title>', '<meta name="claude:viewport-fit-sides" content="cover">\n<title>', 1)
inline = lambda name: '<script>\n' + (ADV / 'prototype' / name).read_text('utf-8').replace('</script', '<\\/script') + '\n</script>'
html = html.replace('<script src="adv_ski.js"></script>', '<script>' + sprites + '</script>\n' + inline('adv_ski.js'))
html = html.replace('<script src="adv_ski_draw.js"></script>', inline('adv_ski_draw.js'))
html = html.replace('<script src="adv_v2_ui.js"></script>', inline('adv_v2_ui.js'))
assert 'src="adv_' not in html
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, 'utf-8'); print(out, len(html))
