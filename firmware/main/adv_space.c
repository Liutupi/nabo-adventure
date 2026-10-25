#include "adv_space.h"
#include "adv_rng.h"
#include <stdlib.h>
#include <string.h>

static int range(adv_space_t *g, int lo, int hi) { return lo + (int)(adv_rand(&g->rng) % (unsigned)(hi - lo + 1)); }
static int min_i(int a, int b) { return a < b ? a : b; }
static int max_i(int a, int b) { return a > b ? a : b; }
static int clamp(int v, int lo, int hi) { return v < lo ? lo : v > hi ? hi : v; }

int adv_space_zone(const adv_space_t *g) { return max_i(14, 40 - g->round * 4); }

static void setup_round(adv_space_t *g)
{
    int x = range(g, 70, 170), vx = range(g, -120, 120);
    g->x = x * 256; g->y = ADV_SPACE_TOP_Y * 256; g->vx = vx; g->vy = min_i(240, g->round * 30);
    g->pad = range(g, 64, 176); g->phase = SPACE_FLY; g->timer = 0; g->thrust = 0; g->side = 0;
    memset(g->objs, 0, sizeof(g->objs));
    if (adv_rand(&g->rng) % 100 < 70) {
        int from_left = (int)(adv_rand(&g->rng) & 1), y = range(g, 150, 230);
        g->objs[0] = (adv_space_obj_t){SPACE_FUEL, (from_left ? -20 : 260) * 256, y * 256, from_left ? 220 : -220};
    }
    int rocks = g->round < 2 ? 0 : g->round < 4 ? 1 : 2;
    for (int i = 0; i < rocks; i++) {
        int from_left = (int)(adv_rand(&g->rng) & 1), y = range(g, 140, 240), speed = range(g, 150, 330);
        g->objs[1 + i] = (adv_space_obj_t){SPACE_ROCK, (from_left ? -30 : 270) * 256, y * 256, (from_left ? 1 : -1) * speed};
    }
}

void adv_space_start(adv_space_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed; g->res = ADV_RESOURCE_MAX; g->pad = 120;
    setup_round(g);
}
void adv_space_up_event(adv_space_t *g, bool pressed)
{
    if (pressed) g->left_hold = 0;
    else { g->short_taps = g->left_hold < ADV_SPACE_HOLD ? min_i(2, g->short_taps + 1) : 0; g->left_hold = 0; }
}
void adv_space_down_event(adv_space_t *g, bool pressed)
{
    if (pressed) g->right_hold = 0;
    else { g->down_taps = g->right_hold < ADV_SPACE_HOLD ? min_i(2, g->down_taps + 1) : 0; g->right_hold = 0; }
}
static void feedback(adv_space_t *g, int message, int cue) { g->message = message; g->feedback = 90; g->cue = cue; }
static void crash(adv_space_t *g, int message)
{
    g->res -= ADV_SPACE_HIT; g->crashes++; g->phase = SPACE_CRASH; g->timer = ADV_SPACE_CRASH;
    g->vx = g->vy = 0; g->thrust = g->side = 0; feedback(g, message, 7);
}
static void touchdown(adv_space_t *g)
{
    int dx = abs(g->x / 256 - g->pad);
    bool soft = g->vy <= ADV_SPACE_SAFE_VY && abs(g->vx) <= ADV_SPACE_SAFE_VX;
    g->y = ADV_SPACE_GROUND * 256;
    if (dx <= adv_space_zone(g) && soft) {
        int bonus = 100 + (ADV_SPACE_SAFE_VY - max_i(0, g->vy)) * 50 / ADV_SPACE_SAFE_VY + min_i(50, g->res / 20);
        g->score += (uint32_t)bonus; g->last_bonus = bonus; g->landings++;
        g->phase = SPACE_LANDED; g->timer = ADV_SPACE_LANDED; g->vx = g->vy = 0; g->thrust = g->side = 0;
        feedback(g, SPACE_MSG_LANDED, 6);
    } else crash(g, soft ? SPACE_MSG_MISSED : SPACE_MSG_HARD);
}

void adv_space_step(adv_space_t *g, const adv_input_t *in)
{
    g->tick++; g->cue = 0;
    if (g->feedback > 0) g->feedback--;
    if (g->over) return;
    g->left_hold = in->up_held ? min_i(ADV_SPACE_HOLD, g->left_hold + 1) : 0;
    g->right_hold = in->down_held ? min_i(ADV_SPACE_HOLD, g->right_hold + 1) : 0;
    if (g->phase != SPACE_FLY) {
        if (--g->timer <= 0) { if (g->phase == SPACE_LANDED) g->round++; setup_round(g); }
    } else {
        g->thrust = in->ok_held ? 1 : 0;
        g->side = (g->right_hold >= ADV_SPACE_HOLD) - (g->left_hold >= ADV_SPACE_HOLD);
        g->drain_acc += (g->thrust ? ADV_SPACE_MAIN_DRAIN : 0) + (g->side ? ADV_SPACE_SIDE_DRAIN : 0);
        while (g->drain_acc >= 60) { g->res--; g->drain_acc -= 60; }
        g->vy = clamp(g->vy + ADV_SPACE_GRAVITY - (g->thrust ? ADV_SPACE_THRUST : 0), -ADV_SPACE_VMAX, ADV_SPACE_VMAX);
        g->vx = clamp(g->vx + g->side * ADV_SPACE_SIDE, -ADV_SPACE_VMAX, ADV_SPACE_VMAX);
        g->x += g->vx; g->y += g->vy;
        if (g->x < ADV_SPACE_LEFT * 256) { g->x = ADV_SPACE_LEFT * 256; g->vx = 0; }
        if (g->x > ADV_SPACE_RIGHT * 256) { g->x = ADV_SPACE_RIGHT * 256; g->vx = 0; }
        if (g->y < (ADV_SPACE_TOP_Y - 60) * 256) { g->y = (ADV_SPACE_TOP_Y - 60) * 256; if (g->vy < 0) g->vy = 0; }
        int lx = g->x / 256, ly = g->y / 256;
        for (int i = 0; i < ADV_SPACE_OBJS; i++) {
            adv_space_obj_t *o = &g->objs[i];
            if (!o->type) continue;
            o->x += o->vx;
            int ox = o->x / 256, oy = o->y / 256;
            if (ox < -40 || ox > 280) { o->type = 0; continue; }
            if (abs(ox - lx) <= ADV_SPACE_FEET + 8 && oy >= ly - ADV_SPACE_BODY_TOP - 8 && oy <= ly + 4) {
                if (o->type == SPACE_FUEL) { g->res = min_i(ADV_RESOURCE_MAX, g->res + ADV_SPACE_CAN); g->cans++; feedback(g, SPACE_MSG_FUEL, 6); }
                else crash(g, SPACE_MSG_ROCK);
                o->type = 0;
                if (g->phase != SPACE_FLY) break;
            }
        }
        if (g->phase == SPACE_FLY && g->y >= ADV_SPACE_GROUND * 256) touchdown(g);
    }
    if (g->res <= 0) { g->res = 0; g->over = 1; g->cue = 8; }
}

static void start_game(void *state, uint32_t seed) { adv_space_start(state, seed); }
static void step_game(void *state, const adv_input_t *input) { adv_space_step(state, input); }
static adv_status_t status_game(const void *state)
{
    const adv_space_t *g = state;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_space_game = {"space", sizeof(adv_space_t), start_game, step_game, status_game};
