// Host shim for test_adv_renderer.py: the production adventure screens and the legacy jump page
// render into an emulated 240x320 panel.
#include <stdint.h>
#include <string.h>
#include "adv_gfx.h"
#include "adv_model.h"
#include "adv_ui.h"
#include "adv_ui_animation.h"
#include "nabo_jump_model.h"

static uint16_t pixels[240 * 320];
static nabo_jump_t game;
static uint32_t now;
static adv_model_t model;

void *bsp_display_panel(void) { return (void *)1; }
void *bsp_display_io(void) { return (void *)1; }
int esp_lcd_panel_io_tx_param(void *io, int cmd, const void *data, size_t n)
{
    (void)io; (void)cmd; (void)data; (void)n;
    return 0;
}
int esp_lcd_panel_draw_bitmap(void *panel, int x0, int y0, int x1, int y1, const void *data)
{
    (void)panel;
    const uint16_t *p = data;
    for (int y = y0; y < y1; y++)
        for (int x = x0; x < x1; x++) pixels[y * 240 + x] = __builtin_bswap16(*p++);
    return 0;
}

void host_snapshot(uint16_t *out) { memcpy(out, pixels, sizeof(pixels)); }
void host_close(void) { adv_ui_close(); adv_free(&model); }

// ---------- adventure ----------

int host_new(uint32_t seed, const uint32_t *best, uint32_t seen)
{
    adv_ui_close();
    adv_free(&model);
    if (!adv_ui_open()) return 0;
    cg_settings_t s = {70, 80, 300, true};
    adv_init(&model, seed, &s, best, seen);
    now = 1000;
    adv_ui_boot_end();
    adv_ui_draw(&model, now, 85, 4010);
    return 1;
}
int host_event(int button, int event) { return adv_event(&model, (adv_btn_t)button, (adv_ev_t)event); }
int host_steps(int n)
{
    int fx = 0;
    for (int i = 0; i < n; i++) fx |= adv_step(&model);
    return fx;
}
int host_legacy(uint32_t best) { return adv_legacy_done(&model, best); }
void host_draw(void) { adv_ui_draw(&model, now, 85, 4010); }
void host_draw_at(uint32_t ms) { now = ms; host_draw(); }
void host_boot_start(uint32_t ms) { now = ms; adv_ui_boot_begin(ms); }
void host_full(void) { adv_ui_invalidate(); adv_ui_draw(&model, now, 85, 4010); }
int host_overflow(void) { return adv_ui_overflow(); }
int host_page(void) { return model.page; }
int host_phase(void) { return model.in_session ? model.phase : -1; }
uint32_t host_bytes(void) { return adv_ui_bytes(); }

// ---------- legacy jump ----------

int host_jump_reset(int seed)
{
    adv_ui_close();
    if (!adv_ui_open()) return 0;
    now = 1000;
    nabo_jump_reset(&game, seed, 0);
    adv_jump_draw(&game, now, true);
    return 1;
}
void host_jump_tick(uint32_t delta, int edge)
{
    now += delta;
    if (edge == 1) nabo_jump_press(&game, now);
    if (edge == 2) nabo_jump_release(&game, now);
    nabo_jump_tick(&game, now);
    adv_jump_draw(&game, now, false);
}
void host_jump_full(void) { adv_jump_draw(&game, now, true); }
void host_jump_item(int size, int skin)
{
    game.next_size = size; game.next_skin = skin;
    adv_jump_draw(&game, now, true);
}
int host_jump_hold(void) { return (game.gap - 4) * 1000 / 150; }

// ---------- raw renderer ----------

static void bitmap_send(void *ctx, int x, int y, int w, int h, uint16_t *px)
{
    (void)ctx;
    esp_lcd_panel_draw_bitmap((void *)1, x, y, x + w, y + h, px);
}

void host_bitmap(int x, int y, int alternate, int full)
{
    static ag_t gfx;
    static uint16_t strips[2][240 * 8];
    static const uint16_t first[16] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
    static const uint16_t second[16] = {16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1};
    static int initialized;
    if (!initialized) {
        ag_init(&gfx, strips[0], strips[1], bitmap_send, NULL);
        initialized = 1;
    }
    if (full) ag_invalidate(&gfx);
    ag_begin(&gfx, 17);
    ag_rect(&gfx, 0, 0, 240, 320, 0, 0x1357, 255, 0, 0);
    ag_bitmap(&gfx, alternate ? second : first, x, y, 4, 4);
    ag_flush(&gfx);
}

// One full-screen gradient band (dither check).
void host_band(uint16_t top, uint16_t bottom)
{
    static ag_t gfx;
    static uint16_t strips[2][240 * 8];
    ag_init(&gfx, strips[0], strips[1], bitmap_send, NULL);
    ag_begin(&gfx, 1);
    ag_band(&gfx, 0, 320, top, bottom);
    ag_flush(&gfx);
}
