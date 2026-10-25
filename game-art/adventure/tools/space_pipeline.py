"""Rebuild only the independent SPACE art package; never touches a device."""
import argparse
import json
from space_rig import ART,build
from space_motion import clips
from space_scene import build_scene
from space_export import export
from space_preview import preview
from space_verify import verify


def main():
    p=argparse.ArgumentParser();p.add_argument('--verify-c',action='store_true');a=p.parse_args()
    rig=build();animations=clips(rig);manifest=export(animations,rig,build_scene());preview(animations);report=verify(a.verify_c)
    print(json.dumps({'manifest':str(ART/'space-manifest.json'),'clips':len(manifest['animations']),
        'frames':sum(len(e['frames']) for e in manifest['animations']),
        'production_c':report['production_c'],'groups':report['groups']},indent=2))


if __name__=='__main__':main()
