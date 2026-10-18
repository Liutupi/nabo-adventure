#include "collection_ui.h"
#include "collection_portrait.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bsp_display.h"
#include "bsp_pins.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "nabo_dive_text.h"
#include "nabo_table_gfx.h"

LV_FONT_DECLARE(collection_font_12)
LV_FONT_DECLARE(collection_font_16)
LV_FONT_DECLARE(collection_font_18)
LV_FONT_DECLARE(nabo_poster_font_28)
LV_FONT_DECLARE(nabo_mono_font_12)

extern const uint8_t table_pack_start[] asm("_binary_table_sprites_bin_start");
extern const uint8_t table_pack_end[] asm("_binary_table_sprites_bin_end");
static nts_pack_t s_pack;
static ntg_t *s_gfx;
static uint16_t *s_strip[2];
static uint8_t *s_sprite;
static bool s_capture, s_jump_valid;
static nabo_jump_t s_previous;
static uint32_t s_previous_ms;
static const uint16_t INK = 0x1927, PAPER = 0xef3b, GOLD = 0xfd70, WHITE = 0xffff;

static void send_strip(void *ctx, int x, int y, int w, int h, uint16_t *px) {
    (void)ctx;
    if (s_capture) {
        const uint8_t *p = (const uint8_t *)px;
        for (int row = 0; row < h; row++) {
            printf("@cap %d %d %d ", y + row, x, w);
            for (int col = 0; col < w; col++) {
                int i = 2 * (row * w + col);
                printf("%02x%02x", p[i], p[i + 1]);
            }
            putchar('\n');
        }
    }
    esp_lcd_panel_draw_bitmap(bsp_display_panel(), x, y, x + w, y + h, px);
    // The caller may reuse this DMA strip as soon as we return.
    esp_lcd_panel_io_tx_param(bsp_display_io(), 0x00, NULL, 0);
}

bool cg_ui_open(void) {
    if (s_gfx) return true;
    if (!nts_open(&s_pack, table_pack_start, table_pack_end - table_pack_start)) return false;
    s_gfx = calloc(1, sizeof(*s_gfx));
    size_t need = nts_buffer_need(&s_pack);
    s_sprite = malloc(need);
    for (int i = 0; i < 2; i++)
        s_strip[i] = heap_caps_malloc(BSP_LCD_W * NTG_STRIP * 2, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    if (!s_gfx || !s_sprite || !s_strip[0] || !s_strip[1]) {
        cg_ui_close();
        return false;
    }
    ntg_init(s_gfx, &s_pack, s_sprite, need, s_strip[0], s_strip[1], send_strip, NULL);
    s_jump_valid = false;
    return true;
}

void cg_ui_close(void) {
    esp_lcd_panel_io_tx_param(bsp_display_io(), 0x00, NULL, 0);
    free(s_gfx); s_gfx = NULL;
    free(s_sprite); s_sprite = NULL;
    for (int i = 0; i < 2; i++) { free(s_strip[i]); s_strip[i] = NULL; }
    s_jump_valid = false;
    s_capture = false;
}

static void text(const lv_font_t *font, const char *s, int x, int baseline, nt_align_t align, uint16_t color) {
    ntg_text(s_gfx, font, s, x, baseline, align, color);
}

void cg_ui_invalidate(void) {
    s_jump_valid = false;
    if (s_gfx) ntg_invalidate(s_gfx);
}

void cg_ui_capture(void) { cg_ui_invalidate(); s_capture = true; }

void cg_ui_draw(const cg_model_t *m, uint32_t ms, int battery, int mv) {
    (void)ms;
    if (!s_gfx) return;
    ntg_begin(s_gfx, m->page);
    ntg_rect(s_gfx, 0, 0, 240, 320, 0, INK, 255, 0, 0);
    text(&nabo_poster_font_28, m->page == CG_HOME ? "NABO GAMES" : m->page == CG_STATUS ? "STATUS" : "SETTINGS",
         120, 39, NT_ALIGN_CENTER, GOLD);
    if (m->page == CG_HOME) {
        text(&collection_font_16, "游戏特辑 · 离线畅玩", 120, 62, NT_ALIGN_CENTER, PAPER);
        ntg_bitmap(s_gfx, collection_portrait, 79, 66, COLLECTION_PORTRAIT_W, COLLECTION_PORTRAIT_H);
        static const char *const names[] = {"深潜 DIVE", "NABO 牌桌", "NABO 跳一跳", "设置"};
        for (int i = 0; i < 4; i++) {
            bool active = i == m->home_cursor;
            ntg_rect(s_gfx, 20, 151 + i * 34, 200, 30, 6, active ? GOLD : 0x2229, 255, active ? WHITE : 0x42ec, 1);
            text(&collection_font_18, names[i], 120, 173 + i * 34, NT_ALIGN_CENTER, active ? INK : PAPER);
        }
        text(&collection_font_16, "上/下选择  OK进入", 120, 309, NT_ALIGN_CENTER, PAPER);
    } else if (m->page == CG_SETTINGS) {
        text(&collection_font_16, m->editing >= 0 ? "上/下调整 · OK保存" : "声音 · 显示 · 休眠", 120, 69, NT_ALIGN_CENTER, PAPER);
        static const char *const names[] = {"音量", "亮度", "扬声器", "自动休眠", "设备状态", "返回"};
        for (int i = 0; i < 6; i++) {
            bool active = i == m->settings_cursor;
            int y = 93 + 30 * i;
            ntg_rect(s_gfx, 16, y, 208, 27, 5, active ? GOLD : INK, 255, 0x42ec, active ? 1 : 0);
            text(&collection_font_18, names[i], 26, y + 21, NT_ALIGN_LEFT, active ? INK : PAPER);
            char value[24] = "";
            if (i == 0) snprintf(value, sizeof(value), "%d%%", m->settings.volume);
            if (i == 1) snprintf(value, sizeof(value), "%d%%", m->settings.brightness);
            if (i == 2) snprintf(value, sizeof(value), "%s", m->settings.speaker ? "开" : "关");
            if (i == 3) {
                if (m->settings.sleep_seconds) snprintf(value, sizeof(value), "%d秒", m->settings.sleep_seconds);
                else snprintf(value, sizeof(value), "不休眠");
            }
            text(&collection_font_16, value, 214, y + 20, NT_ALIGN_RIGHT, active ? INK : PAPER);
        }
        text(&collection_font_16, m->editing >= 0 ? "长按上取消本次调整" : "长按上返回游戏菜单", 120, 305, NT_ALIGN_CENTER, PAPER);
    } else {
        char value[48];
        text(&collection_font_18, "NABO 游戏特辑", 120, 94, NT_ALIGN_CENTER, PAPER);
        text(&nabo_mono_font_12, "v1.0.0", 120, 119, NT_ALIGN_CENTER, GOLD);
        snprintf(value, sizeof(value), battery >= 0 ? "电量 %d%%" : "电量暂不可用", battery);
        text(&collection_font_18, value, 120, 157, NT_ALIGN_CENTER, PAPER);
        snprintf(value, sizeof(value), mv >= 0 ? "%d mV" : "-- mV", mv);
        text(&nabo_mono_font_12, value, 120, 182, NT_ALIGN_CENTER, GOLD);
        text(&collection_font_16, "无需配网和激活", 120, 223, NT_ALIGN_CENTER, PAPER);
        text(&collection_font_16, "所有游戏均可离线玩", 120, 251, NT_ALIGN_CENTER, PAPER);
        text(&collection_font_16, "按任意键返回设置", 120, 305, NT_ALIGN_CENTER, PAPER);
    }
    ntg_flush(s_gfx);
    s_capture = false;
}

static int min(int a, int b) { return a < b ? a : b; }
static int max(int a, int b) { return a > b ? a : b; }

static void jump_rect(const nabo_jump_t *game, uint32_t ms, int x0, int y0, int x1, int y1,
                      dive_text_layout_t *labels, int n) {
    x0 = max(0, x0); x1 = min(239, x1); y0 = max(0, y0); y1 = min(319, y1);
    int w = x1 - x0 + 1;
    if (w <= 0 || y1 < y0) return;
    for (int y = y0; y <= y1; y += NTG_STRIP) {
        int rows = min(NTG_STRIP, y1 - y + 1);
        uint16_t *strip = s_strip[0];
        for (int row = 0; row < rows; row++) {
            uint16_t *line = strip + row * w;
            nabo_jump_draw_row(game, ms, y + row, x0, x1, line);
            for (int i = 0; i < n; i++) dive_text_row(&labels[i], y + row, x0, x1 + 1, line);
            for (int col = 0; col < w; col++) line[col] = __builtin_bswap16(line[col]);
        }
        send_strip(NULL, x0, y, w, rows, strip);
    }
}

void cg_jump_draw(const nabo_jump_t *game, uint32_t ms, bool full) {
    if (!s_gfx) return;
    static const char *const normal[] = {"NABO 医院", "NABO 靶心", "床旁书房", "功德木鱼", "NABO 播客", "值班咖啡"};
    static const char *const tiny[] = {"外带咖啡", "拿铁咖啡", "冰美式", "迷你电脑", "小音箱", "黑胶唱片"};
    char score[16], best[24], station[100];
    snprintf(score, sizeof(score), "%lu", (unsigned long)game->score);
    snprintf(best, sizeof(best), "BEST %lu", (unsigned long)game->best);
    if (game->next_size == JUMP_SIZE_CUP)
        snprintf(station, sizeof(station), "下一站 %s · 一人位", tiny[game->next_skin % 6]);
    else snprintf(station, sizeof(station), "下一站 %s%s", game->next_size == JUMP_SIZE_SMALL ? "迷你" : "", normal[game->next_skin % 6]);
    dive_text_layout_t labels[5];
    dive_text_layout(&labels[0], &nabo_poster_font_28, score, 16, 38, DIVE_ALIGN_LEFT, 0, INK, 255);
    dive_text_layout(&labels[1], &nabo_mono_font_12, best, 225, 31, DIVE_ALIGN_RIGHT, 0, INK, 255);
    dive_text_layout(&labels[2], &collection_font_16, station, 120, 77, DIVE_ALIGN_CENTER, 0, INK, 255);
    dive_text_layout(&labels[3], &collection_font_16, game->phase == JUMP_OVER ? "游戏结束 · OK再来一局" : "按住OK蓄力，松开起跳",
                     120, 303, DIVE_ALIGN_CENTER, 0, INK, 255);
    dive_text_layout(&labels[4], &collection_font_12, "上返回 · 下换角色", 120, 316, DIVE_ALIGN_CENTER, 0, INK, 255);
    full |= !s_jump_valid || s_capture || game->character != s_previous.character;
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
    s_previous = *game; s_previous_ms = ms; s_jump_valid = true; s_capture = false;
}
