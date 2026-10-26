// Exact integer mirror of prototype/adv_space.js; random call order is part of the rules.
#include "adv_space.h"
#include "adv_rng.h"
#include <stdlib.h>
#include <string.h>
static int min_i(int a,int b){return a<b?a:b;}
static int max_i(int a,int b){return a>b?a:b;}
static int clamp(int a,int lo,int hi){return max_i(lo,min_i(hi,a));}
static int rnd(adv_space_t *g,unsigned n){return (int)(adv_rand(&g->rng)%n);}
static const int RAD[]={0,14,16,10,0,0,9,10,0,0,18,6,12,8,10,10};
static bool small(int type){return type==SPACE_BIRDS||type==SPACE_BALLOON||type==SPACE_JUNK;}
int adv_space_mult(const adv_space_t *g){return 1+min_i(4,g->combo/5);}
int adv_space_gauge(int t){int p=t%60;return p<30?p*100/30:(60-p)*100/30;}
int adv_space_zone(int alt){return alt<ADV_SPACE_Z1?1:alt<ADV_SPACE_Z2?2:alt<ADV_SPACE_Z3?3:4;}
static int quality(int v,int target,int perfect,int good){return abs(v-target)<=perfect?2:abs(v-target)<=good?1:0;}
static void effect(adv_space_t *g,int kind,int x,int y,int val)
{g->fx[g->fxHead]=(adv_space_fx_t){kind,x,y,val,0};g->fxHead=(g->fxHead+1)%ADV_SPACE_FX;}
static void hurt(adv_space_t *g,int why)
{
    if(g->invuln)return;
    g->hull--;g->hits++;g->combo=0;g->invuln=70;g->cue=7;
    effect(g,SPACE_FX_HIT,g->x>>8,ADV_SPACE_RY-20,why);
    if(g->hull<=0){g->mode=SPACE_LOST;g->modeT=90;}
}
void adv_space_start(adv_space_t *g,uint32_t seed)
{
    memset(g,0,sizeof(*g));g->rng=seed;g->res=1000;g->mode=SPACE_IGNITE;
    g->x=160<<8;g->fuel=ADV_SPACE_FUEL_MAX;g->hull=3;g->lastBoost=-100;g->zoneSeen=1;g->nextObj=220;
}
static void spawn(adv_space_t *g)
{
    int z=adv_space_zone((g->alt>>8)+250),y=(g->alt>>8)+250+rnd(g,40),v=rnd(g,100),x=20+rnd(g,280);
    int side=rnd(g,2),type,vx=0,state=0;adv_space_obj_t *o=NULL;
    for(int i=0;i<ADV_SPACE_OBJS;i++)if(!g->objs[i].type){o=&g->objs[i];break;}
    if(!o)g->blocked++;
    if(z==1){
        if(v<26){type=SPACE_BIRDS;vx=side?150:-150;}
        else if(v<38){type=SPACE_PLANE;vx=side?380:-380;}
        else if(v<50)type=SPACE_BALLOON;
        else if(v<62)type=SPACE_STORM;
        else if(v<72){type=SPACE_GUST;vx=side?1:-1;}
        else if(v<90)type=SPACE_STAR;else type=SPACE_FUEL;
    }else if(z==2){
        if(v<24){type=SPACE_JET;vx=side?1:-1;}
        else if(v<44)type=SPACE_RING;
        else if(v<58)type=SPACE_BALLOON;
        else if(v<72){type=SPACE_METEOR;vx=side?260:-260;}
        else if(v<90)type=SPACE_STAR;else type=rnd(g,3)?SPACE_FUEL:SPACE_REPAIR;
    }else if(z==3){
        if(v<26){type=SPACE_SAT;vx=side?90:-90;}
        else if(v<50){type=SPACE_JUNK;vx=side?330:-330;}
        else if(v<68){type=SPACE_ROCK;vx=side?40:-40;}
        else if(v<88)type=SPACE_STAR;else type=rnd(g,4)?SPACE_FUEL:SPACE_REPAIR;
    }else{
        if(v<34){type=SPACE_METEOR;vx=side?300:-300;}
        else if(v<54){type=SPACE_ROCK;vx=side?60:-60;}
        else if(v<64){type=SPACE_COMET;vx=side?200:-200;}
        else if(v<86)type=SPACE_STAR;else type=SPACE_FUEL;
    }
    int ox=x;
    if(type==SPACE_PLANE||type==SPACE_JUNK||type==SPACE_METEOR||type==SPACE_COMET){ox=vx>0?-20:340;state=45;}
    if(type==SPACE_GUST||type==SPACE_JET)ox=160;
    if(o)*o=(adv_space_obj_t){type,ox*256,y,vx,state,0};
    int gap=z==1?70:z==2?62:z==3?56:50;g->nextObj=y+gap+rnd(g,50);
}
static void step_ignite(adv_space_t *g,const adv_input_t *in)
{
    g->modeT++;
    if(in->down_down&&g->ign<3){
        int q=quality(adv_space_gauge(g->modeT),80,8,20);g->ign++;g->ignScore+=q;if(q==2)g->perfects++;
        g->bonus+=q*50;effect(g,SPACE_FX_TIMING,160,120,q);g->cue=q?6:7;
    }
    if(g->ign>=3||g->modeT>=ADV_SPACE_IGN_T){g->mode=SPACE_FLY;g->modeT=0;g->vTarget=520+g->ignScore*20;effect(g,SPACE_FX_ZONE,0,0,1);}
}
static void step_fly(adv_space_t *g,const adv_input_t *in)
{
    int z=adv_space_zone(g->alt>>8);
    if(z!=g->zoneSeen){g->zoneSeen=z;effect(g,SPACE_FX_ZONE,0,0,z);g->vTarget+=z==2?220:z==3?180:0;}
    if(!g->sep&&(g->alt>>8)>=ADV_SPACE_Z1){g->sep=1;g->sepT=0;}
    if(g->sep==1){
        g->sepT++;int needle=g->sepT*100/ADV_SPACE_SEP_T;
        if(in->down_down||needle>=100){
            const int fuel[]={6000,18000,30000},speed[]={-80,60,140};
            int q=in->down_down?quality(needle,78,7,18):0;g->sep=2;g->sepQ=q;
            g->fuel=min_i(ADV_SPACE_FUEL_MAX,g->fuel+fuel[q]);g->vTarget+=speed[q];if(q==2)g->perfects++;
            g->bonus+=q*100;effect(g,SPACE_FX_SEP,g->x>>8,ADV_SPACE_RY,q);g->cue=q?6:7;
        }
    }
    if(!g->tli&&(g->alt>>8)>=ADV_SPACE_Z3){g->tli=1;g->tliT=0;}
    if(g->tli==1){
        g->tliT++;
        if(in->down_down){
            int at=ADV_SPACE_TLI_LEAD+g->tliHit*ADV_SPACE_TLI_BEAT,q=quality(g->tliT,at,5,11);
            g->tliHit++;g->tliQ+=q;if(q==2)g->perfects++;g->vTarget+=q*40;g->bonus+=q*60;
            effect(g,SPACE_FX_TIMING,160,100,q);g->cue=q?6:7;
        }
        if(g->tliHit>=3||g->tliT>ADV_SPACE_TLI_LEAD+3*ADV_SPACE_TLI_BEAT+20)g->tli=2;
    }
    bool timing=g->sep==1||g->tli==1,left=in->ok_held&&!in->up_held,right=in->up_held&&!in->ok_held;
    if(left)g->vx=max_i(-700,g->vx-28);else if(right)g->vx=min_i(700,g->vx+28);else g->vx-=g->vx/6;
    if(in->down_down&&!timing&&(int32_t)(g->tick-g->lastBoost)>=20){
        g->lastBoost=(int32_t)g->tick;g->boostT=40;g->v+=260;g->fuel-=2500;if(z<=2)g->heat+=170;g->cue=6;
    }
    if(g->boostT>0)g->boostT--;
    int target=g->sep==1?g->vTarget*3/4:g->vTarget;
    g->v=g->v<target?min_i(target,g->v+4):max_i(target,g->v-6);g->push=0;g->x=clamp(g->x+g->vx,20<<8,300<<8);
    int prev=g->alt>>8;g->alt+=g->v;int alt=g->alt>>8;g->fuel-=z<=2?14:10;
    if(z<=2)g->heat=max_i(0,g->heat+max_i(0,(g->v-target)/24)-4);else g->heat=max_i(0,g->heat-8);
    if(g->heat>=1000){g->heat=500;effect(g,SPACE_FX_OVERHEAT,g->x>>8,ADV_SPACE_RY-30,0);hurt(g,3);}
    if(g->invuln>0)g->invuln--;
    while(g->nextObj<alt+250)spawn(g);
    int rx=g->x>>8;
    for(int i=0;i<ADV_SPACE_OBJS;i++){
        adv_space_obj_t *o=&g->objs[i];if(!o->type)continue;
        if(o->state>0&&o->type!=SPACE_STORM){o->state--;continue;}
        o->x+=o->vx==1||o->vx==-1?0:o->vx;
        if(o->type==SPACE_BALLOON)o->y+=(g->tick&3)==0?1:0;
        if(o->type==SPACE_METEOR)o->y-=3;
        int ox=o->x>>8,r=RAD[o->type];
        if(o->type==SPACE_GUST||o->type==SPACE_JET){
            if(alt+20>=o->y&&alt+20<=o->y+56){int p=o->type==SPACE_JET?22:14;g->vx=clamp(g->vx+o->vx*p,-700,700);g->push=o->vx;}
        }else if(o->type==SPACE_STORM){
            int sy=ADV_SPACE_RY-(o->y-alt);
            if(o->state==0&&sy>20&&sy<150){o->state=62;o->vx=0;o->x=clamp(rx+rnd(g,61)-30,20,300)*256;}
            if(o->state>0){o->state--;if(o->state<12&&o->state>0&&abs(rx-(o->x>>8))<14)hurt(g,2);if(o->state==0)o->state=-1;}
        }else if(!o->done){
            int top=alt+40,dx=abs(ox-rx);bool in_y=o->y+r>=alt&&o->y-r<=top;
            if(in_y&&dx<r+7){
                o->done=1;
                if(o->type==SPACE_STAR){g->stars++;g->combo++;g->best=max_i(g->best,g->combo);int p=20*adv_space_mult(g);g->bonus+=p;effect(g,SPACE_FX_STAR,ox,ADV_SPACE_RY-(o->y-alt),p);g->cue=6;o->type=0;}
                else if(o->type==SPACE_FUEL){g->cans++;g->fuel=min_i(ADV_SPACE_FUEL_MAX,g->fuel+14000);effect(g,SPACE_FX_FUEL,ox,ADV_SPACE_RY-(o->y-alt),0);g->cue=6;o->type=0;}
                else if(o->type==SPACE_REPAIR){g->hull=min_i(3,g->hull+1);effect(g,SPACE_FX_REPAIR,ox,ADV_SPACE_RY-(o->y-alt),0);g->cue=6;o->type=0;}
                else if(o->type==SPACE_RING){g->rings++;g->combo++;g->best=max_i(g->best,g->combo);g->heat=max_i(0,g->heat-300);int p=40*adv_space_mult(g);g->bonus+=p;effect(g,SPACE_FX_RING,ox,ADV_SPACE_RY-(o->y-alt),p);g->cue=6;}
                else if(g->boostT>0&&small(o->type)){g->combo++;g->best=max_i(g->best,g->combo);int p=25*adv_space_mult(g);g->bonus+=p;effect(g,SPACE_FX_SMASH,ox,ADV_SPACE_RY-(o->y-alt),p);g->cue=6;o->type=0;}
                else hurt(g,1);
            }else if(o->type!=SPACE_STAR&&o->type!=SPACE_FUEL&&o->type!=SPACE_REPAIR&&o->type!=SPACE_RING&&prev+20<o->y&&alt+20>=o->y&&dx<r+18){
                o->done=1;g->near++;g->combo++;g->best=max_i(g->best,g->combo);int p=15*adv_space_mult(g);g->bonus+=p;effect(g,SPACE_FX_NEAR,rx,ADV_SPACE_RY-30,p);
            }
        }
        if(o->y<alt-120||ox<-60||ox>380)memset(o,0,sizeof(*o));
    }
    if(alt>=ADV_SPACE_Z4){
        g->mode=SPACE_LAND;g->modeT=0;memset(g->objs,0,sizeof(g->objs));g->lx=(g->x>>8)*256;g->ly=24<<8;g->lvx=0;g->lvy=120;g->pad=60+rnd(g,201);effect(g,SPACE_FX_ZONE,0,0,5);
    }
}
static void step_land(adv_space_t *g,const adv_input_t *in)
{
    g->modeT++;bool left=in->ok_held&&!in->up_held,right=in->up_held&&!in->ok_held;
    if(left){g->lvx-=5;g->fuel-=30;}if(right){g->lvx+=5;g->fuel-=30;}
    if(in->down_down){g->lvy-=170;g->fuel-=1500;g->boostT=10;g->cue=6;}
    if(g->boostT>0)g->boostT--;
    g->lvy=min_i(900,g->lvy+5);g->lvx=clamp(g->lvx,-500,500);
    g->lx=clamp(g->lx+g->lvx,40<<8,280<<8);g->ly=max_i(10<<8,g->ly+g->lvy);g->fuel-=8;
    if(g->invuln>0)g->invuln--;
    if((g->ly>>8)>=ADV_SPACE_GROUND){
        int dx=abs((g->lx>>8)-g->pad);
        if(dx<=ADV_SPACE_PAD_HALF-12&&g->lvy<=ADV_SPACE_SAFE_VY&&abs(g->lvx)<=200){
            bool soft=g->lvy<=120;g->landings++;if(soft)g->perfects++;
            g->bonus+=1000+(soft?500:0)+g->hull*300+max_i(0,g->fuel)/100;
            g->ly=ADV_SPACE_GROUND<<8;g->lvx=g->lvy=0;g->mode=SPACE_ENDING;g->modeT=0;g->win=1;g->cue=6;effect(g,SPACE_FX_LANDED,g->pad,ADV_SPACE_GROUND-110,soft?2:1);
        }else{
            effect(g,SPACE_FX_CRASH,g->lx>>8,ADV_SPACE_GROUND-100,0);g->hull--;g->hits++;g->cue=7;
            if(g->hull<=0){g->mode=SPACE_LOST;g->modeT=90;}else{g->ly=24<<8;g->lvy=120;g->lvx=0;g->fuel-=5000;g->invuln=40;}
        }
    }
}
void adv_space_step(adv_space_t *g,const adv_input_t *in)
{
    g->cue=0;for(int i=0;i<ADV_SPACE_FX;i++)if(g->fx[i].kind&&++g->fx[i].t>=70)g->fx[i].kind=0;
    if(g->over)return;
    g->tick++;g->presses+=(in->ok_down?1:0)+(in->up_down?1:0)+(in->down_down?1:0);
    if(g->mode==SPACE_IGNITE)step_ignite(g,in);else if(g->mode==SPACE_FLY)step_fly(g,in);else if(g->mode==SPACE_LAND)step_land(g,in);
    else if(g->mode==SPACE_ENDING){if(++g->modeT>=150){g->over=1;g->cue=8;}}
    else if(g->mode==SPACE_LOST){if(--g->modeT<=0){g->over=1;g->cue=8;}}
    if(g->fuel<=0&&g->mode!=SPACE_ENDING&&g->mode!=SPACE_LOST){g->fuel=0;g->mode=SPACE_LOST;g->modeT=90;}
    g->res=max_i(0,g->fuel/100);g->score=(uint32_t)(min_i((g->alt>>8)/10,ADV_SPACE_Z4/10)+g->bonus);
}
static void start_game(void *g,uint32_t seed){adv_space_start(g,seed);}
static void step_game(void *g,const adv_input_t *in){adv_space_step(g,in);}
static adv_status_t status_game(const void *state)
{const adv_space_t *g=state;return (adv_status_t){g->score,g->res,g->over!=0,(uint8_t)g->cue};}
const adv_game_t adv_space_game={"space",sizeof(adv_space_t),start_game,step_game,status_game};
