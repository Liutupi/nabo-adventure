#include "adv_night.h"
#include "adv_rng.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>

static const int POS[]={48,120,192};
static int range(adv_night_t *g,int lo,int hi){return lo+(int)(adv_rand(&g->rng)%(unsigned)(hi-lo+1));}
int adv_night_speed(const adv_night_t *g){return g->score>=62?110:48+(int)g->score;}
static unsigned moth_percent(const adv_night_t *g){return g->score>=48?32:8+g->score/2;}
int adv_night_object_y(const adv_night_bug_t *e)
{int q=(e->age+e->phase)%64,v=q<32?q:64-q;return e->base_y+v*16/32-8;}

void adv_night_start(adv_night_t *g,uint32_t seed)
{
    memset(g,0,sizeof(*g));g->rng=seed;g->res=1000;g->lane=1;g->x=g->from_x=120;g->next=30;
}

int adv_night_target(const adv_night_t *g)
{
    int found=-1,best=INT_MAX;
    for(int i=0;i<ADV_NIGHT_CAP;i++){
        const adv_night_bug_t *e=&g->bugs[i];if(!e->type)continue;
        int dx=e->x-(g->x+ADV_NIGHT_JAR_DX)*60,dy=(adv_night_object_y(e)-ADV_NIGHT_JAR_Y)*60;
        if(abs(dx)>ADV_NIGHT_RX*60||abs(dy)>ADV_NIGHT_RY*60)continue;
        int d=dx*dx*ADV_NIGHT_RY*ADV_NIGHT_RY+dy*dy*ADV_NIGHT_RX*ADV_NIGHT_RX;
        if(d<=ADV_NIGHT_RX*ADV_NIGHT_RX*ADV_NIGHT_RY*ADV_NIGHT_RY*3600&&d<best){found=i;best=d;}
    }
    return found;
}

static void spawn(adv_night_t *g)
{
    adv_night_bug_t *e=NULL;
    for(int i=0;i<ADV_NIGHT_CAP;i++)if(!g->bugs[i].type){e=&g->bugs[i];break;}
    if(!e){g->spawn_blocked++;return;}
    int type=adv_rand(&g->rng)%100<moth_percent(g)?NIGHT_MOTH:NIGHT_FIREFLY;
    int dir=adv_rand(&g->rng)%2?1:-1;
    int base_y=range(g,ADV_NIGHT_JAR_Y-10,ADV_NIGHT_JAR_Y+10);
    int phase=(int)(adv_rand(&g->rng)%64);
    *e=(adv_night_bug_t){type,(dir>0?-12:252)*60,base_y,dir,phase,0};
}

void adv_night_step(adv_night_t *g,const adv_input_t *input)
{
    g->tick++;g->cue=0;
    int32_t *timers[]={&g->cast,&g->cooldown,&g->good,&g->bad,&g->feedback};
    for(unsigned i=0;i<sizeof(timers)/sizeof(*timers);i++)if(*timers[i]>0)(*timers[i])--;
    if(g->over)return;
    bool pressed=input->ok_down&&!g->cooldown;int hit=pressed?adv_night_target(g):-1;
    int caught_x=hit<0?0:g->bugs[hit].x/60,caught_y=hit<0?0:adv_night_object_y(&g->bugs[hit]);
    if(!!input->up_down!=!!input->down_down){
        int lane=g->lane+(input->up_down?-1:1);if(lane<0)lane=0;if(lane>2)lane=2;
        if(lane!=g->lane){g->lane=lane;g->from_x=g->x;g->move=ADV_NIGHT_MOVE;g->move_dir=input->up_down?-1:1;g->cue=1;}
    }
    if(g->move){int elapsed=ADV_NIGHT_MOVE-g->move+1;g->x=g->from_x+(POS[g->lane]-g->from_x)*elapsed/ADV_NIGHT_MOVE;g->move--;if(!g->move)g->x=POS[g->lane];}
    g->drain_acc+=25;while(g->drain_acc>=60){g->res--;g->drain_acc-=60;}
    if(--g->next<=0){spawn(g);int delay=g->score>=128?180:(int)g->score*3/4;g->next=range(g,84,100)+delay;if(g->next>180)g->next=180;}
    int velocity=adv_night_speed(g);
    for(int i=0;i<ADV_NIGHT_CAP;i++){
        adv_night_bug_t *e=&g->bugs[i];if(!e->type)continue;
        e->age++;e->x+=e->dir*velocity;if(e->x< -24*60||e->x>264*60)memset(e,0,sizeof(*e));
    }
    if(pressed){
        g->cast=ADV_NIGHT_CAST;g->cooldown=ADV_NIGHT_COOLDOWN;g->feedback=60;
        if(hit<0){g->message=1;g->misses++;g->cue=7;}
        else{
            adv_night_bug_t *e=&g->bugs[hit];g->caught_x=caught_x;g->caught_y=caught_y;
            if(e->type==NIGHT_FIREFLY){if(g->score!=UINT32_MAX)g->score++;g->res+=60;if(g->res>1000)g->res=1000;g->good=60;g->bad=0;g->message=2;g->cue=6;}
            else{g->res-=250;g->bad=60;g->good=0;g->message=3;g->cue=7;}
            memset(e,0,sizeof(*e));
        }
    }
    if(g->res<=0){g->res=0;g->over=1;g->cue=8;}
}

static void start_game(void *state,uint32_t seed){adv_night_start(state,seed);}
static void step_game(void *state,const adv_input_t *input){adv_night_step(state,input);}
static adv_status_t status_game(const void *state){const adv_night_t *g=state;return (adv_status_t){g->score,g->res,g->over!=0,(uint8_t)g->cue};}
const adv_game_t adv_night_game={"night",sizeof(adv_night_t),start_game,step_game,status_game};
