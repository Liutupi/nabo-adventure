// NIGHT V2 rules; see adv_night.h. Mirrors prototype/adv_night_v2.js line by line, including the
// order of every random draw, so tests/night_golden replays exactly.
#include "adv_night.h"
#include "adv_rng.h"
#include <stdlib.h>
#include <string.h>

static const int SPEED[3] = {141, 294, 563}, SCREEN[3] = {78, 112, 156};
enum {
    LIGHT_START = 720000, DECAY = 420, RUN_COST = 220, FLY_LIGHT = 36000, FLY_LIGHT_MIN = 18000, GOLD_LIGHT = 150000,
    MULTI_LIGHT = 60000, WHIFF = 16000, MOTH = 120000, TRIP = 130000, OWL = 200000, BURST_LIGHT = 160000,
    METER = 30, METER_STEP = 12, BURST = 150, OWL_STUN = 30, OWL_HIT = 18, OWL_NEAR = 44, CALM = 900, EVERY = 1500, EVENT_LEN = 480,
};
static const int16_t QSIN[65] = {0,101,201,301,401,501,601,700,799,897,995,1092,1189,1285,1380,1474,1567,1660,1751,1842,1931,2019,
    2106,2191,2276,2359,2440,2520,2598,2675,2751,2824,2896,2967,3035,3102,3166,3229,3290,3349,3406,3461,3513,3564,3612,3659,3703,
    3745,3784,3822,3857,3889,3920,3948,3973,3996,4017,4036,4052,4065,4076,4085,4091,4095,4096};

int adv_night_isin(int i)
{
    i &= 255;
    return i < 64 ? QSIN[i] : i < 128 ? QSIN[128 - i] : i < 192 ? -QSIN[i - 128] : -QSIN[256 - i];
}
static int icos(int i) { return adv_night_isin(i + 64); }
static int rnd(adv_night_t *g, int n) { return (int)(adv_rand(&g->rng) % (uint32_t)n); }
static int px(int32_t q) { return q >> 8; }
static int imin(int a, int b) { return a < b ? a : b; }
static int imax(int a, int b) { return a > b ? a : b; }

int adv_night_fly_y(const adv_night_fly_t *f, uint32_t tick)
{
    uint32_t phase = (uint32_t)f->ph + tick * (uint32_t)f->freq;
    return f->base_y + f->amp * adv_night_isin((int)(phase >> 8)) / 4096;
}
static int speed_of(const adv_night_t *g, int gait) { return SPEED[gait] * (30000 + imin(15000, px(g->x))) / 30000; }
// 2026-10-30: ramp 9000 -> 5400 so a strong player's run tops out near three and a half minutes (adv_night.js DECAY_RAMP)
enum { DECAY_RAMP = 5400 };
static int decay(const adv_night_t *g) { return DECAY * (DECAY_RAMP + (int)(g->tick < 1000000u ? g->tick : 1000000u)) / DECAY_RAMP; }
int adv_night_radius(const adv_night_t *g) { return g->burst > 0 ? 220 : 34 + g->light * 15 / 100000; }
int adv_night_mult(const adv_night_t *g) { return 1 + imin(4, g->combo / 6); }
int adv_night_meter_full(const adv_night_t *g) { return METER + METER_STEP * g->bursts; }

void adv_night_start(adv_night_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed; g->res = 720; g->light = LIGHT_START; g->screen = SCREEN[1] << 8; g->gait = 1; g->last_swing = -1000;
    g->next_group = 120 << 8; g->next_root = 520 << 8;
}

static void fx(adv_night_t *g, int kind, int x, int y, int val)
{
    g->fx[g->fx_head] = (adv_night_fx_t){kind, x, y, val, 0};
    g->fx_head = (g->fx_head + 1) % ADV_NIGHT_FX;
}
static void lose(adv_night_t *g, int amount, int kind)
{
    g->loss[kind] += imin(imax(g->light, 0), amount); g->light -= amount; g->last_loss = kind;
}
static void gain(adv_night_t *g, int amount) { g->light = imin(ADV_NIGHT_LIGHT_MAX, g->light + amount); }
static void detach(adv_night_t *g, int slot) { for (int i = 0; i < ADV_NIGHT_MOTHS; i++) if (g->moths[i].host == slot + 1) g->moths[i].host = 0; }

static void spawn_group(adv_night_t *g)
{
    bool swarm = g->event == NIGHT_EV_SWARM;
    int n = (swarm ? 5 : 3) + rnd(g, swarm ? 5 : 4);
    bool high = rnd(g, 100) < 28;
    int base_y = high ? 104 + rnd(g, 11) : 128 + rnd(g, 41);
    int amp = high ? 26 + rnd(g, 11) : 10 + rnd(g, 27);
    int freq = 261 + rnd(g, 363);
    int vx = -179 + rnd(g, 257);
    int ph = rnd(g, 65536);
    int gold_at = -1;
    if (g->tick > 600 && rnd(g, 100) < 22) gold_at = rnd(g, n);
    int32_t x = adv_night_cam(g) + (340 << 8);
    for (int i = 0; i < n; i++) {
        int dy = rnd(g, 17) - 8;
        int gap = 10 + rnd(g, 11);
        bool gold = i == gold_at;
        int slot = -1;
        for (int k = 0; k < ADV_NIGHT_FLIES; k++) if (!g->flies[k].type) { slot = k; break; }
        if (slot < 0) { g->blocked++; x += gap << 8; continue; }
        g->flies[slot] = (adv_night_fly_t){gold ? 2 : 1, x, base_y + dy, amp, (ph + i * 5734) & 0xffff, freq, vx};
        x += gap << 8;
        if (gold) {
            g->golds++;
            for (int k = 0; k < 2; k++) {
                int a = rnd(g, 65536);
                int rr = 15 + rnd(g, 9);
                int sign = rnd(g, 2) ? -1 : 1;
                int va = sign * (626 + rnd(g, 417));
                for (int m = 0; m < ADV_NIGHT_MOTHS; m++) if (!g->moths[m].host && !g->moths[m].rr) {
                    g->moths[m] = (adv_night_moth_t){slot + 1, g->flies[slot].x, (base_y + dy) << 8, a, rr, va};
                    break;
                }
            }
        }
    }
    int gap = (swarm ? 70 : 150);
    gap += rnd(g, swarm ? 71 : 121);
    g->next_group = g->x + (gap << 8);
}

static void spawn_owl(adv_night_t *g)
{
    for (int i = 0; i < ADV_NIGHT_OWLS; i++) if (!g->owls[i].live) {
        g->owls[i] = (adv_night_owl_t){g->x + speed_of(g, g->gait) * ADV_NIGHT_OWL_WARN, ADV_NIGHT_OWL_WARN, 1};
        return;
    }
    g->blocked++;
}

static void catch_fly(adv_night_t *g, int slot, bool burst)
{
    adv_night_fly_t *f = &g->flies[slot];
    int y = adv_night_fly_y(f, g->tick);
    g->combo++; g->caught++; if (g->combo > g->max_combo) g->max_combo = g->combo;
    int m = adv_night_mult(g);
    if (f->type == 2) { g->score += 5u * (uint32_t)m; gain(g, GOLD_LIGHT); g->meter += 5; fx(g, NIGHT_FX_GOLD, px(f->x), y, 5 * m); }
    else {
        g->score += (uint32_t)m; gain(g, imax(FLY_LIGHT_MIN, FLY_LIGHT - (int)g->tick)); g->meter += 1;
        if (!burst) fx(g, NIGHT_FX_FLY, px(f->x), y, m);
    }
    g->meter = imin(adv_night_meter_full(g), g->meter);
    f->type = 0; detach(g, slot);
}

void adv_night_step(adv_night_t *g, const adv_input_t *in)
{
    g->cue = 0;
    for (int i = 0; i < ADV_NIGHT_FX; i++) if (g->fx[i].kind && ++g->fx[i].t >= 60) g->fx[i].kind = 0;
    if (g->over) return;
    g->tick++;
    g->presses += (in->ok_down ? 1 : 0) + (in->up_down ? 1 : 0) + (in->down_down ? 1 : 0);

    if (g->tick >= CALM && (g->tick - CALM) % EVERY == 0) {
        g->event = 1 + (int)((g->tick - CALM) / EVERY % 3); g->event_t = EVENT_LEN; fx(g, NIGHT_FX_EVENT, 0, 0, g->event);
        if (g->event == NIGHT_EV_OWLS) g->next_owl = (int32_t)g->tick + 40;
    }
    if (g->event_t > 0 && --g->event_t == 0) g->event = 0;

    bool left = in->ok_held, right = in->up_held;
    g->gait = left && !right ? 0 : right && !left ? 2 : 1;
    if (g->stun > 0) g->stun--;
    bool moving = g->stun == 0;
    int prev_foot = px(g->x) + 4;
    if (moving) g->x += speed_of(g, g->gait);
    g->screen += ((SCREEN[moving ? g->gait : 1] << 8) - g->screen) * 15 / 256;

    lose(g, decay(g), NIGHT_LOSS_DECAY);
    if (moving && g->gait == 2) lose(g, RUN_COST, NIGHT_LOSS_RUN);
    if (g->burst > 0) g->burst--;

    if (in->down_down && moving) {
        if (g->meter >= adv_night_meter_full(g) && (int)g->tick - g->last_swing <= ADV_NIGHT_DOUBLE) {
            g->burst = BURST; g->meter = 0; g->bursts++; gain(g, BURST_LIGHT); fx(g, NIGHT_FX_BURST, 0, 0, 0); g->cue = 6;
            int32_t lo = adv_night_cam(g), hi = lo + (ADV_NIGHT_W << 8);
            for (int i = 0; i < ADV_NIGHT_FLIES; i++) if (g->flies[i].type && g->flies[i].x > lo && g->flies[i].x < hi) catch_fly(g, i, true);
            memset(g->moths, 0, sizeof(g->moths));
        } else if (g->swing == 0) { g->swing = ADV_NIGHT_SWING; g->swing_caught = 0; g->swings++; }
        g->last_swing = (int32_t)g->tick;
    }
    if (g->swing > 0) {
        int age = ADV_NIGHT_SWING - g->swing;
        if (age >= ADV_NIGHT_SWING_ON && age <= ADV_NIGHT_SWING_OFF) {
            int nx = px(g->x) + ADV_NIGHT_NET_DX, ny = ADV_NIGHT_GROUND - ADV_NIGHT_NET_DY;
            for (int i = 0; i < ADV_NIGHT_FLIES; i++) {
                const adv_night_fly_t *f = &g->flies[i]; if (!f->type) continue;
                int dx = px(f->x) - nx, dy = adv_night_fly_y(f, g->tick) - ny;
                if (dx * dx + dy * dy <= ADV_NIGHT_NET_R * ADV_NIGHT_NET_R) { catch_fly(g, i, false); g->swing_caught++; g->cue = 6; }
            }
            for (int i = 0; i < ADV_NIGHT_MOTHS; i++) {
                adv_night_moth_t *m = &g->moths[i]; if (!m->rr) continue;
                int dx = px(m->x) - nx, dy = px(m->y) - ny;
                if (dx * dx + dy * dy <= ADV_NIGHT_MOTH_R * ADV_NIGHT_MOTH_R) {
                    fx(g, NIGHT_FX_MOTH, px(m->x), px(m->y), 0); memset(m, 0, sizeof(*m));
                    lose(g, MOTH, NIGHT_LOSS_MOTH); g->combo = 0; g->meter = imax(0, g->meter - 5); g->moth_hits++; g->cue = 7;
                }
            }
        }
        if (--g->swing == 0) {
            if (g->swing_caught == 0) { g->whiffs++; g->combo = 0; lose(g, WHIFF, NIGHT_LOSS_WHIFF); }
            if (g->swing_caught >= 3) {
                g->multi++; gain(g, MULTI_LIGHT);
                fx(g, NIGHT_FX_MULTI, px(g->x) + ADV_NIGHT_NET_DX, ADV_NIGHT_GROUND - 80, g->swing_caught);
            }
        }
    }

    bool wind = g->event == NIGHT_EV_WIND;
    int32_t cull = adv_night_cam(g) - (24 << 8);
    for (int i = 0; i < ADV_NIGHT_FLIES; i++) {
        adv_night_fly_t *f = &g->flies[i]; if (!f->type) continue;
        f->x += f->vx + (wind ? -282 : 0); if (wind) f->ph = (f->ph + 209) & 0xffff;
        if (f->x < cull) { f->type = 0; g->missed++; detach(g, i); }
    }
    int32_t mcull = adv_night_cam(g) - (30 << 8);
    for (int i = 0; i < ADV_NIGHT_MOTHS; i++) {
        adv_night_moth_t *m = &g->moths[i]; if (!m->rr) continue;
        m->a = (m->a + m->va) & 0xffff;
        int ai = m->a >> 8;
        if (m->host) {
            const adv_night_fly_t *h = &g->flies[m->host - 1];
            m->x = h->x + icos(ai) * m->rr / 16; m->y = (adv_night_fly_y(h, g->tick) << 8) + adv_night_isin(ai) * m->rr / 20;
        } else { m->x += -102 + icos(ai) * 205 / 4096; m->y += adv_night_isin(ai * 13 / 10) * 179 / 4096; }
        if (m->x < mcull) memset(m, 0, sizeof(*m));
    }
    if (g->x >= g->next_group) spawn_group(g);

    if (g->x >= g->next_root) {
        int w = 10 + rnd(g, 8), slot = -1;
        for (int i = 0; i < ADV_NIGHT_ROOTS; i++) if (!g->roots[i].state) { slot = i; break; }
        if (slot >= 0) g->roots[slot] = (adv_night_root_t){px(adv_night_cam(g)) + 350, w, 1}; else g->blocked++;
        int gap = 230 + rnd(g, imax(140, 380 - px(g->x) / 120));
        g->next_root = g->x + (gap << 8);
    }
    int foot = px(g->x) + 4;
    for (int i = 0; i < ADV_NIGHT_ROOTS; i++) {
        adv_night_root_t *r = &g->roots[i];
        if (r->state == 1 && prev_foot < r->x && foot >= r->x) {
            if (g->gait == 2 && moving) {
                r->state = 2; g->stun = ADV_NIGHT_TRIP_STUN; g->stun_kind = 1; g->trips++; lose(g, TRIP, NIGHT_LOSS_TRIP); g->combo = 0; g->cue = 7;
                fx(g, NIGHT_FX_TRIP, px(g->x), ADV_NIGHT_GROUND - 70, 0);
            } else { r->state = 3; g->roots_passed++; }
        }
        if (r->state && r->x < px(adv_night_cam(g)) - 40) memset(r, 0, sizeof(*r));
    }

    if (g->event == NIGHT_EV_OWLS) {
        if ((int32_t)g->tick >= g->next_owl) { spawn_owl(g); g->next_owl = (int32_t)g->tick + 110 + rnd(g, 41); }
    } else if (g->tick > 3600) {
        bool any = false;
        for (int i = 0; i < ADV_NIGHT_OWLS; i++) any |= g->owls[i].live != 0;
        if (!any && rnd(g, 10000) < 12) spawn_owl(g);
    }
    for (int i = 0; i < ADV_NIGHT_OWLS; i++) {
        adv_night_owl_t *o = &g->owls[i]; if (!o->live) continue;
        if (--o->t == 0) {
            int32_t d = abs(g->x - o->tx);
            if (d < OWL_HIT << 8 && g->burst == 0) {
                lose(g, OWL, NIGHT_LOSS_OWL); g->stun = imax(g->stun, OWL_STUN); g->stun_kind = 2; g->owl_hits++; g->combo = 0; g->cue = 7;
                fx(g, NIGHT_FX_OWL, px(g->x), ADV_NIGHT_GROUND - 72, 0);
            } else if (d < OWL_NEAR << 8) { g->owl_near++; fx(g, NIGHT_FX_NEAR, px(g->x), ADV_NIGHT_GROUND - 72, 0); }
        }
        if (o->t < -40) memset(o, 0, sizeof(*o));
    }

    if (g->light <= 0) { g->light = 0; g->over = 1; g->cue = 8; }
    g->res = (g->light + 999) / 1000;
}

static void start_game(void *state, uint32_t seed) { adv_night_start(state, seed); }
static void step_game(void *state, const adv_input_t *in) { adv_night_step(state, in); }
static adv_status_t status_game(const void *state)
{
    const adv_night_t *g = state;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_night_game = {"night", sizeof(adv_night_t), start_game, step_game, status_game};
