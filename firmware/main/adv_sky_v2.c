// SKY V2 reference port. Object order and random draws match adv_sky_v2.js exactly.
#include "adv_sky_v2.h"
#include "adv_v2_math.h"
#include <string.h>
#define K(n) SKY_V2_##n
#define T(n) SKY_V2_T_##n
#define FX(n) SKY_V2_FX_##n
#define SEC(n) SKY_V2_SEC_##n
#define MIN v2_min
#define MAX v2_max
static int rnd(adv_sky_v2_t *g, int n)
{
    return (int)(adv_rand(&g->rng) % (uint32_t)n);
}
static const int speeds[] = {230, 340, 450, 560};
static int cam(const adv_sky_v2_t *g)
{
    return g->dist >> 8;
}
static int mult(const adv_sky_v2_t *g)
{
    return 1 + MIN(4, g->combo / 3);
}
static void fx(adv_sky_v2_t *g, int kind, int x, int y, int val)
{
    g->fx[g->fxHead] = (adv_sky_v2_fx_t){kind, x, y, val, 0};
    g->fxHead = (g->fxHead + 1) % 6;
}
static adv_sky_v2_obj_t *slot(adv_sky_v2_t *g)
{
    for (int i = 0; i < K(OBJS); i++)
        if (!g->objs[i].type)
            return &g->objs[i];
    g->blocked++;
    return NULL;
}
void adv_sky_v2_start(adv_sky_v2_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed;
    g->res = 1000;
    g->y = K(Y0) << 8;
    g->spd = speeds[2];
    g->layer = 2;
    g->nextGround = 300;
    g->nextSky = 420;
    for (int i = 0; i < 4; i++)
        g->order[i] = i;
}
static void spawn_ground(adv_sky_v2_t *g, int x)
{
    int s = g->section, v = rnd(g, 100);
    adv_sky_v2_obj_t *o = slot(g);
    int odds = s == SEC(TOWN) ? 80 : s == SEC(STORM) ? 45 : 58;
    if (o && v < odds) {
        int gold = rnd(g, 100) < (s == SEC(RAINBOW) ? 40 : 9);
        int y = 176 + rnd(g, 18), style = rnd(g, 4);
        *o = (adv_sky_v2_obj_t){T(HOUSE), x, y, gold | (style << 1), 0, 0, 0};
        g->houses++;
        if (gold) {
            adv_sky_v2_obj_t *tree = slot(g);
            if (tree) {
                int tx = x + 38 + rnd(g, 10), ty = 150 + rnd(g, 14);
                *tree = (adv_sky_v2_obj_t){T(TREE), tx, ty, 1, 0, 0, 0};
            }
        }
    } else if (o) {
        int y = (s == SEC(TOWN) ? 172 : 150) + rnd(g, 30), thin = rnd(g, 3) == 0;
        *o = (adv_sky_v2_obj_t){T(TREE), x, y, thin, 0, 0, 0};
    }
    g->nextGround = x + (s == SEC(TOWN) ? 62 : 78) + rnd(g, s == SEC(TOWN) ? 30 : 60);
}
static void spawn_sky(adv_sky_v2_t *g, int x)
{
    int s = g->section, v = rnd(g, 100);
    adv_sky_v2_obj_t *o = slot(g);
    if (o) {
        int bird = s == SEC(BIRDS)  ? 62
                   : s == SEC(GUST) ? 22
                                    : 32,
            storm = s == SEC(STORM)   ? 90
                    : s == SEC(BIRDS) ? 92
                                      : 86;
        if (v < bird) {
            int y = 118 + rnd(g, 72), q = rnd(g, 64);
            *o = (adv_sky_v2_obj_t){T(BIRD), x, y, q, 0, 0, 0};
        } else if (v < storm) {
            int y = (s == SEC(STORM) ? 48 : 36) + rnd(g, 18), t = rnd(g, K(STORM_WARN));
            *o = (adv_sky_v2_obj_t){T(STORM), x, y, 0, t, 0, 0};
        } else
            *o = (adv_sky_v2_obj_t){T(TANK), x, 110 + rnd(g, 70), 0, 0, 0, 0};
    }
    g->nextSky = x + (s == SEC(BIRDS) ? 80 : 150) + rnd(g, s == SEC(BIRDS) ? 60 : 140);
}
static void hurt(adv_sky_v2_t *g, int damage, int kind, int x, int y)
{
    if (g->invuln)
        return;
    g->res -= damage;
    g->invuln = K(INVULN);
    g->combo = 0;
    g->hits++;
    g->cue = 7;
    fx(g, kind, x, y, damage);
}
static bool touches(int by, int ox, int oy, int r)
{
    int dx = ox - K(BX), ey = oy - (by - K(ENV_DY)), rr = K(ENV_R) + r;
    if (dx * dx + ey * ey <= rr * rr)
        return true;
    return abs(dx) <= K(BASKET_HALF) + r && oy >= by - K(BASKET_H) - r && oy <= by + r;
}
void adv_sky_v2_step(adv_sky_v2_t *g, const adv_input_t *in)
{
    g->cue = 0;
    for (int i = 0; i < 6; i++)
        if (g->fx[i].kind && ++g->fx[i].t >= 60)
            g->fx[i].kind = 0;
    if (g->over)
        return;
    g->tick++;
    g->presses += !!in->ok_down + !!in->up_down + !!in->down_down;
    if (g->invuln > 0)
        g->invuln--;
    if (g->cool > 0)
        g->cool--;
    if (g->tick >= K(CALM) && (g->tick - K(CALM)) % K(EVERY) == 0) {
        g->section = 1 + (g->tick - K(CALM)) / K(EVERY) % 5;
        g->sectionT = K(SECTION_LEN);
        for (int i = 3; i > 0; i--) {
            int j = rnd(g, i + 1), t = g->order[i];
            g->order[i] = g->order[j];
            g->order[j] = t;
        }
        fx(g, FX(SECTION), 160, 100, g->section);
    }
    if (g->sectionT > 0 && --g->sectionT == 0)
        g->section = 0;
    g->heating = in->up_held && !in->ok_held;
    g->venting = in->ok_held && !in->up_held;
    g->vy += g->heating ? -K(HEAT) : g->venting ? K(VENT) : K(SINK);
    g->vy -= g->vy / K(DAMP);
    g->vy = MAX(-K(VMAX), MIN(K(VMAX), g->vy));
    g->y += g->vy;
    if (g->y < (K(YMIN) << 8)) {
        g->y = K(YMIN) << 8;
        if (g->vy < 0)
            g->vy = 0;
    }
    if (g->y > (K(YMAX) << 8)) {
        g->y = K(YMAX) << 8;
        g->vy = -720;
        if (!g->invuln) {
            g->grounds++;
            hurt(g, K(HIT_GROUND), FX(GROUND), K(BX), K(YMAX));
        }
    }
    int by = g->y >> 8;
    g->drainAcc += K(DRAIN) + MIN(12, g->tick / K(DRAIN_RAMP)) + (g->heating ? K(DRAIN_HEAT) : 0);
    while (g->drainAcc >= 60) {
        g->res--;
        g->drainAcc -= 60;
    }
    int layer = by < 128 ? 0 : by < 160 ? 1 : by < 186 ? 2 : 3;
    if (layer != g->layer) {
        g->layer = layer;
        fx(g, FX(WIND), K(BX), by, layer);
    }
    int target = speeds[g->order[layer]] * (g->section == SEC(GUST) ? 5 : 4) / 4;
    g->spd += (target - g->spd) / 16 + (target > g->spd ? 1 : target < g->spd ? -1 : 0);
    g->dist += g->spd;
    int c = cam(g), bxw = c + K(BX);
    if (in->down_down && !g->cool)
        for (int i = 0; i < K(LETTERS); i++)
            if (!g->letters[i].on) {
                g->letters[i] = (adv_sky_v2_letter_t){
                    1, bxw * 256, (by - 4) * 256, g->spd, g->vy > 0 ? g->vy : 0, by - 4};
                g->cool = K(COOLDOWN);
                g->drops++;
                break;
            }
    for (int i = 0; i < K(OBJS); i++) {
        adv_sky_v2_obj_t *o = &g->objs[i];
        if (!o->type)
            continue;
        if (o->type == T(BIRD)) {
            o->x--;
            o->v++;
        }
        if (o->type == T(STORM))
            o->t++;
        int sx = o->x - c;
        if (sx < K(CULL)) {
            if (o->type == T(HOUSE) && !o->done) {
                g->skipped++;
                if (g->combo)
                    fx(g, FX(SKIP), 20, o->y - 20, 0);
                g->combo = 0;
            }
            memset(o, 0, sizeof(*o));
            continue;
        }
        if (o->done)
            continue;
        if (o->type == T(HOUSE)) {
            if (sx < K(BX) - 40) {
                o->done = 2;
                g->skipped++;
                if (g->combo)
                    fx(g, FX(SKIP), sx, o->y - 20, 0);
                g->combo = 0;
            }
        } else if (o->type == T(TREE)) {
            int hw = o->v ? 6 : 11;
            if (abs(sx - K(BX)) <= hw + K(BASKET_HALF)) {
                if (by > o->y)
                    hurt(g, K(HIT_TREE), FX(HIT), sx, o->y);
                else if (by > o->y - 8 && !o->n && sx <= K(BX)) {
                    o->n = 1;
                    g->nearMiss++;
                    fx(g, FX(NEAR), sx, o->y - 16, 0);
                }
            }
        } else if (o->type == T(BIRD)) {
            int q = o->v & 63, oy = o->y + ((q < 32 ? q : 64 - q) - 16) * 3 / 8;
            if (touches(by, sx, oy, 5)) {
                o->done = 1;
                hurt(g, K(HIT_BIRD), FX(HIT), sx, oy);
            } else if (!o->n && sx < K(BX) && touches(by, sx, oy, 17)) {
                o->n = 1;
                g->nearMiss++;
                fx(g, FX(NEAR), sx, oy - 10, 0);
            }
        } else if (o->type == T(STORM)) {
            if (abs(sx - K(BX)) <= K(STORM_HALF) + K(ENV_R) - 6 &&
                by - K(ENV_DY) - K(ENV_R) <= o->y + K(STORM_H))
                hurt(g, K(HIT_STORM), FX(HIT), sx, o->y);
            int phase = o->t % K(STORM_CYCLE);
            if (phase >= K(STORM_BOLT) && phase < K(STORM_END) &&
                abs(sx - K(BX)) <= K(BOLT_HALF) + K(ENV_R) &&
                by - K(ENV_DY) - K(ENV_R) < o->y + K(STORM_H) + K(BOLT_LEN))
                hurt(g, K(HIT_STORM), FX(HIT), sx, by - K(ENV_DY));
        } else if (o->type == T(TANK) && touches(by, sx, o->y, 9)) {
            o->done = 1;
            g->res = MIN(1000, g->res + K(TANK));
            g->tanks++;
            g->cue = 6;
            fx(g, FX(TANK), sx, o->y, K(TANK));
        }
    }
    for (int i = 0; i < K(LETTERS); i++) {
        adv_sky_v2_letter_t *l = &g->letters[i];
        if (!l->on)
            continue;
        l->vy = MIN(K(LETTER_VMAX), l->vy + K(GRAV));
        l->x += l->vx;
        l->y += l->vy;
        int lx = l->x >> 8, ly = l->y >> 8, land = ly >= K(GROUND) ? K(GROUND) : 0;
        adv_sky_v2_obj_t *hit = NULL;
        for (int j = 0; j < K(OBJS); j++) {
            adv_sky_v2_obj_t *o = &g->objs[j];
            if (o->type != T(HOUSE) || ly < o->y)
                continue;
            int dx = lx - o->x;
            if (abs(dx) <= 24) {
                land = o->y;
                if (!o->done && abs(dx) <= K(BOX_HALF))
                    hit = o;
                break;
            }
        }
        if (!land)
            continue;
        l->on = 0;
        if (hit) {
            hit->done = 1;
            g->combo++;
            g->delivered++;
            if (g->combo > g->best)
                g->best = g->combo;
            int bull = abs(lx - hit->x) <= K(BULL), gold = hit->v & 1, high = hit->y - l->y0 >= K(HIGH_DROP),
                pts = K(PTS) * mult(g);
            if (bull)
                pts *= 2;
            if (gold)
                pts *= K(GOLD);
            if (high)
                pts += pts / 2;
            g->bonus += pts;
            g->res = MIN(1000, g->res + (gold ? K(TIP_GOLD) : K(TIP)));
            if (bull)
                g->bulls++;
            if (gold)
                g->golds++;
            fx(g, bull ? FX(BULL) : FX(DELIVER), hit->x - cam(g), hit->y - 14, pts);
            g->cue = 6;
        } else {
            g->missDrops++;
            g->combo = 0;
            g->res -= K(MISS_COST);
            fx(g, FX(MISS), lx - cam(g), land - 6, 0);
        }
    }
    int ahead = c + K(W) + 40;
    while (g->nextGround < ahead + K(AHEAD) - 320)
        spawn_ground(g, g->nextGround);
    while (g->nextSky < ahead + K(AHEAD) - 320)
        spawn_sky(g, g->nextSky);
    g->meters = (g->dist >> 8) / 16;
    g->score = g->meters / 2 + g->bonus;
    if (g->res <= 0) {
        g->res = 0;
        g->over = 1;
        g->cue = 8;
    }
}
static void start(void *p, uint32_t s)
{
    adv_sky_v2_start(p, s);
}
static void step(void *p, const adv_input_t *i)
{
    adv_sky_v2_step(p, i);
}
static adv_status_t status(const void *p)
{
    const adv_sky_v2_t *g = p;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_sky_v2_game = {"sky", sizeof(adv_sky_v2_t), start, step, status};
