"""Guarded app-only installer. Inspect by default; never erase or rewrite partitions.

Use the ESP-IDF Python environment (esptool 5.5). Backups and receipts are private.
Device identity is checked on the same serial connection that performs the write.
"""
import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
from verify_firmware import parse_partition_table

FLASH_SIZE = 0x800000
APP_OFFSET = 0x10000
APP_SIZE = 0x3f0000
EXPECTED = {'nvs': (1, 2, 0x9000, 0x6000), 'phy_init': (1, 1, 0xf000, 0x1000),
            'factory': (0, 0, APP_OFFSET, APP_SIZE), 'assets': (1, 0x82, 0x400000, 0x300000),
            'files': (1, 0x82, 0x700000, 0x100000)}
LEGACY_EXPECTED = {'nvs': (1, 2, 0x9000, 0x6000), 'phy_init': (1, 1, 0xf000, 0x1000),
                   'factory': (0, 0, APP_OFFSET, 0x1f0000), 'assets': (1, 0x41, 0x200000, 0x600000)}

@dataclass(frozen=True)
class LayoutProfile:
    name: str
    partitions: dict

    @property
    def app_offset(self): return self.partitions['factory'][2]

    @property
    def app_size(self): return self.partitions['factory'][3]

    @property
    def app_end(self): return self.app_offset + self.app_size

CANONICAL = LayoutProfile('canonical_4m_app', EXPECTED)
LEGACY = LayoutProfile('legacy_2m_app_6m_assets', LEGACY_EXPECTED)
LAYOUT_PROFILES = (CANONICAL, LEGACY)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_app(data, expected_hash, layout=CANONICAL):
    if not re.fullmatch('[0-9a-f]{64}', expected_hash):
        raise ValueError('An explicit lowercase SHA256 is required')
    if layout not in LAYOUT_PROFILES:
        raise ValueError('Unrecognized layout profile')
    if len(data) < 256 or len(data) > layout.app_size or data[0] != 0xe9:
        raise ValueError('Invalid app size or image header')
    if struct.unpack_from('<H', data, 12)[0] != 5:
        raise ValueError('Only an ESP32-C3 application is supported')
    if digest(data) != expected_hash:
        raise ValueError('Candidate SHA256 mismatch; no write allowed')
    erased_end = layout.app_offset + ((len(data) + 4095) // 4096) * 4096
    if erased_end > layout.app_end:
        raise ValueError('Erase sectors overlap the preserved resource partition')
    return erased_end

def validate_layout(raw):
    parts, md5 = parse_partition_table(raw)
    if not md5:
        raise ValueError('Unrecognized partition table')
    actual = {p.label: (p.kind, p.subtype, p.offset, p.size) for p in parts}
    layout = next((profile for profile in LAYOUT_PROFILES
                   if len(parts) == len(profile.partitions) and actual == profile.partitions), None)
    if layout is None:
        raise ValueError('Device layout differs; app-only upgrade refused')
    for cursor in range(0, len(parts) * 32, 32):
        if struct.unpack_from('<I', raw, cursor + 28)[0]:
            raise ValueError('Encrypted/flagged partitions are unsupported')
    return layout

def protected_ranges(layout):
    return ((0, layout.app_offset), (layout.app_end, FLASH_SIZE))

def verify_preserved(backup, after, layout):
    if len(backup) != FLASH_SIZE or len(after) != FLASH_SIZE:
        raise ValueError('Incomplete full-flash comparison')
    for start, end in protected_ranges(layout):
        if backup[start:end] != after[start:end]:
            raise ValueError(f'Preserved region changed: {start:#x}..{end:#x}')

def check_device(esp, expected_mac):
    mac = ':'.join(f'{b:02x}' for b in esp.read_mac())
    if mac != expected_mac or esp.CHIP_NAME.lower().replace('-', '') != 'esp32c3':
        raise ValueError('Wrong device MAC/chip; no write allowed')
    security = esp.get_security_info()
    if security['parsed_flags']['SECURE_BOOT_EN'] or int(security['flash_crypt_cnt']).bit_count() % 2:
        raise ValueError('Secure boot or flash encryption is enabled; no write allowed')
    if (esp.flash_id() >> 16) & 255 != 0x17:
        raise ValueError('Exactly 8 MB flash is required')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--app', type=Path, required=True)
    ap.add_argument('--sha256', required=True)
    ap.add_argument('--mode', choices=('inspect', 'backup', 'upgrade'), default='inspect')
    ap.add_argument('--port')
    ap.add_argument('--expected-mac')
    ap.add_argument('--private-dir', type=Path, default=Path('private/device'))
    args = ap.parse_args()
    data = args.app.read_bytes()
    validate_app(data, args.sha256)
    print(f'Candidate verified: {len(data)} bytes; SHA256 {digest(data)}', flush=True)
    if args.mode == 'inspect': return
    if not args.port or not args.expected_mac or not re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}', args.expected_mac):
        ap.error('Device operations require --port and a lowercase --expected-mac')
    import esptool
    from esptool import cmds
    if esptool.__version__ != '5.5.0': raise ValueError('This installer is verified with esptool 5.5.0')
    private = args.private_dir.resolve()
    private.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    receipt_path = private/f'{stamp}-receipt.json'
    backup_path = private/f'{stamp}-before.bin'
    receipt = {'device_mac': args.expected_mac, 'port': args.port, 'app_sha256': digest(data),
               'app_bytes': len(data), 'status': 'NO WRITE', 'mode': args.mode}
    def save(): receipt_path.write_text(json.dumps(receipt, indent=2)+'\n', 'utf-8')
    write_attempted = False
    with cmds.detect_chip(args.port, 460800) as rom:
        esp = cmds.run_stub(rom)
        try:
            check_device(esp, args.expected_mac)
            table = cmds.read_flash(esp, 0x8000, 0x1000, no_progress=True)
            layout = validate_layout(table)
            receipt.update(layout_profile=layout.name, layout=layout.partitions,
                           app_offset=layout.app_offset, app_partition_size=layout.app_size,
                           app_partition_end=layout.app_end,
                           protected_regions=[{'start': start, 'end': end} for start, end in protected_ranges(layout)])
            erased_end = validate_app(data, args.sha256, layout)
            receipt['app_erase_end'] = erased_end
            print(f'Identity, security and exact {layout.name} partition map verified; '
                  f'factory {layout.app_offset:#x}..{layout.app_end:#x}. Reading full private backup...', flush=True)
            backup = cmds.read_flash(esp, 0, FLASH_SIZE, no_progress=True)
            if len(backup) != FLASH_SIZE: raise ValueError('Incomplete backup')
            backup_path.write_bytes(backup)
            if backup_path.read_bytes() != backup: raise ValueError('Backup disk verification failed')
            cmds.verify_flash(esp, [(0, backup)])
            receipt.update(backup_file=backup_path.name, backup_sha256=digest(backup), status='BACKUP VERIFIED; NO WRITE')
            save()
            if args.mode == 'backup':
                cmds.reset_chip(esp); print('PASS: backup verified; original firmware restarted', flush=True); return
            # Recheck immediately before writing, on the same open connection.
            check_device(esp, args.expected_mac)
            print(f'Writing only application at {layout.app_offset:#x}; boot/NVS/PHY and '
                  f'all bytes from {layout.app_end:#x} remain protected...', flush=True)
            write_attempted = True
            cmds.write_flash(esp, [(layout.app_offset, data)], flash_mode='keep', flash_freq='keep', flash_size='keep')
            cmds.verify_flash(esp, [(layout.app_offset, data)])
            print('Reading full flash back to compare application and every protected byte...', flush=True)
            after = cmds.read_flash(esp, 0, FLASH_SIZE, no_progress=True)
            if len(after) != FLASH_SIZE or after[layout.app_offset:layout.app_offset+len(data)] != data:
                raise ValueError('Application readback mismatch')
            verify_preserved(backup, after, layout)
            receipt.update(status='PASS: APP AND ALL PRESERVED BYTES VERIFIED; BOOT NOT YET OBSERVED',
                           preserved_sha256={'boot_nvs_phy': digest(after[:layout.app_offset]),
                                             'resources': digest(after[layout.app_end:])})
            save(); cmds.reset_chip(esp)
            print(f'PASS: restarted candidate; receipt {receipt_path.name}', flush=True)
        except Exception as error:
            receipt['status'] = 'STOPPED: ' + str(error)
            receipt['write_attempted'] = write_attempted
            save()
            if not write_attempted: cmds.reset_chip(esp)
            raise

if __name__ == '__main__':
    main()
