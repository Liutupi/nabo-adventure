#include "adv_gfx.h"

#include <string.h>

// ---------- display list ----------

static uint32_t mix(uint32_t h, uint32_t v)
{
    h ^= v + 0x9E3779B9u + (h << 6) + (h >> 2);
    return h;
}

static ag_op_t *add(ag_t *g, int kind, int x0, int y0, int x1, int y1)
{
    if (g->n >= AG_MAX_OPS) { g->overflow = true; return NULL; }
    ag_op_t *op = &g->ops[g->n++];
    memset(op, 0, sizeof(*op));
    op->kind = (uint8_t)kind;
    op->x0 = (int16_t)x0; op->y0 = (int16_t)y0; op->x1 = (int16_t)x1; op->y1 = (int16_t)y1;
    return op;
}

static void seal(ag_op_t *op, uint32_t key)
{
    op->key = mix(mix(mix(mix(mix(key, op->kind), (uint16_t)op->x0), (uint16_t)op->y0), (uint16_t)op->x1),
                  (uint16_t)op->y1);
}

void ag_init(ag_t *g, uint16_t *strip0, uint16_t *strip1, ag_send_fn send, void *ctx)
{
    memset(g, 0, sizeof(*g));
    g->strip[0] = strip0;
    g->strip[1] = strip1;
    g->send = send;
    g->ctx = ctx;
    g->full = true;
    g->prev_scene_id = -1;
}

void ag_invalidate(ag_t *g) { g->full = true; }

void ag_begin(ag_t *g, int scene_id)
{
    g->n = 0;
    g->glyphs.used = 0;
    g->overflow = false;
    g->scene_id = scene_id;
}

bool ag_band(ag_t *g, int y, int h, uint16_t top, uint16_t bottom)
{
    ag_op_t *op = add(g, AG_BAND, 0, y, AG_W, y + h);
    if (!op) return false;
    op->u.band.y = (int16_t)y; op->u.band.h = (int16_t)h;
    // Keep 8-bit channels so the dither can place the in-between shades.
    op->u.band.r0 = (uint8_t)((top >> 11) * 255 / 31); op->u.band.g0 = (uint8_t)((top >> 5 & 63) * 255 / 63);
    op->u.band.b0 = (uint8_t)((top & 31) * 255 / 31);
    op->u.band.r1 = (uint8_t)((bottom >> 11) * 255 / 31); op->u.band.g1 = (uint8_t)((bottom >> 5 & 63) * 255 / 63);
    op->u.band.b1 = (uint8_t)((bottom & 31) * 255 / 31);
    seal(op, mix(top, bottom));
    return true;
}

bool ag_rect(ag_t *g, int x, int y, int w, int h, int r, uint16_t fill, uint8_t alpha, uint16_t line, int line_w)
{
    ag_op_t *op = add(g, AG_RRECT, x, y, x + w, y + h);
    if (!op) return false;
    op->u.rect.x = (int16_t)x; op->u.rect.y = (int16_t)y; op->u.rect.w = (int16_t)w; op->u.rect.h = (int16_t)h;
    op->u.rect.r = (int16_t)r; op->u.rect.fill = fill; op->u.rect.alpha = alpha;
    op->u.rect.line = line; op->u.rect.line_w = (uint8_t)line_w;
    seal(op, mix(mix(mix(mix((uint32_t)r, fill), alpha), line), (uint32_t)line_w));
    return true;
}

bool ag_circle(ag_t *g, int cx, int cy, int r, uint16_t fill, uint8_t alpha, uint16_t line, int line_w)
{
    return ag_rect(g, cx - r, cy - r, 2 * r, 2 * r, r, fill, alpha, line, line_w);
}

int ag_text_width(const lv_font_t *font, const char *utf8) { return nt_text_width(font, utf8); }

bool ag_text(ag_t *g, const lv_font_t *font, const char *utf8, int x, int baseline, nt_align_t align, uint16_t color)
{
    if (!font || !utf8 || !*utf8) return true;
    nt_text_t t;
    if (!nt_text_layout(&g->glyphs, &t, font, utf8, x, baseline, align)) { g->overflow = true; return false; }
    ag_op_t *op = add(g, AG_TEXT, t.x0, t.y0, t.x1, t.y1);
    if (!op) return false;
    op->u.text.t = t;
    op->u.text.color = color;
    uint32_t h = mix((uint32_t)(uintptr_t)font, color);
    for (const char *s = utf8; *s; s++) h = mix(h, (uint8_t)*s);
    seal(op, h);
    return true;
}

bool ag_tri(ag_t *g, int cx, int cy, int size, bool up, uint16_t color)
{
    ag_op_t *op = add(g, AG_TRI, cx - size, cy - size, cx + size + 1, cy + size + 1);
    if (!op) return false;
    op->u.tri.cx = (int16_t)cx; op->u.tri.cy = (int16_t)cy; op->u.tri.size = (uint8_t)size;
    op->u.tri.up = up; op->u.tri.color = color;
    seal(op, mix(mix((uint32_t)size, up), color));
    return true;
}

bool ag_glow(ag_t *g, int cx, int cy, int r, uint16_t color)
{
    ag_op_t *op = add(g, AG_GLOW, cx - r, cy - r, cx + r + 1, cy + r + 1);
    if (!op) return false;
    op->u.glow.cx = (int16_t)cx; op->u.glow.cy = (int16_t)cy; op->u.glow.r = (int16_t)r; op->u.glow.color = color;
    seal(op, mix((uint32_t)r, color));
    return true;
}

bool ag_bitmap(ag_t *g, const uint16_t *pixels, int x, int y, int w, int h)
{
    if (!pixels || w <= 0 || h <= 0) return false;
    ag_op_t *op = add(g, AG_BITMAP, x, y, x + w, y + h);
    if (!op) return false;
    op->u.bitmap.pixels = pixels;
    op->u.bitmap.w = (int16_t)w;
    seal(op, (uint32_t)(uintptr_t)pixels);
    return true;
}

bool ag_sprite(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y)
{
    if (!adv_sprite_frame_valid(asset, frame) || x < INT16_MIN || y < INT16_MIN ||
        x > INT16_MAX - asset->width || y > INT16_MAX - asset->height) return false;
    ag_op_t *op = add(g, AG_SPRITE, x, y, x + asset->width, y + asset->height);
    if (!op) return false;
    op->u.sprite.asset = asset;
    op->u.sprite.frame = (uint16_t)frame;
    uintptr_t ptr = (uintptr_t)asset;
    uint32_t h = (uint32_t)ptr;
    // Include both halves on 64-bit hosts, without shifting a 32-bit C3 pointer.
    h = mix(h, (uint32_t)((uint64_t)ptr >> 32));
    seal(op, mix(h, frame));
    return true;
}

// ---------- dirty rectangles ----------

typedef struct { int16_t x0, y0, x1, y1; } rect_t;

static void add_rect(rect_t *r, int *n, int x0, int y0, int x1, int y1, bool *overflow)
{
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > AG_W) x1 = AG_W;
    if (y1 > AG_H) y1 = AG_H;
    if (x0 >= x1 || y0 >= y1) return;
    // Merge with anything it touches (8 px slack keeps the list short).
    for (int i = 0; i < *n; i++) {
        if (x0 <= r[i].x1 + 8 && r[i].x0 <= x1 + 8 && y0 <= r[i].y1 + 8 && r[i].y0 <= y1 + 8) {
            int a = x0 < r[i].x0 ? x0 : r[i].x0, b = y0 < r[i].y0 ? y0 : r[i].y0;
            int c = x1 > r[i].x1 ? x1 : r[i].x1, d = y1 > r[i].y1 ? y1 : r[i].y1;
            r[i] = r[--*n];
            add_rect(r, n, a, b, c, d, overflow);
            return;
        }
    }
    if (*n >= AG_MAX_RECTS) { *overflow = true; return; }
    r[*n].x0 = (int16_t)x0; r[*n].y0 = (int16_t)y0; r[*n].x1 = (int16_t)x1; r[*n].y1 = (int16_t)y1;
    ++*n;
}

// ---------- composition ----------

static void paint(ag_t *g, const ag_op_t *op, int y, int x0, int x1, uint16_t *row)
{
    if (y < op->y0 || y >= op->y1 || x1 <= op->x0 || x0 >= op->x1) return;
    switch (op->kind) {
    case AG_BAND: ag_paint_band(op, y, x0, x1, row); break;
    case AG_RRECT: ag_paint_rect(op, y, x0, x1, row); break;
    case AG_TEXT: nt_text_row(&g->glyphs, &op->u.text.t, y, x0, x1, row, op->u.text.color); break;
    case AG_TRI: ag_paint_tri(op, y, x0, x1, row); break;
    case AG_GLOW: ag_paint_glow(op, y, x0, x1, row); break;
    case AG_BITMAP: {
        int first = x0 > op->x0 ? x0 : op->x0;
        int last = x1 < op->x1 ? x1 : op->x1;
        const uint16_t *src = op->u.bitmap.pixels + (y - op->y0) * op->u.bitmap.w;
        for (int x = first; x < last; x++) row[x - x0] = src[x - op->x0];
        break;
    }
    case AG_SPRITE: {
        const adv_sprite_t *s = op->u.sprite.asset;
        uint8_t indices[ADV_SPRITE_MAX_SIDE];
        if (!adv_sprite_row(s, op->u.sprite.frame, (unsigned)(y - op->y0), indices, sizeof(indices))) break;
        int first = x0 > op->x0 ? x0 : op->x0;
        int last = x1 < op->x1 ? x1 : op->x1;
        for (int x = first; x < last; x++) {
            uint8_t index = indices[x - op->x0];
            if (index) row[x - x0] = s->palette[index];
        }
        break;
    }
    default: break;
    }
}

static void compose(ag_t *g, int x0, int y0, int x1, int y1)
{
    int w = x1 - x0;
    for (int y = y0; y < y1; y += AG_STRIP) {
        int h = y + AG_STRIP < y1 ? AG_STRIP : y1 - y;
        uint16_t *px = g->strip[g->which];
        g->which ^= 1;
        memset(px, 0, (size_t)(w * h) * 2);
        for (int r = 0; r < h; r++)
            for (int i = 0; i < g->n; i++) paint(g, &g->ops[i], y + r, x0, x1, px + r * w);
        for (int k = 0; k < w * h; k++) px[k] = (uint16_t)(px[k] << 8 | px[k] >> 8);   // panel order
        g->send(g->ctx, x0, y, w, h, px);
        g->bytes += (uint32_t)(w * h * 2);
    }
}

void ag_flush(ag_t *g)
{
    rect_t rects[AG_MAX_RECTS];
    int n = 0;
    bool overflow = g->full || g->scene_id != g->prev_scene_id;
    if (!overflow) {
        bool matched_prev[AG_MAX_OPS] = {0};
        for (int i = 0; i < g->n && !overflow; i++) {
            const ag_op_t *op = &g->ops[i];
            int j = 0;
            while (j < g->prev_n && (matched_prev[j] || op->kind != g->prev[j].kind || op->key != g->prev[j].key)) j++;
            if (j < g->prev_n) matched_prev[j] = true;
            // Identical ops in a different order can change overlapping pixels.
            if (j >= g->prev_n || j != i) add_rect(rects, &n, op->x0, op->y0, op->x1, op->y1, &overflow);
        }
        for (int j = 0; j < g->prev_n && !overflow; j++)
            if (!matched_prev[j]) add_rect(rects, &n, g->prev[j].x0, g->prev[j].y0, g->prev[j].x1, g->prev[j].y1, &overflow);
    }
    g->bytes = 0;
    if (overflow) compose(g, 0, 0, AG_W, AG_H);
    else
        for (int i = 0; i < n; i++) compose(g, rects[i].x0, rects[i].y0, rects[i].x1, rects[i].y1);
    memcpy(g->prev, g->ops, sizeof(ag_op_t) * (size_t)g->n);
    g->prev_n = g->n;
    g->prev_scene_id = g->scene_id;
    g->full = false;
}
