"""High-value manifest, safe publication and actual production C decoder checks."""
import _ctypes
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_adventure_assets import build, OWNERSHIP
from adventure_assets_manifest import load_resources


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n', 'utf-8')


def fixture(folder):
    art = folder/'art'; ui = art/'ui'; ui.mkdir(parents=True)
    colors = {'ink': '#183048', 'paper': '#f0d8a0'}
    write_json(ui/'palette.json', colors)
    entries = []
    def asset(path, bitmap):
        target = ui/path; target.parent.mkdir(parents=True, exist_ok=True); bitmap.save(target)
        entries.append({'name': path, 'path': path, 'size': list(bitmap.size), 'sha256': sha(target),
                        'pack': True, 'palette_group': 'shared', 'color_limit': 32})
    # Logical 240x320 input must split; this is test art, never production artwork.
    large = Image.new('RGBA', (240, 320), colors['paper'])
    ImageDraw.Draw(large).rectangle((8, 17, 100, 310), fill=colors['ink'])
    asset('background.png', large)
    atlas = Image.new('RGBA', (32, 32), colors['paper'])
    d = ImageDraw.Draw(atlas); d.rectangle((0, 0, 31, 31), outline=colors['ink'], width=2)
    atlas.putpixel((0, 0), (0, 0, 0, 0))
    xs = (0, 12, 20, 32)
    names = ('top-left', 'top', 'top-right', 'left', 'center', 'right', 'bottom-left', 'bottom', 'bottom-right')
    for i, name in enumerate(names):
        asset(f'cards/menu/normal/{name}.png', atlas.crop((xs[i%3], xs[i//3], xs[i%3+1], xs[i//3+1])))
    write_json(ui/'ui-manifest.json', {'shared_ui_palette': {'path': 'palette.json'}, 'assets': entries,
                                     'nine_slice': [{'family': 'menu', 'state': 'normal', 'corner_px': 12,
                                                     'path': 'cards/menu/normal'}], 'digit_metrics': {}})
    runtime = art/'frames/runtime'; runtime.mkdir(parents=True)
    paths = []
    for i in range(3):
        bitmap = Image.new('RGBA', (12, 10))
        ImageDraw.Draw(bitmap).rectangle((i, 2, i+4, 8), fill=colors['ink'])
        target = runtime/f'{i}.png'; bitmap.save(target); paths.append(target)
    write_json(art/'manifest.json', {'animations': [{'name': 'idle', 'skin': 'travel', 'runtime_canvas': [12, 10],
               'runtime_anchor': [6, 10], 'runtime_frames': [str(p.relative_to(art)) for p in paths],
               'runtime_sha256': [sha(p) for p in paths], 'fps': 12, 'loop': True}]})
    return art


@contextmanager
def compiled_catalog(output):
    """Read pointers/metadata from the actual generated C catalog, not a Python map."""
    source=output/'_intern_probe.c'
    source.write_text('''#include "adv_assets_catalog.h"
#include <stdint.h>
uintptr_t host_pointer(const char *id, unsigned p) {
 const adv_asset_record_t *r=adv_assets_find(id);
 return r && p<r->piece_count ? (uintptr_t)r->pieces[p].sprite : 0;
}
int host_meta(const char *id, int *out) {
 const adv_asset_record_t *r=adv_assets_find(id); if(!r) return 0;
 out[0]=r->width; out[1]=r->height; out[2]=r->anchor_x; out[3]=r->anchor_y;
 out[4]=r->fps; out[5]=r->loop; out[6]=r->piece_count;
 out[7]=r->pieces[0].x; out[8]=r->pieces[0].y; return 1;
}
''','utf-8')
    cc=os.environ.get('CC') or shutil.which('gcc')
    if not cc: raise ValueError('Pointer regression requires host C compiler')
    library=output/'_intern_probe.dll'
    args=['-std=c11','-O2','-shared','-Wall','-Wextra','-Werror',
          '-Wl,--export-all-symbols' if os.name=='nt' else '-fPIC',
          '-I',str(ROOT/'firmware/main'),'-I',str(output),
          *map(str,sorted(output.glob('adv_assets_*.c'))),str(source),'-o',str(library)]
    response=output/'_intern_probe.rsp'
    response.write_text('\n'.join('"'+a.replace('\\','/').replace('"','\\"')+'"' for a in args),'utf-8')
    subprocess.run([cc,'@'+str(response)],check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(library));lib.host_pointer.argtypes=[ctypes.c_char_p,ctypes.c_uint]
    lib.host_pointer.restype=ctypes.c_size_t
    lib.host_meta.argtypes=[ctypes.c_char_p,ctypes.POINTER(ctypes.c_int)]
    try: yield lib
    finally:
        handle=lib._handle;del lib
        if os.name=='nt':_ctypes.FreeLibrary(handle)
        else:_ctypes.dlclose(handle)


class AdventurePackage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.folder = Path(self.tmp.name)
        self.art = fixture(self.folder); self.output = self.folder/'generated'

    def tearDown(self): self.tmp.cleanup()

    def ui(self): return json.loads((self.art/'ui/ui-manifest.json').read_text('utf-8'))
    def update_ui(self, manifest): write_json(self.art/'ui/ui-manifest.json', manifest)

    def duplicate_ui(self, original, target, **extra):
        manifest=self.ui();entry=next(e for e in manifest['assets'] if e['path']==original)
        clone={**entry,'name':target,'path':target,**extra};source=self.art/'ui'/original
        destination=self.art/'ui'/target;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination);clone['sha256']=sha(destination)
        manifest['assets'].append(clone);self.update_ui(manifest)

    def test_actual_generated_c_roundtrips_split_background_animation_and_patch(self):
        report = build(self.art, self.output, ('ui', 'travel'), check_c=True)
        self.assertGreater(report['production_c']['verified_frames'], 3)
        self.assertEqual(report['production_c']['verified_ninepatch_rows'], 32+120)
        background = next(r for r in report['source_frames'] if r['id'] == 'ui/background')
        self.assertEqual([p['size'] for p in background['pieces']], [[240, 256], [240, 64]])
        self.assertEqual([p['offset'] for p in background['pieces']], [[0, 0], [0, 256]])
        animation = next(r for r in report['source_frames'] if r['id'] == 'travel/idle')
        self.assertEqual((animation['anchor'], animation['fps'], animation['loop']), ([6, 10], 12, True))

    def test_game_manifest_roundtrips_actor_and_prop_without_changing_firmware_selection(self):
        travel = json.loads((self.art/'manifest.json').read_text('utf-8'))
        animation = {**travel['animations'][0], 'skin': 'post_a', 'name': 'window_idle'}
        prop = self.art/'train.png'; Image.new('RGBA', (20, 12), '#183048').save(prop)
        write_json(self.art/'post-manifest.json', {'animations': [animation], 'assets': [
            {'id': 'post/train', 'path': 'train.png', 'sha256': sha(prop), 'size': [20, 12], 'anchor': [10, 12], 'color_limit': 16}]})
        report = build(self.art, self.output, ('post',), check_c=True)
        self.assertEqual(set(report['groups']), {'post'})
        self.assertEqual(report['production_c']['verified_frames'], 4)
        self.assertEqual({a['id'] for a in report['source_frames']}, {'post_a/window_idle', 'game/post/train'})
        self.assertLess(report['groups']['post']['static_bytes_estimate_c3'], 260*1024)

    def test_identical_ui_uses_one_real_c_object_and_keeps_logical_metadata_and_budget(self):
        self.duplicate_ui('background.png','alias.png',anchor=[13,-7],draw_offset=[9,11])
        self.duplicate_ui('background.png','same.png',anchor=[0,0],draw_offset=[-3,4])
        report=build(self.art,self.output,('ui',),check_c=True)
        records={r['id']:r for r in report['source_frames']};g=report['groups']['ui']
        self.assertEqual((g['resources'],g['pieces'],g['frames']),(12,15,15))
        self.assertEqual(g['physical_sprites'],11)
        self.assertEqual(g['interned_pieces'],4)
        self.assertEqual(report['python_verified_frames'],15)
        self.assertEqual(report['production_c']['verified_frames'],15)
        self.assertEqual(report['production_c']['verified_ninepatch_rows'],152)
        self.assertEqual([p['offset'] for p in records['ui/alias']['pieces']],[[9,11],[9,267]])
        self.assertEqual(records['ui/alias']['anchor'],[13,-7])
        for index in range(2):
            symbols=[records[name]['pieces'][index]['symbol'] for name in ('ui/alias','ui/background','ui/same')]
            self.assertEqual(len(set(symbols)),1)
        physical=[json.loads(p.read_text('utf-8')) for p in self.output.glob('adv_assets_*.json') if p.name!=OWNERSHIP]
        self.assertEqual(len(physical),g['physical_sprites'])
        self.assertEqual(g['rle_bytes'],sum(p['data_bytes'] for p in physical))
        self.assertEqual(g['table_bytes'],sum(p['table_bytes'] for p in physical))
        expected=sum(24+len(r['id'].encode())+1 for r in report['source_frames'])+8*g['pieces']+32*g['physical_sprites']
        expected+=36+len(report['catalog']['shared_ui_palette_rgb565'])*2+8
        self.assertEqual(g['descriptor_catalog_estimate_c3'],expected)
        with compiled_catalog(self.output) as c:
            for index in range(2):
                self.assertEqual(c.host_pointer(b'ui/alias',index),c.host_pointer(b'ui/background',index))
                self.assertEqual(c.host_pointer(b'ui/same',index),c.host_pointer(b'ui/background',index))
            values=(ctypes.c_int*9)();self.assertTrue(c.host_meta(b'ui/alias',values))
            self.assertEqual(list(values),[240,320,13,-7,0,0,2,9,11])

    def test_exact_source_pixels_required_even_if_rgb565_decodes_to_same_color(self):
        original='cards/menu/normal/top-left.png';self.duplicate_ui(original,'different.png')
        path=self.art/'ui/different.png';bitmap=Image.open(path).convert('RGBA')
        bitmap.putpixel((1,0),(25,48,72,255));bitmap.save(path)
        manifest=self.ui();next(e for e in manifest['assets'] if e['path']=='different.png')['sha256']=sha(path)
        self.update_ui(manifest);palette=self.art/'ui/palette.json';colors=json.loads(palette.read_text('utf-8'))
        colors['different-source-rgb']='#193048';write_json(palette,colors)
        report=build(self.art,self.output,('ui',),check_c=True)
        self.assertEqual(report['production_c']['verified_frames'],12)
        with compiled_catalog(self.output) as c:
            self.assertNotEqual(c.host_pointer(b'ui/different',0),c.host_pointer(b'ui/cards/menu/normal/top-left',0))

    def test_interned_ninepatch_tiles_keep_each_logical_patch_and_source_count(self):
        manifest=self.ui()
        for e in list(manifest['assets']):
            if 'cards/menu/normal/' in e['path']:
                self.duplicate_ui(e['path'],e['path'].replace('/normal/','/selected/'))
        manifest=self.ui();manifest['nine_slice'].append({**manifest['nine_slice'][0],'state':'selected'})
        self.update_ui(manifest);report=build(self.art,self.output,('ui',),check_c=True)
        self.assertEqual(report['groups']['ui']['resources'],19)
        self.assertEqual(report['groups']['ui']['pieces'],20)
        self.assertEqual(report['groups']['ui']['interned_pieces'],9)
        self.assertEqual(report['production_c']['verified_frames'],20)
        self.assertEqual(report['production_c']['verified_ninepatch_rows'],304)
        self.assertEqual(len(report['source_frames']),19)
        with compiled_catalog(self.output) as c:
            for tile in ('top-left','top','top-right','left','center','right','bottom-left','bottom','bottom-right'):
                self.assertEqual(c.host_pointer(('ui/cards/menu/normal/'+tile).encode(),0),
                                 c.host_pointer(('ui/cards/menu/selected/'+tile).encode(),0))

    def test_animation_sequence_interns_independently_of_anchor_fps_and_loop(self):
        path=self.art/'manifest.json';manifest=json.loads(path.read_text('utf-8'));idle=manifest['animations'][0]
        manifest['animations'] += [{**idle,'name':'alias','runtime_anchor':[1,9],'fps':6,'loop':False},
                                   {**idle,'name':'reversed','runtime_frames':idle['runtime_frames'][::-1],
                                    'runtime_sha256':idle['runtime_sha256'][::-1]}]
        write_json(path,manifest);report=build(self.art,self.output,('travel',),check_c=True);g=report['groups']['travel']
        self.assertEqual((g['resources'],g['frames'],g['physical_sprites'],g['physical_frames']),(3,9,2,6))
        self.assertEqual(report['production_c']['verified_frames'],9)
        with compiled_catalog(self.output) as c:
            self.assertEqual(c.host_pointer(b'travel/alias',0),c.host_pointer(b'travel/idle',0))
            self.assertNotEqual(c.host_pointer(b'travel/reversed',0),c.host_pointer(b'travel/idle',0))
            values=(ctypes.c_int*9)();self.assertTrue(c.host_meta(b'travel/alias',values))
            self.assertEqual(list(values),[12,10,1,9,6,0,1,0,0])

    def test_same_pixels_in_different_groups_are_separately_charged_real_objects(self):
        source=self.art/'frames/runtime/0.png';target=self.art/'ui/cross.png';shutil.copyfile(source,target)
        manifest=self.ui();manifest['assets'].append({'name':'cross','path':'cross.png','size':[12,10],
            'sha256':sha(target),'pack':True,'palette_group':'shared','color_limit':32});self.update_ui(manifest)
        write_json(self.art/'shared-static-manifest.json',{'assets':[{'id':'cross','path':'frames/runtime/0.png',
            'size':[12,10],'anchor':[0,0],'sha256':sha(source),'color_limit':64}]})
        report=build(self.art,self.output,('ui','static'),check_c=True)
        self.assertEqual(report['groups']['static']['physical_sprites'],1)
        self.assertGreater(report['groups']['static']['rle_bytes'],0)
        self.assertEqual(report['groups']['ui']['interned_pieces'],0)
        with compiled_catalog(self.output) as c:
            self.assertNotEqual(c.host_pointer(b'ui/cross',0),c.host_pointer(b'static/cross',0))

    def test_equal_rgba_byte_stream_with_different_dimensions_is_not_interned(self):
        manifest=self.ui()
        for name,size in (('wide',(16,8)),('tall',(8,16))):
            path=self.art/'ui'/f'{name}.png';Image.new('RGBA',size,'#183048').save(path)
            manifest['assets'].append({'name':name,'path':path.name,'size':list(size),'sha256':sha(path),
                                      'pack':True,'palette_group':'shared','color_limit':32})
        self.update_ui(manifest);report=build(self.art,self.output,('ui',),check_c=True)
        self.assertEqual(report['groups']['ui']['interned_pieces'],0)
        with compiled_catalog(self.output) as c:
            self.assertNotEqual(c.host_pointer(b'ui/wide',0),c.host_pointer(b'ui/tall',0))

    def test_frame_count_is_part_of_the_intern_identity(self):
        path=self.art/'manifest.json';manifest=json.loads(path.read_text('utf-8'));idle=manifest['animations'][0]
        manifest['animations']=[{**idle,'name':'one','runtime_frames':idle['runtime_frames'][:1],
                                'runtime_sha256':idle['runtime_sha256'][:1]},
                               {**idle,'name':'three','runtime_frames':idle['runtime_frames'][:1]*3,
                                'runtime_sha256':idle['runtime_sha256'][:1]*3}]
        write_json(path,manifest);report=build(self.art,self.output,('travel',),check_c=True)
        self.assertEqual(report['groups']['travel']['physical_frames'],4)
        with compiled_catalog(self.output) as c:
            self.assertNotEqual(c.host_pointer(b'travel/one',0),c.host_pointer(b'travel/three',0))

    def test_alias_conversion_removes_only_its_previously_owned_sprite_files(self):
        original='cards/menu/normal/top-left.png';self.duplicate_ui(original,'zz-alias.png')
        path=self.art/'ui/zz-alias.png';bitmap=Image.open(path).convert('RGBA')
        bitmap.putpixel((0,0),(24,48,72,255));bitmap.save(path)
        manifest=self.ui();next(e for e in manifest['assets'] if e['path']=='zz-alias.png')['sha256']=sha(path)
        self.update_ui(manifest);old=build(self.art,self.output,('ui',))
        old_symbol=next(r for r in old['source_frames'] if r['id']=='ui/zz-alias')['pieces'][0]['symbol']
        self.assertTrue((self.output/(old_symbol+'.c')).exists())
        manual=self.output/'adv_assets_manual.c';manual.write_text('/* unowned */','utf-8')
        shutil.copyfile(self.art/'ui'/original,path);manifest=self.ui()
        next(e for e in manifest['assets'] if e['path']=='zz-alias.png')['sha256']=sha(path);self.update_ui(manifest)
        new=build(self.art,self.output,('ui',),check_c=True)
        for suffix in ('.c','.h','.json'):self.assertFalse((self.output/(old_symbol+suffix)).exists())
        self.assertEqual(manual.read_text('utf-8'),'/* unowned */')
        self.assertEqual(new['groups']['ui']['interned_pieces'],1)

    def test_budget_failure_leaves_the_valid_package_and_manual_files_untouched(self):
        build(self.art, self.output, ('ui',))
        before = {p.name: p.read_bytes() for p in self.output.iterdir() if p.is_file()}
        manual = self.output/'handwritten.c'; manual.write_text('/* keep */', 'utf-8')
        with self.assertRaisesRegex(ValueError, 'budget'):
            build(self.art, self.output, ('ui',), ui_limit=1)
        self.assertEqual({name: (self.output/name).read_bytes() for name in before}, before)
        self.assertEqual(manual.read_text('utf-8'), '/* keep */')

    def test_startup_actor_is_counted_with_ui_even_when_stored_in_travel(self):
        manifest = json.loads((self.art/'manifest.json').read_text('utf-8'))
        manifest['animations'][0].update(name='welcome', startup=True)
        manifest['animations'].append({**manifest['animations'][0],'name':'welcome_alias'})
        write_json(self.art/'manifest.json', manifest)
        first = build(self.art, self.output, ('travel', 'ui'))
        before = (self.output/OWNERSHIP).read_bytes()
        opening = first['startup_composition']
        self.assertGreater(opening['startup_actor_estimate_c3'], 0)
        self.assertEqual(opening['startup_actor_estimate_c3'],first['groups']['travel']['static_bytes_estimate_c3'])
        self.assertEqual(first['groups']['travel']['physical_sprites'],1)
        limit = opening['ui_assets_estimate_c3'] + 1
        with self.assertRaisesRegex(ValueError, 'Startup UI composition'):
            build(self.art, self.output, ('travel', 'ui'), ui_limit=limit)
        self.assertEqual((self.output/OWNERSHIP).read_bytes(), before)

    def test_rebuild_cleans_only_previous_owned_files(self):
        old = build(self.art, self.output, ('ui',))
        manual = self.output/'adv_assets_handwritten.c'; manual.write_text('/* unowned */', 'utf-8')
        new = build(self.art, self.output, ('travel',))
        for name in set(old['files'])-set(new['files']): self.assertFalse((self.output/name).exists())
        self.assertEqual(manual.read_text('utf-8'), '/* unowned */')
        self.assertTrue((self.output/OWNERSHIP).exists())

    def test_hash_mismatch_is_rejected_before_output_exists(self):
        (self.art/'ui/background.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            build(self.art, self.output, ('ui',))
        self.assertFalse(self.output.exists())

    def test_runtime_contract_is_required_without_master_fallback(self):
        path = self.art/'manifest.json'; manifest = json.loads(path.read_text('utf-8'))
        del manifest['animations'][0]['runtime_frames']; write_json(path, manifest)
        with self.assertRaises(KeyError): load_resources(self.art, ('travel',))

    def test_declared_canvas_and_binary_alpha_are_enforced(self):
        for kind in ('size', 'alpha'):
            with self.subTest(kind=kind):
                manifest = self.ui(); entry = manifest['assets'][0]
                if kind == 'size': entry['size'] = [239, 320]
                else:
                    entry['size'] = [240, 320]
                    path = self.art/'ui/background.png'
                    with Image.open(path) as source: bitmap = source.convert('RGBA')
                    bitmap.putpixel((0, 0), (24, 48, 72, 128)); bitmap.save(path); entry['sha256'] = sha(path)
                self.update_ui(manifest)
                with self.assertRaises(ValueError): load_resources(self.art, ('ui',))

    def test_path_traversal_and_unsafe_ownership_are_rejected(self):
        manifest = self.ui(); manifest['assets'][0]['path'] = '../escape.png'; self.update_ui(manifest)
        with self.assertRaisesRegex(ValueError, 'escapes'): load_resources(self.art, ('ui',))
        self.output.mkdir()
        write_json(self.output/OWNERSHIP, {'schema': 'adventure-assets-package-v1', 'files': ['../manual.c']})
        with self.assertRaises(ValueError): build(self.art, self.output, ('travel',))

    def test_combined_shared_ui_palette_cannot_exceed_32(self):
        path = self.art/'ui/background.png'
        bitmap = Image.new('RGBA', (240, 320), '#f0d8a0')
        for i in range(33): bitmap.putpixel((i, 0), (i*7, 30, 80, 255))
        bitmap.save(path)
        manifest = self.ui(); manifest['assets'][0]['sha256'] = sha(path)
        manifest['assets'][0]['color_limit'] = 64; self.update_ui(manifest)
        with self.assertRaisesRegex(ValueError, 'Combined shared UI palette'):
            load_resources(self.art, ('ui',))

    def test_c_identifiers_and_digit_metric_contracts_are_validated(self):
        manifest = self.ui(); manifest['nine_slice'][0]['state'] = 'bad;declaration'
        self.update_ui(manifest)
        with self.assertRaisesRegex(ValueError, 'identifier'): load_resources(self.art, ('ui',))
        manifest['nine_slice'][0]['state'] = 'normal'
        manifest['digit_metrics'] = {'36': {'x': {'path': 'numbers/36/x.png', 'advance': 12}}}
        self.update_ui(manifest)
        with self.assertRaisesRegex(ValueError, 'digit metric'): load_resources(self.art, ('ui',))


if __name__ == '__main__': unittest.main(verbosity=2)
