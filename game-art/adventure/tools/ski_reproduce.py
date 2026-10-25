"""Repeat the complete SKI pipeline and require byte-identical output SHA records."""
from pathlib import Path
import json
import subprocess
import sys
from ski_config import ART,PREVIEW
from ski_rig import sha


def snapshot():
    paths=[]
    for relative in ['games/ski','rig/ski','frames/ski','preview/ski']:
        paths.extend(p for p in (ART/relative).rglob('*') if p.is_file() and p.name not in ['reproducibility.json','README.md','QA.md'])
    paths.append(ART/'ski-manifest.json')
    return {p.relative_to(ART).as_posix():sha(p) for p in paths}


def main():
    before=snapshot();subprocess.run([sys.executable,str(Path(__file__).with_name('ski_pipeline.py'))],check=True)
    after=snapshot();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    assert not changed,changed
    (PREVIEW/'reproducibility.json').write_text(json.dumps({'passed':True,'files_compared':len(after),'changed':[],
        'manifest_sha256':sha(ART/'ski-manifest.json'),'method':'two complete deterministic builds including production C frame/row comparison',
        'tools':'bundled Python3.12.14/Pillow12.3.0/numpy2.3.5 and portable w64devkit gcc16.2.0',
        'cross_library_version_guarantee':False,'new_imagegen_frames':0},indent=2)+'\n','utf-8')
    print('SKI byte-identical:',len(after),'files')


if __name__=='__main__':main()
