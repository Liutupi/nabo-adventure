#!/usr/bin/env python3
"""Validate an explicit boot selection/timeline and emit immutable C pose data."""
import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import wave
from adventure_assets_manifest import Resource, digest, pair, scoped, validate

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_ART=ROOT/'game-art/adventure/art'
DEFAULT_OUTPUT=ROOT/'firmware/main/generated/adv_boot_presentation.h'
VOICE_SHA256='38b4eb8435d6a7915d17af2083a696acfa2660244be1bf7e65dc78251f0c468b'


@dataclass
class Presentation:
    resource: Resource
    dependencies: dict
    starts: list
    frames: list
    duration_ms: int
    voice_start_ms: int
    voice_end_us: int

    @property
    def table_bytes(self): return len(self.starts)*4+16


def integer(value, maximum, label, minimum=0):
    if type(value) is not int or not minimum<=value<=maximum:
        raise ValueError(f'{label} must be an integer in {minimum}..{maximum}')
    return value


def microseconds(value, label):
    if type(value) not in (int,float): raise ValueError(f'{label} must be numeric milliseconds')
    try: scaled=Decimal(str(value))*1000
    except InvalidOperation as error: raise ValueError(f'Invalid {label}') from error
    if not scaled.is_finite() or scaled!=scaled.to_integral_value(): raise ValueError(f'Invalid {label} precision')
    return integer(int(scaled),0xffffffff,label)


def voice_contract(art, manifest, timeline, total):
    voice=manifest['voice'];path=scoped(art.parent,voice['path'])
    canonical=scoped(art.parent,'audio/boot-welcome.wav')
    if path!=canonical or voice['sha256']!=VOICE_SHA256 or digest(path)!=VOICE_SHA256:
        raise ValueError('Boot voice path/SHA differs from the unchanged narration')
    with wave.open(str(path),'rb') as wav:
        if (wav.getnchannels(),wav.getframerate(),wav.getsampwidth(),wav.getcomptype())!=(1,16000,2,'NONE'):
            raise ValueError('Boot voice requires mono16k PCM16 WAV')
        count=wav.getnframes();pcm=wav.readframes(count)
        if not count or len(pcm)!=count*2 or count*1000000%16000:
            raise ValueError('Boot voice sample count/duration is invalid')
    duration=count*1000000//16000
    source=(ROOT/'firmware/main/adv_boot.h').read_text('utf-8')
    match=re.search(r'#define\s+ADV_BOOT_DELAY_MS\s+(\d+)u?\b',source)
    if not match: raise ValueError('Cannot verify ADV_BOOT_DELAY_MS from the production header')
    delay=int(match[1])
    start=integer(timeline['voice_start_ms'],65535,'voice_start_ms')
    end=microseconds(timeline['voice_end_ms'],'voice_end_ms')
    if start!=delay or end!=start*1000+duration or end>total*1000:
        raise ValueError('Voice timing differs from ADV_BOOT_DELAY_MS or actual sample duration')
    if 'voice_duration_ms' in timeline and microseconds(timeline['voice_duration_ms'],'voice_duration_ms')!=duration:
        raise ValueError('Voice duration differs from actual WAV samples')
    return start,end,path


def selected_path(art, explicit):
    if explicit is None:
        selection=art/'boot/selection.json'
        if not selection.exists() and not selection.is_symlink(): return None,{},None
        # scoped also rejects symlinks escaping ART, even at the fixed location.
        selection=scoped(art,'boot/selection.json');value=json.loads(selection.read_text('utf-8'))
        if not isinstance(value,dict) or type(value.get('version')) is not int or value['version']!=1:
            raise ValueError('Unsupported boot selection version')
        if not isinstance(value.get('manifest'),str) or not value['manifest']:
            raise ValueError('Boot selection requires a relative manifest path')
        path=scoped(art,value['manifest']);expected=value['sha256']
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected) or digest(path)!=expected:
            raise ValueError('Selected boot manifest SHA256 mismatch')
        return path,{'boot/selection.json':digest(selection)},value.get('storage_order')
    path=Path(explicit)
    if path.is_absolute() or path.is_file():
        path=path.resolve()
        if not path.is_relative_to(art): raise ValueError('Explicit boot manifest escapes ART')
        path=scoped(art,path.relative_to(art))
    else: path=scoped(art,explicit)
    return path,{},None


def read_presentation(art=DEFAULT_ART, manifest=None):
    art=Path(art).resolve();path,dependencies,storage_order=selected_path(art,manifest)
    if path is None:return None
    dependencies[path.relative_to(art).as_posix()]=digest(path)
    value=json.loads(path.read_text('utf-8'))
    if value.get('schema')=='adventure-boot-mpeg1-ip-v1':
        from generate_boot_video import read_video
        if manifest is not None:raise ValueError('Video candidates use their separate generator')
        if read_video(art) is None:raise ValueError('Video requires explicit codec selection')
        return None
    animations=value['animations']
    if not isinstance(animations,list) or len(animations)!=1: raise ValueError('Boot manifest requires exactly one actor')
    entry=animations[0];fps=integer(entry['fps'],120,'fps',1)
    if entry['loop'] is not False: raise ValueError('Boot presentation must be nonlooping')
    size=pair(entry['runtime_canvas'],'runtime_canvas',positive=True);anchor=pair(entry['runtime_anchor'],'runtime_anchor')
    if any(not 0<=v<=size[i] for i,v in enumerate(anchor)): raise ValueError('Boot anchor outside runtime canvas')
    paths=[scoped(art,p) for p in entry['runtime_frames']]
    if not 1<=len(paths)<=256: raise ValueError('Boot storage frame count exceeds uint8 frame index')
    resource=Resource(f'{entry["skin"]}/{entry["name"]}','travel',paths,entry['runtime_sha256'],size,anchor,
                      fps=fps,loop=False,startup=True)
    validate(resource)
    timeline=value['timeline']
    if not isinstance(timeline,dict): raise ValueError('Boot timeline must be an object')
    for presentation in (value.get('presentation'),entry.get('presentation')):
        if presentation and presentation.get('timeline')!=timeline:
            raise ValueError('Duplicate boot timeline declarations disagree')
    starts=timeline['pose_start_ms'];frames=timeline['pose_frame_indices']
    if not isinstance(starts,list) or not isinstance(frames,list) or not 1<=len(starts)<=65535 or len(starts)!=len(frames):
        raise ValueError('Boot event/frame counts differ or exceed uint16')
    for at in starts:integer(at,65535,'pose_start_ms')
    for frame in frames:integer(frame,min(255,len(paths)-1),'pose_frame_indices')
    if starts[0]!=0 or any(b<=a for a,b in zip(starts,starts[1:])):
        raise ValueError('Boot event times must start at zero and strictly increase')
    total=integer(timeline['total_duration_ms'],65535,'total_duration_ms',1)
    if starts[-1]>=total or frames[0]!=0 or frames[-1]!=0:
        raise ValueError('Boot must finish with a positive held neutral frame0 interval')
    if 'duration_ms' in timeline:
        durations=timeline['duration_ms']
        if (not isinstance(durations,list) or any(type(d) is not int or d<=0 for d in durations) or
                durations!=[b-a for a,b in zip(starts,[*starts[1:],total])]):
            raise ValueError('Boot per-pose durations disagree with event boundaries')
    for key,expected in (('unique_frame_count',len(paths)),('logical_pose_count',len(starts))):
        if key in timeline and (type(timeline[key]) is not int or timeline[key]!=expected):
            raise ValueError(f'Boot {key} disagrees')
    start,end,voice=voice_contract(art,value,timeline,total)
    dependencies['../'+voice.relative_to(art.parent).as_posix()]=digest(voice)
    resource.presentation_bytes=len(starts)*4+16
    # Physical storage may follow similar poses for lossless delta compression.
    # The logical exposure order/timing is preserved through an inverse mapping.
    if storage_order is not None:
        count=len(paths)
        if (not isinstance(storage_order,list) or len(storage_order)!=count or
                any(type(index) is not int for index in storage_order) or
                set(storage_order)!=set(range(count)) or storage_order[0]!=0):
            raise ValueError('Boot storage_order must be a permutation with neutral frame0 first')
        inverse={old:new for new,old in enumerate(storage_order)}
        resource.paths=[paths[index] for index in storage_order]
        resource.hashes=[resource.hashes[index] for index in storage_order]
        resource.images=[resource.images[index] for index in storage_order]
        frames=[inverse[index] for index in frames]
    result=Presentation(resource,dependencies,starts,frames,total,start,end)
    verify_presentation_sources(art,result)
    return result


def verify_presentation_sources(art, presentation):
    for relative,expected in presentation.dependencies.items():
        if digest(art/relative)!=expected: raise ValueError('Boot selection/manifest/voice changed during validation')
    for path,expected in zip(presentation.resource.paths,presentation.resource.hashes):
        if digest(path)!=expected: raise ValueError('Boot frame changed during validation')


def generate(art=DEFAULT_ART, output=DEFAULT_OUTPUT, manifest=None):
    art=Path(art).resolve();output=Path(output).resolve()
    if manifest is not None and output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'private'):
        raise ValueError('Explicit candidate header requires a private --output; production activation requires selection')
    p=read_presentation(art,manifest);selected=p is not None
    starts,frames=(p.starts,p.frames) if p else ([0],[0])
    resource=p.resource if p else None
    rows=['// Generated by tools/generate_boot_presentation.py; do not edit.','#pragma once',
          '#include <stdint.h>','#include "adv_boot.h"',
          f'#define ADV_BOOT_PRESENTATION_SELECTED {int(selected)}u',
          '#define ADV_BOOT_PRESENTATION_ASSET_ID '+(json.dumps(resource.id) if p else '((const char *)0)'),
          f'#define ADV_BOOT_PRESENTATION_FRAME_COUNT {len(resource.paths) if p else 0}u',
          f'#define ADV_BOOT_PRESENTATION_TABLE_BYTES {p.table_bytes if p else 0}u',
          'typedef struct { uint16_t at_ms; uint8_t frame, reserved; } adv_boot_pose_t;',
          'typedef struct { uint32_t duration_ms, voice_start_ms, voice_end_us; uint16_t poses, fps; } adv_boot_presentation_meta_t;',
          '_Static_assert(sizeof(adv_boot_pose_t)==4,"boot pose size");',
          '_Static_assert(sizeof(adv_boot_presentation_meta_t)==16,"boot metadata size");',
          f'_Static_assert(ADV_BOOT_DELAY_MS=={p.voice_start_ms if p else 1400}u,"voice delay changed; regenerate presentation");',
          'static const adv_boot_pose_t adv_boot_poses[] = {']
    rows += [f'    {{{at}, {frame}, 0}},' for at,frame in zip(starts,frames)]
    rows += ['};','static const adv_boot_presentation_meta_t adv_boot_presentation_meta = {'+
             f'{p.duration_ms if p else 0}u, {p.voice_start_ms if p else 1400}u, {p.voice_end_us if p else 0}u, '
             f'{len(p.starts) if p else 0}u, {resource.fps if p else 0}u'+'};']
    if p:rows.append('_Static_assert(sizeof(adv_boot_poses)+sizeof(adv_boot_presentation_meta)==ADV_BOOT_PRESENTATION_TABLE_BYTES,"boot table budget mismatch");')
    if p:
        rows += ['// Source SHA256 '+relative+' '+sha for relative,sha in sorted(p.dependencies.items())]
        verify_presentation_sources(art,p)
    output.parent.mkdir(parents=True,exist_ok=True);temporary=output.with_suffix('.h.tmp')
    temporary.write_text('\n'.join(rows)+'\n','utf-8',newline='\n');temporary.replace(output)
    return {'enabled':selected,'asset_id':resource.id if p else None,'events':len(p.starts) if p else 0,
            'table_bytes':p.table_bytes if p else 0,'dependencies':p.dependencies if p else {},'header':str(output)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--art',type=Path,default=DEFAULT_ART)
    parser.add_argument('--manifest',help='Candidate relative to ART or an existing path within ART')
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT);args=parser.parse_args()
    try:report=generate(args.art,args.output,args.manifest)
    except (ValueError,KeyError,OSError,wave.Error) as error:parser.error(str(error))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
