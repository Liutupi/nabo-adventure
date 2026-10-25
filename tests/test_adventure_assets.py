"""High-value manifest, safe publication and actual production C decoder checks."""
import hashlib
import json
from pathlib import Path
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


class AdventurePackage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.folder = Path(self.tmp.name)
        self.art = fixture(self.folder); self.output = self.folder/'generated'

    def tearDown(self): self.tmp.cleanup()

    def ui(self): return json.loads((self.art/'ui/ui-manifest.json').read_text('utf-8'))
    def update_ui(self, manifest): write_json(self.art/'ui/ui-manifest.json', manifest)

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

    def test_budget_failure_leaves_the_valid_package_and_manual_files_untouched(self):
        build(self.art, self.output, ('ui',))
        before = {p.name: p.read_bytes() for p in self.output.iterdir() if p.is_file()}
        manual = self.output/'handwritten.c'; manual.write_text('/* keep */', 'utf-8')
        with self.assertRaisesRegex(ValueError, 'budget'):
            build(self.art, self.output, ('ui',), ui_limit=1)
        self.assertEqual({name: (self.output/name).read_bytes() for name in before}, before)
        self.assertEqual(manual.read_text('utf-8'), '/* keep */')

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
