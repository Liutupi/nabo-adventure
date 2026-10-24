#include "adv_demo.h"
#include <string.h>
#include "adv_model.h"
#include "adv_rng.h"

static void new_zone(adv_demo_t *g)
{
    g->zc = g->zh + (int)(adv_rand(&g->rng) % (uint32_t)(1000 - 2 * g->zh + 1));
}

static void demo_start(void *state, uint32_t seed)
{
    adv_demo_t *g = state;
    memset(g, 0, sizeof(*g));
    g->rng = seed;
    g->v = 12;
    g->zh = 180;
    g->res = ADV_RESOURCE_MAX;
    new_zone(g);
}

static void demo_step(void *state, const adv_input_t *in)
{
    adv_demo_t *g = state;
    g->cue = ADV_CUE_NONE;
    if (g->hit) g->hit--;
    if (g->miss) g->miss--;
    if (g->over) return;
    g->p += g->v;
    if (g->p >= 1000) { g->p = 1000; g->v = -g->v; }
    if (g->p <= 0) { g->p = 0; g->v = -g->v; }
    g->res -= 2;
    if (in->ok_down) {
        int d = g->p - g->zc;
        if ((d < 0 ? -d : d) <= g->zh) {
            g->score++;
            g->res = g->res + 150 > ADV_RESOURCE_MAX ? ADV_RESOURCE_MAX : g->res + 150;
            g->zh = g->zh - 10 < 60 ? 60 : g->zh - 10;
            int speed = (g->v < 0 ? -g->v : g->v) + 1;
            if (speed > 30) speed = 30;
            g->v = g->v < 0 ? -speed : speed;
            new_zone(g);
            g->hit = 12;
            g->cue = ADV_CUE_HIT;
        } else {
            g->res -= 250;
            g->miss = 12;
            g->cue = ADV_CUE_MISS;
        }
    }
    if (g->res <= 0) { g->res = 0; g->over = 1; g->cue = ADV_CUE_OVER; }
}

static adv_status_t demo_status(const void *state)
{
    const adv_demo_t *g = state;
    return (adv_status_t){.score = g->score, .resource = g->res, .over = g->over != 0, .cue = g->cue};
}

const adv_game_t adv_demo_game = {"demo", sizeof(adv_demo_t), demo_start, demo_step, demo_status};
