// Host shim for test_adv_renderer.py: the production adventure screens and the legacy jump page
// render into an emulated 240x320 panel.
#include <stdint.h>
#include <string.h>
#include "adv_gfx.h"
#include "adv_model.h"
#include "adv_post_v2.h"
#include "adv_night.h"
#include "adv_climb_v2.h"
#include "adv_ski.h"
#include "adv_sky_v2.h"
#include "adv_space.h"
#include "adv_ui.h"
#include "adv_ui_art.h"
#include "adv_ui_animation.h"
#include "nabo_jump_model.h"

static uint16_t pixels[240 * 320];
static nabo_jump_t game;
static uint32_t now;
static adv_model_t model;
static const uint16_t *pending_dma;
static int dma_x0,dma_y0,dma_x1,dma_y1,dma_faults;
static uint32_t dma_hash;
size_t host_caps_fail_size;
void host_fail_caps(size_t n){host_caps_fail_size=n;}
static uint32_t hash_pixels(const uint16_t *p,int count)
{uint32_t h=2166136261u;for(int i=0;i<count;i++)h=(h^p[i])*16777619u;return h;}
static void drain_dma(void)
{
    if(!pending_dma)return;
    if(hash_pixels(pending_dma,(dma_x1-dma_x0)*(dma_y1-dma_y0))!=dma_hash)dma_faults++;
    const uint16_t *p=pending_dma;
    for(int y=dma_y0;y<dma_y1;y++)for(int x=dma_x0;x<dma_x1;x++)pixels[y*240+x]=__builtin_bswap16(*p++);
    pending_dma=NULL;
}

void *bsp_display_panel(void) { return (void *)1; }
void *bsp_display_io(void) { return (void *)1; }
int esp_lcd_panel_io_tx_param(void *io, int cmd, const void *data, size_t n)
{
    (void)io; (void)cmd; (void)data; (void)n;
    drain_dma();
    return 0;
}
int esp_lcd_panel_draw_bitmap(void *panel, int x0, int y0, int x1, int y1, const void *data)
{
    (void)panel;
    if(pending_dma){dma_faults++;drain_dma();}
    pending_dma=data;dma_x0=x0;dma_y0=y0;dma_x1=x1;dma_y1=y1;
    dma_hash=hash_pixels(data,(x1-x0)*(y1-y0));
    return 0;
}

void host_snapshot(uint16_t *out) { memcpy(out, pixels, sizeof(pixels)); }
int host_dma_selftest(void)
{
    if(pending_dma)return 0;
    int before=dma_faults;uint16_t source[2]={0x1234,0xabcd};
    esp_lcd_panel_draw_bitmap((void *)1,0,0,2,1,source);source[0]^=1;
    esp_lcd_panel_io_tx_param((void *)1,0,NULL,0);
    int detected=dma_faults==before+1;dma_faults=before;return detected&&!pending_dma;
}
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
int host_overflow(void) { return adv_ui_overflow()||dma_faults||pending_dma!=NULL; }
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

static void *late_open(int station);
static void late_phase(int which,int station,uint32_t score,int *res,int *over,uint32_t *pscore);
void host_post_case(int which)
{
    adv_post_v2_t *p=late_open(3);adv_post_v2_start(p,1234);p->tick=10;p->nextEvent=100000;
    if(which==1){p->v=900;p->steaming=1;}
    if(which==2){p->stun=30;p->reds=1;p->fx[0]=(adv_post_v2_fx_t){POST_V2_FX_RED,196,136,160,6};}
    if(which==3)p->fx[0]=(adv_post_v2_fx_t){POST_V2_FX_NET,120,142,20,5};
    if(which==4){p->fx[0]=(adv_post_v2_fx_t){POST_V2_FX_PERFECT,120,142,40,15};p->score=40;p->delivered=2;}
    if(which==5){p->braking=1;p->v=400;p->zone=360;p->ev[0]=(adv_post_v2_event_t){POST_V2_T_LIMIT,180,360,180,0,0};}
    if(which==6)for(int i=0;i<POST_V2_EVENTS;i++)p->ev[i]=(adv_post_v2_event_t){1+i%5,20+i*20,80+i*10,60,1,0};
    if(which==7)p->ev[0]=(adv_post_v2_event_t){POST_V2_T_NET,120,0,0,0,0};
    if(which==8){p->bags=0;p->ev[0]=(adv_post_v2_event_t){POST_V2_T_NET,140,0,0,0,0};}
    if(which>=9&&which<=12)p->ev[0]=(adv_post_v2_event_t){POST_V2_T_CRANE,110+(which-9)*12,0,0,0,0};
}

void host_night_case(int which)
{
    model.phase=ADV_PLAY;adv_night_t *p=late_open(4);adv_night_start(p,1234);
    adv_input_t walk={0},run={.up_held=1},swing={.down_down=1};
    for(int i=0;i<200;i++)adv_night_step(p,which==1?&run:&walk);
    int32_t base=p->x>>8;
    if(which>=2&&which<=4){p->flies[0]=(adv_night_fly_t){1,(base+ADV_NIGHT_NET_DX+4)<<8,158,0,0,0,0};p->flies[1]=(adv_night_fly_t){1,(base+60)<<8,140,10,0,300,0};}
    if(which==2){adv_night_step(p,&swing);for(int i=0;i<5;i++)adv_night_step(p,&walk);p->combo=13;}
    if(which==3){p->flies[2]=(adv_night_fly_t){2,(base+120)<<8,150,0,0,0,0};p->moths[0]=(adv_night_moth_t){3,(base+136)<<8,146<<8,0,18,700};p->moths[1]=(adv_night_moth_t){3,(base+108)<<8,156<<8,128<<8,18,-700};}
    if(which==4){p->light=90000;p->roots[0]=(adv_night_root_t){base+40,14,1};p->roots[1]=(adv_night_root_t){base+150,14,1};}
    if(which==5){p->owls[0]=(adv_night_owl_t){(base+70)<<8,40,1};p->owls[1]=(adv_night_owl_t){(base+150)<<8,12,1};}
    if(which==6){p->meter=adv_night_meter_full(p);p->last_swing=(int32_t)p->tick;adv_night_step(p,&swing);for(int i=0;i<6;i++)adv_night_step(p,&walk);}
    if(which==7){p->event=NIGHT_EV_SWARM;p->event_t=400;p->fx[0]=(adv_night_fx_t){NIGHT_FX_EVENT,0,0,NIGHT_EV_SWARM,20};}
    if(which==14)for(int i=0;i<ADV_NIGHT_FLIES;i++)p->flies[i]=(adv_night_fly_t){1+(i%9==0),(base-100+i*9)<<8,110+i%7*10,20,i*1600,400,0};
    if(which==14)for(int i=0;i<ADV_NIGHT_FX;i++)p->fx[i]=(adv_night_fx_t){i==0?NIGHT_FX_EVENT:NIGHT_FX_FLY,base+i*30,150,i==0?1:3,10};
    if(which==14){p->owls[0]=(adv_night_owl_t){(base+90)<<8,20,1};p->owls[1]=(adv_night_owl_t){(base+200)<<8,50,1};for(int i=0;i<ADV_NIGHT_ROOTS;i++)p->roots[i]=(adv_night_root_t){base-60+i*60,12,1};for(int i=0;i<ADV_NIGHT_MOTHS;i++)p->moths[i]=(adv_night_moth_t){0,(base-60+i*30)<<8,120<<8,0,16,600};p->combo=30;p->meter=adv_night_meter_full(p);}
    if(which==8)model.phase=ADV_TITLE;
    if(which==9){model.phase=ADV_READY;model.t=120;}
    if(which==10)model.phase=ADV_PAUSE;
    if(which==11){model.phase=ADV_END;model.t=60;p->light=0;p->res=0;p->over=1;}
    if(which==12||which==13){model.phase=ADV_RESULT;p->score=which==13?UINT32_MAX:1268;p->caught=412;p->max_combo=57;p->bursts=3;p->last_loss=NIGHT_LOSS_OWL;model.best[4]=p->score;model.record=which==12;model.test=false;host_draw();now+=1400;}
}

// V2 scenes exercise both lanes, ice, traverses, rocks and every shell card.
void host_climb_case(int which)
{
    adv_climb_v2_t *p=late_open(5);adv_climb_v2_start(p,1234);p->tick=10;p->nextRock=100000;
    if(which==1||which==3){p->trav=7;p->row=3;}
    if(which==2){p->row=1;p->ice=8;p->iceSide=1;p->rows[1].h0=CLIMB_V2_H_ICE;}
    if(which==4){p->row=3;p->stun=12;p->slips=1;}
    if(which==5){p->row=2;p->lane=1;p->rows[2]=(adv_climb_v2_row_t){1,3,0,0};p->rows[3]=(adv_climb_v2_row_t){2,1,0,1};p->rows[4]=(adv_climb_v2_row_t){3,2,2,0};p->res=200;}
    if(which==6){p->rocks[0]=(adv_climb_v2_rock_t){1,0,30,-16,0};p->rocks[1]=(adv_climb_v2_rock_t){1,1,0,100,0};p->rocks[2]=(adv_climb_v2_rock_t){1,0,0,180,0};}
    if(which==7||which==15){p->row=which==7?240:150;p->genRow=p->row+15;for(int i=0;i<CLIMB_V2_ROWS;i++)p->rows[i]=(adv_climb_v2_row_t){1+i%3,3-i%3,i%3==0,0};}
    if(which==14){p->section=CLIMB_V2_SEC_NIGHT;p->combo=24;p->fx[0]=(adv_climb_v2_fx_t){CLIMB_V2_FX_SECTION,160,100,CLIMB_V2_SEC_NIGHT,15};}
    late_phase(which,5,286,&p->res,&p->over,&p->score);
}

static void *late_open(int station)
{
    if(model.in_session&&model.station!=station){
        if((model.station>=3&&model.station<=8)&&model.phase==ADV_PLAY)
            adv_event(&model,ADV_BTN_DOWN,ADV_EV_LONG);
        adv_event(&model,ADV_BTN_UP,ADV_EV_DOUBLE);
    }
    if(!model.in_session){model.test=true;model.page=ADV_PAGE_MAP;adv_test_open(&model,station);}
    model.phase=ADV_PLAY;model.seed++;model.best_before=0;return model.game;
}
static void late_phase(int which,int station,uint32_t score,int *res,int *over,uint32_t *pscore)
{
    if(which==8)model.phase=ADV_TITLE;
    if(which==9){model.phase=ADV_READY;model.t=120;}
    if(which==10)model.phase=ADV_PAUSE;
    if(which==11){model.phase=ADV_END;model.t=60;*res=0;*over=1;}
    if(which==12||which==13){model.phase=ADV_RESULT;*pscore=which==13?UINT32_MAX:score;model.best[station]=*pscore;model.record=which==12;model.test=false;host_draw();now+=1400;}
}
void host_post_session_case(int which)
{
    host_post_case(0);adv_post_v2_t *p=model.game;
    late_phase(which,3,512,&p->res,&p->over,&p->score);
}
// SKI V2: 0 straight, 1 carving, 2 hop, 3 tree crash, 4 kicker spin, 5 dense course, 6 gate pass + section,
// 7 avalanche close in fog, 8.. phases (title, ready, pause, end, result, max-record).
void host_ski_case(int which)
{
    adv_ski_t *p=late_open(6);adv_ski_start(p,4321);
    adv_input_t none={0},right={.up_held=1},jump={.down_down=1};
    for(int i=0;i<200;i++)adv_ski_step(p,&none);
    int top=p->y>>8;
    if(which==1)for(int i=0;i<20;i++)adv_ski_step(p,&right);
    if(which==2){adv_ski_step(p,&jump);for(int i=0;i<12;i++)adv_ski_step(p,&none);}
    if(which==3){p->objs[0]=(adv_ski_obj_t){SKI_TREE,p->x>>8,top+2,0};for(int i=0;i<8;i++)adv_ski_step(p,&none);}
    if(which==4){p->objs[0]=(adv_ski_obj_t){SKI_KICKER,p->x>>8,top+2,0};for(int i=0;i<4;i++)adv_ski_step(p,&none);adv_ski_step(p,&jump);for(int i=0;i<10;i++)adv_ski_step(p,&none);}
    if(which==5){top=p->y>>8;for(int i=0;i<ADV_SKI_OBJS;i++)p->objs[i]=(adv_ski_obj_t){1+i%8,24+(i*61)%276,top-60+i*10,0};p->combo=17;p->flow=400;
        for(int i=0;i<ADV_SKI_FX;i++)p->fx[i]=(adv_ski_fx_t){i==0?SKI_FX_SECTION:SKI_FX_GATE,60+i*40,62,i==0?SKI_SEC_PARK:50,10};}
    if(which==6){p->objs[0]=(adv_ski_obj_t){SKI_GATE_RED,p->x>>8,top+2,0};for(int i=0;i<3;i++)adv_ski_step(p,&none);p->fx[5]=(adv_ski_fx_t){SKI_FX_SECTION,160,100,SKI_SEC_SLALOM,8};}
    if(which==7){p->section=SKI_SEC_FOG;p->section_t=300;p->aval=p->y-(40<<8);adv_ski_step(p,&none);}
    late_phase(which,6,1268,&p->res,&p->over,&p->score);
}
// SKY V2: envelope, active wind layers, letters, houses, trees and storms.
void host_sky_case(int which)
{
    adv_sky_v2_t *p=late_open(7);adv_sky_v2_start(p,4321);p->nextGround=p->nextSky=100000;p->tick=100;
    if(which==1)p->heating=1;if(which==2)p->venting=1;if(which==3){p->invuln=64;p->res=700;}
    if(which==4){p->combo=4;p->score=340;p->letters[0]=(adv_sky_v2_letter_t){1,100*256,180*256,450,300,140};}
    if(which==5)for(int i=0;i<SKY_V2_OBJS;i++)p->objs[i]=(adv_sky_v2_obj_t){1+i%5,20+i*15,40+i*7,i%4,180+i,0,0};
    if(which==6){p->y=204*256;p->objs[0]=(adv_sky_v2_obj_t){SKY_V2_T_TREE,160,170,0,0,0,0};}
    if(which==7)p->objs[0]=(adv_sky_v2_obj_t){SKY_V2_T_TANK,180,140,0,0,0,0};
    if(which==0){p->objs[0]=(adv_sky_v2_obj_t){SKY_V2_T_HOUSE,200,185,1,0,0,0};p->objs[1]=(adv_sky_v2_obj_t){SKY_V2_T_STORM,250,45,0,190,0,0};}
    late_phase(which,7,1240,&p->res,&p->over,&p->score);
}
// SPACE V2: ignition, ascent, boost, touchdown, flag, lost, orbit objects, TLI; 8..13 shell phases; 14 dense, 15 separation, 16 upper sky, 17 landing.
void host_space_case(int which)
{
    adv_space_t *p=late_open(8);adv_space_start(p,4321);p->modeT=24;
    if(which!=0&&which<8){p->mode=SPACE_FLY;p->alt=600<<8;p->v=p->vTarget=640;}
    if(which==1){p->vx=450;p->ign=3;}
    if(which==2){p->alt=5800<<8;p->boostT=30;p->heat=780;p->sep=2;}
    if(which==3||which==4){p->mode=SPACE_ENDING;p->win=1;p->pad=160;p->lx=160<<8;p->ly=206<<8;p->modeT=which==3?16:66;p->score=6042;}
    if(which==5){p->mode=SPACE_LOST;p->modeT=50;p->invuln=60;p->hull=0;p->fx[0]=(adv_space_fx_t){SPACE_FX_HIT,160,156,1,6};}
    if(which==6){p->alt=9200<<8;p->sep=2;p->objs[0]=(adv_space_obj_t){SPACE_FUEL,220<<8,9250,0,0,0};p->objs[1]=(adv_space_obj_t){SPACE_ROCK,100<<8,9280,40,0,0};p->objs[2]=(adv_space_obj_t){SPACE_SAT,230<<8,9300,-90,0,0};}
    if(which==7){p->alt=15500<<8;p->sep=2;p->tli=1;p->tliT=75;p->tliHit=1;p->tliQ=2;}
    if(which>=8&&which<=13){p->mode=SPACE_FLY;p->alt=600<<8;late_phase(which,8,6042,&p->res,&p->over,&p->score);}
    if(which==14){p->mode=SPACE_FLY;p->alt=5200<<8;p->sep=2;p->boostT=20;p->combo=24;p->heat=840;
        for(int i=0;i<ADV_SPACE_OBJS;i++)p->objs[i]=(adv_space_obj_t){1+i%15,(24+(i*47)%272)<<8,5200+20+(i*31)%160,i%2?1:-1,i%15==3?8:0,0};
        for(int i=0;i<ADV_SPACE_FX;i++)p->fx[i]=(adv_space_fx_t){i==0?SPACE_FX_ZONE:SPACE_FX_STAR,80+i*30,100+i*10,i==0?2:100,10+i*3};
    }
    if(which==15){p->mode=SPACE_FLY;p->alt=4100<<8;p->sep=1;p->sepT=75;}
    if(which==16){p->mode=SPACE_FLY;p->alt=6800<<8;p->sep=2;p->boostT=30;}
    if(which==17){p->mode=SPACE_LAND;p->pad=210;p->lx=180<<8;p->ly=125<<8;p->lvy=380;p->boostT=6;}
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
int host_jump_score(void) { return (int)game.score; }

// ---------- raw renderer ----------

static void bitmap_send(void *ctx, int x, int y, int w, int h, uint16_t *px)
{
    (void)ctx;
    esp_lcd_panel_draw_bitmap((void *)1, x, y, x + w, y + h, px);
    esp_lcd_panel_io_tx_param((void *)1,0,NULL,0);
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
