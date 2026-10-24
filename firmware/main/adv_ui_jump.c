// Legacy 跳一跳 page, moved unchanged from the NABO games collection (collection_ui.c): the
// jump model renders its own rows; labels are overlaid with the DIVE text helper.
#include <stdio.h>
#include "adv_ui.h"
#include "adv_ui_internal.h"
#include "nabo_dive_text.h"

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
    dive_text_layout_t labels[5];
    dive_text_layout(&labels[0], &nabo_poster_font_28, score, 16, 38, DIVE_ALIGN_LEFT, 0, UI_INK, 255);
    dive_text_layout(&labels[1], &nabo_mono_font_12, best, 225, 31, DIVE_ALIGN_RIGHT, 0, UI_INK, 255);
    dive_text_layout(&labels[2], &collection_font_16, station, 120, 77, DIVE_ALIGN_CENTER, 0, UI_INK, 255);
    dive_text_layout(&labels[3], &collection_font_16, game->phase == JUMP_OVER ? "游戏结束 · OK再来一局" : "按住OK蓄力，松开起跳",
                     120, 303, DIVE_ALIGN_CENTER, 0, UI_INK, 255);
    dive_text_layout(&labels[4], &collection_font_12, "上返回 · 下换角色", 120, 316, DIVE_ALIGN_CENTER, 0, UI_INK, 255);
    full |= !s_jump_valid || adv_ui_capturing() || game->character != s_previous.character;
    if (full) jump_rect(game, ms, 0, 0, 239, 319, labels, 5);
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
        jump_rect(game, ms, min(x0, a0), min(y0, b0), max(x1, a1), max(y1, b1), labels, 5);
        if (game->score != s_previous.score || game->best != s_previous.best || game->next_skin != s_previous.next_skin || game->next_size != s_previous.next_size)
            jump_rect(game, ms, 0, 0, 239, 82, labels, 5);
        if ((game->phase == JUMP_OVER) != (s_previous.phase == JUMP_OVER))
            jump_rect(game, ms, 0, 287, 239, 319, labels, 5);
        if (nabo_jump_charging(game) || nabo_jump_charging(&s_previous))
            jump_rect(game, ms, 30, 281, 210, 286, labels, 5);
    }
    s_previous = *game; s_previous_ms = ms; s_jump_valid = true; adv_ui_capture_done();
}
