// CLIMB, 240x320 portrait with the native A-skin climbing art. Layout: CLIMB_DESIGN.md.
// The camera is locked to NABO's hand (adv_climb_hand_y), so the walls scroll smoothly.
#include <stdio.h>
#include "adv_climb.h"
#include "adv_ui_internal.h"

#define HAND_Y 230
#define TOP 32
#define BOTTOM 290
static const int HOLD_X[2] = {33, 207}, ROOT_X[2] = {56, 184}, CANTEEN_X[2] = {18, 222};
// Per-frame hand contact x of switch_grab (manifest contacts.per_frame); the root follows the hand.
static const int8_t SWITCH_HAND[2][6] = {{7, 5, 38, 50, 52, 51}, {51, 52, 50, 38, 5, 7}};
static const char *const SIDE[2] = {"left", "right"};
static const char *const ZONE[3] = {"grey", "cold", "snow"};

static int zone(int world_y) { int row = world_y < 0 ? 0 : world_y / ADV_CLIMB_ROW; return row < 100 ? 0 : row < 200 ? 1 : 2; }
static int floor_div(int a, int b) { return a >= 0 ? a / b : -((-a + b - 1) / b); }
static void text(ag_t *g, const char *s, int x, int y, int size, nt_align_t align, uint16_t color)
{
    ag_text_top(g, size == 18 ? &collection_font_18 : size == 16 ? &collection_font_16 : &collection_font_12, s, x, y, align, color);
}
static void actor(ag_t *g, const char *action, int side, unsigned frame, int x, int y)
{
    char id[48];
    if (side < 0) snprintf(id, sizeof(id), "climb_a/%s", action);
    else snprintf(id, sizeof(id), "climb_a/%s_%s", action, SIDE[side]);
    ui_art_frame_anchor(g, id, frame, x, y);
}
static void score_text(char *out, size_t size, uint32_t v)
{
    if (v > 9999) snprintf(out, size, "9999+");
    else snprintf(out, size, "%um", (unsigned)v);
}

static void hud(ag_t *g, const adv_climb_t *p)
{
    ui_art(g, "ui/bars/top", 0, 0, 0);
    ui_art(g, "ui/resources/icons/stamina", 0, 10, 8);
    ui_art(g, "ui/resources/bar-frame", 0, 36, 11);
    int w = p->res * 124 / ADV_RESOURCE_MAX;
    if (w > 0) ag_rect(g, 38, 13, w, 6, 0, p->res < ADV_RESOURCE_MAX / 4 ? UI_RED : ADV_ASSETS_UI_TEAL, 255, 0, 0);
    char n[16];
    score_text(n, sizeof(n), p->score);
    ui_number_tint(g, n, 20, 230, 6, NT_ALIGN_RIGHT, UI_WHITE);
}

static void walls(ag_t *g, int hand)
{
    static const uint16_t chasm_top[3] = {0x8CD4, 0xA5B8, 0xCEFC}, chasm_bottom[3] = {0x84B4, 0x9D98, 0xC6DB};
    int z = zone(hand);
    ag_band(g, TOP, BOTTOM - TOP, chasm_top[z], chasm_bottom[z]);
    // World tile t covers y [t*32, t*32+32) upward; its top edge is at screen HAND_Y-(t*32+32-hand).
    int first = floor_div(hand + HAND_Y - TOP, 32), last = floor_div(hand + HAND_Y - BOTTOM, 32);
    for (int t = first; t >= last; t--) {
        int y = HAND_Y - (t * 32 + 32 - hand), kind = zone(t * 32);
        for (int s = 0; s < 2; s++) {
            char id[40];
            snprintf(id, sizeof(id), "game/climb/tiles/%s-%d", ZONE[kind], (t * 7 + s) & 1);
            ui_art(g, id, 0, s ? 208 : 0, y);
            if (kind == 2 && ((t + s * 3) % 5 + 5) % 5 == 0) ui_art(g, "game/climb/shared/snow-mound", 0, s ? 208 : 0, y);
        }
    }
}

static void holds(ag_t *g, const adv_climb_t *p, int hand)
{
    static const char *const HOLD[4] = {"", "game/climb/props/hold-normal", "game/climb/props/hold-fragile", "game/climb/props/hold-ice"};
    int lo = (hand - (BOTTOM - HAND_Y) - 20) / ADV_CLIMB_ROW - 1, hi = (hand + HAND_Y - TOP + 20) / ADV_CLIMB_ROW + 1;
    for (int r = lo < 0 ? 0 : lo; r <= hi; r++)
        for (int s = 0; s < 2; s++) {
            int t = adv_climb_hold(p, r, s), y = HAND_Y - (r * ADV_CLIMB_ROW - hand);
            if (!t) continue;
            ui_art_frame_anchor(g, HOLD[t], 0, HOLD_X[s], y);
            if (adv_climb_canteen(p, r, s)) ui_art_frame_anchor(g, "game/climb/props/canteen", 0, CANTEEN_X[s], y + 4);
        }
}

static bool rock_warning(const adv_climb_t *p, int hand, int side)
{
    for (int i = 0; i < ADV_CLIMB_ROCKS; i++) {
        const adv_climb_rock_t *r = &p->rocks[i];
        if (r->on && r->side == side && r->y > hand - ADV_CLIMB_BODY_LO) return true;
    }
    return false;
}

static void rocks(ag_t *g, const adv_climb_t *p, int hand)
{
    for (int i = 0; i < ADV_CLIMB_ROCKS; i++) {
        const adv_climb_rock_t *r = &p->rocks[i];
        if (!r->on) continue;
        int y = HAND_Y - (r->y - hand), x = ROOT_X[r->side];
        if (y - ADV_CLIMB_ROCK_H < TOP + 4) {   // still above the screen: a red marker in its column
            ag_rect(g, x - 7, TOP + 4, 14, 14, 3, UI_RED, 255, UI_WHITE, 1);
            text(g, "!", x, TOP + 5, 12, NT_ALIGN_CENTER, UI_WHITE);
        } else ui_art_frame_anchor(g, "game/climb/props/falling-rock", 0, x, y);
    }
}

static void nabo(ag_t *g, const adv_climb_t *p)
{
    int side = p->act == CLIMB_IDLE ? p->side : p->from_side, done = p->act_len - p->act_t, x = ROOT_X[side];
    unsigned frame = p->tick / 5 % 6;
    const char *name = "grip_idle";
    if (p->act != CLIMB_IDLE) {
        frame = (unsigned)(done * 6 / p->act_len);
        if (frame > 5) frame = 5;
        name = p->act == CLIMB_SWITCH ? "switch_grab" : p->act == CLIMB_JUMP ? "jump" : "slide";
        if (p->act == CLIMB_SWITCH) {
            int hand_x = HOLD_X[p->from_side] + (HOLD_X[p->to_side] - HOLD_X[p->from_side]) * (int)frame / 5;
            x = hand_x - SWITCH_HAND[p->from_side][frame] + 30;
        }
    } else if (p->press >= ADV_CLIMB_TAP) {
        name = "charge";
        frame = (unsigned)((p->press - ADV_CLIMB_TAP) * 4 / (ADV_CLIMB_CHARGE3 - ADV_CLIMB_TAP));
        if (frame > 3) frame = 3;
    } else if (p->cheer > 0) {
        name = "summit_cheer";
        frame = (unsigned)((ADV_CLIMB_CHEER - p->cheer) / 6);
        if (frame > 7) frame = 7;
    }
    if (p->invuln > 0 && p->act != CLIMB_SLIDE && p->invuln / 4 % 2) return;   // brief blink after a hit
    actor(g, name, side, frame, x, HAND_Y + ADV_CLIMB_BODY_LO);
}

static const char *hint(const adv_climb_t *p, int hand, bool *warn)
{
    static const char *const messages[] = {"", "那边没有岩点 · 体力-100", "被落石砸中 · 体力-250", "碎石塌了！", "水壶 体力+250", ""};
    static char milestone[40];
    *warn = false;
    if (p->feedback && p->message) {
        *warn = p->message <= CLIMB_MSG_CRUMBLE;
        if (p->message != CLIMB_MSG_MILESTONE) return messages[p->message];
        snprintf(milestone, sizeof(milestone), "海拔 %u 米！", (unsigned)(p->score / 50 * 50));
        return milestone;
    }
    if (p->press >= ADV_CLIMB_CHARGE3) return "松开 同侧跳3米";
    if (p->press >= ADV_CLIMB_TAP) return "继续按住跳3米 · 松开跳2米";
    if (p->act == CLIMB_IDLE && rock_warning(p, hand, p->side)) { *warn = true; return "落石！快换边"; }
    int t = p->act == CLIMB_IDLE ? adv_climb_hold(p, p->row, p->side) : CLIMB_NONE;
    if (t == CLIMB_FRAGILE) { *warn = true; return "碎石要塌 快离开"; }
    if (t == CLIMB_ICE) return "结冰 体力消耗翻倍";
    return "点OK换边 · 按住蓄力跳";
}

static void play(ag_t *g, const adv_climb_t *p, bool footer)
{
    int hand = adv_climb_hand_y(p);
    walls(g, hand);
    holds(g, p, hand);
    nabo(g, p);
    rocks(g, p, hand);
    hud(g, p);
    if (!footer) return;
    bool warn;
    const char *h = hint(p, hand, &warn);
    ui_art(g, "ui/bars/bottom", 0, 0, BOTTOM);
    ag_text(g, &collection_font_12, h, 120, 310, NT_ALIGN_CENTER, warn ? ADV_ASSETS_UI_ACCENT : UI_PAPER);
}

static void title(ag_t *g, const adv_model_t *m)
{
    ui_paper(g);
    ui_header(g, "雪山", NULL);
    ui_art(g, "ui/wordmarks/climb", 0, 20, 42);
    static const char *const lines[] = {"点OK 换到对面岩点 上1米", "按住OK蓄力 松开同侧跳2/3米", "碎石1秒就塌 结冰更耗体力",
                                        "看准落石换边 水壶补体力", "体力耗尽结束"};
    for (int i = 0; i < 5; i++) text(g, lines[i], 120, 128 + i * 17, 12, NT_ALIGN_CENTER, UI_INK);
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        int x = 60 + tier * 60;
        bool on = earned & adv_stamp_bit(5, tier);
        ag_circle(g, x, 236, 9, ui_tier_color(tier), on ? 255 : 40, on ? UI_INK : ui_tier_color(tier), 2);
        char th[16];
        snprintf(th, sizeof(th), "%um", (unsigned)adv_threshold(5, tier));
        ag_text(g, &nabo_mono_font_12, th, x, 258, NT_ALIGN_CENTER, UI_INK);
    }
    char best[32];
    if (m->best[5] > 9999) snprintf(best, sizeof(best), "最佳 9999+");
    else snprintf(best, sizeof(best), "最佳 %um", (unsigned)m->best[5]);
    ag_text(g, &collection_font_16, best, 120, 283, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, "OK开始 · 长按上暂停 · 双击上返回");
}

static void result(ag_t *g, const adv_model_t *m, const adv_climb_t *p, uint32_t elapsed_ms)
{
    ag_rect(g, 0, 34, 240, 286, 0, UI_INK, 150, 0, 0);
    ui_popup(g, 24, 50, 192, 228);
    ag_text(g, &collection_font_16, "本次到达", 120, 78, NT_ALIGN_CENTER, UI_INK);
    char n[24];
    score_text(n, sizeof(n), p->score);
    ui_number(g, n, 36, 120, 90, NT_ALIGN_CENTER);
    if (m->record) ui_art(g, m->test ? "ui/labels/test-no-record" : "ui/labels/new-record", 0, m->test ? 72 : 84, 134);
    unsigned frame = elapsed_ms / 83;
    actor(g, "settlement_cheer", -1, frame > 7 ? 7 : frame, 120, 236);
    if (m->best[5] > 9999) snprintf(n, sizeof(n), "最佳 9999+");
    else snprintf(n, sizeof(n), "最佳 %um", (unsigned)m->best[5]);
    ag_text(g, &collection_font_16, n, 120, 258, NT_ALIGN_CENTER, UI_INK);
    ui_stamps(g, m, 5, 92, 274, 7, 28);
    ui_footer(g, "OK 再来一局 · 双击上 回地图");
}

void ui_draw_climb_session(ag_t *g, const adv_model_t *m)
{
    static int prior_phase = -1;
    static uint32_t prior_seed, phase_started;
    if ((int)m->phase != prior_phase || m->seed != prior_seed) { prior_phase = m->phase; prior_seed = m->seed; phase_started = ui_millis(); }
    ag_begin(g, m->phase == ADV_TITLE ? UI_SCENE_TITLE : m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    if (m->phase == ADV_TITLE) { title(g, m); return; }
    const adv_climb_t *p = m->game;
    play(g, p, m->phase == ADV_PLAY);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 120, 130, 46, UI_GOLD);
        ui_number(g, n, 36, 120, 112, NT_ALIGN_CENTER);
        ui_footer(g, "点OK换边 · 按住蓄力跳");
    } else if (m->phase == ADV_END) {
        ag_rect(g, 60, 136, 120, 40, 12, UI_INK, 230, UI_RED, 2);
        ag_text(g, &collection_font_18, "体力耗尽", 120, 163, NT_ALIGN_CENTER, UI_PAPER);
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
