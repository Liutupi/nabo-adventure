#include "adv_ski.h"
#include "adv_rng.h"
#include <stdlib.h>
#include <string.h>

static int range(adv_ski_t *g, int lo, int hi) { return lo + (int)(adv_rand(&g->rng) % (unsigned)(hi - lo + 1)); }
static int min_i(int a, int b) { return a < b ? a : b; }
static int max_i(int a, int b) { return a > b ? a : b; }

static adv_ski_obj_t *slot(adv_ski_t *g)
{
    for (int i = 0; i < ADV_SKI_CAP; i++) if (!g->objs[i].type) return &g->objs[i];
    g->blocked++;
    return NULL;
}
static const adv_ski_obj_t *near_gate(const adv_ski_t *g, int y)
{
    for (int i = 0; i < ADV_SKI_CAP; i++) {
        const adv_ski_obj_t *o = &g->objs[i];
        if (o->type && o->type <= SKI_GATE_BLUE && abs(o->y - y) < 56) return o;
    }
    return NULL;
}
static void spawn_gate(adv_ski_t *g)
{
    adv_ski_obj_t *o = slot(g);
    if (!o) return;
    int lo = max_i(64, g->last_gate_x - 90), hi = min_i(176, g->last_gate_x + 90), x = range(g, lo, hi);
    *o = (adv_ski_obj_t){g->gates & 1 ? SKI_GATE_BLUE : SKI_GATE_RED, x, g->next_gate, 0};
    g->last_gate_x = x; g->gates++;
}
static void spawn_hazard(adv_ski_t *g)
{
    int v = (int)(adv_rand(&g->rng) % 100), y = g->next_hazard;
    int type = v < 45 ? SKI_TREE : v < 65 ? SKI_PINE : v < 90 ? SKI_MOGUL : SKI_CABIN;
    if (type == SKI_CABIN && g->cabin_wait > 0) type = SKI_TREE;
    int x = type == SKI_CABIN ? ((adv_rand(&g->rng) & 1) ? 200 : 40) : range(g, 32, 208);
    const adv_ski_obj_t *gate = near_gate(g, y);
    if (gate && abs(x - gate->x) < 48) x = gate->x < 120 ? min_i(208, gate->x + 56) : max_i(32, gate->x - 56);
    adv_ski_obj_t *o = slot(g);
    if (!o) return;
    *o = (adv_ski_obj_t){type, x, y, 0};
    if (type == SKI_CABIN) g->cabin_wait = 8;
}

void adv_ski_start(adv_ski_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed; g->res = ADV_RESOURCE_MAX; g->x = 120 * 16; g->speed = ADV_SKI_SPEED0;
    g->next_gate = 300; g->next_hazard = 200; g->last_gate_x = 120; g->cabin_wait = 3;
}
void adv_ski_up_event(adv_ski_t *g, bool pressed)
{
    if (pressed) g->left_hold = 0;
    else { g->short_taps = g->left_hold < ADV_SKI_HOLD ? min_i(2, g->short_taps + 1) : 0; g->left_hold = 0; }
}
static void feedback(adv_ski_t *g, int message, int cue) { g->message = message; g->feedback = 60; g->cue = cue; }

static void cross(adv_ski_t *g, adv_ski_obj_t *o)
{
    o->done = 1;
    int dx = abs(g->x / 16 - o->x);
    if (o->type <= SKI_GATE_BLUE) {
        if (dx <= ADV_SKI_GATE_HALF) {
            if (g->score != UINT32_MAX) g->score++;
            g->speed = min_i(ADV_SKI_SPEED_MAX, g->speed + ADV_SKI_SPEED_STEP);
            feedback(g, SKI_MSG_PASS, 6);
        } else { g->res -= ADV_SKI_MISS; g->misses++; feedback(g, SKI_MSG_MISS, 7); }
    } else if (o->type == SKI_CABIN) {
        if (dx < 34) { g->res = min_i(ADV_RESOURCE_MAX, g->res + ADV_SKI_COCOA); g->cocoa++; feedback(g, SKI_MSG_COCOA, 6); }
    } else if (!g->invuln && !g->fall) {
        if (o->type == SKI_TREE && dx < 20) {
            g->res -= ADV_SKI_TREE; g->crashes++; g->fall = ADV_SKI_FALL; g->vx = 0; g->air = 0; feedback(g, SKI_MSG_TREE, 7);
        } else if (o->type != SKI_TREE && !g->air && dx < (o->type == SKI_MOGUL ? 16 : 14)) {
            g->res -= ADV_SKI_BUMP; g->bumps++; g->fall = ADV_SKI_BUMP_T; g->vx = 0; feedback(g, SKI_MSG_BUMP, 7);
        }
    }
}

void adv_ski_step(adv_ski_t *g, const adv_input_t *in)
{
    g->tick++; g->cue = 0;
    if (g->feedback > 0) g->feedback--;
    if (g->invuln > 0) g->invuln--;
    if (g->over) return;
    g->left_hold = in->up_held ? min_i(ADV_SKI_HOLD, g->left_hold + 1) : 0;
    g->right_hold = in->down_held ? min_i(ADV_SKI_HOLD, g->right_hold + 1) : 0;
    if (in->ok_down && !g->air && !g->fall) { g->air = ADV_SKI_AIR; g->cue = 1; }
    if (g->fall) { if (--g->fall == 0) g->invuln = ADV_SKI_INVULN; }
    else {
        int dir = (g->right_hold >= ADV_SKI_HOLD) - (g->left_hold >= ADV_SKI_HOLD);
        if (dir) g->vx = max_i(-ADV_SKI_VMAX, min_i(ADV_SKI_VMAX, g->vx + dir * ADV_SKI_ACCEL));
        else { g->vx -= g->vx / 6; if (abs(g->vx) < 4) g->vx = 0; }
        g->x += g->vx;
        if (g->x < ADV_SKI_LEFT * 16) { g->x = ADV_SKI_LEFT * 16; g->vx = 0; }
        if (g->x > ADV_SKI_RIGHT * 16) { g->x = ADV_SKI_RIGHT * 16; g->vx = 0; }
        if (g->air) g->air--;
        g->sub += g->speed; g->pos += g->sub >> 4; g->sub &= 15;
    }
    while (g->pos + ADV_SKI_AHEAD + 60 >= g->next_gate) { spawn_gate(g); g->next_gate += range(g, 190, 250); }
    while (g->pos + ADV_SKI_AHEAD >= g->next_hazard) {
        spawn_hazard(g);
        if (g->cabin_wait > 0) g->cabin_wait--;
        int cut = g->score > 40 ? 40 : (int)g->score;
        g->next_hazard += range(g, 70, 130) - cut;
    }
    for (int i = 0; i < ADV_SKI_CAP; i++) {
        adv_ski_obj_t *o = &g->objs[i];
        if (!o->type) continue;
        if (!o->done && o->y <= g->pos) cross(g, o);
        if (o->y < g->pos - ADV_SKI_BEHIND) memset(o, 0, sizeof(*o));
    }
    g->drain_acc += ADV_SKI_DRAIN;
    while (g->drain_acc >= 60) { g->res--; g->drain_acc -= 60; }
    if (g->res <= 0) { g->res = 0; g->over = 1; g->cue = 8; }
}

static void start_game(void *state, uint32_t seed) { adv_ski_start(state, seed); }
static void step_game(void *state, const adv_input_t *input) { adv_ski_step(state, input); }
static adv_status_t status_game(const void *state)
{
    const adv_ski_t *g = state;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_ski_game = {"ski", sizeof(adv_ski_t), start_game, step_game, status_game};
