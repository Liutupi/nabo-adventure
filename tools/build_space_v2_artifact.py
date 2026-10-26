#!/usr/bin/env python3
"""Bundle the SPACE V2「火箭登月」G1 prototype into one self-contained page (painted layers + space art as data URIs).

Output goes to the path given (default private/space_v2_artifact.html, not committed).
"""
import base64, json, re, sys
from pathlib import Path

ADV = Path(__file__).resolve().parents[1] / 'game-art/adventure'
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ADV.parents[1] / 'private/space_v2_artifact.html'
html = (ADV / 'prototype/space_v2.html').read_text('utf-8')
painted = json.loads((ADV / 'art/space-v2-manifest.json').read_text('utf-8'))
space = json.loads((ADV / 'art/space-manifest.json').read_text('utf-8'))
clips = [c for c in space['animations'] if c['skin'] == 'space_a']
slim_space = {'animations': [{k: c[k] for k in ('skin', 'name', 'runtime_frames', 'runtime_anchor')} for c in clips],
              'assets': [{k: a[k] for k in ('id', 'path', 'anchor') if k in a} for a in space['assets']]}
paths = {p for c in clips for p in c['runtime_frames']} | {a['path'] for a in space['assets']} | {a['path'] for a in painted['assets']}
files = {p: 'data:image/png;base64,' + base64.b64encode((ADV / 'art' / p).read_bytes()).decode() for p in sorted(paths)}
sprites = 'window.SPACE_V2_SPRITES=' + json.dumps({'painted': painted, 'space': slim_space, 'files': files}, separators=(',', ':')) + ';'
for tag in (r'<!doctype html>\s*', r'<html[^>]*>\s*', r'</?head>\s*', r'</?body>\s*', r'</html>\s*', r'<meta charset[^>]*>\s*', r'<meta name="viewport"[^>]*>\s*'):
    html = re.sub(tag, '', html, flags=re.I)
html = html.replace('<title>', '<meta name="claude:viewport-fit-sides" content="cover">\n<title>', 1)
inline = lambda name: '<script>\n' + (ADV / 'prototype' / name).read_text('utf-8').replace('</script', '<\\/script') + '\n</script>'
html = html.replace('<script src="adv_space.js"></script>', '<script>' + sprites + '</script>\n' + inline('adv_space.js'))
html = html.replace('<script src="adv_space_v2_draw.js"></script>', inline('adv_space_v2_draw.js'))
assert 'src="adv_' not in html
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, 'utf-8'); print(out, len(html))
