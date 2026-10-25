"""Pre-write checks must reject wrong images, identities and partition layouts."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'firmware/tools'))
from flash_candidate import (APP_SIZE, EXPECTED, FLASH_SIZE, LEGACY_EXPECTED, CANONICAL, LEGACY,
                             check_device, protected_ranges, validate_app, validate_layout, verify_preserved)
from verify_firmware import validate_flash_size

def table(entries):
    raw = b''.join(struct.pack('<HBBII16sI', 0x50aa, k, s, offset, size, name.encode(), flags)
                   for name, k, s, offset, size, flags in entries)
    raw += b'\xeb\xeb' + b'\xff'*14 + hashlib.md5(raw).digest()
    return raw.ljust(4096, b'\xff')

class Device:
    CHIP_NAME = 'ESP32-C3'
    def __init__(self):
        self.mac = bytes.fromhex('010203040506')
        self.secure = False
        self.crypt = 0
        self.size_code = 0x17
    def read_mac(self): return self.mac
    def get_security_info(self):
        return {'parsed_flags': {'SECURE_BOOT_EN': self.secure}, 'flash_crypt_cnt': self.crypt}
    def flash_id(self): return self.size_code << 16

class Guard(unittest.TestCase):
    def image(self, size=256, chip=5):
        data = bytearray(size); data[0] = 0xe9; struct.pack_into('<H', data, 12, chip)
        return bytes(data)

    def test_valid_c3_image_passes_and_changed_bytes_do_not(self):
        image = self.image(); sha = hashlib.sha256(image).hexdigest()
        validate_app(image, sha)
        changed = bytearray(image); changed[100] = 1
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'): validate_app(bytes(changed), sha)

    def test_wrong_chip_and_oversize_image_are_rejected(self):
        for data in (self.image(chip=9), self.image(APP_SIZE+1)):
            with self.assertRaises(ValueError): validate_app(data, hashlib.sha256(data).hexdigest())

    def test_exact_compatible_layout_is_required(self):
        entries = [(name, *values, 0) for name, values in EXPECTED.items()]
        validate_layout(table(entries))
        wrong = entries.copy(); name, k, s, offset, _, flags = wrong[2]
        wrong[2] = (name, k, s, offset, 0x7f0000, flags)
        with self.assertRaises(ValueError): validate_layout(table(wrong))

    def test_exact_legacy_profile_is_accepted_without_changing_canonical(self):
        for expected, profile in ((EXPECTED, CANONICAL), (LEGACY_EXPECTED, LEGACY)):
            entries = [(name, *values, 0) for name, values in expected.items()]
            self.assertEqual(validate_layout(table(entries)), profile)
        self.assertEqual(protected_ranges(CANONICAL), ((0, 0x10000), (0x400000, FLASH_SIZE)))
        self.assertEqual(protected_ranges(LEGACY), ((0, 0x10000), (0x200000, FLASH_SIZE)))

    def test_legacy_app_size_and_rounded_erase_end_use_actual_factory(self):
        # A canonical-size candidate must still be rejected on the smaller real device.
        too_large = self.image(LEGACY.app_size + 1)
        sha = hashlib.sha256(too_large).hexdigest()
        validate_app(too_large, sha, CANONICAL)
        with self.assertRaises(ValueError): validate_app(too_large, sha, LEGACY)
        for size in (LEGACY.app_size, LEGACY.app_size - 4095):
            data = self.image(size)
            self.assertEqual(validate_app(data, hashlib.sha256(data).hexdigest(), LEGACY), 0x200000)
        data = self.image(LEGACY.app_size - 4096)
        self.assertEqual(validate_app(data, hashlib.sha256(data).hexdigest(), LEGACY), 0x1ff000)

    def test_every_legacy_partition_field_difference_is_rejected(self):
        entries = [(name, *values, 0) for name, values in LEGACY_EXPECTED.items()]
        for index, entry in enumerate(entries):
            # label, type, subtype, offset, size, flags: no approximate layouts.
            for field in range(6):
                changed = list(entry)
                changed[field] = 'other' if field == 0 else changed[field] + 1
                wrong = entries.copy(); wrong[index] = tuple(changed)
                with self.subTest(partition=entry[0], field=field), self.assertRaises(ValueError):
                    validate_layout(table(wrong))
        for wrong in (entries[:-1], entries + [('files', 1, 0x82, 0x700000, 0x100000, 0)]):
            with self.assertRaises(ValueError): validate_layout(table(wrong))

    def test_legacy_readback_protects_every_byte_after_real_factory_end(self):
        before = bytes(FLASH_SIZE)
        after = bytearray(before)
        after[0x10000:0x10004] = b'app!'
        verify_preserved(before, after, LEGACY)
        # Especially the legacy-only 0x200000..0x400000 protected range.
        for address in (0, 0x9000, 0xffff, 0x200000, 0x300000, FLASH_SIZE - 1):
            changed = bytearray(after); changed[address] = 1
            with self.subTest(address=address), self.assertRaisesRegex(ValueError, 'Preserved region'):
                verify_preserved(before, changed, LEGACY)
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            verify_preserved(before, after[:-1], LEGACY)

    def test_encrypted_partition_and_corrupt_table_are_rejected(self):
        entries = [(name, *values, int(name == 'nvs')) for name, values in EXPECTED.items()]
        with self.assertRaisesRegex(ValueError, 'flagged'): validate_layout(table(entries))
        raw = bytearray(table([(name, *values, 0) for name, values in EXPECTED.items()]))
        raw[20] ^= 1
        with self.assertRaises(ValueError): validate_layout(raw)

    def test_identity_is_checked_before_any_write_can_be_selected(self):
        device = Device(); check_device(device, '01:02:03:04:05:06')
        with self.assertRaisesRegex(ValueError, 'MAC'): check_device(device, '11:22:33:44:55:66')
        device.CHIP_NAME = 'ESP32-S3'
        with self.assertRaisesRegex(ValueError, 'chip'): check_device(device, '01:02:03:04:05:06')

    def test_security_and_flash_size_are_hard_limits(self):
        for field, value in (('secure', True), ('crypt', 1), ('size_code', 0x16)):
            device = Device(); setattr(device, field, value)
            with self.assertRaises(ValueError): check_device(device, '01:02:03:04:05:06')

    def test_both_official_flash_size_spellings_are_supported(self):
        for flag in ('--flash_size', '--flash-size'):
            validate_flash_size(flag+' 8MB\n0x10000 app.bin')
        for raw in ('--flash-size 4MB', '', '--flash-size 8MB --flash-size 4MB'):
            with self.assertRaises(ValueError): validate_flash_size(raw)

if __name__ == '__main__':
    unittest.main(verbosity=2)
