"""Execute the production zero-allocation WAV parser and one-shot PCM mixer."""
import ctypes
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import wave
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'firmware/main'


class Boot(ctypes.Structure):
    _fields_ = [('wav', ctypes.c_void_p), ('data_offset', ctypes.c_size_t),
                ('sample_count', ctypes.c_size_t), ('position', ctypes.c_size_t),
                ('start_ms', ctypes.c_uint32), ('started', ctypes.c_bool), ('active', ctypes.c_bool)]


def chunk(name, payload, pad=True):
    return name + struct.pack('<I', len(payload)) + payload + (b'\0' if pad and len(payload) & 1 else b'')


def riff(chunks):
    body = b'WAVE' + b''.join(chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


FMT = struct.pack('<HHIIHH', 1, 1, 16000, 32000, 2, 16)


def wav(samples, extra=()):
    data = struct.pack('<' + 'h' * len(samples), *samples)
    return riff([*extra, chunk(b'fmt ', FMT), chunk(b'data', data)])


class BootVoice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        library = Path(cls.tmp.name) / 'adv_boot.dll'
        subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-I', str(BOARD), str(BOARD / 'adv_boot.c'), '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.adv_boot_open.argtypes = [ctypes.POINTER(Boot), ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
        cls.lib.adv_boot_open.restype = ctypes.c_bool
        cls.lib.adv_boot_tick.argtypes = [ctypes.POINTER(Boot), ctypes.c_uint32]
        cls.lib.adv_boot_fill.argtypes = [ctypes.POINTER(Boot), ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t]
        cls.lib.adv_boot_stop.argtypes = [ctypes.POINTER(Boot)]
        cls.lib.adv_boot_elapsed.argtypes = [ctypes.POINTER(Boot), ctypes.c_uint32]
        cls.lib.adv_boot_elapsed.restype = ctypes.c_uint32

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def setUp(self):
        self.boot = Boot()
        self.buffers = []

    def open(self, data, start=100, unaligned=False):
        buffer = ctypes.create_string_buffer((b'x' if unaligned else b'') + data)
        self.buffers.append(buffer)  # Flash stand-in stays alive for the entire test.
        pointer = ctypes.addressof(buffer) + int(unaligned)
        return self.lib.adv_boot_open(ctypes.byref(self.boot), pointer, len(data), start)

    def tick(self, now):
        self.lib.adv_boot_tick(ctypes.byref(self.boot), now)

    def fill(self, cues):
        pcm = (ctypes.c_int16 * len(cues))(*cues)
        self.lib.adv_boot_fill(ctypes.byref(self.boot), pcm, len(cues))
        return list(pcm)

    def test_exact_delay_and_original_sample_values(self):
        samples = [0, 1, -1, 1000, -1000, 32767, -32768]
        self.assertTrue(self.open(wav(samples)))
        self.assertTrue(self.boot.active)
        self.assertEqual(self.fill([20, -20]), [20, -20])
        self.tick(1499)
        self.assertFalse(self.boot.started)
        self.assertEqual(self.fill([20, -20]), [20, -20])
        self.assertEqual(self.boot.position, 0)
        self.tick(1500)
        self.assertTrue(self.boot.started)
        self.assertEqual(self.boot.position, 0, 'Only fill advances PCM, not tick')
        self.assertEqual(self.fill([0] * len(samples)), samples)
        self.assertFalse(self.boot.active)

    def test_natural_completion_never_replays(self):
        self.assertTrue(self.open(wav([100, -200])))
        self.tick(1500)
        self.assertEqual(self.fill([0, 0, 701, -702]), [100, -200, 701, -702])
        self.tick(999999)
        self.assertEqual(self.fill([1234, -1234]), [1234, -1234])
        self.assertTrue(self.boot.started)
        self.assertEqual(self.boot.position, 2)
        self.assertEqual(self.lib.adv_boot_elapsed(ctypes.byref(self.boot), 3100), 3000)

    def test_stop_pending_playing_and_finished_clears_all_state(self):
        for state in ('pending', 'playing', 'finished'):
            with self.subTest(state=state):
                self.assertTrue(self.open(wav([123, -456])))
                if state != 'pending':
                    self.tick(1500)
                    self.fill([0] if state == 'playing' else [0, 0])
                self.lib.adv_boot_stop(ctypes.byref(self.boot))
                self.assertEqual(bytes(self.boot), bytes(Boot()))
                self.tick(100000)
                self.assertEqual(self.fill([800, -800]), [800, -800])
                self.assertEqual(self.lib.adv_boot_elapsed(ctypes.byref(self.boot), 100000), 0)

    def test_reopen_reinitializes_the_one_shot(self):
        for _ in range(2):
            self.assertTrue(self.open(wav([321]), start=5000))
            self.assertFalse(self.boot.started)
            self.tick(6399)
            self.assertEqual(self.fill([111]), [111])
            self.tick(6400)
            self.assertEqual(self.fill([0]), [321])

    def test_arbitrary_pcm_chunk_boundaries_match_fixture(self):
        samples = [i * 997 - 17000 for i in range(35)]
        for chunk_size in (1, 2, 3, 7, 16, 32, 320):
            with self.subTest(chunk_size=chunk_size):
                self.assertTrue(self.open(wav(samples)))
                self.tick(1500)
                actual = []
                while self.boot.active:
                    actual.extend(self.fill([0] * chunk_size))
                self.assertEqual(actual[:len(samples)], samples)
                self.assertTrue(all(value == 0 for value in actual[len(samples):]))
                self.assertEqual(self.boot.position, len(samples))

    def test_ducking_saturates_and_restores_the_unconsumed_cue_tail(self):
        self.assertTrue(self.open(wav([30000, -30000, 4, -4, 32767, -32768])))
        self.tick(1500)
        self.assertEqual(self.fill([20000, -20000, 7, -7, 4, -4, 123, -234]),
                         [32767, -32768, 5, -5, 32767, -32768, 123, -234])
        self.assertEqual(self.fill([32000, -32000]), [32000, -32000])

    def test_legal_unknown_zero_and_odd_padded_chunks_are_skipped(self):
        extras = [chunk(b'JUNK', b'abc'), chunk(b'LIST', b''), chunk(b'INFO', b'z')]
        data = riff([extras[0], chunk(b'fmt ', FMT), extras[1],
                     chunk(b'data', struct.pack('<hh', 123, -456)), extras[2]])
        self.assertTrue(self.open(data, unaligned=True))
        self.tick(1500)
        self.assertEqual(self.fill([0, 0]), [123, -456])
        self.assertTrue(self.open(riff([chunk(b'fmt ', FMT + b'\0\0'), chunk(b'data', b'\0\0')])))

    def test_clock_wrap_preserves_the_delay(self):
        start = 0xffffff00
        self.assertTrue(self.open(wav([123]), start=start))
        self.tick((start + 1399) & 0xffffffff)
        self.assertFalse(self.boot.started)
        self.tick((start + 1400) & 0xffffffff)
        self.assertTrue(self.boot.started)
        self.assertEqual(self.fill([0]), [123])

    def test_invalid_format_fields_and_short_or_inconsistent_fmt_are_rejected(self):
        wrong = [(3, 1, 16000, 32000, 2, 16), (1, 2, 16000, 32000, 2, 16),
                 (1, 1, 8000, 32000, 2, 16), (1, 1, 16000, 16000, 2, 16),
                 (1, 1, 16000, 32000, 4, 16), (1, 1, 16000, 32000, 2, 8)]
        formats = [struct.pack('<HHIIHH', *fields) for fields in wrong]
        formats += [FMT[:15], FMT + b'x', FMT + b'\x02\0']
        for fmt in formats:
            with self.subTest(fmt=fmt.hex()):
                self.assertFalse(self.open(riff([chunk(b'fmt ', fmt), chunk(b'data', b'\0\0')])))

    def test_bad_riff_truncation_duplicate_chunks_and_missing_or_odd_data_rejected(self):
        good = wav([12, -34])
        bodies = [b'', b'RIFF', good[:11], b'RIFX' + good[4:], good[:8] + b'NOPE' + good[12:],
                  good[:-1], good + b'\0', riff([chunk(b'fmt ', FMT)]),
                  riff([chunk(b'data', b'\0\0')]), riff([chunk(b'fmt ', FMT), chunk(b'data', b'')]),
                  riff([chunk(b'fmt ', FMT), chunk(b'data', b'x')]),
                  riff([chunk(b'fmt ', FMT), chunk(b'fmt ', FMT), chunk(b'data', b'\0\0')]),
                  riff([chunk(b'fmt ', FMT), chunk(b'data', b'\0\0'), chunk(b'data', b'\0\0')]),
                  riff([chunk(b'fmt ', FMT), b'data' + struct.pack('<I', 200) + b'\0\0']),
                  riff([chunk(b'fmt ', FMT), chunk(b'data', b'\0\0'), chunk(b'JUNK', b'abc', pad=False)]),
                  riff([chunk(b'fmt ', FMT), chunk(b'data', b'\0\0'), b'junk']),
                  riff([chunk(b'fmt ', FMT), b'JUNK' + struct.pack('<I', 0xffffffff)])]
        for index, data in enumerate(bodies):
            with self.subTest(case=index):
                self.assertTrue(self.open(good))
                self.assertFalse(self.open(data))
                self.assertEqual(bytes(self.boot), bytes(Boot()), 'Invalid replacement must cancel old audio')

    def test_null_context_storage_and_output_are_safe(self):
        self.assertFalse(self.lib.adv_boot_open(None, None, 0, 0))
        self.assertFalse(self.lib.adv_boot_open(ctypes.byref(self.boot), None, 44, 0))
        self.lib.adv_boot_tick(None, 1400)
        self.lib.adv_boot_stop(None)
        self.lib.adv_boot_fill(None, None, 0)
        self.assertEqual(self.lib.adv_boot_elapsed(None, 100), 0)
        self.assertTrue(self.open(wav([1])))
        self.tick(1500)
        self.lib.adv_boot_fill(ctypes.byref(self.boot), None, 10)
        self.assertEqual(self.boot.position, 0)

    def test_real_boot_clip_roundtrips_every_sample_when_available(self):
        path = ROOT / 'game-art/adventure/audio/boot-welcome.wav'
        if not path.exists():
            self.skipTest('Real project narration is not present in this checkout')
        data = path.read_bytes()
        self.assertTrue(self.open(data))
        with wave.open(str(path), 'rb') as source:
            self.assertEqual((source.getnchannels(), source.getframerate(), source.getsampwidth()), (1, 16000, 2))
            expected = source.readframes(source.getnframes())
        self.tick(1500)
        replay = []
        while self.boot.active:
            remaining = self.boot.sample_count - self.boot.position
            replay.extend(self.fill([0] * min(320, remaining)))
        actual = struct.pack('<' + 'h' * len(replay), *replay)
        self.assertEqual(hashlib.sha256(actual).digest(), hashlib.sha256(expected).digest())
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
