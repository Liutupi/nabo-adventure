#pragma once
// Pure 60 Hz SKY rules. Reference: prototype/adv_sky.js. Altitude/distance are px*16; y up.
#include "adv_game.h"

#define ADV_SKY_CAP 10
#define ADV_SKY_CEIL 1200
#define ADV_SKY_LIFT 3
#define ADV_SKY_SINK 2
#define ADV_SKY_VMAX 40
#define ADV_SKY_HEAT_DRAIN 60
#define ADV_SKY_SPEED0 24
#define ADV_SKY_SPEED_MAX 56
#define ADV_SKY_SPAWN_X 260
#define ADV_SKY_GONE_X (-90)
#define ADV_SKY_INVULN 60
#define ADV_SKY_ENV_Y 141
#define ADV_SKY_ENV_RX 44
#define ADV_SKY_ENV_RY 46
#define ADV_SKY_BASKET_X 32
#define ADV_SKY_BASKET_LO (-22)
#define ADV_SKY_BASKET_HI 8
#define ADV_SKY_WARM_W 36
#define ADV_SKY_WARM_H 18
#define ADV_SKY_HIT 250
#define ADV_SKY_GROUND 250
#define ADV_SKY_WARM 200
#define ADV_SKY_STAMP 10

enum { SKY_BIRD = 1, SKY_STORM, SKY_STAMP, SKY_WARM };
enum { SKY_MSG_NONE, SKY_MSG_BIRD, SKY_MSG_STORM, SKY_MSG_STAMP, SKY_MSG_WARM, SKY_MSG_GROUND };

typedef struct { int32_t type, x, alt, phase, done; } adv_sky_obj_t;
typedef struct {
    uint32_t rng, tick, score;
    int32_t res, over, cue, alt, vy, dist, speed, heating, invuln, drain_acc, next_spawn, bonus, message, feedback;
    int32_t hits, grounds, stamps, warms, blocked;
    adv_sky_obj_t objs[ADV_SKY_CAP];
} adv_sky_t;

void adv_sky_start(adv_sky_t *g, uint32_t seed);
void adv_sky_step(adv_sky_t *g, const adv_input_t *input);
int adv_sky_object_alt(const adv_sky_obj_t *o);
extern const adv_game_t adv_sky_game;
