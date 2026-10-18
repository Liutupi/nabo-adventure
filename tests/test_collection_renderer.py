"""Render the production launcher and jump integration into an emulated panel."""
import ctypes
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from PIL import Image
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT/'firmware/main'
HOST = ROOT/'tests/collection_host'

class Renderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        folder = Path(cls.tmp.name)
        assembly = folder/'assets.S'
        section = '.section .rdata,"dr"' if os.name == 'nt' else '.section .rodata'
        lines = [section]
        for filename in ('table_sprites.bin', 'jump_sprites.bin'):
            stem = filename.replace('.', '_')
            lines += ['.balign 4', f'.global _binary_{stem}_start', f'_binary_{stem}_start:',
                      f'.incbin "{(BOARD/filename).as_posix()}"',
                      f'.global _binary_{stem}_end', f'_binary_{stem}_end:']
        assembly.write_text('\n'.join(lines)+'\n', 'utf-8')
        sources = ['collection_model.c', 'collection_ui.c', 'collection_portrait.c', 'nabo_jump_model.c', 'nabo_jump_rig.c',
                   'nabo_dive_text.c', 'nabo_table_gfx.c', 'nabo_table_text.c', 'nabo_table_shapes.c',
                   'nabo_table_sprites.c', 'nabo_dice_render.c', 'collection_font_12.c',
                   'collection_font_16.c', 'collection_font_18.c', 'nabo_poster_font_28.c', 'nabo_mono_font_12.c']
        library = folder/'collection_render.dll'
        subprocess.run([CC, '-std=gnu11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-Wno-missing-field-initializers', '-I', str(HOST), '-I', str(ROOT/'tests/table_host'),
                        '-I', str(BOARD)] + [str(BOARD/s) for s in sources] +
                       [str(HOST/'collection_host.c'), str(assembly), '-lm', '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.host_show.argtypes = [ctypes.c_int] * 3
        cls.lib.host_snapshot.argtypes = [ctypes.POINTER(ctypes.c_uint16)]
        cls.lib.host_jump_reset.argtypes = [ctypes.c_int]
        cls.lib.host_jump_tick.argtypes = [ctypes.c_uint32, ctypes.c_int]
        cls.lib.host_jump_item.argtypes = [ctypes.c_int, ctypes.c_int]
        cls.lib.host_menu_cursor.argtypes = [ctypes.c_int]
        cls.previews = ROOT/'private/previews'
        cls.previews.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.lib.host_close()
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def snapshot(self):
        pixels = (ctypes.c_uint16 * (240*320))()
        self.lib.host_snapshot(pixels)
        return list(pixels)

    def save(self, name):
        pixels = self.snapshot()
        rgb = [((v >> 11)*255//31, ((v >> 5)&63)*255//63, (v&31)*255//31) for v in pixels]
        image = Image.new('RGB', (240, 320)); image.putdata(rgb)
        image.save(self.previews/name)

    def test_menu_and_settings_render(self):
        for page, cursor, edit, name in [(0, 0, -1, 'menu.png'), (4, 0, -1, 'settings.png'),
                                         (4, 1, 1, 'brightness-edit.png'), (5, 0, -1, 'status.png')]:
            self.assertEqual(self.lib.host_show(page, cursor, edit), 1)
            self.save(name)

    def test_menu_selection_clears_old_highlight_without_stale_pixels(self):
        for page, count in ((0, 4), (4, 6)):
            self.assertEqual(self.lib.host_show(page, 0, -1), 1)
            for cursor in range(1, count):
                previous = self.snapshot()
                self.lib.host_menu_cursor(cursor)
                incremental = self.snapshot()
                self.assertNotEqual(previous, incremental)
                self.lib.host_menu_full()
                self.assertEqual(incremental, self.snapshot())

    def test_all_six_one_person_items_render(self):
        self.assertEqual(self.lib.host_jump_reset(5), 1)
        for skin in range(6):
            self.lib.host_jump_item(2, skin)
            self.save(f'jump-item-{skin}.png')

    def test_bitmap_clipping_movement_and_image_replacement(self):
        for x, y, alternate in [(-2, -1, 0), (238, 318, 0), (238, 318, 1), (500, 500, 0), (110, 90, 1)]:
            self.lib.host_bitmap(x, y, alternate, 0)
            incremental = self.snapshot()
            expected = [0x1357] * (240 * 320)
            for sy in range(4):
                for sx in range(4):
                    if 0 <= x + sx < 240 and 0 <= y + sy < 320:
                        index = sy * 4 + sx
                        expected[(y + sy) * 240 + x + sx] = 16 - index if alternate else index + 1
            self.assertEqual(incremental, expected)
            self.lib.host_bitmap(x, y, alternate, 1)
            self.assertEqual(incremental, self.snapshot())

    def test_incremental_jump_frame_matches_complete_frame(self):
        self.assertEqual(self.lib.host_jump_reset(5), 1)
        self.lib.host_jump_tick(10, 1)
        hold = self.lib.host_jump_hold()
        for _ in range(hold//10): self.lib.host_jump_tick(10, 0)
        self.lib.host_jump_tick(hold % 10, 2)
        for frame in range(100):
            self.lib.host_jump_tick(10, 0)
            incremental = self.snapshot()
            self.lib.host_jump_full()
            self.assertEqual(incremental, self.snapshot(), f'stale jump pixels at frame {frame}')
        self.save('jump.png')

if __name__ == '__main__':
    unittest.main(verbosity=2)
