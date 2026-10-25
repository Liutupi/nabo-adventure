#!/usr/bin/env python3
"""Pack target-size RGBA PNGs into flash-backed RGB565 row RLE sprites.

No art is generated. All frames share <=63 opaque colours plus transparency.
Lossy quantization precedes packing; verification is exact against those indexed
frames, not against the original full-colour PNG. Partial alpha requires an
explicit matte. Output: <output>.c, .h and an auditable .json packing report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image

MAX_SIDE, KEY_INTERVAL, INHERIT = 256, 8, 64


def pixels_of(image):
    # Support the repository's unpinned Pillow on both older and newer hosts.
    return image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata()


def rgb565(rgb):
    r, g, b = rgb
    return (r >> 3) << 11 | (g >> 2) << 5 | b >> 3


def rgb888(value):
    return ((value >> 11) * 255 // 31, (value >> 5 & 63) * 255 // 63, (value & 31) * 255 // 31)


def index_frames(images, background=None):
    """Quantize once for the entire clip; transparent pixels never consume colour slots."""
    if not images or len(images) > 65535:
        raise ValueError('expected 1..65535 frames')
    w, h = images[0].size
    if not (1 <= w <= MAX_SIDE and 1 <= h <= MAX_SIDE) or any(im.size != (w, h) for im in images):
        raise ValueError('frames must share a target canvas of 1..256 pixels per side')
    if w * h * len(images) > 16 * 1024 * 1024:
        raise ValueError('clip exceeds the 16-million-pixel packing limit; split the clip')
    pixels, opaque = [], set()
    for image in images:
        values = []
        for r, g, b, a in pixels_of(image.convert('RGBA')):
            if a == 0:
                values.append(None)
                continue
            if a < 255:
                if background is None:
                    raise ValueError('partial alpha requires --background #RRGGBB')
                r, g, b = ((c * a + bg * (255 - a) + 127) // 255
                           for c, bg in zip((r, g, b), background))
            value = rgb565((r, g, b))
            values.append(value)
            opaque.add(value)
        pixels.append(values)
    colours = sorted(opaque)
    if len(colours) > 63:
        # Sorted samples make the shared palette independent of frame order.
        sample = Image.new('RGB', (len(colours), 1))
        sample.putdata([rgb888(c) for c in colours])
        quantized = sample.quantize(colors=63, method=Image.Quantize.MEDIANCUT,
                                    dither=Image.Dither.NONE).convert('RGB')
        colours = sorted({rgb565(c) for c in pixels_of(quantized)})
    palette = [0] + colours
    lookup = {}
    for value in sorted(opaque):
        rgb = rgb888(value)
        lookup[value] = 1 + min(range(len(colours)), key=lambda i: sum(
            (a - b) ** 2 for a, b in zip(rgb, rgb888(colours[i]))))
    return palette, [bytes(0 if v is None else lookup[v] for v in frame) for frame in pixels]


def rle(row):
    result = bytearray()
    x = 0
    while x < len(row):
        end = x + 1
        while end < len(row) and row[end] == row[x] and end - x < 255:
            end += 1
        result.extend((end - x, row[x]))
        x = end
    return bytes(result)


def pack(width, height, frames):
    if not 1 <= width <= MAX_SIDE or not 1 <= height <= MAX_SIDE or not 1 <= len(frames) <= 65535:
        raise ValueError('invalid clip dimensions or frame count')
    if any(len(frame) != width * height or any(v >= 64 for v in frame) for frame in frames):
        raise ValueError('incorrect indexed frame size')
    keys, rows, data = [], [], bytearray()
    key = 0
    for f, frame in enumerate(frames):
        full = [rle(frame[y * width:(y + 1) * width]) for y in range(height)]
        encoded = full
        if f and f - key < KEY_INTERVAL:
            delta = bytes(INHERIT if a == b else a for a, b in zip(frame, frames[f - 1]))
            diff = [rle(delta[y * width:(y + 1) * width]) for y in range(height)]
            if sum(map(len, diff)) < sum(map(len, full)):
                encoded = diff
            else:
                key = f
        else:
            key = f
        keys.append(key)
        for row in encoded:
            rows.append(len(data))
            data.extend(row)
        rows.append(len(data))
    return {'width': width, 'height': height, 'keys': keys, 'rows': rows, 'data': bytes(data)}


def decode(asset, frame):
    """Independent reference unpacker used by the generator's mandatory round trip."""
    w, h = asset['width'], asset['height']
    result = bytearray(w * h)
    for f in range(asset['keys'][frame], frame + 1):
        for y in range(h):
            row = f * (h + 1) + y
            start, end = asset['rows'][row:row + 2]
            x = 0
            for p in range(start, end, 2):
                count, value = asset['data'][p:p + 2]
                if value != INHERIT:
                    result[y * w + x:y * w + x + count] = bytes([value]) * count
                x += count
            if x != w:
                raise ValueError('RLE row has the wrong width')
    return bytes(result)


def c_array(ctype, name, values):
    lines = [f'static const {ctype} {name}[] = {{']
    for i in range(0, len(values), 20):
        lines.append('    ' + ', '.join(str(v) for v in values[i:i + 20]) + ',')
    return '\n'.join(lines + ['};'])


def generate(paths, output, name, background=None):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
        raise ValueError('name must be a C identifier beginning with a letter')
    output = Path(output)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', output.name):
        raise ValueError('output basename must contain only letters, digits, hyphen or underscore')
    images = []
    for path in paths:
        with Image.open(path) as image:
            images.append(image.convert('RGBA'))
    palette, frames = index_frames(images, background)
    w, h = images[0].size
    asset = pack(w, h, frames)
    for f, expected in enumerate(frames):
        if decode(asset, f) != expected:
            raise ValueError(f'packed frame {f} differs from the indexed reference')
    report = {
        'format': 'adv-row-rle-v1', 'name': name, 'width': w, 'height': h,
        'palette_rgb565': palette, 'background_rgb888': background,
        'key_interval': KEY_INTERVAL, 'keys': asset['keys'],
        'data_bytes': len(asset['data']),
        'table_bytes': len(palette) * 2 + len(asset['keys']) * 2 + len(asset['rows']) * 4,
        'frame_sha256': [hashlib.sha256(frame).hexdigest() for frame in frames],
        'source_sha256': [hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths],
        'verified_frames': len(frames), 'comparison': 'lossless after shared RGB565 quantization',
    }
    # All verification completes before any deliverable is written.
    output.parent.mkdir(parents=True, exist_ok=True)
    header = f'#pragma once\n#include "adv_sprite.h"\nextern const adv_sprite_t {name};\n'
    source = [f'// Generated by tools/generate_adv_sprites.py; do not edit.\n#include "{output.name}.h"']
    for ctype, suffix, values in [('uint16_t', 'palette', palette), ('uint16_t', 'keys', asset['keys']),
                                   ('uint32_t', 'rows', asset['rows']), ('uint8_t', 'data', asset['data'])]:
        source.append(c_array(ctype, f'{name}_{suffix}', values))
    source.append(f'const adv_sprite_t {name} = {{\n'
                  f'    {w}, {h}, {len(frames)}, {len(palette)}, {len(asset["rows"])}, {len(asset["data"])},\n'
                  f'    {name}_palette, {name}_keys, {name}_rows, {name}_data\n}};\n')
    Path(str(output) + '.h').write_text(header, encoding='utf-8')
    Path(str(output) + '.c').write_text('\n'.join(source), encoding='utf-8')
    Path(str(output) + '.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def matte(value):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise argparse.ArgumentTypeError('expected #RRGGBB')
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('frames', type=Path, nargs='+', help='target-size PNGs in playback order')
    parser.add_argument('--output', type=Path, required=True, help='output basename without extension')
    parser.add_argument('--name', required=True, help='C asset symbol')
    parser.add_argument('--background', type=matte, help='explicit matte for partial alpha, e.g. #183040')
    args = parser.parse_args()
    try:
        report = generate(args.frames, args.output, args.name, args.background)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f'Verified {report["verified_frames"]} frames; palette {len(report["palette_rgb565"])}; '
          f'RLE {report["data_bytes"]} B + tables {report["table_bytes"]} B')


if __name__ == '__main__':
    main()
