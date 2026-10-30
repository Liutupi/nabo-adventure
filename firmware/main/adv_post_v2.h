#pragma once
// Approved V2 rules: prototype/adv_post_v2.js. Integer 60 Hz; no platform dependencies.
#include "adv_game.h"
#define POST_V2_W (320)
#define POST_V2_H (240)
#define POST_V2_RAIL (196)
#define POST_V2_LOCO_X (150)
#define POST_V2_DOOR_X (120)
#define POST_V2_FRONT_X (196)
#define POST_V2_VMAX (1024)
#define POST_V2_ACC (7)
#define POST_V2_BRAKE (18)
#define POST_V2_DRAG (1)
#define POST_V2_V0 (300)
#define POST_V2_WINDOW (14)
#define POST_V2_PERFECT (4)
#define POST_V2_COOL (10)
#define POST_V2_BAGS0 (3)
#define POST_V2_BAGS_MAX (5)
#define POST_V2_TIME_NET (85)
#define POST_V2_TIME_PERFECT (30)
#define POST_V2_TIME_CRANE (25)
#define POST_V2_TIME_SKIP (40)
#define POST_V2_TIME_RED (160)
#define POST_V2_TIME_DERAIL (180)
#define POST_V2_TIME_ANIMAL (130)
#define POST_V2_TIME_WASTE (20)
#define POST_V2_DRAIN (28)
#define POST_V2_DRAIN_RAMP (1800)
#define POST_V2_DRAIN_MAX (14)
#define POST_V2_PTS (10)
#define POST_V2_CRANE_PTS (15)
#define POST_V2_SLOW (260)
#define POST_V2_OVER_GRACE (24)
#define POST_V2_STUN (50)
#define POST_V2_EVENTS (16)
#define POST_V2_AHEAD (380)
#define POST_V2_CULL (-80)
#define POST_V2_CALM (900)
#define POST_V2_EVERY (1500)
#define POST_V2_SECTION_LEN (900)
enum { POST_V2_T_NET = 1, POST_V2_T_CRANE = 2, POST_V2_T_LIMIT = 3, POST_V2_T_SIGNAL = 4, POST_V2_T_ANIMAL = 5 };
enum { POST_V2_SEC_NONE = 0, POST_V2_SEC_TOWN = 1, POST_V2_SEC_HILLS = 2, POST_V2_SEC_FARM = 3, POST_V2_SEC_NIGHT = 4, POST_V2_SEC_DOWNHILL = 5 };
enum { POST_V2_FX_NET = 1, POST_V2_FX_PERFECT = 2, POST_V2_FX_CRANE = 3, POST_V2_FX_WASTE = 4, POST_V2_FX_SKIP = 5, POST_V2_FX_RED = 6, POST_V2_FX_DERAIL = 7, POST_V2_FX_ANIMAL = 8, POST_V2_FX_SECTION = 9, POST_V2_FX_OVER = 10, POST_V2_FX_NEAR = 11, POST_V2_FX_TIER = 12 };
typedef struct { int32_t kind,x,y,val,t; } adv_post_v2_fx_t;
typedef struct { int32_t type,x,a,b,t,done; } adv_post_v2_event_t;
typedef struct {
    uint32_t rng,tick,score;
    int32_t res,over,cue,v,dist,bags,cool,stun,braking,steaming,combo,best,bonus,drainAcc,over_t,zone,tier,delivered,perfects,cranes,wasted,skipped,reds,derails,animals,nearMiss,nets,section,sectionT,nextEvent,presses,blocked,fxHead,meters,topSpeedT;
    adv_post_v2_event_t ev[POST_V2_EVENTS];
    adv_post_v2_fx_t fx[6];
} adv_post_v2_t;
void adv_post_v2_start(adv_post_v2_t *g,uint32_t seed);
void adv_post_v2_step(adv_post_v2_t *g,const adv_input_t *input);
extern const adv_game_t adv_post_v2_game;
