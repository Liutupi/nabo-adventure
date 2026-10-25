#include "adv_night.h"
#include "adv_rng.h"
#include <limits.h>
#include <stdlib.h>
#include <string.h>

static const int POS[]={54,160,266};
static int range(adv_night_t *g,int lo,int hi){return lo+(int)(adv_rand(&g->rng)%(unsigned)(hi-lo+1));}
int adv_night_interval(const adv_night_t *g){return g->score>=56?204:120+(int)g->score*3/2;}
static unsigned moth_percent(const adv_night_t *g){return g->score>=60?20:8+g->score/5;}
int adv_night_object_y(const adv_night_bug_t *e)
{int q=(e->age+e->phase)%64,v=q<32?q:64-q;return e->base_y+v*16/32-8;}
static int object_x(const adv_night_bug_t *e)
{int q=(e->age+e->phase)%48,v=q<24?q:48-q;return (POS[e->lane]+ADV_NIGHT_JAR_DX+v*20/24-10)*60;}

void adv_night_start(adv_night_t *g,uint32_t seed)
{
    memset(g,0,sizeof(*g));g->rng=seed;g->res=1000;g->lane=1;g->x=g->from_x=160;g->next=45;g->last_lane=-1;
}
void adv_night_up_event(adv_night_t *g,bool pressed)
{
    if(pressed)g->right_hold=0;
    else {g->short_taps=g->right_hold<ADV_NIGHT_HOLD?(g->short_taps<2?g->short_taps+1:2):0;g->right_hold=0;}
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
    if(!g->bag_left){
        static const int orders[]={36,24,33,9,18,6};g->bag=orders[adv_rand(&g->rng)%6];
        if((g->bag&3)==g->last_lane)g->bag=(g->bag&48)|((g->bag&3)<<2)|((g->bag>>2)&3);
        g->bag_left=3;
    }
    int lane=g->bag&3;g->bag>>=2;g->bag_left--;g->last_lane=lane;
    int base_y=range(g,ADV_NIGHT_JAR_Y-8,ADV_NIGHT_JAR_Y+8),phase=(int)(adv_rand(&g->rng)%64);
    *e=(adv_night_bug_t){NIGHT_FIREFLY,0,base_y,lane,phase,0};e->x=object_x(e);
    if(adv_rand(&g->rng)%100<moth_percent(g)){
        adv_night_bug_t *moth=NULL;for(int i=0;i<ADV_NIGHT_CAP;i++)if(!g->bugs[i].type){moth=&g->bugs[i];break;}
        if(moth){
            int y=range(g,ADV_NIGHT_JAR_Y-8,ADV_NIGHT_JAR_Y+8),other=(lane+1+adv_rand(&g->rng)%2)%3;
            int p=(int)(adv_rand(&g->rng)%64);*moth=(adv_night_bug_t){NIGHT_MOTH,0,y,other,p,0};moth->x=object_x(moth);
        }
    }
}

void adv_night_step(adv_night_t *g,const adv_input_t *input)
{
    g->tick++;g->cue=0;
    int32_t *timers[]={&g->cast,&g->cooldown,&g->good,&g->bad,&g->feedback};
    for(unsigned i=0;i<sizeof(timers)/sizeof(*timers);i++)if(*timers[i]>0)(*timers[i])--;
    if(g->over)return;
    bool pressed=input->down_down&&!g->cooldown;int hit=pressed?adv_night_target(g):-1;
    int caught_x=hit<0?0:g->bugs[hit].x/60,caught_y=hit<0?0:adv_night_object_y(&g->bugs[hit]);
    g->left_hold=input->ok_held?(g->left_hold<ADV_NIGHT_HOLD?g->left_hold+1:ADV_NIGHT_HOLD):0;
    g->right_hold=input->up_held?(g->right_hold<ADV_NIGHT_HOLD?g->right_hold+1:ADV_NIGHT_HOLD):0;
    int direction=(g->right_hold>=ADV_NIGHT_HOLD)-(g->left_hold>=ADV_NIGHT_HOLD),old_x=g->x;
    g->from_x=g->x;g->x+=direction*ADV_NIGHT_WALK;if(g->x<POS[0])g->x=POS[0];if(g->x>POS[2])g->x=POS[2];
    g->move=g->x!=old_x?ADV_NIGHT_MOVE-g->tick%ADV_NIGHT_MOVE:0;if(g->move)g->move_dir=direction;
    g->lane=(g->x-POS[0]+53)/106;if(g->lane<0)g->lane=0;if(g->lane>2)g->lane=2;
    g->drain_acc+=25;while(g->drain_acc>=60){g->res--;g->drain_acc-=60;}
    if(--g->next<=0){spawn(g);g->next=adv_night_interval(g)+range(g,0,12);}
    for(int i=0;i<ADV_NIGHT_CAP;i++){
        adv_night_bug_t *e=&g->bugs[i];if(!e->type)continue;
        e->age++;e->x=object_x(e);if(e->age>=ADV_NIGHT_LIFE){if(e->type==NIGHT_FIREFLY)g->escaped++;memset(e,0,sizeof(*e));}
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
