// POST V2 reference port: mail cranes, throttle/brake, signals and speed limits.
#include "adv_post_v2.h"
#include "adv_v2_math.h"
#include <string.h>
#define K(n) POST_V2_##n
#define T(n) POST_V2_T_##n
#define SEC(n) POST_V2_SEC_##n
#define FX(n) POST_V2_FX_##n
#define MIN v2_min
#define MAX v2_max
static int rnd(adv_post_v2_t *g, int n)
{
    return (int)(adv_rand(&g->rng) % (uint32_t)n);
}
static int tier_of(int v)
{
    return v >= 720 ? 3 : v >= 420 ? 2 : 1;
}
static int mult(const adv_post_v2_t *g)
{
    return tier_of(g->v) + MIN(3, g->combo / 4);
}
static int cam(const adv_post_v2_t *g)
{
    return g->dist >> 8;
}
static void fx(adv_post_v2_t *g, int kind, int x, int y, int val)
{
    g->fx[g->fxHead] = (adv_post_v2_fx_t){kind, x, y, val, 0};
    g->fxHead = (g->fxHead + 1) % 6;
}
static adv_post_v2_event_t *slot(adv_post_v2_t *g)
{
    for (int i = 0; i < K(EVENTS); i++)
        if (!g->ev[i].type)
            return &g->ev[i];
    g->blocked++;
    return NULL;
}
void adv_post_v2_start(adv_post_v2_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed;
    g->res = 1000;
    g->v = K(V0);
    g->bags = K(BAGS0);
    g->tier = 1;
    g->nextEvent = 360;
}
static void spawn(adv_post_v2_t *g, int x)
{
    int s = g->section, v = rnd(g, 100);
    adv_post_v2_event_t *e = slot(g);
    static const int weights[5][5] = {{34, 24, 18, 12, 12},
                                      {44, 26, 8, 14, 8},
                                      {26, 20, 36, 9, 9},
                                      {26, 20, 9, 9, 36},
                                      {30, 22, 12, 26, 10}};
    int index = s >= SEC(TOWN) && s <= SEC(NIGHT) ? s : 0, acc = 0, type = 1;
    for (int i = 0; i < 5; i++) {
        acc += weights[index][i];
        if (v < acc) {
            type = i + 1;
            break;
        }
    }
    if (g->tick < 600 && (type == T(SIGNAL) || type == T(ANIMAL)))
        type = T(NET);
    if (e) {
        if (type == T(LIMIT)) {
            int a = 360 + rnd(g, 5) * 60, b = 160 + rnd(g, 120);
            *e = (adv_post_v2_event_t){type, x, a, b, 0, 0};
        } else if (type == T(SIGNAL))
            *e = (adv_post_v2_event_t){type, x, 50 + rnd(g, 130), 0, -1, 0};
        else if (type == T(ANIMAL)) {
            int a = 80 + rnd(g, 120), b = rnd(g, 2);
            *e = (adv_post_v2_event_t){type, x, a, b, -1, 0};
        } else {
            *e = (adv_post_v2_event_t){type, x, type == T(NET) ? rnd(g, 4) : 0, 0, 0, 0};
            if (type == T(NET))
                g->nets++;
        }
    }
    g->nextEvent = x + (s == SEC(TOWN) ? 110 : 140) + rnd(g, 120) + (type == T(LIMIT) && e ? e->b : 0);
}
static void lose(adv_post_v2_t *g, int kind, int time, int x)
{
    g->res -= time;
    g->combo = 0;
    g->cue = 7;
    fx(g, kind, x, K(RAIL) - 60, time);
}
void adv_post_v2_step(adv_post_v2_t *g, const adv_input_t *in)
{
    g->cue = 0;
    for (int i = 0; i < 6; i++)
        if (g->fx[i].kind && ++g->fx[i].t >= 60)
            g->fx[i].kind = 0;
    if (g->over)
        return;
    g->tick++;
    g->presses += !!in->ok_down + !!in->up_down + !!in->down_down;
    if (g->cool > 0)
        g->cool--;
    if (g->tick >= K(CALM) && (g->tick - K(CALM)) % K(EVERY) == 0) {
        g->section = 1 + (g->tick - K(CALM)) / K(EVERY) % 5;
        g->sectionT = K(SECTION_LEN);
        fx(g, FX(SECTION), 160, 100, g->section);
    }
    if (g->sectionT > 0 && --g->sectionT == 0)
        g->section = 0;
    g->braking = in->ok_held && !in->up_held;
    g->steaming = in->up_held && !in->ok_held;
    if (g->stun > 0) {
        g->stun--;
        g->v = MAX(0, g->v - K(BRAKE));
    } else if (g->braking)
        g->v = MAX(0, g->v - K(BRAKE));
    else if (g->steaming)
        g->v = MIN(K(VMAX), g->v + K(ACC));
    else
        g->v = MAX(0, g->v - K(DRAG) + (g->section == SEC(DOWNHILL) ? 3 : 0));
    g->v = MIN(K(VMAX), g->v);
    int tier = tier_of(g->v);
    if (tier > g->tier)
        fx(g, FX(TIER), K(LOCO_X), K(RAIL) - 96, tier);
    g->tier = tier;
    if (g->v >= 720)
        g->topSpeedT++;
    g->dist += g->v;
    int c = cam(g);
    g->drainAcc += K(DRAIN) + MIN(K(DRAIN_MAX), g->tick / K(DRAIN_RAMP));
    while (g->drainAcc >= 60) {
        g->res--;
        g->drainAcc -= 60;
    }
    if (in->down_down && !g->cool && !g->stun) {
        g->cool = K(COOL);
        adv_post_v2_event_t *best = NULL;
        int bd = 1000000000;
        for (int i = 0; i < K(EVENTS); i++) {
            adv_post_v2_event_t *e = &g->ev[i];
            if ((e->type == T(NET) || e->type == T(CRANE)) && !e->done) {
                int d = abs(e->x - c - K(DOOR_X));
                if (d < bd) {
                    bd = d;
                    best = e;
                }
            }
        }
        if (best && bd <= K(WINDOW)) {
            best->done = 1;
            if (best->type == T(NET)) {
                if (g->bags > 0) {
                    g->bags--;
                    g->delivered++;
                    g->combo++;
                    if (g->combo > g->best)
                        g->best = g->combo;
                    int perfect = bd <= K(PERFECT), pts = K(PTS) * mult(g) * (perfect ? 2 : 1);
                    g->bonus += pts;
                    g->res = MIN(1000, g->res + K(TIME_NET) + (perfect ? K(TIME_PERFECT) : 0));
                    if (perfect)
                        g->perfects++;
                    fx(g, perfect ? FX(PERFECT) : FX(NET), best->x - c, K(RAIL) - 54, pts);
                    g->cue = 6;
                } else
                    best->done = 0;
            } else {
                g->bags = MIN(K(BAGS_MAX), g->bags + 1);
                g->cranes++;
                int pts = K(CRANE_PTS) * tier_of(g->v);
                g->bonus += pts;
                g->res = MIN(1000, g->res + K(TIME_CRANE));
                fx(g, FX(CRANE), best->x - c, K(RAIL) - 70, pts);
                g->cue = 6;
            }
        } else if (best && bd <= K(WINDOW) * 4 && g->bags > 0 && best->type == T(NET)) {
            g->bags--;
            g->wasted++;
            lose(g, FX(WASTE), K(TIME_WASTE), K(DOOR_X));
        }
    }
    g->zone = 0;
    for (int i = 0; i < K(EVENTS); i++) {
        adv_post_v2_event_t *e = &g->ev[i];
        if (!e->type)
            continue;
        int sx = e->x - c;
        if ((e->type == T(LIMIT) && e->x + e->b - c < K(CULL)) || (e->type != T(LIMIT) && sx < K(CULL))) {
            memset(e, 0, sizeof(*e));
            continue;
        }
        if ((e->type == T(SIGNAL) || e->type == T(ANIMAL)) && e->t < 0 && sx < K(W) + 10)
            e->t = (int)g->tick;
        if (e->type == T(NET)) {
            if (!e->done && sx < K(DOOR_X) - K(WINDOW)) {
                e->done = 2;
                if (g->bags > 0) {
                    g->skipped++;
                    lose(g, FX(SKIP), K(TIME_SKIP), K(DOOR_X) - 30);
                }
            }
        } else if (e->type == T(CRANE)) {
            if (!e->done && sx < K(DOOR_X) - K(WINDOW))
                e->done = 2;
        } else if (e->type == T(LIMIT)) {
            if (sx <= K(FRONT_X) && e->x + e->b - c >= K(LOCO_X) - 48) {
                g->zone = e->a;
                if (g->v > e->a + 24) {
                    if (++g->over_t == 1)
                        fx(g, FX(OVER), K(LOCO_X), K(RAIL) - 96, e->a * 120 / K(VMAX));
                    if (g->over_t >= K(OVER_GRACE) && !e->done) {
                        e->done = 1;
                        g->derails++;
                        g->stun = K(STUN);
                        lose(g, FX(DERAIL), K(TIME_DERAIL), K(LOCO_X));
                        g->over_t = 0;
                    }
                } else
                    g->over_t = 0;
            }
        } else if (e->type == T(SIGNAL)) {
            bool red = e->t >= 0 && (int)g->tick - e->t < e->a;
            if (!e->done && sx <= K(FRONT_X)) {
                e->done = 1;
                if (red && g->v > K(SLOW)) {
                    g->reds++;
                    lose(g, FX(RED), K(TIME_RED), K(FRONT_X));
                    g->v /= 2;
                } else if (red) {
                    g->nearMiss++;
                    fx(g, FX(NEAR), K(FRONT_X), K(RAIL) - 80, 0);
                }
            }
        } else if (e->type == T(ANIMAL)) {
            bool on = e->t >= 0 && (int)g->tick - e->t < e->a;
            if (!e->done && sx <= K(FRONT_X) + 4 && sx >= K(FRONT_X) - 40) {
                if (on) {
                    e->done = 1;
                    g->animals++;
                    g->v /= 3;
                    lose(g, FX(ANIMAL), K(TIME_ANIMAL), K(FRONT_X));
                } else {
                    e->done = 1;
                    if ((int)g->tick - e->t - e->a < 40) {
                        g->nearMiss++;
                        fx(g, FX(NEAR), K(FRONT_X), K(RAIL) - 80, 0);
                    }
                }
            }
        }
    }
    if (!g->zone)
        g->over_t = 0;
    while (g->nextEvent < c + K(W) + K(AHEAD) - 320 + 160)
        spawn(g, g->nextEvent);
    g->meters = (g->dist >> 8) / 4;
    g->score = g->meters / 40 + g->bonus;
    if (g->res <= 0) {
        g->res = 0;
        g->over = 1;
        g->cue = 8;
    }
}
static void start(void *p, uint32_t s)
{
    adv_post_v2_start(p, s);
}
static void step(void *p, const adv_input_t *i)
{
    adv_post_v2_step(p, i);
}
static adv_status_t status(const void *p)
{
    const adv_post_v2_t *g = p;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_post_v2_game = {"post", sizeof(adv_post_v2_t), start, step, status};
