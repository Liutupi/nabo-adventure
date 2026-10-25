"""Full owned SKI rebuild + source/pose review + real production C verification."""
import json
from pathlib import Path
import subprocess
import sys
from ski_config import ART,PREVIEW,ROOT
from ski_rig import sha


def main():
    here=Path(__file__).parent
    for script in ['ski_build.py','ski_verify.py','ski_fall_preview.py','ski_fall_review.py']:
        subprocess.run([sys.executable,str(here/script)],check=True)
    sys.path.insert(0,str(ROOT/'tools'))
    from build_adventure_assets import build
    report=build(ART,ROOT/'private/game-art-c/ski',['ski'],True)
    summary={'passed':True,'source_manifest_sha256':sha(ART/'ski-manifest.json'),'groups':report['groups'],
        'python_verified_frames':report['python_verified_frames'],'production_c':report['production_c'],
        'source_manifest_binding':report['source_manifests_sha256'],
        'command':'CC=D:/nabo-passport-tools/w64devkit/bin/gcc.exe; python game-art/adventure/tools/ski_pipeline.py',
        'acceptance':'host art/production decoder only, gameplay and actual device acceptance not claimed',
        'final_ELF':'RLE and tables exact; C3 descriptors estimated, linker alignment not measured'}
    (PREVIEW/'packing-validation.json').write_text(json.dumps(summary,indent=2)+'\n','utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
