#pragma once
// Pure 60 Hz SPACE rules. Reference: prototype/adv_space.js. Screen px, y down; position 1/256 px,
// velocity 1/256 px per frame. OK = main engine, held UP/DOWN = side thrusters (the art cannot rotate).
#include "adv_game.h"

#define ADV_SPACE_GROUND 270
#define ADV_SPACE_TOP_Y 132
#define ADV_SPACE_LEFT 48
#define ADV_SPACE_RIGHT 192
#define ADV_SPACE_HOLD 6
#define ADV_SPACE_GRAVITY 5
#define ADV_SPACE_THRUST 12
#define ADV_SPACE_SIDE 6
#define ADV_SPACE_VMAX 1024
#define ADV_SPACE_MAIN_DRAIN 90
#define ADV_SPACE_SIDE_DRAIN 40
#define ADV_SPACE_SAFE_VY 300
#define ADV_SPACE_SAFE_VX 160
#define ADV_SPACE_LANDED 150
#define ADV_SPACE_CRASH 72
#define ADV_SPACE_CAN 300
#define ADV_SPACE_HIT 250
#define ADV_SPACE_OBJS 3
#define ADV_SPACE_FEET 39
#define ADV_SPACE_BODY_TOP 80

enum { SPACE_FUEL = 1, SPACE_ROCK };
enum { SPACE_FLY, SPACE_LANDED, SPACE_CRASH };
enum { SPACE_MSG_NONE, SPACE_MSG_LANDED, SPACE_MSG_HARD, SPACE_MSG_MISSED, SPACE_MSG_ROCK, SPACE_MSG_FUEL };

typedef struct { int32_t type, x, y, vx; } adv_space_obj_t;
typedef struct {
    uint32_t rng, tick, score;
    int32_t res, over, cue, round, landings, crashes, cans, phase, timer, x, y, vx, vy, pad, thrust, side, drain_acc;
    int32_t left_hold, right_hold, short_taps, down_taps, message, feedback, last_bonus;
    adv_space_obj_t objs[ADV_SPACE_OBJS];
} adv_space_t;

void adv_space_start(adv_space_t *g, uint32_t seed);
void adv_space_step(adv_space_t *g, const adv_input_t *input);
void adv_space_up_event(adv_space_t *g, bool pressed);
void adv_space_down_event(adv_space_t *g, bool pressed);
int adv_space_zone(const adv_space_t *g);
extern const adv_game_t adv_space_game;
