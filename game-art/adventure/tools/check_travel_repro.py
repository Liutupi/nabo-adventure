"""Rebuild in an isolated scratch tree so packaging can read frozen live PNGs safely."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from PIL import Image
from build_travel_rig import ART,RIG


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out=ART/'preview/travel'; compared=[];changed=[]
    with tempfile.TemporaryDirectory(prefix='repro-',dir=out) as tmp:
        scratch=Path(tmp).resolve()
        # Explicit containment check before TemporaryDirectory's recursive cleanup.
        assert scratch.parent==out.resolve() and scratch.name.startswith('repro-')
        repo=scratch/'repo';adventure=repo/'game-art/adventure';art=adventure/'art'
        shutil.copytree(ART.parent/'tools',adventure/'tools',ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(RIG/'source',art/'rig/source')
        shutil.copytree(out/'revisions',art/'preview/travel/revisions')
        (adventure/'audio').mkdir(parents=True)
        shutil.copy2(ART.parent/'audio/boot-welcome.wav',adventure/'audio/boot-welcome.wav')
        shutil.copy2(ART/'manifest.json',art/'manifest.json')
        if (ART/'shared-static-manifest.json').exists():shutil.copy2(ART/'shared-static-manifest.json',art/'shared-static-manifest.json')
        (repo/'tools').mkdir(parents=True)
        shutil.copy2(ART.parents[2]/'tools/generate_adv_sprites.py',repo/'tools/generate_adv_sprites.py')
        for script in ['render_travel.py','rig_atlas.py','verify_travel.py']:
            subprocess.run([sys.executable,str(adventure/'tools'/script)],check=True,capture_output=True)
        for p in sorted(art.rglob('*')):
            if not p.is_file() or 'source' in p.relative_to(art).parts:continue
            relative=p.relative_to(art)
            if relative.as_posix() in ['manifest.json','shared-static-manifest.json']:continue
            destination=ART/relative
            compared.append(relative.as_posix())
            if not destination.exists() or sha(p)!=sha(destination):changed.append(relative.as_posix())
        # Main manifest can carry other packages/C-build fields; validate only the
        # travel-owned runtime contract against the isolated deterministic rebuild.
        current=json.loads((ART/'manifest.json').read_text('utf-8'))
        rebuilt=json.loads((art/'manifest.json').read_text('utf-8'))
        byname={x['name']:x for x in current['animations']}
        keys=['frames','masters','frame_sha256','master_sha256','runtime_frames','runtime_sha256','runtime_anchor','runtime_canvas','fps','loop']
        for entry in rebuilt['animations']:
            for key in keys:assert entry[key]==byname[entry['name']][key],(entry['name'],key)
    gif_checks=[]
    for path in sorted(out.glob('*.gif')):
        with Image.open(path) as image:
            durations=[]
            for i in range(image.n_frames):image.seek(i);durations.append(image.info.get('duration',0))
            expected=round(image.n_frames*100/12)*10
            assert abs(sum(durations)-expected)<=10,(path.name,image.n_frames,sum(durations),expected)
            gif_checks.append({'file':path.relative_to(ART).as_posix(),'frames':image.n_frames,
                               'duration_ms':sum(durations),'loop':image.info.get('loop')})
    result={'isolation':'scratch tree under preview/travel; frozen live assets never rewritten',
            'files_compared':len(compared),'byte_identical_after_rebuild':not changed,'changed':changed,
            'runtime_contracts_match':True,'gif_checks':gif_checks,'technical_verification_passed':True,
            'not_a_human_visual_acceptance':True}
    (out/'reproducibility.json').write_text(json.dumps(result,indent=2)+'\n','utf-8')
    if changed:raise ValueError('Nonreproducible generated assets: '+', '.join(changed))
    print(json.dumps({'files_compared':len(compared),'byte_identical_after_rebuild':True,'gifs_checked':len(gif_checks)}))


if __name__=='__main__':main()
