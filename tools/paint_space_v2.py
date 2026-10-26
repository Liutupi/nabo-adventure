#!/usr/bin/env python3
"""Paint the SPACE V2「火箭登月」backdrops and props offline (deterministic, no external art).

Writes RGBA PNGs with 1-bit alpha and a limited palette to game-art/adventure/art/space-v2/, plus
space-v2-manifest.json (ids, sizes, anchors). Skies are drawn at runtime as gradients; these layers sit on top.
Usage: python tools/paint_space_v2.py [--preview out.png]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'game-art/adventure/art/space-v2'


# ---------------------------------------------------------------- helpers
def rng(seed):
    return np.random.default_rng(seed)


def value_noise(w, h, cell, seed):
    r = rng(seed)
    gw, gh = w // cell + 3, h // cell + 3
    grid = r.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / cell
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = grid[y0, x0], grid[y0, x0 + 1]
    c, d = grid[y0 + 1, x0], grid[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(w, h, cell, octaves, seed, gain=0.5):
    total, amp, norm = np.zeros((h, w)), 1.0, 0.0
    for o in range(octaves):
        total += amp * value_noise(w, h, max(1, cell >> o), seed + o * 101)
        norm += amp
        amp *= gain
    return total / norm


def noise1d(n, cell, seed, octaves=4):
    return fbm(n, 1, cell, octaves, seed)[0]


def hexc(s):
    s = s.lstrip('#')
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def ramp(t, stops):
    """t in [0,1] array -> RGB via colour stops [(pos, '#hex'), ...]."""
    t = np.clip(t, 0, 1)
    out = np.zeros(t.shape + (3,))
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (t >= p0) & (t <= p1)
        k = ((t - p0) / max(1e-6, p1 - p0))[..., None]
        out[m] = (hexc(c0) * (1 - k) + hexc(c1) * k)[m]
    return out


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5


def dither(t, levels):
    """Ordered dither of a [0,1] field into `levels` steps (pixel-art banding instead of smooth blur)."""
    h, w = t.shape
    b = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    return np.clip(np.floor(t * (levels - 1) + 0.5 + b * 0.9), 0, levels - 1) / (levels - 1)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3))
        self.a = np.zeros((h, w), bool)

    def put(self, mask, color):
        c = hexc(color) if isinstance(color, str) else color
        self.rgb[mask] = c if np.ndim(c) == 1 else c[mask]
        self.a |= mask

    def rect(self, x, y, w, h, color):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            m = np.zeros((self.h, self.w), bool); m[y0:y1, x0:x1] = True; self.put(m, color)

    def pix(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rgb[y, x] = hexc(color); self.a[y, x] = True

    def line(self, x0, y0, x1, y1, color):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.pix(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), color)

    def disc(self, cx, cy, r, color, ry=None):
        ry = ry or r
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        self.put(((xs - cx) / r) ** 2 + ((ys - cy) / ry) ** 2 <= 1, color)

    def image(self, colors):
        rgba = np.zeros((self.h, self.w, 4), np.uint8)
        rgba[..., :3] = np.clip(self.rgb, 0, 255).astype(np.uint8)
        rgba[..., 3] = np.where(self.a, 255, 0)
        im = Image.fromarray(rgba, 'RGBA')
        # limited palette, alpha kept 1-bit
        q = im.convert('RGB').quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
        out = np.array(q.convert('RGBA')); out[..., 3] = rgba[..., 3]
        out[out[..., 3] == 0, :3] = 0
        return Image.fromarray(out, 'RGBA')


# ---------------------------------------------------------------- launch site
def launch_far():
    """320x120: haze mountains, coastal city at dawn, the sea with the sun's path. Parallax ~0.35."""
    w, h, horizon = 320, 120, 74
    c = Canvas(w, h)
    # far mountain range (two layers)
    for layer, (base, amp, col_top, col_low, seed) in enumerate([(62, 26, '#8a6fa8', '#5e5287', 3), (70, 16, '#6f5d93', '#4a4673', 9)]):
        ridge = base - amp * noise1d(w, 48 >> layer, seed, 5)
        ys, xs = np.mgrid[0:h, 0:w]
        m = (ys >= ridge[None, :]) & (ys < horizon)
        t = np.clip((ys - ridge[None, :]) / 22, 0, 1)
        lit = np.clip((np.gradient(ridge)[None, :] * -3 + 0.5), 0, 1)   # slopes facing the sunrise (right) are lighter
        colr = ramp(dither(t * 0.7 + (1 - lit) * 0.3, 5), [(0, col_top), (1, col_low)])
        c.put(m, colr)
    # sea
    ys, xs = np.mgrid[0:h, 0:w]
    sea = ys >= horizon
    depth = (ys - horizon) / (h - horizon)
    waves = fbm(w, h, 6, 3, 21)
    base = ramp(dither(np.clip(depth * 0.8 + (waves - 0.5) * 0.25, 0, 1), 6), [(0, '#e6a07a'), (0.25, '#7d6d9a'), (0.6, '#3c4f7e'), (1, '#24365e')])
    c.put(sea, base)
    # glittering sun path around x=250
    sp = sea & (np.abs(xs - 250 + (ys - horizon) * 0.15) < 6 + (ys - horizon) * 0.5) & (fbm(w, h, 3, 2, 33) > 0.52) & ((ys % 2) == 0)
    c.put(sp, '#ffe0a0')
    for i in range(70):                                   # wave glints
        r = rng(400 + i); x, y = int(r.integers(0, w)), int(r.integers(horizon + 3, h))
        c.rect(x, y, int(r.integers(2, 6)), 1, '#9fb4dc' if i % 3 else '#f2c49a')
    # coastal city skyline on the left
    r = rng(77)
    x = 6
    while x < 168:
        bw, bh = int(r.integers(6, 15)), int(r.integers(8, 34 if 40 < x < 120 else 20))
        top = horizon - bh
        c.rect(x, top, bw, bh, '#2b2e52' if r.random() < .6 else '#353a63')
        c.rect(x, top, 1, bh, '#4a4f80')                       # sunrise rim on the right faces
        for wy in range(top + 2, horizon - 1, 3):
            for wx in range(x + 1, x + bw - 1, 2):
                if r.random() < 0.28: c.pix(wx, wy, '#ffd27a' if r.random() < .8 else '#9ff0ff')
        if bh > 26 and r.random() < .5:
            c.line(x + bw // 2, top - 1, x + bw // 2, top - 6, '#2b2e52'); c.pix(x + bw // 2, top - 7, '#ff5a4a')
        x += bw + int(r.integers(0, 3))
    # a lighthouse on a rock on the right
    c.disc(206, horizon + 2, 9, '#2d2f4f', 4)
    c.rect(204, horizon - 16, 5, 16, '#e9e3d6'); c.rect(204, horizon - 11, 5, 3, '#d9534a'); c.rect(203, horizon - 19, 7, 3, '#2d2f4f'); c.pix(206, horizon - 21, '#ffe97a')
    return c


def launch_near():
    """320x150, bottom of the first screen: pad deck at y=86 (screen 176), tower, tanks, beach. Parallax 1.0."""
    w, h, deck = 320, 150, 86
    c = Canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    # dunes and shore grass behind the complex
    dune = 70 - 8 * noise1d(w, 40, 5, 4)
    m = ys >= dune[None, :]
    c.put(m, ramp(dither(np.clip((ys - dune[None, :]) / 40 + (fbm(w, h, 8, 3, 6) - .5) * .4, 0, 1), 5), [(0, '#e9c28c'), (.5, '#c99c6c'), (1, '#8a6d55')]))
    grass = m & (ys < dune[None, :] + 4) & (fbm(w, h, 3, 2, 8) > .48)
    c.put(grass, '#6f9a5a')
    # palm trees on the right
    for px_, s in ((268, 0), (292, 1), (250, 2)):
        r = rng(90 + s); top = 34 + s * 3
        for k in range(30):
            c.pix(px_ + int(k * 0.15 * (1 if s % 2 else -1)), 70 - k + top - 34, '#7a5a3c')
        cx, cy = px_ + int(30 * 0.15 * (1 if s % 2 else -1)), 40 + top - 34
        for a in np.linspace(0, 2 * np.pi, 9, endpoint=False):
            for k in range(13):
                dx, dy = int(np.cos(a) * k), int(np.sin(a) * k * 0.55 + (k * k) / 28)
                c.pix(cx + dx, cy + dy, '#3f7a4a' if k < 8 else '#5f9a54')
    # fuel tanks (spheres) and pipes on the left
    for tx, ty, tr in ((30, 62, 13), (58, 66, 10)):
        d = np.sqrt((xs - tx) ** 2 + (ys - ty) ** 2)
        m = d <= tr
        light = np.clip(((xs - tx) * .5 + (ty - ys) * .6) / tr * .5 + .5, 0, 1)
        c.put(m, ramp(dither(1 - light, 5), [(0, '#ffffff'), (.5, '#c9d2e0'), (1, '#7f8aa3')]))
        c.rect(tx - tr + 2, ty + tr - 2, 3, 10, '#6d7690'); c.rect(tx + tr - 5, ty + tr - 2, 3, 10, '#6d7690')
    c.rect(20, 82, 110, 2, '#8e97ad'); c.rect(20, 85, 110, 1, '#6d7690')
    # launch deck with flame trench
    c.rect(96, deck, 128, 8, '#7b8296'); c.rect(96, deck, 128, 2, '#a9b0c2')
    for x in range(96, 224, 8): c.rect(x, deck + 6, 4, 2, '#f2c14e'); c.rect(x + 4, deck + 6, 4, 2, '#2b2b33')
    c.rect(136, deck + 8, 48, 12, '#2a2530'); c.rect(140, deck + 10, 40, 8, '#4a2a26')
    # ground apron and road
    sand = ys >= deck + 8
    c.put(sand, ramp(dither(np.clip((ys - deck - 8) / 60 + (fbm(w, h, 6, 3, 12) - .5) * .5, 0, 1), 5), [(0, '#d9b483'), (.5, '#b48d63'), (1, '#7d6450')]))
    turf = sand & (ys < deck + 16) & (fbm(w, h, 7, 3, 13) > .5) | (sand & (ys > h - 14) & (fbm(w, h, 5, 2, 16) > .45))
    c.put(turf, ramp(dither(fbm(w, h, 3, 2, 14), 3), [(0, '#7aa65f'), (1, '#4f7d45')]))
    apron = (ys >= deck + 8) & (xs >= 84) & (xs < 236)
    c.put(apron, ramp(dither(np.clip((ys - deck - 8) / 60 + (fbm(w, h, 5, 3, 15) - .5) * .4, 0, 1), 4), [(0, '#9a9fae'), (1, '#6a6f80')]))
    c.rect(136, deck + 8, 48, 12, '#2a2530'); c.rect(140, deck + 10, 40, 8, '#4a2a26')
    for x in range(88, 232, 16): c.rect(x, deck + 34, 9, 2, '#e8e2c8')
    # service tower: lattice with X bracing, crane arm toward the rocket at x=160
    tx0, tx1, ttop = 112, 128, 6
    c.rect(tx0, ttop, 2, deck - ttop, '#b8452f'); c.rect(tx1, ttop, 2, deck - ttop, '#b8452f')
    for y in range(ttop, deck - 8, 10):
        c.line(tx0, y, tx1 + 1, y + 10, '#8e2f22'); c.line(tx1 + 1, y, tx0, y + 10, '#8e2f22'); c.rect(tx0, y, tx1 - tx0 + 2, 1, '#d0634a')
    for arm_y in (24, 50):
        c.rect(tx1 + 2, arm_y, 22, 2, '#9aa3b8'); c.rect(tx1 + 2, arm_y + 2, 22, 1, '#646d85')
    c.rect(tx0 - 4, ttop - 3, tx1 - tx0 + 10, 3, '#5d6377'); c.line(tx0 - 2, ttop - 3, tx0 + 26, ttop - 14, '#d0d6e2'); c.pix(tx0 + 26, ttop - 15, '#ff4a3a')
    c.pix(tx0 + 1, ttop - 5, '#ff4a3a')
    # floodlight masts
    for mx in (84, 236):
        c.rect(mx, 30, 2, deck - 30, '#5d6377'); c.rect(mx - 4, 26, 10, 4, '#e8eef8'); c.rect(mx - 3, 27, 8, 2, '#fff6c0')
    # control bunker and dish on the right
    c.rect(226, 64, 26, 22, '#c9cfdc'); c.rect(226, 64, 26, 3, '#e7ecf5'); c.rect(230, 72, 4, 3, '#7fd6ff'); c.rect(238, 72, 4, 3, '#7fd6ff')
    c.disc(300, 60, 12, '#e3e8f2', 7); c.disc(300, 58, 9, '#b7c0d3', 5); c.rect(299, 66, 2, 20, '#7f889f')
    return c


# ---------------------------------------------------------------- sky layers
def cloud_bank(seed, w=320, h=96, dark=False, count=None):
    """Cumulus bank: a union of domes (height field) lit from the upper left, flat-ish base, crisp rim light."""
    c = Canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    g = rng(seed)
    height = np.zeros((h, w))
    base = h - 14
    n = count or w // 16
    for i in range(n):
        cx = g.uniform(-10, w + 10); r = g.uniform(10, 26) * (1.25 if 0.25 < cx / w < 0.75 else 1.0)
        cy = base - r * g.uniform(.35, .85)
        d2 = (xs - cx) ** 2 + ((ys - cy) * 1.15) ** 2
        height = np.maximum(height, np.sqrt(np.clip(r * r - d2, 0, None)))
    for i in range(n * 2):                                 # small top puffs
        cx = g.uniform(0, w); r = g.uniform(5, 11)
        top = np.argmax(height[:, int(np.clip(cx, 0, w - 1))] > 0) if height[:, int(np.clip(cx, 0, w - 1))].max() > 0 else base
        cy = top + r * .4
        d2 = (xs - cx) ** 2 + (ys - cy) ** 2
        height = np.maximum(height, np.sqrt(np.clip(r * r - d2, 0, None)) * .9)
    m = (height > 0.6) & (ys <= base + 3)
    gy, gx = np.gradient(height)
    light = np.clip(.8 - gx * .09 - gy * .16, 0, 1)          # brighter where the surface faces up-left
    light = np.clip(light - np.clip((ys - (base - 10)) / 14, 0, 1) * .45 + (fbm(w, h, 4, 2, seed + 3) - .5) * .12, 0, 1)
    stops = [(0, '#3b3f58'), (.4, '#5d6380'), (1, '#9aa0b6')] if dark else [(0, '#7f93ba'), (.35, '#b4c4de'), (.7, '#e3ecf8'), (1, '#ffffff')]
    c.put(m, ramp(dither(light, 7), stops))
    rim = m & ~np.roll(m, 1, 0) & ~np.roll(m, 1, 1)
    c.put(rim, '#ffffff' if not dark else '#b8bdcc')
    return c


def cloud_far():
    """Distant small cumulus, blue-tinted by air, for the parallax layer behind the main banks."""
    c = cloud_bank(131, 320, 56, count=26)
    m = c.a
    lum = c.rgb.mean(axis=2) / 255
    c.rgb[m] = ramp(dither(np.clip(lum[m][None, :], 0, 1), 4), [(0, '#8fb6e6'), (1, '#e4f0fc')])[0]
    return c


def storm_cloud():
    c = cloud_bank(41, 112, 60, dark=True)
    return c


def aurora():
    w, h = 320, 120
    c = Canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    base = 78 + 18 * np.sin(xs / 46.0) + 10 * (noise1d(w, 36, 61, 3)[None, :] - .5)
    height = 30 + 34 * noise1d(w, 28, 65, 3)[None, :]
    rays = noise1d(w, 2, 64, 2)[None, :] * .55 + noise1d(w, 9, 66, 2)[None, :] * .45
    t = (base - ys) / np.maximum(1, height)                          # 0 at the lower hem, 1 at the top
    strength = np.clip(1 - np.abs(t - .25) * 1.7, 0, 1) * (rays * 1.3)
    m = (t > -0.05) & (t < 1) & (dither(np.clip(strength, 0, 1), 5) > .45)
    c.put(m, ramp(dither(np.clip(t, 0, 1), 5), [(0, '#d4ffe6'), (.25, '#5af0b0'), (.6, '#2fb7a3'), (1, '#8a6ce0')]))
    return c


def cirrus():
    w, h = 320, 48
    c = Canvas(w, h)
    g = rng(71)
    for i in range(26):
        x0, y0, L = g.uniform(-40, w), g.uniform(4, h - 6), g.uniform(30, 90)
        for k in range(int(L)):
            x = int(x0 + k); y = int(y0 + 3 * np.sin(k / 14.0 + i) - k * .06)
            if g.random() < .82: c.pix(x, y, '#e8f0ff' if k < L * .6 else '#b9cbef')
            if k % 5 == 0 and g.random() < .6: c.pix(x + 1, y + 1, '#9fb6e8')
    return c


def earth_limb():
    """320x130: the Earth below as the rocket leaves the atmosphere - curved limb, oceans, cloud swirls, glow."""
    w, h = 320, 130
    c = Canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    R, cx, cy = 520, 160, 40 + 520
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    glow = (d <= R + 5) & (d > R)
    c.put(glow, ramp(dither(np.clip((d - R) / 5, 0, 1), 3), [(0, '#9fe3ff'), (1, '#3d7bd6')]))
    planet = d <= R
    land = fbm(w, h, 40, 5, 81) > .6
    ocean = ramp(dither(np.clip((ys - 40) / 90 + (fbm(w, h, 10, 3, 82) - .5) * .3, 0, 1), 5), [(0, '#3f8fe0'), (1, '#173f8a')])
    ground = ramp(dither(fbm(w, h, 6, 3, 83), 4), [(0, '#7fb35a'), (.5, '#5d8f44'), (1, '#c7b07a')])
    col = np.where(land[..., None], ground, ocean)
    clouds = fbm(w, h, 10, 5, 84) * .6 + fbm(w * 3, h, 30, 3, 85)[:, ::3] * .4      # wind-stretched cloud streets
    swirl = clouds + .1 * np.sin(xs / 22.0 + ys / 7.0)
    col = np.where((swirl > .62)[..., None], ramp(dither(np.clip((swirl - .62) * 5, 0, 1), 3), [(0, '#b8d4ef'), (1, '#ffffff')]), col)
    rim = np.clip((R - d) / 10, 0, 1)
    col = col * (0.55 + 0.45 * rim[..., None]) + hexc('#8fd0ff') * (1 - rim[..., None]) * .45
    c.put(planet, col)
    return c


def nebula():
    w, h = 320, 220
    c = Canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    n = fbm(w, h, 48, 6, 91)
    n2 = fbm(w, h, 20, 4, 92)
    band = np.exp(-((ys - 110 - 40 * np.sin(xs / 70.0)) / 70.0) ** 2)
    v = n * band + .25 * n2 * band
    m = v > .42
    t = np.clip((v - .42) * 2.4, 0, 1)
    c.put(m, ramp(dither(t, 6), [(0, '#241a4c'), (.35, '#4b2b78'), (.65, '#8a3b8c'), (.88, '#d0668f'), (1, '#f7b3cc')]))
    dust = m & (fbm(w, h, 9, 3, 93) > .66) & (t < .55)
    c.put(dust, '#3a2566')
    r = rng(94)
    for i in range(160):                                 # embedded star clusters
        x, y = int(r.integers(0, w)), int(r.integers(0, h))
        if band[y, x] > .3:
            col = ['#ffffff', '#ffe9c2', '#bfe0ff'][i % 3]
            c.pix(x, y, col)
            if i % 9 == 0: c.pix(x + 1, y, col); c.pix(x - 1, y, col); c.pix(x, y + 1, col); c.pix(x, y - 1, col)
    return c


def moon(size):
    c = Canvas(size, size)
    ys, xs = np.mgrid[0:size, 0:size]
    r = size / 2 - .5
    d = np.sqrt((xs - r) ** 2 + (ys - r) ** 2)
    m = d <= r
    nz = (xs - r) / r, (ys - r) / r
    light = np.clip(-nz[0] * .55 - nz[1] * .45 + .45, 0, 1)            # sun from upper left
    tex = fbm(size, size, max(2, size // 6), 4, 101 + size)
    maria = fbm(size, size, max(3, size // 3), 3, 102) > .58
    base = ramp(dither(np.clip(1 - light * .8 - (tex - .5) * .4, 0, 1), 6), [(0, '#f4f1e6'), (.4, '#cfcabb'), (.7, '#8f8b84'), (1, '#4c4a52')])
    base = np.where(maria[..., None], base * .78, base)
    c.put(m, base)
    g = rng(103 + size)
    for i in range(max(4, size // 6)):
        cx, cy, cr = g.uniform(.15, .85) * size, g.uniform(.15, .85) * size, g.uniform(.03, .1) * size
        if (cx - r) ** 2 + (cy - r) ** 2 > (r - cr) ** 2: continue
        dd = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        c.put(m & (dd <= cr), base * .7)
        c.put(m & (dd <= cr) & (dd > cr - 1.2) & (ys < cy), base * 1.15)
    return c


def lunar_surface():
    """320x120: grey regolith plain with a ridge, craters and boulders; the landing site sits at y=56."""
    w, h = 320, 120
    c = Canvas(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    ridge = 24 - 22 * noise1d(w, 50, 111, 4)
    m = ys >= ridge[None, :]
    c.put(m & (ys < 50), ramp(dither(np.clip((ys - ridge[None, :]) / 30, 0, 1), 4), [(0, '#9a99a4'), (1, '#6c6b78')]))
    plain = ys >= 50
    tex = fbm(w, h, 7, 4, 112)
    c.put(plain, ramp(dither(np.clip((ys - 50) / 70 * .6 + (tex - .5) * .6 + .2, 0, 1), 6), [(0, '#c9c7cf'), (.5, '#a5a3ae'), (1, '#6f6d7a')]))
    g = rng(113)
    for i in range(26):
        cx, cy = g.uniform(0, w), g.uniform(58, h - 4)
        rx = g.uniform(4, 16) * (1 + (cy - 50) / 70); ry = rx * .32
        e = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2
        c.put(plain & (e <= 1), '#8a8895'); c.put(plain & (e <= 1) & (ys < cy), '#6a6876'); c.put(plain & (e > 1) & (e <= 1.35) & (ys > cy), '#dcdae2')
    for i in range(40):
        x, y = int(g.uniform(0, w)), int(g.uniform(54, h))
        c.rect(x, y, 2, 1, '#5d5b68'); c.pix(x, y - 1, '#e2e0e8')
    return c


# ---------------------------------------------------------------- props
def rocket(lean):
    """16x44 rocket: white body, red fins and nose band, round window. lean -1/0/1 shifts the nose a pixel."""
    w, h = 18, 46
    c = Canvas(w, h)
    cx = 9
    for y in range(4, 40):
        half = 5 if y > 12 else max(1, int((y - 3) * 5 / 9))
        off = round(lean * (40 - y) / 36)
        x0, x1 = cx - half + off, cx + half + off
        for x in range(x0, x1):
            t = (x - x0) / max(1, x1 - x0 - 1)
            col = '#ffffff' if t < .35 else '#dfe6f1' if t < .7 else '#a8b3c8'
            if 13 <= y <= 15: col = '#d9473a' if t < .7 else '#a3352c'
            if 30 <= y <= 31: col = '#2d3a5a'
            c.pix(x, y, col)
    off = round(lean * 18 / 36)
    c.disc(cx + off, 20, 2.6, '#2d3a5a'); c.disc(cx + off - .5, 19.5, 1.6, '#7fd6ff'); c.pix(cx + off - 1, 19, '#ffffff')
    for side in (-1, 1):                                  # fins
        for k in range(8):
            x = cx + side * (5 + k // 3)
            c.rect(min(x, x - side), 32 + k, 1, 1, '#d9473a')
            c.pix(cx + side * 5, 32 + k, '#d9473a')
    c.rect(cx - 3, 40, 6, 3, '#4b556e'); c.rect(cx - 2, 43, 4, 1, '#2b3045')
    return c


def booster():
    c = Canvas(14, 30)
    for y in range(0, 28):
        for x in range(2, 12):
            t = (x - 2) / 9
            c.pix(x, y, '#e9eef6' if t < .4 else '#b9c3d6' if t < .8 else '#8691a9')
    c.rect(2, 4, 10, 2, '#2d3a5a'); c.rect(1, 22, 12, 4, '#d9473a'); c.rect(4, 26, 6, 3, '#4b556e')
    return c


def birds(frame):
    c = Canvas(20, 10)
    for bx, by in ((2, 5), (9, 2), (15, 6)):
        if frame: c.line(bx, by, bx + 2, by - 2, '#2b2e44'); c.line(bx + 2, by - 2, bx + 4, by, '#2b2e44')
        else: c.line(bx, by - 2, bx + 2, by, '#2b2e44'); c.line(bx + 2, by, bx + 4, by - 2, '#2b2e44')
    return c


def plane():
    c = Canvas(40, 14)
    c.rect(4, 6, 32, 4, '#eef2f8'); c.rect(4, 9, 32, 1, '#a9b3c6'); c.rect(34, 6, 4, 3, '#eef2f8'); c.pix(37, 7, '#9fd8ff')
    c.rect(14, 3, 8, 3, '#c9d1df'); c.rect(14, 10, 8, 3, '#c9d1df'); c.rect(4, 2, 4, 4, '#d9473a'); c.rect(5, 10, 6, 2, '#c9d1df')
    for x in range(26, 34, 2): c.pix(x, 7, '#5d7aa8')
    return c


def balloon():
    c = Canvas(16, 26)
    c.disc(8, 8, 7, '#e8604c', 8); c.disc(6, 6, 3, '#ff9f8a')
    c.rect(4, 4, 1, 9, '#f4d35e'); c.rect(11, 4, 1, 9, '#f4d35e')
    c.line(5, 15, 7, 21, '#7f6a55'); c.line(11, 15, 9, 21, '#7f6a55'); c.rect(6, 21, 5, 4, '#a57a4f')
    return c


def satellite():
    c = Canvas(44, 18)
    for x0 in (1, 29):
        c.rect(x0, 4, 14, 10, '#2f4f9c')
        for x in range(x0, x0 + 14, 3): c.rect(x, 4, 1, 10, '#5d7fd0')
        c.rect(x0, 8, 14, 1, '#5d7fd0')
    c.rect(15, 8, 14, 2, '#9aa3b8'); c.rect(18, 3, 8, 12, '#e3c56b'); c.rect(18, 3, 8, 2, '#fff1b0'); c.rect(21, 0, 2, 3, '#c9d1df'); c.pix(22, 0, '#ff5a4a')
    return c


def station():
    c = Canvas(84, 34)
    c.rect(4, 15, 76, 3, '#b9c3d6')
    for x0 in (4, 22, 50, 68):
        c.rect(x0, 2, 12, 12, '#2f4f9c'); c.rect(x0, 19, 12, 12, '#2f4f9c')
        for x in range(x0, x0 + 12, 3): c.rect(x, 2, 1, 12, '#5d7fd0'); c.rect(x, 19, 1, 12, '#5d7fd0')
    c.rect(34, 11, 16, 12, '#e9eef6'); c.rect(34, 11, 16, 2, '#ffffff'); c.rect(38, 15, 3, 3, '#7fd6ff'); c.rect(44, 15, 3, 3, '#7fd6ff')
    return c


def junk():
    c = Canvas(12, 10)
    c.rect(1, 3, 7, 4, '#9aa3b8'); c.rect(2, 3, 5, 1, '#d6dbe6'); c.line(7, 2, 11, 0, '#c9a85a'); c.rect(4, 7, 2, 2, '#5d6377')
    return c


def comet():
    c = Canvas(56, 18)
    ys, xs = np.mgrid[0:18, 0:56]
    tail = (xs > 10) & (np.abs(ys - 9) < (xs - 10) * .18 + 1) & (fbm(56, 18, 3, 2, 121) > .35)
    c.put(tail, ramp(dither(np.clip((xs - 10) / 46, 0, 1), 4), [(0, '#e9fbff'), (.5, '#7fd6ff'), (1, '#3b5fb0')]))
    c.disc(8, 9, 6, '#cfefff'); c.disc(7, 8, 3, '#ffffff')
    return c


def repair():
    c = Canvas(14, 14)
    c.rect(1, 3, 12, 10, '#e9eef6'); c.rect(1, 3, 12, 2, '#ffffff'); c.rect(5, 1, 4, 2, '#9aa3b8')
    c.rect(6, 5, 2, 7, '#3cb371'); c.rect(3, 8, 8, 2, '#3cb371')
    return c


ASSETS = [  # id, painter, colours, anchor (x, y) as fraction-free pixel point
    ('space-v2/bg/launch-far', launch_far, 48, (0, 120)), ('space-v2/bg/launch-near', launch_near, 56, (0, 150)),
    ('space-v2/bg/cloud-a', lambda: cloud_bank(51), 16, (0, 96)), ('space-v2/bg/cloud-b', lambda: cloud_bank(57), 16, (0, 96)),
    ('space-v2/bg/cloud-far', cloud_far, 8, (0, 56)), ('space-v2/bg/cirrus', cirrus, 6, (0, 48)), ('space-v2/bg/aurora', aurora, 10, (0, 120)), ('space-v2/bg/earth-limb', earth_limb, 40, (0, 130)),
    ('space-v2/bg/nebula', nebula, 24, (0, 220)), ('space-v2/bg/moon-32', lambda: moon(32), 16, (16, 16)),
    ('space-v2/bg/moon-64', lambda: moon(64), 20, (32, 32)), ('space-v2/bg/moon-128', lambda: moon(128), 28, (64, 64)),
    ('space-v2/bg/lunar-surface', lunar_surface, 24, (0, 120)), ('space-v2/bg/station', station, 10, (42, 17)),
    ('space-v2/props/rocket-left', lambda: rocket(-1), 12, (9, 44)), ('space-v2/props/rocket', lambda: rocket(0), 12, (9, 44)),
    ('space-v2/props/rocket-right', lambda: rocket(1), 12, (9, 44)), ('space-v2/props/booster', booster, 8, (7, 15)),
    ('space-v2/props/storm-cloud', storm_cloud, 12, (56, 30)), ('space-v2/props/birds-0', lambda: birds(0), 2, (10, 5)),
    ('space-v2/props/birds-1', lambda: birds(1), 2, (10, 5)), ('space-v2/props/plane', plane, 10, (20, 7)),
    ('space-v2/props/balloon', balloon, 10, (8, 13)), ('space-v2/props/satellite', satellite, 10, (22, 9)),
    ('space-v2/props/junk', junk, 6, (6, 5)), ('space-v2/props/comet', comet, 10, (8, 9)), ('space-v2/props/repair', repair, 6, (7, 7)),
    ('space-v2/props/plane-left', lambda: flipped(plane()), 10, (20, 7)), ('space-v2/props/comet-right', lambda: flipped(comet()), 10, (48, 9)),
]


def flipped(c):
    """Left-right copy of a prop (never used for NABO: the cap logo must not be mirrored)."""
    c.rgb = c.rgb[:, ::-1].copy(); c.a = c.a[:, ::-1].copy()
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preview', type=Path)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for ident, painter, colours, anchor in ASSETS:
        im = painter().image(colours)
        path = OUT / (ident.split('/', 1)[1].replace('/', '-') + '.png')
        im.save(path, optimize=True)
        manifest.append({'id': ident, 'path': str(path.relative_to(ROOT / 'game-art/adventure/art')), 'size': list(im.size), 'anchor': list(anchor)})
    (ROOT / 'game-art/adventure/art/space-v2-manifest.json').write_text(json.dumps({'schema': 'space-v2-painted-v1', 'assets': manifest}, indent=1) + '\n', 'utf-8')
    print(len(manifest), 'assets')
    if args.preview:
        ims = [Image.open(ROOT / 'game-art/adventure/art' / a['path']) for a in manifest]
        W = 660; y = 0; x = 0; row = 0; pos = []
        for im in ims:
            if x + im.width > W: x = 0; y += row + 6; row = 0
            pos.append((x, y)); x += im.width + 6; row = max(row, im.height)
        sheet = Image.new('RGBA', (W, y + row), (40, 60, 110, 255))
        for im, p in zip(ims, pos): sheet.alpha_composite(im.convert('RGBA'), p)
        sheet.save(args.preview)


if __name__ == '__main__':
    main()
