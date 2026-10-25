"""Synthetic geometry proves the packer, C row decoder and dirty strip renderer.

These fixtures contain no NABO artwork. Exact comparisons start after palette
quantization; generated C is also compiled and checked against the same frames.
"""
import ctypes as C
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD, HOST = ROOT / 'firmware/main', ROOT / 'tests/adv_host'
spec = importlib.util.spec_from_file_location('generate_adv_sprites', ROOT / 'tools/generate_adv_sprites.py')
packer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packer)


class Asset(C.Structure):
    _fields_ = [('width', C.c_uint16), ('height', C.c_uint16), ('frame_count', C.c_uint16),
                ('palette_size', C.c_uint16), ('row_count', C.c_uint32), ('data_size', C.c_uint32),
                ('palette', C.POINTER(C.c_uint16)), ('keys', C.POINTER(C.c_uint16)),
                ('rows', C.POINTER(C.c_uint16)), ('data', C.POINTER(C.c_uint8))]


def asset_for(palette, packed):
    arrays = [(t * len(v))(*v) for t, v in [(C.c_uint16, palette), (C.c_uint16, packed['keys']),
              (C.c_uint16, packed['rows']), (C.c_uint8, packed['data'])]]
    asset = Asset(packed['width'], packed['height'], len(packed['keys']), len(palette),
                  len(packed['rows']), len(packed['data']), *arrays)
    asset.keepalive = arrays
    return asset


def synthetic_frames(count=18):
    frames = []
    for f in range(count):
        image = Image.new('RGBA', (37, 19))
        draw = ImageDraw.Draw(image)
        # A busy static region makes sparse deltas smaller than full rows.
        for x in range(37):
            draw.line((x, 0, x, 18), fill=((x % 5) * 48, (x % 3) * 80, 128, 255))
        draw.rectangle((f % 20, 4, f % 20 + 4, 11), fill=(0, 0, 0, 0))
        draw.point((36, 18), fill=(255, 0, 0, 255))  # asymmetric orientation marker
        frames.append(image)
    return frames


class Sprites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.tmp.name)
        cls.library = cls.folder / 'sprites.dll'
        cls.compile(cls.library, [HOST / 'adv_sprite_host.c'])
        cls.lib = lib = C.CDLL(str(cls.library))
        lib.adv_sprite_row.argtypes = [C.POINTER(Asset), C.c_uint, C.c_uint, C.POINTER(C.c_uint8), C.c_size_t]
        lib.adv_sprite_row.restype = C.c_bool
        lib.adv_sprite_frame_valid.argtypes = [C.POINTER(Asset), C.c_uint]
        lib.adv_sprite_frame_valid.restype = C.c_bool
        lib.sprite_host_add.argtypes = [C.POINTER(Asset), C.c_uint, C.c_int, C.c_int]
        lib.sprite_host_tint.argtypes = [C.POINTER(Asset), C.c_uint, C.c_int, C.c_int, C.c_uint16]
        lib.sprite_host_dim.argtypes = lib.sprite_host_add.argtypes
        lib.sprite_host_crop.argtypes=[C.POINTER(Asset),C.c_uint]+[C.c_int]*6
        lib.sprite_host_flush.argtypes = [C.POINTER(C.c_uint16)]
        lib.sprite_host_flush.restype = C.c_uint

    @classmethod
    def compile(cls, output, extra):
        subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-I', str(HOST), '-I', str(BOARD), *[str(BOARD / s) for s in
                        ['adv_gfx.c', 'adv_sprite.c', 'adv_ninepatch.c', 'adv_shapes.c', 'adv_text.c']],
                        *map(str, extra), '-o', str(output)], check=True)

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def c_decode(self, asset, frame):
        result = bytearray()
        for y in range(asset.height):
            buf = (C.c_uint8 * (asset.width + 2))(*([173] * (asset.width + 2)))
            row = C.cast(C.byref(buf, 1), C.POINTER(C.c_uint8))
            self.assertTrue(self.lib.adv_sprite_row(C.byref(asset), frame, y, row, asset.width))
            self.assertEqual((buf[0], buf[-1]), (173, 173))
            result.extend(buf[1:-1])
        return bytes(result)

    def test_each_frame_random_access_matches_quantized_reference(self):
        palette, frames = packer.index_frames(synthetic_frames())
        packed = packer.pack(37, 19, frames)
        asset = asset_for(palette, packed)
        self.assertLessEqual(len(palette), 64)
        self.assertTrue(any(k != f for f, k in enumerate(packed['keys'])))
        for f, key in enumerate(packed['keys']):
            self.assertLessEqual(key, f)
            self.assertLess(f - key, packer.KEY_INTERVAL)
            self.assertEqual(packed['keys'][key], key)
            self.assertEqual(packed['keys'][key:f + 1], [key] * (f - key + 1))
        order = list(range(len(frames))); random.Random(8).shuffle(order)
        for f in order:
            self.assertEqual(packer.decode(packed, f), frames[f])
            self.assertEqual(self.c_decode(asset, f), frames[f])

    def test_shared_palette_quantizes_more_than_64_colours_deterministically(self):
        image = Image.new('RGBA', (40, 20))
        image.putdata([(x % 256, (x * 29) % 256, (x * 73) % 256, 255) for x in range(800)])
        palette, frames = packer.index_frames([image, image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)])
        self.assertLessEqual(len(palette), 64)
        self.assertEqual((palette, frames), packer.index_frames([image, image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)]))
        asset = asset_for(palette, packer.pack(40, 20, frames))
        for f in range(2): self.assertEqual(self.c_decode(asset, f), frames[f])

    def test_alpha_requires_explicit_matte_and_preserves_transparent_zero(self):
        image = Image.new('RGBA', (3, 1))
        image.putdata([(255, 0, 0, 128), (0, 0, 0, 255), (4, 5, 6, 0)])
        with self.assertRaisesRegex(ValueError, 'partial alpha'):
            packer.index_frames([image])
        palette, frames = packer.index_frames([image], (0, 0, 255))
        self.assertEqual(palette[frames[0][0]], packer.rgb565((128, 0, 127)))
        self.assertNotEqual(frames[0][1], 0)  # opaque black is not transparency
        self.assertEqual(frames[0][2], 0)

    def test_transparent_clip_and_long_runs(self):
        for image in [Image.new('RGBA', (256, 2)), Image.new('RGBA', (256, 2), (255, 255, 255, 255))]:
            palette, frames = packer.index_frames([image] * 10)
            asset = asset_for(palette, packer.pack(256, 2, frames))
            for f in (9, 0, 7, 8): self.assertEqual(self.c_decode(asset, f), frames[f])

    def test_generator_cli_emits_reproducible_compilable_verified_c(self):
        paths = []
        for f, image in enumerate(synthetic_frames(10)):
            path = self.folder / f'fixture-{f}.png'; image.save(path); paths.append(path)
        output = self.folder / 'synthetic'
        args = [sys.executable, str(ROOT / 'tools/generate_adv_sprites.py'), '--output', str(output),
                '--name', 'synthetic', *map(str, paths)]
        subprocess.run(args, check=True, capture_output=True)
        before = [Path(str(output) + ext).read_bytes() for ext in ('.h', '.c', '.json')]
        subprocess.run(args, check=True, capture_output=True)
        self.assertEqual(before, [Path(str(output) + ext).read_bytes() for ext in ('.h', '.c', '.json')])
        report = json.loads(before[2]); self.assertEqual(report['verified_frames'], 10)
        self.assertEqual(report['format'], packer.FORMAT)
        library = self.folder / 'generated.dll'
        self.compile(library, [Path(str(output) + '.c')])
        lib = C.CDLL(str(library))
        try:
            asset = Asset.in_dll(lib, 'synthetic')
            _, frames = packer.index_frames(synthetic_frames(10))
            for f in range(10): self.assertEqual(self.c_decode(asset, f), frames[f])
        finally:
            del asset
            unload_library(lib._handle)

    def render(self, items, full=False):
        self.lib.sprite_host_begin(int(full))
        for asset, frame, x, y in items:
            self.assertTrue(self.lib.sprite_host_add(C.byref(asset), frame, x, y))
        out = (C.c_uint16 * (240 * 320))()
        sent = self.lib.sprite_host_flush(out)
        self.assertFalse(self.lib.sprite_host_overflow())
        return list(out), sent

    def expected(self, items):
        result = [0x1357] * (240 * 320)
        for asset, frame, x, y in items:
            indices = self.c_decode(asset, frame)
            for sy in range(asset.height):
                for sx in range(asset.width):
                    index = indices[sy * asset.width + sx]
                    if index and 0 <= x + sx < 240 and 0 <= y + sy < 320:
                        result[(y + sy) * 240 + x + sx] = asset.palette[index]
        return result

    def test_renderer_animation_movement_clipping_removal_and_asset_replacement(self):
        palette, frames = packer.index_frames(synthetic_frames())
        a = asset_for(palette, packer.pack(37, 19, frames))
        b = asset_for([0, 0xffff], packer.pack(5, 3, [bytes([1, 0, 1, 0, 1] * 3)]))
        self.lib.sprite_host_reset()
        scenes = [[(a, f, x, y)] for f, x, y in [(0, -2, -1), (7, -2, -1), (8, 235, 317),
                   (17, 235, 317), (2, 500, 500), (1, -37, 10), (3, 44, 60)]]
        scenes += [[(b, 0, 44, 60)], [(a, 7, 44, 60), (b, 0, 46, 62)], []]
        for scene in scenes:
            incremental, _ = self.render(scene)
            self.assertEqual(incremental, self.expected(scene))
            self.assertEqual(incremental, self.render(scene, True)[0])
            self.assertEqual(self.render(scene)[1], 0, 'unchanged immutable asset should send no pixels')

    def test_renderer_fuzz_matches_pixel_oracle_and_full_redraw(self):
        palette, frames = packer.index_frames(synthetic_frames())
        asset = asset_for(palette, packer.pack(37, 19, frames))
        rng = random.Random(983)
        self.lib.sprite_host_reset()
        for _ in range(80):
            scene = [(asset, rng.randrange(18), rng.randrange(-40, 260), rng.randrange(-30, 340))
                     for _ in range(rng.randrange(4))]
            incremental, _ = self.render(scene)
            self.assertEqual(incremental, self.expected(scene))
            self.assertEqual(incremental, self.render(scene, True)[0])

    def test_overlapping_sprites_respect_changed_paint_order(self):
        a = asset_for([0, 0xf800], packer.pack(4, 4, [bytes([1] * 16)]))
        b = asset_for([0, 0x07e0], packer.pack(4, 4, [bytes([1] * 16)]))
        first, second = (a, 0, 10, 10), (b, 0, 12, 12)
        self.lib.sprite_host_reset()
        self.render([first, second])
        scene = [second, first]
        incremental, _ = self.render(scene)
        self.assertEqual(incremental, self.expected(scene))
        self.assertEqual(incremental, self.render(scene, True)[0])

    def test_stamp_tint_changes_dirty_pixels_and_keeps_transparency(self):
        a = asset_for([0, 0xffff], packer.pack(4, 2, [bytes([1, 0, 1, 0, 0, 1, 1, 1])]))
        self.lib.sprite_host_reset()
        out = (C.c_uint16 * (240 * 320))()
        for color, x, y in [(0xbb87, -1, 1), (0x9d54, -1, 1), (0xd527, 239, 319), (0, 5, 4)]:
            expected = [0x1357] * (240 * 320)
            indices = self.c_decode(a, 0)
            for sy in range(2):
                for sx in range(4):
                    if indices[sy * 4 + sx] and 0 <= x+sx < 240 and 0 <= y+sy < 320:
                        expected[(y+sy)*240+x+sx] = color
            for full in (False, True):
                self.lib.sprite_host_begin(full)
                self.assertTrue(self.lib.sprite_host_tint(C.byref(a), 0, x, y, color))
                self.lib.sprite_host_flush(out)
                self.assertEqual(list(out), expected)

    def test_locked_landmark_dim_preserves_rgb_channels_and_transparency(self):
        palette = [0, 0xffff, 0xf800, 0x07e0, 0x001f, 0]
        a = asset_for(palette, packer.pack(6, 1, [bytes(range(6))]))
        self.lib.sprite_host_reset()
        out = (C.c_uint16 * (240 * 320))()
        for dim in (False, True, False):
            expected = [0x1357] * (240 * 320)
            for i, color in enumerate(palette[1:], 1):
                r, g, b = color >> 11, color >> 5 & 63, color & 31
                expected[10*240+20+i] = (r//2 << 11 | g//2 << 5 | b//2) if dim else color
            for full in (False, True):
                self.lib.sprite_host_begin(full)
                add = self.lib.sprite_host_dim if dim else self.lib.sprite_host_add
                self.assertTrue(add(C.byref(a), 0, 20, 10))
                self.lib.sprite_host_flush(out)
                self.assertEqual(list(out), expected)

    def test_crop_keeps_native_source_coordinates_and_checks_bounds(self):
        pixels=bytes([x%3 for y in range(5) for x in range(8)])
        a=asset_for([0,0xf800,0],packer.pack(8,5,[pixels]))
        self.lib.sprite_host_reset();out=(C.c_uint16*(240*320))()
        # The first two share destination bounds but use different source pixels.
        for x,y,sx,sy,w,h in [(5,6,2,1,4,3),(4,5,3,2,4,3),(-4,-2,1,1,7,4),(237,317,0,0,8,5)]:
            expected=[0x1357]*(240*320)
            for yy in range(sy,sy+h):
                for xx in range(sx,sx+w):
                    v=pixels[yy*8+xx]
                    if v and 0<=x+xx<240 and 0<=y+yy<320:expected[(y+yy)*240+x+xx]=[0,0xf800,0][v]
            for full in (False,True):
                self.lib.sprite_host_begin(full)
                self.assertTrue(self.lib.sprite_host_crop(C.byref(a),0,x,y,sx,sy,w,h))
                self.lib.sprite_host_flush(out);self.assertEqual(list(out),expected)
        for sx,sy,w,h in [(-1,0,1,1),(0,-1,1,1),(8,0,1,1),(0,5,1,1),(0,0,0,1),(0,0,1,0),(0,0,9,1),(0,0,1,6),(2147483647,0,1,1)]:
            self.lib.sprite_host_begin(0)
            self.assertFalse(self.lib.sprite_host_crop(C.byref(a),0,0,0,sx,sy,w,h))
            self.lib.sprite_host_flush(out);self.assertEqual(list(out),[0x1357]*(240*320))

    def test_decoder_rejects_malformed_streams_and_bounds(self):
        def make(data=b'\x04\x01', rows=None, keys=None):
            return asset_for([0, 0xffff], {'width': 4, 'height': 1, 'keys': keys or [0],
                             'rows': rows or [0, len(data)], 'data': data})
        out = (C.c_uint8 * 8)(*([173] * 8))
        for asset in [make(b'\x00\x01'), make(b'\x05\x01'), make(b'\x03\x01'),
                      make(b'\x04\x02'), make(b'\x04\x40'), make(b'\x04'), make(rows=[0, 99]),
                      make(rows=[2, 0]), make(keys=[1])]:
            self.assertFalse(self.lib.adv_sprite_row(C.byref(asset), 0, 0, out, 8))
            self.assertEqual(list(out[4:]), [173] * 4)
        valid = make()
        for f, y, cap in [(1, 0, 8), (0, 1, 8), (0, 0, 3)]:
            self.assertFalse(self.lib.adv_sprite_row(C.byref(valid), f, y, out, cap))
        self.assertFalse(self.lib.adv_sprite_row(None, 0, 0, out, 8))
        valid.row_count = 1
        self.assertFalse(self.lib.adv_sprite_frame_valid(C.byref(valid), 0))
        long_chain = make(b'\x04\x01' * 9, rows=list(range(0, 18, 2)) + [18] * 9, keys=[0] * 9)
        self.assertFalse(self.lib.adv_sprite_frame_valid(C.byref(long_chain), 8))

    def test_generator_rejects_invalid_inputs(self):
        for images in [[], [Image.new('RGBA', (257, 1))],
                       [Image.new('RGBA', (1, 1)), Image.new('RGBA', (2, 1))]]:
            with self.assertRaises(ValueError): packer.index_frames(images)
        with self.assertRaises(ValueError): packer.generate([], self.folder / 'bad', 'bad;code')


if __name__ == '__main__':
    unittest.main()
