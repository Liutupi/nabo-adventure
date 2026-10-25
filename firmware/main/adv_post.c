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
    memset(g,0,sizeof(*g));g->rng=seed;g->res=1000;g->lane=g->choice=1;
    g->y=264;g->speed=90;g->next_fork=100;g->next_coal=300;g->next_animal=360;
    load(g);
}

static void penalty(adv_post_t *g) { g->res-=250;g->miss=24;g->cue=ADV_CUE_MISS; }

static void unload(adv_post_t *g)
{
    adv_post_event_t *station=NULL;
    for(int i=0;i<ADV_POST_CAP;i++) {
        adv_post_event_t *e=&g->events[i];int d=e->x-ADV_POST_X;
        if(e->type==POST_STATION&&!e->done&&d>=-ADV_POST_WINDOW&&d<=ADV_POST_WINDOW){station=e;break;}
    }
    if(station&&g->remaining&&station->lane==g->lane&&station->color==g->mail[0]) {
        if(g->score!=UINT32_MAX)g->score++;
        g->delivered=60;g->cue=ADV_CUE_HIT;station->done=1;
        memmove(g->mail,g->mail+1,4*sizeof(g->mail[0]));g->mail[4]=0;g->remaining--;
        if(!g->remaining&&!g->refill){g->refill=1;spawn(g,POST_DEPOT,320,g->lane,0);}
    } else {penalty(g);if(station)station->done=1;}
}

void adv_post_step(adv_post_t *g,const adv_input_t *in)
{
    g->cue=0;g->tick++;
    if(g->hit)g->hit--;
    if(g->miss)g->miss--;
    if(g->delivered)g->delivered--;
    if(g->over)return;
    if(in->up_down)g->choice=0;
    if(in->down_down)g->choice=1;
    if(in->ok_down)g->hold=1;
    else if(in->ok_held&&g->hold)g->hold=min(65535,g->hold+1);
    bool tap=in->ok_up&&g->hold>0&&g->hold<ADV_POST_HOLD;
    g->whistle=in->ok_held&&g->hold>=ADV_POST_HOLD;
    if(g->whistle&&(g->hold-ADV_POST_HOLD)%24==0)g->cue=ADV_CUE_WHISTLE;
    if(!in->ok_held)g->hold=0;
    g->drain_acc+=20+(g->whistle?30:0);
    while(g->drain_acc>=60){g->res--;g->drain_acc-=60;}
    g->distance+=(uint32_t)g->speed;
    if(--g->next_fork<=0) {
        spawn(g,POST_FORK,280,0,0);
        if(adv_rand(&g->rng)%100<60&&g->remaining)spawn(g,POST_STATION,380,(int)(adv_rand(&g->rng)%2),255);
        g->next_fork=range(g,150,240);
    }
    if(--g->next_coal<=0){spawn(g,POST_COAL,280,(int)(adv_rand(&g->rng)%2),0);g->next_coal=range(g,360,540);}
    if(g->lap>=3&&--g->next_animal<=0) {
        // Random calls stay ordered; C argument evaluation order is unspecified.
        int lane=(int)(adv_rand(&g->rng)%2),color=(int)(adv_rand(&g->rng)%2);
        spawn(g,POST_ANIMAL,max(280,110+g->speed*2),lane,color);g->next_animal=range(g,360,600);
    }
    for(int i=0;i<ADV_POST_CAP;i++) {
        adv_post_event_t *e=&g->events[i];if(!e->type)continue;
        e->x-=g->speed;
        if(e->type==POST_FORK&&!e->done&&e->x<=ADV_POST_X+60*60) {
            e->done=1;if(g->lane!=g->choice){g->lane=g->choice;g->transition=(7200+g->speed-1)/g->speed;}
        }
        if(e->type==POST_STATION&&e->color==255&&e->x<=240*60) {
            if(g->remaining)e->color=g->mail[0];else e->done=1;
        }
    }
    if(tap)unload(g);
    for(int i=0;i<ADV_POST_CAP;i++) {
        adv_post_event_t *e=&g->events[i];if(!e->type||e->done)continue;
        if(e->type==POST_STATION&&e->x<ADV_POST_X-ADV_POST_WINDOW){e->done=1;if(g->remaining)penalty(g);}
        if(e->type==POST_ANIMAL) {
            int gap=g->y-(e->lane?264:184);bool same=gap>=-20&&gap<=20;
            if(g->whistle&&same&&e->x>ADV_POST_X&&e->x<ADV_POST_X+g->speed*90)e->horn++;
            else e->horn=0;
            if(e->horn>=36){e->done=2;g->cue=ADV_CUE_MOVE;}
            else if(e->x<=ADV_POST_X){e->done=1;if(same){penalty(g);g->hit=24;}}
        }
        if(e->type==POST_COAL&&e->x<=ADV_POST_X) {
            int gap=g->y-(e->lane?264:184);
            e->done=1;if(gap>=-20&&gap<=20){g->res=min(1000,g->res+300);g->cue=ADV_CUE_HIT;}
        }
        if(e->type==POST_DEPOT&&e->x<=ADV_POST_X) {
            e->done=1;g->lap++;g->speed=min(200,(g->speed*108+50)/100);load(g);g->cue=ADV_CUE_ENTER;
        }
    }
    for(int i=0;i<ADV_POST_CAP;i++)if(g->events[i].type&&g->events[i].x<-100*60)memset(&g->events[i],0,sizeof(g->events[i]));
    if(g->transition){g->y+=((g->lane?264:184)-g->y)/g->transition;g->transition--;}
    else g->y=g->lane?264:184;
    if(g->res<=0){g->res=0;g->over=1;g->whistle=0;g->cue=ADV_CUE_OVER;}
}

static void start(void *g,uint32_t seed) {adv_post_start(g,seed);}
static void step(void *g,const adv_input_t *in) {adv_post_step(g,in);}
static adv_status_t status(const void *state)
{
    const adv_post_t *g=state;
    return (adv_status_t){g->score,g->res,g->over!=0,(uint8_t)g->cue};
}
const adv_game_t adv_post_game={"post",sizeof(adv_post_t),start,step,status};
