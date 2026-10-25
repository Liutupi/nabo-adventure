"""Rebuild SKY in its owned directories and compare every deterministic output hash."""
import subprocess
import sys
from pathlib import Path
from sky_config import ART,PREVIEW
from sky_rig import sha,dump


def snapshot():
    paths=[]
    for relative in ['games/sky','rig/sky','frames/sky']:
        paths.extend(p for p in (ART/relative).rglob('*') if p.is_file())
    paths.extend(PREVIEW.glob('*.png'));paths.extend(PREVIEW.glob('*.gif'))
    paths.extend([PREVIEW/'motion-quality.json',ART/'sky-manifest.json'])
    return {p.relative_to(ART).as_posix():sha(p) for p in paths if p.name!='all-actions-overview.png'}


def main():
    before=snapshot();subprocess.run([sys.executable,str(Path(__file__).with_name('sky_pipeline.py'))],check=True)
    after=snapshot();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    assert not changed,changed
    dump(PREVIEW/'reproducibility.json',{'passed':True,'files_compared':len(after),'changed':[],
        'source_manifest_sha256':sha(ART/'sky-manifest.json'),'method':'two deterministic complete builds, every owned output SHA compared',
        'scope':'same-machine bundled Python/Pillow/numpy; not a cross-library-version guarantee',
        'no_generative_frames':True})
    print('SKY byte-identical:',len(after),'files')


if __name__=='__main__':main()
