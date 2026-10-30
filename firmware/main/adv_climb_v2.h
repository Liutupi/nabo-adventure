#pragma once
// Approved V2 rules: prototype/adv_climb_v2.js. Integer 60 Hz; no platform dependencies.
#include "adv_game.h"
#define CLIMB_V2_W (320)
#define CLIMB_V2_H (240)
#define CLIMB_V2_NY (150)
#define CLIMB_V2_STEP (26)
// LANE_X: [104, 216]
#define CLIMB_V2_HOLD_DX (23)
#define CLIMB_V2_ROWS (32)
#define CLIMB_V2_AHEAD (14)
#define CLIMB_V2_TWEEN (6)
#define CLIMB_V2_RHYTHM (24)
#define CLIMB_V2_COMBO_IDLE (70)
#define CLIMB_V2_STUN (18)
#define CLIMB_V2_TRAVERSE (14)
#define CLIMB_V2_ICE_HOLD (15)
#define CLIMB_V2_CRUMBLE (42)
#define CLIMB_V2_DRAIN (28)
#define CLIMB_V2_DRAIN_ROWS (8)
#define CLIMB_V2_DRAIN_MAX (40)
#define CLIMB_V2_GAIN (22)
#define CLIMB_V2_GAIN_RHYTHM (26)
#define CLIMB_V2_SLIP (90)
#define CLIMB_V2_ROCK_HIT (170)
#define CLIMB_V2_TRAV_COST (10)
#define CLIMB_V2_GAIN_MIN (8)
#define CLIMB_V2_GAIN_FADE (16)
#define CLIMB_V2_CANTEEN (260)
#define CLIMB_V2_FLAG (30)
#define CLIMB_V2_INVULN (50)
#define CLIMB_V2_ROCKS (3)
#define CLIMB_V2_ROCK_WARN (75)
#define CLIMB_V2_ROCK_V (5)
#define CLIMB_V2_ROCK_TOP (-16)
#define CLIMB_V2_CALM (900)
#define CLIMB_V2_EVERY (1500)
#define CLIMB_V2_SECTION_LEN (900)
enum { CLIMB_V2_H_BLANK = 0, CLIMB_V2_H_NORMAL = 1, CLIMB_V2_H_FRAGILE = 2, CLIMB_V2_H_ICE = 3 };
enum { CLIMB_V2_ITEM_NONE = 0, CLIMB_V2_ITEM_CANTEEN = 1, CLIMB_V2_ITEM_FLAG = 2 };
enum { CLIMB_V2_SEC_NONE = 0, CLIMB_V2_SEC_ROCKS = 1, CLIMB_V2_SEC_ICE = 2, CLIMB_V2_SEC_CRUMBLE = 3, CLIMB_V2_SEC_NIGHT = 4, CLIMB_V2_SEC_SPRINT = 5 };
enum { CLIMB_V2_FX_GRAB = 1, CLIMB_V2_FX_SLIP = 2, CLIMB_V2_FX_ROCK = 3, CLIMB_V2_FX_CANTEEN = 4, CLIMB_V2_FX_FLAG = 5, CLIMB_V2_FX_SECTION = 6, CLIMB_V2_FX_NEAR = 7, CLIMB_V2_FX_NOHOLD = 8, CLIMB_V2_FX_CRUMBLE = 9, CLIMB_V2_FX_TRAVERSE = 10, CLIMB_V2_FX_RHYTHM = 11 };
typedef struct { int32_t kind,x,y,val,t; } adv_climb_v2_fx_t;
typedef struct { int32_t h0,h1,i0,i1; } adv_climb_v2_row_t;
typedef struct { int32_t on,lane,t,y,n; } adv_climb_v2_rock_t;
typedef struct {
    uint32_t rng,tick,score;
    int32_t res,over,cue,row,lane,tween,stun,trav,ice,iceSide,crumble,invuln,lastGrab,combo,best,bonus,drainAcc,genRow,grabs,rhythmGrabs,slips,rockHits,nearMiss,canteens,flags,traverses,crumbles,iceSlips,section,sectionT,nextRock,presses,fxHead,meters;
    int32_t blankRun[2];
    adv_climb_v2_row_t rows[CLIMB_V2_ROWS];
    adv_climb_v2_rock_t rocks[CLIMB_V2_ROCKS];
    adv_climb_v2_fx_t fx[6];
} adv_climb_v2_t;
void adv_climb_v2_start(adv_climb_v2_t *g,uint32_t seed);
void adv_climb_v2_step(adv_climb_v2_t *g,const adv_input_t *input);
extern const adv_game_t adv_climb_v2_game;
