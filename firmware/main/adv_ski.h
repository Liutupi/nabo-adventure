#pragma once
// SKI V2「雪崩速降」rules, integer 60 Hz. Reference: game-art/adventure/prototype/adv_ski.js (step-by-step
// goldens in tests/ski_golden). Landscape: OK holds carve left, UP holds carve right, DOWN jumps (spins in
// the air after a kicker). World y is Q8 px downhill; x is Q8 screen px. An avalanche chases from above.
#include "adv_game.h"

#define ADV_SKI_NABO_Y 92
#define ADV_SKI_LEFT 18
#define ADV_SKI_RIGHT 302
#define ADV_SKI_OBJS 28
#define ADV_SKI_FX 6
#define ADV_SKI_ICE_HALF 34
#define ADV_SKI_ICE_LEN 60
#define ADV_SKI_SPIN 22
#define ADV_SKI_CRASH 36
#define ADV_SKI_AVAL_CAP 300
#define ADV_SKI_FLOW_MAX 520

enum { SKI_GATE_RED = 1, SKI_GATE_BLUE, SKI_TREE, SKI_PINE, SKI_MOGUL, SKI_KICKER, SKI_ICE, SKI_DRIFT };
enum { SKI_SEC_NONE, SKI_SEC_SLALOM, SKI_SEC_FOREST, SKI_SEC_PARK, SKI_SEC_ICE, SKI_SEC_FOG };
enum { SKI_FX_GATE = 1, SKI_FX_MISS, SKI_FX_CRASH, SKI_FX_STUMBLE, SKI_FX_SPIN, SKI_FX_LAND, SKI_FX_WIPE, SKI_FX_SECTION, SKI_FX_KICK, SKI_FX_NEAR };

typedef struct { int32_t type, x, y, done; } adv_ski_obj_t;       // x, y in px; y is the object's base line
typedef struct { int32_t kind, x, y, val, t; } adv_ski_fx_t;

typedef struct {
    uint32_t rng, tick, score;
    int32_t res, over, cue, x, vx, y, v, air, air_max, kicked, spin_t, spins, crash, invuln, aval, combo, best, gates, passed,
        misses, tricks, flow, crashes, stumbles, near_miss, next_gate, next_row, last_gate_x, section, section_t, on_ice, meters,
        bonus, presses, blocked, fx_head;
    adv_ski_obj_t objs[ADV_SKI_OBJS];
    adv_ski_fx_t fx[ADV_SKI_FX];
} adv_ski_t;

void adv_ski_start(adv_ski_t *g, uint32_t seed);
void adv_ski_step(adv_ski_t *g, const adv_input_t *in);
int adv_ski_mult(const adv_ski_t *g);
static inline int32_t adv_ski_gap(const adv_ski_t *g) { return g->y - g->aval; }
extern const adv_game_t adv_ski_game;
