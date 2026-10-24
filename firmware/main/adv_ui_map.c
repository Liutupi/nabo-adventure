// The vertical adventure map (deep sea at the bottom, space at the top), the passport and the
// stamp ceremony. Placeholder art: shapes and text only, no NABO drawing until the sprite pack
// lands (game-art/adventure/ART_BRIEF.md). The camera snaps; hardware scrolling is a TODO.
#include <stdio.h>
#include "adv_ui_internal.h"

#define MAP_TOP 120          // world y of the top station
#define MAP_SLOT 112         // world distance between stations
#define MAP_H (MAP_TOP + (ADV_STATIONS - 1) * MAP_SLOT + 140)
#define NODE_R 17

typedef struct { uint8_t r, g, b; } rgb_t;
// Ground colour at each station along the path, bottom (dive) to top (space).
static const rgb_t WORLD[ADV_STATIONS] = {
    {6, 20, 52}, {40, 120, 160}, {246, 226, 180}, {150, 200, 110}, {24, 48, 60},
    {150, 170, 200}, {225, 236, 248}, {140, 200, 250}, {16, 10, 40},
};

static int world_y(int path_index) { return MAP_TOP + (ADV_STATIONS - 1 - path_index) * MAP_SLOT; }
static int node_x(int path_index) { return path_index % 2 ? 160 : 80; }
static uint16_t c565(rgb_t c) { return ag_rgb(c.r, c.g, c.b); }

static int camera(const adv_model_t *m)
{
    int cam = world_y(adv_path_index(m->cursor)) - 176;
    return cam < 0 ? 0 : cam > MAP_H - 320 ? MAP_H - 320 : cam;
}

static void draw_ground(ag_t *g, int cam)
{
    // Bands between neighbouring stations, plus the sky above space and the sea floor below.
    ag_band(g, 0 - cam, world_y(ADV_STATIONS - 1), ag_rgb(5, 3, 20), c565(WORLD[ADV_STATIONS - 1]));
    for (int i = ADV_STATIONS - 1; i > 0; i--) {
        int y0 = world_y(i) - cam, y1 = world_y(i - 1) - cam;
        if (y1 < 0 || y0 > 320) continue;
        ag_band(g, y0, y1 - y0, c565(WORLD[i]), c565(WORLD[i - 1]));
    }
    int bottom = world_y(0) - cam;
    if (bottom < 320) ag_band(g, bottom, MAP_H - world_y(0), c565(WORLD[0]), ag_rgb(2, 8, 24));
}

static void draw_path(ag_t *g, int cam)
{
    for (int i = 0; i + 1 < ADV_STATIONS; i++) {
        int ax = node_x(i), ay = world_y(i) - cam, bx = node_x(i + 1), by = world_y(i + 1) - cam;
        if (ay < -20 && by < -20) continue;
        if (ay > 340 && by > 340) continue;
        for (int k = 1; k <= 5; k++) {
            int x = ax + (bx - ax) * k / 6, y = ay + (by - ay) * k / 6;
            if (y > 30 && y < 290) ag_circle(g, x, y, 3, UI_WHITE, 220, UI_INK, 1);
        }
    }
}

static void draw_station(ag_t *g, const adv_model_t *m, int i, int cam)
{
    int s = adv_path[i], x = node_x(i), y = world_y(i) - cam;
    if (y < 10 || y > 310) return;
    const adv_station_t *st = &adv_station[s];
    bool open = adv_unlocked(m, s), here = s == m->cursor;
    if (here) {
        ag_glow(g, x, y, 34, UI_GOLD);
        ag_circle(g, x, y, NODE_R + 5, UI_GOLD, 0, UI_GOLD, 2);
    }
    ag_circle(g, x, y, NODE_R, open ? st->color : UI_LOCK, 255, UI_INK, 2);
    char mark[8];
    if (s == ADV_KIOSK) snprintf(mark, sizeof(mark), "护");
    else if (open) snprintf(mark, sizeof(mark), "%d", s);
    else snprintf(mark, sizeof(mark), "?");
    ag_text(g, &collection_font_18, mark, x, y + 7, NT_ALIGN_CENTER, UI_INK);
    // Label card on the side away from the path's turn.
    int cx = x < 120 ? x + NODE_R + 8 : x - NODE_R - 8 - 112;
    ag_rect(g, cx, y - 20, 112, 40, 8, UI_PAPER, 235, here ? UI_GOLD : UI_INK, here ? 2 : 1);
    ag_text(g, &collection_font_16, st->cn, cx + 8, y - 2, NT_ALIGN_LEFT, open ? UI_INK : UI_LOCK);
    if (s == ADV_KIOSK) {
        ag_text(g, &collection_font_12, "护照 · 设置", cx + 8, y + 15, NT_ALIGN_LEFT, UI_INK);
    } else if (!open) {
        ag_text(g, &collection_font_12, "未解锁", cx + 8, y + 15, NT_ALIGN_LEFT, UI_LOCK);
    } else {
        ui_stamps(g, m, s, cx + 13, y + 10, 4, 11);
        char best[16];
        snprintf(best, sizeof(best), "%u", (unsigned)m->best[s]);
        ag_text(g, &nabo_mono_font_12, best, cx + 104, y + 14, NT_ALIGN_RIGHT, UI_INK);
    }
    if (here) {
        ag_rect(g, x - 22, y - NODE_R - 26, 44, 16, 8, UI_GOLD, 255, UI_INK, 1);
        ag_text(g, &nabo_mono_font_12, "NABO", x, y - NODE_R - 14, NT_ALIGN_CENTER, UI_INK);
        ag_tri(g, x, y - NODE_R - 6, 6, false, UI_INK);
    }
}

void ui_draw_map(ag_t *g, const adv_model_t *m)
{
    int cam = camera(m);
    draw_ground(g, cam);
    draw_path(g, cam);
    for (int i = 0; i < ADV_STATIONS; i++) draw_station(g, m, i, cam);
    const adv_station_t *st = &adv_station[m->cursor];
    char title[48], count[16];
    snprintf(title, sizeof(title), "冒险地图 · %s", st->world);
    snprintf(count, sizeof(count), "章 %d/24", ui_stamp_count(m));
    ui_header(g, title, count);
    if (m->cursor == ADV_KIOSK) ui_footer(g, "OK 进入护照亭 · 上/下 走");
    else if (!adv_unlocked(m, m->cursor)) {
        char hint[64];
        snprintf(hint, sizeof(hint), "拿到%s的铜章后解锁", adv_station[m->cursor - 1].cn);
        ui_footer(g, hint);
    } else ui_footer(g, "OK 进入 · 长按OK 护照 · 上/下 走");
}

// ---------- passport ----------

void ui_draw_passport(ag_t *g, const adv_model_t *m)
{
    ag_band(g, 0, 320, ag_rgb(30, 40, 74), ag_rgb(58, 36, 70));
    char count[16];
    snprintf(count, sizeof(count), "章 %d/24", ui_stamp_count(m));
    ui_header(g, "冒险护照", count);
    for (int i = 0; i < 8; i++) {
        int s = i + 1, x = i % 2 ? 124 : 12, y = 38 + (i / 2) * 57;
        bool on = i == m->passport, open = adv_unlocked(m, s);
        ag_rect(g, x, y, 104, 52, 8, open ? UI_PAPER : ag_rgb(70, 70, 90), 255, on ? UI_GOLD : UI_INK, on ? 3 : 1);
        ag_rect(g, x + 4, y + 4, 6, 44, 3, adv_station[s].color, open ? 255 : 90, 0, 0);
        ag_text(g, &collection_font_16, adv_station[s].cn, x + 16, y + 21, NT_ALIGN_LEFT, open ? UI_INK : UI_LOCK);
        ui_stamps(g, m, s, x + 22, y + 37, 5, 13);
        char best[16];
        snprintf(best, sizeof(best), "%u", (unsigned)m->best[s]);
        ag_text(g, &nabo_mono_font_12, best, x + 98, y + 41, NT_ALIGN_RIGHT, open ? UI_INK : UI_LOCK);
    }
    int s = m->passport + 1;
    char line[64];
    uint32_t earned = adv_earned(m);
    int tier = 0;
    while (tier < 3 && (earned & adv_stamp_bit(s, tier))) tier++;
    static const char *const tiers[] = {"铜章", "银章", "金章"};
    if (tier == 3) snprintf(line, sizeof(line), "%s · 三枚章已集齐", adv_station[s].cn);
    else snprintf(line, sizeof(line), "%s · 最佳 %u · %s %u", adv_station[s].cn, (unsigned)m->best[s], tiers[tier],
                  (unsigned)adv_threshold(s, tier));
    ag_text(g, &collection_font_16, line, 120, 282, NT_ALIGN_CENTER, UI_PAPER);
    ui_footer(g, "上/下 查看 · OK 返回");
}

// ---------- stamp ceremony ----------

void ui_draw_stamp(ag_t *g, const adv_model_t *m)
{
    int s = m->stamp / 3 + 1, tier = m->stamp % 3;
    uint16_t c = ui_tier_color(tier);
    ag_band(g, 0, 320, UI_INK, ag_rgb(46, 30, 64));
    ag_text(g, &collection_font_18, "获得新印章", 120, 52, NT_ALIGN_CENTER, UI_GOLD);
    char line[64];
    snprintf(line, sizeof(line), "%s · %s", adv_station[s].world, adv_station[s].cn);
    ag_text(g, &collection_font_16, line, 120, 78, NT_ALIGN_CENTER, UI_PAPER);
    ag_glow(g, 120, 162, 86, c);
    ag_circle(g, 120, 162, 60, c, 255, UI_INK, 3);
    ag_circle(g, 120, 162, 50, c, 0, UI_INK, 1);
    ag_text(g, &nabo_poster_font_28, adv_station[s].en, 120, 172, NT_ALIGN_CENTER, UI_INK);
    static const char *const names[] = {"铜章", "银章", "金章"};
    ag_text(g, &collection_font_18, names[tier], 120, 246, NT_ALIGN_CENTER, c);
    if (tier == 0 && s + 1 < ADV_STATIONS) snprintf(line, sizeof(line), "解锁下一站：%s", adv_station[s + 1].cn);
    else if (tier == 1) snprintf(line, sizeof(line), "解锁第二款服装");
    else snprintf(line, sizeof(line), "护照金章");
    ag_text(g, &collection_font_16, line, 120, 272, NT_ALIGN_CENTER, UI_PAPER);
    ui_footer(g, "OK 收下");
}
