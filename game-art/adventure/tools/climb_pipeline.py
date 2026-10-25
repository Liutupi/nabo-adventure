"""Rebuild CLIMB art only. Does not touch firmware, shared originals or device."""
import argparse
import json
from climb_rig import build, ART
from climb_motion import clips
from climb_scene import build_scene
from climb_export import export
from climb_preview import preview
from climb_verify import verify


def main():
    p=argparse.ArgumentParser();p.add_argument('--verify-c',action='store_true');args=p.parse_args()
    rig=build();animations=clips(rig);assets=build_scene()
    manifest=export(animations,rig,assets);preview(animations);report=verify(animations,args.verify_c)
    print(json.dumps({'manifest':str(ART/'climb-manifest.json'),'clips':len(manifest['animations']),
                      'frames':sum(len(e['frames']) for e in manifest['animations']),
                      'production_c':report['production_c'],'budgets':report['groups']},indent=2))


if __name__=='__main__':main()
