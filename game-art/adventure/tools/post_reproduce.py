#!/usr/bin/env python3
"""Rebuild POST and verify every generated image/manifest by SHA256."""
import json
from pathlib import Path
import subprocess
import sys
from post_config import ART,GAME,RIG,PREVIEW
from post_rig import sha


def snapshot():
    outputs={}
    for folder in (GAME,RIG,ART/'frames/post',PREVIEW):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.suffix in ('.png','.gif','.svg','.json'):
                if path.name in ('reproducibility.json','packing-validation.json'):continue
                outputs[path.relative_to(ART).as_posix()]=sha(path)
    outputs['post-manifest.json']=sha(ART/'post-manifest.json')
    return outputs


def main():
    before=snapshot();tools=Path(__file__).parent
    for script in ('post_build.py','post_verify.py'):
        subprocess.run([sys.executable,str(tools/script)],check=True)
    after=snapshot()
    changed=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
    result=dict(passed=not changed,files_compared=len(after),changed=changed,
                source_manifest_sha256=sha(ART/'post-manifest.json'),
                method='Rebuild source-pixel bones, frozen palette exports, cab/cord native PNG/SVG and actual target compositions; compare every generated file byte-for-byte. No model rerun.',
                outputs=after)
    (PREVIEW/'reproducibility.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    assert not changed,changed
    print(json.dumps({k:v for k,v in result.items() if k!='outputs'},indent=2))


if __name__=='__main__':main()
