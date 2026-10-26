#include "adv_gfx.h"

#include <string.h>
#include <stdio.h>
#ifdef ESP_PLATFORM
#include "esp_cpu.h"
#endif
static bool s_profile_pending,s_profiling;
static uint32_t s_profile_cycles[16],s_profile_calls[16];
void ag_profile_next(void){s_profile_pending=true;}
static uint32_t cycles(void){
#ifdef ESP_PLATFORM
    return esp_cpu_get_cycle_count();
#else
    return 0;
#endif
}

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
    g->width=AG_W;g->height=AG_H;
    g->strip_rows=AG_STRIP;
    g->prev_scene_id = -1;
}

bool ag_strips(ag_t *g,uint16_t *strip0,uint16_t *strip1,unsigned rows)
{
    if(!g||!strip0||!strip1||(rows!=8&&rows!=16&&rows!=32))return false;
    g->strip[0]=strip0;g->strip[1]=strip1;g->strip_rows=(uint16_t)rows;g->which=0;
    return true;
}

bool ag_viewport(ag_t *g,int width,int height)
{
    if(!g||!((width==240&&height==320)||(width==320&&height==240)))return false;
    if(g->width!=width||g->height!=height){g->width=(uint16_t)width;g->height=(uint16_t)height;g->full=true;}
    return true;
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
    ag_op_t *op = add(g, AG_BAND, 0, y, g->width, y + h);
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

bool ag_text_top(ag_t *g, const lv_font_t *font, const char *utf8, int x, int ink_top, nt_align_t align, uint16_t color)
{
    return ag_text(g, font, utf8, x, ink_top + nt_text_ascent(font, utf8), align, color);
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

bool ag_rows(ag_t *g,ag_row_fn paint_row,const void *ctx,uint32_t generation)
{
    return g&&ag_rows_region(g,paint_row,ctx,0,g->height,generation);
}

bool ag_rows_region(ag_t *g,ag_row_fn paint_row,const void *ctx,int y0,int y1,uint32_t generation)
{
    if(!g||!paint_row||!ctx||y0<0||y1>g->height||y0>=y1)return false;
    ag_op_t *op=add(g,AG_ROWS,0,y0,g->width,y1);
    if(!op)return false;
    op->u.rows.paint=paint_row;op->u.rows.ctx=ctx;
    seal(op,mix(mix((uint32_t)(uintptr_t)ctx,(uint32_t)((uint64_t)(uintptr_t)ctx>>32)),generation));
    return true;
}

static bool sprite(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y,
                   bool tinted, uint16_t color, bool dimmed,const int *crop)
{
    if (!adv_sprite_frame_valid(asset, frame) || x < INT16_MIN || y < INT16_MIN ||
        x > INT16_MAX - asset->width || y > INT16_MAX - asset->height) return false;
    int sx=0,sy=0,cw=asset->width,ch=asset->height;
    if(crop){
        sx=crop[0];sy=crop[1];cw=crop[2];ch=crop[3];
        if(sx<0||sy<0||sx>=asset->width||sy>=asset->height||cw<=0||ch<=0||cw>asset->width-sx||ch>asset->height-sy)return false;
    }
    ag_op_t *op = add(g, AG_SPRITE, x+sx, y+sy, x+sx+cw, y+sy+ch);
    if (!op) return false;
    op->u.sprite.asset = asset;
    op->u.sprite.frame = (uint16_t)frame;
    op->u.sprite.tinted = tinted;
    op->u.sprite.color = color;
    op->u.sprite.dimmed = dimmed;
    op->u.sprite.origin_x=(int16_t)x;op->u.sprite.origin_y=(int16_t)y;
    uintptr_t ptr = (uintptr_t)asset;
    uint32_t h = (uint32_t)ptr;
    // Include both halves on 64-bit hosts, without shifting a 32-bit C3 pointer.
    h = mix(h, (uint32_t)((uint64_t)ptr >> 32));
    h=mix(mix(h,(uint16_t)x),(uint16_t)y);
    seal(op, mix(mix(mix(mix(h, frame), tinted), color), dimmed));
    return true;
}

bool ag_sprite(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y)
{
    return sprite(g, asset, frame, x, y, false, 0, false,NULL);
}

bool ag_sprite_crop(ag_t *g,const adv_sprite_t *s,unsigned f,int x,int y,int sx,int sy,int w,int h)
{
    const int crop[]={sx,sy,w,h};return sprite(g,s,f,x,y,false,0,false,crop);
}

bool ag_sprite_tint(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y, uint16_t color)
{
    return sprite(g, asset, frame, x, y, true, color, false,NULL);
}

bool ag_sprite_dim(ag_t *g, const adv_sprite_t *asset, unsigned frame, int x, int y)
{
    return sprite(g, asset, frame, x, y, false, 0, true,NULL);
}

bool ag_ninepatch(ag_t *g, const adv_ninepatch_t *asset, int x, int y, int w, int h)
{
    if (!adv_ninepatch_valid(asset) || w < asset->tile[0]->width + asset->tile[2]->width ||
        h < asset->tile[0]->height + asset->tile[6]->height || x < INT16_MIN || y < INT16_MIN ||
        w > INT16_MAX || h > INT16_MAX || x > INT16_MAX - w || y > INT16_MAX - h) return false;
    ag_op_t *op = add(g, AG_NINEPATCH, x, y, x + w, y + h);
    if (!op) return false;
    op->u.ninepatch.asset = asset;
    uintptr_t ptr = (uintptr_t)asset;
    seal(op, mix((uint32_t)ptr, (uint32_t)((uint64_t)ptr >> 32)));
    return true;
}

// ---------- dirty rectangles ----------

typedef struct { int16_t x0, y0, x1, y1; } rect_t;

static void add_rect(const ag_t *g,rect_t *r, int *n, int x0, int y0, int x1, int y1, bool *overflow)
{
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > g->width) x1 = g->width;
    if (y1 > g->height) y1 = g->height;
    if (x0 >= x1 || y0 >= y1) return;
    // Merge with anything it touches (8 px slack keeps the list short).
    for (int i = 0; i < *n; i++) {
        if (x0 <= r[i].x1 + 8 && r[i].x0 <= x1 + 8 && y0 <= r[i].y1 + 8 && r[i].y0 <= y1 + 8) {
            int a = x0 < r[i].x0 ? x0 : r[i].x0, b = y0 < r[i].y0 ? y0 : r[i].y0;
            int c = x1 > r[i].x1 ? x1 : r[i].x1, d = y1 > r[i].y1 ? y1 : r[i].y1;
            r[i] = r[--*n];
            add_rect(g,r, n, a, b, c, d, overflow);
            return;
        }
    }
    if (*n >= AG_MAX_RECTS) { *overflow = true; return; }
    r[*n].x0 = (int16_t)x0; r[*n].y0 = (int16_t)y0; r[*n].x1 = (int16_t)x1; r[*n].y1 = (int16_t)y1;
    ++*n;
}

// ---------- composition ----------

static void paint_op(ag_t *g, const ag_op_t *op, int y, int x0, int x1, uint16_t *restrict row)
{
    if (y < op->y0 || y >= op->y1 || x1 <= op->x0 || x0 >= op->x1) return;
    switch (op->kind) {
    case AG_ROWS: op->u.rows.paint(op->u.rows.ctx,y,x0,x1,row); break;
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
        if (!adv_sprite_row(s, op->u.sprite.frame, (unsigned)(y - op->u.sprite.origin_y), indices, sizeof(indices))) break;
        int first = x0 > op->x0 ? x0 : op->x0;
        int last = x1 < op->x1 ? x1 : op->x1;
        for (int x = first; x < last; x++) {
            uint8_t index = indices[x - op->u.sprite.origin_x];
            if (index) {
                uint16_t color = op->u.sprite.tinted ? op->u.sprite.color : s->palette[index];
                // Halve each RGB565 channel independently, without cross-channel carries.
                row[x - x0] = op->u.sprite.dimmed ? (color & 0xf7deu) >> 1 : color;
            }
        }
        break;
    }
    case AG_NINEPATCH: {
        int first = x0 > op->x0 ? x0 : op->x0;
        int last = x1 < op->x1 ? x1 : op->x1;
        (void)adv_ninepatch_row(op->u.ninepatch.asset, (unsigned)(op->x1 - op->x0),
                               (unsigned)(op->y1 - op->y0), (unsigned)(y - op->y0),
                               (unsigned)(first - op->x0), (unsigned)(last - op->x0), row + first - x0);
        break;
    }
    default: break;
    }
}

static void paint(ag_t *g,const ag_op_t *op,int y,int x0,int x1,uint16_t *row)
{
    if(!s_profiling){paint_op(g,op,y,x0,x1,row);return;}
    uint32_t at=cycles();paint_op(g,op,y,x0,x1,row);
    if(op->kind<16){s_profile_cycles[op->kind]+=cycles()-at;s_profile_calls[op->kind]++;}
}
static void compose(ag_t *g, int x0, int y0, int x1, int y1)
{
    int w = x1 - x0;
    for (int y = y0; y < y1; y += g->strip_rows) {
        int h = y + g->strip_rows < y1 ? g->strip_rows : y1 - y;
        uint16_t *px = g->strip[g->which];
        g->which ^= 1;
        memset(px, 0, (size_t)(w * h) * 2);
        // Rows are independent; keep each layer's code, palette and RLE rows hot
        // across the strip, and skip layers outside it before calling painters.
        for(int i=0;i<g->n;i++){
            const ag_op_t *op=&g->ops[i];
            if(x1<=op->x0||x0>=op->x1)continue;
            int first=y>op->y0?y:op->y0,last=y+h<op->y1?y+h:op->y1;
            for(int yy=first;yy<last;yy++)paint(g,op,yy,x0,x1,px+(yy-y)*w);
        }
        for (int k = 0; k < w * h; k++) px[k] = (uint16_t)(px[k] << 8 | px[k] >> 8);   // panel order
        g->send(g->ctx, x0, y, w, h, px);
        g->bytes += (uint32_t)(w * h * 2);
    }
}

void ag_flush(ag_t *g)
{
    s_profiling=s_profile_pending;s_profile_pending=false;
    if(s_profiling){memset(s_profile_cycles,0,sizeof(s_profile_cycles));memset(s_profile_calls,0,sizeof(s_profile_calls));}
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
            if (j >= g->prev_n || j != i) add_rect(g,rects, &n, op->x0, op->y0, op->x1, op->y1, &overflow);
        }
        for (int j = 0; j < g->prev_n && !overflow; j++)
            if (!matched_prev[j]) add_rect(g,rects, &n, g->prev[j].x0, g->prev[j].y0, g->prev[j].x1, g->prev[j].y1, &overflow);
    }
    g->bytes = 0;
    if (overflow) compose(g, 0, 0, g->width, g->height);
    else
        for (int i = 0; i < n; i++) compose(g, rects[i].x0, rects[i].y0, rects[i].x1, rects[i].y1);
    memcpy(g->prev, g->ops, sizeof(ag_op_t) * (size_t)g->n);
    g->prev_n = g->n;
    g->prev_scene_id = g->scene_id;
    g->full = false;
    if(s_profiling){
#ifdef ESP_PLATFORM
        flockfile(stdout);
#endif
        printf("@gfx_profile {\"bytes\":%u,\"ops\":%d,\"kinds\":[",(unsigned)g->bytes,g->n);
        for(unsigned i=0;i<16;i++)printf("%s[%u,%u,%u]",i?",":"",i,(unsigned)s_profile_cycles[i],(unsigned)s_profile_calls[i]);
        puts("]}");
#ifdef ESP_PLATFORM
        funlockfile(stdout);
#endif
        s_profiling=false;
    }
}
