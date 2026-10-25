// Landscape POST shell; all art remains at its native pixel size.
#include <stdio.h>
#include "adv_post.h"
#include "adv_ui_internal.h"
void ui_draw_post(ag_t *g,const adv_post_t *p);

static void text(ag_t *g,const char *s,int x,int y,int size,nt_align_t align,uint16_t color)
{ag_text_top(g,size==18?&collection_font_18:size==16?&collection_font_16:&collection_font_12,s,x,y,align,color);}

static void footer(ag_t *g,const char *s)
{ag_rect(g,0,220,320,20,0,UI_INK,255,0,0);text(g,s,160,224,12,NT_ALIGN_CENTER,UI_WHITE);}

static void title(ag_t *g,const adv_model_t *m)
{
    ag_band(g,0,240,UI_PAPER,UI_PAPER);
    ag_rect(g,0,0,320,30,0,UI_INK,255,0,0);
    text(g,"铁路平原",16,6,18,NT_ALIGN_LEFT,UI_WHITE);
    text(g,"顺时针横拿 按键朝下",304,9,12,NT_ALIGN_RIGHT,UI_WHITE);
    ui_art(g,"ui/wordmarks/post",0,60,32);
    text(g,"先看待送的第一封信",16,106,12,NT_ALIGN_LEFT,UI_INK);
    text(g,"同色站前点OK送信",16,124,12,NT_ALIGN_LEFT,UI_INK);
    text(g,"蒸汽空了结束 煤补汽",16,142,12,NT_ALIGN_LEFT,UI_INK);
    ag_rect(g,184,108,120,42,5,UI_INK,255,0,0);
    text(g,"下键 分步练习",244,120,16,NT_ALIGN_CENTER,UI_WHITE);
    text(g,"上下键选轨",244,158,12,NT_ALIGN_CENTER,UI_INK);
    text(g,"按住OK鸣笛",244,176,12,NT_ALIGN_CENTER,UI_INK);
    uint32_t earned=adv_earned(m);
    for(int tier=0;tier<3;tier++) {
        int x=36+tier*68;bool on=earned&adv_stamp_bit(3,tier);
        ag_circle(g,x,190,8,ui_tier_color(tier),on?255:40,ui_tier_color(tier),2);
        char n[12];snprintf(n,sizeof(n),"%u",(unsigned)adv_threshold(3,tier));
        text(g,n,x,204,12,NT_ALIGN_CENTER,UI_INK);
    }
    char best[32];if(m->best[3]>9999)snprintf(best,sizeof(best),"最佳9999+");else snprintf(best,sizeof(best),"最佳 %u",(unsigned)m->best[3]);
    text(g,best,304,201,16,NT_ALIGN_RIGHT,UI_INK);
    footer(g,"OK直接开始 · 下键练习 · 长按上返回");
}

static void card(ag_t *g,int x,int y,int w,int h)
{
    ag_rect(g,0,0,320,240,0,UI_INK,150,0,0);ui_popup(g,x,y,w,h);
}

void ui_draw_post_session(ag_t *g,const adv_model_t *m)
{
    ag_begin(g,m->phase==ADV_TITLE?UI_SCENE_TITLE:m->phase==ADV_RESULT?UI_SCENE_RESULT:UI_SCENE_PLAY);
    if(m->phase==ADV_TITLE){title(g,m);return;}
    const adv_post_t *p=m->game;ui_draw_post(g,p);
    if(m->phase==ADV_READY) {
        char n[12];snprintf(n,sizeof(n),"%d",(m->t+59)/60);
        ag_glow(g,160,132,38,UI_GOLD);ui_number(g,n,36,160,113,NT_ALIGN_CENTER);
    } else if(m->phase==ADV_PAUSE) {
        card(g,64,44,192,156);text(g,"暂停",160,60,18,NT_ALIGN_CENTER,UI_INK);
        text(g,"OK继续",160,99,16,NT_ALIGN_CENTER,UI_INK);
        text(g,"下键重新开始",160,132,16,NT_ALIGN_CENTER,UI_INK);
        text(g,"长按上回地图",160,165,16,NT_ALIGN_CENTER,UI_INK);
    } else if(m->phase==ADV_END) {
        ag_rect(g,80,99,160,44,8,UI_INK,240,UI_RED,2);
        text(g,"蒸汽耗尽",160,110,18,NT_ALIGN_CENTER,UI_WHITE);
    } else if(m->phase==ADV_RESULT) {
        card(g,40,36,240,172);text(g,"本局送达",160,47,16,NT_ALIGN_CENTER,UI_INK);
        char n[24];if(p->score>9999)snprintf(n,sizeof(n),"9999+");else snprintf(n,sizeof(n),"%u",(unsigned)p->score);
        ui_number(g,n,36,160,80,NT_ALIGN_CENTER);
        if(m->record)text(g,m->test?"测试不保存":"新纪录",160,124,12,NT_ALIGN_CENTER,UI_RED);
        if(m->best[3]>9999)snprintf(n,sizeof(n),"最佳9999+");else snprintf(n,sizeof(n),"最佳 %u",(unsigned)m->best[3]);
        text(g,n,160,147,16,NT_ALIGN_CENTER,UI_INK);
        ui_stamps(g,m,3,132,184,8,28);
        footer(g,"OK重玩 · 下键练习 · 长按上返回");
    }
}
