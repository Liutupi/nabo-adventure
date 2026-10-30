// Native 320x240 SKY V2. NABO's pixels/anchor stay unchanged; only machine
// parts are smaller.
#include "adv_sky_v2.h"
#include "adv_ui_cards.h"
#include "adv_v2_rows.h"
#include "esp_heap_caps.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define K(n) SKY_V2_##n
#define T(n) SKY_V2_T_##n
#define RGB(r, g, b) ((uint16_t)(((r) >> 3) << 11 | ((g) >> 2) << 5 | (b) >> 3))
static struct
{
    const adv_sky_v2_t *p;
    uint32_t ms;
} context;
// Cache scenery indices: four bits for clouds, eight for the 27-colour hills.
// Release all 68.75 KiB on exit; allocation failure uses the original sprite rows.
typedef struct
{
    const adv_sprite_t *sprite;
    const uint8_t *pixels;
} sky_piece_t;
typedef struct
{
    const sky_piece_t *piece;
    int x, y;
} sky_draw_t;
static struct
{
    uint8_t *data;
    sky_piece_t piece[8];
    sky_draw_t draw[32];
    unsigned used;
} sky_cache;
static const char *const scenery_ids[] = {"game/space-v2/bg/cirrus", "game/space-v2/bg/cloud-far",
                                          "game/space-v2/bg/launch-far", "game/space-v2/bg/cloud-a"};
uint32_t ui_sky_v2_cache_bytes(void) { return sky_cache.data ? 70400 : 0; }
void ui_sky_v2_close(void)
{
    free(sky_cache.data);
    memset(&sky_cache, 0, sizeof(sky_cache));
}
static void prepare_scenery(void)
{
    sky_cache.used = 0;
    if (sky_cache.data)
        return;
    uint8_t *data = heap_caps_malloc(70400, MALLOC_CAP_INTERNAL);
    if (!data)
        return;
    unsigned offset = 0;
    for (unsigned n = 0; n < 4; n++)
    {
        const adv_asset_record_t *a = adv_assets_find(scenery_ids[n]);
        if (!a || a->piece_count != 2)
            goto fail;
        for (unsigned i = 0; i < 2; i++)
        {
            const adv_sprite_t *s = a->pieces[i].sprite;
            unsigned divisor = s->palette_size <= 16 ? 2 : 1;
            unsigned bytes = (unsigned)s->width * s->height / divisor;
            if (s->palette_size > 64 || s->width % 2 || offset + bytes > 70400)
                goto fail;
            sky_cache.piece[n * 2 + i] = (sky_piece_t){s, data + offset};
            uint8_t row[ADV_SPRITE_MAX_SIDE];
            for (unsigned y = 0; y < s->height; y++)
            {
                if (!adv_sprite_row(s, 0, y, row, sizeof(row)))
                    goto fail;
                if (divisor == 1)
                    memcpy(data + offset + y * s->width, row, s->width);
                else
                    for (unsigned x = 0; x < s->width; x += 2)
                        data[offset + (y * s->width + x) / 2] = row[x] | (row[x + 1] << 4);
            }
            offset += bytes;
        }
    }
    sky_cache.data = data;
    return;
fail:
    free(data);
}
static void scenery_row(const void *ctx, int y, int x0, int x1, uint16_t *row)
{
    const sky_draw_t *d = ctx;
    const adv_sprite_t *s = d->piece->sprite;
    int first = x0 > d->x ? x0 : d->x, last = x1 < d->x + s->width ? x1 : d->x + s->width;
    unsigned divisor = s->palette_size <= 16 ? 2 : 1;
    const uint8_t *src = d->piece->pixels + (y - d->y) * s->width / divisor;
    for (int x = first; x < last; x++)
    {
        unsigned sx = (unsigned)(x - d->x),
                 index = divisor == 1 ? src[sx] : (src[sx / 2] >> ((sx & 1) * 4)) & 15;
        if (index)
            row[x - x0] = s->palette[index];
    }
}
static void objects_row(const void *ctx, int y, int x0, int x1, uint16_t *row)
{
    (void)ctx;
    const adv_sky_v2_t *p = context.p;
    int cam = p->dist >> 8;
    static const int bound[] = {64, 128, 160, 186, 210}, speed[] = {230, 340, 450, 560};
    int vt = (int)(context.ms % 100000) * 60 / 1000;
    for (int l = 0; l < 4; l++)
    {
        int cy0 = bound[l] - K(ENV_DY) + 8, cy1 = bound[l + 1] - K(ENV_DY) + 8,
            v = speed[p->order[l]] * (p->section == SKY_V2_SEC_GUST ? 5 : 4) / 4;
        for (int i = 0; i < 6; i++)
        {
            unsigned h = v2_hash((uint32_t)(l * 97 + i * 13));
            int yy = cy0 + (int)(h % 1000u) * (cy1 - cy0) / 1000;
            if (y == yy)
            {
                int x = 320 - ((vt * v * 8 / 5 + (int)(h % 153600u)) / 256) % 380;
                v2_span(x, x + 8 + v * 9 / 256, x0, x1, row, 0xffff, l == p->layer ? 190 : 90);
            }
        }
    }
    if (y >= K(GROUND))
        v2_span(x0, x1, x0, x1, row, y >= 226 && y < 230 ? RGB(201, 180, 138) : RGB(127, 184, 92), 255);
    for (int i = 0; i < K(OBJS); i++)
    {
        const adv_sky_v2_obj_t *o = &p->objs[i];
        int x = o->x - cam;
        if (!o->type || x < -70 || x > 390)
            continue;
        if (o->type == T(HOUSE))
        {
            static const uint16_t wall[] = {RGB(242, 227, 198), RGB(223, 233, 242), RGB(246, 215, 180),
                                            RGB(232, 236, 214)};
            static const uint16_t roof[] = {RGB(208, 88, 74), RGB(77, 111, 168), RGB(122, 90, 168),
                                            RGB(63, 138, 106)};
            int color = (o->v >> 1) & 3;
            v2_rect_row(y, x0, x1, row, x - 22, o->y + 10, 44, K(GROUND) - o->y - 10, wall[color], 255);
            int r = y - o->y + 2;
            if (r >= 0 && r < 12)
                v2_span(x - 25 + r, x + 25 - r, x0, x1, row, roof[color], 255);
            v2_rect_row(y, x0, x1, row, x - 12, o->y + 18, 7, 8, RGB(40, 50, 80), 180);
            v2_rect_row(y, x0, x1, row, x + 6, o->y + 18, 7, 8, RGB(40, 50, 80), 180);
            v2_rect_row(y, x0, x1, row, x - 3, K(GROUND) - 12, 7, 12, RGB(138, 90, 58), 255);
            if (o->done != 2)
            {
                v2_rect_row(y, x0, x1, row, x - 5, o->y - 10, 10, 8,
                            o->done == 1 ? RGB(159, 224, 160)
                            : (o->v & 1) ? RGB(255, 207, 58)
                                         : RGB(232, 71, 58),
                            255);
                v2_rect_row(y, x0, x1, row, x - 3, o->y - 8, 6, 1, RGB(42, 42, 58), 255);
            }
        }
        else if (o->type == T(TREE))
        {
            v2_rect_row(y, x0, x1, row, x - 2, o->y + 20, 4, K(GROUND) - o->y - 20, RGB(107, 74, 50), 255);
            if (o->v)
            {
                int dy = y - o->y;
                if (dy >= 0 && dy < 44)
                {
                    int w = 7 - (dy < 22 ? 22 - dy : dy - 22) / 4;
                    if (w > 0)
                        v2_span(x - w, x + w, x0, x1, row, RGB(47, 122, 79), 255);
                }
            }
            else
                for (int k = 0; k < 3; k++)
                {
                    int dy = y - o->y - k * 12;
                    if (dy >= 0 && dy < 16)
                    {
                        int hw = (6 + k * 3) * dy / 16;
                        v2_span(x - hw, x + hw + 1, x0, x1, row, RGB(58, 138, 82), 255);
                    }
                }
        }
        else if (o->type == T(TANK) && !o->done)
        {
            v2_rect_row(y, x0, x1, row, x - 8, o->y - 20, 16, 5, RGB(255, 154, 58), 255);
            v2_rect_row(y, x0, x1, row, x - 1, o->y - 15, 2, 16, 0xffff, 255);
            v2_rect_row(y, x0, x1, row, x - 4, o->y - 1, 8, 10, RGB(210, 58, 58), 255);
        }
    }
    for (int i = 0; i < K(LETTERS); i++)
    {
        const adv_sky_v2_letter_t *l = &p->letters[i];
        if (l->on)
        {
            int x = (l->x >> 8) - cam, ly = l->y >> 8;
            v2_rect_row(y, x0, x1, row, x - 4, ly - 3, 8, 6, 0xffff, 255);
            v2_rect_row(y, x0, x1, row, x - 1, ly - 1, 2, 2, RGB(208, 88, 74), 255);
        }
    }
}
static void tiles(ag_t *g, const char *id, int scroll, int y)
{
    const adv_asset_record_t *a = adv_assets_find(id);
    if (!a)
        return;
    int w = a->width, off = scroll % w;
    for (int x = -off; x < 320; x += w)
    {
        unsigned n;
        for (n = 0; n < 4 && strcmp(id, scenery_ids[n]); n++)
        {
        }
        if (!sky_cache.data || n == 4 || sky_cache.used + a->piece_count > 32)
        {
            ui_art(g, id, 0, x, y);
            continue;
        }
        for (unsigned i = 0; i < a->piece_count; i++)
        {
            const adv_asset_piece_t *p = &a->pieces[i];
            int xx = x + p->x, yy = y + p->y;
            sky_draw_t *d = &sky_cache.draw[sky_cache.used++];
            *d = (sky_draw_t){&sky_cache.piece[n * 2 + i], xx, yy};
            uint32_t key = v2_hash((uint32_t)xx) ^ v2_hash((uint32_t)yy + 65536u) ^ (n * 2 + i);
            int first = yy > 0 ? yy : 0, last = yy + p->sprite->height < 240 ? yy + p->sprite->height : 240;
            if (first < last)
                ag_rows_region(g, scenery_row, d, first, last, key);
        }
    }
}
static void world(ag_t *g, const adv_sky_v2_t *p, int phase, uint32_t ms)
{
    int cam = p->dist >> 8, by = p->y >> 8;
    bool storm = p->section == SKY_V2_SEC_STORM;
    prepare_scenery();
    ag_band(g, 0, 132, storm ? RGB(59, 74, 110) : RGB(94, 159, 224),
            storm ? RGB(109, 122, 153) : RGB(169, 211, 242));
    ag_band(g, 132, 108, storm ? RGB(109, 122, 153) : RGB(169, 211, 242), RGB(248, 220, 180));
    tiles(g, "game/space-v2/bg/cirrus", cam * 8 / 100, 18);
    tiles(g, "game/space-v2/bg/cloud-far", cam * 15 / 100, 48);
    tiles(g, "game/space-v2/bg/launch-far", cam / 4, 128);
    tiles(g, "game/space-v2/bg/cloud-a", cam * 45 / 100, 92);
    context.p = p;
    context.ms = ms;
    ag_rows(g, objects_row, &context, v2_state_key(p, sizeof(*p)) ^ (ms / 17));
    for (int i = 0; i < K(OBJS); i++)
    {
        const adv_sky_v2_obj_t *o = &p->objs[i];
        int x = o->x - cam;
        if (!o->type || x < -70 || x > 390)
            continue;
        if (o->type == T(BIRD))
        {
            int q = o->v & 63, oy = o->y + ((q < 32 ? q : 64 - q) - 16) * 3 / 8;
            ui_art_frame_anchor(g, "sky_props/bird", ms / 133 % 4, x, oy + 8);
        }
        else if (o->type == T(STORM))
        {
            int t = o->t % K(STORM_CYCLE);
            bool warn = t >= K(STORM_WARN) && t < K(STORM_BOLT),
                 bolt = t >= K(STORM_BOLT) && t < K(STORM_END);
            if (warn || bolt)
                ag_rect(g, x - K(BOLT_HALF), o->y + K(STORM_H), 2 * K(BOLT_HALF), K(BOLT_LEN), 0,
                        RGB(255, 220, 90), bolt ? 110 : (t / 8 % 2 ? 60 : 24), 0, 0);
            if (bolt)
                ag_rect(g, x - 1, o->y + K(STORM_H), 3, K(BOLT_LEN), 0, RGB(255, 246, 160), 255, 0, 0);
            ui_art(g, "game/sky/thundercloud", 0, x - 24, o->y - 16);
        }
    }
    int bob = phase == ADV_RESULT ? 20 : 0;
    by += bob;
    ag_rect(g, K(BX) - 11, K(GROUND), 22, 4, 2, RGB(30, 50, 40), 65, 0, 0);
    ui_art_frame_anchor(g, "game/sky/v2/envelope", 0, K(BX), by - K(ENV_DY) - 32);
    ag_rect(g, K(BX) - 19, by - 33, 1, 16, 0, RGB(90, 64, 48), 255, 0, 0);
    ag_rect(g, K(BX) + 19, by - 33, 1, 16, 0, RGB(90, 64, 48), 255, 0, 0);
    if (p->heating)
        ag_tri(g, K(BX), by - 34, 6, true, RGB(255, 176, 58));
    ui_art_frame_anchor(g, "game/sky/v2/basket_back", 0, K(BX), by - 20);
    const char *action = phase == ADV_RESULT          ? "settlement_cheer"
                         : p->invuln > K(INVULN) - 24 ? "hit"
                         : p->heating                 ? "heat"
                         : p->venting                 ? "vent"
                                                      : "idle";
    char id[48];
    snprintf(id, sizeof(id), "sky_a/%s", action);
    ui_art_frame_anchor(g, id, ms / 83 % 6, K(BX), by - 4);
    ui_art_frame_anchor(g, "game/sky/v2/basket_front", 0, K(BX), by - 19);
}
static void hud(ag_t *g, const adv_sky_v2_t *p)
{
    ui_v2_hud(g, "燃料", p->res, p->score, p->combo, 1 + (p->combo / 3 < 4 ? p->combo / 3 : 4));
    static const int mid[] = {116, 144, 173, 195}, speed[] = {230, 340, 450, 560};
    for (int l = 0; l < 4; l++)
    {
        int y = mid[l] - K(ENV_DY) + 10, v = speed[p->order[l]] * (p->section == SKY_V2_SEC_GUST ? 5 : 4) / 4,
            len = 6 + (v - 200 + 15) / 30;
        ag_rect(g, 286, y - 6, 32, 12, 0, 0x18c5, l == p->layer ? 190 : 100, 0, 0);
        ag_rect(g, 316 - len, y - 1, len - 4, 2, 0, 0xffff, 255, 0, 0);
        ui_v2_text(g, "▶", 314, y, 12, NT_ALIGN_RIGHT, 0xffff);
    }
}
static void effects(ag_t *g, const adv_sky_v2_t *p)
{
    static const char *const section[] = {"",
                                          "小镇 · 房子多，连着送",
                                          "候鸟 · 鸟群很多",
                                          "雷暴 · 闪电前先下降",
                                          "彩虹 · 金邮筒变多",
                                          "顺风 · 所有风层更快"};
    for (int i = 0; i < 6; i++)
    {
        const adv_sky_v2_fx_t *e = &p->fx[i];
        if (!e->kind)
            continue;
        char line[40];
        const char *s = NULL;
        if (e->kind == SKY_V2_FX_DELIVER || e->kind == SKY_V2_FX_BULL)
        {
            snprintf(line, sizeof(line), "%s+%d", e->kind == SKY_V2_FX_BULL ? "正中! " : "", (int)e->val);
            s = line;
        }
        if (e->kind == SKY_V2_FX_MISS)
            s = "扔歪了";
        if (e->kind == SKY_V2_FX_HIT)
            s = "撞到了！";
        if (e->kind == SKY_V2_FX_GROUND)
            s = "擦到地面";
        if (e->kind == SKY_V2_FX_TANK)
            s = "+燃料";
        if (e->kind == SKY_V2_FX_NEAR)
            s = "好险";
        if (e->kind == SKY_V2_FX_SECTION && e->val >= 1 && e->val <= 5)
        {
            ag_rect(g, 0, 150, 320, 38, 0, 0x18c5, 200, 0, 0);
            ui_v2_text(g, "风向变了", 160, 160, 16, NT_ALIGN_CENTER, 0xff69);
            ui_v2_text(g, section[e->val], 160, 179, 12, NT_ALIGN_CENTER, 0xffff);
        }
        else if (s)
            ui_v2_text(g, s, e->x, e->y - e->t / 3, 12, NT_ALIGN_CENTER, 0xff69);
    }
}
void ui_draw_sky_v2_session(ag_t *g, const adv_model_t *m)
{
    static adv_sky_v2_t title;
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
    const adv_sky_v2_t *p = m->game;
    if (m->phase == ADV_TITLE)
    {
        adv_sky_v2_start(&title, 3);
        title.dist = (int32_t)(ms % 100000) * 25;
        int t = (int)(ms / 90 % 80);
        title.y = (150 + (t < 40 ? t - 20 : 60 - t)) * 256;
        p = &title;
    }
    world(g, p, m->phase, ms);
    if (m->phase == ADV_TITLE)
    {
        ui_v2_title(g, m);
        return;
    }
    hud(g, p);
    if (m->phase == ADV_PLAY)
        effects(g, p);
    if (m->phase == ADV_READY)
        ui_v2_ready(g, m);
    if (m->phase == ADV_PAUSE)
        ui_v2_pause(g);
    if (m->phase == ADV_RESULT)
    {
        char line[80], detail[60];
        snprintf(line, sizeof(line), "送达 %d/%d 家 · 正中 %d", (int)p->delivered, (int)p->houses,
                 (int)p->bulls);
        snprintf(detail, sizeof(detail), "金邮筒 %d · 最长 %d 连送", (int)p->golds, (int)p->best);
        ui_v2_result(g, m, ms - started, "燃料用完，平安降落", line, detail);
    }
}
