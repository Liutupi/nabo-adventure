// Host shim for test_adv_renderer.py: the production adventure screens and the legacy jump page
// render into an emulated 240x320 panel.
#include <stdint.h>
#include <string.h>
#include "adv_gfx.h"
#include "adv_model.h"
#include "adv_post.h"
#include "adv_night.h"
#include "adv_climb.h"
#include "adv_ski.h"
#include "adv_sky.h"
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
    // V2 scenes from the real rules: 0 walk, 1 run with a group ahead, 2 swing catching, 3 moth + gold,
    // 4 low light with a root, 5 owl ring, 6 burst, 7 event banner, 8 title, 9 ready, 10 pause, 11 end,
    // 12 result record, 13 max result, 14 dense swarm (op budget).
    model.phase=ADV_PLAY;adv_night_t *p=model.game;adv_night_start(p,1234);
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
    if(which==12||which==13){model.phase=ADV_RESULT;p->score=which==13?UINT32_MAX:1268;p->caught=412;p->max_combo=57;p->bursts=3;p->last_loss=NIGHT_LOSS_OWL;model.best[4]=p->score;model.record=which==12;model.test=false;}
}

// CLIMB scenes: 0 idle, 1 switch mid-air, 2 charging, 3 jump, 4 slide after a hit, 5 fragile/ice/canteen,
// 6 rock warning + falling rocks, 7 snow zone, 8 title, 9 ready, 10 pause, 11 end, 12 result record, 13 max result,
// 14 milestone cheer, 15 cold zone.
void host_climb_case(int which)
{
    if(model.in_session&&model.station!=5)adv_event(&model,ADV_BTN_UP,ADV_EV_DOUBLE);
    if(!model.in_session){model.test=true;model.page=ADV_PAGE_MAP;adv_test_open(&model,5);}
    model.phase=ADV_PLAY;adv_climb_t *p=model.game;adv_climb_start(p,1234);p->tick=10;p->rock_next=100000;
    adv_input_t none={0},down={.ok_down=1,.ok_held=1},held={.ok_held=1},up={.ok_up=1};
    if(which==1){adv_climb_step(p,&down);adv_climb_step(p,&up);for(int i=0;i<12;i++)adv_climb_step(p,&none);}
    if(which==2){adv_climb_step(p,&down);for(int i=0;i<26;i++)adv_climb_step(p,&held);}
    if(which==3){adv_climb_step(p,&down);for(int i=0;i<20;i++)adv_climb_step(p,&held);adv_climb_step(p,&up);for(int i=0;i<14;i++)adv_climb_step(p,&none);}
    if(which==4){p->row=3;p->score=8;p->rocks[0]=(adv_climb_rock_t){1,0,3*ADV_CLIMB_ROW+20};adv_climb_step(p,&none);for(int i=0;i<10;i++)adv_climb_step(p,&none);}
    if(which==5){p->row=2;p->side=1;p->grid[2]=CLIMB_NORMAL|(CLIMB_ICE<<2);p->grid[3]=CLIMB_FRAGILE|(CLIMB_NORMAL<<2)|(1<<5);
        p->grid[4]=CLIMB_ICE|(CLIMB_FRAGILE<<2)|(1<<4);p->res=200;}
    if(which==6){p->score=40;p->rocks[0]=(adv_climb_rock_t){1,0,14*ADV_CLIMB_ROW};p->rocks[1]=(adv_climb_rock_t){1,1,3*ADV_CLIMB_ROW};
        p->rocks[2]=(adv_climb_rock_t){1,0,4*ADV_CLIMB_ROW};p->rocks[3]=(adv_climb_rock_t){1,1,12*ADV_CLIMB_ROW};}
    if(which==7||which==15){int row=which==7?240:150;
        for(int r=row-10;r<=row+12;r++){p->gen_top=r;p->grid[r%ADV_CLIMB_RING]=(uint8_t)(r%3==0?CLIMB_NORMAL|(CLIMB_ICE<<2):r%3==1?CLIMB_NORMAL:CLIMB_ICE<<2);}
        p->row=row;p->score=(uint32_t)row;p->side=0;}
    if(which==8)model.phase=ADV_TITLE;
    if(which==9){model.phase=ADV_READY;model.t=120;}
    if(which==10)model.phase=ADV_PAUSE;
    if(which==11){model.phase=ADV_END;model.t=60;p->res=0;p->over=1;}
    if(which==12||which==13){model.phase=ADV_RESULT;p->score=which==13?UINT32_MAX:186;model.best[5]=p->score;model.record=which==12;model.test=false;}
    if(which==14){p->row=50;p->score=50;p->cheer=30;p->feedback=60;p->message=CLIMB_MSG_MILESTONE;
        for(int r=40;r<=62;r++){p->gen_top=r;p->grid[r%ADV_CLIMB_RING]=CLIMB_NORMAL|(CLIMB_NORMAL<<2);}}
}

static void *late_open(int station)
{
    if(model.in_session&&model.station!=station)adv_event(&model,ADV_BTN_UP,ADV_EV_DOUBLE);
    if(!model.in_session){model.test=true;model.page=ADV_PAGE_MAP;adv_test_open(&model,station);}
    model.phase=ADV_PLAY;return model.game;
}
static void late_phase(int which,int station,uint32_t score,int *res,int *over,uint32_t *pscore)
{
    if(which==8)model.phase=ADV_TITLE;
    if(which==9){model.phase=ADV_READY;model.t=120;}
    if(which==10)model.phase=ADV_PAUSE;
    if(which==11){model.phase=ADV_END;model.t=60;*res=0;*over=1;}
    if(which==12||which==13){model.phase=ADV_RESULT;*pscore=which==13?UINT32_MAX:score;model.best[station]=*pscore;model.record=which==12;model.test=false;}
}
// SKI: 0 straight, 1 lean, 2 jump, 3 tree fall, 4 bump, 5 dense course, 6 gate pass, 7 cocoa, 8.. phases.
void host_ski_case(int which)
{
    adv_ski_t *p=late_open(6);adv_ski_start(p,4321);
    adv_input_t none={0},right={.down_held=1},jump={.ok_down=1,.ok_held=1};
    for(int i=0;i<90;i++)adv_ski_step(p,&none);
    if(which==1)for(int i=0;i<16;i++)adv_ski_step(p,&right);
    if(which==2){adv_ski_step(p,&jump);for(int i=0;i<14;i++)adv_ski_step(p,&none);}
    if(which==3||which==4){p->fall=which==3?30:12;p->message=which==3?SKI_MSG_TREE:SKI_MSG_BUMP;p->feedback=50;p->res=which==3?600:820;}
    if(which==5)for(int i=0;i<ADV_SKI_CAP;i++)p->objs[i]=(adv_ski_obj_t){1+i%6,30+(i*53)%180,p->pos+10+i*22,0};
    if(which==6){p->score=12;p->message=SKI_MSG_PASS;p->feedback=40;}
    if(which==7){p->message=SKI_MSG_COCOA;p->feedback=40;p->objs[0]=(adv_ski_obj_t){SKI_CABIN,150,p->pos+60,0};}
    late_phase(which,6,31,&p->res,&p->over,&p->score);
}
// SKY: 0 drifting, 1 heating, 2 venting, 3 hit, 4 stamp, 5 dense sky, 6 low over treetops, 7 warm current.
void host_sky_case(int which)
{
    adv_sky_t *p=late_open(7);adv_sky_start(p,4321);
    adv_input_t none={0},heat={.ok_held=1};
    for(int i=0;i<60;i++)adv_sky_step(p,&none);
    for(int i=0;i<ADV_SKY_CAP;i++)p->objs[i]=(adv_sky_obj_t){0};
    int d=p->dist>>4,a=p->alt>>4;
    if(which==1)for(int i=0;i<20;i++)adv_sky_step(p,&heat);
    if(which==2)p->vy=-32;
    if(which==3){p->invuln=ADV_SKY_INVULN-6;p->message=SKY_MSG_STORM;p->feedback=54;p->res=700;}
    if(which==4){p->message=SKY_MSG_STAMP;p->feedback=50;p->bonus=10;}
    if(which==5)for(int i=0;i<ADV_SKY_CAP;i++)p->objs[i]=(adv_sky_obj_t){1+i%4,d+40+i*24,a-100+(i*47)%260,i*9,0};
    if(which==6){p->alt=20*16;}
    if(which==7)p->objs[0]=(adv_sky_obj_t){SKY_WARM,d+110,a+20,0,0};
    if(which==0){p->objs[0]=(adv_sky_obj_t){SKY_STORM,d+120,a+150,0,0};p->objs[1]=(adv_sky_obj_t){SKY_BIRD,d+90,a+40,8,0};}
    late_phase(which,7,640,&p->res,&p->over,&p->score);
}
// SPACE: 0 falling, 1 main engine, 2 side thruster, 3 landed, 4 planting the flag, 5 crash, 6 fuel can + rock, 7 round 5.
void host_space_case(int which)
{
    adv_space_t *p=late_open(8);adv_space_start(p,4321);
    adv_input_t none={0},thrust={.ok_held=1},side={.down_held=1};
    for(int i=0;i<40;i++)adv_space_step(p,&none);
    if(which==1)for(int i=0;i<12;i++)adv_space_step(p,&thrust);
    if(which==2)for(int i=0;i<12;i++)adv_space_step(p,&side);
    if(which==3||which==4){p->x=p->pad*256;p->y=ADV_SPACE_GROUND*256;p->phase=SPACE_LANDED;p->timer=which==3?ADV_SPACE_LANDED-20:ADV_SPACE_LANDED-90;
        p->score=242;p->last_bonus=242;p->message=SPACE_MSG_LANDED;p->feedback=60;}
    if(which==5){p->y=ADV_SPACE_GROUND*256;p->phase=SPACE_CRASH;p->timer=40;p->message=SPACE_MSG_HARD;p->feedback=60;p->res=600;}
    if(which==6){int lx=p->x/256,ly=p->y/256;p->objs[0]=(adv_space_obj_t){SPACE_FUEL,(lx+70)*256,(ly+20)*256,-220};p->objs[1]=(adv_space_obj_t){SPACE_ROCK,(lx-70)*256,(ly+40)*256,200};}
    if(which==7){p->round=4;p->score=860;}
    late_phase(which,8,1210,&p->res,&p->over,&p->score);
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
