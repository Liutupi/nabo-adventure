// Host shim for test_adv_renderer.py: the production adventure screens and the legacy jump page
// render into an emulated 240x320 panel.
#include <stdint.h>
#include <string.h>
#include "adv_gfx.h"
#include "adv_model.h"
#include "adv_post.h"
#include "adv_night.h"
#include "adv_ui.h"
#include "adv_ui_art.h"
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

// Distinct colored pixels verify the production stripe rotation's handedness.
int host_rotation_patch(void)
{
    extern void adv_ui_send(void *,int,int,int,int,uint16_t *);
    uint16_t source[6],before[6];
    for(int i=0;i<6;i++)source[i]=__builtin_bswap16((uint16_t)(0x1001+i));
    memcpy(before,source,sizeof(source));adv_ui_send(NULL,7,9,2,3,source);
    return memcmp(before,source,sizeof(source))==0;
}

static uint16_t viewport_pixels[320*320];
static int viewport_bad,viewport_width,viewport_height;
static void viewport_send(void *ctx,int x,int y,int w,int h,uint16_t *px)
{
    (void)ctx;
    if(x<0||y<0||x+w>viewport_width||y+h>viewport_height||w>320||h>AG_STRIP){viewport_bad=1;return;}
    for(int r=0;r<h;r++)for(int c=0;c<w;c++)viewport_pixels[(y+r)*320+x+c]=__builtin_bswap16(px[r*w+c]);
}
int host_viewport_edges(void)
{
    static ag_t gfx;static uint16_t strips[2][AG_MAX_W*AG_STRIP];
    ag_init(&gfx,strips[0],strips[1],viewport_send,NULL);
    if(!ag_viewport(&gfx,320,240)||ag_viewport(&gfx,321,240)||ag_viewport(&gfx,0,240))return 0;
    viewport_bad=0;viewport_width=320;viewport_height=240;
    for(unsigned i=0;i<sizeof(viewport_pixels)/sizeof(*viewport_pixels);i++)viewport_pixels[i]=0x2468;
    ag_begin(&gfx,90);ag_rect(&gfx,0,0,320,240,0,0x1357,255,0,0);ag_rect(&gfx,319,239,4,4,0,0xffff,255,0,0);ag_flush(&gfx);
    if(viewport_bad||gfx.bytes!=153600||viewport_pixels[239*320+319]!=0xffff||viewport_pixels[240*320]!=0x2468)return 0;
    ag_begin(&gfx,90);ag_rect(&gfx,0,0,320,240,0,0x1357,255,0,0);ag_rect(&gfx,319,239,4,4,0,0,255,0,0);ag_flush(&gfx);
    if(viewport_bad||viewport_pixels[239*320+319]||gfx.bytes!=2)return 0;
    if(!ag_viewport(&gfx,240,320))return 0;
    viewport_width=240;viewport_height=320;ag_begin(&gfx,90);ag_rect(&gfx,0,0,240,320,0,0x3579,255,0,0);ag_flush(&gfx);
    return !viewport_bad&&gfx.bytes==153600&&viewport_pixels[319*320+239]==0x3579;
}

void host_post_case(int which)
{
    if(model.in_session&&model.station!=3)adv_event(&model,ADV_BTN_UP,ADV_EV_DOUBLE);
    if(!model.in_session){model.test=true;model.page=ADV_PAGE_MAP;adv_test_open(&model,3);}
    model.phase=ADV_PLAY;adv_post_t *p=model.game;adv_post_start(p,1234);
    p->tick=10;p->distance=600;p->next_fork=p->next_coal=p->next_animal=10000;
    if(which==1){p->whistle=1;p->hold=ADV_POST_HOLD+10;}
    if(which==2){p->lane=0;p->y=ADV_POST_UPPER;p->hit=24;}
    if(which==3)p->delivered=50;
    if(which==4)p->delivered=20;
    if(which==5){p->lane=0;p->y=172;p->transition=40;p->events[0]=(adv_post_event_t){POST_FORK,110*60,0,0,1,0};}
    if(which==6){
        p->remaining=5;p->mail[3]=3;p->mail[4]=1;
        const adv_post_event_t events[]={
            {POST_FORK,50*60,0,0,0,0},{POST_FORK,275*60,0,0,0,0},
            {POST_STATION,200*60,0,0,0,0},{POST_STATION,170*60,1,2,0,0},
            {POST_ANIMAL,220*60,0,1,0,0},{POST_ANIMAL,180*60,1,0,0,0},
            {POST_COAL,235*60,1,0,0,0},{POST_COAL,130*60,0,0,0,0},
            {POST_COAL,10*60,1,0,0,0},{POST_DEPOT,225*60,1,0,0,0},
            {POST_STATION,-10*60,0,1,1,0},{POST_ANIMAL,250*60,0,0,2,36}};
        memcpy(p->events,events,sizeof(events));
    }
    if(which==7)p->events[0]=(adv_post_event_t){POST_STATION,ADV_POST_MAIL_X,p->lane,p->mail[0],0,0};
    if(which==8){p->miss_reason=2;p->feedback=90;}
    if(which>=9&&which<=12) {
        int lane=which==10?1:0;
        if(which==10){p->lane=p->choice=0;p->y=ADV_POST_UPPER;}
        if(which==12)p->choice=0;
        p->events[0]=(adv_post_event_t){POST_FORK,(which==11?90:240)*60,0,0,which==11,0};
        p->events[1]=(adv_post_event_t){POST_STATION,(which==11?190:340)*60,lane,p->mail[0],0,0};
    }
}

void host_night_case(int which)
{
    if(model.in_session&&model.station!=4)adv_event(&model,ADV_BTN_UP,ADV_EV_DOUBLE);
    if(!model.in_session){model.test=true;model.page=ADV_PAGE_MAP;adv_test_open(&model,4);}
    model.phase=ADV_PLAY;adv_night_t *p=model.game;adv_night_start(p,1234);p->next=10000;p->tick=10;
    if(which==1){adv_input_t input={.up_down=1};adv_night_step(p,&input);}
    if(which==2||which==3)p->bugs[0]=(adv_night_bug_t){which==2?NIGHT_FIREFLY:NIGHT_MOTH,(p->x+ADV_NIGHT_JAR_DX)*60,ADV_NIGHT_JAR_Y,1,16,0};
    if(which>=4&&which<=6){p->cast=20;p->feedback=60;p->message=which-3;p->score=6;p->caught_x=130;p->caught_y=227;if(which==5)p->good=60;if(which==6){p->bad=60;p->res=200;}}
    if(which==7)for(int i=0;i<ADV_NIGHT_CAP;i++)p->bugs[i]=(adv_night_bug_t){i%2+1,(20+i*28)*60,217+i%3*10,1,i*7,i*3};
    if(which==8)model.phase=ADV_TITLE;
    if(which==9){model.phase=ADV_READY;model.t=120;}
    if(which==10)model.phase=ADV_PAUSE;
    if(which==11){model.phase=ADV_END;model.t=60;p->res=0;p->over=1;}
    if(which>=12){model.phase=ADV_RESULT;p->score=which==13?UINT32_MAX:68;model.best[4]=p->score;model.record=which==12;model.test=false;}
}

void host_post_station_at(int lane,int x)
{
    host_post_case(0);adv_post_t *p=model.game;
    p->events[0]=(adv_post_event_t){POST_STATION,x*60,lane,p->mail[0],0,0};
    adv_ui_invalidate();
}

// Draw the native station alone on a sentinel background. The test compares
// every opaque station/mail pixel against the complete production scene.
void host_post_station_reference(int lane,int x)
{
    extern void adv_ui_send(void *,int,int,int,int,uint16_t *);
    static ag_t gfx;static uint16_t strips[2][AG_MAX_W*AG_STRIP];
    ag_init(&gfx,strips[0],strips[1],adv_ui_send,NULL);ag_viewport(&gfx,320,240);
    ag_begin(&gfx,99);ag_rect(&gfx,0,0,320,240,0,0xf81f,255,0,0);
    int y=lane?ADV_POST_LOWER:ADV_POST_UPPER;
    ui_art_tint(&gfx,"game/post/props/station-platform-mask",x-40,y-66,0xcae6);
    ui_art(&gfx,"game/post/props/envelope-red",0,x-16,y-64);ag_flush(&gfx);
}

void host_post_practice_case(int lesson)
{
    host_post_case(0);adv_post_t *p=model.game;adv_post_start_practice(p,42);
    adv_input_t in={.up_down=1};
    if(lesson>0)adv_post_step(p,&in);
    if(lesson>1){in=(adv_input_t){0};for(int i=0;i<240;i++)adv_post_step(p,&in);}
    if(lesson>2){in=(adv_input_t){.ok_down=1,.ok_held=1};adv_post_step(p,&in);in=(adv_input_t){.ok_up=1};adv_post_step(p,&in);}
    if(lesson>3){in=(adv_input_t){.ok_down=1,.ok_held=1};adv_post_step(p,&in);in=(adv_input_t){.ok_held=1};for(int i=0;i<60;i++)adv_post_step(p,&in);}
    if(lesson>4){in=(adv_input_t){.ok_up=1};adv_post_step(p,&in);}
}

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
    static uint16_t strips[2][AG_MAX_W * AG_STRIP];
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
    static uint16_t strips[2][AG_MAX_W * AG_STRIP];
    ag_init(&gfx, strips[0], strips[1], bitmap_send, NULL);
    ag_begin(&gfx, 1);
    ag_band(&gfx, 0, 320, top, bottom);
    ag_flush(&gfx);
}
