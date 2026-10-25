#pragma once
// Integer 60Hz POST. Reference: prototype/adv_post.js. 1 position unit=1/60px.
#include "adv_game.h"
#define ADV_POST_CAP 12
#define ADV_POST_HOLD 24
#define ADV_POST_X (110*60)
#define ADV_POST_MAIL_X (156*60)
#define ADV_POST_WINDOW (32*60)
enum { POST_FORK=1, POST_STATION, POST_COAL, POST_ANIMAL, POST_DEPOT };
typedef struct { int32_t type,x,lane,color,done,horn; } adv_post_event_t;
typedef struct {
    uint32_t tick,score;
    int32_t res,over,lane,choice,y,transition,speed,drain_acc,hold,whistle,lap;
    int32_t remaining,refill,next_fork,next_coal,next_animal,hit,miss,delivered,cue,spawn_blocked;
    uint32_t distance,rng;
    int32_t practice,lesson,tap_target,tap_reason,miss_reason,feedback;
    uint32_t presses,taps;
    int32_t mail[5];
    adv_post_event_t events[ADV_POST_CAP];
} adv_post_t;
void adv_post_start(adv_post_t *g,uint32_t seed);
void adv_post_start_practice(adv_post_t *g,uint32_t seed);
bool adv_post_can_deliver(const adv_post_t *g);
void adv_post_step(adv_post_t *g,const adv_input_t *input);
extern const adv_game_t adv_post_game;
