// Two readable climbing routes. Dense texture/holds compose by native rows,
// without framebuffers.
#include "adv_climb_v2.h"
#include "adv_ui_cards.h"
#include "adv_v2_rows.h"
#include "esp_heap_caps.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define K(n) CLIMB_V2_##n
#define RGB(r, g, b) ((uint16_t)(((r) >> 3) << 11 | ((g) >> 2) << 5 | (b) >> 3))
static struct
{
    const adv_climb_v2_t *p;
    int top;
    const adv_asset_record_t *tile[3][2], *hold[4], *canteen;
} context;
// Decode six opaque tiles once and preblend their three exact wall treatments.
// The 8.25 KiB cache is released on exit; allocation failure keeps the row
// decoder.
typedef struct
{
    uint8_t pixels[6][32 * 32];
    uint16_t palette[6][3][64];
} wall_cache_t;
static wall_cache_t *wall_cache;
uint32_t ui_climb_v2_cache_bytes(void) { return wall_cache ? sizeof(*wall_cache) : 0; }
void ui_climb_v2_close(void)
{
    free(wall_cache);
    wall_cache = NULL;
}
static void prepare_wall(void)
{
    if (wall_cache)
        return;
    wall_cache_t *c = heap_caps_malloc(sizeof(*c), MALLOC_CAP_INTERNAL);
    if (!c)
        return;
    for (unsigned n = 0; n < 6; n++)
    {
        const adv_asset_record_t *a = context.tile[n / 2][n % 2];
        if (!a || a->piece_count != 1 || a->pieces[0].x || a->pieces[0].y)
            goto fail;
        const adv_sprite_t *s = a->pieces[0].sprite;
        if (s->width != 32 || s->height != 32 || s->palette_size > 64)
            goto fail;
        for (unsigned y = 0; y < 32; y++)
        {
            uint8_t *dst = c->pixels[n] + y * 32;
            if (!adv_sprite_row(s, 0, y, dst, 32))
                goto fail;
            for (unsigned x = 0; x < 32; x++)
                if (!dst[x])
                    goto fail;
        }
        for (unsigned i = 0; i < s->palette_size; i++)
        {
            c->palette[n][0][i] = s->palette[i];
            c->palette[n][1][i] = nt_blend565(s->palette[i], RGB(22, 28, 44), 107 * 256 / 255);
            c->palette[n][2][i] = nt_blend565(c->palette[n][1][i], 0xffff, 18 * 256 / 255);
        }
    }
    wall_cache = c;
    return;
fail:
    free(c);
}
static void cached_tile_row(unsigned n, int x, int sy, int x0, int x1, uint16_t *row)
{
    int first = x > x0 ? x : x0, last = x + 32 < x1 ? x + 32 : x1;
    const uint8_t *src = wall_cache->pixels[n] + sy * 32;
    for (int xx = first; xx < last; xx++)
    {
        unsigned zone = xx >= 268 ? 0 : ((xx >= 70 && xx < 138) || (xx >= 182 && xx < 250)) ? 2 : 1;
        row[xx - x0] = wall_cache->palette[n][zone][src[xx - x]];
    }
}
static int lx(int lane) { return lane ? 216 : 104; }
static int hx(int r, int lane) { return lx(lane) + (((r + lane) & 1) ? 23 : -23); }
static void wall_row(const void *ctx, int y, int x0, int x1, uint16_t *row)
{
    (void)ctx;
    const adv_climb_v2_t *p = context.p;
    int top = context.top;
    int offset = ((top % 32) + 32) % 32;
    for (int ty = -32; ty < 272; ty += 32)
    {
        if (y < ty + offset || y >= ty + offset + 32)
            continue;
        int wy = top + 240 - ty, band = wy < 60 * 26 ? 0 : wy < 140 * 26 ? 1 : 2;
        for (int x = 52; x < 268; x += 32)
        {
            unsigned variant = v2_hash((uint32_t)(wy / 32 * 17 + x)) >> 31;
            const adv_asset_record_t *a = context.tile[band][variant];
            if (wall_cache)
                cached_tile_row((unsigned)band * 2 + variant, x, y - ty - offset, x0, x1, row);
            else if (a)
                v2_art_row(a, 0, x + a->anchor_x, ty + offset + a->anchor_y, y, x0, x1, row);
        }
    }
    if (!wall_cache)
    {
        v2_span(52, 268, x0, x1, row, RGB(22, 28, 44), 107);
        for (int lane = 0; lane < 2; lane++)
            v2_span(lx(lane) - 34, lx(lane) + 34, x0, x1, row, 0xffff, 18);
    }
    int r0 = p->row - 4;
    if (r0 < 0)
        r0 = 0;
    for (int r = r0; r <= p->row + 10 && r < p->genRow; r++)
    {
        int yy = K(NY) - 31 - r * K(STEP) + top;
        if (yy < -25 || yy > 265)
            continue;
        const adv_climb_v2_row_t *o = &p->rows[r % K(ROWS)];
        for (int l = 0; l < 2; l++)
        {
            int h = l ? o->h1 : o->h0, item = l ? o->i1 : o->i0, x = hx(r, l);
            if (!h)
            {
                v2_rect_row(y, x0, x1, row, lx(l) - 2, yy - 6, 3, 12, RGB(30, 30, 40), 120);
                continue;
            }
            v2_art_row(context.hold[h], 0, x, yy, y, x0, x1, row);
            int ix = x + (((r + l) & 1) ? -16 : 16);
            if (item == CLIMB_V2_ITEM_CANTEEN)
                v2_art_row(context.canteen, 0, ix, yy + 8, y, x0, x1, row);
            if (item == CLIMB_V2_ITEM_FLAG)
            {
                v2_rect_row(y, x0, x1, row, ix, yy - 14, 2, 20, RGB(107, 74, 50), 255);
                v2_rect_row(y, x0, x1, row, ix + 2, yy - 14, 11, 8, RGB(232, 71, 58), 255);
            }
        }
    }
}
static void world(ag_t *g, const adv_climb_v2_t *p, int phase, uint32_t ms)
{
    int top = p->row * K(STEP) - (p->tween > 0 ? p->tween * K(STEP) / K(TWEEN) * (p->stun ? -1 : 1) : 0);
    ag_band(g, 0, 240, p->row > 120 ? RGB(61, 111, 184) : RGB(106, 168, 232), RGB(233, 244, 251));
    int base = 200 + (p->row * 35 / 100 < 120 ? p->row * 35 / 100 : 120);
    for (int i = -1; i < 6; i++)
    {
        int height = 60 + (int)(v2_hash((uint32_t)(i + 3)) % 50);
        ag_tri(g, i * 70 + 20, base - height / 2, height / 2, true, RGB(159, 182, 214));
    }
    context.p = p;
    context.top = top;
    static const char *const bands[] = {"grey", "cold", "snow"};
    for (int b = 0; b < 3; b++)
        for (int i = 0; i < 2; i++)
        {
            char id[48];
            snprintf(id, sizeof(id), "game/climb/tiles/%s-%d", bands[b], i);
            context.tile[b][i] = adv_assets_find(id);
        }
    context.hold[1] = adv_assets_find("game/climb/props/hold-normal");
    context.hold[2] = adv_assets_find("game/climb/props/hold-fragile");
    context.hold[3] = adv_assets_find("game/climb/props/hold-ice");
    context.canteen = adv_assets_find("game/climb/props/canteen");
    prepare_wall();
    ag_rows(g, wall_row, &context, v2_state_key(p, sizeof(*p)));
    int next = p->row + 1, x = hx(next, p->lane), y = K(NY) - 31 - next * K(STEP) + top;
    const adv_climb_v2_row_t *o = &p->rows[next % K(ROWS)];
    int h = p->lane ? o->h1 : o->h0;
    if (h && !p->trav)
    {
        ag_circle(g, x, y, 13, 0, 0, RGB(255, 230, 120), 2);
        ui_v2_text(g, ((next + p->lane) & 1) ? "▶" : "◀", x + (((next + p->lane) & 1) ? 20 : -20), y, 12,
                   NT_ALIGN_CENTER, RGB(255, 230, 120));
    }
    int side = (p->row + p->lane) & 1;
    const char *dir = side ? "right" : "left", *action = "grip_idle";
    int f = ms / 133 % 6, ax = lx(p->lane), ay = K(NY) + 10;
    if (p->trav)
    {
        int t = K(TRAVERSE) - p->trav;
        ax += (lx(p->lane ^ 1) - ax) * t / K(TRAVERSE);
        ay -= 4 * 10 * t * (K(TRAVERSE) - t) / (K(TRAVERSE) * K(TRAVERSE));
        action = "jump";
        dir = p->lane ? "left" : "right";
        f = t * 6 / K(TRAVERSE);
    }
    else if (p->stun)
    {
        action = "slide";
        f = (K(STUN) - p->stun) / 4;
    }
    else if (p->ice)
    {
        action = "charge";
        f = (K(ICE_HOLD) - p->ice) / 4;
        if (f > 3)
            f = 3;
    }
    else if (p->tween)
    {
        action = "switch_grab";
        f = K(TWEEN) - p->tween;
    }
    ag_rect(g, ax + 4, ay - 18, 1, 240 - ay + 18, 0, RGB(208, 87, 63), 255, 0, 0);
    char id[64];
    if (phase == ADV_RESULT)
    {
        snprintf(id, sizeof(id), "climb_a/settlement_cheer");
        ax = 160;
        f = 7;
    }
    else
        snprintf(id, sizeof(id), "climb_a/%s_%s", action, dir);
    ui_art_frame_anchor(g, id, (unsigned)f, ax, ay);
    if (p->ice)
    {
        ui_v2_text(g, "按住", hx(p->row, p->lane), 77, 12, NT_ALIGN_CENTER, RGB(191, 239, 255));
        ag_rect(g, lx(p->lane) - 18, 86, 36 * (K(ICE_HOLD) - p->ice) / K(ICE_HOLD), 3, 0, RGB(191, 239, 255),
                255, 0, 0);
    }
    for (int i = 0; i < K(ROCKS); i++)
    {
        const adv_climb_v2_rock_t *rock = &p->rocks[i];
        if (!rock->on)
            continue;
        int xx = lx(rock->lane);
        if (rock->t)
        {
            ag_rect(g, xx - 26, 18, 52, K(NY) - 30, 0, RGB(255, 90, 60),
                    rock->t < 30 && ms / 60 % 2 ? 120 : 46, 0, 0);
            ag_tri(g, xx, 28, 9, true, RGB(255, 90, 60));
            ui_v2_text(g, "!", xx, 30, 12, NT_ALIGN_CENTER, 0xffff);
        }
        else
            ui_art_frame_anchor(g, "game/climb/props/falling-rock", 0, xx, rock->y);
    }
    if (p->section == CLIMB_V2_SEC_NIGHT)
    {
        int left = lx(p->lane) - 70;
        ag_rect(g, 0, 0, 320, 45, 0, RGB(10, 14, 34), 220, 0, 0);
        ag_rect(g, 0, 195, 320, 45, 0, RGB(10, 14, 34), 220, 0, 0);
        ag_rect(g, 0, 45, left, 150, 0, RGB(10, 14, 34), 220, 0, 0);
        ag_rect(g, left + 140, 45, 320 - left - 140, 150, 0, RGB(10, 14, 34), 220, 0, 0);
    }
}
static void effects(ag_t *g, const adv_climb_v2_t *p)
{
    static const char *const SECTION[] = {"",
                                          "落石区 · 看到红色警告就换线",
                                          "冰壁 · 冰点要按住抓牢",
                                          "碎石段 · 碎石点别停留",
                                          "入夜 · 只看得清身边",
                                          "冲刺 · 节奏分翻倍"};
    for (int i = 0; i < 6; i++)
    {
        const adv_climb_v2_fx_t *e = &p->fx[i];
        if (!e->kind)
            continue;
        const char *s = NULL;
        if (e->kind == CLIMB_V2_FX_SLIP)
            s = "打滑";
        if (e->kind == CLIMB_V2_FX_ROCK)
            s = "被落石砸到！";
        if (e->kind == CLIMB_V2_FX_CRUMBLE)
            s = "碎了！";
        if (e->kind == CLIMB_V2_FX_NOHOLD)
            s = "这条线断了 · 按中键换线";
        if (e->kind == CLIMB_V2_FX_CANTEEN)
            s = "+握力";
        if (e->kind == CLIMB_V2_FX_SECTION && e->val >= 1 && e->val <= 5)
        {
            ag_rect(g, 0, 192, 320, 32, 0, 0x18c5, 220, 0, 0);
            ui_v2_text(g, SECTION[e->val], 160, 208, 12, NT_ALIGN_CENTER, 0xff69);
        }
        else if (s)
            ui_v2_text(g, s, 160, 188 - e->t / 4, 12, NT_ALIGN_CENTER, 0xff69);
    }
}
void ui_draw_climb_v2_session(ag_t *g, const adv_model_t *m)
{
    static adv_climb_v2_t title;
    static int old_phase = -1;
    static uint32_t old_seed, started;
    uint32_t ms = ui_millis();
    if (old_phase != m->phase || old_seed != m->seed)
    {
        old_phase = m->phase;
        old_seed = m->seed;
        started = ms;
    }
    ag_begin(g, m->phase == ADV_TITLE    ? UI_SCENE_TITLE
                : m->phase == ADV_RESULT ? UI_SCENE_RESULT
                                         : UI_SCENE_PLAY);
    const adv_climb_v2_t *p = m->game;
    if (m->phase == ADV_TITLE)
    {
        adv_climb_v2_start(&title, 5);
        title.row = (int)(ms / 270) % 120;
        title.genRow = title.row + 15;
        for (int i = 0; i < K(ROWS); i++)
            title.rows[i] = (adv_climb_v2_row_t){1, i % 5 ? 1 : 2, 0, 0};
        p = &title;
    }
    world(g, p, m->phase, ms);
    if (m->phase == ADV_TITLE)
    {
        ui_v2_title(g, m);
        return;
    }
    ui_v2_hud(g, "握力", p->res, p->score, p->combo, 1 + (p->combo / 6 < 4 ? p->combo / 6 : 4));
    if (m->phase == ADV_PLAY)
        effects(g, p);
    if (m->phase == ADV_READY)
        ui_v2_ready(g, m);
    if (m->phase == ADV_PAUSE)
        ui_v2_pause(g);
    if (m->phase == ADV_RESULT)
    {
        char line[80], detail[60];
        snprintf(line, sizeof(line), "%d m · 抓握 %d · 最长 %d 连", (int)p->meters, (int)p->grabs,
                 (int)p->best);
        snprintf(detail, sizeof(detail), "换线 %d · 打滑 %d · 落石 %d", (int)p->traverses, (int)p->slips,
                 (int)p->rockHits);
        ui_v2_result(g, m, ms - started, "握力用完，安全绳接住了你", line, detail);
    }
}
