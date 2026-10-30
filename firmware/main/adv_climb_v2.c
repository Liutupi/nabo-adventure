// CLIMB V2 reference port: alternating hands, traverses, ice and timed rocks.
#include "adv_climb_v2.h"
#include "adv_v2_math.h"
#include <string.h>
#define K(n) CLIMB_V2_##n
#define H(n) CLIMB_V2_H_##n
#define ITEM(n) CLIMB_V2_ITEM_##n
#define SEC(n) CLIMB_V2_SEC_##n
#define FX(n) CLIMB_V2_FX_##n
#define MIN v2_min
#define MAX v2_max
static int rnd(adv_climb_v2_t *g, int n)
{
    return (int)(adv_rand(&g->rng) % (uint32_t)n);
}
static int lane_x(int lane)
{
    return lane ? 216 : 104;
}
static adv_climb_v2_row_t *row_at(adv_climb_v2_t *g, int row)
{
    return &g->rows[row % K(ROWS)];
}
static int hold_at(adv_climb_v2_t *g, int row, int lane)
{
    adv_climb_v2_row_t *o = row_at(g, row);
    return lane ? o->h1 : o->h0;
}
static int side_of(int row, int lane)
{
    return (row + lane) & 1;
}
static int hold_x(int row, int lane)
{
    return lane_x(lane) + (side_of(row, lane) ? K(HOLD_DX) : -K(HOLD_DX));
}
static int mult(const adv_climb_v2_t *g)
{
    return 1 + MIN(4, g->combo / 6);
}
static void fx(adv_climb_v2_t *g, int kind, int x, int y, int val)
{
    g->fx[g->fxHead] = (adv_climb_v2_fx_t){kind, x, y, val, 0};
    g->fxHead = (g->fxHead + 1) % 6;
}
static int pick(adv_climb_v2_t *g)
{
    int v = rnd(g, 100), ice = g->section == SEC(ICE) ? 45 : 10, fr = g->section == SEC(CRUMBLE) ? 45 : 10;
    return v < ice ? H(ICE) : v < ice + fr ? H(FRAGILE) : H(NORMAL);
}
static void gen(adv_climb_v2_t *g)
{
    int r = g->genRow++;
    adv_climb_v2_row_t *o = row_at(g, r);
    if (r < 3) {
        *o = (adv_climb_v2_row_t){H(NORMAL), H(NORMAL), 0, 0};
        return;
    }
    int h[2];
    h[0] = pick(g);
    h[1] = pick(g);
    for (int l = 0; l < 2; l++) {
        if (g->blankRun[l] > 0) {
            h[l] = H(BLANK);
            g->blankRun[l]--;
        } else if (!g->blankRun[1 - l] && r > 6 && rnd(g, 100) < 9) {
            g->blankRun[l] = 1 + rnd(g, 3);
            h[l] = H(BLANK);
        }
    }
    if (h[0] == H(BLANK) && h[1] == H(BLANK))
        h[rnd(g, 2)] = H(NORMAL);
    int items[2] = {0, 0};
    if (rnd(g, 100) < 7) {
        int l = rnd(g, 2);
        if (h[l])
            items[l] = rnd(g, 100) < 45 ? ITEM(CANTEEN) : ITEM(FLAG);
    }
    *o = (adv_climb_v2_row_t){h[0], h[1], items[0], items[1]};
}
void adv_climb_v2_start(adv_climb_v2_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed;
    g->res = 1000;
    g->lastGrab = -99;
    g->nextRock = 420;
    for (int r = 0; r <= K(AHEAD); r++)
        gen(g);
}
static void slip(adv_climb_v2_t *g, int kind)
{
    if (g->row > 0)
        g->row--;
    while (g->row > 0 && !hold_at(g, g->row, g->lane))
        g->row--;
    g->stun = K(STUN);
    g->res -= K(SLIP);
    g->combo = 0;
    g->ice = 0;
    g->crumble = 0;
    g->slips++;
    g->cue = 7;
    g->tween = K(TWEEN);
    fx(g, kind, lane_x(g->lane), K(NY) - 30, 0);
}
static void arrive(adv_climb_v2_t *g)
{
    int h = hold_at(g, g->row, g->lane);
    adv_climb_v2_row_t *o = row_at(g, g->row);
    int it = g->lane ? o->i1 : o->i0;
    int interval = (int)g->tick - g->lastGrab;
    bool rhythm = interval <= K(RHYTHM) || (g->section == SEC(SPRINT) && interval <= K(RHYTHM) + 10);
    g->lastGrab = (int)g->tick;
    g->grabs++;
    if (rhythm) {
        g->combo++;
        g->rhythmGrabs++;
        if (g->combo > g->best)
            g->best = g->combo;
    } else
        g->combo = MAX(0, g->combo - 2);
    g->res =
        MIN(1000, g->res + MAX(K(GAIN_MIN), (rhythm ? K(GAIN_RHYTHM) : K(GAIN)) - g->row / K(GAIN_FADE)));
    g->bonus += mult(g) * (g->section == SEC(SPRINT) ? 2 : 1);
    g->crumble = h == H(FRAGILE) ? K(CRUMBLE) : 0;
    if (it) {
        if (g->lane)
            o->i1 = 0;
        else
            o->i0 = 0;
        if (it == ITEM(CANTEEN)) {
            g->res = MIN(1000, g->res + K(CANTEEN));
            g->canteens++;
            fx(g, FX(CANTEEN), hold_x(g->row, g->lane), K(NY) - 20, K(CANTEEN));
        } else {
            int p = K(FLAG) * mult(g);
            g->bonus += p;
            g->flags++;
            fx(g, FX(FLAG), hold_x(g->row, g->lane), K(NY) - 20, p);
        }
        g->cue = 6;
    }
    if (g->combo && g->combo % 10 == 0)
        fx(g, FX(RHYTHM), 160, 60, g->combo);
    g->tween = K(TWEEN);
}
void adv_climb_v2_step(adv_climb_v2_t *g, const adv_input_t *in)
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
    if (g->tween > 0)
        g->tween--;
    if (g->tick >= K(CALM) && (g->tick - K(CALM)) % K(EVERY) == 0) {
        g->section = 1 + (g->tick - K(CALM)) / K(EVERY) % 5;
        g->sectionT = K(SECTION_LEN);
        fx(g, FX(SECTION), 160, 100, g->section);
    }
    if (g->sectionT > 0 && --g->sectionT == 0)
        g->section = 0;
    if ((int)g->tick - g->lastGrab > K(COMBO_IDLE) && g->combo)
        g->combo = 0;
    if (g->stun > 0)
        g->stun--;
    else if (g->trav > 0) {
        if (--g->trav == 0) {
            g->lane ^= 1;
            while (g->row > 0 && !hold_at(g, g->row, g->lane))
                g->row--;
            g->crumble = hold_at(g, g->row, g->lane) == H(FRAGILE) ? K(CRUMBLE) : 0;
            g->tween = K(TWEEN);
        }
    } else if (g->ice) {
        int held = g->iceSide ? in->up_held : in->ok_held;
        if (!held) {
            g->iceSlips++;
            slip(g, FX(SLIP));
        } else if (--g->ice == 0)
            arrive(g);
    } else if (in->down_down) {
        g->trav = K(TRAVERSE);
        g->res -= K(TRAV_COST);
        g->traverses++;
        g->crumble = 0;
        fx(g, FX(TRAVERSE), lane_x(g->lane), K(NY), 0);
    } else if ((in->ok_down || in->up_down) && g->tween <= 2) {
        int side = in->ok_down && !in->up_down   ? 0
                   : in->up_down && !in->ok_down ? 1
                                                 : -1,
            next = g->row + 1, h = hold_at(g, next, g->lane);
        if (side < 0)
            slip(g, FX(SLIP));
        else if (!h) {
            g->stun = 8;
            g->combo = 0;
            fx(g, FX(NOHOLD), lane_x(g->lane), K(NY) - 50, 0);
        } else if (side != side_of(next, g->lane))
            slip(g, FX(SLIP));
        else {
            g->row = next;
            if (h == H(ICE)) {
                g->ice = K(ICE_HOLD);
                g->iceSide = side;
                g->tween = K(TWEEN);
            } else
                arrive(g);
        }
    }
    if (g->crumble > 0 && !g->trav && --g->crumble == 0) {
        g->crumbles++;
        adv_climb_v2_row_t *o = row_at(g, g->row);
        if (g->lane)
            o->h1 = H(BLANK);
        else
            o->h0 = H(BLANK);
        slip(g, FX(CRUMBLE));
    }
    g->drainAcc += K(DRAIN) + MIN(K(DRAIN_MAX), g->row / K(DRAIN_ROWS));
    while (g->drainAcc >= 60) {
        g->res--;
        g->drainAcc -= 60;
    }
    if ((int)g->tick >= g->nextRock) {
        for (int i = 0; i < K(ROCKS); i++)
            if (!g->rocks[i].on) {
                g->rocks[i] = (adv_climb_v2_rock_t){1, rnd(g, 2), K(ROCK_WARN), K(ROCK_TOP), 0};
                break;
            }
        g->nextRock =
            g->tick + (g->section == SEC(ROCKS) ? 80 : 200) + rnd(g, g->section == SEC(ROCKS) ? 60 : 180);
    }
    for (int i = 0; i < K(ROCKS); i++) {
        adv_climb_v2_rock_t *k = &g->rocks[i];
        if (!k->on)
            continue;
        if (k->t > 0) {
            k->t--;
            continue;
        }
        k->y += K(ROCK_V);
        if (!k->n && k->y >= K(NY) - 56 && k->y <= K(NY) + 4) {
            bool in_lane = g->trav ? (g->trav > K(TRAVERSE) / 2 ? g->lane == k->lane : g->lane != k->lane)
                                   : g->lane == k->lane;
            if (in_lane && !g->invuln) {
                k->n = 1;
                g->rockHits++;
                g->res -= K(ROCK_HIT) - K(SLIP);
                g->invuln = K(INVULN);
                slip(g, FX(ROCK));
            } else if (!in_lane && k->y >= K(NY) - 4) {
                k->n = 1;
                g->nearMiss++;
                fx(g, FX(NEAR), lane_x(g->lane), K(NY) - 40, 0);
            }
        }
        if (k->y > K(H) + 20)
            k->on = 0;
    }
    while (g->genRow <= g->row + K(AHEAD))
        gen(g);
    g->meters = g->row / 2;
    g->score = g->meters + g->bonus;
    if (g->res <= 0) {
        g->res = 0;
        g->over = 1;
        g->cue = 8;
    }
}
static void start(void *p, uint32_t s)
{
    adv_climb_v2_start(p, s);
}
static void step(void *p, const adv_input_t *i)
{
    adv_climb_v2_step(p, i);
}
static adv_status_t status(const void *p)
{
    const adv_climb_v2_t *g = p;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_climb_v2_game = {"climb", sizeof(adv_climb_v2_t), start, step, status};
