#include "adv_post.h"
#include <string.h>
#include "adv_rng.h"
#include "adv_model.h"

static int range(adv_post_t *g,int a,int b) { return a+(int)(adv_rand(&g->rng)%(uint32_t)(b-a+1)); }
static int min(int a,int b) { return a<b?a:b; }
static int max(int a,int b) { return a>b?a:b; }

static void spawn(adv_post_t *g,int type,int x,int lane,int color)
{
    for(int i=0;i<ADV_POST_CAP;i++)if(!g->events[i].type) {
        g->events[i]=(adv_post_event_t){type,x*60,lane,color,0,0};return;
    }
    g->spawn_blocked++;
}

static void load(adv_post_t *g)
{
    g->remaining=g->lap?range(g,3,5):3;
    memset(g->mail,0,sizeof(g->mail));
    for(int i=0;i<g->remaining;i++)g->mail[i]=(int)(adv_rand(&g->rng)%(g->lap>=2?4u:3u));
    g->refill=0;
}

void adv_post_start(adv_post_t *g,uint32_t seed)
{
    memset(g,0,sizeof(*g));g->rng=seed;g->res=1000;g->lane=g->choice=1;g->tap_target=-1;
    g->y=ADV_POST_LOWER;g->speed=90;g->next_fork=100;g->next_coal=300;g->next_animal=360;
    load(g);
}

static void penalty(adv_post_t *g,int reason)
{g->res-=250;g->miss=24;g->miss_reason=reason;g->feedback=90;g->cue=ADV_CUE_MISS;}

static int station_at_nose(const adv_post_t *g)
{
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&g->events[i];int d=e->x-ADV_POST_MAIL_X;
        if(e->type==POST_STATION&&!e->done&&d>=-ADV_POST_WINDOW&&d<=ADV_POST_WINDOW)return i;
    }
    return -1;
}

static int tap_reason(const adv_post_t *g,int index)
{
    if(!g->remaining)return 4;
    if(index<0)return 1;
    const adv_post_event_t *e=&g->events[index];int d=g->y-(e->lane?ADV_POST_LOWER:ADV_POST_UPPER);
    if(d<-20||d>20)return 2;
    return e->color==g->mail[0]?0:3;
}

bool adv_post_can_deliver(const adv_post_t *g){return tap_reason(g,station_at_nose(g))==0;}

adv_post_route_t adv_post_route(const adv_post_t *g)
{
    const adv_post_event_t *station=NULL;
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&g->events[i];
        if(e->type==POST_STATION&&!e->done&&e->x>=ADV_POST_MAIL_X-ADV_POST_WINDOW&&(!station||e->x<station->x))station=e;
    }
    if(!station)return (adv_post_route_t){-1,0,0,0};
    int d=g->y-(station->lane?ADV_POST_LOWER:ADV_POST_UPPER);
    adv_post_route_t r={station->lane,0,g->choice==station->lane,d>=-20&&d<=20};
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&g->events[i];
        if(e->type==POST_FORK&&!e->done&&e->x>ADV_POST_X+3600&&e->x<station->x)r.can_choose=1;
    }
    return r;
}

static bool controls(adv_post_t *g,const adv_input_t *in,bool horn_allowed)
{
    if(in->ok_down) {
        g->hold=1;if(g->presses!=UINT32_MAX)g->presses++;
        g->tap_target=station_at_nose(g);g->tap_reason=tap_reason(g,g->tap_target);
    } else if(in->ok_held&&g->hold)g->hold=min(65535,g->hold+1);
    bool tap=in->ok_up&&g->hold>0&&g->hold<ADV_POST_HOLD;
    g->whistle=in->ok_held&&g->hold>=ADV_POST_HOLD&&horn_allowed;
    if(g->whistle&&(g->hold-ADV_POST_HOLD)%24==0)g->cue=ADV_CUE_WHISTLE;
    if(g->hold>=ADV_POST_HOLD)g->tap_target=-1;
    if(!in->ok_held){g->hold=0;if(!in->ok_up)g->tap_target=-1;}
    return tap;
}

static void unload(adv_post_t *g)
{
    adv_post_event_t *station=g->tap_target>=0&&g->tap_target<ADV_POST_CAP?&g->events[g->tap_target]:NULL;
    if(g->taps!=UINT32_MAX)g->taps++;
    if(station&&!station->done&&g->tap_reason==0) {
        if(g->score!=UINT32_MAX)g->score++;
        g->delivered=60;g->cue=ADV_CUE_HIT;station->done=1;g->feedback=0;
        memmove(g->mail,g->mail+1,4*sizeof(g->mail[0]));g->mail[4]=0;g->remaining--;
        if(!g->remaining&&!g->refill){g->refill=1;spawn(g,POST_DEPOT,ADV_POST_WIDTH+80,g->lane,0);}
    } else {penalty(g,g->tap_reason?g->tap_reason:1);if(station)station->done=1;}
    g->tap_target=-1;
}

void adv_post_start_practice(adv_post_t *g,uint32_t seed)
{
    adv_post_start(g,seed);g->practice=1;g->speed=60;g->remaining=1;g->refill=1;
    memset(g->mail,0,sizeof(g->mail));spawn(g,POST_FORK,210,0,0);spawn(g,POST_STATION,330,0,0);
}

static void practice_step(adv_post_t *g,const adv_input_t *in)
{
    bool tap=controls(g,in,g->lesson>=3&&g->lesson<=4);
    adv_post_event_t *fork=&g->events[0],*station=&g->events[1],*animal=&g->events[2];
    if(g->lesson==0&&in->up_down){g->choice=0;g->lesson=1;g->cue=ADV_CUE_MOVE;}
    if(g->lesson==1) {
        g->distance+=(uint32_t)g->speed;fork->x-=g->speed;station->x-=g->speed;
        if(!fork->done&&fork->x<=ADV_POST_X+3600){fork->done=1;g->lane=0;g->transition=120;}
        if(g->transition){g->y+=(ADV_POST_UPPER-g->y)/g->transition;g->transition--;}
        if(station->x<=ADV_POST_MAIL_X&&!g->transition){station->x=ADV_POST_MAIL_X;g->y=ADV_POST_UPPER;g->lesson=2;g->cue=ADV_CUE_ENTER;}
    } else if(g->lesson==2&&tap) {
        unload(g);g->lesson=3;spawn(g,POST_ANIMAL,160,0,0);
    } else if(g->lesson==3) {
        if(g->whistle)animal->horn++;else animal->horn=0;
        if(animal->horn>=36){animal->done=2;g->lesson=4;g->cue=ADV_CUE_MOVE;}
    } else if(g->lesson==4&&!in->ok_held){g->lesson=5;g->whistle=0;animal->done=1;}
    else if(g->lesson==5&&tap){g->over=1;g->whistle=0;g->cue=ADV_CUE_ENTER;}
}

void adv_post_step(adv_post_t *g,const adv_input_t *in)
{
    g->cue=0;g->tick++;
    if(g->hit)g->hit--;
    if(g->miss)g->miss--;
    if(g->delivered)g->delivered--;
    if(g->feedback)g->feedback--;
    if(g->over)return;
    if(g->practice){practice_step(g,in);return;}
    if(in->up_down)g->choice=0;
    if(in->down_down)g->choice=1;
    bool tap=controls(g,in,true);
    g->drain_acc+=20+(g->whistle?30:0);
    while(g->drain_acc>=60){g->res--;g->drain_acc-=60;}
    g->distance+=(uint32_t)g->speed;
    if(--g->next_fork<=0) {
        spawn(g,POST_FORK,ADV_POST_WIDTH+40,0,0);
        if(adv_rand(&g->rng)%100<60&&g->remaining)spawn(g,POST_STATION,ADV_POST_WIDTH+140,(int)(adv_rand(&g->rng)%2),255);
        g->next_fork=range(g,150,240);
    }
    if(--g->next_coal<=0){spawn(g,POST_COAL,ADV_POST_WIDTH+40,(int)(adv_rand(&g->rng)%2),0);g->next_coal=range(g,360,540);}
    if(g->lap>=3&&--g->next_animal<=0) {
        // Random calls stay ordered; C argument evaluation order is unspecified.
        int lane=(int)(adv_rand(&g->rng)%2),color=(int)(adv_rand(&g->rng)%2);
        spawn(g,POST_ANIMAL,max(ADV_POST_WIDTH+40,110+g->speed*2),lane,color);g->next_animal=range(g,360,600);
    }
    for(int i=0;i<ADV_POST_CAP;i++) {
        adv_post_event_t *e=&g->events[i];if(!e->type)continue;
        e->x-=g->speed;
        if(e->type==POST_FORK&&!e->done&&e->x<=ADV_POST_X+60*60) {
            e->done=1;if(g->lane!=g->choice){g->lane=g->choice;g->transition=(7200+g->speed-1)/g->speed;}
        }
        if(e->type==POST_STATION&&e->color==255&&e->x<=ADV_POST_WIDTH*60) {
            if(g->remaining)e->color=g->mail[0];else e->done=1;
        }
    }
    if(tap)unload(g);
    for(int i=0;i<ADV_POST_CAP;i++) {
        adv_post_event_t *e=&g->events[i];if(!e->type||e->done)continue;
        if(e->type==POST_STATION&&e->x<ADV_POST_MAIL_X-ADV_POST_WINDOW&&
           !(g->tap_target==i&&g->hold>0&&g->hold<ADV_POST_HOLD)) {
            e->done=1;if(g->remaining)penalty(g,5);
        }
        if(e->type==POST_ANIMAL) {
            int gap=g->y-(e->lane?ADV_POST_LOWER:ADV_POST_UPPER);bool same=gap>=-20&&gap<=20;
            if(g->whistle&&same&&e->x>ADV_POST_X&&e->x<ADV_POST_X+g->speed*90)e->horn++;
            else e->horn=0;
            if(e->horn>=36){e->done=2;g->cue=ADV_CUE_MOVE;}
            else if(e->x<=ADV_POST_X){e->done=1;if(same){penalty(g,6);g->hit=24;}}
        }
        if(e->type==POST_COAL&&e->x<=ADV_POST_X) {
            int gap=g->y-(e->lane?ADV_POST_LOWER:ADV_POST_UPPER);
            e->done=1;if(gap>=-20&&gap<=20){g->res=min(1000,g->res+300);g->cue=ADV_CUE_HIT;}
        }
        if(e->type==POST_DEPOT&&e->x<=ADV_POST_X) {
            e->done=1;g->lap++;g->speed=min(200,(g->speed*108+50)/100);load(g);g->cue=ADV_CUE_ENTER;
        }
    }
    for(int i=0;i<ADV_POST_CAP;i++)if(g->events[i].type&&g->events[i].x<-100*60)memset(&g->events[i],0,sizeof(g->events[i]));
    if(g->transition){g->y+=((g->lane?ADV_POST_LOWER:ADV_POST_UPPER)-g->y)/g->transition;g->transition--;}
    else g->y=g->lane?ADV_POST_LOWER:ADV_POST_UPPER;
    if(g->res<=0){g->res=0;g->over=1;g->whistle=0;g->cue=ADV_CUE_OVER;}
}

static void start(void *g,uint32_t seed) {adv_post_start(g,seed);}
static void step(void *g,const adv_input_t *in) {adv_post_step(g,in);}
static adv_status_t status(const void *state)
{
    const adv_post_t *g=state;
    return (adv_status_t){g->practice?0:g->score,g->res,g->over!=0,(uint8_t)g->cue};
}
const adv_game_t adv_post_game={"post",sizeof(adv_post_t),start,step,status};
