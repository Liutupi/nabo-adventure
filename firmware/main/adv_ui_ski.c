// SKI, 240x320 portrait, rear view: NABO skis up the screen; gates and hazards come down.
#include <stdio.h>
#include "adv_ski.h"
#include "adv_ui_internal.h"

#define FEET_Y 262
#define TOP 32
#define BOTTOM 290

static void text(ag_t *g, const char *s, int x, int y, int size, nt_align_t align, uint16_t color)
{
    ag_text_top(g, size == 18 ? &collection_font_18 : size == 16 ? &collection_font_16 : &collection_font_12, s, x, y, align, color);
}
static void actor(ag_t *g, const char *action, unsigned frame, int x, int y)
{
    char id[40];
    snprintf(id, sizeof(id), "ski_a/%s", action);
    ui_art_frame_anchor(g, id, frame, x, y);
}
static int screen_y(const adv_ski_t *p, int world_y) { return FEET_Y - (world_y - p->pos); }

static void hud(ag_t *g, const adv_ski_t *p)
{
    ui_art(g, "ui/bars/top", 0, 0, 0);
    ui_art(g, "ui/resources/icons/temperature", 0, 10, 8);
    ui_art(g, "ui/resources/bar-frame", 0, 36, 11);
    int w = p->res * 124 / ADV_RESOURCE_MAX;
    if (w > 0) ag_rect(g, 38, 13, w, 6, 0, p->res < ADV_RESOURCE_MAX / 4 ? UI_RED : ADV_ASSETS_UI_TEAL, 255, 0, 0);
    char n[16];
    if (p->score > 9999) snprintf(n, sizeof(n), "9999+");
    else snprintf(n, sizeof(n), "%u", (unsigned)p->score);
    ui_number_tint(g, n, 20, 230, 6, NT_ALIGN_RIGHT, UI_WHITE);
}

static void snow(ag_t *g, const adv_ski_t *p)
{
    ag_band(g, TOP, BOTTOM - TOP, ag_rgb(222, 232, 250), ag_rgb(238, 244, 255));
    // Fixed world marks give the speed cue: one drift every 90 px of slope, x hashed from its row.
    for (int row = (p->pos - 40) / 90; row * 90 <= p->pos + FEET_Y - TOP + 40; row++) {
        if (row < 0) continue;
        int x = 20 + (int)((unsigned)(row * 73 + 41) % 200u), y = screen_y(p, row * 90);
        ui_art_frame_anchor(g, "game/ski/shared/snow-ground", 0, x, y);   // sparkle only: drifts read as obstacles
    }
}

static void object(ag_t *g, const adv_ski_t *p, const adv_ski_obj_t *o)
{
    static const char *const ART[] = {"", "game/ski/props/gate-red", "game/ski/props/gate-blue", "game/ski/props/pine-large",
                                      "game/ski/shared/pine-small", "game/ski/shared/snow-mogul", "game/ski/props/hot-cocoa-cabin"};
    int y = screen_y(p, o->y);
    if (y < TOP - 8 || y > BOTTOM + 90) return;
    ui_art_frame_anchor(g, ART[o->type], 0, o->x, y);
    if (o->type <= SKI_GATE_BLUE && o->done) ag_rect(g, o->x - 3, y - 47, 6, 6, 3, UI_GOLD, 255, 0, 0);
}

static void nabo(ag_t *g, const adv_ski_t *p)
{
    int x = p->x / 16, lift = 0;
    const char *name = "straight";
    unsigned frame = p->tick / 5 % 6;
    if (p->fall) {
        int total = p->message == SKI_MSG_TREE ? ADV_SKI_FALL : ADV_SKI_BUMP_T;
        name = "fall"; frame = (unsigned)((total - p->fall) * 8 / total);
        if (frame > 7) frame = 7;
    } else if (p->air) {
        int t = ADV_SKI_AIR - p->air;
        name = "jump"; frame = (unsigned)(t * 6 / ADV_SKI_AIR);
        lift = 64 * t * p->air / (ADV_SKI_AIR * ADV_SKI_AIR);
    } else if (p->vx < -12 || p->vx > 12) {
        int lean = (p->vx < 0 ? -p->vx : p->vx) - 12;
        name = p->vx < 0 ? "lean_left" : "lean_right"; frame = (unsigned)(lean / 8 > 3 ? 3 : lean / 8);
    }
    if (p->invuln && p->invuln / 4 % 2) return;
    if (lift) ag_rect(g, x - 14, FEET_Y - 2, 28, 4, 2, ag_rgb(196, 208, 230), 200, 0, 0);
    actor(g, name, frame, x, FEET_Y - lift);
}

static const char *hint(const adv_ski_t *p, bool *warn)
{
    static const char *const messages[] = {"", "过门 +1", "漏过旗门 · 体温-100", "撞树 · 体温-250", "绊倒 · 体温-100", "热可可 体温+300"};
    *warn = p->feedback && (p->message == SKI_MSG_MISS || p->message == SKI_MSG_TREE || p->message == SKI_MSG_BUMP);
    if (p->feedback && p->message) return messages[p->message];
    return "按住上下转弯 · 点OK跳";
}

static void play(ag_t *g, const adv_ski_t *p, bool footer)
{
    snow(g, p);
    for (int pass = 0; pass < 2; pass++)   // far objects first, then NABO, then what he already passed
        for (int depth = ADV_SKI_AHEAD + 60; depth >= -ADV_SKI_BEHIND; depth -= 20) {
            for (int i = 0; i < ADV_SKI_CAP; i++) {
                const adv_ski_obj_t *o = &p->objs[i];
                int d = o->y - p->pos;
                if (!o->type || d > depth || d <= depth - 20 || (pass == 0) != (d >= 0)) continue;
                object(g, p, o);
            }
            if (pass == 0 && depth == 0) nabo(g, p);
        }
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
    ui_header(g, "雪坡", NULL);
    ui_art(g, "ui/wordmarks/ski", 0, 20, 42);
    static const char *const lines[] = {"按住上往左 · 按住下往右", "点OK跳过雪包和小树", "穿过旗门+1 · 漏门扣体温",
                                        "撞树扣250 · 热可可补体温", "体温耗尽结束"};
    for (int i = 0; i < 5; i++) text(g, lines[i], 120, 128 + i * 17, 12, NT_ALIGN_CENTER, UI_INK);
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        int x = 60 + tier * 60;
        bool on = earned & adv_stamp_bit(6, tier);
        ag_circle(g, x, 236, 9, ui_tier_color(tier), on ? 255 : 40, on ? UI_INK : ui_tier_color(tier), 2);
        char th[16];
        snprintf(th, sizeof(th), "%u", (unsigned)adv_threshold(6, tier));
        ag_text(g, &nabo_mono_font_12, th, x, 258, NT_ALIGN_CENTER, UI_INK);
    }
    char best[32];
    if (m->best[6] > 9999) snprintf(best, sizeof(best), "最佳 9999+");
    else snprintf(best, sizeof(best), "最佳 %u", (unsigned)m->best[6]);
    ag_text(g, &collection_font_16, best, 120, 283, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, "OK开始 · 长按OK暂停 · 双击上返回");
}

static void result(ag_t *g, const adv_model_t *m, const adv_ski_t *p, uint32_t elapsed_ms)
{
    ag_rect(g, 0, 34, 240, 286, 0, UI_INK, 150, 0, 0);
    ui_popup(g, 24, 50, 192, 228);
    ag_text(g, &collection_font_16, "本局成绩", 120, 78, NT_ALIGN_CENTER, UI_INK);
    char n[24];
    if (p->score > 9999) snprintf(n, sizeof(n), "9999+");
    else snprintf(n, sizeof(n), "%u", (unsigned)p->score);
    ui_number(g, n, 36, 120, 90, NT_ALIGN_CENTER);
    if (m->record) ui_art(g, m->test ? "ui/labels/test-no-record" : "ui/labels/new-record", 0, m->test ? 72 : 84, 134);
    unsigned frame = elapsed_ms / 83;
    actor(g, "settlement_cheer", frame > 7 ? 7 : frame, 120, 238);
    if (m->best[6] > 9999) snprintf(n, sizeof(n), "最佳 9999+");
    else snprintf(n, sizeof(n), "最佳 %u", (unsigned)m->best[6]);
    ag_text(g, &collection_font_16, n, 120, 258, NT_ALIGN_CENTER, UI_INK);
    ui_stamps(g, m, 6, 92, 274, 7, 28);
    ui_footer(g, "OK 再来一局 · 双击上 回地图");
}

void ui_draw_ski_session(ag_t *g, const adv_model_t *m)
{
    static int prior_phase = -1;
    static uint32_t prior_seed, phase_started;
    if ((int)m->phase != prior_phase || m->seed != prior_seed) { prior_phase = m->phase; prior_seed = m->seed; phase_started = ui_millis(); }
    ag_begin(g, m->phase == ADV_TITLE ? UI_SCENE_TITLE : m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    if (m->phase == ADV_TITLE) { title(g, m); return; }
    const adv_ski_t *p = m->game;
    play(g, p, m->phase == ADV_PLAY);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 120, 130, 46, UI_GOLD);
        ui_number(g, n, 36, 120, 112, NT_ALIGN_CENTER);
        ui_footer(g, "按住上下转弯 · 点OK跳");
    } else if (m->phase == ADV_END) {
        ag_rect(g, 60, 136, 120, 40, 12, UI_INK, 230, UI_RED, 2);
        ag_text(g, &collection_font_18, "体温耗尽", 120, 163, NT_ALIGN_CENTER, UI_PAPER);
        ui_footer(g, "双击上 回地图");
    } else if (m->phase == ADV_PAUSE) {
        ag_rect(g, 0, 34, 240, 256, 0, UI_INK, 150, 0, 0);
        ui_popup(g, 24, 80, 192, 160);
        ag_text(g, &collection_font_18, "暂停", 120, 112, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "OK 继续", 120, 148, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "下 重新开始", 120, 178, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "双击上 回地图", 120, 208, NT_ALIGN_CENTER, UI_INK);
        ui_footer(g, "长按OK已暂停");
    } else if (m->phase == ADV_RESULT) result(g, m, p, ui_millis() - phase_started);
}
