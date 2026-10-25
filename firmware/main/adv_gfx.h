#pragma once
// Adventure renderer core (forked from the NABO TABLE renderer). Each frame a page builder fills
// a display list of draw ops; ops that changed since the last frame mark dirty rectangles, and
// only those are composed, AG_STRIP rows at a time, and sent to the panel. Integer maths only.
#include <stdbool.h>
#include <stdint.h>

#include "adv_text.h"
#include "adv_sprite.h"
#include "adv_ninepatch.h"

#ifdef __cplusplus
extern "C" {
#endif

#define AG_W 240
#define AG_H 320
#define AG_MAX_W 320
#define AG_MAX_OPS 128
#define AG_MAX_RECTS 16
#define AG_STRIP 8

// Sends big-endian RGB565 for screen rows [y, y + h), columns [x, x + w).
typedef void (*ag_send_fn)(void *ctx, int x, int y, int w, int h, uint16_t *px);
typedef void (*ag_row_fn)(const void *ctx,int y,int x0,int x1,uint16_t *row);

typedef enum {
    AG_BAND,      // vertical gradient, ordered dither against RGB565 banding
    AG_RRECT,     // rounded rectangle (circle when r = w / 2), optional outline, alpha
    AG_TEXT,
    AG_TRI,       // small up / down arrow
    AG_GLOW,      // soft round highlight
    AG_BITMAP,    // immutable native RGB565 image in flash
    AG_SPRITE,    // immutable indexed row RLE with bounded keyframe/delta replay
    AG_NINEPATCH, // fixed corners, tiled edges/center, one display-list op
    AG_ROWS,      // immutable during flush; e.g. a decoded YCbCr reference image
} ag_kind_t;

typedef struct {
    uint8_t kind;
    int16_t x0, y0, x1, y1;   // bounding box, exclusive end, unclipped
    uint32_t key;             // hash of everything that changes pixels
    union {
        struct { int16_t y, h; uint8_t r0, g0, b0, r1, g1, b1; } band;
        struct { int16_t x, y, w, h, r; uint16_t fill, line; uint8_t alpha, line_w; } rect;
        struct { nt_text_t t; uint16_t color; } text;
        struct { int16_t cx, cy; uint16_t color; uint8_t up, size; } tri;
        struct { int16_t cx, cy, r; uint16_t color; } glow;
        struct { const uint16_t *pixels; int16_t w; } bitmap;
        struct { const adv_sprite_t *asset; uint16_t frame, color; bool tinted, dimmed; int16_t origin_x,origin_y; } sprite;
        struct { const adv_ninepatch_t *asset; } ninepatch;
        struct { ag_row_fn paint; const void *ctx; } rows;
    } u;
} ag_op_t;

typedef struct {
    ag_op_t ops[AG_MAX_OPS], prev[AG_MAX_OPS];
    int n, prev_n;
    nt_glyph_pool_t glyphs;
    bool full;                // redraw everything on the next frame
    int scene_id, prev_scene_id;
    ag_send_fn send;
    void *ctx;
    uint16_t *strip[2];
    int which;
    uint16_t width,height;
    uint32_t bytes;           // pixel bytes sent by the last frame
    bool overflow;            // a builder ran out of ops or glyphs this frame (host tests)
} ag_t;

// Strip buffers: two of AG_MAX_W x AG_STRIP pixels, including landscape use.
void ag_init(ag_t *g, uint16_t *strip0, uint16_t *strip1, ag_send_fn send, void *ctx);
bool ag_viewport(ag_t *g,int width,int height); // 240x320 or 320x240; invalidates on change
void ag_begin(ag_t *g, int scene_id);   // starts a new display list; a new scene redraws everything
void ag_invalidate(ag_t *g);
void ag_flush(ag_t *g);                 // diffs, composes and sends the dirty areas

// Builders (return false when the list is full). Colours are native RGB565.
bool ag_band(ag_t *g, int y, int h, uint16_t top, uint16_t bottom);
bool ag_rect(ag_t *g, int x, int y, int w, int h, int r, uint16_t fill, uint8_t alpha, uint16_t line, int line_w);
bool ag_circle(ag_t *g, int cx, int cy, int r, uint16_t fill, uint8_t alpha, uint16_t line, int line_w);
bool ag_text(ag_t *g, const lv_font_t *font, const char *utf8, int x, int baseline, nt_align_t align, uint16_t color);
bool ag_text_top(ag_t *g, const lv_font_t *font, const char *utf8, int x, int ink_top, nt_align_t align, uint16_t color);
bool ag_tri(ag_t *g, int cx, int cy, int size, bool up, uint16_t color);
bool ag_glow(ag_t *g, int cx, int cy, int r, uint16_t color);
bool ag_bitmap(ag_t *g, const uint16_t *pixels, int x, int y, int w, int h);
bool ag_rows(ag_t *g,ag_row_fn paint,const void *ctx,uint32_t generation);
bool ag_sprite(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y);
// Keep native pixel coordinates, but omit an explicitly bounded source region's
// exterior from painting and dirty bounds. No scaling or framebuffer allocation.
bool ag_sprite_crop(ag_t *g,const adv_sprite_t *asset,unsigned frame,int x,int y,int sx,int sy,int w,int h);
// Recolour every nontransparent pixel, e.g. the white stamp masters.
bool ag_sprite_tint(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y, uint16_t color);
bool ag_sprite_dim(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y);
bool ag_ninepatch(ag_t *g, const adv_ninepatch_t *asset, int x, int y, int w, int h);
int ag_text_width(const lv_font_t *font, const char *utf8);

// Per-op row painters (adv_shapes.c).
void ag_paint_band(const ag_op_t *op, int y, int x0, int x1, uint16_t *row);
void ag_paint_rect(const ag_op_t *op, int y, int x0, int x1, uint16_t *row);
void ag_paint_tri(const ag_op_t *op, int y, int x0, int x1, uint16_t *row);
void ag_paint_glow(const ag_op_t *op, int y, int x0, int x1, uint16_t *row);

static inline uint16_t ag_rgb(int r, int g, int b) { return (uint16_t)((r >> 3) << 11 | (g >> 2) << 5 | b >> 3); }

#ifdef __cplusplus
}
#endif
