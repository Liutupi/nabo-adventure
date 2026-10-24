// Row painters for the adventure renderer: dithered gradient bands, rounded rectangles and
// circles, arrows and glows. Coordinates inside shapes are Q4 (1/16 px); coverage is 0..256 with
// about one pixel of anti-aliasing. No floats. Rect, arrow and glow come from NABO TABLE.
#include "adv_gfx.h"

static int iabs_(int v) { return v < 0 ? -v : v; }
static int imax(int a, int b) { return a > b ? a : b; }
static int imin(int a, int b) { return a < b ? a : b; }
static int clampi(int v, int lo, int hi) { return v < lo ? lo : v > hi ? hi : v; }

static uint32_t isqrt_u(uint32_t v)
{
    uint32_t r = 0, bit = 1u << 30;
    while (bit > v) bit >>= 2;
    while (bit) {
        if (v >= r + bit) { v -= r + bit; r = (r >> 1) + bit; } else { r >>= 1; }
        bit >>= 2;
    }
    return r;
}

// Signed distance (Q4) to a rounded box centred at (cx, cy) Q4 with half size (hx, hy) Q4, radius r Q4.
static int rbox_sd(int px, int py, int cx, int cy, int hx, int hy, int r)
{
    int qx = iabs_(px - cx) - (hx - r), qy = iabs_(py - cy) - (hy - r);
    int out = qx > 0 && qy > 0 ? (int)isqrt_u((uint32_t)(qx * qx + qy * qy)) : imax(qx, qy);
    return out - r;
}

static int cov_from_sd(int sd) { return clampi(8 - sd, 0, 16) * 16; }   // 256 well inside, 0 outside

// 4x4 Bayer matrix, 0..15: the threshold for rounding each 8-bit channel down to 5 or 6 bits.
static const uint8_t BAYER[4][4] = {{0, 8, 2, 10}, {12, 4, 14, 6}, {3, 11, 1, 9}, {15, 7, 13, 5}};

static int dither(int v, int bits, int t)
{
    int max = (1 << bits) - 1;
    int scaled = v * max * 16 / 255;               // Q4 position between two output levels
    int out = (scaled >> 4) + ((scaled & 15) > t ? 1 : 0);
    return out > max ? max : out;
}

void ag_paint_band(const ag_op_t *op, int y, int x0, int x1, uint16_t *row)
{
    int h = op->u.band.h > 1 ? op->u.band.h - 1 : 1, k = clampi(y - op->u.band.y, 0, h);
    int r = op->u.band.r0 + (op->u.band.r1 - op->u.band.r0) * k / h;
    int g = op->u.band.g0 + (op->u.band.g1 - op->u.band.g0) * k / h;
    int b = op->u.band.b0 + (op->u.band.b1 - op->u.band.b0) * k / h;
    for (int x = imax(x0, op->x0); x < imin(x1, op->x1); x++) {
        int t = BAYER[y & 3][x & 3];
        row[x - x0] = (uint16_t)(dither(r, 5, t) << 11 | dither(g, 6, t) << 5 | dither(b, 5, t));
    }
}

void ag_paint_rect(const ag_op_t *op, int y, int x0, int x1, uint16_t *row)
{
    int w = op->u.rect.w, h = op->u.rect.h, r = op->u.rect.r * 16, lw = op->u.rect.line_w * 16;
    int cx = op->u.rect.x * 16 + w * 8, cy = op->u.rect.y * 16 + h * 8, py = y * 16 + 8;
    int a = imax(x0, op->x0), b = imin(x1, op->x1);
    for (int x = a; x < b; x++) {
        int sd = rbox_sd(x * 16 + 8, py, cx, cy, w * 8, h * 8, r);
        int cov = cov_from_sd(sd);
        if (!cov) continue;
        uint16_t *p = &row[x - x0];
        if (op->u.rect.alpha) *p = nt_blend565(*p, op->u.rect.fill, cov * op->u.rect.alpha / 255);
        if (lw) {
            int ring = cov - cov_from_sd(sd + lw);
            if (ring > 0) *p = nt_blend565(*p, op->u.rect.line, ring);
        }
    }
}

void ag_paint_glow(const ag_op_t *op, int y, int x0, int x1, uint16_t *row)
{
    int r = op->u.glow.r, dy = y - op->u.glow.cy;
    for (int x = imax(x0, op->x0); x < imin(x1, op->x1); x++) {
        int dx = x - op->u.glow.cx, d2 = dx * dx + dy * dy;
        if (d2 >= r * r) continue;
        int a = 180 * (r * r - d2) / (r * r);
        row[x - x0] = nt_blend565(row[x - x0], op->u.glow.color, a);
    }
}

void ag_paint_tri(const ag_op_t *op, int y, int x0, int x1, uint16_t *row)
{
    int s = op->u.tri.size, k = y - (op->u.tri.cy - s / 2);   // rows 0..s-1
    if (k < 0 || k >= s) return;
    int half = (op->u.tri.up ? k : s - 1 - k) * 16 * 2 / 3 + 8;   // Q4, widest at the base
    int cx = op->u.tri.cx * 16 + 8;
    for (int x = imax(x0, op->x0); x < imin(x1, op->x1); x++) {
        int cov = clampi(half - iabs_(x * 16 + 8 - cx) + 8, 0, 16) * 16;
        if (cov) row[x - x0] = nt_blend565(row[x - x0], op->u.tri.color, cov);
    }
}
