// Legacy 跳一跳 page, moved unchanged from the NABO games collection (collection_ui.c): the
// jump model renders its own rows; labels are overlaid with the DIVE text helper.
#include <stdio.h>
#include "adv_ui.h"
#include "adv_ui_internal.h"
#include "nabo_dive_text.h"
#include "adv_stations.h"

uint16_t *adv_ui_strip(void);
bool adv_ui_ready(void);
bool adv_ui_capturing(void);
void adv_ui_capture_done(void);
void adv_ui_send(void *ctx, int x, int y, int w, int h, uint16_t *px);

static bool s_jump_valid;
static nabo_jump_t s_previous;
static uint32_t s_previous_ms;

void adv_jump_invalidate(void) { s_jump_valid = false; }

static int min(int a, int b) { return a < b ? a : b; }
static int max(int a, int b) { return a > b ? a : b; }

// 2026-10-30 collection polish (rules untouched): three medal pips under BEST, a game-over card with the
// medal row and the gap to the next one. Thresholds come from the station table (jump = station 1).
#define JUMP_STATION 1
#define CARD_X0 20
#define CARD_X1 219
#define CARD_Y0 104
#define CARD_Y1 200
#define PIP_Y 50
#define MEDAL_Y 176
static uint32_t s_best_before;      // best when this run started, to tell a freshly earned medal
static int earned(uint32_t score) { int n = 0; for (int i = 0; i < 3; i++) n += score >= adv_threshold(JUMP_STATION, i); return n; }
static uint16_t blend(uint16_t bg, uint16_t fg, unsigned a)
{
    unsigned r = (((bg >> 11) & 31) * (255 - a) + ((fg >> 11) & 31) * a) / 255;
    unsigned g = (((bg >> 5) & 63) * (255 - a) + ((fg >> 5) & 63) * a) / 255;
    unsigned b = ((bg & 31) * (255 - a) + (fg & 31) * a) / 255;
    return (uint16_t)(r << 11 | g << 5 | b);
}
static const uint16_t kMedal[3] = {UI_BRONZE, UI_SILVER, UI_GOLDSTAMP};
static void medal_row(uint16_t *line, int y, int x0, int x1, int cx, int cy, int r, int tier, bool on, uint16_t empty)
{
    int dy = y - cy;
    if (dy < -r || dy > r) return;
    for (int x = max(x0, cx - r); x <= min(x1, cx + r); x++) {
        int dx = x - cx, d = dx * dx + dy * dy;
        if (d > r * r) continue;
        uint16_t c = on ? kMedal[tier] : empty;
        if (on && d >= (r - 1) * (r - 1)) c = blend(c, UI_WHITE, 140);     // light rim
        line[x - x0] = c;
    }
}
static void overlay_row(const nabo_jump_t *game, int y, int x0, int x1, uint16_t *line)
{
    int have = earned(game->best);
    for (int i = 0; i < 3; i++) medal_row(line, y, x0, x1, 196 + i * 14, PIP_Y, 5, i, i < have, UI_DIM);
    if (game->phase != JUMP_OVER || y < CARD_Y0 || y > CARD_Y1) return;
    for (int x = max(x0, CARD_X0); x <= min(x1, CARD_X1); x++) {
        bool corner = (y == CARD_Y0 || y == CARD_Y1) && (x == CARD_X0 || x == CARD_X1);
        if (!corner) line[x - x0] = blend(line[x - x0], UI_INK, 222);
    }
    for (int i = 0; i < 3; i++) medal_row(line, y, x0, x1, 96 + i * 24, MEDAL_Y, 7, i, i < have, blend(UI_INK, UI_WHITE, 60));
}

static void jump_rect(const nabo_jump_t *game, uint32_t ms, int x0, int y0, int x1, int y1,
                      dive_text_layout_t *labels, int n) {
    x0 = max(0, x0); x1 = min(239, x1); y0 = max(0, y0); y1 = min(319, y1);
    int w = x1 - x0 + 1;
    if (w <= 0 || y1 < y0) return;
    for (int y = y0; y <= y1; y += AG_STRIP) {
        int rows = min(AG_STRIP, y1 - y + 1);
        uint16_t *strip = adv_ui_strip();
        for (int row = 0; row < rows; row++) {
            uint16_t *line = strip + row * w;
            nabo_jump_draw_row(game, ms, y + row, x0, x1, line);
            overlay_row(game, y + row, x0, x1, line);
            for (int i = 0; i < n; i++) dive_text_row(&labels[i], y + row, x0, x1 + 1, line);
            for (int col = 0; col < w; col++) line[col] = __builtin_bswap16(line[col]);
        }
        adv_ui_send(NULL, x0, y, w, rows, strip);
    }
}

void adv_jump_draw(const nabo_jump_t *game, uint32_t ms, bool full) {
    if (!adv_ui_ready()) return;
    static const char *const normal[] = {"NABO 医院", "NABO 靶心", "床旁书房", "功德木鱼", "NABO 播客", "值班咖啡"};
    static const char *const tiny[] = {"外带咖啡", "拿铁咖啡", "冰美式", "迷你电脑", "小音箱", "黑胶唱片"};
    char score[16], best[24], station[100];
    snprintf(score, sizeof(score), "%lu", (unsigned long)game->score);
    snprintf(best, sizeof(best), "BEST %lu", (unsigned long)game->best);
    if (game->next_size == JUMP_SIZE_CUP)
        snprintf(station, sizeof(station), "下一站 %s · 一人位", tiny[game->next_skin % 6]);
    else snprintf(station, sizeof(station), "下一站 %s%s", game->next_size == JUMP_SIZE_SMALL ? "迷你" : "", normal[game->next_skin % 6]);
    if (game->score == 0 && game->phase != JUMP_OVER) s_best_before = game->best;
    char combo[24], gap[40], card_score[16];
    int before = earned(s_best_before), now = earned(game->score), have = earned(game->best);
    if (game->combo >= 2) snprintf(combo, sizeof(combo), "正中 ×%d 连", (int)game->combo); else combo[0] = 0;
    static const char *const tier_name[3] = {"铜章", "银章", "金章"};
    if (now > before) snprintf(gap, sizeof(gap), "拿到%s!", tier_name[now - 1]);
    else if (have < 3) snprintf(gap, sizeof(gap), "离%s %lu 分", tier_name[have], (unsigned long)(adv_threshold(JUMP_STATION, have) - game->score));
    else snprintf(gap, sizeof(gap), "三枚章都拿到了");
    snprintf(card_score, sizeof(card_score), "%lu", (unsigned long)game->score);
    bool over = game->phase == JUMP_OVER, record = over && game->score > s_best_before;
    dive_text_layout_t labels[10];
    dive_text_layout(&labels[0], &nabo_poster_font_28, score, 16, 38, DIVE_ALIGN_LEFT, 0, UI_INK, 255);
    dive_text_layout(&labels[1], &nabo_mono_font_12, best, 225, 31, DIVE_ALIGN_RIGHT, 0, UI_INK, 255);
    dive_text_layout(&labels[2], &collection_font_16, station, 120, 77, DIVE_ALIGN_CENTER, 0, UI_INK, 255);
    dive_text_layout(&labels[3], &collection_font_16, game->phase == JUMP_OVER ? "游戏结束 · OK再来一局" : "按住OK蓄力，松开起跳",
                     120, 303, DIVE_ALIGN_CENTER, 0, UI_INK, 255);
    dive_text_layout(&labels[4], &collection_font_12, "双击上回地图 · 下换角色", 120, 316, DIVE_ALIGN_CENTER, 0, UI_INK, 255);
    int n = 5;
    if (game->combo >= 2) dive_text_layout(&labels[n++], &collection_font_12, combo, 16, 58, DIVE_ALIGN_LEFT, 0, UI_RED, 255);
    if (over) {
        dive_text_layout(&labels[n++], &collection_font_16, record ? "新纪录!" : "本局", 120, 126, DIVE_ALIGN_CENTER, 0, record ? UI_GOLD : UI_WHITE, 255);
        dive_text_layout(&labels[n++], &nabo_poster_font_28, card_score, 120, 160, DIVE_ALIGN_CENTER, 0, UI_WHITE, 255);
        dive_text_layout(&labels[n++], &collection_font_12, gap, 120, 196, DIVE_ALIGN_CENTER, 0, now > before ? UI_GOLD : UI_WHITE, 255);
    }
    full |= !s_jump_valid || adv_ui_capturing() || game->character != s_previous.character || over != (s_previous.phase == JUMP_OVER);
    if (full) jump_rect(game, ms, 0, 0, 239, 319, labels, n);
    else {
        int x0, y0, x1, y1, a0, b0, a1, b1;
        bool moving = nabo_jump_camera_moving(game, ms) || nabo_jump_camera_moving(&s_previous, s_previous_ms);
        if (moving) {
            nabo_jump_scene_bounds(game, ms, &x0, &y0, &x1, &y1);
            nabo_jump_scene_bounds(&s_previous, s_previous_ms, &a0, &b0, &a1, &b1);
        } else {
            nabo_jump_character_bounds(game, ms, &x0, &y0, &x1, &y1);
            nabo_jump_character_bounds(&s_previous, s_previous_ms, &a0, &b0, &a1, &b1);
        }
        jump_rect(game, ms, min(x0, a0), min(y0, b0), max(x1, a1), max(y1, b1), labels, n);
        if (game->score != s_previous.score || game->best != s_previous.best || game->combo != s_previous.combo || game->next_skin != s_previous.next_skin || game->next_size != s_previous.next_size)
            jump_rect(game, ms, 0, 0, 239, 82, labels, n);
        if ((game->phase == JUMP_OVER) != (s_previous.phase == JUMP_OVER))
            jump_rect(game, ms, 0, 287, 239, 319, labels, n);
        if (nabo_jump_charging(game) || nabo_jump_charging(&s_previous))
            jump_rect(game, ms, 30, 281, 210, 286, labels, n);
    }
    s_previous = *game; s_previous_ms = ms; s_jump_valid = true; adv_ui_capture_done();
}
