// SPACE, 240x320 portrait, fixed camera: lander (back, crew, front layers), pad, fuel cans, rocks.
#include <stdio.h>
#include "adv_space.h"
#include "adv_ui_internal.h"

#define TOP 32
#define BOTTOM 290
#define G ADV_SPACE_GROUND

static void text(ag_t *g, const char *s, int x, int y, int size, nt_align_t align, uint16_t color)
{
    ag_text_top(g, size == 18 ? &collection_font_18 : size == 16 ? &collection_font_16 : &collection_font_12, s, x, y, align, color);
}
static void crew(ag_t *g, const char *action, unsigned frame, int x, int y)
{
    char id[40];
    snprintf(id, sizeof(id), "space_a/%s", action);
    ui_art_frame_anchor(g, id, frame, x, y);
}

static void hud(ag_t *g, const adv_space_t *p)
{
    ui_art(g, "ui/bars/top", 0, 0, 0);
    ui_art(g, "ui/resources/icons/fuel", 0, 10, 8);
    ui_art(g, "ui/resources/bar-frame", 0, 36, 11);
    int w = p->res * 124 / ADV_RESOURCE_MAX;
    if (w > 0) ag_rect(g, 38, 13, w, 6, 0, p->res < ADV_RESOURCE_MAX / 4 ? UI_RED : ADV_ASSETS_UI_TEAL, 255, 0, 0);
    char n[16];
    if (p->score > 9999) snprintf(n, sizeof(n), "9999+");
    else snprintf(n, sizeof(n), "%u", (unsigned)p->score);
    ui_number_tint(g, n, 20, 230, 6, NT_ALIGN_RIGHT, UI_WHITE);
}

static void scene(ag_t *g, const adv_space_t *p)
{
    ag_band(g, TOP, BOTTOM - TOP, ag_rgb(10, 16, 36), ag_rgb(26, 34, 64));
    static const uint8_t stars[][2] = {{18, 52}, {64, 84}, {110, 46}, {150, 98}, {204, 60}, {226, 132}, {38, 150}, {176, 176}, {90, 196}, {12, 226}, {130, 140}, {200, 220}};
    for (unsigned i = 0; i < sizeof(stars) / sizeof(*stars); i++)
        ag_rect(g, stars[i][0], stars[i][1], 1 + (i % 3 == 0), 1 + (i % 3 == 0), 0, ag_rgb(200, 210, 240), 255, 0, 0);
    for (int x = 0; x < 240; x += 32) {
        char id[32];
        snprintf(id, sizeof(id), "game/space/tiles/lunar-%d", (x / 32) % 3);
        ui_art(g, id, 0, x, G);
    }
    ui_art_frame_anchor(g, "game/space/props/landing-pad", 0, p->pad, G + 19);   // platform row 5 at the surface
    int z = adv_space_zone(p);
    for (int s = -1; s <= 1; s += 2) {
        ag_glow(g, p->pad + s * z, G - 2, 6, UI_GOLD);
        ag_rect(g, p->pad + s * z - 1, G - 4, 3, 4, 1, ag_rgb(255, 236, 160), 255, 0, 0);
    }
}

static void objects(ag_t *g, const adv_space_t *p)
{
    for (int i = 0; i < ADV_SPACE_OBJS; i++) {
        const adv_space_obj_t *o = &p->objs[i];
        if (!o->type) continue;
        int x = o->x / 256, y = o->y / 256;
        if (o->type == SPACE_FUEL) ui_art_frame_anchor(g, "game/space/props/fuel-can", 0, x, y + 12);
        else ui_art_frame_anchor(g, "game/space/props/asteroid", 0, x, y + 14);
    }
}

static void lander(ag_t *g, const adv_space_t *p)
{
    int x = p->x / 256, y = p->y / 256;
    const char *action = p->thrust ? "jet" : "cabin_idle";
    unsigned frame = p->tick / 5 % (p->thrust ? 4 : 6);
    bool outside = false;
    if (p->phase == SPACE_CRASH) {
        x += (p->timer / 3 % 2) ? 2 : -2;
        action = "hard_land"; frame = (unsigned)(ADV_SPACE_CRASH - p->timer) * 8 / ADV_SPACE_CRASH;
    } else if (p->phase == SPACE_LANDED) {
        int t = ADV_SPACE_LANDED - p->timer;
        if (t < 48) { action = "land"; frame = (unsigned)t / 8; }
        else { outside = true; action = "plant_flag"; frame = (unsigned)(t - 48) / 8; }
    }
    if (frame > 7) frame = 7;
    if (p->thrust) {
        ag_glow(g, x, y + 6, 10 + (int)(p->tick / 2 % 3), ag_rgb(255, 160, 60));
        ag_tri(g, x, y + 8, 8, false, ag_rgb(255, 230, 150));
    }
    if (p->side > 0) ag_glow(g, x - 46, y - 27, 7, ag_rgb(160, 220, 255));
    if (p->side < 0) ag_glow(g, x + 45, y - 27, 7, ag_rgb(160, 220, 255));
    ui_art_frame_anchor(g, "game/space/lander/back", 0, x, y);
    if (!outside) crew(g, action, frame, x, y - 22);
    ui_art_frame_anchor(g, "game/space/lander/front", 0, x, y);
    if (outside) {
        int nx = x < 120 ? x + 62 : x - 62;
        crew(g, action, frame, nx, G);
        if (frame >= 4) ui_art_frame_anchor(g, "game/space/props/flag", 0, nx + 10, G);
    }
}

static const char *hint(const adv_space_t *p, bool *warn, char *buf, size_t size)
{
    static const char *const messages[] = {"", "", "硬着陆 · 燃料-250", "没落在着陆台 · 燃料-250", "撞上陨石 · 燃料-250", "燃料罐 +300"};
    *warn = p->feedback && p->message >= SPACE_MSG_HARD && p->message <= SPACE_MSG_ROCK;
    if (p->feedback && p->message == SPACE_MSG_LANDED) { snprintf(buf, size, "平稳着陆 +%d", (int)p->last_bonus); return buf; }
    if (p->feedback && p->message) return messages[p->message];
    if (p->phase == SPACE_FLY && p->vy > ADV_SPACE_SAFE_VY && G - p->y / 256 < 90) { *warn = true; return "太快了！按住OK减速"; }
    return "按住OK喷气 · 按住上下平移";
}

static void play(ag_t *g, const adv_space_t *p, bool footer)
{
    scene(g, p);
    objects(g, p);
    lander(g, p);
    hud(g, p);
    char round[24];
    snprintf(round, sizeof(round), "第%d轮", (int)p->round + 1);
    text(g, round, 8, 38, 12, NT_ALIGN_LEFT, ag_rgb(200, 210, 240));
    if (!footer) return;
    bool warn;
    char buf[40];
    const char *h = hint(p, &warn, buf, sizeof(buf));
    ui_art(g, "ui/bars/bottom", 0, 0, BOTTOM);
    ag_text(g, &collection_font_12, h, 120, 310, NT_ALIGN_CENTER, warn ? ADV_ASSETS_UI_ACCENT : UI_PAPER);
}

static void title(ag_t *g, const adv_model_t *m)
{
    ui_paper(g);
    ui_header(g, "太空", NULL);
    ui_art(g, "ui/wordmarks/space", 0, 20, 42);
    static const char *const lines[] = {"按住OK主引擎减速", "按住上下 向左右平移", "慢慢落在发光的着陆台上",
                                        "硬着陆或撞陨石扣250燃料", "燃料耗尽结束"};
    for (int i = 0; i < 5; i++) text(g, lines[i], 120, 128 + i * 17, 12, NT_ALIGN_CENTER, UI_INK);
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        int x = 60 + tier * 60;
        bool on = earned & adv_stamp_bit(8, tier);
        ag_circle(g, x, 236, 9, ui_tier_color(tier), on ? 255 : 40, on ? UI_INK : ui_tier_color(tier), 2);
        char th[16];
        snprintf(th, sizeof(th), "%u", (unsigned)adv_threshold(8, tier));
        ag_text(g, &nabo_mono_font_12, th, x, 258, NT_ALIGN_CENTER, UI_INK);
    }
    char best[32];
    if (m->best[8] > 9999) snprintf(best, sizeof(best), "最佳 9999+");
    else snprintf(best, sizeof(best), "最佳 %u", (unsigned)m->best[8]);
    ag_text(g, &collection_font_16, best, 120, 283, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, "OK开始 · 双击下暂停 · 双击上返回");
}

static void result(ag_t *g, const adv_model_t *m, const adv_space_t *p, uint32_t elapsed_ms)
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
    crew(g, "settlement_cheer", frame > 7 ? 7 : frame, 120, 238);
    if (m->best[8] > 9999) snprintf(n, sizeof(n), "最佳 9999+");
    else snprintf(n, sizeof(n), "最佳 %u", (unsigned)m->best[8]);
    ag_text(g, &collection_font_16, n, 120, 258, NT_ALIGN_CENTER, UI_INK);
    ui_stamps(g, m, 8, 92, 274, 7, 28);
    ui_footer(g, "OK 再来一局 · 双击上 回地图");
}

void ui_draw_space_session(ag_t *g, const adv_model_t *m)
{
    static int prior_phase = -1;
    static uint32_t prior_seed, phase_started;
    if ((int)m->phase != prior_phase || m->seed != prior_seed) { prior_phase = m->phase; prior_seed = m->seed; phase_started = ui_millis(); }
    ag_begin(g, m->phase == ADV_TITLE ? UI_SCENE_TITLE : m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    if (m->phase == ADV_TITLE) { title(g, m); return; }
    const adv_space_t *p = m->game;
    play(g, p, m->phase == ADV_PLAY);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 120, 90, 40, UI_GOLD);
        ui_number(g, n, 36, 120, 72, NT_ALIGN_CENTER);
        ui_footer(g, "按住OK喷气 · 按住上下平移");
    } else if (m->phase == ADV_END) {
        ag_rect(g, 60, 136, 120, 40, 12, UI_INK, 230, UI_RED, 2);
        ag_text(g, &collection_font_18, "燃料耗尽", 120, 163, NT_ALIGN_CENTER, UI_PAPER);
        ui_footer(g, "双击上 回地图");
    } else if (m->phase == ADV_PAUSE) {
        ag_rect(g, 0, 34, 240, 256, 0, UI_INK, 150, 0, 0);
        ui_popup(g, 24, 80, 192, 160);
        ag_text(g, &collection_font_18, "暂停", 120, 112, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "OK 继续", 120, 148, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "下 重新开始", 120, 178, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "双击上 回地图", 120, 208, NT_ALIGN_CENTER, UI_INK);
        ui_footer(g, "双击下已暂停");
    } else if (m->phase == ADV_RESULT) result(g, m, p, ui_millis() - phase_started);
}
