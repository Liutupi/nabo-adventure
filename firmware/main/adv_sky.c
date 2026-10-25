#include "adv_sky.h"
#include "adv_rng.h"
#include <stdlib.h>
#include <string.h>

static const int RADIUS[] = {0, 8, 18, 8, 0};
static int range(adv_sky_t *g, int lo, int hi) { return lo + (int)(adv_rand(&g->rng) % (unsigned)(hi - lo + 1)); }
static int min_i(int a, int b) { return a < b ? a : b; }
static int max_i(int a, int b) { return a > b ? a : b; }

static void spawn(adv_sky_t *g)
{
    adv_sky_obj_t *o = NULL;
    for (int i = 0; i < ADV_SKY_CAP; i++) if (!g->objs[i].type) { o = &g->objs[i]; break; }
    if (!o) { g->blocked++; return; }
    int v = (int)(adv_rand(&g->rng) % 100), type = v < 30 ? SKY_STORM : v < 70 ? SKY_BIRD : v < 85 ? SKY_STAMP : SKY_WARM;
    int offset = range(g, -180, 180), alt = max_i(40, min_i(ADV_SKY_CEIL - 40, (g->alt >> 4) + offset));
    int phase = (int)(adv_rand(&g->rng) % 64);
    *o = (adv_sky_obj_t){type, (g->dist >> 4) + ADV_SKY_SPAWN_X, alt, phase, 0};
}

void adv_sky_start(adv_sky_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed; g->res = ADV_RESOURCE_MAX; g->alt = 300 * 16; g->speed = ADV_SKY_SPEED0; g->next_spawn = 220;
}
static void feedback(adv_sky_t *g, int message, int cue) { g->message = message; g->feedback = 60; g->cue = cue; }

static bool touches(int dx, int dy, int r)
{
    if (dx >= -ADV_SKY_BASKET_X - r && dx <= ADV_SKY_BASKET_X + r && dy >= ADV_SKY_BASKET_LO - r && dy <= ADV_SKY_BASKET_HI + r) return true;
    int rx = ADV_SKY_ENV_RX + r, ry = ADV_SKY_ENV_RY + r, ey = dy - ADV_SKY_ENV_Y;
    if (abs(dx) > rx || abs(ey) > ry) return false;
    return dx * dx * ry * ry + ey * ey * rx * rx <= rx * rx * ry * ry;
}
int adv_sky_object_alt(const adv_sky_obj_t *o)
{
    int q = o->phase % 64, v = q < 32 ? q : 64 - q;
    return o->type == SKY_BIRD ? o->alt + v * 24 / 32 - 12 : o->alt;
}

void adv_sky_step(adv_sky_t *g, const adv_input_t *in)
{
    g->tick++; g->cue = 0;
    if (g->feedback > 0) g->feedback--;
    if (g->invuln > 0) g->invuln--;
    if (g->over) return;
    g->heating = in->ok_held ? 1 : 0;
    g->vy = max_i(-ADV_SKY_VMAX, min_i(ADV_SKY_VMAX, g->vy + (g->heating ? ADV_SKY_LIFT : -ADV_SKY_SINK)));
    if (g->heating) { g->drain_acc += ADV_SKY_HEAT_DRAIN; while (g->drain_acc >= 60) { g->res--; g->drain_acc -= 60; } }
    g->alt += g->vy;
    if (g->alt > ADV_SKY_CEIL * 16) { g->alt = ADV_SKY_CEIL * 16; g->vy = 0; }
    if (g->alt < 0) {
        g->alt = 0;
        if (!g->invuln) { g->res -= ADV_SKY_GROUND; g->grounds++; g->invuln = ADV_SKY_INVULN; g->vy = 32; feedback(g, SKY_MSG_GROUND, 7); }
        else g->vy = 0;
    }
    g->dist += g->speed;
    g->speed = min_i(ADV_SKY_SPEED_MAX, ADV_SKY_SPEED0 + g->dist / (16 * 400));
    while ((g->dist >> 4) + ADV_SKY_SPAWN_X >= g->next_spawn) {
        spawn(g);
        g->next_spawn += range(g, 90, 160) - min_i(50, g->dist / (16 * 200));
    }
    int d = g->dist >> 4, a = g->alt >> 4;
    for (int i = 0; i < ADV_SKY_CAP; i++) {
        adv_sky_obj_t *o = &g->objs[i];
        if (!o->type) continue;
        if (o->type == SKY_BIRD) { o->x--; o->phase++; }
        int dx = o->x - d;
        if (dx < ADV_SKY_GONE_X) { memset(o, 0, sizeof(*o)); continue; }
        if (o->done) continue;
        int dy = adv_sky_object_alt(o) - a;
        if (o->type == SKY_WARM) {
            if (abs(dx) <= ADV_SKY_WARM_W && dy >= -ADV_SKY_WARM_H - ADV_SKY_BASKET_HI && dy <= ADV_SKY_WARM_H - ADV_SKY_BASKET_LO) {
                o->done = 1; g->res = min_i(ADV_RESOURCE_MAX, g->res + ADV_SKY_WARM); g->warms++; feedback(g, SKY_MSG_WARM, 6);
            }
            continue;
        }
        if (!touches(dx, dy, RADIUS[o->type])) continue;
        if (o->type == SKY_STAMP) { o->done = 1; g->bonus += ADV_SKY_STAMP; g->stamps++; feedback(g, SKY_MSG_STAMP, 6); }
        else if (!g->invuln) {
            o->done = 1; g->res -= ADV_SKY_HIT; g->hits++; g->invuln = ADV_SKY_INVULN;
            feedback(g, o->type == SKY_BIRD ? SKY_MSG_BIRD : SKY_MSG_STORM, 7);
        }
    }
    g->score = (uint32_t)(g->dist / 160 + g->bonus);
    if (g->res <= 0) { g->res = 0; g->over = 1; g->cue = 8; }
}

static void start_game(void *state, uint32_t seed) { adv_sky_start(state, seed); }
static void step_game(void *state, const adv_input_t *input) { adv_sky_step(state, input); }
static adv_status_t status_game(const void *state)
{
    const adv_sky_t *g = state;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_sky_game = {"sky", sizeof(adv_sky_t), start_game, step_game, status_game};
