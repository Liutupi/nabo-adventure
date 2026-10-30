#!/usr/bin/env python3
"""Package prebuilt, SHA-bound firmware; never build, flash, or read a device."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'firmware/tools'))
from verify_firmware import (parse_flash_args,validate_flash_size,verify_flash_images,
    verify_firmware_layout,verify_extra_image_partitions)

VERSION='0.2.0'
APP_SHA='e9fe81f6cd52f194d309638305cd9e41faaf074c2c076f815578fb34981e8afc'
VALIDATION=ROOT/'validation/v2-20261030-e9fe81f6.json'
REUSED_COMPONENTS={'bootloader/bootloader.bin':'d492cb90188413bb25f6acfa1915bf3d3b2b680d4d17179c8dbf72f1aec8b7c7',
                   'partition_table/partition-table.bin':'feb7ea496adb63179bf197f87431e6c8ddade47ce0228c1e671ef01421effc0c'}

def sha(data):return hashlib.sha256(data).hexdigest()
def safe_member(name):
    p=PurePosixPath(name)
    if not name or '\\' in name or p.is_absolute() or '..' in p.parts or ':' in name:
        raise ValueError('Unsafe archive path: '+name)
    if any(part.lower() in ('private','backups','.git','nvs','credentials') for part in p.parts):
        raise ValueError('Private material in archive: '+name)
    return name

def verify_padding(merged,images):
    cursor=0
    for offset,data in sorted(images):
        if offset<cursor or merged[offset:offset+len(data)]!=data:
            raise ValueError('Overlapping or substituted image')
        if any(v!=255 for v in merged[cursor:offset]):
            raise ValueError('Non-FF image gap; possible private partition data')
        cursor=offset+len(data)
    if cursor!=len(merged):raise ValueError('Unexpected merged suffix')

def frozen_write(path,data):
    if path.exists() and path.read_bytes()!=data:raise ValueError('Refuse to replace frozen artifact: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_bytes(data)

def encode(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def sums(files):return ''.join(sha(data)+'  '+name+'\n' for name,data in sorted(files.items())).encode()

def validate_binding(app,validation):
    if sha(app)!=APP_SHA or validation['candidate_sha256']!=APP_SHA:
        raise ValueError('Hardware checkpoint binding changed')
    device=validation.get('device',{})
    if (not validation['status'].startswith('BUILD AND HOST PASS; DEVICE SERIAL AUTOMATION PASS') or
            not device.get('application_readback_verified') or not device.get('normal_mode_restored') or
            not device.get('nvs_unchanged_after_tests') or set(device.get('games',{}))!={'jump','dive','post','night','climb','ski','sky','space'}):
        raise ValueError('Missing device serial validation')

def package(build,output,idf,source):
    build=Path(build);output=Path(output);idf=Path(idf)
    if not re.fullmatch('[0-9a-f]{40}',source):raise ValueError('Exact firmware source commit required')
    app=(build/'nabo-adventure.bin').read_bytes();validation=json.loads(VALIDATION.read_text('utf-8'))
    validate_binding(app,validation)
    for name,h in REUSED_COMPONENTS.items():
        if sha((build/name).read_bytes())!=h:raise ValueError('Released v0.1.0 component changed: '+name)
    merged=(build/'nabo-adventure-merged.bin').read_bytes()
    args=(build/'flash_args').read_text('utf-8');validate_flash_size(args);offsets=parse_flash_args(args)
    expected={'bootloader/bootloader.bin':0,'partition_table/partition-table.bin':0x8000,'nabo-adventure.bin':0x10000}
    if offsets!=expected:raise ValueError('Release accepts only three build images, never device dumps')
    sizes=verify_flash_images(merged,build,offsets)
    parts=verify_firmware_layout(merged,build,0x8000,0x10000)
    verify_extra_image_partitions(offsets,sizes,parts)
    verify_padding(merged,[(offset,(build/name).read_bytes()) for name,offset in offsets.items()])
    prefix='nabo-adventure-v'+VERSION
    app_name=prefix+'-app.bin';full_name=prefix+'-full.bin';zip_name=prefix+'.zip'
    files={app_name:app,full_name:merged,'bootloader.bin':(build/'bootloader/bootloader.bin').read_bytes(),
           'partition-table.bin':(build/'partition_table/partition-table.bin').read_bytes(),
           'INSTALL.md':(ROOT/('docs/INSTALL_v'+VERSION+'.md')).read_bytes(),'VALIDATION.json':VALIDATION.read_bytes(),
           'GAME_CONTROLS.md':(ROOT/'docs/GAME_CONTROLS.md').read_bytes(),
           'tools/flash_candidate.py':(ROOT/'firmware/tools/flash_candidate.py').read_bytes(),
           'tools/verify_firmware.py':(ROOT/'firmware/tools/verify_firmware.py').read_bytes()}
    for name in ('LICENSE','LICENSE.Table','LICENSE.Jump','NOTICE.md'):files[name]=(ROOT/name).read_bytes()
    for name in ('firmware/LICENSE.FoloToy','firmware/main/OFL-SpaceMono.txt','firmware/main/OFL-SourceHanSans.txt',
                 'firmware/main/OFL-ArchivoBlack.txt','firmware/main/font-licenses/SourceHanSans-OFL.txt',
                 'firmware/main/font-licenses/NotoSansSC-Bold-OFL.txt',
                 'firmware/main/third_party/pl_mpeg/pl_mpeg.h','firmware/main/third_party/pl_mpeg/UPSTREAM.md'):
        files['licenses/'+name.removeprefix('firmware/')]=(ROOT/name).read_bytes()
    files['licenses/ESP-IDF-LICENSE']=(idf/'LICENSE').read_bytes()
    for component in sorted((ROOT/'firmware/managed_components').iterdir()):
        if not component.is_dir():continue
        found=False
        for p in sorted(component.iterdir()):
            if p.is_file() and re.match(r'(?i)^(licen[sc]e|copying|copyrights|notice)(\.[a-z0-9]+)?$',p.name):
                files['licenses/'+component.name+'/'+p.name]=p.read_bytes();found=True
        if not found:raise ValueError('Missing component license: '+component.name)
    for name in files:safe_member(name)
    manifest={'schema':'nabo-adventure-release-v1','version':VERSION,'date':'2026-10-30','prerelease':True,
      'firmware_source_commit':source,'release_ref':'v'+VERSION,'device':'FoloToy AI Passport ESP32-C3 8MB',
      'application':{'file':app_name,'bytes':len(app),'sha256':APP_SHA,'offset':'0x10000','hardware_serial_verified':True},
      'full_install':{'file':full_name,'bytes':len(merged),'sha256':sha(merged),'offset':'0x0',
                      'contains_same_application':True,'hardware_first_install_verified':False,'resets_settings_and_scores':True},
      'build_components':{name:{'offset':hex(at),'bytes':sizes[name],'sha256':sha((build/name).read_bytes())} for name,at in offsets.items()},
      'component_provenance':{'application':'exact e9fe81f6 device-tested build output; not rebuilt',
                              'bootloader_and_partition_table':'reused byte-for-byte from public v0.1.0 ZIP'},
      'archive':zip_name,'archive_members':{name:{'bytes':len(data),'sha256':sha(data)} for name,data in sorted(files.items())},
      'privacy':{'source':'prebuilt build outputs plus explicit allowlisted documents/licenses/tools',
                 'device_flash_or_nvs_included':False,'all_gaps_ff_verified':True},
      'validation':'VALIDATION.json','human_acceptance':{'status':'pending','unverified':validation['unverified']}}
    files['manifest.json']=encode(manifest);files['contents.sha256']=sums(files)
    import io
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(safe_member(name),(2026,10,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=9)
    assets={app_name:app,full_name:merged,zip_name:stream.getvalue(),
            'manifest.json':files['manifest.json'],'INSTALL.md':files['INSTALL.md'],'VALIDATION.json':files['VALIDATION.json']}
    assets['SHA256SUMS.txt']=sums(assets)
    for name,data in assets.items():frozen_write(output/name,data)
    print(json.dumps({'output':str(output),'assets':{n:len(d) for n,d in assets.items()},'app_sha256':APP_SHA},indent=2))
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,default=ROOT/'firmware/build-idf6')
    p.add_argument('--output',type=Path,default=ROOT/'release-v0.2.0');p.add_argument('--idf',type=Path,required=True)
    p.add_argument('--source-commit',required=True)
    a=p.parse_args();package(a.build,a.output,a.idf,a.source_commit)
