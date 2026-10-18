"""Exercise the compiled menu/settings model, including cancel versus persistent save."""
import ctypes
import subprocess
import tempfile
import unittest
import re
from pathlib import Path
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT/'firmware/main'

class Settings(ctypes.Structure):
    _fields_ = [('volume', ctypes.c_int), ('brightness', ctypes.c_int),
                ('sleep_seconds', ctypes.c_int), ('speaker', ctypes.c_bool)]

class Model(ctypes.Structure):
    _fields_ = [('page', ctypes.c_int), ('home_cursor', ctypes.c_int),
                ('settings_cursor', ctypes.c_int), ('editing', ctypes.c_int),
                ('settings', Settings), ('saved_edit', Settings)]

class Collection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name)/'collection.dll'
        subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-I', str(BOARD), str(BOARD/'collection_model.c'), '-o', str(path)], check=True)
        cls.lib = ctypes.CDLL(str(path))
        cls.lib.cg_init.argtypes = [ctypes.POINTER(Model), ctypes.POINTER(Settings)]
        cls.lib.cg_key.argtypes = [ctypes.POINTER(Model), ctypes.c_int]
        cls.lib.cg_key.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def model(self, volume=70, brightness=80, sleep=300):
        m = Model(); s = Settings(volume, brightness, sleep, True)
        self.lib.cg_init(ctypes.byref(m), ctypes.byref(s))
        return m

    def key(self, m, key):
        return self.lib.cg_key(ctypes.byref(m), key)

    def settings(self):
        m = self.model(); m.home_cursor = 3
        self.assertTrue(self.key(m, 2) & 4)
        self.assertEqual(m.page, 4)
        return m

    def test_bad_persisted_values_are_clamped_without_destroying_other_state(self):
        m = self.model(-1, 0, 99999)
        self.assertEqual((m.settings.volume, m.settings.brightness, m.settings.sleep_seconds), (0, 10, 600))
        self.assertEqual(m.editing, -1)

    def test_all_families_and_settings_are_reachable_and_return_home(self):
        m = self.model()
        for cursor, expected in enumerate((1, 2, 3, 4)):
            m.home_cursor = cursor
            self.assertTrue(self.key(m, 2) & 4)
            self.assertEqual(m.page, expected)
            self.key(m, 3)
            self.assertEqual(m.page, 0)

    def test_home_cursor_wraps_in_both_directions(self):
        m = self.model(); self.key(m, 0)
        self.assertEqual(m.home_cursor, 3)
        self.key(m, 1); self.assertEqual(m.home_cursor, 0)

    def test_edit_preview_is_not_saved_and_back_restores_old_value(self):
        m = self.settings(); self.key(m, 2)
        self.assertEqual(m.editing, 0)
        self.assertFalse(self.key(m, 0) & 2)
        self.assertEqual(m.settings.volume, 75)
        self.assertFalse(self.key(m, 3) & 2)
        self.assertEqual((m.page, m.editing, m.settings.volume), (4, -1, 70))

    def test_ok_commits_edit_and_later_cancel_does_not_undo_that_commit(self):
        m = self.settings(); self.key(m, 2); self.key(m, 0)
        self.assertTrue(self.key(m, 2) & 2)
        self.key(m, 2); self.key(m, 1); self.key(m, 3)
        self.assertEqual(m.settings.volume, 75)

    def test_volume_and_brightness_can_never_blackout_screen_or_exceed_bounds(self):
        for field, index, minimum in (('volume', 0, 0), ('brightness', 1, 10)):
            m = self.settings(); m.settings_cursor = index; self.key(m, 2)
            for _ in range(100): self.key(m, 1)
            self.assertEqual(getattr(m.settings, field), minimum)
            for _ in range(100): self.key(m, 0)
            self.assertEqual(getattr(m.settings, field), 100)

    def test_speaker_toggle_commits_without_entering_editor(self):
        m = self.settings(); m.settings_cursor = 2
        self.assertTrue(self.key(m, 2) & 2)
        self.assertFalse(m.settings.speaker)
        self.assertEqual(m.editing, -1)

    def test_sleep_zero_means_disabled_and_choices_are_bounded(self):
        m = self.settings(); m.settings_cursor = 3; self.key(m, 2)
        for _ in range(20): self.key(m, 1)
        self.assertEqual(m.settings.sleep_seconds, 0)
        values = []
        for _ in range(7): self.key(m, 0); values.append(m.settings.sleep_seconds)
        self.assertEqual(values, [30, 60, 120, 300, 600, 600, 600])

    def test_status_returns_to_settings_and_back_item_returns_home(self):
        m = self.settings(); m.settings_cursor = 4; self.key(m, 2)
        self.assertEqual(m.page, 5)
        self.key(m, 2); self.assertEqual(m.page, 4)
        m.settings_cursor = 5; self.key(m, 2)
        self.assertEqual(m.page, 0)

    def test_menu_keys_do_not_change_game_state(self):
        m = self.model(); self.key(m, 2)
        for key in (0, 1, 2): self.assertEqual(self.key(m, key), 0)
        self.assertEqual(m.page, 1)

    def test_every_collection_label_has_a_font_glyph(self):
        literals = re.findall(r'"([^"\n]*)"', (BOARD/'collection_ui.c').read_text('utf-8'))
        used = {c for s in literals for c in s if ord(c) > 127}
        for size in (12, 16, 18):
            font = (BOARD/f'collection_font_{size}.c').read_text('utf-8')
            have = {chr(int(h, 16)) for h in re.findall(r'/\* U\+([0-9A-F]+) ', font)}
            self.assertEqual(used - have, set(), f'missing collection font {size} glyph')

if __name__ == '__main__':
    unittest.main(verbosity=2)
