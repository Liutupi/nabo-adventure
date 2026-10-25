#pragma once
// Pure 60 Hz CLIMB rules. Reference: prototype/adv_climb.js. World y grows upward in px.
#include "adv_game.h"

#define ADV_CLIMB_ROW 40
#define ADV_CLIMB_RING 32
#define ADV_CLIMB_AHEAD 12
#define ADV_CLIMB_FLOOR 28
#define ADV_CLIMB_ROCKS 4
#define ADV_CLIMB_TAP 12
#define ADV_CLIMB_CHARGE3 40
#define ADV_CLIMB_SWITCH 24
#define ADV_CLIMB_JUMP 30
#define ADV_CLIMB_SLIDE 30
#define ADV_CLIMB_FRAGILE 60
#define ADV_CLIMB_INVULN 60
#define ADV_CLIMB_CHEER 48
#define ADV_CLIMB_DRAIN 30
#define ADV_CLIMB_ICE_DRAIN 60
#define ADV_CLIMB_GAIN 20
#define ADV_CLIMB_CANTEEN 250
#define ADV_CLIMB_HIT 250
#define ADV_CLIMB_MISS 100
#define ADV_CLIMB_ROCK_V 3
#define ADV_CLIMB_ROCK_START 8
#define ADV_CLIMB_ROCK_SPAWN 9
#define ADV_CLIMB_BODY_LO 41
#define ADV_CLIMB_BODY_HI 21
#define ADV_CLIMB_ROCK_H 24

enum { CLIMB_NONE, CLIMB_NORMAL, CLIMB_FRAGILE, CLIMB_ICE };
enum { CLIMB_IDLE, CLIMB_SWITCH, CLIMB_JUMP, CLIMB_SLIDE };
enum { CLIMB_MSG_NONE, CLIMB_MSG_MISS, CLIMB_MSG_HIT, CLIMB_MSG_CRUMBLE, CLIMB_MSG_CANTEEN, CLIMB_MSG_MILESTONE };

typedef struct { int32_t on, side, y; } adv_climb_rock_t;
typedef struct {
    uint32_t rng, tick, score;
    int32_t res, over, cue, row, side, act, act_t, act_len, from_row, from_side, to_row, to_side;
    int32_t press, queue, fragile_t, drain_acc, gen_top, canteen_next, rock_next, invuln, cheer, message, feedback;
    int32_t hits, misses, crumbles, canteens;
    uint8_t grid[ADV_CLIMB_RING];  // bits0-1 left hold, 2-3 right hold, 4 left canteen, 5 right canteen
    adv_climb_rock_t rocks[ADV_CLIMB_ROCKS];
} adv_climb_t;

void adv_climb_start(adv_climb_t *g, uint32_t seed);
void adv_climb_step(adv_climb_t *g, const adv_input_t *input);
int adv_climb_hold(const adv_climb_t *g, int row, int side);
bool adv_climb_canteen(const adv_climb_t *g, int row, int side);
int adv_climb_hand_y(const adv_climb_t *g);
int adv_climb_body_side(const adv_climb_t *g);
extern const adv_game_t adv_climb_game;
