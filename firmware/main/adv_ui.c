// Adventure screens: panel output, shared widgets, cover, kiosk, settings and status.
// The map, passport and stamp pages live in adv_ui_map.c; game sessions in adv_ui_session.c.
#include "adv_ui.h"
#include "adv_ui_internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bsp_display.h"
#include "bsp_pins.h"
#include "adv_ui_animation.h"
#include "adv_boot_motion.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"

#define ADV_VERSION "v0.1.0"

static ag_t *s_gfx;
static uint16_t *s_strip[2];
static bool s_capture;
static uint32_t s_millis;
uint32_t ui_millis(void) { return s_millis; }

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
    ui_map_reset();
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
    ui_art(g, "ui/bars/top", 0, 0, 0);
    ag_text_top(g, &collection_font_18, title, 20, 8, NT_ALIGN_LEFT, UI_WHITE);
    if (right) ag_text_top(g, &collection_font_12, right, 224, 11, NT_ALIGN_RIGHT, UI_WHITE);
}

void ui_footer(ag_t *g, const char *hint)
{
    ui_art(g, "ui/bars/bottom", 0, 0, 290);
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
    (void)m;
    uint32_t t = adv_ui_boot_initial() ? adv_ui_boot_elapsed(ui_millis()) : adv_boot_motion_duration();
    ui_art(g, "ui/cover-background-top", 0, 0, 0);
    ui_art(g, "ui/cover-background-bottom", 0, 0, 0);
    ui_art(g, "ui/wordmarks/collection", 0, 10, 12);
    if (adv_boot_motion_enabled()) {
        ui_art_frame_anchor(g, adv_boot_motion_asset_id(), adv_boot_motion_frame(t), 120, 266);
    } else {
        ui_art_anchor(g, "travel/welcome", 0, 120, 266);
    }
    ui_art(g, "ui/labels/boot-caption", 0, 10, 270);
    ui_art(g, "ui/labels/press-start", 0, 16, 284);
}

// ---------- kiosk ----------

static void draw_kiosk(ag_t *g, const adv_model_t *m)
{
    ui_paper(g);
    char count[16];
    snprintf(count, sizeof(count), "章 %d/24", ui_stamp_count(m));
    ui_header(g, "护照亭", count);
    ag_text(g, &collection_font_18, "欢迎来到小镇护照亭", 120, 72, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_12, "盖过的章都收在冒险护照里", 120, 94, NT_ALIGN_CENTER, UI_INK);
    static const char *const items[] = {"冒险护照", "设置", "返回地图"};
    for (int i = 0; i < 3; i++) {
        bool on = i == m->kiosk;
        int y = 124 + i * 46;
        ui_card(g, 30, y, 180, 36, on, false);
        ag_text_top(g, &collection_font_18, items[i], 120, y + 8, NT_ALIGN_CENTER, on ? UI_WHITE : UI_INK);
    }
    ui_footer(g, "上/下选择 · OK确认 · 长按上返回");
}

// ---------- settings and status (layout of the NABO games collection) ----------

static void draw_settings(ag_t *g, const adv_model_t *m)
{
    const cg_model_t *c = &m->cfg;
    ui_paper(g);
    ui_header(g, "设置", NULL);
    ag_text(g, &collection_font_16, c->editing >= 0 ? "上/下调整 · OK保存" : "声音 · 显示 · 休眠", 120, 69,
            NT_ALIGN_CENTER, UI_INK);
    static const char *const names[] = {"音量", "亮度", "扬声器", "自动休眠", "设备状态", "返回"};
    for (int i = 0; i < 6; i++) {
        bool on = i == c->settings_cursor;
        int y = 80 + 34 * i;
        ui_card(g, 16, y, 208, 34, on, false);
        ag_text_top(g, &collection_font_16, names[i], 26, y + 8, NT_ALIGN_LEFT, on ? UI_WHITE : UI_INK);
        char value[24] = "";
        if (i == 0) snprintf(value, sizeof(value), "%d%%", c->settings.volume);
        if (i == 1) snprintf(value, sizeof(value), "%d%%", c->settings.brightness);
        if (i == 2) snprintf(value, sizeof(value), "%s", c->settings.speaker ? "开" : "关");
        if (i == 3) {
            if (c->settings.sleep_seconds) snprintf(value, sizeof(value), "%d秒", c->settings.sleep_seconds);
            else snprintf(value, sizeof(value), "不休眠");
        }
        ag_text_top(g, &collection_font_16, value, 214, y + 8, NT_ALIGN_RIGHT, on ? UI_WHITE : UI_INK);
    }
    ui_footer(g, c->editing >= 0 ? "长按上取消本次调整" : "长按上返回护照亭");
}

static void draw_status(ag_t *g, int battery, int mv)
{
    char value[48];
    ui_paper(g);
    ui_header(g, "设备状态", NULL);
    ui_popup(g, 12, 56, 216, 220);
    ag_text(g, &collection_font_18, "NABO 的冒险之旅", 120, 94, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &nabo_mono_font_12, ADV_VERSION, 120, 119, NT_ALIGN_CENTER, UI_RED);
    snprintf(value, sizeof(value), battery >= 0 ? "电量 %d%%" : "电量暂不可用", battery);
    ag_text(g, &collection_font_18, value, 120, 157, NT_ALIGN_CENTER, UI_INK);
    snprintf(value, sizeof(value), mv >= 0 ? "%d mV" : "-- mV", mv);
    ag_text(g, &nabo_mono_font_12, value, 120, 182, NT_ALIGN_CENTER, UI_RED);
    ag_text(g, &collection_font_16, "无需配网和激活", 120, 223, NT_ALIGN_CENTER, UI_INK);
    ag_text(g, &collection_font_16, "所有游戏均可离线玩", 120, 251, NT_ALIGN_CENTER, UI_INK);
    ui_footer(g, "按任意键返回设置");
}

// ---------- dispatch ----------

void adv_ui_draw(const adv_model_t *m, uint32_t ms, int battery, int mv)
{
    s_millis = ms;
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
