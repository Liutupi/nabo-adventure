// Vertical world map, animated travel, passport and stamp ceremony.
#include <stdio.h>
#include "adv_ui_internal.h"

#define MAP_TOP 120          // world y of the top station
#define MAP_SLOT 112         // world distance between stations
#define MAP_H (MAP_TOP + (ADV_STATIONS - 1) * MAP_SLOT + 140)
#define NODE_R 17
#define TURN_MS 500          // six frames at 12 fps, including the final frame
#define WALK_MS 667          // eight frames at 12 fps

static int s_cursor = -1, s_from_x, s_from_y, s_from_cam;
static uint32_t s_move_start, s_idle_start;
static bool s_moving;
void ui_map_reset(void) { s_cursor = -1; s_moving = false; }

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

static int blend(int from, int to, uint32_t t)
{
    if (t > WALK_MS) t = WALK_MS;
    return from + (to - from) * (int)t / WALK_MS;
}

static uint32_t move_time(void) { return ui_millis() - s_move_start; }

static void traveler(const adv_model_t *m, int *x, int *y, int *cam, const char **action, uint32_t *time)
{
    int i = adv_path_index(m->cursor), tx = node_x(i), ty = world_y(i);
    int target_cam = camera(m);
    uint32_t elapsed = move_time();
    if (s_cursor != m->cursor) {
        if (s_cursor < 0) { s_from_x = tx; s_from_y = ty; s_from_cam = target_cam; s_idle_start = ui_millis(); }
        else {
            int old = adv_path_index(s_cursor);
            uint32_t p = !s_moving ? WALK_MS : elapsed > TURN_MS ? elapsed - TURN_MS : 0;
            s_from_x = blend(s_from_x, node_x(old), p);
            s_from_y = blend(s_from_y, world_y(old), p);
            adv_model_t previous = *m; previous.cursor = s_cursor;
            s_from_cam = blend(s_from_cam, camera(&previous), p);
        }
        s_moving = s_cursor >= 0;
        s_cursor = m->cursor; s_move_start = ui_millis(); elapsed = 0;
    }
    uint32_t p = !s_moving ? WALK_MS : elapsed > TURN_MS ? elapsed - TURN_MS : 0;
    *x = blend(s_from_x, tx, p); *y = blend(s_from_y, ty, p);
    *cam = blend(s_from_cam, target_cam, p);
    bool left = tx < s_from_x;
    if (!s_moving || elapsed >= 2 * TURN_MS + WALK_MS) {
        if (s_moving) s_idle_start = s_move_start + 2 * TURN_MS + WALK_MS;
        s_moving = false; *action = "travel/idle"; *time = ui_millis() - s_idle_start;
    }
    else if (elapsed < TURN_MS) { *action = left ? "travel/turn_left" : "travel/turn_right"; *time = elapsed; }
    else if (elapsed < TURN_MS + WALK_MS) { *action = left ? "travel/walk_left" : "travel/walk_right"; *time = elapsed - TURN_MS; }
    else { *action = left ? "travel/turn_front_from_left" : "travel/turn_front_from_right"; *time = elapsed - TURN_MS - WALK_MS; }
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
            if (y > 30 && y < 290) ui_art(g, "ui/map/footprints-forward", 0, x - 5, y - 5);
        }
    }
}

static void draw_decor(ag_t *g, int cam)
{
    static const char *const tiles[] = {
        "deep-sea/coral-fan", "harbor/rope-coil", "town/flowerbed", "rail/wheat",
        "night-forest/fireflies", "mountain/young-pine", "ski/snow-pine", "sky/cloud-small", "space/ring-planet"
    };
    for (int i = 0; i < ADV_STATIONS; i++) {
        int y = world_y(i) - cam - 92;
        if (y < 0 || y > 288) continue;
        char asset[80]; snprintf(asset, sizeof(asset), "static/tiles/%s", tiles[i]);
        ui_art(g, asset, 0, i % 2 ? 12 : 196, y);
    }
}

static void draw_station(ag_t *g, const adv_model_t *m, int i, int cam)
{
    int s = adv_path[i], x = node_x(i), y = world_y(i) - cam;
    if (y < 10 || y > 310) return;
    const adv_station_t *st = &adv_station[s];
    bool open = adv_unlocked(m, s), here = s == m->cursor;
    char asset[80];
    snprintf(asset, sizeof(asset), "static/landmark/%s", st->id);
    if (open) ui_art(g, asset, 0, x - 48, y - 83);
    else ui_art_dim(g, asset, x - 48, y - 83);
    ui_art(g, here ? "ui/map/station-current" : open ? "ui/map/station-unlocked" :
           "ui/map/station-locked", 0, x - 24, y - 14);
    // Label card on the side away from the path's turn.
    int cx = x < 120 ? x + NODE_R + 8 : x - NODE_R - 8 - 112;
    int top = y - 26;
    uint16_t ink = here ? UI_WHITE : open ? UI_INK : UI_LOCK;
    ag_ninepatch(g, here ? &adv_assets_patch_info_current : &adv_assets_patch_info_normal,
                 cx, top, 112, 52);
    ag_text_top(g, &collection_font_16, st->cn, cx + 8, top + 8, NT_ALIGN_LEFT, ink);
    if (s == ADV_KIOSK) {
        ag_text_top(g, &collection_font_12, "护照 · 设置", cx + 8, top + 30, NT_ALIGN_LEFT, ink);
    } else if (!open) {
        ag_text_top(g, &collection_font_12, "未解锁", cx + 8, top + 30, NT_ALIGN_LEFT, ink);
    } else {
        ag_text_top(g, &collection_font_12, "最佳", cx + 104, top + 8, NT_ALIGN_RIGHT, ink);
        ui_stamps(g, m, s, cx + 13, top + 37, 4, 11);
        char best[16];
        if (m->best[s] > 9999) snprintf(best, sizeof(best), "9999+");
        else snprintf(best, sizeof(best), "%u", (unsigned)m->best[s]);
        if (here) ui_number_tint(g, best, 20, cx + 104, top + 24, NT_ALIGN_RIGHT, UI_WHITE);
        else ui_number(g, best, 20, cx + 104, top + 24, NT_ALIGN_RIGHT);
    }
    if (!open) ui_art(g, "ui/map/lock", 0, x - 8, y - 55);
}

void ui_draw_map(ag_t *g, const adv_model_t *m)
{
    int x, y, cam; const char *action; uint32_t time;
    traveler(m, &x, &y, &cam, &action, &time);
    draw_ground(g, cam);
    draw_decor(g, cam);
    draw_path(g, cam);
    for (int i = 0; i < ADV_STATIONS; i++) draw_station(g, m, i, cam);
    ui_art_anchor(g, action, time, x, y - cam + 15);
    const adv_station_t *st = &adv_station[m->cursor];
    char count[16];
    snprintf(count, sizeof(count), "章 %d/24", ui_stamp_count(m));
    ui_header(g, "冒险地图", count);
    ag_text_top(g, &collection_font_12, st->world, 104, 11, NT_ALIGN_LEFT, UI_WHITE);
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
    ui_paper(g);
    int selected = m->passport + 1, tier = 0;
    uint32_t earned = adv_earned(m);
    while (tier < 3 && (earned & adv_stamp_bit(selected, tier))) tier++;
    static const char *const tiers[] = {"铜章", "银章", "金章"};
    char goal[24], count[16];
    if (tier == 3) snprintf(goal, sizeof(goal), "三枚章已集齐");
    else snprintf(goal, sizeof(goal), "%s %u", tiers[tier], (unsigned)adv_threshold(selected, tier));
    ui_header(g, "冒险护照", goal);
    ui_art(g, "ui/passport/header", 0, 12, 40);
    snprintf(count, sizeof(count), "%02d / 24", ui_stamp_count(m));
    ag_text_top(g, &collection_font_12, count, 224, 48, NT_ALIGN_RIGHT, UI_DIM);
    for (int i = 0; i < 8; i++) {
        int s = i + 1, x = i % 2 ? 124 : 12, y = 70 + (i / 2) * 54;
        bool on = i == m->passport, open = adv_unlocked(m, s);
        uint16_t ink = on ? UI_WHITE : open ? UI_INK : UI_LOCK;
        ui_art(g, on ? "ui/passport/grid-current" : "ui/passport/grid-normal", 0, x, y);
        if (!open) {
            if (on) ui_art_tint(g, "ui/passport/locked-mask", x, y, UI_WHITE);
            else ui_art(g, "ui/passport/locked-mask", 0, x, y);
        }
        ag_text_top(g, &collection_font_16, adv_station[s].cn, x + 8, y + 8, NT_ALIGN_LEFT, ink);
        if (open) {
            ui_stamps(g, m, s, x + 13, y + 37, 4, 13);
            char best[16];
            if (m->best[s] > 9999) snprintf(best, sizeof(best), "9999+");
            else snprintf(best, sizeof(best), "%u", (unsigned)m->best[s]);
            ag_text_top(g, &collection_font_12, best, x + 96, y + 30, NT_ALIGN_RIGHT, ink);
        } else ag_text_top(g, &collection_font_12, "未解锁", x + 8, y + 30, NT_ALIGN_LEFT, ink);
    }
    ui_footer(g, "上/下 查看 · OK 返回");
}

// ---------- stamp ceremony ----------

void ui_draw_stamp(ag_t *g, const adv_model_t *m)
{
    int s = m->stamp / 3 + 1, tier = m->stamp % 3;
    uint16_t c = ui_tier_color(tier);
    ui_paper(g);
    ui_header(g, "获得新印章", NULL);
    char line[64];
    snprintf(line, sizeof(line), "%s · %s", adv_station[s].world, adv_station[s].cn);
    ag_text(g, &collection_font_16, line, 120, 78, NT_ALIGN_CENTER, UI_INK);
    ui_popup(g, 48, 98, 144, 128);
    char asset[64];
    snprintf(asset, sizeof(asset), "static/stamp/%s", adv_station[s].id);
    ui_art_tint(g, asset, 72, 114, c);
    static const char *const names[] = {"铜章", "银章", "金章"};
    // Tier metal remains on the seal; the small caption needs full ink contrast.
    ag_text(g, &collection_font_18, names[tier], 120, 246, NT_ALIGN_CENTER, UI_INK);
    if (tier == 0 && s + 1 < ADV_STATIONS) snprintf(line, sizeof(line), "解锁下一站：%s", adv_station[s + 1].cn);
    else if (tier == 1) snprintf(line, sizeof(line), "解锁第二款服装");
    else snprintf(line, sizeof(line), "护照金章");
    ag_text(g, &collection_font_16, line, 120, 272, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, "OK 收下");
}
