// SPACE V2: native 320x240 rocket journey; painted layers retain source pixels.
#include <stdio.h>
#include <stdlib.h>
#include "esp_heap_caps.h"
#include "adv_space.h"
#include "adv_ui_internal.h"
#define RY ADV_SPACE_RY
#define RGB(r,g,b) ((uint16_t)((((r)>>3)<<11)|(((g)>>2)<<5)|((b)>>3)))
#define INK RGB(6,10,30)
#define WHITE RGB(232,236,255)
#define GOLD RGB(255,211,74)
#define GREEN RGB(127,224,192)
#define RED RGB(255,138,106)
static uint32_t hash(uint32_t n){n=(n^0x9e3779b9u)*0x85ebca6bu;n^=n>>13;n*=0xc2b2ae35u;return n^(n>>16);}
static int min_i(int a,int b){return a<b?a:b;}
static int max_i(int a,int b){return a>b?a:b;}
static void text(ag_t *g,const char *s,int x,int y,int size,nt_align_t align,uint16_t col)
{ag_text_top(g,size==18?&collection_font_18:size==16?&collection_font_16:&collection_font_12,s,x,y,align,col);}
static void put(ag_t *g,const char *id,int x,int y){ui_art_frame_anchor(g,id,0,x,y);}
static void crew(ag_t *g,const char *action,unsigned f,int x,int y)
{char id[48];snprintf(id,sizeof(id),"space_a/%s",action);ui_art_frame_anchor(g,id,f,x,y);}
// Batch tiny stars, trails, warning lines and weather into one row operation.
// Their count does not consume the display-list budget needed by the painted layers.
typedef struct {uint32_t x:9,w:9,y:8;uint32_t h:8,c:16,a:8;} mark_t;
_Static_assert(sizeof(mark_t)==8,"Clipped screen marks must occupy two aligned words");
static struct {mark_t *m;unsigned n,first,groups;bool overflow;} s_marks;
uint32_t ui_space_staging_bytes(void){return s_marks.m?1024u*sizeof(mark_t):0;}
void ui_space_close(void){free(s_marks.m);s_marks.m=NULL;s_marks.n=s_marks.first=s_marks.groups=0;}
typedef struct {unsigned first,last;} mark_group_t;
static mark_group_t s_mark_groups[4];
static void mark(int x,int y,int w,int h,uint16_t c,int alpha)
{
    if(w<=0||h<=0||x>=320||y>=240||x+w<=0||y+h<=0)return;
    int right=min_i(320,x+w),bottom=min_i(240,y+h);
    x=max_i(0,x);y=max_i(0,y);w=right-x;h=bottom-y;
    if(s_marks.n>=1024){s_marks.overflow=true;return;}
    s_marks.m[s_marks.n++]=(mark_t){(unsigned)x,(unsigned)w,(unsigned)y,(unsigned)h,c,(unsigned)alpha};
}
static void marks_row(const void *ctx,int y,int x0,int x1,uint16_t *row)
{
    const mark_group_t *group=ctx;
    for(unsigned i=group->first;i<group->last;i++){
        const mark_t *m=&s_marks.m[i];if(y<m->y||y>=m->y+m->h)continue;
        int first=max_i(x0,m->x),last=min_i(x1,m->x+m->w);
        for(int x=first;x<last;x++)row[x-x0]=nt_blend565(row[x-x0],m->c,m->a*256/255);
    }
}
static void flush_marks(ag_t *g)
{
    if(s_marks.first==s_marks.n)return;
    if(s_marks.groups>=4){s_marks.overflow=true;return;}
    mark_group_t *ctx=&s_mark_groups[s_marks.groups++];*ctx=(mark_group_t){s_marks.first,s_marks.n};
    uint32_t key=2166136261u;
    for(unsigned i=ctx->first;i<ctx->last;i++){
        const mark_t *m=&s_marks.m[i];
        key=(key^(uint16_t)m->x)*16777619u;key=(key^(uint16_t)m->y)*16777619u;
        key=(key^(uint16_t)m->w)*16777619u;key=(key^(uint16_t)m->h)*16777619u;key=(key^m->c)*16777619u;key=(key^m->a)*16777619u;
    }
    ag_rows(g,marks_row,ctx,key);s_marks.first=s_marks.n;
}
static void sky(ag_t *g,int alt)
{
    static const int stops[]={0,900,1800,4000,6200,8200,99999};
    static const uint8_t colors[][6]={{30,42,92,242,166,110},{47,99,184,217,185,160},{58,128,212,169,214,245},
      {42,92,184,121,180,236},{19,32,90,60,86,168},{7,10,38,26,32,80},{4,5,26,11,14,42}};
    int at=0;while(at<5&&alt>=stops[at+1])at++;
    int h=stops[at+1]-stops[at],k=max_i(0,min_i(h,alt-stops[at])),c[6];
    for(int i=0;i<6;i++)c[i]=colors[at][i]+((int)colors[at+1][i]-colors[at][i])*k/h;
    ag_band(g,0,240,RGB(c[0],c[1],c[2]),RGB(c[3],c[4],c[5]));
}
static void backdrop(ag_t *g,int alt,unsigned vt)
{
    sky(g,alt);
    int star_a=min_i(255,max_i(0,(alt-4800)*255/3000));
    if(star_a)for(unsigned i=0;i<90;i++){
        int x=(int)(hash(i)%320),y=(int)((hash(i+300)%400+(unsigned)alt/50)%400)-80,s=i%11?1:2;
        mark(x,y,s,s,i%7?WHITE:RGB(255,217,168),star_a*(102+(int)(hash(i*3+(vt>>4))%154))/255);
    }
    flush_marks(g);
    if(alt<2600){int sy=154+alt*35/100;ag_glow(g,250,sy,70,RGB(255,190,120));ag_circle(g,250,sy,13,RGB(255,230,166),255,0,0);}
    if(alt>11000&&alt<99999){
        int k=min_i(8000,alt-11000);const char *id=k<3040?"game/space-v2/bg/moon-32":k<6000?"game/space-v2/bg/moon-64":"game/space-v2/bg/moon-128";
        put(g,id,250-k*60/8000,40+k*10/8000);
    }
    if(alt>8600)put(g,"game/space-v2/bg/nebula",0,160+(alt-8600)/20);
    if(alt>7000&&alt<12200)put(g,"game/space-v2/bg/earth-limb",0,244+(alt-7000)*24/1000);
    if(alt>9800&&alt<12000)put(g,"game/space-v2/bg/station",70+(alt-9800)*6/100,60+(alt-9800)*7/100);
    for(int a=4300;a<=5900;a+=800){int y=RY-(a-alt)*8/10;if(y>-10&&y<300)put(g,"game/space-v2/bg/cirrus",a*7%120-60,y);}
    for(int a=6100;a<=7000;a+=900){int y=RY-(a-alt)*55/100+40;if(y>-10&&y<380)put(g,"game/space-v2/bg/aurora",0,y);}
    for(unsigned i=0;i<12;i++){
        int a=300+(int)i*420,y=RY-(a-alt)*3/10+10;if(y<-10||y>300)continue;
        int off=(int)(hash(i+40)%301);put(g,"game/space-v2/bg/cloud-far",-off,y);put(g,"game/space-v2/bg/cloud-far",320-off,y);
    }
    static const int cloud_alt[]={600,1100,1600,2100,2600,3100,3600,4100,4500};
    for(unsigned i=0;i<sizeof(cloud_alt)/sizeof(*cloud_alt);i++){
        int y=RY-(cloud_alt[i]-alt)*7/10+50;if(y<-10||y>350)continue;
        int off=(int)(hash(i)%201);const char *id=i%2?"game/space-v2/bg/cloud-b":"game/space-v2/bg/cloud-a";
        put(g,id,-off,y);put(g,id,320-off,y);
    }
    if(alt<900)put(g,"game/space-v2/bg/launch-far",0,196+alt*35/100);
    if(alt<260)put(g,"game/space-v2/bg/launch-near",0,240+alt);
}
static void objects(ag_t *g,const adv_space_t *p,unsigned vt)
{
    for(int i=0;i<ADV_SPACE_OBJS;i++){
        const adv_space_obj_t *o=&p->objs[i];if(!o->type)continue;
        int x=o->x>>8,y=RY-(o->y-(p->alt>>8));
        if(o->state>0&&o->type!=SPACE_STORM){
            if((vt>>3)%2){int ex=x<0?10:310;ag_tri(g,ex,y,12,x>=0,RED);text(g,"!",ex,y-6,12,NT_ALIGN_CENTER,WHITE);}continue;
        }
        if(y<-60||y>300)continue;
        switch(o->type){
        case SPACE_BIRDS:put(g,(vt>>3)&1?"game/space-v2/props/birds-1":"game/space-v2/props/birds-0",x,y);break;
        case SPACE_PLANE:put(g,o->vx>0?"game/space-v2/props/plane":"game/space-v2/props/plane-left",x,y);break;
        case SPACE_BALLOON:put(g,"game/space-v2/props/balloon",x,y);break;
        case SPACE_STORM:
            put(g,"game/space-v2/props/storm-cloud",x,y);
            if(o->state>12){if((vt>>2)%2)for(int yy=y+20;yy<240;yy+=10)mark(x,yy,1,4,GOLD,140);}
            else if(o->state>0){for(int yy=y+18;yy<240;yy+=7)mark(x+(int)(hash((unsigned)yy+vt)%17)-8,yy,3,8,RGB(255,251,224),255);mark(0,0,320,240,RGB(255,255,230),64);}
            break;
        case SPACE_GUST:case SPACE_JET:
            for(unsigned n=0;n<9;n++){int xx=((int)(hash(n+(unsigned)o->y)%320)+(int)vt*4*o->vx)%320;if(xx<0)xx+=320;mark(xx,y-4-(int)n*6,18,1,WHITE,150);mark(xx+(o->vx>0?16:0),y-5-(int)n*6,2,3,WHITE,150);}break;
        case SPACE_STAR:ag_glow(g,x,y,9,GOLD);mark(x-1,y-6,3,13,GOLD,255);mark(x-6,y-1,13,3,GOLD,255);break;
        case SPACE_FUEL:ag_glow(g,x,y-4,13,GREEN);put(g,"game/space/props/fuel-can",x,y+8);break;
        case SPACE_REPAIR:put(g,"game/space-v2/props/repair",x,y);break;
        case SPACE_RING:ag_rect(g,x-18,y-7,36,14,7,0,0,GREEN,o->done?1:3);break;
        case SPACE_SAT:put(g,"game/space-v2/props/satellite",x,y);break;
        case SPACE_JUNK:put(g,"game/space-v2/props/junk",x,y);break;
        case SPACE_METEOR:for(int k=0;k<7;k++)mark(x-o->vx*k/70,y-k*4,4,5,RGB(255,150,70),190);put(g,"game/space/props/asteroid",x,y+14);break;
        case SPACE_ROCK:put(g,"game/space/props/asteroid",x,y+14);break;
        case SPACE_COMET:put(g,o->vx<0?"game/space-v2/props/comet":"game/space-v2/props/comet-right",x,y);break;
        }
    }
}
static void rocket(ag_t *g,const adv_space_t *p,unsigned vt,bool on)
{
    int x=p->x>>8,base=p->sep<2?RY+30:RY+2,flame=on?8+(int)(vt%3)*2+(p->boostT?10:0):0;
    if(on)for(unsigned n=0;n<16;n++){
        int age=(int)((vt+n*3)%40),yy=base+age*(2+(p->v>>8)),xx=x+(int)(hash(n+vt/4)%15)-7;
        ag_circle(g,xx,yy,3+age/4,RGB(225,230,240),max_i(0,100-age*2),0,0);
    }
    if((p->sep<2&&p->mode==SPACE_FLY)||p->mode==SPACE_IGNITE)put(g,"game/space-v2/props/booster",x,RY+14);
    if(flame){ag_glow(g,x,base+flame/2,12,RGB(255,150,60));ag_tri(g,x,base+flame/2,flame,false,GOLD);ag_tri(g,x,base+flame/4,flame/2,false,WHITE);}
    if(p->boostT){ag_rect(g,x-14,RY-50,28,56,14,0,0,RGB(140,230,255),2);for(unsigned n=0;n<8;n++)mark((int)(hash(n+vt)%320),(int)(hash(n*7+vt)%240),1,12,WHITE,150);}
    if(p->heat>450&&(p->alt>>8)<ADV_SPACE_Z2)ag_glow(g,x,RY-40,12,RED);
    if(!p->invuln||(vt>>2)%2)put(g,p->vx<-220?"game/space-v2/props/rocket-left":p->vx>220?"game/space-v2/props/rocket-right":"game/space-v2/props/rocket",x,RY+2);
    if(p->sep==2)for(int i=0;i<ADV_SPACE_FX;i++)if(p->fx[i].kind==SPACE_FX_SEP)put(g,"game/space-v2/props/booster",x-p->fx[i].t*6/10,RY+20+p->fx[i].t*24/10);
}
static void landing(ag_t *g,const adv_space_t *p,unsigned vt,bool play)
{
    ag_band(g,0,240,RGB(3,4,26),RGB(16,19,46));
    for(unsigned i=0;i<80;i++)mark((int)(hash(i)%320),(int)(hash(i+9)%150),1,1,WHITE,80+(int)(hash(i+(vt>>5))%176));
    flush_marks(g);
    ag_glow(g,70,46,19,RGB(150,200,255));ag_circle(g,70,46,15,RGB(47,111,208),255,0,0);ag_circle(g,64,42,5,RGB(95,191,122),255,0,0);ag_circle(g,76,52,4,RGB(95,191,122),255,0,0);
    put(g,"game/space-v2/bg/lunar-surface",0,240);
    ag_rect(g,p->pad-34,206,68,6,0,RGB(58,66,88),255,0,0);ag_rect(g,p->pad-31,208,62,2,0,(vt>>4)%2?GREEN:RGB(63,160,128),255,0,0);
    for(int s=-1;s<=1;s+=2)ag_rect(g,p->pad+s*34-1,203,3,3,0,GOLD,255,0,0);
    int x=p->lx>>8,y=p->ly>>8;bool ending=p->mode==SPACE_ENDING,out=false;const char *action=p->boostT?"jet":"cabin_idle";unsigned f=(vt>>3)%4;
    if(ending){if(p->modeT<30){action="land";f=(unsigned)p->modeT>>2;}else if(p->modeT<100){out=true;action="plant_flag";f=(unsigned)(p->modeT-30)>>3;}else{out=true;action="settlement_cheer";f=(unsigned)(p->modeT-100)>>2;}}
    if(!ending&&play)for(int yy=60;yy<202;yy+=8)mark(p->pad,yy,1,3,GREEN,100);
    flush_marks(g);
    if(p->boostT)ag_tri(g,x,y+8,16,false,GOLD);
    put(g,"game/space/lander/back",x,y);if(!out)crew(g,action,f,x,y-22);put(g,"game/space/lander/front",x,y);
    if(out){int nx=x<200?x+62:x-62;crew(g,action,f,nx,206);if(action[0]!='p'||f>=4)put(g,"game/space/props/flag",nx+10,206);}
    bool notice=false;for(int i=0;i<ADV_SPACE_FX;i++)if(p->fx[i].kind==SPACE_FX_ZONE&&p->fx[i].val==5)notice=true;
    if(!ending&&play&&!notice){char s[72];int speed=abs(p->lvy);snprintf(s,sizeof(s),"高度 %d  下降速度 %s%d.%d",max_i(0,206-y),p->lvy<0?"-":"",speed/100,speed/10%10);text(g,s,195,17,12,NT_ALIGN_CENTER,p->lvy<=260?GREEN:RED);if(206-y<90&&p->lvy>260)text(g,"太快了！点中键反推",195,35,12,NT_ALIGN_CENTER,RED);}
}
static void cockpit(ag_t *g,const adv_space_t *p,unsigned vt)
{
    ag_rect(g,4,4,62,62,10,INK,235,0,0);ag_rect(g,7,7,56,56,8,RGB(32,42,82),255,0,0);
    const char *action=p->mode==SPACE_ENDING?"settlement_cheer":p->invuln>40?"hard_land":p->boostT||(p->mode==SPACE_IGNITE&&p->ign)?"jet":"cabin_idle";
    char id[48];snprintf(id,sizeof(id),"space_a/%s",action);const adv_asset_record_t *a=adv_assets_find(id);
    if(a){int x=35-a->anchor_x,y=(p->mode==SPACE_ENDING?78:66)-a->anchor_y;ui_art_crop(g,id,(vt>>3)%(action[0]=='j'?4:6),x,y,7-x,7-y,63-x,63-y);}
    ag_rect(g,7,7,56,56,8,0,0,p->invuln>40?RED:RGB(142,166,232),2);
}
static int km_at(int alt)
{if(alt<4000)return (alt*12+2000)/4000;if(alt<8000)return 12+((alt-4000)*88+2000)/4000;if(alt<14000)return 100+((alt-8000)*1900+3000)/6000;return min_i(384400,2000+(int)(((int64_t)(alt-14000)*382400+2500)/5000));}
static void hud(ag_t *g,const adv_space_t *p,unsigned vt)
{
    ag_rect(g,0,216,320,24,0,INK,235,0,0);text(g,"燃料",4,216,12,NT_ALIGN_LEFT,WHITE);
    ag_rect(g,31,221,62,5,0,RGB(45,52,76),255,0,0);int fuel=min_i(62,max_i(0,p->fuel*62/100000));if(fuel)ag_rect(g,31,221,fuel,5,0,p->fuel<25000&&((vt>>3)%2)?RED:GREEN,255,0,0);
    if(p->mode!=SPACE_LAND){text(g,"温度",4,228,12,NT_ALIGN_LEFT,WHITE);ag_rect(g,31,232,62,4,0,RGB(45,52,76),255,0,0);int heat=min_i(62,max_i(0,p->heat*62/1000));if(heat)ag_rect(g,31,232,heat,4,0,p->heat>700?RED:GOLD,255,0,0);}
    for(int i=0;i<3;i++)ag_rect(g,102+i*12,222,9,12,2,i<p->hull?GREEN:RGB(45,52,76),255,0,0);
    char s[40];if(p->combo>=2){snprintf(s,sizeof(s),"×%d",adv_space_mult(p));text(g,s,145,222,12,NT_ALIGN_LEFT,GOLD);}
    if(p->mode>=SPACE_LAND)snprintf(s,sizeof(s),"月面");else snprintf(s,sizeof(s),"%d km",km_at(p->alt>>8));text(g,s,253,219,12,NT_ALIGN_RIGHT,RGB(200,210,240));
    if(p->score>99999)snprintf(s,sizeof(s),"99999+");else snprintf(s,sizeof(s),"%u",(unsigned)p->score);text(g,s,316,218,16,NT_ALIGN_RIGHT,WHITE);
    int prog=p->mode>=SPACE_LAND?170:min_i(170,(p->alt>>8)*170/19000);ag_rect(g,74,8,170,2,0,RGB(70,80,105),255,0,0);if(prog)ag_rect(g,74,8,prog,2,0,RGB(127,214,255),255,0,0);
    for(int z=1;z<=3;z++)ag_rect(g,74+(z==1?4000:z==2?8000:14000)*170/19000,6,1,6,0,GREEN,255,0,0);
    ag_circle(g,70,9,4,RGB(47,111,208),255,0,0);ag_circle(g,248,9,4,RGB(217,214,204),255,0,0);ag_rect(g,73+prog,4,3,10,0,WHITE,255,0,0);
}
static void gauge(ag_t *g,const char *title,const char *hint,int needle,int lo,int hi,int ylo,int yhi)
{
    ag_rect(g,70,72,180,74,10,INK,240,0,0);text(g,title,160,78,16,NT_ALIGN_CENTER,GOLD);text(g,hint,160,128,12,NT_ALIGN_CENTER,WHITE);
    ag_rect(g,86,103,148,12,0,RGB(90,42,42),255,0,0);ag_rect(g,86+148*ylo/100,103,148*(yhi-ylo)/100,12,0,RGB(122,106,42),255,0,0);ag_rect(g,86+148*lo/100,103,148*(hi-lo)/100,12,0,RGB(47,154,106),255,0,0);ag_rect(g,85+148*needle/100,99,3,20,0,WHITE,255,0,0);
}
static void timing(ag_t *g,const adv_space_t *p)
{
    if(p->mode==SPACE_IGNITE){
        char s[64];snprintf(s,sizeof(s),"绿区点中键 · 点亮 %d/3 台",(int)p->ign);gauge(g,"点火",s,adv_space_gauge(p->modeT),72,88,60,100);
        for(int i=0;i<3;i++)ag_circle(g,140+i*20,155,5,i<p->ign?GOLD:RGB(70,80,105),255,0,0);
        snprintf(s,sizeof(s),"T-%d",max_i(0,(300-p->modeT+59)/60));text(g,s,160,51,16,NT_ALIGN_CENTER,WHITE);
    }else if(p->sep==1)gauge(g,"一级分离！","绿区点中键",min_i(100,p->sepT*100/96),71,85,60,96);
    else if(p->tli==1){
        ag_rect(g,70,72,180,74,10,INK,240,0,0);text(g,"地月转移点火",160,78,16,NT_ALIGN_CENTER,GOLD);text(g,"光圈到中间，点中键 ×3",160,128,12,NT_ALIGN_CENTER,WHITE);
        for(int i=0;i<3;i++){int x=120+i*40,d=50+i*32-p->tliT;ag_circle(g,x,109,7,i<p->tliHit?GREEN:0,i<p->tliHit?255:0,WHITE,1);if(i>=p->tliHit&&d>-12&&d<40)ag_circle(g,x,109,7+max_i(0,d)/2,0,0,GOLD,2);}
    }
}
static void effects(ag_t *g,const adv_space_t *p)
{
    static const char *const zones[]={"","发射升空","冲出大气层","进入太空","奔向月球","登月舱分离"};
    static const char *const hints[]={"","左右避障，中键加速","少加速防过热，穿光环降温","护盾能撞碎小碎片","躲流星雨，准备登月","中键反推，左右对准着陆台"};
    for(int i=0;i<ADV_SPACE_FX;i++){
        const adv_space_fx_t *e=&p->fx[i];if(!e->kind)continue;char s[48];int y=e->y-14-e->t*4/10;
        if(e->kind==SPACE_FX_ZONE&&e->val>=1&&e->val<=5){ag_rect(g,74,16,242,48,6,INK,225,0,0);text(g,zones[e->val],195,18,16,NT_ALIGN_CENTER,GOLD);text(g,hints[e->val],195,42,12,NT_ALIGN_CENTER,WHITE);}
        else if(e->kind==SPACE_FX_STAR||e->kind==SPACE_FX_RING||e->kind==SPACE_FX_NEAR||e->kind==SPACE_FX_SMASH){snprintf(s,sizeof(s),"%s+%d",e->kind==SPACE_FX_NEAR?"擦边 ":e->kind==SPACE_FX_SMASH?"撞碎 ":"",(int)e->val);text(g,s,e->x,y,12,NT_ALIGN_CENTER,GOLD);}
        else if(e->kind==SPACE_FX_TIMING||e->kind==SPACE_FX_SEP){static const char *const q[]={"偏了","不错","完美！"};text(g,q[e->val>=0&&e->val<3?e->val:0],160,46-e->t/4,16,NT_ALIGN_CENTER,e->val==2?GOLD:e->val?WHITE:RED);}
        else if(e->kind==SPACE_FX_LANDED)text(g,e->val==2?"完美登月！":"登月成功！",160,70,18,NT_ALIGN_CENTER,GOLD);
        else if(e->kind==SPACE_FX_HIT)text(g,e->val==2?"被闪电劈中！":e->val==3?"过热！":"撞上了！",e->x,e->y-50,16,NT_ALIGN_CENTER,RED);
        else if(e->kind==SPACE_FX_OVERHEAT)text(g,"过热",e->x,e->y-40,12,NT_ALIGN_CENTER,RED);
        else if(e->kind==SPACE_FX_FUEL)text(g,"燃料 +",e->x,y,12,NT_ALIGN_CENTER,GREEN);
        else if(e->kind==SPACE_FX_REPAIR)text(g,"修好一格",e->x,y,12,NT_ALIGN_CENTER,GREEN);
        else if(e->kind==SPACE_FX_CRASH)text(g,"摔了！再来一次",160,90,16,NT_ALIGN_CENTER,RED);
    }
}
void ui_draw_space_session(ag_t *g,const adv_model_t *m)
{
    uint32_t ms=ui_millis();unsigned vt=ms/1000u*60u+ms%1000u*60u/1000u;
    const adv_space_t *p=m->game;s_marks.n=s_marks.first=s_marks.groups=0;s_marks.overflow=false;
    ag_begin(g,m->phase==ADV_TITLE?UI_SCENE_TITLE:m->phase==ADV_RESULT?UI_SCENE_RESULT:UI_SCENE_PLAY);
    if(!s_marks.m)s_marks.m=heap_caps_malloc(1024u*sizeof(mark_t),MALLOC_CAP_INTERNAL);
    if(!s_marks.m){
        ag_rect(g,0,0,320,240,0,INK,255,0,0);text(g,"内存不足",160,74,18,NT_ALIGN_CENTER,RED);
        text(g,"长按中键暂停",160,114,16,NT_ALIGN_CENTER,WHITE);text(g,"暂停后双击右键返回",160,148,12,NT_ALIGN_CENTER,WHITE);g->overflow=true;return;
    }
    if(m->phase==ADV_TITLE){
        backdrop(g,0,vt);rocket(g,p,vt,false);flush_marks(g);ag_rect(g,0,0,320,96,0,INK,205,0,0);
        text(g,"火箭登月",160,15,18,NT_ALIGN_CENTER,WHITE);text(g,"左移 · 中键加速/关键时刻按 · 右移",160,48,12,NT_ALIGN_CENTER,WHITE);
        text(g,"点火 → 升空 → 分离 → 奔月 → 登月",160,70,12,NT_ALIGN_CENTER,GOLD);
        if(vt%60<42)text(g,"中键开始",160,107,16,NT_ALIGN_CENTER,WHITE);
        text(g,"长按中键暂停 · 暂停后双击右键返回",160,222,12,NT_ALIGN_CENTER,WHITE);return;
    }
    bool lunar=p->mode==SPACE_LAND||p->mode==SPACE_ENDING||(p->mode==SPACE_LOST&&p->lvy+p->ly>0);
    if(lunar)landing(g,p,vt,m->phase==ADV_PLAY);else{backdrop(g,p->alt>>8,vt);objects(g,p,vt);flush_marks(g);rocket(g,p,vt,p->mode==SPACE_FLY||(p->mode==SPACE_IGNITE&&p->ign));}
    flush_marks(g);timing(g,p);effects(g,p);cockpit(g,p,vt);hud(g,p,vt);
    if(m->phase==ADV_READY){ag_rect(g,78,88,164,54,9,INK,240,0,0);text(g,"准备发射",160,98,18,NT_ALIGN_CENTER,WHITE);}
    if(m->phase==ADV_PAUSE){ag_rect(g,0,0,320,240,0,INK,220,0,0);text(g,"暂停",160,58,18,NT_ALIGN_CENTER,WHITE);text(g,"中键继续",160,100,16,NT_ALIGN_CENTER,GOLD);text(g,"左键重来",160,131,12,NT_ALIGN_CENTER,WHITE);text(g,"双击右键回地图",160,158,12,NT_ALIGN_CENTER,WHITE);}
    if(m->phase==ADV_RESULT){
        ag_rect(g,0,0,320,240,0,INK,225,0,0);text(g,p->win?"登月成功！":p->fuel<=0?"燃料耗尽":"火箭受损，任务中止",160,24,18,NT_ALIGN_CENTER,p->win?GOLD:WHITE);
        char s[80];snprintf(s,sizeof(s),"%u",(unsigned)p->score);ui_number_tint(g,s,36,160,60,NT_ALIGN_CENTER,WHITE);
        snprintf(s,sizeof(s),"%d km · 星星 %d · 擦边 %d",p->win?384400:km_at(p->alt>>8),(int)p->stars,(int)p->near);text(g,s,160,112,12,NT_ALIGN_CENTER,WHITE);
        snprintf(s,sizeof(s),"完美 %d · 最佳 %u",(int)p->perfects,(unsigned)m->best[8]);text(g,s,160,138,12,NT_ALIGN_CENTER,GOLD);
        if(m->record)text(g,m->test?"测试不保存":"新纪录！",160,166,12,NT_ALIGN_CENTER,GOLD);
        text(g,"中键重玩 · 双击右键回地图",160,205,12,NT_ALIGN_CENTER,WHITE);
    }
    if(s_marks.overflow)g->overflow=true;
}
