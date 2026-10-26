// SKI V2「雪崩速降」screen, 320x240 clockwise landscape. Layout follows
// game-art/adventure/prototype/adv_ski_draw.js: ski_a frames and ski props, procedural kicker/ice/avalanche.
#include <stdio.h>
#include <stdlib.h>
#include "adv_ski.h"
#include "adv_ui_internal.h"

#define NY ADV_SKI_NABO_Y
#define W 320
#define H 240
static const uint16_t SNOW_TOP = 0xF7DF, SNOW_LOW = 0xDF5E, SPECK = 0xB5DB, TRACK = 0xC63C, ICE = 0xAF3E, RAMP = 0xBE9D;
static const uint16_t HUD_INK = 0x1928, GOLD = 0xFE89, WARN = 0xFB49, OKC = 0x8F15, MID = 0xFE09, FLOW = 0x7E5F, PALE = 0xCEFE;

static uint32_t hash(uint32_t n) { n = (n ^ 0x9e3779b9u) * 0x85ebca6bu; n ^= n >> 13; n *= 0xc2b2ae35u; return n ^ (n >> 16); }
static void text(ag_t *g, const char *s, int x, int y, int size, nt_align_t align, uint16_t color)
{ ag_text_top(g, size == 18 ? &collection_font_18 : size == 16 ? &collection_font_16 : &collection_font_12, s, x, y, align, color); }
static void actor(ag_t *g, const char *action, unsigned frame, int x, int y)
{ char id[40]; snprintf(id, sizeof(id), "ski_a/%s", action); ui_art_frame_anchor(g, id, frame, x, y); }

static void slope(ag_t *g, int wy)
{
    ag_band(g, 0, H, SNOW_TOP, SNOW_LOW);
    int top = wy - NY;
    for (int i = top / 22 - 1; i < (top + H) / 22 + 1; i++) {
        uint32_t h = hash((uint32_t)i * 7u);
        int y = i * 22 - top + (int)(h % 22u);
        ag_rect(g, (int)((h >> 8) % (uint32_t)W), y, (h >> 20) & 1 ? 3 : 2, 1, 0, SPECK, 255, 0, 0);
        ag_rect(g, (int)((h >> 14) % (uint32_t)W), y + 9, 2, 1, 0, TRACK, 255, 0, 0);
    }
}

static const char *const PROP[] = {NULL, "game/ski/props/gate-red", "game/ski/props/gate-blue", "game/ski/props/pine-large",
                                   "game/ski/shared/pine-small", "game/ski/shared/snow-mogul", NULL, NULL, "game/ski/shared/snow-drift"};
static void flat(ag_t *g, const adv_ski_t *p)
{
    int top = (p->y >> 8) - NY;
    for (int i = 0; i < ADV_SKI_OBJS; i++) {
        const adv_ski_obj_t *o = &p->objs[i];
        int y = o->y - top;
        if (!o->type || y < -70 || y > H + 10) continue;
        if (o->type == SKI_ICE) ag_rect(g, o->x - ADV_SKI_ICE_HALF, y, ADV_SKI_ICE_HALF * 2, ADV_SKI_ICE_LEN, 12, ICE, 190, 0xFFFF, 1);
        else if (o->type == SKI_KICKER) {
            ag_rect(g, o->x - 22, y - 14, 44, 16, 3, RAMP, 255, 0, 0);
            ag_rect(g, o->x - 20, y - 14, 40, 5, 2, 0xFFFF, 255, 0, 0);
            ag_rect(g, o->x - 3, y - 13, 6, 3, 1, 0xEAA7, 255, 0, 0);
        }
    }
}
// Standing props sorted by base line: `front` picks those below NABO's feet.
static void standing(ag_t *g, const adv_ski_t *p, bool front)
{
    int top = (p->y >> 8) - NY, order[ADV_SKI_OBJS], n = 0;
    for (int i = 0; i < ADV_SKI_OBJS; i++) {
        const adv_ski_obj_t *o = &p->objs[i];
        int y = o->y - top;
        if (!o->type || (o->type >= SKI_KICKER && o->type <= SKI_ICE) || y < -2 || y > H + 66 || (y > NY) != front) continue;
        int k = n++;
        while (k > 0 && p->objs[order[k - 1]].y > o->y) { order[k] = order[k - 1]; k--; }
        order[k] = i;
    }
    for (int k = 0; k < n; k++) { const adv_ski_obj_t *o = &p->objs[order[k]]; ui_art_frame_anchor(g, PROP[o->type], 0, o->x, o->y - top); }
}

static void nabo(ag_t *g, const adv_ski_t *p, bool out, uint32_t ms)
{
    int x = p->x >> 8, lift = 0;
    const char *name = "straight";
    unsigned f = ms / 100 % 6;
    if (p->vx < -170) { name = "lean_left"; f = ms / 133 % 4; } else if (p->vx > 170) { name = "lean_right"; f = ms / 133 % 4; }
    if (p->air > 0) {
        int t = p->air_max - p->air, T = p->air_max, peak = T > 30 ? 26 : T > 12 ? 10 : 4;
        lift = 4 * peak * t * (T - t) / (T * T); name = "jump"; f = (unsigned)(t * 6 / T > 5 ? 5 : t * 6 / T);
        if (p->spin_t > 0) { static const char *const SPIN[] = {"lean_left", "straight", "lean_right", "straight"}; name = SPIN[(ADV_SKI_SPIN - p->spin_t) / 6 % 4]; f = 1; }
    }
    if (p->crash > 0) { name = "fall"; f = (unsigned)((ADV_SKI_CRASH - p->crash) / 5 > 7 ? 7 : (ADV_SKI_CRASH - p->crash) / 5); lift = 0; }
    if (out) { name = "fall"; f = 7; }
    ag_rect(g, x - 15 + lift / 4, NY - 2, 30 - lift / 2, 5, 2, 0x4B10, 70, 0, 0);
    actor(g, name, f, x, NY - lift);
    if (p->spin_t > 0) {        // sparkle ring: 8 points of a 26 px circle, half of it lit and turning
        static const int8_t RX[8] = {26, 18, 0, -18, -26, -18, 0, 18}, RY[8] = {0, 18, 26, 18, 0, -18, -26, -18};
        for (int k = 0; k < 4; k++) { int j = (int)(ms / 60 + (uint32_t)k) % 8; ag_rect(g, x + RX[j] - 1, NY - lift - 30 + RY[j] - 1, 3, 3, 1, GOLD, 230, 0, 0); }
    }
}

static void avalanche(ag_t *g, const adv_ski_t *p, uint32_t ms)
{
    int gap = adv_ski_gap(p) > 0 ? adv_ski_gap(p) >> 8 : 0, front = NY - gap * (NY + 40) / ADV_SKI_AVAL_CAP;
    if (front < -30) return;
    if (front > 0) ag_rect(g, 0, 0, W, front, 0, 0xFFFF, 255, 0, 0);
    int top = p->y >> 8;
    for (int x = -8; x < W + 24; x += 26) {
        uint32_t h = hash((uint32_t)((x + 8) / 26) * 13u);
        int r = 14 + (int)(h % 10u), y = front + (int)((hash((uint32_t)(top + x) / 9u + (uint32_t)(ms / 120)) % 9u)) - 4;
        ag_circle(g, x, y, r, (h >> 9) & 1 ? 0xFFFF : 0xEF9F, 255, 0, 0);
    }
    for (int i = 0; i < 8; i++) { uint32_t h = hash((uint32_t)i * 31u + ms / 70); ag_rect(g, (int)(h % (uint32_t)W), front + 12 + (int)((h >> 10) % 26u), 2, 2, 0, 0xFFFF, 255, 0, 0); }
}

static void hud(ag_t *g, const adv_ski_t *p, uint32_t ms)
{
    int y = H - 26, pct = p->res / 10, m = adv_ski_mult(p);
    ag_rect(g, 0, y, W, 26, 0, HUD_INK, 210, 0, 0);
    text(g, "雪崩", 6, y + 1, 12, NT_ALIGN_LEFT, 0xFFFF);
    ag_rect(g, 34, y + 5, 86, 7, 0, 0x4A8E, 255, 0, 0);
    uint16_t c = pct < 30 ? ((ms / 170) % 2 ? WARN : 0xFD94) : pct < 60 ? MID : OKC;
    if (pct) ag_rect(g, 34, y + 5, 86 * pct / 100, 7, 0, c, 255, 0, 0);
    text(g, "速度", 6, y + 13, 12, NT_ALIGN_LEFT, 0xFFFF);
    ag_rect(g, 34, y + 17, 86, 5, 0, 0x4A8E, 255, 0, 0);
    if (p->flow) ag_rect(g, 34, y + 17, 86 * p->flow / ADV_SKI_FLOW_MAX, 5, 0, FLOW, 255, 0, 0);
    char s[40];
    if (p->combo >= 2) {
        if (m > 1) snprintf(s, sizeof(s), "%d连 ×%d", (int)p->combo, m); else snprintf(s, sizeof(s), "%d连", (int)p->combo);
        text(g, s, 132, y + 6, 12, NT_ALIGN_LEFT, m > 1 ? GOLD : 0xFFFF);
    }
    snprintf(s, sizeof(s), "%d m", (int)p->meters);
    text(g, s, 238, y + 6, 12, NT_ALIGN_RIGHT, PALE);
    snprintf(s, sizeof(s), "%u", (unsigned)p->score);
    text(g, s, 314, y + 3, 18, NT_ALIGN_RIGHT, 0xFFFF);
}

static void effects(ag_t *g, const adv_ski_t *p)
{
    static const char *const NAME[] = {"", "旗门密集", "进入树林", "跳台公园", "冰面", "起雾了"};
    static const char *const HINT[] = {"", "连过旗门越滑越快", "小心大树", "起跳后按中键转体", "转向变慢", "看不清远处"};
    char s[32];
    for (int i = 0; i < ADV_SKI_FX; i++) {
        const adv_ski_fx_t *e = &p->fx[i];
        if (!e->kind) continue;
        int rise = e->t / 3;
        switch (e->kind) {
        case SKI_FX_GATE: snprintf(s, sizeof(s), "+%d", (int)e->val); text(g, s, e->x, e->y - 8 - rise, 12, NT_ALIGN_CENTER, GOLD); break;
        case SKI_FX_MISS: text(g, "漏门", e->x, e->y - 8 - rise, 12, NT_ALIGN_CENTER, WARN); break;
        case SKI_FX_CRASH: text(g, "撞树了！", e->x, e->y - 70, 16, NT_ALIGN_CENTER, WARN); break;
        case SKI_FX_STUMBLE: text(g, "绊了一下", e->x, e->y - 68, 12, NT_ALIGN_CENTER, 0xFD8F); break;
        case SKI_FX_WIPE: text(g, "没转完就落地", e->x, e->y - 86, 12, NT_ALIGN_CENTER, WARN); break;
        case SKI_FX_LAND: snprintf(s, sizeof(s), "转体 +%d", (int)e->val); text(g, s, e->x, e->y - 78 - rise, 16, NT_ALIGN_CENTER, GOLD); break;
        case SKI_FX_KICK: text(g, "起跳！按中键转体", e->x, e->y - 92, 12, NT_ALIGN_CENTER, HUD_INK); break;
        case SKI_FX_NEAR: text(g, "好险", e->x, e->y - 70 - rise, 12, NT_ALIGN_CENTER, 0x4C7F); break;
        case SKI_FX_SECTION:
            if (e->val < 1 || e->val > 5) break;
            ag_rect(g, 0, 156, W, 40, 0, HUD_INK, 180, 0, 0);
            text(g, NAME[e->val], 160 + (e->t < 10 ? (10 - e->t) * 20 : 0), 158, 16, NT_ALIGN_CENTER, GOLD);
            text(g, HINT[e->val], 160, 178, 12, NT_ALIGN_CENTER, 0xFFFF); break;
        default: break;
        }
    }
}

static void world(ag_t *g, const adv_ski_t *p, bool out, uint32_t ms)
{
    slope(g, p->y >> 8); flat(g, p); standing(g, p, false); nabo(g, p, out, ms); standing(g, p, true);
    if (p->section == SKI_SEC_FOG) { ag_rect(g, 0, NY + 30, W, 30, 0, 0xF7BF, 160, 0, 0); ag_rect(g, 0, NY + 60, W, H - NY - 60, 0, 0xF7BF, 245, 0, 0); }
    avalanche(g, p, ms);
}

static int sway(uint32_t ms) { int t = (int)(ms / 10 % 400); return (t < 200 ? t - 100 : 300 - t) * 3 / 5; }
static void title(ag_t *g, const adv_model_t *m, uint32_t ms)
{
    slope(g, (int)(ms * 36 / 100));
    int x = 160 + sway(ms), d = sway(ms + 300) - sway(ms);
    actor(g, d < -8 ? "lean_left" : d > 8 ? "lean_right" : "straight", ms / 120 % 4, x, NY);
    ag_rect(g, 0, 110, W, 130, 0, HUD_INK, 150, 0, 0);
    char best[32];
    snprintf(best, sizeof(best), "最佳 %u", (unsigned)m->best[6]);
    text(g, best, 312, 6, 12, NT_ALIGN_RIGHT, 0x2945);
    text(g, "雪崩速降", 160, 118, 18, NT_ALIGN_CENTER, 0xFFFF);
    text(g, "左键 左转 · 中键 跳/空中转体 · 右键 右转", 160, 146, 12, NT_ALIGN_CENTER, PALE);
    text(g, "过旗门、做转体越滑越快，别让雪崩追上", 160, 166, 12, NT_ALIGN_CENTER, PALE);
    if ((ms / 500) % 3) text(g, "中键开始", 160, 190, 16, NT_ALIGN_CENTER, 0xFFFF);
    text(g, "长按中键暂停 · 双击上键回地图", 160, 222, 12, NT_ALIGN_CENTER, 0x9CF3);
}

static void result(ag_t *g, const adv_model_t *m, const adv_ski_t *p, uint32_t since)
{
    world(g, p, true, since);
    ag_rect(g, 0, 0, W, H, 0, HUD_INK, 205, 0, 0);
    text(g, "被雪崩追上了", 160, 16, 12, NT_ALIGN_CENTER, PALE);
    char s[64];
    snprintf(s, sizeof(s), "%u", (unsigned)p->score);
    ui_number_tint(g, s, 36, 160, 38, NT_ALIGN_CENTER, 0xFFFF);
    if (m->record) text(g, m->test ? "测试不保存" : "新纪录！", 254, 44, 12, NT_ALIGN_CENTER, GOLD);
    snprintf(s, sizeof(s), "%d 米 · 旗门 %d/%d · 转体 %d · 最长 %d 连", (int)p->meters, (int)p->passed, (int)(p->passed + p->misses), (int)p->tricks, (int)p->best);
    text(g, s, 160, 90, 12, NT_ALIGN_CENTER, PALE);
    unsigned frame = since / 83 > 7 ? 7 : since / 83;
    actor(g, "settlement_cheer", frame, 160, 196);
    snprintf(s, sizeof(s), "最佳 %u", (unsigned)m->best[6]);
    text(g, s, 160, 200, 12, NT_ALIGN_CENTER, 0xFFFF);
    text(g, "中键重玩 · 双击上键回地图", 160, 222, 12, NT_ALIGN_CENTER, 0x9CF3);
}

void ui_draw_ski_session(ag_t *g, const adv_model_t *m)
{
    static int prior_phase = -1;
    static uint32_t prior_seed, phase_started;
    uint32_t ms = ui_millis();
    if ((int)m->phase != prior_phase || m->seed != prior_seed) { prior_phase = m->phase; prior_seed = m->seed; phase_started = ms; }
    ag_begin(g, m->phase == ADV_TITLE ? UI_SCENE_TITLE : m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    if (m->phase == ADV_TITLE) { title(g, m, ms); return; }
    const adv_ski_t *p = m->game;
    if (m->phase == ADV_RESULT) { result(g, m, p, ms - phase_started); return; }
    world(g, p, m->phase == ADV_END, ms);
    if (m->phase == ADV_PAUSE) {
        ag_rect(g, 56, 50, 208, 124, 8, HUD_INK, 235, GOLD, 1);
        text(g, "暂停", 160, 60, 18, NT_ALIGN_CENTER, 0xFFFF);
        text(g, "中键继续", 160, 92, 16, NT_ALIGN_CENTER, GOLD);
        text(g, "左键重新开始", 160, 120, 12, NT_ALIGN_CENTER, 0xFFFF);
        text(g, "双击上键回地图", 160, 142, 12, NT_ALIGN_CENTER, 0xFFFF);
        return;
    }
    effects(g, p); hud(g, p, ms);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 160, 140, 34, GOLD); ui_number(g, n, 36, 160, 122, NT_ALIGN_CENTER);
        text(g, "雪崩从后面追来了", 160, 168, 12, NT_ALIGN_CENTER, HUD_INK);
    } else if (m->phase == ADV_END) { ag_rect(g, 82, 120, 156, 44, 8, HUD_INK, 235, WARN, 1); text(g, "被追上了", 160, 130, 18, NT_ALIGN_CENTER, 0xFFFF); }
}
