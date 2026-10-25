"""Verify fixed corners, repeating edges and dirty rendering against tiled images."""
import ctypes as C
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image
from host_tools import unload_library
import test_adv_sprites as sprites


class Patch(C.Structure):
    _fields_ = [('tile', C.POINTER(sprites.Asset) * 9)]


def fixture(corner=12):
    palette = [0] + [0x2000 + i * 0x101 for i in range(1, 28)]
    assets, images = [], []
    for i in range(9):
        w, h = (3 if i % 3 == 1 else corner), (3 if i // 3 == 1 else corner)
        indices = bytes(0 if x == y == 0 else 1 + i * 3 + (x + y) % 3
                        for y in range(h) for x in range(w))
        assets.append(sprites.asset_for(palette, sprites.packer.pack(w, h, [indices])))
        images.append((w, h, indices, palette))
    patch = Patch((C.POINTER(sprites.Asset) * 9)(*[C.pointer(a) for a in assets]))
    patch.keepalive = assets
    return patch, images


def tiled_reference(images, width, height, corner):
    """Paste full or cropped source tiles into the nine independent rectangles."""
    target = Image.new('I', (width, height), 0x1357)
    xs, ys = [0, corner, width - corner, width], [0, corner, height - corner, height]
    for index, (tw, th, indices, palette) in enumerate(images):
        source = Image.new('I', (tw, th)); source.putdata([palette[i] for i in indices])
        mask = Image.frombytes('L', (tw, th), bytes(255 if i else 0 for i in indices))
        col, row = index % 3, index // 3
        for y in range(ys[row], ys[row + 1], th):
            for x in range(xs[col], xs[col + 1], tw):
                box = (0, 0, min(tw, xs[col + 1] - x), min(th, ys[row + 1] - y))
                target.paste(source.crop(box), (x, y), mask.crop(box))
    return target


class Ninepatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        library = Path(cls.tmp.name) / 'ninepatch.dll'
        sprites.Sprites.compile(library, [sprites.HOST / 'adv_sprite_host.c'])
        cls.lib = lib = C.CDLL(str(library))
        lib.sprite_host_patch.argtypes = [C.POINTER(Patch), C.c_int, C.c_int, C.c_int, C.c_int]
        lib.sprite_host_flush.argtypes = [C.POINTER(C.c_uint16)]
        lib.adv_ninepatch_valid.argtypes = [C.POINTER(Patch)]
        lib.adv_ninepatch_valid.restype = C.c_bool
        lib.adv_ninepatch_row.argtypes = [C.POINTER(Patch), C.c_uint, C.c_uint, C.c_uint,
                                         C.c_uint, C.c_uint, C.POINTER(C.c_uint16)]
        lib.adv_ninepatch_row.restype = C.c_bool

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def snapshot(self):
        out = (C.c_uint16 * (240 * 320))()
        self.lib.sprite_host_flush(out)
        self.assertFalse(self.lib.sprite_host_overflow())
        return list(out)

    def test_minimum_and_maximum_cards_preserve_corners_and_repeat_tiles(self):
        for corner in (12, 16):
            patch, images = fixture(corner)
            for width, height in ((48, 32), (240, 120), (corner * 2, corner * 2)):
                self.lib.sprite_host_reset(); self.lib.sprite_host_begin(0)
                self.assertEqual(self.lib.sprite_host_patch(C.byref(patch), 0, 0, width, height), 1)
                expected = Image.new('I', (240, 320), 0x1357)
                expected.paste(tiled_reference(images, width, height, corner), (0, 0))
                self.assertEqual(self.snapshot(), list(expected.get_flattened_data()))

    def test_clipped_moving_and_resized_cards_match_full_redraw(self):
        patch, images = fixture()
        rng = random.Random(19)
        self.lib.sprite_host_reset()
        for _ in range(80):
            x, y, w, h = rng.randrange(-40, 220), rng.randrange(-30, 300), rng.randrange(24, 241), rng.randrange(24, 121)
            self.lib.sprite_host_begin(0)
            self.assertEqual(self.lib.sprite_host_patch(C.byref(patch), x, y, w, h), 1)
            incremental = self.snapshot()
            expected = Image.new('I', (240, 320), 0x1357)
            expected.paste(tiled_reference(images, w, h, 12), (x, y))
            self.assertEqual(incremental, list(expected.get_flattened_data()))
            self.lib.sprite_host_begin(1)
            self.lib.sprite_host_patch(C.byref(patch), x, y, w, h)
            self.assertEqual(incremental, self.snapshot())

    def test_invalid_geometry_is_rejected_and_row_bounds_do_not_overwrite(self):
        patch, _ = fixture()
        self.assertTrue(self.lib.adv_ninepatch_valid(C.byref(patch)))
        for args in ((0, 0, 23, 32), (0, 0, 48, 23), (32760, 0, 48, 32), (0, -32769, 48, 32)):
            self.lib.sprite_host_reset(); self.lib.sprite_host_begin(0)
            self.assertEqual(self.lib.sprite_host_patch(C.byref(patch), *args), 0)
        guard = (C.c_uint16 * 3)(0xabcd, 0x1357, 0xdcba)
        pixel = C.cast(C.byref(guard, 2), C.POINTER(C.c_uint16))
        self.assertTrue(self.lib.adv_ninepatch_row(C.byref(patch), 48, 32, 7, 8, 9, pixel))
        self.assertEqual((guard[0], guard[2]), (0xabcd, 0xdcba))
        self.assertFalse(self.lib.adv_ninepatch_row(C.byref(patch), 48, 32, 32, 0, 1, pixel))
        original = C.pointer(patch.keepalive[2])
        patch.tile[2] = C.POINTER(sprites.Asset)()
        self.assertFalse(self.lib.adv_ninepatch_valid(C.byref(patch)))
        patch.tile[2] = original
        self.assertTrue(self.lib.adv_ninepatch_valid(C.byref(patch)))
        patch.keepalive[2].width += 1
        self.assertFalse(self.lib.adv_ninepatch_valid(C.byref(patch)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
