"""Publication guards catch substitutions, private partitions and unsafe ZIP members."""
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_release import safe_member,verify_padding,frozen_write,sha
from verify_release import parse_sums

class ReleaseGuards(unittest.TestCase):
    def test_rejects_archive_traversal_and_absolute_names(self):
        for name in ('../app.bin','/app.bin','C:/app.bin','tools\\app.py'):
            with self.subTest(name=name),self.assertRaises(ValueError):safe_member(name)

    def test_rejects_private_payload_paths(self):
        for name in ('private/before.bin','backups/device.bin','NVS/keys.json','credentials/key'):
            with self.subTest(name=name),self.assertRaises(ValueError):safe_member(name)

    def test_checksum_manifest_rejects_duplicate_and_bad_hash(self):
        for raw in ((('a'*64+'  app.bin\n')*2).encode(),b'bad  app.bin\n'):
            with self.assertRaises(ValueError):parse_sums(raw)

    def test_blank_partition_gaps_are_accepted(self):
        verify_padding(b'BOOT'+b'\xff'*12+b'APP',[(0,b'BOOT'),(16,b'APP')])

    def test_private_bytes_inside_partition_gaps_are_rejected(self):
        with self.assertRaises(ValueError):verify_padding(b'BOOT'+b'NVS'+b'\xff'*9+b'APP',[(0,b'BOOT'),(16,b'APP')])

    def test_substituted_app_and_trailing_device_data_are_rejected(self):
        for blob in (b'BOOT'+b'\xff'*12+b'BAD',b'BOOT'+b'\xff'*12+b'APPPRIVATE'):
            with self.assertRaises(ValueError):verify_padding(blob,[(0,b'BOOT'),(16,b'APP')])

    def test_overlapping_flash_inputs_are_rejected(self):
        with self.assertRaises(ValueError):verify_padding(b'BOOTAPP',[(0,b'BOOT'),(3,b'TAPP')])

    def test_frozen_package_is_idempotent_and_refuses_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'app.bin';frozen_write(p,b'accepted');frozen_write(p,b'accepted')
            with self.assertRaises(ValueError):frozen_write(p,b'rebuilt')
            self.assertEqual(sha(p.read_bytes()),sha(b'accepted'))
