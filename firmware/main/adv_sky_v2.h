#pragma once
// Approved V2 rules: prototype/adv_sky_v2.js. Integer 60 Hz; no platform dependencies.
#include "adv_game.h"
#define SKY_V2_W (320)
#define SKY_V2_H (240)
#define SKY_V2_BX (92)
#define SKY_V2_YMIN (104)
#define SKY_V2_YMAX (204)
#define SKY_V2_GROUND (214)
#define SKY_V2_Y0 (150)
// LAYER: [128, 160, 186]
// SPEEDS: [230, 340, 450, 560]
#define SKY_V2_HEAT (15)
#define SKY_V2_VENT (20)
#define SKY_V2_SINK (5)
#define SKY_V2_DAMP (12)
#define SKY_V2_VMAX (440)
#define SKY_V2_DRAIN (9)
#define SKY_V2_DRAIN_HEAT (15)
#define SKY_V2_LETTERS (4)
#define SKY_V2_COOLDOWN (16)
#define SKY_V2_GRAV (22)
#define SKY_V2_LETTER_VMAX (900)
#define SKY_V2_BOX_HALF (10)
#define SKY_V2_BULL (3)
#define SKY_V2_HIGH_DROP (70)
#define SKY_V2_PTS (10)
#define SKY_V2_GOLD (3)
#define SKY_V2_TIP (30)
#define SKY_V2_TIP_GOLD (100)
#define SKY_V2_TANK (180)
#define SKY_V2_DRAIN_RAMP (1200)
#define SKY_V2_HIT_TREE (120)
#define SKY_V2_HIT_BIRD (100)
#define SKY_V2_HIT_STORM (150)
#define SKY_V2_HIT_GROUND (60)
#define SKY_V2_INVULN (70)
#define SKY_V2_ENV_DY (58)
#define SKY_V2_ENV_R (29)
#define SKY_V2_BASKET_HALF (15)
#define SKY_V2_BASKET_H (16)
#define SKY_V2_OBJS (24)
#define SKY_V2_AHEAD (360)
#define SKY_V2_CULL (-60)
#define SKY_V2_CALM (900)
#define SKY_V2_EVERY (1500)
#define SKY_V2_SECTION_LEN (900)
#define SKY_V2_STORM_CYCLE (230)
#define SKY_V2_STORM_WARN (150)
#define SKY_V2_STORM_BOLT (200)
#define SKY_V2_STORM_END (222)
#define SKY_V2_BOLT_HALF (7)
#define SKY_V2_STORM_HALF (26)
#define SKY_V2_BOLT_LEN (62)
#define SKY_V2_STORM_H (12)
#define SKY_V2_MISS_COST (25)
enum { SKY_V2_T_HOUSE = 1, SKY_V2_T_TREE = 2, SKY_V2_T_BIRD = 3, SKY_V2_T_STORM = 4, SKY_V2_T_TANK = 5 };
enum { SKY_V2_SEC_NONE = 0, SKY_V2_SEC_TOWN = 1, SKY_V2_SEC_BIRDS = 2, SKY_V2_SEC_STORM = 3, SKY_V2_SEC_RAINBOW = 4, SKY_V2_SEC_GUST = 5 };
enum { SKY_V2_FX_DELIVER = 1, SKY_V2_FX_BULL = 2, SKY_V2_FX_MISS = 3, SKY_V2_FX_SKIP = 4, SKY_V2_FX_HIT = 5, SKY_V2_FX_TANK = 6, SKY_V2_FX_SECTION = 7, SKY_V2_FX_NEAR = 8, SKY_V2_FX_GROUND = 9, SKY_V2_FX_WIND = 10 };
typedef struct { int32_t kind,x,y,val,t; } adv_sky_v2_fx_t;
typedef struct { int32_t type,x,y,v,t,done,n; } adv_sky_v2_obj_t;
typedef struct { int32_t on,x,y,vx,vy,y0; } adv_sky_v2_letter_t;
typedef struct {
    uint32_t rng,tick,score;
    int32_t res,over,cue,y,vy,dist,spd,layer,heating,venting,drainAcc,invuln,cool,combo,best,bonus,delivered,bulls,golds,skipped,missDrops,drops,hits,tanks,nearMiss,grounds,section,sectionT,nextGround,nextSky,houses,presses,blocked,fxHead,meters;
    int32_t order[4];
    adv_sky_v2_obj_t objs[SKY_V2_OBJS];
    adv_sky_v2_letter_t letters[SKY_V2_LETTERS];
    adv_sky_v2_fx_t fx[6];
} adv_sky_v2_t;
void adv_sky_v2_start(adv_sky_v2_t *g,uint32_t seed);
void adv_sky_v2_step(adv_sky_v2_t *g,const adv_input_t *input);
extern const adv_game_t adv_sky_v2_game;
