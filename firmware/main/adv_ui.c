// Adventure screens: panel output, shared widgets, cover, kiosk, settings and status.
// The map, passport and stamp pages live in adv_ui_map.c; game sessions in adv_ui_session.c.
#include "adv_ui.h"
#include "adv_ui_internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bsp_display.h"
#include "bsp_pins.h"
#include "collection_portrait.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"

#define ADV_VERSION "v0.1.0"

static ag_t *s_gfx;
static uint16_t *s_strip[2];
static bool s_capture;

// Shared with adv_ui_jump.c, which composes its own rows.
uint16_t *adv_ui_strip(void) { return s_strip[0]; }
bool adv_ui_ready(void) { return s_gfx != NULL; }
bool adv_ui_capturing(void) { return s_capture; }
void adv_ui_capture_done(void) { s_capture = false; }

void adv_ui_send(void *ctx, int x, int y, int w, int h, uint16_t *px)
{
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

bool adv_ui_open(void)
{
    if (s_gfx) return true;
    s_gfx = calloc(1, sizeof(*s_gfx));
    for (int i = 0; i < 2; i++)
        s_strip[i] = heap_caps_malloc(BSP_LCD_W * AG_STRIP * 2, MALLOC_CAP_DMA | MALLOC_CAP_INTERNAL);
    if (!s_gfx || !s_strip[0] || !s_strip[1]) {
        adv_ui_close();
        return false;
    }
    ag_init(s_gfx, s_strip[0], s_strip[1], adv_ui_send, NULL);
    return true;
}

void adv_ui_close(void)
{
    esp_lcd_panel_io_tx_param(bsp_display_io(), 0x00, NULL, 0);
    free(s_gfx);
    s_gfx = NULL;
    for (int i = 0; i < 2; i++) { free(s_strip[i]); s_strip[i] = NULL; }
    s_capture = false;
}

void adv_ui_invalidate(void)
{
    extern void adv_jump_invalidate(void);
    adv_jump_invalidate();
    if (s_gfx) ag_invalidate(s_gfx);
}

void adv_ui_capture(void) { adv_ui_invalidate(); s_capture = true; }
uint32_t adv_ui_bytes(void) { return s_gfx ? s_gfx->bytes : 0; }
bool adv_ui_overflow(void) { return s_gfx && s_gfx->overflow; }

// ---------- shared widgets ----------

void ui_header(ag_t *g, const char *title, const char *right)
{
    ag_rect(g, 0, 0, 240, 32, 0, UI_INK, 235, 0, 0);
    ag_text(g, &collection_font_16, title, 12, 22, NT_ALIGN_LEFT, UI_PAPER);
    if (right) ag_text(g, &collection_font_16, right, 228, 22, NT_ALIGN_RIGHT, UI_GOLD);
}

void ui_footer(ag_t *g, const char *hint)
{
    ag_rect(g, 0, 290, 240, 30, 0, UI_INK, 235, 0, 0);
    ag_text(g, &collection_font_12, hint, 120, 310, NT_ALIGN_CENTER, UI_PAPER);
}

void ui_stamps(ag_t *g, const adv_model_t *m, int station, int x, int cy, int r, int gap)
{
    uint32_t earned = adv_earned(m);
    for (int tier = 0; tier < 3; tier++) {
        bool on = earned & adv_stamp_bit(station, tier);
        ag_circle(g, x + tier * gap, cy, r, ui_tier_color(tier), on ? 255 : 0, on ? UI_INK : UI_DIM, 1);
    }
}

int ui_stamp_count(const adv_model_t *m) { return __builtin_popcount(adv_earned(m)); }

// ---------- cover ----------

static void draw_cover(ag_t *g, const adv_model_t *m)
{
    ag_band(g, 0, 200, ag_rgb(28, 36, 86), ag_rgb(118, 120, 170));
    ag_band(g, 200, 120, ag_rgb(118, 120, 170), ag_rgb(244, 196, 150));
    ag_glow(g, 120, 196, 70, UI_GOLD);
    ag_text(g, &nabo_poster_font_28, "NABO", 120, 58, NT_ALIGN_CENTER, UI_WHITE);
    ag_text(g, &nabo_poster_font_28, "ADVENTURE", 120, 90, NT_ALIGN_CENTER, UI_GOLD);
    ag_text(g, &collection_font_18, "NABO 的冒险之旅", 120, 120, NT_ALIGN_CENTER, UI_PAPER);
    ag_circle(g, 120, 196, 54, UI_PAPER, 255, UI_INK, 3);
    ag_bitmap(g, collection_portrait, 120 - COLLECTION_PORTRAIT_W / 2, 196 - COLLECTION_PORTRAIT_H / 2,
              COLLECTION_PORTRAIT_W, COLLECTION_PORTRAIT_H);
    char line[32];
    snprintf(line, sizeof(line), "STAMPS %d/24", ui_stamp_count(m));
    ag_text(g, &nabo_mono_font_12, line, 120, 276, NT_ALIGN_CENTER, UI_INK);
    ag_rect(g, 60, 284, 120, 26, 13, UI_GOLD, 255, UI_INK, 2);
    ag_text(g, &collection_font_16, "按 OK 出发", 120, 302, NT_ALIGN_CENTER, UI_INK);
}

// ---------- kiosk ----------

static void draw_kiosk(ag_t *g, const adv_model_t *m)
{
    ag_band(g, 0, 320, ag_rgb(246, 226, 180), ag_rgb(232, 176, 120));
    char count[16];
    snprintf(count, sizeof(count), "章 %d/24", ui_stamp_count(m));
    ui_header(g, "护照亭", count);
    ag_text(g, &collection_font_18, "欢迎来到小镇护照亭", 120, 72, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_12, "盖过的章都收在冒险护照里", 120, 94, NT_ALIGN_CENTER, UI_INK);
    static const char *const items[] = {"冒险护照", "设置", "返回地图"};
    for (int i = 0; i < 3; i++) {
        bool on = i == m->kiosk;
        int y = 124 + i * 46;
        ag_rect(g, 30, y, 180, 36, 10, on ? UI_GOLD : UI_PAPER, 255, UI_INK, on ? 2 : 1);
        ag_text(g, &collection_font_18, items[i], 120, y + 25, NT_ALIGN_CENTER, UI_INK);
    }
    ui_footer(g, "上/下选择 · OK确认 · 长按上返回");
}

// ---------- settings and status (layout of the NABO games collection) ----------

static void draw_settings(ag_t *g, const adv_model_t *m)
{
    const cg_model_t *c = &m->cfg;
    ag_band(g, 0, 320, UI_INK, ag_rgb(40, 34, 70));
    ag_text(g, &nabo_poster_font_28, "SETTINGS", 120, 39, NT_ALIGN_CENTER, UI_GOLD);
    ag_text(g, &collection_font_16, c->editing >= 0 ? "上/下调整 · OK保存" : "声音 · 显示 · 休眠", 120, 69,
            NT_ALIGN_CENTER, UI_PAPER);
    static const char *const names[] = {"音量", "亮度", "扬声器", "自动休眠", "设备状态", "返回"};
    for (int i = 0; i < 6; i++) {
        bool on = i == c->settings_cursor;
        int y = 93 + 30 * i;
        ag_rect(g, 16, y, 208, 27, 5, on ? UI_GOLD : UI_INK, 255, 0x42ec, on ? 1 : 0);
        ag_text(g, &collection_font_18, names[i], 26, y + 21, NT_ALIGN_LEFT, on ? UI_INK : UI_PAPER);
        char value[24] = "";
        if (i == 0) snprintf(value, sizeof(value), "%d%%", c->settings.volume);
        if (i == 1) snprintf(value, sizeof(value), "%d%%", c->settings.brightness);
        if (i == 2) snprintf(value, sizeof(value), "%s", c->settings.speaker ? "开" : "关");
        if (i == 3) {
            if (c->settings.sleep_seconds) snprintf(value, sizeof(value), "%d秒", c->settings.sleep_seconds);
            else snprintf(value, sizeof(value), "不休眠");
        }
        ag_text(g, &collection_font_16, value, 214, y + 20, NT_ALIGN_RIGHT, on ? UI_INK : UI_PAPER);
    }
    ag_text(g, &collection_font_16, c->editing >= 0 ? "长按上取消本次调整" : "长按上返回护照亭", 120, 305,
            NT_ALIGN_CENTER, UI_PAPER);
}

static void draw_status(ag_t *g, int battery, int mv)
{
    char value[48];
    ag_band(g, 0, 320, UI_INK, ag_rgb(40, 34, 70));
    ag_text(g, &nabo_poster_font_28, "STATUS", 120, 39, NT_ALIGN_CENTER, UI_GOLD);
    ag_text(g, &collection_font_18, "NABO 的冒险之旅", 120, 94, NT_ALIGN_CENTER, UI_PAPER);
    ag_text(g, &nabo_mono_font_12, ADV_VERSION, 120, 119, NT_ALIGN_CENTER, UI_GOLD);
    snprintf(value, sizeof(value), battery >= 0 ? "电量 %d%%" : "电量暂不可用", battery);
    ag_text(g, &collection_font_18, value, 120, 157, NT_ALIGN_CENTER, UI_PAPER);
    snprintf(value, sizeof(value), mv >= 0 ? "%d mV" : "-- mV", mv);
    ag_text(g, &nabo_mono_font_12, value, 120, 182, NT_ALIGN_CENTER, UI_GOLD);
    ag_text(g, &collection_font_16, "无需配网和激活", 120, 223, NT_ALIGN_CENTER, UI_PAPER);
    ag_text(g, &collection_font_16, "所有游戏均可离线玩", 120, 251, NT_ALIGN_CENTER, UI_PAPER);
    ag_text(g, &collection_font_16, "按任意键返回设置", 120, 305, NT_ALIGN_CENTER, UI_PAPER);
}

// ---------- dispatch ----------

void adv_ui_draw(const adv_model_t *m, uint32_t ms, int battery, int mv)
{
    (void)ms;
    if (!s_gfx) return;
    ag_t *g = s_gfx;
    switch (m->page) {
    case ADV_PAGE_COVER: ag_begin(g, UI_SCENE_COVER); draw_cover(g, m); break;
    case ADV_PAGE_MAP: ag_begin(g, UI_SCENE_MAP); ui_draw_map(g, m); break;
    case ADV_PAGE_KIOSK: ag_begin(g, UI_SCENE_KIOSK); draw_kiosk(g, m); break;
    case ADV_PAGE_PASSPORT: ag_begin(g, UI_SCENE_PASSPORT); ui_draw_passport(g, m); break;
    case ADV_PAGE_SETTINGS:
        if (m->cfg.page == CG_STATUS) { ag_begin(g, UI_SCENE_STATUS); draw_status(g, battery, mv); }
        else { ag_begin(g, UI_SCENE_SETTINGS); draw_settings(g, m); }
        break;
    case ADV_PAGE_STAMP: ag_begin(g, UI_SCENE_STAMP); ui_draw_stamp(g, m); break;
    case ADV_PAGE_SESSION: ui_draw_session(g, m); break;
    default: return;   // legacy games draw themselves
    }
    ag_flush(g);
    s_capture = false;
}
