#include <stdint.h>
#include <string.h>
#include "collection_ui.h"
#include "nabo_jump_model.h"
#include "nabo_table_gfx.h"
static uint16_t pixels[240*320];
static nabo_jump_t game;
static uint32_t now;
static cg_model_t model;
void *bsp_display_panel(void) { return (void *)1; }
void *bsp_display_io(void) { return (void *)1; }
int esp_lcd_panel_io_tx_param(void *io,int cmd,const void *data,size_t n) {
    (void)io;(void)cmd;(void)data;(void)n;return 0;
}
int esp_lcd_panel_draw_bitmap(void *panel,int x0,int y0,int x1,int y1,const void *data) {
    (void)panel;
    const uint16_t *p=data;
    for(int y=y0;y<y1;y++)for(int x=x0;x<x1;x++) pixels[y*240+x]=__builtin_bswap16(*p++);
    return 0;
}
int host_show(int page,int cursor,int editing) {
    cg_ui_close();
    if(!cg_ui_open()) return 0;
    cg_settings_t settings={70,80,300,true};
    cg_init(&model,&settings);
    model.page=page;model.home_cursor=cursor;model.settings_cursor=cursor;model.editing=editing;
    cg_ui_draw(&model,1000,85,4010);
    return 1;
}
void host_snapshot(uint16_t *out) { memcpy(out,pixels,sizeof(pixels)); }
void host_menu_cursor(int cursor) {
    model.home_cursor=cursor;model.settings_cursor=cursor;
    cg_ui_draw(&model,1000,85,4010);
}
void host_menu_full(void) { cg_ui_invalidate();cg_ui_draw(&model,1000,85,4010); }
int host_jump_reset(int seed) {
    cg_ui_close();
    if(!cg_ui_open())return 0;
    now=1000;nabo_jump_reset(&game,seed,0);cg_jump_draw(&game,now,true);return 1;
}
void host_jump_tick(uint32_t delta,int edge) {
    now+=delta;
    if(edge==1)nabo_jump_press(&game,now);
    if(edge==2)nabo_jump_release(&game,now);
    nabo_jump_tick(&game,now);
    cg_jump_draw(&game,now,false);
}
void host_jump_full(void) { cg_jump_draw(&game,now,true); }
void host_jump_item(int size,int skin) {
    game.next_size=size;game.next_skin=skin;cg_jump_draw(&game,now,true);
}
int host_jump_hold(void) { return (game.gap-4)*1000/150; }
void host_close(void) { cg_ui_close(); }

static void bitmap_send(void *ctx, int x, int y, int w, int h, uint16_t *px) {
    (void)ctx;
    esp_lcd_panel_draw_bitmap((void *)1, x, y, x + w, y + h, px);
}

void host_bitmap(int x, int y, int alternate, int full) {
    static ntg_t gfx;
    static uint16_t strips[2][240*8];
    static const uint16_t first[16] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16};
    static const uint16_t second[16] = {16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1};
    static int initialized;
    if (!initialized) {
        ntg_init(&gfx, NULL, NULL, 0, strips[0], strips[1], bitmap_send, NULL);
        initialized = 1;
    }
    if (full) ntg_invalidate(&gfx);
    ntg_begin(&gfx, 17);
    ntg_rect(&gfx, 0, 0, 240, 320, 0, 0x1357, 255, 0, 0);
    ntg_bitmap(&gfx, alternate ? second : first, x, y, 4, 4);
    ntg_flush(&gfx);
}
