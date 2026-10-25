// Native sleepwear/jar art in320x240 clockwise landscape.
#include <stdio.h>
#include "adv_night.h"
#include "adv_ui_internal.h"

static const int POS[]={54,160,266};
static void text(ag_t *g,const char *s,int x,int y,int size,nt_align_t align,uint16_t color)
{ag_text_top(g,size==18?&collection_font_18:size==16?&collection_font_16:&collection_font_12,s,x,y,align,color);}
static void actor(ag_t *g,const char *action,unsigned frame,int x,int y)
{char id[48];snprintf(id,sizeof(id),"night_a/%s",action);ui_art_frame_anchor(g,id,frame,x,y);}
static void background(ag_t *g)
{
    ag_band(g,0,240,ag_rgb(11,19,38),ag_rgb(25,56,47));
    for(int i=0;i<4;i++){
        int x=8+i*100;ag_rect(g,x-4,60,8,145,0,ag_rgb(13,36,46),255,0,0);
        ag_circle(g,x,75,36,ag_rgb(14,41,49),255,0,0);ag_circle(g,x+14,95,28,ag_rgb(16,47,51),255,0,0);
        char id[48];snprintf(id,sizeof(id),"game/night/tree_shadow_0%d",i);ui_art(g,id,0,x-16,68);
    }
    for(int i=0;i<10;i++){char id[48];snprintf(id,sizeof(id),"game/night/grass_0%d",i%4);ui_art(g,id,0,i*32,190);}
    static const int stars[][2]={{22,54},{99,74},{221,58},{297,112},{152,96}};
    for(unsigned i=0;i<sizeof(stars)/sizeof(*stars);i++)ag_rect(g,stars[i][0],stars[i][1],1,1,0,ag_rgb(130,154,157),255,0,0);
}
static void footer(ag_t *g,const char *hint)
{ag_rect(g,0,220,320,20,0,UI_INK,255,0,0);text(g,hint,160,224,12,NT_ALIGN_CENTER,UI_WHITE);}
static void header(ag_t *g,const adv_night_t *p)
{
    ag_rect(g,0,0,320,32,0,UI_INK,255,0,0);text(g,"夜林",8,9,12,NT_ALIGN_LEFT,UI_WHITE);
    text(g,"精神",48,9,12,NT_ALIGN_LEFT,UI_WHITE);ag_rect(g,80,11,152,10,0,0,0,UI_DIM,1);
    int w=p->res*148/1000;if(w>0)ag_rect(g,82,13,w,6,0,p->res<250?UI_RED:ag_rgb(138,172,134),255,0,0);
    char n[24];if(p->score>9999)snprintf(n,sizeof(n),"9999+");else snprintf(n,sizeof(n),"%u",(unsigned)p->score);
    text(g,n,312,5,18,NT_ALIGN_RIGHT,UI_GOLD);
}
static void play(ag_t *g,const adv_night_t *p)
{
    int fly=-1;for(int i=0;i<ADV_NIGHT_CAP;i++)if(p->bugs[i].type==NIGHT_FIREFLY){fly=i;break;}
    for(int lane=0;lane<3;lane++){
        bool active=fly>=0&&p->bugs[fly].lane==lane;
        for(int j=-1;j<=1;j++)ag_circle(g,POS[lane]+ADV_NIGHT_JAR_DX+j*10,203,12,ag_rgb(29,65,55),255,0,0);
        if(active)ag_glow(g,POS[lane]+ADV_NIGHT_JAR_DX,210,24,UI_GOLD);
        ag_rect(g,POS[lane]-16,214,36,4,2,active?UI_GOLD:ag_rgb(82,107,101),160,0,0);
    }
    const char *action="seat_idle";unsigned frame=p->tick/5%8;
    if(p->cast){action="catch";frame=(ADV_NIGHT_CAST-p->cast)/5;}
    else if(p->good>0&&p->good<=30){action="lift_jar";frame=(30-p->good)/5;}
    else if(p->move){action=p->move_dir<0?"move_left":"move_right";frame=(ADV_NIGHT_MOVE-p->move)/5;}
    else if(p->res<250&&p->tick%240<30){action="yawn";frame=p->tick%240/5;}
    actor(g,action,frame,p->x,ADV_NIGHT_FOOT);
    int target=adv_night_target(p);bool moth=target>=0&&p->bugs[target].type==NIGHT_MOTH;
    static const int dx[]={26,24,18,10,0,-10,-18,-24,-26,-24,-18,-10,0,10,18,24};
    static const int dy[]={0,8,14,18,20,18,14,8,0,-8,-14,-18,-20,-18,-14,-8};
    uint16_t ink=target<0?ag_rgb(83,103,93):moth?UI_RED:UI_GOLD;
    for(int i=0;i<16;i++)ag_rect(g,p->x+ADV_NIGHT_JAR_DX+dx[i],ADV_NIGHT_JAR_Y+dy[i],2,1,0,ink,200,0,0);
    for(int i=0;i<ADV_NIGHT_CAP;i++){
        const adv_night_bug_t *e=&p->bugs[i];if(!e->type)continue;int x=e->x/60,y=adv_night_object_y(e);
        if(e->type==NIGHT_FIREFLY){
            ag_glow(g,x,y,6+(e->age/6%2),UI_GOLD);ag_rect(g,x-1,y-1,3,3,0,ag_rgb(255,247,180),255,0,0);
            int w=(36*(ADV_NIGHT_LIFE-e->age)+ADV_NIGHT_LIFE-1)/ADV_NIGHT_LIFE;
            if(w>0)ag_rect(g,POS[e->lane]+ADV_NIGHT_JAR_DX-18,132,w,3,0,UI_GOLD,255,0,0);
        }else ui_art_anchor(g,"night_shared/moth",(uint32_t)e->age*1000/60,x,y+6);
    }
    if(p->good>48){int t=60-p->good;ag_glow(g,p->caught_x+(p->x+ADV_NIGHT_JAR_DX-p->caught_x)*t/12,p->caught_y+(ADV_NIGHT_JAR_Y-p->caught_y)*t/12,7-t/2,UI_GOLD);}
    static const char *const messages[]={"","没抓到，去亮起的草丛","抓到了 +1 · 精神+60","这是飞蛾 · 精神-250"};
    char direction[64];snprintf(direction,sizeof(direction),"去%s草丛，过时会飞走",fly>=0?(const char *[]) {"左","中","右"}[p->bugs[fly].lane]:"");
    const char *hint=p->feedback&&p->message>=1&&p->message<=3?messages[p->message]:target>=0?(moth?"飞蛾别抓！":"现在按中键举罐"):fly>=0?direction:"留意下一簇亮起的草丛";
    text(g,hint,160,40,12,NT_ALIGN_CENTER,moth?UI_RED:UI_GOLD);header(g,p);
}
static void title(ag_t *g,const adv_model_t *m)
{
    ag_rect(g,0,0,320,32,0,UI_INK,255,0,0);text(g,"夜林",8,9,12,NT_ALIGN_LEFT,UI_WHITE);
    char best[32];if(m->best[4]>9999)snprintf(best,sizeof(best),"最佳9999+");else snprintf(best,sizeof(best),"最佳 %u",(unsigned)m->best[4]);
    text(g,best,312,9,12,NT_ALIGN_RIGHT,UI_WHITE);text(g,"三键朝下",160,9,12,NT_ALIGN_CENTER,UI_WHITE);ui_art(g,"ui/wordmarks/night",0,16,36);actor(g,"seat_idle",ui_millis()/83%8,266,116);
    text(g,"光点只在一簇草丛停留，过时飞走",160,128,12,NT_ALIGN_CENTER,UI_GOLD);
    text(g,"按住左/右移动 · 中键举罐",160,148,12,NT_ALIGN_CENTER,UI_WHITE);
    text(g,"抓到 +1 / 精神+60 · 飞蛾扣250",160,168,12,NT_ALIGN_CENTER,UI_WHITE);
    text(g,"精神耗尽结束 · 铜15 / 银35 / 金60",160,190,12,NT_ALIGN_CENTER,UI_WHITE);
    footer(g,"中键开始 · 长按中暂停 · 双击上返回");
}
void ui_draw_night_session(ag_t *g,const adv_model_t *m)
{
    static int prior_phase=-1;static uint32_t prior_seed,phase_started;
    if((int)m->phase!=prior_phase||m->seed!=prior_seed){prior_phase=m->phase;prior_seed=m->seed;phase_started=ui_millis();}
    ag_begin(g,m->phase==ADV_TITLE?UI_SCENE_TITLE:m->phase==ADV_RESULT?UI_SCENE_RESULT:UI_SCENE_PLAY);background(g);
    if(m->phase==ADV_TITLE){title(g,m);return;}
    const adv_night_t *p=m->game;
    if(m->phase==ADV_RESULT){
        header(g,p);text(g,"本局捕获",160,42,18,NT_ALIGN_CENTER,UI_WHITE);
        char n[24];if(p->score>9999)snprintf(n,sizeof(n),"9999+");else snprintf(n,sizeof(n),"%u",(unsigned)p->score);
        ui_number_tint(g,n,36,160,68,NT_ALIGN_CENTER,UI_GOLD);
        if(m->record)text(g,m->test?"测试不保存":"新纪录",250,140,12,NT_ALIGN_CENTER,UI_GOLD);
        unsigned frame=(ui_millis()-phase_started)/83;if(frame>7)frame=7;actor(g,"cheer",frame,160,188);
        if(m->best[4]>9999)snprintf(n,sizeof(n),"最佳9999+");else snprintf(n,sizeof(n),"最佳 %u",(unsigned)m->best[4]);
        text(g,n,160,199,12,NT_ALIGN_CENTER,UI_WHITE);footer(g,"中键重玩 · 双击上键回地图");return;
    }
    play(g,p);
    if(m->phase==ADV_READY){char n[12];snprintf(n,sizeof(n),"%d",(m->t+59)/60);ag_glow(g,160,104,34,UI_GOLD);ui_number(g,n,36,160,86,NT_ALIGN_CENTER);}
    else if(m->phase==ADV_PAUSE){
        ag_rect(g,56,65,208,124,8,UI_INK,255,UI_GOLD,1);text(g,"暂停",160,80,18,NT_ALIGN_CENTER,UI_WHITE);
        text(g,"中键继续",160,122,16,NT_ALIGN_CENTER,UI_GOLD);text(g,"左键重新开始",160,154,12,NT_ALIGN_CENTER,UI_WHITE);
    }else if(m->phase==ADV_END){ag_rect(g,82,80,156,44,8,UI_INK,255,UI_RED,1);text(g,"精神耗尽",160,91,18,NT_ALIGN_CENTER,UI_WHITE);}
    footer(g,"按住左右移动 · 长按中暂停 · 双击上返回");
}
