#!/usr/bin/env python3
"""Pack target-size RGBA PNGs into flash-backed RGB565 row RLE sprites.

No art is generated. All frames share <=63 opaque colours plus transparency.
Lossy quantization precedes packing; verification is exact against those indexed
frames, not against the original full-colour PNG. Partial alpha requires an
explicit matte. Output: <output>.c, .h and an auditable .json packing report.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re

from PIL import Image

MAX_SIDE, KEY_INTERVAL, INHERIT = 256, 8, 64
FORMAT = 'adv-row-rle-v3'  # uint16 row offsets; v1 runs and v2 literals remain readable.
MAX_DATA = 65535


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


def _rle_legacy(row):
    result = bytearray()
    x = 0
    while x < len(row):
        end = x + 1
        while end < len(row) and row[end] == row[x] and end - x < 255:
            end += 1
        result.extend((end - x, row[x]))
        x = end
    return bytes(result)


def rle(row):
    """Shortest run/literal mixture; keep v1 bytes when lengths tie.

    Backward DP chooses a run or a literal of at most 255 indices. Extending a
    same-value run costs nothing and cannot increase the remaining stream size.
    A monotone queue finds the cheapest literal suffix in linear time. Ties
    prefer runs, then longer tokens, so repeated builds produce identical bytes.
    """
    n = len(row)
    cost, choice, repeats = [0] * (n + 1), [None] * n, [1] * n
    suffixes = deque()
    for x in range(n - 1, -1, -1):
        if x + 1 < n and row[x] == row[x + 1]:
            repeats[x] = min(255, repeats[x + 1] + 1)
        j = x + 1
        candidate = (cost[j] + j, -j)
        while suffixes and suffixes[-1] >= candidate:
            suffixes.pop()
        suffixes.append(candidate)
        while -suffixes[0][1] > x + 255:
            suffixes.popleft()
        length = -suffixes[0][1] - x
        run = repeats[x]
        best = min((2 + cost[x + run], 0, -run),
                   (suffixes[0][0] + 2 - x, 1, -length))
        cost[x], kind, negative_length = best
        choice[x] = (kind, -negative_length)
    result, x = bytearray(), 0
    while x < n:
        literal, length = choice[x]
        if literal:
            result.extend((0, length))
            result.extend(row[x:x + length])
        else:
            result.extend((length, row[x]))
        x += length
    legacy = _rle_legacy(row)
    return bytes(result) if len(result) < len(legacy) else legacy


def pack(width, height, frames):
    """Choose minimum-byte key blocks without reordering any physical frames.

    A block is one key plus 0..7 deltas. Since each delta refers to the previous
    frame, its cost is independent of the block's start. DP tries all eight
    possible starts; row tables and descriptor size do not change.
    """
    if not 1 <= width <= MAX_SIDE or not 1 <= height <= MAX_SIDE or not 1 <= len(frames) <= 65535:
        raise ValueError('invalid clip dimensions or frame count')
    if any(len(frame) != width * height or any(v >= 64 for v in frame) for frame in frames):
        raise ValueError('incorrect indexed frame size')
    full, delta = [], [None]
    for f, frame in enumerate(frames):
        full.append([rle(frame[y * width:(y + 1) * width]) for y in range(height)])
        if f:
            pixels = bytes(INHERIT if a == b else a for a, b in zip(frame, frames[f - 1]))
            delta.append([rle(pixels[y * width:(y + 1) * width]) for y in range(height)])
    full_cost, prefix = [sum(map(len, rows)) for rows in full], [0]
    for rows in delta[1:]:
        prefix.append(prefix[-1] + sum(map(len, rows)))
    costs, starts = [], []
    for end in range(len(frames)):
        cost, _, key = min(((costs[k - 1] if k else 0) + full_cost[k] + prefix[end] - prefix[k], -k, k)
                           for k in range(max(0, end - KEY_INTERVAL + 1), end + 1))
        costs.append(cost)
        starts.append(key)
    keys, end = [0] * len(frames), len(frames) - 1
    while end >= 0:
        key = starts[end]
        keys[key:end + 1] = [key] * (end - key + 1)
        end = key - 1
    rows, data = [], bytearray()
    for f, key in enumerate(keys):
        for row in full[f] if f == key else delta[f]:
            rows.append(len(data))
            data.extend(row)
        rows.append(len(data))
    if len(data) > MAX_DATA:
        raise ValueError(f'packed sprite needs {len(data)} data bytes; uint16 row offsets allow {MAX_DATA}, split the image')
    return {'width': width, 'height': height, 'keys': keys, 'rows': rows, 'data': bytes(data)}


def decode_row(asset, frame, y, palette_size=64, capacity=MAX_SIDE):
    """Strict reference parser for both v1 runs and v2 literals, matching C."""
    w, h = asset['width'], asset['height']
    keys, rows, data = asset['keys'], asset['rows'], asset['data']
    if not (1 <= w <= MAX_SIDE and 1 <= h <= MAX_SIDE and 1 <= palette_size <= 64
            and 1 <= len(keys) <= 65535 and 0 <= frame < len(keys) and 0 <= y < h
            and capacity >= w and len(rows) == len(keys) * (h + 1)):
        raise ValueError('invalid sprite metadata or capacity')
    key = keys[frame]
    if (key < 0 or key > frame or frame - key >= KEY_INTERVAL or keys[key] != key
            or any(keys[f] != key for f in range(key, frame + 1))):
        raise ValueError('invalid key schedule')
    out = bytearray(w)
    for f in range(key, frame + 1):
        at = f * (h + 1) + y
        p, end = rows[at:at + 2]
        if not 0 <= p <= end <= len(data):
            raise ValueError('row outside data bounds')
        x = 0
        while p < end:
            if end - p < 2:
                raise ValueError('truncated row token')
            count, value = data[p:p + 2]
            p += 2
            if count:
                values = bytes([value]) * count
            else:
                count = value
                if not count or count > end - p:
                    raise ValueError('empty or truncated literal')
                values = data[p:p + count]
                p += count
            if count > w - x:
                raise ValueError('row exceeds width')
            for value in values:
                if ((value >= palette_size and value != INHERIT) or (value == INHERIT and f == key)):
                    raise ValueError('invalid palette index or key inheritance')
                if value != INHERIT:
                    out[x] = value
                x += 1
        if x != w:
            raise ValueError('row has the wrong width')
    return bytes(out)


def decode(asset, frame, palette_size=64):
    """Mandatory round trip after quantization; checks metadata even at height 0."""
    first = decode_row(asset, frame, 0, palette_size)
    return first + b''.join(decode_row(asset, frame, y, palette_size) for y in range(1, asset['height']))


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
        if decode(asset, f, len(palette)) != expected:
            raise ValueError(f'packed frame {f} differs from the indexed reference')
    report = {
        'format': FORMAT, 'name': name, 'width': w, 'height': h,
        'palette_rgb565': palette, 'background_rgb888': background,
        'key_interval': KEY_INTERVAL, 'keys': asset['keys'],
        'data_bytes': len(asset['data']),
        'table_bytes': len(palette) * 2 + len(asset['keys']) * 2 + len(asset['rows']) * 2,
        'frame_sha256': [hashlib.sha256(frame).hexdigest() for frame in frames],
        'source_sha256': [hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths],
        'verified_frames': len(frames), 'comparison': 'lossless after shared RGB565 quantization',
    }
    # All verification completes before any deliverable is written.
    output.parent.mkdir(parents=True, exist_ok=True)
    header = f'#pragma once\n#include "adv_sprite.h"\nextern const adv_sprite_t {name};\n'
    source = [f'// Generated by tools/generate_adv_sprites.py; do not edit.\n#include "{output.name}.h"']
    for ctype, suffix, values in [('uint16_t', 'palette', palette), ('uint16_t', 'keys', asset['keys']),
                                   ('uint16_t', 'rows', asset['rows']), ('uint8_t', 'data', asset['data'])]:
        source.append(c_array(ctype, f'{name}_{suffix}', values))
    source.append(f'const adv_sprite_t {name} = {{\n'
                  f'    {w}, {h}, {len(frames)}, {len(palette)}, {len(asset["rows"])}, {len(asset["data"])},\n'
                  f'    {name}_palette, {name}_keys, {name}_rows, {name}_data\n}};\n')
    Path(str(output) + '.h').write_text(header, encoding='utf-8', newline='\r\n')
    Path(str(output) + '.c').write_text('\n'.join(source), encoding='utf-8', newline='\r\n')
    Path(str(output) + '.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\r\n')
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
