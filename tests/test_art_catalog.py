"""A catalog must reject stale or inconsistent C evidence, even with current art."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from build_adventure_assets import build, OWNERSHIP
from adventure_assets_manifest import load_resources
from catalog_adventure_art import evidence
from adventure_assets_manifest import scoped
from test_adventure_assets import fixture


class CatalogEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        folder = Path(cls.temp.name)
        cls.art = fixture(folder)
        cls.output = folder/'generated'
        cls.report = build(cls.art, cls.output, ('travel', 'ui'), check_c=True)
        cls.resources, cls.manifests, cls.ui = load_resources(cls.art, ('travel', 'ui'))
        cls.path = cls.output/OWNERSHIP

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.path.write_text(json.dumps(self.report), 'utf-8')

    def check(self):
        return evidence(self.path, tuple(self.manifests), self.resources, self.art, self.ui)

    def changed(self, edit):
        report = json.loads(self.path.read_text('utf-8'))
        edit(report)
        self.path.write_text(json.dumps(report), 'utf-8')

    def test_actual_c_evidence_and_split_geometry_are_accepted(self):
        self.assertEqual(self.check()['production_c']['verified_frames'], self.report['python_verified_frames'])

    def test_nonempty_fake_proof_cannot_replace_exact_frame_and_group_counts(self):
        self.changed(lambda r: r.update(groups={}, production_c={'verified_frames': 1}))
        with self.assertRaisesRegex(ValueError, 'groups differ'): self.check()
        self.setUp()
        self.changed(lambda r: r['production_c'].update(verified_frames=1))
        with self.assertRaisesRegex(ValueError, 'validation counts'): self.check()

    def test_decoder_source_hash_is_required_even_when_manifest_still_matches(self):
        self.changed(lambda r: r['tools_sha256'].update({'firmware/main/adv_sprite.c': '0'*64}))
        with self.assertRaisesRegex(ValueError, 'decoder source hashes'): self.check()

    def test_generated_c_edit_after_check_is_rejected(self):
        path = self.output/'adv_assets_catalog.c'
        before = path.read_bytes()
        try:
            path.write_bytes(before+b'\n/* later edit */\n')
            with self.assertRaisesRegex(ValueError, 'changed after verification'): self.check()
        finally:
            path.write_bytes(before)

    def test_windows_manifest_separators_are_scoped_on_every_host(self):
        target=self.art/'frames/runtime/0.png'
        self.assertEqual(scoped(self.art,r'frames\runtime\0.png'),target.resolve())
        for escape in (r'..\outside.png',r'C:\outside.png',r'\\server\share\outside.png'):
            with self.subTest(path=escape),self.assertRaises(ValueError):scoped(self.art,escape)


if __name__ == '__main__':
    unittest.main()
