// NIGHT uses native sleepwear/held-jar sprites; no whole-character transforms.
#include <stdio.h>
#include "adv_night.h"
#include "adv_ui_internal.h"

static void text(ag_t *g,const char *s,int x,int y,int size,nt_align_t align,uint16_t color)
{ag_text_top(g,size==18?&collection_font_18:size==16?&collection_font_16:&collection_font_12,s,x,y,align,color);}
static void actor(ag_t *g,const char *action,unsigned frame,int x,int y)
{char id[48];snprintf(id,sizeof(id),"night_a/%s",action);ui_art_frame_anchor(g,id,frame,x,y);}
static void background(ag_t *g)
{
    ag_band(g,0,320,ag_rgb(11,19,38),ag_rgb(25,56,47));
    for(int i=0;i<4;i++){char id[48];snprintf(id,sizeof(id),"game/night/tree_shadow_0%d",i);ui_art(g,id,0,i*64-16,68);}
    for(int i=0;i<8;i++){char id[48];snprintf(id,sizeof(id),"game/night/grass_0%d",i%4);ui_art(g,id,0,i*32,258);}
    static const int points[][2]={{22,54},{79,74},{191,58},{217,112},{112,116}};
    for(unsigned i=0;i<sizeof(points)/sizeof(*points);i++)ag_rect(g,points[i][0],points[i][1],1,1,0,ag_rgb(130,154,157),255,0,0);
}
static void footer(ag_t *g,const char *hint)
{ag_rect(g,0,292,240,28,0,UI_INK,255,0,0);text(g,hint,120,300,12,NT_ALIGN_CENTER,UI_WHITE);}
static void header(ag_t *g,const adv_night_t *p)
{
    ag_rect(g,0,0,240,32,0,UI_INK,255,0,0);text(g,"精神",8,9,12,NT_ALIGN_LEFT,UI_WHITE);
    ag_rect(g,40,11,128,10,0,0,0,UI_DIM,1);
    int w=p->res*124/1000;if(w>0)ag_rect(g,42,13,w,6,0,p->res<250?UI_RED:ag_rgb(138,172,134),255,0,0);
    char value[24];if(p->score>9999)snprintf(value,sizeof(value),"9999+");else snprintf(value,sizeof(value),"%u",(unsigned)p->score);
    text(g,value,232,5,18,NT_ALIGN_RIGHT,UI_GOLD);
}
static void play(ag_t *g,const adv_night_t *p)
{
    const char *action="seat_idle";unsigned frame=p->tick/5%8;
    if(p->cast){action="catch";frame=(ADV_NIGHT_CAST-p->cast)/5;}
    else if(p->good>0&&p->good<=30){action="lift_jar";frame=(30-p->good)/5;}
    else if(p->move){action=p->move_dir<0?"move_left":"move_right";frame=(ADV_NIGHT_MOVE-p->move)/5;}
    else if(p->res<250&&p->tick%240<30){action="yawn";frame=p->tick%240/5;}
    for(int i=0;i<3;i++)ag_rect(g,48+i*72-18,280,36,4,2,ag_rgb(82,107,101),100,0,0);
    actor(g,action,frame,p->x,ADV_NIGHT_FOOT);
    int target=adv_night_target(p);bool moth=target>=0&&p->bugs[target].type==NIGHT_MOTH;
    static const int dx[]={26,24,18,10,0,-10,-18,-24,-26,-24,-18,-10,0,10,18,24};
    static const int dy[]={0,8,14,18,20,18,14,8,0,-8,-14,-18,-20,-18,-14,-8};
    uint16_t ink=target<0?ag_rgb(83,103,93):moth?UI_RED:UI_GOLD;
    for(int i=0;i<16;i++)ag_rect(g,p->x+ADV_NIGHT_JAR_DX+dx[i],ADV_NIGHT_JAR_Y+dy[i],2,1,0,ink,200,0,0);
    for(int i=0;i<ADV_NIGHT_CAP;i++){
        const adv_night_bug_t *e=&p->bugs[i];if(!e->type)continue;
        int x=e->x/60,y=adv_night_object_y(e);
        if(e->type==NIGHT_FIREFLY){ag_glow(g,x,y,6+(e->age/6%2),UI_GOLD);ag_rect(g,x-1,y-1,3,3,0,ag_rgb(255,247,180),255,0,0);}
        else ui_art_anchor(g,"night_shared/moth",(uint32_t)e->age*1000/60,x,y+6);
    }
    if(p->good>48){int elapsed=60-p->good;ag_glow(g,p->caught_x+(p->x+ADV_NIGHT_JAR_DX-p->caught_x)*elapsed/12,p->caught_y+(ADV_NIGHT_JAR_Y-p->caught_y)*elapsed/12,7-elapsed/2,UI_GOLD);}
    static const char *const messages[]={"","没碰到，等进光圈再按","抓到了 +1 · 精神+60","这是飞蛾 · 精神-250"};
    const char *hint=p->feedback&&p->message>=1&&p->message<=3?messages[p->message]:target>=0?(moth?"飞蛾别抓！":"现在点OK举罐"):"上左 · 下右 · 等光点进圈";
    text(g,hint,120,174,12,NT_ALIGN_CENTER,moth?UI_RED:UI_GOLD);
    header(g,p);
}
static void title(ag_t *g,const adv_model_t *m)
{
    ui_header(g,"夜林",NULL);char best[32];if(m->best[4]>9999)snprintf(best,sizeof(best),"最佳9999+");else snprintf(best,sizeof(best),"最佳 %u",(unsigned)m->best[4]);
    text(g,best,224,11,12,NT_ALIGN_RIGHT,UI_WHITE);ui_art(g,"ui/wordmarks/night",0,20,40);
    actor(g,"seat_idle",ui_millis()/83%8,120,174);
    text(g,"上左挪 · 下右挪 · OK举罐",120,184,12,NT_ALIGN_CENTER,UI_WHITE);
    text(g,"等金色光点进罐口圈再抓",120,202,12,NT_ALIGN_CENTER,UI_GOLD);
    text(g,"萤火虫 +1  精神+60",120,222,12,NT_ALIGN_CENTER,UI_WHITE);
    text(g,"飞蛾扣250 · 精神空了结束",120,240,12,NT_ALIGN_CENTER,UI_WHITE);
    ui_stamps(g,m,4,70,266,6,50);
    for(int i=0;i<3;i++){char threshold[12];snprintf(threshold,sizeof(threshold),"%u",(unsigned)adv_threshold(4,i));text(g,threshold,70+i*50,274,12,NT_ALIGN_CENTER,UI_WHITE);}
    footer(g,"OK开始 · 双击上回地图");
}
void ui_draw_night_session(ag_t *g,const adv_model_t *m)
{
    static int prior_phase=-1;static uint32_t prior_seed,phase_started;
    if((int)m->phase!=prior_phase||m->seed!=prior_seed){prior_phase=m->phase;prior_seed=m->seed;phase_started=ui_millis();}
    ag_begin(g,m->phase==ADV_TITLE?UI_SCENE_TITLE:m->phase==ADV_RESULT?UI_SCENE_RESULT:UI_SCENE_PLAY);background(g);
    if(m->phase==ADV_TITLE){title(g,m);return;}
    const adv_night_t *p=m->game;
    if(m->phase==ADV_RESULT){
        header(g,p);text(g,"本局捕获",120,50,18,NT_ALIGN_CENTER,UI_WHITE);
        char n[24];if(p->score>9999)snprintf(n,sizeof(n),"9999+");else snprintf(n,sizeof(n),"%u",(unsigned)p->score);
        ui_number_tint(g,n,36,120,78,NT_ALIGN_CENTER,UI_GOLD);
        if(m->record)text(g,m->test?"测试不保存":"新纪录",120,128,12,NT_ALIGN_CENTER,UI_GOLD);
        unsigned frame=(ui_millis()-phase_started)/83;if(frame>7)frame=7;actor(g,"cheer",frame,120,216);
        if(m->best[4]>9999)snprintf(n,sizeof(n),"最佳9999+");else snprintf(n,sizeof(n),"最佳 %u",(unsigned)m->best[4]);
        text(g,n,120,238,16,NT_ALIGN_CENTER,UI_WHITE);ui_stamps(g,m,4,92,274,8,28);footer(g,"OK重玩 · 双击上回地图");return;
    }
    play(g,p);
    if(m->phase==ADV_READY){char n[12];snprintf(n,sizeof(n),"%d",(m->t+59)/60);ag_glow(g,120,124,34,UI_GOLD);ui_number(g,n,36,120,106,NT_ALIGN_CENTER);}
    else if(m->phase==ADV_PAUSE){
        ag_rect(g,18,80,204,138,8,UI_INK,255,UI_GOLD,1);text(g,"暂停",120,99,18,NT_ALIGN_CENTER,UI_WHITE);
        text(g,"OK继续",120,141,16,NT_ALIGN_CENTER,UI_GOLD);text(g,"下键重新开始",120,173,12,NT_ALIGN_CENTER,UI_WHITE);
    }else if(m->phase==ADV_END){ag_rect(g,42,114,156,44,8,UI_INK,255,UI_RED,1);text(g,"精神耗尽",120,125,18,NT_ALIGN_CENTER,UI_WHITE);}
    footer(g,"双击上回地图 · 长按上暂停");
}
