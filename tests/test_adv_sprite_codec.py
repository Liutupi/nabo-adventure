"""Actual production C/Python row codec: compatibility, optimality and bounds."""
import ctypes as C
import itertools
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from host_tools import CC, SHARED_EXPORT, unload_library
from test_adv_sprites import Asset, asset_for, packer

ROOT = Path(__file__).resolve().parents[1]


def row(width, data, keys=None, rows=None):
    return dict(width=width, height=1, keys=keys if keys is not None else [0],
                rows=rows if rows is not None else [0, len(data)], data=bytes(data))


def minimum_row_bytes(values):
    """Slow exhaustive-token DP oracle, independent of the production queue."""
    costs = [0] * (len(values) + 1)
    for x in range(len(values) - 1, -1, -1):
        candidates = [2 + k + costs[x + k] for k in range(1, min(255, len(values) - x) + 1)]
        for k in range(1, min(255, len(values) - x) + 1):
            if values[x + k - 1] != values[x]:
                break
            candidates.append(2 + costs[x + k])
        costs[x] = min(candidates)
    return costs[0]


class LiteralCodec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        output = Path(cls.tmp.name) / 'codec.dll'
        board = ROOT / 'firmware/main'
        subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-I', str(board), str(board / 'adv_sprite.c'), '-o', str(output)], check=True)
        cls.lib = C.CDLL(str(output))
        cls.lib.adv_sprite_row.argtypes = [C.POINTER(Asset), C.c_uint, C.c_uint, C.POINTER(C.c_uint8), C.c_size_t]
        cls.lib.adv_sprite_row.restype = C.c_bool

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def check(self, packed, valid, palette_size=64, frame=0, y=0, capacity=None, mutate=None):
        asset = asset_for(list(range(palette_size)), packed)
        if mutate:
            mutate(asset)
        capacity = packed['width'] if capacity is None else capacity
        buffer = (C.c_uint8 * (packed['width'] + 4))(*([173] * (packed['width'] + 4)))
        out = C.cast(C.byref(buffer, 2), C.POINTER(C.c_uint8))
        accepted = self.lib.adv_sprite_row(C.byref(asset), frame, y, out, capacity)
        self.assertEqual(accepted, valid)
        self.assertEqual(list(buffer[:2]) + list(buffer[-2:]), [173] * 4)
        if capacity < packed['width']:
            self.assertEqual(list(buffer), [173] * len(buffer))
        if mutate is None:
            if valid:
                expected = packer.decode_row(packed, frame, y, palette_size, capacity)
                self.assertEqual(bytes(buffer[2:-2]), expected)
                return expected
            with self.assertRaises(ValueError):
                packer.decode_row(packed, frame, y, palette_size, capacity)

    def test_legacy_run_streams_remain_byte_exact(self):
        packed = row(4, [4, 1, 1, 0, 3, 64], keys=[0, 0], rows=[0, 2, 2, 6])
        self.assertEqual(self.check(packed, True, 2, frame=0), b'\x01' * 4)
        self.assertEqual(self.check(packed, True, 2, frame=1), b'\x00\x01\x01\x01')
        self.assertEqual(packer.rle(b'\x01' * 256), b'\xff\x01\x01\x01')

    def test_literals_odd_spans_transparency_and_delta_inheritance(self):
        cases = [row(1, [0, 1, 0]), row(3, [0, 3, 1, 0, 2]),
                 row(255, [0, 255, *[i % 64 for i in range(255)]]),
                 row(256, [0, 255, *[i % 64 for i in range(255)], 1, 3]),
                 row(256, [100, 1, 0, 5, 3, 2, 0, 1, 2, 151, 0])]
        for packed in cases:
            with self.subTest(width=packed['width'], size=len(packed['data'])):
                self.check(packed, True)
        packed = row(3, [0, 3, 1, 2, 3, 0, 3, 64, 0, 64], keys=[0, 0], rows=[0, 5, 5, 10])
        self.assertEqual(self.check(packed, True, 4, frame=1), b'\x01\x00\x03')

    def test_rejects_truncation_overflow_and_palette_errors(self):
        cases = [(1, [0, 0]), (3, [0, 3, 1, 2]), (1, [0]), (1, [1]),
                 (3, [0, 4, 1, 2, 3, 0]), (3, [0, 2, 1, 2]), (3, [4, 1]),
                 (2, [0, 2, 1, 65]), (2, [0, 2, 1, 255]), (1, [1, 1, 9]),
                 (1, [1, 1, 0, 1, 0]), (1, [0, 1, 64]), (1, [1, 64])]
        for width, data in cases:
            with self.subTest(width=width, data=data):
                self.check(row(width, data), False)
        for data in ([0, 2, 1, 3], [2, 3]):
            self.check(row(2, data), False, 3)
        for offsets in ([0, 4], [3, 2], [0, 6]):
            self.check(row(3, [0, 3, 1, 2, 3], rows=offsets), False)

    def test_metadata_key_chain_and_capacity_fail_without_overrun(self):
        for capacity in (0, 2):
            self.check(row(3, [3, 1]), False, capacity=capacity)
        self.check(row(3, [3, 1]), False, frame=1)
        self.check(row(3, [3, 1]), False, y=1)
        for size in (0, 65):
            self.check(row(3, [3, 1]), False, size)
        for pointer in ('palette', 'keys', 'rows', 'data'):
            self.check(row(3, [3, 1]), False, mutate=lambda a, p=pointer: setattr(a, p, None))
        self.check(row(3, [3, 1]), False, mutate=lambda a: setattr(a, 'row_count', 1))
        self.check(row(3, [3, 1]), False, mutate=lambda a: setattr(a, 'data_size', 1))
        self.check(row(1, [1, 1] * 9, keys=[0] * 9,
                       rows=[v for i in range(9) for v in (i * 2, i * 2 + 2)]), False, frame=8)
        self.check(row(1, [1, 1] * 3, keys=[0, 1, 0], rows=[0, 2, 2, 4, 4, 6]), False, frame=2)
        self.check(row(1, [1, 1] * 2, keys=[1, 0], rows=[0, 2, 2, 4]), False, frame=1)
        self.check(row(1, [1, 1], keys=[1]), False)
        self.assertFalse(self.lib.adv_sprite_row(None, 0, 0, None, 0))
        for height in (0, 257):
            with self.assertRaises(ValueError):
                packer.decode(dict(row(1, [1, 1]), height=height), 0)

    def test_optimal_row_encoder_matches_exhaustive_cost_oracle(self):
        rng = random.Random(303)
        values = [bytes(bits) for n in range(1, 10) for bits in itertools.product(range(2), repeat=n)]
        values += [bytes(rng.randrange(65) for _ in range(rng.randint(1, 256))) for _ in range(240)]
        values += [bytes([3] * 255 + [4]), bytes([3] * 256), bytes(range(64)) * 4]
        for value in values:
            encoded = packer.rle(value)
            self.assertEqual(len(encoded), minimum_row_bytes(value))
            if len(encoded) == len(packer._rle_legacy(value)):
                self.assertEqual(encoded, packer._rle_legacy(value))
            if 64 not in value:
                self.check(row(len(value), encoded), True)

    def test_key_partition_matches_all_legal_partitions(self):
        rng = random.Random(88)
        frames = [bytes(rng.randrange(6) for _ in range(12))]
        for f in range(1, 12):
            pixels = bytearray(frames[-1] if f != 5 else frames[0])
            pixels[f % 12] = f % 6
            frames.append(bytes(pixels))
        full = [len(packer.rle(f)) for f in frames]
        delta = [0] + [len(packer.rle(bytes(64 if a == b else b for a, b in zip(p, c))))
                       for p, c in zip(frames, frames[1:])]
        sizes = []
        for mask in range(1 << (len(frames) - 1)):
            key, size = 0, full[0]
            for f in range(1, len(frames)):
                if mask & (1 << (f - 1)):
                    key = f
                    size += full[f]
                else:
                    size += delta[f]
                if f - key >= packer.KEY_INTERVAL:
                    break
            else:
                sizes.append(size)
        packed = packer.pack(12, 1, frames)
        self.assertEqual(len(packed['data']), min(sizes))
        for f, pixels in enumerate(frames):
            self.assertEqual(self.check(packed, True, 6, frame=f), pixels)

    def test_deterministic_mutations_match_production_python_and_C(self):
        rng = random.Random(20261025)
        for _ in range(2400):
            width, palette = rng.randint(1, 256), rng.randint(1, 64)
            data = bytearray(packer.rle(bytes(rng.randrange(palette) for _ in range(width))))
            if rng.randrange(4):
                action = rng.randrange(3)
                if action == 0:
                    data[rng.randrange(len(data))] = rng.randrange(256)
                elif action == 1:
                    del data[rng.randrange(len(data)):]
                else:
                    data.extend(rng.randbytes(rng.randint(1, 4)))
            packed = row(width, data)
            try:
                packer.decode_row(packed, 0, 0, palette)
                valid = True
            except ValueError:
                valid = False
            self.check(packed, valid, palette)


if __name__ == '__main__':
    unittest.main()
