#pragma once
// SPACE V2 rocket-to-Moon. Integer 60 Hz reference: prototype/adv_space.js.
// Q8 positions/velocities; objects' altitude is in px. Left OK, middle DOWN, right UP.
#include "adv_game.h"
#define ADV_SPACE_OBJS 24
#define ADV_SPACE_FX 6
#define ADV_SPACE_RY 176
#define ADV_SPACE_Z1 4000
#define ADV_SPACE_Z2 8000
#define ADV_SPACE_Z3 14000
#define ADV_SPACE_Z4 19000
#define ADV_SPACE_GROUND 206
#define ADV_SPACE_PAD_HALF 34
#define ADV_SPACE_SAFE_VY 260
#define ADV_SPACE_FUEL_MAX 100000
#define ADV_SPACE_IGN_T 300
#define ADV_SPACE_SEP_T 96
#define ADV_SPACE_TLI_LEAD 50
#define ADV_SPACE_TLI_BEAT 32
enum { SPACE_BIRDS=1,SPACE_PLANE,SPACE_BALLOON,SPACE_STORM,SPACE_GUST,SPACE_STAR,SPACE_FUEL,
       SPACE_RING,SPACE_JET,SPACE_SAT,SPACE_JUNK,SPACE_ROCK,SPACE_METEOR,SPACE_COMET,SPACE_REPAIR };
enum { SPACE_IGNITE,SPACE_FLY,SPACE_LAND,SPACE_ENDING,SPACE_LOST };
enum { SPACE_FX_HIT=1,SPACE_FX_STAR,SPACE_FX_FUEL,SPACE_FX_NEAR,SPACE_FX_RING,SPACE_FX_TIMING,
       SPACE_FX_ZONE,SPACE_FX_OVERHEAT,SPACE_FX_LANDED,SPACE_FX_CRASH,SPACE_FX_REPAIR,SPACE_FX_SEP,SPACE_FX_SMASH };
typedef struct { int32_t type,x,y,vx,state,done; } adv_space_obj_t;
typedef struct { int32_t kind,x,y,val,t; } adv_space_fx_t;
typedef struct {
    uint32_t rng,tick,score;
    int32_t res,over,cue,mode,modeT,win,alt,v,vTarget,x,vx,fuel,hull,heat,boostT,lastBoost,invuln,
        ign,ignScore,sep,sepT,sepQ,tli,tliT,tliHit,tliQ,zoneSeen,combo,best,stars,near,hits,perfects,
        rings,cans,bonus,nextObj,push,lx,ly,lvx,lvy,pad,landings,presses,blocked,fxHead;
    adv_space_obj_t objs[ADV_SPACE_OBJS];
    adv_space_fx_t fx[ADV_SPACE_FX];
} adv_space_t;
void adv_space_start(adv_space_t *g,uint32_t seed);
void adv_space_step(adv_space_t *g,const adv_input_t *in);
int adv_space_mult(const adv_space_t *g);
int adv_space_gauge(int t);
int adv_space_zone(int altitude);
extern const adv_game_t adv_space_game;
