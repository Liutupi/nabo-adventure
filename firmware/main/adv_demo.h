#pragma once
// Placeholder game for stations whose real game is not written yet: a marker sweeps a track,
// OK inside the zone scores and refills the bar, OK outside costs a quarter. Same rules as
// Demo in game-art/adventure/prototype/adv_core.js.
#include "adv_game.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t rng;
    int p, v, zc, zh;           // marker 0..1000 and its speed, zone centre and half width
    uint32_t score;
    int res;
    uint8_t over, hit, miss, cue;
} adv_demo_t;

extern const adv_game_t adv_demo_game;

#ifdef __cplusplus
}
#endif
