// SKI V2 rules; see adv_ski.h. Mirrors prototype/adv_ski.js line by line, including the order of every
// random draw, so tests/ski_golden replays exactly.
#include "adv_ski.h"
#include "adv_rng.h"
#include <stdlib.h>
#include <string.h>

enum {
    AHEAD = 200, CULL = 110, STEER = 26, VX_MAX = 600, V0 = 470, FLOW_GATE = 85, FLOW_SPIN = 70, ACCEL = 8, DRAG_DIV = 40,
    GATE_HALF = 21, GATE_STEP = 44, GATE_BOOST = 110, GATE_PUSH = 26, MISS_PULL = 20, TREE_R = 11, PINE_R = 9, MOGUL_R = 11, KICK_HALF = 18,
    DRIFT_HALF = 14, HOP = 26, KICK_AIR = 72, SPIN_PTS = 50, SPIN_PUSH = 18, STUMBLE = 20, INVULN = 50,
    AVAL0 = 340, AVAL_RAMP = 460, AVAL_DIV = 12, AVAL_START = 200, CALM = 900, EVERY = 1500, SECTION_LEN = 600,
};
static int rnd(adv_ski_t *g, int n) { return (int)(adv_rand(&g->rng) % (uint32_t)n); }
static int px(int32_t q) { return q >> 8; }
static int imin(int a, int b) { return a < b ? a : b; }
static int imax(int a, int b) { return a > b ? a : b; }
static int iabs(int a) { return a < 0 ? -a : a; }
int adv_ski_mult(const adv_ski_t *g) { return 1 + imin(4, g->combo / 4); }
static int aval_speed(const adv_ski_t *g) { return AVAL0 + (int)(g->tick / AVAL_DIV < AVAL_RAMP ? g->tick / AVAL_DIV : AVAL_RAMP); }

void adv_ski_start(adv_ski_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed; g->x = 160 << 8; g->v = V0; g->aval = -(AVAL_START << 8); g->next_gate = 260; g->next_row = 140; g->last_gate_x = 160;
}

static void fx(adv_ski_t *g, int kind, int x, int y, int val)
{
    g->fx[g->fx_head] = (adv_ski_fx_t){kind, x, y, val, 0};
    g->fx_head = (g->fx_head + 1) % ADV_SKI_FX;
}
static adv_ski_obj_t *slot(adv_ski_t *g)
{
    for (int i = 0; i < ADV_SKI_OBJS; i++) if (!g->objs[i].type) return &g->objs[i];
    g->blocked++;
    return NULL;
}
static bool near_gate(const adv_ski_t *g, int y, int x)
{
    for (int i = 0; i < ADV_SKI_OBJS; i++) {
        const adv_ski_obj_t *o = &g->objs[i];
        if (o->type && o->type <= SKI_GATE_BLUE && abs(o->y - y) < 44 && abs(o->x - x) < 46) return true;
    }
    return false;
}

static void spawn_gate(adv_ski_t *g, int y)
{
    bool slalom = g->section == SKI_SEC_SLALOM;
    int swing = slalom ? 110 : 80, lo = imax(48, g->last_gate_x - swing), hi = imin(272, g->last_gate_x + swing);
    int x = lo + rnd(g, hi - lo + 1);
    // gates never line up: at least GATE_STEP to the side of the last one (adv_ski.js, 2026-10-30)
    if (iabs(x - g->last_gate_x) < GATE_STEP) {
        x = g->last_gate_x + (x >= g->last_gate_x ? GATE_STEP : -GATE_STEP);
        if (x > 272 || x < 48) x = g->last_gate_x + (x > 272 ? -GATE_STEP : GATE_STEP);
    }
    adv_ski_obj_t *o = slot(g);
    if (o) *o = (adv_ski_obj_t){g->gates & 1 ? SKI_GATE_BLUE : SKI_GATE_RED, x, y, 0};
    g->last_gate_x = x; g->gates++;
    int gap = slalom ? 110 : 170;
    g->next_gate = y + gap + rnd(g, slalom ? 50 : 90);
}

static void spawn_row(adv_ski_t *g, int y)
{
    int s = g->section, n = 1 + rnd(g, s == SKI_SEC_FOREST ? 4 : 3);
    for (int i = 0; i < n; i++) {
        int v = rnd(g, 100);
        int x = ADV_SKI_LEFT + rnd(g, ADV_SKI_RIGHT - ADV_SKI_LEFT);
        int dy = rnd(g, 30), type;
        if (s == SKI_SEC_PARK) type = v < 35 ? SKI_KICKER : v < 60 ? SKI_MOGUL : v < 80 ? SKI_PINE : SKI_TREE;
        else if (s == SKI_SEC_FOREST) type = v < 60 ? SKI_TREE : v < 85 ? SKI_PINE : SKI_MOGUL;
        else if (s == SKI_SEC_ICE) type = v < 40 ? SKI_ICE : v < 70 ? SKI_TREE : SKI_DRIFT;
        else type = v < 40 ? SKI_TREE : v < 58 ? SKI_PINE : v < 74 ? SKI_MOGUL : v < 86 ? SKI_DRIFT : v < 94 ? SKI_KICKER : SKI_ICE;
        if (near_gate(g, y + dy, x)) continue;
        adv_ski_obj_t *o = slot(g);
        if (o) *o = (adv_ski_obj_t){type, x, y + dy, 0};
    }
    int gap = s == SKI_SEC_FOREST ? 34 : 46;
    g->next_row = y + gap + rnd(g, 40);
}

static void crash(adv_ski_t *g, int kind)
{
    bool hard = kind == SKI_FX_CRASH;
    g->crash = hard ? ADV_SKI_CRASH : STUMBLE; g->v = hard ? 0 : g->v / 2; g->vx = 0; g->combo = 0; g->spin_t = 0; g->air = 0; g->flow /= 2;
    g->invuln = INVULN; if (hard) g->crashes++; else g->stumbles++;
    g->cue = 7; fx(g, kind, px(g->x), ADV_SKI_NABO_Y, 0);
}

void adv_ski_step(adv_ski_t *g, const adv_input_t *in)
{
    g->cue = 0;
    for (int i = 0; i < ADV_SKI_FX; i++) if (g->fx[i].kind && ++g->fx[i].t >= 60) g->fx[i].kind = 0;
    if (g->over) return;
    g->tick++;
    g->presses += (in->ok_down ? 1 : 0) + (in->up_down ? 1 : 0) + (in->down_down ? 1 : 0);

    if (g->tick >= CALM && (g->tick - CALM) % EVERY == 0) {
        g->section = 1 + (int)((g->tick - CALM) / EVERY % 5); g->section_t = SECTION_LEN; fx(g, SKI_FX_SECTION, 160, 100, g->section);
    }
    if (g->section_t > 0 && --g->section_t == 0) g->section = 0;

    bool left = in->ok_held, right = in->up_held;
    if (g->crash > 0) g->crash--;
    else if (!g->air) {
        int acc = g->on_ice ? STEER / 4 : STEER, want = left && !right ? -1 : right && !left ? 1 : 0;
        if (want) g->vx = imax(-VX_MAX, imin(VX_MAX, g->vx + want * acc));
        else if (!g->on_ice) g->vx -= g->vx / 6;
        int target = V0 + g->flow - abs(g->vx) / 3;
        if (g->v < target) g->v = imin(target, g->v + ACCEL); else g->v = imax(target, g->v - abs(g->vx) / DRAG_DIV - 1);
    }
    if (g->invuln > 0) g->invuln--;
    if (g->flow > 0 && (g->tick & 1)) g->flow--;

    if (in->down_down && !g->crash) {
        if (!g->air) { g->air = g->air_max = HOP; g->kicked = 0; }
        else if (g->kicked && g->spin_t == 0) g->spin_t = ADV_SKI_SPIN;
    }
    int32_t prev_y = g->y;
    g->x = imax(ADV_SKI_LEFT << 8, imin(ADV_SKI_RIGHT << 8, g->x + g->vx));
    g->y += g->v;
    if (g->spin_t > 0 && --g->spin_t == 0) { g->spins++; g->tricks++; }
    if (g->air > 0 && --g->air == 0) {
        if (g->spin_t > 0) { crash(g, SKI_FX_CRASH); fx(g, SKI_FX_WIPE, px(g->x), ADV_SKI_NABO_Y, 0); g->spins = 0; }
        else if (g->spins) {
            int pts = g->spins * SPIN_PTS * adv_ski_mult(g);
            g->bonus += pts; g->aval -= g->spins * SPIN_PUSH << 8; g->combo += g->spins; g->flow = imin(ADV_SKI_FLOW_MAX, g->flow + g->spins * FLOW_SPIN);
            fx(g, SKI_FX_LAND, px(g->x), ADV_SKI_NABO_Y, pts); g->cue = 6; g->spins = 0;
        }
        g->kicked = 0;
    }

    g->on_ice = 0;
    int nx = px(g->x), y0 = px(prev_y), y1 = px(g->y);
    for (int i = 0; i < ADV_SKI_OBJS; i++) {
        adv_ski_obj_t *o = &g->objs[i];
        if (!o->type) continue;
        int dx = abs(nx - o->x);
        if (o->type == SKI_ICE) {
            if (dx <= ADV_SKI_ICE_HALF && y1 >= o->y && y1 <= o->y + ADV_SKI_ICE_LEN && !g->air) g->on_ice = 1;
            continue;
        }
        if (o->done || !(y0 < o->y && y1 >= o->y)) continue;
        o->done = 1;
        if (o->type <= SKI_GATE_BLUE) {
            if (dx <= GATE_HALF) {
                g->combo++; g->passed++; if (g->combo > g->best) g->best = g->combo;
                g->v += GATE_BOOST; g->flow = imin(ADV_SKI_FLOW_MAX, g->flow + FLOW_GATE); g->aval -= GATE_PUSH << 8;
                int pts = 10 * adv_ski_mult(g);
                g->bonus += pts; fx(g, SKI_FX_GATE, o->x, ADV_SKI_NABO_Y - 30, pts); g->cue = 6;
            } else { g->combo = 0; g->misses++; g->aval += MISS_PULL << 8; fx(g, SKI_FX_MISS, o->x, ADV_SKI_NABO_Y - 30, 0); g->cue = 7; }
        } else if (o->type == SKI_KICKER) {
            if (dx <= KICK_HALF && !g->crash) { g->air = g->air_max = KICK_AIR; g->kicked = 1; g->spin_t = 0; fx(g, SKI_FX_KICK, nx, ADV_SKI_NABO_Y, 0); }
        } else if (g->air || g->invuln || g->crash) continue;
        else if (o->type == SKI_TREE) {
            if (dx <= TREE_R) crash(g, SKI_FX_CRASH);
            else if (dx <= TREE_R + 10) { g->near_miss++; fx(g, SKI_FX_NEAR, nx, ADV_SKI_NABO_Y, 0); }
        } else if (o->type == SKI_PINE) { if (dx <= PINE_R) crash(g, SKI_FX_STUMBLE); }
        else if (o->type == SKI_MOGUL) { if (dx <= MOGUL_R) { g->v = g->v * 2 / 3; g->air = g->air_max = 10; g->kicked = 0; } }
        else if (o->type == SKI_DRIFT) { if (dx <= DRIFT_HALF) g->v /= 2; }
    }

    int ahead = y1 + AHEAD;
    while (g->next_gate < ahead) spawn_gate(g, g->next_gate);
    while (g->next_row < ahead) spawn_row(g, g->next_row);
    for (int i = 0; i < ADV_SKI_OBJS; i++) if (g->objs[i].type && g->objs[i].y < y1 - CULL) memset(&g->objs[i], 0, sizeof(g->objs[i]));

    g->aval += aval_speed(g);
    if (adv_ski_gap(g) > ADV_SKI_AVAL_CAP << 8) g->aval = g->y - (ADV_SKI_AVAL_CAP << 8);
    g->res = imax(0, adv_ski_gap(g) * 1000 / (ADV_SKI_AVAL_CAP << 8));
    g->meters = px(g->y) / 8;
    g->score = (uint32_t)(g->meters / 4 + g->bonus);
    if (adv_ski_gap(g) <= 0) { g->over = 1; g->res = 0; g->cue = 8; }
}

static void start_game(void *state, uint32_t seed) { adv_ski_start(state, seed); }
static void step_game(void *state, const adv_input_t *in) { adv_ski_step(state, in); }
static adv_status_t status_game(const void *state)
{
    const adv_ski_t *g = state;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_ski_game = {"ski", sizeof(adv_ski_t), start_game, step_game, status_game};
