// POST's native 320x240 world, route signs and local practice prompts.
#include <stdio.h>
#include "adv_post.h"
#include "adv_ui_internal.h"

static const char *const COLORS[]={"red","blue","yellow","green"};
static const uint16_t INKS[]={0xcae6,0x43f3,0xd569,0x544b};
static void text(ag_t *g,const char *s,int x,int y,int size,nt_align_t align,uint16_t color)
{ag_text_top(g,size==16?&collection_font_16:&collection_font_12,s,x,y,align,color);}

static void mail(ag_t *g,int color,int x,int y)
{char id[64];snprintf(id,sizeof(id),"game/post/props/envelope-%s",COLORS[color&3]);ui_art(g,id,0,x,y);}

static void paint_fork(ag_t *g,int x)
{
    for(int j=0;j<6;j++)for(int direction=0;direction<2;direction++) {
        int yy=(direction?ADV_POST_LOWER-10:ADV_POST_UPPER-10)+(direction?-1:1)*j*14;
        ag_rect(g,x-60+j*20,yy,23,5,0,UI_INK,255,0,0);
    }
    ui_art(g,"game/post/tiles/track-fork",0,x-32,156);
}

static void events(ag_t *g,const adv_post_t *p)
{
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&p->events[i];if(!e->type)continue;
        int x=e->x/60,y=e->lane?ADV_POST_LOWER:ADV_POST_UPPER;
        if(e->type==POST_FORK)paint_fork(g,x);
        if(e->type==POST_STATION&&e->color<4) {
            ui_art_tint(g,"game/post/props/station-platform-mask",x-40,y-66,INKS[e->color]);
            mail(g,e->color,x-16,y-64);
        }
        if(e->type==POST_COAL&&!e->done)ui_art(g,"game/post/props/coal-pile",0,x-16,y-23);
        if(e->type==POST_ANIMAL&&e->done!=1)
            ui_art(g,e->color?"game/post/props/cow":"game/post/props/sheep",0,x-(e->color?24:20),y-(e->color?34:28)-(e->done==2?30:0));
        if(e->type==POST_DEPOT) {
            ag_rect(g,x-34,y-72,68,63,4,UI_INK,255,UI_WHITE,1);
            text(g,"车库",x,y-60,16,NT_ALIGN_CENTER,UI_WHITE);
        }
    }
}

static void train(ag_t *g,const adv_post_t *p)
{
    for(int k=0;k<p->remaining;k++) {
        int x=30-k*64;ui_art(g,"game/post/props/carriage",0,x-32,p->y-44);mail(g,p->mail[k],x-16,p->y-65);
    }
    int left=62,top=p->y-81,frame=(p->tick/5)%6;const char *action="idle";
    if(p->hit||p->miss){action="hit";int t=p->hit>p->miss?p->hit:p->miss;frame=(24-t)/5;}
    else if(p->whistle){action="whistle";frame=((p->hold-ADV_POST_HOLD)/5)%6;}
    else if(p->delivered){action=p->delivered>30?"throw":"delivered";frame=((p->delivered>30?60:30)-p->delivered)/5;}
    ui_art_crop(g,"post_props/wheel-cycle",(p->tick/5)%4,left,top,13,58,88,81);
    ui_art_crop(g,"game/post/props/locomotive-body",0,left,top,1,1,96,70);
    ui_art_crop(g,"post_props/whistle-cord",p->whistle?frame:0,left,top,6,5,19,51);
    char id[64];snprintf(id,sizeof(id),"post_a/%s",action);
    ui_art_frame_anchor(g,id,(unsigned)frame,left+25,top+49);
    ui_art_crop(g,"game/post/props/cab-foreground",0,left,top,8,49,44,63);
}

static void header(ag_t *g,const adv_post_t *p)
{
    ag_rect(g,0,0,320,32,0,UI_INK,255,0,0);text(g,p->practice?"练习":"蒸汽",8,9,12,NT_ALIGN_LEFT,UI_WHITE);
    ag_rect(g,36,10,66,10,0,0,0,UI_WHITE,1);
    int w=p->res*62/1000;if(w>0)ag_rect(g,38,12,w,6,0,p->res<250?UI_RED:ADV_ASSETS_UI_TEAL,255,0,0);
    text(g,p->remaining?"先送":p->practice?"已送":"补给",106,9,12,NT_ALIGN_LEFT,UI_WHITE);
    for(int k=0;k<p->remaining;k++)mail(g,p->mail[k],134+k*34,4);
    if(p->remaining)ag_rect(g,132,2,36,28,0,0,0,UI_GOLD,2);
    ag_rect(g,0,32,78,58,4,UI_INK,255,0,0);
    text(g,p->transition?"正在换轨":p->lane?"当前 下轨":"当前 上轨",8,36,12,NT_ALIGN_LEFT,UI_WHITE);
    text(g,p->choice?"预选 下轨":"预选 上轨",8,54,12,NT_ALIGN_LEFT,UI_WHITE);
    char score[32];
    if(p->practice)snprintf(score,sizeof(score),"练习 %d/3",p->lesson<2?1:p->lesson<3?2:3);
    else if(p->score>9999)snprintf(score,sizeof(score),"送达9999+");
    else snprintf(score,sizeof(score),"送达 %u封",(unsigned)p->score);
    text(g,score,8,74,12,NT_ALIGN_LEFT,UI_WHITE);
}

static void guidance(ag_t *g,const adv_post_t *p)
{
    adv_post_route_t r=adv_post_route(p);const char *title,*action;char route[40];
    if(p->practice) {
        static const char *const titles[]={"第一步 选上轨","正在切换到上轨","第二步 送红信","第三步 鸣笛","鸣笛成功","你学会了"};
        static const char *const prompts[]={"按上键选择上轨","等到红站再送信","现在轻点一下OK","按住OK让羊离开","先松开OK","点OK继续"};
        int step=p->lesson>=0&&p->lesson<6?p->lesson:5;title=titles[step];action=prompts[step];
    } else if(r.lane<0){title=p->remaining?"前方暂无车站":"信已送完";action=p->remaining?"看到站牌再选轨":"自动回库补信";}
    else {
        snprintf(route,sizeof(route),"下一站 %s",r.lane?"下轨":"上轨");title=route;
        action=r.can_choose?(r.choice_matches?"已选好，保持轨道":r.lane?"按下键选下轨":"按上键选上轨"):
            r.at_lane?"保持轨道，等送信":p->lane==r.lane?"正在切换轨道":"已过岔口，来不及了";
    }
    ag_rect(g,176,34,140,54,4,UI_INK,255,0,0);
    text(g,title,246,38,16,NT_ALIGN_CENTER,UI_WHITE);
    if(!p->practice&&r.lane>=0)ag_tri(g,306,47,5,r.lane==0,UI_GOLD);
    text(g,action,246,63,12,NT_ALIGN_CENTER,!p->practice&&r.can_choose&&!r.choice_matches?UI_GOLD:UI_WHITE);
    static const char *const reasons[]={"","未到送信位置","这站在另一轨","信封颜色不同","没有待送的信","错过站台 蒸汽-250","撞到牲畜 蒸汽-250"};
    bool animal=false;
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&p->events[i];
        if(e->type==POST_ANIMAL&&!e->done&&e->lane==p->lane&&e->x>ADV_POST_X&&e->x<ADV_POST_X+p->speed*90)animal=true;
    }
    bool pending=p->hold>0&&p->hold<ADV_POST_HOLD&&p->tap_target>=0&&!p->tap_reason;
    const char *hint=p->practice?"练习不耗汽 · 长按上暂停":p->feedback?reasons[p->miss_reason>=0&&p->miss_reason<7?p->miss_reason:1]:
        p->delivered?"送达 +1":pending?"松开OK，送出这封信":adv_post_can_deliver(p)?"现在点OK，送出同色信":
        p->whistle?"鸣笛中，松开停止":animal?"前方牲畜，按住OK鸣笛":"OK送信/鸣笛 · 下键下轨 · 上键上轨";
    ag_rect(g,0,220,320,20,0,UI_INK,255,0,0);text(g,hint,160,224,12,NT_ALIGN_CENTER,UI_WHITE);
}

void ui_draw_post(ag_t *g,const adv_post_t *p)
{
    ag_band(g,0,64,ag_rgb(178,212,209),ag_rgb(178,212,209));
    ag_band(g,64,176,ag_rgb(148,202,106),ag_rgb(148,202,106));
    for(int x=0;x<320;x+=96)ui_art(g,"game/post/tiles/far-mountains",0,x,40);
    int scroll=(int)(p->distance/60%32);
    for(int track=0;track<2;track++)for(int tile=-1;tile<=10;tile++)
        ui_art(g,"game/post/tiles/track-straight",0,tile*32-scroll,(track?ADV_POST_LOWER:ADV_POST_UPPER)-32);
    events(g,p);train(g,p);
    if(adv_post_can_deliver(p))ag_rect(g,128,p->y-68,56,34,0,0,0,UI_WHITE,2);
    header(g,p);guidance(g,p);
}
