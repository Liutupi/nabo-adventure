// Shell game sessions: title, the resource bar and score over the game, countdown, pause, end
// and result. Every shell game shares this frame; the game draws only its play field.
#include <stdio.h>
#include "adv_demo.h"
#include "adv_ui_internal.h"

static void draw_backdrop(ag_t *g, const adv_station_t *st)
{
    uint16_t c = st->color;
    int r = (c >> 11) * 255 / 31, gr = (c >> 5 & 63) * 255 / 63, b = (c & 31) * 255 / 31;
    ag_band(g, 0, 320, ag_rgb(r / 5, gr / 5, b / 4 + 20), ag_rgb(r / 2, gr / 2, b / 2));
}

// Placeholder play field (adv_demo.c): the track, the zone and the marker.
static void draw_demo(ag_t *g, const adv_demo_t *d, const adv_station_t *st)
{
    ag_text(g, &collection_font_16, "占位关卡", 120, 108, NT_ALIGN_CENTER, UI_PAPER);
    ag_text(g, &collection_font_12, "正式玩法和美术完成后替换", 120, 128, NT_ALIGN_CENTER, UI_DIM);
    int zx = 20 + (d->zc - d->zh) * 200 / 1000, zw = d->zh * 2 * 200 / 1000, mx = 20 + d->p * 200 / 1000;
    ag_rect(g, 16, 180, 208, 20, 10, UI_INK, 200, d->miss ? UI_RED : UI_PAPER, d->miss ? 2 : 1);
    ag_rect(g, zx, 182, zw, 16, 8, st->color, 230, 0, 0);
    if (d->hit) ag_glow(g, mx, 190, 26, UI_GOLD);
    ag_rect(g, mx - 3, 174, 6, 32, 3, UI_WHITE, 255, UI_INK, 1);
    ag_tri(g, mx, 214, 10, true, UI_WHITE);
    ag_text(g, &collection_font_12, "色块里按 OK 得分 · 按错扣四分之一", 120, 248, NT_ALIGN_CENTER, UI_PAPER);
}

static void draw_hud(ag_t *g, const adv_model_t *m, const adv_station_t *st)
{
    adv_status_t status = adv_game_status(m);
    ag_rect(g, 0, 0, 240, 34, 0, UI_INK, 210, 0, 0);
    ag_text(g, &collection_font_12, st->resource, 10, 21, NT_ALIGN_LEFT, UI_PAPER);
    int w = status.resource * 120 / ADV_RESOURCE_MAX;
    ag_rect(g, 40, 12, 124, 10, 5, ag_rgb(20, 24, 40), 255, UI_PAPER, 1);
    if (w > 0) ag_rect(g, 42, 14, w, 6, 3, status.resource < ADV_RESOURCE_MAX / 4 ? UI_RED : st->color, 255, 0, 0);
    char score[16];
    snprintf(score, sizeof(score), "%u", (unsigned)status.score);
    ag_text(g, &nabo_poster_font_28, score, 230, 29, NT_ALIGN_RIGHT, UI_WHITE);
}

static void draw_title(ag_t *g, const adv_model_t *m, const adv_station_t *st, int s)
{
    ag_text(g, &collection_font_12, st->world, 120, 44, NT_ALIGN_CENTER, UI_PAPER);
    ag_text(g, &nabo_poster_font_28, st->en, 120, 80, NT_ALIGN_CENTER, UI_WHITE);
    ag_text(g, &collection_font_18, st->cn, 120, 108, NT_ALIGN_CENTER, UI_GOLD);
    if (st->placeholder) {
        ag_rect(g, 80, 120, 80, 20, 10, UI_GOLD, 255, UI_INK, 1);
        ag_text(g, &collection_font_12, "占位关卡", 120, 135, NT_ALIGN_CENTER, UI_INK);
    }
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        int x = 60 + tier * 60;
        bool on = earned & adv_stamp_bit(s, tier);
        ag_circle(g, x, 182, 18, ui_tier_color(tier), on ? 255 : 40, on ? UI_INK : ui_tier_color(tier), 2);
        char th[16];
        snprintf(th, sizeof(th), "%u", (unsigned)adv_threshold(s, tier));
        ag_text(g, &nabo_mono_font_12, th, x, 218, NT_ALIGN_CENTER, UI_PAPER);
    }
    char best[32];
    snprintf(best, sizeof(best), "最佳 %u", (unsigned)m->best[s]);
    ag_text(g, &collection_font_18, best, 120, 254, NT_ALIGN_CENTER, UI_PAPER);
    ui_footer(g, "OK 开始 · 长按上 回地图");
}

static void draw_card(ag_t *g, int y, int h)
{
    ag_rect(g, 0, 34, 240, 286, 0, UI_INK, 150, 0, 0);
    ag_rect(g, 24, y, 192, h, 14, UI_PAPER, 250, UI_INK, 2);
}

static void draw_result(ag_t *g, const adv_model_t *m, int s)
{
    adv_status_t status = adv_game_status(m);
    draw_card(g, 60, 200);
    ag_text(g, &collection_font_16, "本局成绩", 120, 88, NT_ALIGN_CENTER, UI_INK);
    char line[32];
    snprintf(line, sizeof(line), "%u", (unsigned)status.score);
    ag_text(g, &nabo_poster_font_48, line, 120, 142, NT_ALIGN_CENTER, UI_INK);
    if (m->record) {
        ag_rect(g, 82, 152, 76, 20, 10, UI_GOLD, 255, UI_INK, 1);
        ag_text(g, &collection_font_12, m->test ? "测试不记录" : "新纪录", 120, 167, NT_ALIGN_CENTER, UI_INK);
    }
    snprintf(line, sizeof(line), "最佳 %u", (unsigned)m->best[s]);
    ag_text(g, &collection_font_16, line, 120, 194, NT_ALIGN_CENTER, UI_INK);
    ui_stamps(g, m, s, 92, 226, 9, 28);
    ui_footer(g, "OK 再来一局 · 长按上 回地图");
}

void ui_draw_session(ag_t *g, const adv_model_t *m)
{
    int s = m->station;
    const adv_station_t *st = &adv_station[s];
    if (m->phase == ADV_TITLE) {
        ag_begin(g, UI_SCENE_TITLE);
        draw_backdrop(g, st);
        draw_title(g, m, st, s);
        return;
    }
    ag_begin(g, m->phase == ADV_RESULT ? UI_SCENE_RESULT : UI_SCENE_PLAY);
    draw_backdrop(g, st);
    if (st->game == &adv_demo_game) draw_demo(g, m->game, st);
    draw_hud(g, m, st);
    if (m->phase == ADV_READY) {
        char n[12];
        snprintf(n, sizeof(n), "%d", (m->t + 59) / 60);
        ag_glow(g, 120, 150, 50, UI_GOLD);
        ag_text(g, &nabo_poster_font_48, n, 120, 168, NT_ALIGN_CENTER, UI_WHITE);
        ag_text(g, &collection_font_18, "准备", 120, 270, NT_ALIGN_CENTER, UI_PAPER);
    } else if (m->phase == ADV_END) {
        ag_rect(g, 70, 136, 100, 40, 12, UI_INK, 230, UI_RED, 2);
        ag_text(g, &collection_font_18, "结束", 120, 163, NT_ALIGN_CENTER, UI_PAPER);
    } else if (m->phase == ADV_PAUSE) {
        draw_card(g, 80, 160);
        ag_text(g, &collection_font_18, "暂停", 120, 112, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "OK 继续", 120, 148, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "下 重新开始", 120, 178, NT_ALIGN_CENTER, UI_INK);
        ag_text(g, &collection_font_16, "长按上 回地图", 120, 208, NT_ALIGN_CENTER, UI_INK);
    } else if (m->phase == ADV_RESULT) draw_result(g, m, s);
}
