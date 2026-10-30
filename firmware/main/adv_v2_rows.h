#pragma once
#include "adv_gfx.h"
// Native-row helpers keep dense scenery out of the 128-operation display list.
static inline void v2_span(int left, int right, int x0, int x1, uint16_t *row, uint16_t color, int alpha)
{
    if (left < x0)
        left = x0;
    if (right > x1)
        right = x1;
    for (int x = left; x < right; x++)
        row[x - x0] = alpha == 255 ? color : nt_blend565(row[x - x0], color, alpha * 256 / 255);
}
static inline void v2_rect_row(int y, int x0, int x1, uint16_t *row, int x, int top, int w, int h,
                               uint16_t color, int alpha)
{
    if (y >= top && y < top + h)
        v2_span(x, x + w, x0, x1, row, color, alpha);
}
static inline uint32_t v2_hash(uint32_t n)
{
    n = (n ^ 0x9e3779b9u) * 0x85ebca6bu;
    n ^= n >> 13;
    n *= 0xc2b2ae35u;
    return n ^ (n >> 16);
}
static inline void v2_art_row(const adv_asset_record_t *a, unsigned frame, int ax, int ay, int y, int x0,
                              int x1, uint16_t *row)
{
    if (!a)
        return;
    for (unsigned i = 0; i < a->piece_count; i++) {
        const adv_asset_piece_t *p = &a->pieces[i];
        const adv_sprite_t *s = p->sprite;
        int left = ax - a->anchor_x + p->x, top = ay - a->anchor_y + p->y;
        if (y < top || y >= top + s->height || left >= x1 || left + s->width <= x0)
            continue;
        unsigned f = frame < s->frame_count ? frame : s->frame_count - 1;
        uint8_t pixels[ADV_SPRITE_MAX_SIDE];
        if (!adv_sprite_row(s, f, (unsigned)(y - top), pixels, sizeof(pixels)))
            continue;
        int first = left > x0 ? left : x0, last = left + s->width < x1 ? left + s->width : x1;
        for (int x = first; x < last; x++) {
            unsigned index = pixels[x - left];
            if (index)
                row[x - x0] = s->palette[index];
        }
    }
}
static inline uint32_t v2_state_key(const void *state, size_t size)
{
    const uint8_t *p = state;
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < size; i++)
        h = (h ^ p[i]) * 16777619u;
    return h;
}
