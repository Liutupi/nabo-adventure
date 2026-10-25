// SKY, 240x320 portrait. The basket point B stays at (80,250); altitude and distance move the sky.
// Layer offsets follow game-art/adventure/tools/sky_export.py scene().
#include <stdio.h>
#include "adv_sky.h"
#include "adv_ui_internal.h"

#define BX 80
#define BY 236
#define TOP 32
#define BOTTOM 290

static void text(ag_t *g, const char *s, int x, int y, int size, nt_align_t align, uint16_t color)
{
    ag_text_top(g, size == 18 ? &collection_font_18 : size == 16 ? &collection_font_16 : &collection_font_12, s, x, y, align, color);
}
static void score_text(char *out, size_t size, uint32_t v)
{
    if (v > 9999) snprintf(out, size, "9999+");
    else snprintf(out, size, "%um", (unsigned)v);
}
// Thin near-vertical rope as 1px rectangles (the renderer has no line primitive).
static void rope(ag_t *g, int x0, int y0, int x1, int y1, uint16_t color)
{
    int steps = (y1 - y0 + 9) / 10;
    for (int i = 0; i < steps; i++) {
        int ya = y0 + (y1 - y0) * i / steps, yb = y0 + (y1 - y0) * (i + 1) / steps;
        ag_rect(g, x0 + (x1 - x0) * (2 * i + 1) / (2 * steps), ya, 1, yb - ya, 0, color, 255, 0, 0);
    }
}

static void hud(ag_t *g, const adv_sky_t *p)
{
    ui_art(g, "ui/bars/top", 0, 0, 0);
    ui_art(g, "ui/resources/icons/hot-air", 0, 10, 8);
    ui_art(g, "ui/resources/bar-frame", 0, 36, 11);
    int w = p->res * 124 / ADV_RESOURCE_MAX;
    if (w > 0) ag_rect(g, 38, 13, w, 6, 0, p->res < ADV_RESOURCE_MAX / 4 ? UI_RED : ADV_ASSETS_UI_TEAL, 255, 0, 0);
    char n[16];
    score_text(n, sizeof(n), p->score);
    ui_number_tint(g, n, 20, 230, 6, NT_ALIGN_RIGHT, UI_WHITE);
}

static void backdrop(ag_t *g, const adv_sky_t *p)
{
    int alt = p->alt >> 4, dist = p->dist >> 4;
    ag_band(g, TOP, BOTTOM - TOP, ag_rgb(122, 186, 246), ag_rgb(156, 210, 252));
    // Far clouds drift at half speed; one per 80 px of travel, height hashed from the index.
    for (int k = (dist / 2 - 60) / 80; k * 80 <= dist / 2 + 300; k++) {
        if (k < 0) continue;
        int x = k * 80 - dist / 2, h = 60 + (int)((unsigned)(k * 97 + 13) % 900u), y = BY - (h - alt) / 2;
        if (y < TOP - 30 || y > BOTTOM + 30) continue;
        char id[32];
        snprintf(id, sizeof(id), "game/sky/cloud_%02d", k % 4);
        ui_art_frame_anchor(g, id, 0, x, y);
    }
    int ground = BY + 22 + alt;   // treetops: the basket bottom touches them at altitude 0
    if (ground < BOTTOM) {
        ag_rect(g, 0, ground + 6, 240, BOTTOM - ground - 6 > 0 ? BOTTOM - ground - 6 : 0, 0, ag_rgb(70, 128, 82), 255, 0, 0);
        for (int x = -(dist % 24); x < 252; x += 24) ag_circle(g, x + 12, ground + 10, 13, ag_rgb(52, 108, 70), 255, 0, 0);
    }
}

static void balloon(ag_t *g, const adv_sky_t *p)
{
    bool hit = p->invuln > ADV_SKY_INVULN - 24 && (p->message == SKY_MSG_BIRD || p->message == SKY_MSG_STORM || p->message == SKY_MSG_GROUND);
    const char *action = "idle", *controls = NULL;
    unsigned frame = p->tick / 5 % 6;
    if (hit) { action = "hit"; frame = (unsigned)(ADV_SKY_INVULN - p->invuln) / 4; }
    else if (p->message == SKY_MSG_STAMP && p->feedback > 40) { action = "receive_stamp"; frame = (unsigned)(60 - p->feedback) / 5; }
    else if (p->heating) { action = "heat"; controls = "sky_props/heat_controls"; }
    else if (p->vy < -20) { action = "vent"; controls = "sky_props/vent_controls"; }
    if (frame > 5) frame = 5;
    ui_art_frame_anchor(g, "game/sky/envelope", 0, BX, BY - 94);
    rope(g, BX - 11, BY - 97, BX - 30, BY - 6, ag_rgb(101, 79, 63));
    rope(g, BX + 11, BY - 97, BX + 30, BY - 6, ag_rgb(101, 79, 63));
    rope(g, BX - 7, BY - 97, BX - 16, BY - 40, ag_rgb(116, 91, 68));
    rope(g, BX + 8, BY - 97, BX + 19, BY - 40, ag_rgb(64, 91, 103));
    if (p->heating) ag_glow(g, BX, BY - 68, 10 + (int)(p->tick / 3 % 3), ag_rgb(255, 170, 70));
    ui_art_frame_anchor(g, "game/sky/burner", 0, BX, BY - 58);
    ui_art_frame_anchor(g, "game/sky/basket_back", 0, BX, BY - 6);
    if (controls) ui_art_frame_anchor(g, controls, frame, BX, BY);
    else ui_art_frame_anchor(g, "game/sky/controls_idle", 0, BX, BY);
    if (!(p->invuln && p->invuln / 4 % 2) || !hit) {
        char id[40];
        snprintf(id, sizeof(id), "sky_a/%s", action);
        ui_art_frame_anchor(g, id, frame, BX, BY);
    }
    ui_art_frame_anchor(g, "game/sky/basket_front", 0, BX, BY - 6);
}

static void objects(ag_t *g, const adv_sky_t *p)
{
    int dist = p->dist >> 4, alt = p->alt >> 4;
    for (int i = 0; i < ADV_SKY_CAP; i++) {
        const adv_sky_obj_t *o = &p->objs[i];
        if (!o->type || (o->done && o->type != SKY_WARM)) continue;
        int x = BX + o->x - dist, y = BY - (adv_sky_object_alt(o) - alt);
        if (x < -60 || x > 300 || y < TOP - 40 || y > BOTTOM + 40) continue;
        if (o->type == SKY_STORM) ui_art_frame_anchor(g, "game/sky/thundercloud", 0, x, y + 13);
        else if (o->type == SKY_BIRD) ui_art_frame_anchor(g, "sky_props/bird", (unsigned)(o->phase / 6 % 4), x, y);
        else if (o->type == SKY_STAMP) ui_art_frame_anchor(g, "game/sky/stamp", 0, x, y);
        else {
            uint8_t a = o->done ? 60 : 130;
            ag_rect(g, x - ADV_SKY_WARM_W, y - ADV_SKY_WARM_H, ADV_SKY_WARM_W * 2, ADV_SKY_WARM_H * 2, 10, ag_rgb(255, 214, 120), a, 0, 0);
            if (!o->done) for (int k = -1; k <= 1; k++) ag_glow(g, x + k * 22, y, 9, UI_GOLD);
        }
    }
}

static const char *hint(const adv_sky_t *p, bool *warn)
{
    static const char *const messages[] = {"", "撞到鸟群 · 热气-250", "撞进雷云 · 热气-250", "邮票 +10米", "暖风 热气+200", "擦到树梢 · 热气-250"};
    *warn = p->feedback && (p->message == SKY_MSG_BIRD || p->message == SKY_MSG_STORM || p->message == SKY_MSG_GROUND);
    if (p->feedback && p->message) return messages[p->message];
    if ((p->alt >> 4) < 60) { *warn = true; return "太低了！按住OK加热"; }
    return "按住OK加热 · 松开下降";
}

static void play(ag_t *g, const adv_sky_t *p, bool footer)
{
    backdrop(g, p);
    balloon(g, p);
    objects(g, p);
    hud(g, p);
    if (!footer) return;
    bool warn;
    const char *h = hint(p, &warn);
    ui_art(g, "ui/bars/bottom", 0, 0, BOTTOM);
    ag_text(g, &collection_font_12, h, 120, 310, NT_ALIGN_CENTER, warn ? ADV_ASSETS_UI_ACCENT : UI_PAPER);
}

static void title(ag_t *g, const adv_model_t *m)
{
    ui_paper(g);
    ui_header(g, "云端", NULL);
    ui_art(g, "ui/wordmarks/sky", 0, 20, 42);
    static const char *const lines[] = {"按住OK加热上升 · 松开下降", "躲开鸟群和雷云 · 撞到扣250", "穿过暖风补热气 · 邮票+10米",
                                        "别碰树梢 · 热气耗尽结束"};
    for (int i = 0; i < 4; i++) text(g, lines[i], 120, 130 + i * 18, 12, NT_ALIGN_CENTER, UI_INK);
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        int x = 60 + tier * 60;
        bool on = earned & adv_stamp_bit(7, tier);
        ag_circle(g, x, 236, 9, ui_tier_color(tier), on ? 255 : 40, on ? UI_INK : ui_tier_color(tier), 2);
        char th[16];
        snprintf(th, sizeof(th), "%um", (unsigned)adv_threshold(7, tier));
        ag_text(g, &nabo_mono_font_12, th, x, 258, NT_ALIGN_CENTER, UI_INK);
    }
    char best[32];
    if (m->best[7] > 9999) snprintf(best, sizeof(best), "最佳 9999+");
    else snprintf(best, sizeof(best), "最佳 %um", (unsigned)m->best[7]);
    ag_text(g, &collection_font_16, best, 120, 283, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, "OK开始 · 长按上暂停 · 双击上返回");
}

static void result(ag_t *g, const adv_model_t *m, const adv_sky_t *p, uint32_t elapsed_ms)
{
    ag_rect(g, 0, 34, 240, 286, 0, UI_INK, 150, 0, 0);
    ui_popup(g, 24, 50, 192, 228);
    ag_text(g, &collection_font_16, "本局成绩", 120, 78, NT_ALIGN_CENTER, UI_INK);
    char n[24];
    score_text(n, sizeof(n), p->score);
    ui_number(g, n, 36, 120, 90, NT_ALIGN_CENTER);
    if (m->record) ui_art(g, m->test ? "ui/labels/test-no-record" : "ui/labels/new-record", 0, m->test ? 72 : 84, 134);
    unsigned frame = elapsed_ms / 83;
    ui_art_frame_anchor(g, "sky_a/settlement_cheer", frame > 7 ? 7 : frame, 120, 238);
    if (m->best[7] > 9999) snprintf(n, sizeof(n), "最佳 9999+");
    else snprintf(n, sizeof(n), "最佳 %um", (unsigned)m->best[7]);
    ag_text(g, &collection_font_16, n, 120, 258, NT_ALIGN_CENTER, UI_INK);
    ui_stamps(g, m, 7, 92, 274, 7, 28);
    ui_footer(g, "OK 再来一局 · 双击上 回地图");
}

void ui_draw_sky_session(ag_t *g, const adv_model_t *m)
{
    static int prior_phase = -1;
    static uint32_t prior_seed, phase_started;
    if ((int)m->phase != prior_phase || m->seed != prior_seed) { prior_phase = m->phase; prior_seed = m->seed; phase_started = ui_millis(); }
    ag_begin(g, m->phase == ADV_TITLE ? UI_SCENE_TITLE : m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    if (m->phase == ADV_TITLE) { title(g, m); return; }
    const adv_sky_t *p = m->game;
    play(g, p, m->phase == ADV_PLAY);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 170, 130, 46, UI_GOLD);
        ui_number(g, n, 36, 170, 112, NT_ALIGN_CENTER);
        ui_footer(g, "按住OK加热 · 松开下降");
    } else if (m->phase == ADV_END) {
        ag_rect(g, 60, 136, 120, 40, 12, UI_INK, 230, UI_RED, 2);
        ag_text(g, &collection_font_18, "热气耗尽", 120, 163, NT_ALIGN_CENTER, UI_PAPER);
        ui_footer(g, "双击上 回地图");
    } else if (m->phase == ADV_PAUSE) {
        ag_rect(g, 0, 34, 240, 256, 0, UI_INK, 150, 0, 0);
        ui_popup(g, 24, 80, 192, 160);
        ag_text(g, &collection_font_18, "暂停", 120, 112, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "OK 继续", 120, 148, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "下 重新开始", 120, 178, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "双击上 回地图", 120, 208, NT_ALIGN_CENTER, UI_INK);
        ui_footer(g, "长按上已暂停");
    } else if (m->phase == ADV_RESULT) result(g, m, p, ui_millis() - phase_started);
}
