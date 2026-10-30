// POST V2 native landscape: speed, mail windows, signals and limited bridges are visible in-world.
#include "adv_post_v2.h"
#include "adv_ui_cards.h"
#include "adv_v2_rows.h"
#include <stdio.h>
#include <stdlib.h>
#define K(n) POST_V2_##n
#define T(n) POST_V2_T_##n
#define RGB(r, g, b) ((uint16_t)(((r) >> 3) << 11 | ((g) >> 2) << 5 | (b) >> 3))
static struct {
    const adv_post_v2_t *p;
    const adv_asset_record_t *track;
} context;
static void scenery_row(const void *ctx, int y, int x0, int x1, uint16_t *row)
{
    (void)ctx;
    const adv_post_v2_t *p = context.p;
    int cam = p->dist >> 8;
    if (y >= 150 && y < 192)
        v2_span(x0, x1, x0, x1, row, p->section == POST_V2_SEC_NIGHT ? RGB(42, 68, 52) : RGB(148, 202, 106),
                255);
    if (y >= 192)
        v2_span(x0, x1, x0, x1, row, RGB(169, 154, 124), 255);
    for (int i = 0; i < K(EVENTS); i++) {
        const adv_post_v2_event_t *e = &p->ev[i];
        int x = e->x - cam;
        if (!e->type)
            continue;
        if (e->type == T(LIMIT) && y >= K(RAIL) + 2)
            v2_span(x, x + e->b, x0, x1, row, RGB(90, 160, 200), 255);
        if (x < -90 || x > 380)
            continue;
        if (e->type == T(NET)) {
            v2_rect_row(y, x0, x1, row, x - 1, K(RAIL) - 46, 3, 46, RGB(90, 64, 48), 255);
            uint16_t c = e->done == 1 ? RGB(159, 224, 160) : RGB(201, 93, 80);
            v2_rect_row(y, x0, x1, row, x - 10, K(RAIL) - 56, 20, 3, c, 255);
            v2_rect_row(y, x0, x1, row, x - 10, K(RAIL) - 56, 2, 14, c, 255);
            v2_rect_row(y, x0, x1, row, x + 8, K(RAIL) - 56, 2, 14, c, 255);
            v2_rect_row(y, x0, x1, row, x - 8, K(RAIL) - 42, 16, 2, 0xffff, 200);
        } else if (e->type == T(CRANE)) {
            v2_rect_row(y, x0, x1, row, x + 14, K(RAIL) - 74, 3, 74, RGB(58, 74, 90), 255);
            v2_rect_row(y, x0, x1, row, x - 2, K(RAIL) - 74, 19, 3, RGB(58, 74, 90), 255);
            if (!e->done) {
                v2_rect_row(y, x0, x1, row, x, K(RAIL) - 71, 1, 7, RGB(58, 74, 90), 255);
                v2_rect_row(y, x0, x1, row, x - 7, K(RAIL) - 64, 14, 16, RGB(200, 165, 106), 255);
            }
        } else if (e->type == T(LIMIT)) {
            v2_rect_row(y, x0, x1, row, x - 1, K(RAIL) - 40, 2, 40, RGB(90, 64, 48), 255);
            int dy = abs(y - (K(RAIL) - 46));
            if (dy < 14)
                v2_span(x - 14 + dy, x + 15 - dy, x0, x1, row, RGB(255, 211, 74), 255);
        } else if (e->type == T(SIGNAL)) {
            bool red = e->t < 0 || (int)p->tick - e->t < e->a;
            v2_rect_row(y, x0, x1, row, x - 1, K(RAIL) - 62, 3, 62, RGB(42, 52, 64), 255);
            v2_rect_row(y, x0, x1, row, x - 6, K(RAIL) - 76, 13, 24, RGB(42, 52, 64), 255);
            v2_rect_row(y, x0, x1, row, x - 3, K(RAIL) - 73, 7, 7, red ? RGB(255, 74, 58) : RGB(90, 42, 42),
                        255);
            v2_rect_row(y, x0, x1, row, x - 3, K(RAIL) - 61, 7, 7, red ? RGB(42, 74, 42) : RGB(90, 255, 122),
                        255);
        }
    }
    const adv_asset_record_t *a = context.track;
    if (a)
        for (int x = -(cam % a->width); x < 320; x += a->width)
            v2_art_row(a, 0, x + a->anchor_x, K(RAIL) - 28 + a->anchor_y, y, x0, x1, row);
}
static void backdrop(ag_t *g, const adv_post_v2_t *p)
{
    int cam = p->dist >> 8;
    bool night = p->section == POST_V2_SEC_NIGHT;
    ag_band(g, 0, 240, night ? RGB(29, 42, 74) : RGB(120, 184, 216),
            night ? RGB(61, 74, 106) : RGB(216, 236, 216));
    const adv_asset_record_t *a = adv_assets_find("game/post/tiles/far-mountains");
    if (a)
        for (int x = -((cam / 5) % a->width); x < 320; x += a->width)
            ui_art(g, a->id, 0, x, 116);
    context.p = p;
    context.track = adv_assets_find("game/post/tiles/track-straight");
    ag_rows(g, scenery_row, &context, v2_state_key(p, sizeof(*p)));
}
static void train(ag_t *g, const adv_post_v2_t *p, int phase, uint32_t ms)
{
    int left = K(LOCO_X) - 48, top = K(RAIL) - 77;
    ui_art(g, "game/post/props/carriage", 0, left - 66, K(RAIL) - 40);
    for (int i = 0; i < p->bags && i < 5; i++)
        ag_rect(g, left - 58 + i * 11, K(RAIL) - 52, 10, 12, 3, RGB(200, 165, 106), 255, 0, 0);
    for (int i = 0; i < 2 + (p->v >> 8); i++) {
        int age = (int)((ms / 17 + i * 23) % 60);
        ag_circle(g, K(LOCO_X) + 22 - age * (4 + p->v / 90) / 10, top + 10 - age * 55 / 100, 3 + age / 9,
                  RGB(245, 245, 240), (uint8_t)(190 - age * 3), 0, 0);
    }
    ui_art_frame_anchor(g, "post_props/wheel-cycle", (unsigned)(p->dist >> 8) / 6 % 4, K(LOCO_X),
                        K(RAIL) + 4);
    ui_art(g, "game/post/props/locomotive-body", 0, left, top);
    const char *action = "idle";
    unsigned f = ms / 133 % 6;
    for (int i = 0; i < 6; i++) {
        const adv_post_v2_fx_t *e = &p->fx[i];
        if (!e->kind || e->t >= 24)
            continue;
        if (e->kind == POST_V2_FX_NET || e->kind == POST_V2_FX_PERFECT || e->kind == POST_V2_FX_CRANE) {
            action = e->t < 12 ? "throw" : "delivered";
            f = (unsigned)(e->t % 12) / 2;
        } else if (e->kind == POST_V2_FX_RED || e->kind == POST_V2_FX_ANIMAL ||
                   e->kind == POST_V2_FX_DERAIL) {
            action = "hit";
            f = (unsigned)e->t / 4;
        }
    }
    if (phase == ADV_RESULT) {
        action = "delivered";
        f = 5;
    }
    char id[48];
    snprintf(id, sizeof(id), "post_a/%s", action);
    ui_art_frame_anchor(g, id, f, left + 25, top + 49);
    ui_art(g, "game/post/props/cab-foreground", 0, left, top);
}
static void events(ag_t *g, const adv_post_v2_t *p)
{
    int cam = p->dist >> 8;
    char str[24];
    for (int i = 0; i < K(EVENTS); i++) {
        const adv_post_v2_event_t *e = &p->ev[i];
        int x = e->x - cam;
        if (!e->type || x < -90 || x > 380)
            continue;
        if (e->type == T(ANIMAL) && e->done != 1) {
            bool on = e->t < 0 || (int)p->tick - e->t < e->a;
            ui_art(g, e->b ? "game/post/props/cow" : "game/post/props/sheep", 0, x - (e->b ? 24 : 20),
                   K(RAIL) - (e->b ? 34 : 28) + (on ? 0 : 25));
        }
        if (e->type == T(LIMIT)) {
            snprintf(str, sizeof(str), "%d", (int)e->a * 120 / K(VMAX));
            ui_v2_text(g, str, x, K(RAIL) - 46, 12, NT_ALIGN_CENTER, 0x18c5);
        }
    }
    int bd = 1000000000;
    const adv_post_v2_event_t *best = NULL;
    for (int i = 0; i < K(EVENTS); i++) {
        const adv_post_v2_event_t *e = &p->ev[i];
        if ((e->type == T(NET) || e->type == T(CRANE)) && !e->done) {
            int d = abs(e->x - cam - K(DOOR_X));
            if (d < bd) {
                bd = d;
                best = e;
            }
        }
    }
    if (best && bd <= 70) {
        bool can = best->type == T(CRANE) || p->bags > 0;
        uint16_t color = !can               ? 0x9cd3
                         : bd <= K(PERFECT) ? RGB(255, 211, 74)
                         : bd <= K(WINDOW)  ? RGB(159, 224, 160)
                                            : 0xffff;
        int y = K(RAIL) - (best->type == T(CRANE) ? 58 : 50);
        ag_rect(g, K(DOOR_X) - K(WINDOW), y - 8, 2, 16, 0, color, 255, 0, 0);
        ag_rect(g, K(DOOR_X) + K(WINDOW), y - 8, 2, 16, 0, color, 255, 0, 0);
        if (bd <= K(WINDOW) && can)
            ui_v2_text(g, best->type == T(CRANE) ? "抓!" : "扔!", K(DOOR_X), y - 18, 12, NT_ALIGN_CENTER,
                       color);
        if (!can && bd < 40)
            ui_v2_text(g, "没邮袋了 · 去吊架抓", K(DOOR_X), y - 18, 12, NT_ALIGN_CENTER, RGB(255, 224, 160));
    }
}
static void gauge_row(const void *ctx, int y, int x0, int x1, uint16_t *row)
{
    const adv_post_v2_t *p = ctx;
    static const int vx[] = {-1024, -1004, -946, -851, -724, -569, -392, -200, 0,
                             200,   392,   569,  724,  851,  946,  1004, 1024};
    static const int vy[] = {0,     -200, -392, -569, -724, -851, -946, -1004, -1024,
                             -1004, -946, -851, -724, -569, -392, -200, 0};
    int v = (int)p->v * 16, index = v / 1024, part = v % 1024;
    if (index > 15) {
        index = 15;
        part = 1024;
    }
    int nx = vx[index] + (vx[index + 1] - vx[index]) * part / 1024,
        ny = vy[index] + (vy[index + 1] - vy[index]) * part / 1024;
    int z = (int)p->zone * 16, zi = z / 1024, zp = z % 1024;
    if (zi > 15) {
        zi = 15;
        zp = 1024;
    }
    int zx = vx[zi] + (vx[zi + 1] - vx[zi]) * zp / 1024, zy = vy[zi] + (vy[zi + 1] - vy[zi]) * zp / 1024;
    int dy = y - 232;
    if (dy > 0)
        return;
    for (int x = x0; x < x1; x++) {
        int dx = x - 284, d = dx * dx + dy * dy;
        if (d > 33 * 33)
            continue;
        row[x - x0] = nt_blend565(row[x - x0], RGB(32, 46, 58), 200);
        if (d >= 26 * 26 && d <= 30 * 30)
            row[x - x0] = x < 276 ? RGB(154, 176, 192) : x < 301 ? RGB(127, 208, 224) : RGB(255, 211, 74);
        int dot = dx * nx + dy * ny;
        if (dot >= 0 && dot <= 24 * 1024 && abs(dx * ny - dy * nx) < 1100)
            row[x - x0] = 0xffff;
        int zdot = dx * zx + dy * zy;
        if (p->zone && zdot >= 21 * 1024 && zdot <= 33 * 1024 && abs(dx * zy - dy * zx) < 1600)
            row[x - x0] = RGB(255, 74, 58);
    }
}
static void hud(ag_t *g, const adv_post_v2_t *p)
{
    ui_v2_hud(g, "时刻表", p->res, p->score, 0, 1);
    for (int i = 0; i < 5; i++)
        ag_rect(g, 122 + i * 10, 6, 8, 8, 0, i < p->bags ? RGB(242, 227, 198) : RGB(110, 120, 130), 255, 0,
                0);
    char s[32];
    int tier = p->v >= 720 ? 3 : p->v >= 420 ? 2 : 1;
    snprintf(s, sizeof(s), "×%d", tier + (int)(p->combo / 4 < 3 ? p->combo / 4 : 3));
    ui_v2_text(g, s, 196, 10, 12, NT_ALIGN_CENTER, RGB(255, 211, 74));
    ag_rows_region(g, gauge_row, p, 199, 233, v2_state_key(p, sizeof(*p)));
    snprintf(s, sizeof(s), "%d", (int)p->v * 120 / K(VMAX));
    ui_v2_text(g, s, 284, 222, 12, NT_ALIGN_CENTER, 0xffff);
    ui_v2_text(g, tier == 3 ? "特快" : tier == 2 ? "快车" : "慢车", 246, 228, 12, NT_ALIGN_RIGHT, 0xffff);
}
static void effects(ag_t *g, const adv_post_v2_t *p)
{
    static const char *const SECTION[] = {"",
                                          "小镇 · 站台密集，连着扔",
                                          "山区 · 限速桥多，提前刹车",
                                          "牧场 · 牛羊常过铁路",
                                          "夜车 · 看信号灯",
                                          "下坡 · 车会自己变快"};
    for (int i = 0; i < 6; i++) {
        const adv_post_v2_fx_t *e = &p->fx[i];
        if (!e->kind)
            continue;
        const char *s = NULL;
        char str[40];
        if (e->kind == POST_V2_FX_NET || e->kind == POST_V2_FX_PERFECT || e->kind == POST_V2_FX_CRANE) {
            snprintf(str, sizeof(str), "%s+%d",
                     e->kind == POST_V2_FX_PERFECT ? "正中! "
                     : e->kind == POST_V2_FX_CRANE ? "抓到邮袋 "
                                                   : "",
                     (int)e->val);
            s = str;
        }
        if (e->kind == POST_V2_FX_WASTE)
            s = "扔早了/扔晚了";
        if (e->kind == POST_V2_FX_SKIP)
            s = "漏站";
        if (e->kind == POST_V2_FX_RED)
            s = "冲红灯！";
        if (e->kind == POST_V2_FX_DERAIL)
            s = "超速，急停！";
        if (e->kind == POST_V2_FX_ANIMAL)
            s = "撞到牛羊了";
        if (e->kind == POST_V2_FX_SECTION && e->val >= 1 && e->val <= 5) {
            ag_rect(g, 0, 75, 320, 30, 0, 0x18c5, 210, 0, 0);
            ui_v2_text(g, SECTION[e->val], 160, 90, 12, NT_ALIGN_CENTER, RGB(255, 211, 74));
        } else if (s)
            ui_v2_text(g, s, e->x, e->y - e->t / 3, 12, NT_ALIGN_CENTER, RGB(255, 211, 74));
    }
}
void ui_draw_post_v2_session(ag_t *g, const adv_model_t *m)
{
    static adv_post_v2_t title;
    static int old_phase = -1;
    static uint32_t old_seed, started;
    uint32_t ms = ui_millis();
    if (old_phase != m->phase || old_seed != m->seed) {
        old_phase = m->phase;
        old_seed = m->seed;
        started = ms;
    }
    ag_begin(g, m->phase == ADV_TITLE    ? UI_SCENE_TITLE
                : m->phase == ADV_RESULT ? UI_SCENE_RESULT
                                         : UI_SCENE_PLAY);
    const adv_post_v2_t *p = m->game;
    if (m->phase == ADV_TITLE) {
        adv_post_v2_start(&title, 3);
        title.dist = (int32_t)(ms % 100000) * 30;
        title.v = 600;
        p = &title;
    }
    backdrop(g, p);
    train(g, p, m->phase, ms);
    events(g, p);
    if (m->phase == ADV_TITLE) {
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
    if (m->phase == ADV_RESULT) {
        char line[80], detail[80];
        snprintf(line, sizeof(line), "送达 %d 袋 · 正中 %d · 抓袋 %d", (int)p->delivered, (int)p->perfects,
                 (int)p->cranes);
        snprintf(detail, sizeof(detail), "%d 米 · 冲红灯 %d · 超速 %d", (int)p->meters, (int)p->reds,
                 (int)p->derails);
        ui_v2_result(g, m, ms - started, "时刻表用完，今天的班次结束了", line, detail);
    }
}
