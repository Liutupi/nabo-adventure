#pragma once
// Pure60Hz NIGHT rules. Reference: prototype/adv_night.js. Bug x is1/60px.
#include "adv_game.h"
#define ADV_NIGHT_CAP 8
#define ADV_NIGHT_MOVE 20
#define ADV_NIGHT_CAST 30
#define ADV_NIGHT_COOLDOWN 12
#define ADV_NIGHT_FOOT 280
#define ADV_NIGHT_JAR_DX 10
#define ADV_NIGHT_JAR_Y 227
#define ADV_NIGHT_RX 26
#define ADV_NIGHT_RY 20
enum {NIGHT_FIREFLY=1,NIGHT_MOTH};
typedef struct {int32_t type,x,base_y,dir,phase,age;} adv_night_bug_t;
typedef struct {
    uint32_t rng,tick,score;
    int32_t res,over,lane,x,from_x,move,move_dir,next,drain_acc,cast,cooldown,good,bad,feedback,message,cue,misses,caught_x,caught_y,spawn_blocked;
    adv_night_bug_t bugs[ADV_NIGHT_CAP];
} adv_night_t;
void adv_night_start(adv_night_t *g,uint32_t seed);
void adv_night_step(adv_night_t *g,const adv_input_t *input);
int adv_night_target(const adv_night_t *g);
int adv_night_object_y(const adv_night_bug_t *bug);
int adv_night_speed(const adv_night_t *g);
extern const adv_game_t adv_night_game;
