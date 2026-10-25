#pragma once
// Pure 60 Hz SKI rules. Reference: prototype/adv_ski.js. World y grows ahead of NABO in px; x is 1/16 px.
#include "adv_game.h"

#define ADV_SKI_CAP 16
#define ADV_SKI_LEFT 24
#define ADV_SKI_RIGHT 216
#define ADV_SKI_AHEAD 340
#define ADV_SKI_BEHIND 80
#define ADV_SKI_HOLD 6
#define ADV_SKI_AIR 34
#define ADV_SKI_FALL 48
#define ADV_SKI_BUMP_T 24
#define ADV_SKI_INVULN 40
#define ADV_SKI_ACCEL 5
#define ADV_SKI_VMAX 40
#define ADV_SKI_SPEED0 40
#define ADV_SKI_SPEED_STEP 2
#define ADV_SKI_SPEED_MAX 96
#define ADV_SKI_DRAIN 15
#define ADV_SKI_GATE_HALF 24
#define ADV_SKI_MISS 100
#define ADV_SKI_TREE 250
#define ADV_SKI_BUMP 100
#define ADV_SKI_COCOA 300

enum { SKI_GATE_RED = 1, SKI_GATE_BLUE, SKI_TREE, SKI_PINE, SKI_MOGUL, SKI_CABIN };
enum { SKI_MSG_NONE, SKI_MSG_PASS, SKI_MSG_MISS, SKI_MSG_TREE, SKI_MSG_BUMP, SKI_MSG_COCOA };

typedef struct { int32_t type, x, y, done; } adv_ski_obj_t;
typedef struct {
    uint32_t rng, tick, score;
    int32_t res, over, cue, x, vx, pos, speed, air, fall, invuln, drain_acc, left_hold, right_hold, short_taps;
    int32_t next_gate, next_hazard, last_gate_x, gates, cabin_wait, message, feedback, misses, crashes, bumps, cocoa, blocked, sub;
    adv_ski_obj_t objs[ADV_SKI_CAP];
} adv_ski_t;

void adv_ski_start(adv_ski_t *g, uint32_t seed);
void adv_ski_step(adv_ski_t *g, const adv_input_t *input);
void adv_ski_up_event(adv_ski_t *g, bool pressed);
extern const adv_game_t adv_ski_game;
