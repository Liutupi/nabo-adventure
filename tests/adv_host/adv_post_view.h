#pragma once
#include <stdint.h>
#include <string.h>
#include "adv_post.h"
#define POST_VALUES 110
static inline void post_values(const adv_post_t *g,int64_t *out)
{
    const int64_t head[]={g->tick,g->score,g->res,g->over,g->lane,g->choice,g->y,g->transition,g->speed,
        g->drain_acc,g->hold,g->whistle,g->lap,g->remaining,g->refill,g->next_fork,g->next_coal,
        g->next_animal,g->hit,g->miss,g->delivered,g->cue,g->spawn_blocked,g->distance,g->rng,
        g->practice,g->lesson,g->tap_target,g->tap_reason,g->miss_reason,g->feedback,g->presses,g->taps};
    memcpy(out,head,sizeof(head));int n=33;
    for(int i=0;i<5;i++)out[n++]=g->mail[i];
    for(int i=0;i<ADV_POST_CAP;i++) {
        const adv_post_event_t *e=&g->events[i];
        out[n++]=e->type;out[n++]=e->x;out[n++]=e->lane;out[n++]=e->color;out[n++]=e->done;out[n++]=e->horn;
    }
}
