"""Pre-write checks must reject wrong images, identities and partition layouts."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'firmware/tools'))
from flash_candidate import APP_SIZE, EXPECTED, check_device, validate_app, validate_layout
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
