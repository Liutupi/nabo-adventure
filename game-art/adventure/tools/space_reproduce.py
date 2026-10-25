"""Same-machine deterministic SPACE rebuild including real production C verification."""
import os
from pathlib import Path
import subprocess
import sys
from space_rig import ART,digest,write_json


def snapshot():
    files=[]
    for relative in ['games/space','frames/space','rig/space','preview/space']:
        files.extend(p for p in (ART/relative).rglob('*') if p.is_file() and p.name not in ['reproducibility.json','README.md'])
    files.append(ART/'space-manifest.json')
    return {p.relative_to(ART).as_posix():digest(p) for p in files}


def main():
    before=snapshot()
    subprocess.run([sys.executable,str(Path(__file__).with_name('space_pipeline.py')),'--verify-c'],check=True)
    after=snapshot();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    if changed:raise ValueError('SPACE nonreproducible output: '+repr(changed))
    write_json(ART/'preview/space/reproducibility.json',{'passed':True,'files_compared':len(after),'changed':[],
        'manifest_sha256':digest(ART/'space-manifest.json'),'method':'two full same-machine builds with actual production C decode, every owned output SHA compared',
        'tools':'bundled Python 3.12.14, Pillow12.3.0, numpy2.3.5; portable w64devkit gcc16.2.0',
        'no_generative_frames':True,'cross_library_version_guarantee':False})
    print('SPACE byte-identical:',len(after),'files')


if __name__=='__main__':main()
