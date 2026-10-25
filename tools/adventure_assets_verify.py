"""Compile generated assets with the production sprite and ninepatch decoders."""
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import _ctypes

ROOT = Path(__file__).resolve().parents[1]


def verify_c(resources, pieces, catalog, folder):
    cc = os.environ.get('CC') or shutil.which('gcc')
    if not cc: raise ValueError('--verify-c requires a host C compiler (set CC)')
    patch_names = [patch['name'] for patch in catalog['patches']]
    harness = ['#include "adv_assets_catalog.h"',
               'static const adv_ninepatch_t *patches[] = {'+', '.join('&'+p for p in patch_names or [])+('NULL' if not patch_names else '')+'};',
               f'size_t host_patch_count(void) {{ return {len(patch_names)}; }}',
               'size_t host_asset_count(void) { return adv_assets_catalog_count; }',
               'int host_row(size_t i,size_t p,unsigned f,unsigned y,uint8_t *out,size_t n) {',
               ' if(i>=adv_assets_catalog_count || p>=adv_assets_catalog[i].piece_count) return 0;',
               ' return adv_sprite_row(adv_assets_catalog[i].pieces[p].sprite,f,y,out,n); }',
               'int host_patch_valid(size_t i) { return i<host_patch_count() && adv_ninepatch_valid(patches[i]); }',
               'int host_patch_row(size_t i,unsigned w,unsigned h,unsigned y,uint16_t *out) {',
               ' return i<host_patch_count() && adv_ninepatch_row(patches[i],w,h,y,0,w,out); }']
    source = folder/'_verify_host.c'; source.write_text('\n'.join(harness)+'\n', 'utf-8')
    library = folder/'_verify_assets.dll'
    args = ['-std=c11', '-O2', '-shared', '-Wall', '-Wextra', '-Werror',
            '-Wl,--export-all-symbols' if os.name == 'nt' else '-fPIC',
            '-I', str(ROOT/'firmware/main'), '-I', str(folder),
            *[str(p) for p in sorted(folder.glob('adv_assets_*.c'))], str(source),
            str(ROOT/'firmware/main/adv_sprite.c'), str(ROOT/'firmware/main/adv_ninepatch.c'), '-o', str(library)]
    # Response files keep Windows command lengths bounded and preserve spaceful paths.
    response = folder/'_verify.rsp'
    response.write_text('\n'.join('"'+arg.replace('\\', '/').replace('"', '\\"')+'"' for arg in args)+'\n', 'utf-8')
    try:
        subprocess.run([cc, '@'+str(response)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        raise ValueError('Host verification compilation failed:\n'+error.stderr) from error
    lib = ctypes.CDLL(str(library))
    lib.host_asset_count.restype = ctypes.c_size_t
    lib.host_row.argtypes = [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint,
                            ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t]
    lib.host_patch_valid.argtypes = [ctypes.c_size_t]
    lib.host_patch_row.argtypes = [ctypes.c_size_t, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                                  ctypes.POINTER(ctypes.c_uint16)]
    frame_count = row_count = patch_rows = 0
    try:
        if lib.host_asset_count() != len(resources): raise ValueError('C catalog resource count differs')
        for index, resource in enumerate(resources):
            part = [piece for piece in pieces if piece['resource'] is resource]
            for piece_index, piece in enumerate(part):
                w, h = piece['images'][0].size
                row = (ctypes.c_uint8*w)()
                for frame, expected in enumerate(piece['frames']):
                    for y in range(h):
                        if not lib.host_row(index, piece_index, frame, y, row, w) or bytes(row) != expected[y*w:(y+1)*w]:
                            raise ValueError(f'Production C sprite decode mismatch: {resource.id}/{piece_index}/{frame}/{y}')
                        row_count += 1
                    frame_count += 1
        by_id = {piece['resource'].id: piece for piece in pieces}
        names = ('top-left', 'top', 'top-right', 'left', 'center', 'right', 'bottom-left', 'bottom', 'bottom-right')
        for index, patch in enumerate(catalog['patches']):
            if not lib.host_patch_valid(index): raise ValueError('Production C rejected generated ninepatch')
            tiles = [by_id['ui/cards/'+patch['id']+'/'+name] for name in names]
            c = patch['corner_px']
            for w, h in ((48, 32), (240, 120)):
                row = (ctypes.c_uint16*w)()
                for y in range(h):
                    for x in range(w): row[x] = 0x1357
                    if not lib.host_patch_row(index, w, h, y, row): raise ValueError('Production C ninepatch row failed')
                    gy = 0 if y<c else 2 if y>=h-c else 1
                    ly = y if gy == 0 else y-(h-c) if gy == 2 else (y-c) % 8
                    for x in range(w):
                        gx = 0 if x<c else 2 if x>=w-c else 1
                        lx = x if gx == 0 else x-(w-c) if gx == 2 else (x-c) % 8
                        tile = tiles[gy*3+gx]; tw = tile['images'][0].width
                        ink = tile['frames'][0][ly*tw+lx]
                        expected = tile['palette'][ink] if ink else 0x1357
                        if row[x] != expected: raise ValueError('Production C ninepatch pixels differ from native tiles')
                    patch_rows += 1
    finally:
        handle = lib._handle; del lib
        if os.name == 'nt': _ctypes.FreeLibrary(handle)
        else: _ctypes.dlclose(handle)
    return {'verified_frames': frame_count, 'verified_sprite_rows': row_count,
            'verified_ninepatch_rows': patch_rows, 'comparison': 'generated C and production decoders vs indexed source'}
