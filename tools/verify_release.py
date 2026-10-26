#!/usr/bin/env python3
"""Check every downloaded release asset, archive member, image gap and app binding."""
import argparse
import json
from pathlib import Path
import zipfile
from package_release import APP_SHA,VERSION,sha,safe_member,verify_padding

def parse_sums(raw):
    result={}
    for line in raw.decode('ascii').splitlines():
        h,name=line.split('  ',1);safe_member(name)
        if len(h)!=64 or any(c not in '0123456789abcdef' for c in h) or name in result:raise ValueError('Bad checksum manifest')
        result[name]=h
    return result

def verify(folder):
    folder=Path(folder);checks=parse_sums((folder/'SHA256SUMS.txt').read_bytes())
    expected={'nabo-adventure-v'+VERSION+s for s in ('-app.bin','-full.bin','.zip')}|{'manifest.json','INSTALL.md','VALIDATION.json'}
    if set(checks)!=expected or {p.name for p in folder.iterdir()}!=expected|{'SHA256SUMS.txt'}:
        raise ValueError('Unexpected or missing release assets')
    for name,h in checks.items():
        if sha((folder/name).read_bytes())!=h:raise ValueError('Asset mismatch: '+name)
    manifest=json.loads((folder/'manifest.json').read_text('utf-8'))
    if manifest['application']['sha256']!=APP_SHA or manifest['version']!=VERSION:raise ValueError('Wrong release binding')
    with zipfile.ZipFile(folder/manifest['archive']) as z:
        names=z.namelist()
        for n in names:safe_member(n)
        if len(names)!=len(set(names)):raise ValueError('Duplicate archive member')
        if set(names)!=set(manifest['archive_members'])|{'manifest.json','contents.sha256'}:
            raise ValueError('Archive allowlist mismatch')
        if z.read('manifest.json')!=(folder/'manifest.json').read_bytes():raise ValueError('Inner manifest differs')
        internal=parse_sums(z.read('contents.sha256'))
        if set(internal)!=set(names)-{'contents.sha256'}:raise ValueError('Incomplete archive checksums')
        for name in names:
            data=z.read(name)
            if name in internal and sha(data)!=internal[name]:raise ValueError('Inner checksum mismatch: '+name)
            if name in manifest['archive_members']:
                item=manifest['archive_members'][name]
                if len(data)!=item['bytes'] or sha(data)!=item['sha256']:raise ValueError('Archive member changed: '+name)
        for name in (manifest['application']['file'],manifest['full_install']['file'],'INSTALL.md','VALIDATION.json'):
            if z.read(name)!=(folder/name).read_bytes():raise ValueError('Inner/external asset differs: '+name)
        app=z.read(manifest['application']['file']);full=z.read(manifest['full_install']['file'])
        if sha(app)!=APP_SHA or sha(full)!=manifest['full_install']['sha256']:raise ValueError('Wrong firmware')
        verify_padding(full,[(0,z.read('bootloader.bin')),(0x8000,z.read('partition-table.bin')),(0x10000,app)])
    return {'status':'PASS: ALL ASSETS AND ZIP MEMBERS VERIFIED','assets':len(checks)+1,'members':len(names),'app_sha256':APP_SHA,'full_sha256':sha(full)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.folder),indent=2))
