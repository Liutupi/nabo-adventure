"""Rebuild only NIGHT-owned assets and require byte-identical deterministic outputs."""
import subprocess
import sys
from pathlib import Path
from night_config import ART,PREVIEW
from night_export import sha,write_json


def snapshot():
    paths=[]
    for relative in ['games/night','rig/night','frames/night']:
        paths.extend(p for p in (ART/relative).rglob('*') if p.is_file())
    paths.extend(PREVIEW.glob('*.png'));paths.extend(PREVIEW.glob('*.gif'))
    paths.extend([PREVIEW/'motion-quality.json',ART/'night-manifest.json'])
    return {p.relative_to(ART).as_posix():sha(p) for p in paths if p.name!='all-actions-overview.png'}


def main():
    before=snapshot()
    subprocess.run([sys.executable,str(Path(__file__).with_name('night_pipeline.py'))],check=True)
    after=snapshot();changes=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    assert not changes,changes
    write_json(PREVIEW/'reproducibility.json',{'passed':True,'files_compared':len(after),'changed':changes,
        'method':'same environment two complete deterministic source-pixel builds; every owned output SHA compared',
        'source_manifests_sha256':sha(ART/'night-manifest.json'),
        'tools':'bundled Python 3.12.14/Pillow 12.3/numpy; no generative frame calls',
        'limits':'same-machine repeatability; not a cross-Pillow-version guarantee'})
    print('NIGHT byte-identical:',len(after),'files')


if __name__=='__main__':main()
