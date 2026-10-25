// POST H mode: fixed upper landscape, moving rails and native sprites below.
#include <stdio.h>
#include "adv_post.h"
#include "adv_ui_internal.h"

static const char *const COLORS[]={"red","blue","yellow","green"};
static const uint16_t INKS[]={0xcae6,0x43f3,0xd569,0x544b};

static void mail(ag_t *g,int color,int x,int y)
{
    char id[64];snprintf(id,sizeof(id),"game/post/props/envelope-%s",COLORS[color&3]);ui_art(g,id,0,x,y);
}

static void paint_fork(ag_t *g,int x)
{
    // The supplied 64x56 switch decoration is complemented by engine rails
    // spanning the game's 80px lane gap, without scaling any authored bitmap.
    for(int j=0;j<6;j++)for(int direction=0;direction<2;direction++) {
        int yy=(direction?254:174)+(direction?-1:1)*j*14;
        ag_rect(g,x-60+j*20,yy,23,5,0,UI_INK,255,0,0);
    }
    ui_art(g,"game/post/tiles/track-fork",0,x-32,208);
}

static void events(ag_t *g,const adv_post_t *p)
{
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&p->events[i];if(!e->type)continue;
        int x=e->x/60,y=e->lane?264:184;
        if(e->type==POST_FORK)paint_fork(g,x);
        if(e->type==POST_STATION&&e->color<4) {
            ui_art_tint(g,"game/post/props/station-platform-mask",x-40,y-66,INKS[e->color]);
            mail(g,e->color,x-16,y-64);
        }
        if(e->type==POST_COAL&&!e->done)ui_art(g,"game/post/props/coal-pile",0,x-16,y-23);
        if(e->type==POST_ANIMAL&&e->done!=1) {
            ui_art(g,e->color?"game/post/props/cow":"game/post/props/sheep",0,
                   x-(e->color?24:20),y-(e->color?34:28)-(e->done==2?30:0));
        }
        if(e->type==POST_DEPOT) {
            ag_rect(g,x-34,y-72,68,63,4,UI_INK,255,UI_WHITE,1);
            ag_text_top(g,&collection_font_16,"车库",x,y-60,NT_ALIGN_CENTER,UI_WHITE);
        }
    }
}

static void train(ag_t *g,const adv_post_t *p)
{
    for(int k=0;k<p->remaining;k++) {
        int x=110-80-k*64;ui_art(g,"game/post/props/carriage",0,x-32,p->y-44);
        mail(g,p->mail[k],x-16,p->y-65);
    }
    int left=62,top=p->y-81,frame=(p->tick/5)%6;
    const char *action="idle";
    if(p->hit||p->miss) {
        action="hit";int t=p->hit>p->miss?p->hit:p->miss;frame=(24-t)/5;
    } else if(p->whistle){action="whistle";frame=((p->hold-ADV_POST_HOLD)/5)%6;}
    else if(p->delivered){action=p->delivered>30?"throw":"delivered";frame=((p->delivered>30?60:30)-p->delivered)/5;}
    // Exact alpha unions of the unchanged native PNGs; tests bind every frame.
    ui_art_crop(g,"post_props/wheel-cycle",(p->tick/5)%4,left,top,13,58,88,81);
    ui_art_crop(g,"game/post/props/locomotive-body",0,left,top,1,1,96,70);
    ui_art_crop(g,"post_props/whistle-cord",p->whistle?frame:0,left,top,6,5,19,51);
    char id[64];snprintf(id,sizeof(id),"post_a/%s",action);
    ui_art_frame_anchor(g,id,(unsigned)frame,left+25,top+49);
    ui_art_crop(g,"game/post/props/cab-foreground",0,left,top,8,49,44,63);
}

void ui_draw_post(ag_t *g,const adv_post_t *p)
{
    ag_band(g,0,110,ag_rgb(178,212,209),ag_rgb(178,212,209));
    ag_band(g,110,210,ag_rgb(148,202,106),ag_rgb(148,202,106));
    for(int x=0;x<240;x+=96)ui_art(g,"game/post/tiles/far-mountains",0,x,84);
    int scroll=(int)(p->distance/60%32);
    // Fixed slots keep later static HUD ops at the same display-list indices.
    for(int track=0;track<2;track++)for(int tile=-1;tile<=8;tile++)
        ui_art(g,"game/post/tiles/track-straight",0,tile*32-scroll,(track?264:184)-32);
    events(g,p);train(g,p);
    ag_text_top(g,&collection_font_12,p->remaining?"先送":p->practice?"红信已送达":"回库补信",8,44,NT_ALIGN_LEFT,UI_INK);
    for(int k=0;k<p->remaining;k++)mail(g,p->mail[k],64+k*34,40);
    if(p->remaining)ag_rect(g,62,38,36,28,0,0,0,UI_GOLD,2);
    char line[32];snprintf(line,sizeof(line),"第%d趟",(int)p->lap+1);
    ag_text_top(g,&collection_font_12,line,8,72,NT_ALIGN_LEFT,UI_INK);
    bool animal=false,change=false;const adv_post_event_t *station=NULL;
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&p->events[i];
        if(e->type==POST_STATION&&!e->done&&e->x>=ADV_POST_MAIL_X-ADV_POST_WINDOW&&(!station||e->x<station->x))station=e;
        if(e->type==POST_FORK&&!e->done&&e->x>ADV_POST_X&&e->x<ADV_POST_X+p->speed*90+60*60)change=true;
        if(e->done||e->x<=ADV_POST_X||e->x>=ADV_POST_X+p->speed*90)continue;
        if(e->type==POST_FORK)change=true;
        if(e->type==POST_ANIMAL&&e->lane==p->lane)animal=true;
    }
    char target[48];
    if(station)snprintf(target,sizeof(target),"站台%s 已选%s",station->lane?"下轨":"上轨",p->choice?"下轨":"上轨");
    bool ready=adv_post_can_deliver(p),pending=p->hold>0&&p->hold<ADV_POST_HOLD&&p->tap_target>=0&&!p->tap_reason;
    static const char *const reasons[]={"","未到送信位置","这站在另一轨","信封颜色不同","没有待送的信","错过站台 扣250","撞到牲畜 扣250"};
    const char *hint=p->feedback?reasons[p->miss_reason>=0&&p->miss_reason<7?p->miss_reason:1]:
        p->delivered?"送达 +1":pending?"松开OK 送出这封信":ready?"现在点OK 送同色信":
        animal?"前方牲畜 按住鸣笛":station?target:change?(p->choice?"即将岔口 下轨":"即将岔口 上轨"):NULL;
    if(hint)ag_text_top(g,&collection_font_12,hint,232,72,NT_ALIGN_RIGHT,p->feedback||animal?UI_RED:UI_INK);
    ui_footer(g,p->whistle?"鸣笛中 · 松开停止":(p->tick/240)%2?"蒸汽空了结束 · 煤堆补汽":"上下选轨 · 点OK送信");
    if(ready&&!p->practice)ag_rect(g,128,(p->lane?264:184)-68,56,34,0,0,0,UI_WHITE,2);
    if(p->practice) {
        static const char *const titles[]={"第一步 选轨","火车正在换轨","第二步 送红信","第三步 鸣笛","鸣笛成功","你学会了"};
        static const char *const prompts[]={"按上键 选择上轨","等等，到红站再送信","现在轻点一下OK","按住OK让小羊离开","先松开OK","点OK继续"};
        int lesson=p->lesson>=0&&p->lesson<6?p->lesson:5;
        ag_rect(g,0,66,240,45,0,UI_INK,255,0,0);
        ag_text_top(g,&collection_font_16,titles[lesson],120,69,NT_ALIGN_CENTER,UI_WHITE);
        ag_text_top(g,&collection_font_12,prompts[lesson],120,93,NT_ALIGN_CENTER,UI_WHITE);
        ui_footer(g,"练习不耗汽 · 长按上暂停");
        if(lesson==2)ag_rect(g,128,116,56,30,0,0,0,UI_WHITE,3);
    }
}
