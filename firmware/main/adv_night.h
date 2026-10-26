#pragma once
// NIGHT V2「萤火虫之夜」rules, integer 60 Hz. Reference: game-art/adventure/prototype/adv_night_v2.js
// (step-by-step goldens in tests/night_golden). Landscape: OK holds slow, DOWN swings (double tap
// = burst when the meter is full), UP holds run. World x is Q8 px; light is resource x 1000.
#include "adv_game.h"

#define ADV_NIGHT_W 320
#define ADV_NIGHT_GROUND 200
#define ADV_NIGHT_FLIES 40
#define ADV_NIGHT_MOTHS 12
#define ADV_NIGHT_ROOTS 6
#define ADV_NIGHT_OWLS 4
#define ADV_NIGHT_FX 6
#define ADV_NIGHT_LIGHT_MAX 1000000
#define ADV_NIGHT_SWING 18
#define ADV_NIGHT_SWING_ON 3
#define ADV_NIGHT_SWING_OFF 12
#define ADV_NIGHT_NET_DX 20
#define ADV_NIGHT_NET_DY 42
#define ADV_NIGHT_NET_R 31
#define ADV_NIGHT_MOTH_R 24
#define ADV_NIGHT_DOUBLE 16
#define ADV_NIGHT_TRIP_STUN 54
#define ADV_NIGHT_OWL_WARN 96

enum { NIGHT_EV_NONE, NIGHT_EV_SWARM, NIGHT_EV_OWLS, NIGHT_EV_WIND };
enum { NIGHT_FX_FLY = 1, NIGHT_FX_GOLD, NIGHT_FX_MULTI, NIGHT_FX_MOTH, NIGHT_FX_TRIP, NIGHT_FX_OWL, NIGHT_FX_NEAR, NIGHT_FX_BURST, NIGHT_FX_EVENT };
enum { NIGHT_LOSS_DECAY, NIGHT_LOSS_RUN, NIGHT_LOSS_WHIFF, NIGHT_LOSS_MOTH, NIGHT_LOSS_TRIP, NIGHT_LOSS_OWL, NIGHT_LOSS_N };

typedef struct { int32_t type, x, base_y, amp, ph, freq, vx; } adv_night_fly_t;     // type 1 firefly, 2 gold
typedef struct { int32_t host, x, y, a, rr, va; } adv_night_moth_t;                    // alive when rr != 0; host = fly slot + 1
typedef struct { int32_t x, w, state; } adv_night_root_t;                              // state 1 live, 2 tripped, 3 passed
typedef struct { int32_t tx, t, live; } adv_night_owl_t;                               // dives when t reaches 0
typedef struct { int32_t kind, x, y, val, t; } adv_night_fx_t;

typedef struct {
    uint32_t rng, tick, score;
    int32_t res, over, cue, light, x, screen, gait, stun, stun_kind, swing, swing_caught, last_swing, burst, combo, caught,
        meter, bursts, event, event_t, next_group, next_root, next_owl, last_loss, max_combo, whiffs, trips, owl_hits,
        owl_near, moth_hits, missed, golds, multi, swings, presses, roots_passed, blocked, fx_head;
    int32_t loss[NIGHT_LOSS_N];
    adv_night_fly_t flies[ADV_NIGHT_FLIES];
    adv_night_moth_t moths[ADV_NIGHT_MOTHS];
    adv_night_root_t roots[ADV_NIGHT_ROOTS];
    adv_night_owl_t owls[ADV_NIGHT_OWLS];
    adv_night_fx_t fx[ADV_NIGHT_FX];
} adv_night_t;

void adv_night_start(adv_night_t *g, uint32_t seed);
void adv_night_step(adv_night_t *g, const adv_input_t *in);
int adv_night_isin(int i);
int adv_night_fly_y(const adv_night_fly_t *f, uint32_t tick);
int adv_night_radius(const adv_night_t *g);
int adv_night_mult(const adv_night_t *g);
int adv_night_meter_full(const adv_night_t *g);
static inline int32_t adv_night_cam(const adv_night_t *g) { return g->x - g->screen; }
extern const adv_game_t adv_night_game;
