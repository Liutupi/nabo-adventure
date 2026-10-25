// Production renderer into an emulated panel; synthetic assets only.
#include "adv_gfx.h"
#include <string.h>

static ag_t gfx;
static uint16_t strips[2][AG_W * AG_STRIP], pixels[AG_W * AG_H];

static void send(void *ctx, int x, int y, int w, int h, uint16_t *px)
{
    (void)ctx;
    for (int r = 0; r < h; r++)
        for (int c = 0; c < w; c++)
            pixels[(y + r) * AG_W + x + c] = __builtin_bswap16(px[r * w + c]);
}

void sprite_host_reset(void)
{
    memset(pixels, 0, sizeof(pixels));
    ag_init(&gfx, strips[0], strips[1], send, NULL);
}

void sprite_host_begin(int full)
{
    if (full) ag_invalidate(&gfx);
    ag_begin(&gfx, 42);
    ag_rect(&gfx, 0, 0, AG_W, AG_H, 0, 0x1357, 255, 0, 0);
}

int sprite_host_add(const adv_sprite_t *s, unsigned frame, int x, int y)
{
    return ag_sprite(&gfx, s, frame, x, y);
}

int sprite_host_tint(const adv_sprite_t *s, unsigned frame, int x, int y, uint16_t color)
{
    return ag_sprite_tint(&gfx, s, frame, x, y, color);
}

int sprite_host_dim(const adv_sprite_t *s, unsigned frame, int x, int y)
{
    return ag_sprite_dim(&gfx, s, frame, x, y);
}

int sprite_host_crop(const adv_sprite_t *s,unsigned f,int x,int y,int sx,int sy,int w,int h)
{
    return ag_sprite_crop(&gfx,s,f,x,y,sx,sy,w,h);
}

unsigned sprite_host_flush(uint16_t *out)
{
    ag_flush(&gfx);
    memcpy(out, pixels, sizeof(pixels));
    return gfx.bytes;
}

int sprite_host_overflow(void) { return gfx.overflow; }

int sprite_host_patch(const adv_ninepatch_t *patch, int x, int y, int w, int h)
{
    return ag_ninepatch(&gfx, patch, x, y, w, h);
}
