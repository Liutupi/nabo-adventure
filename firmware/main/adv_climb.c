#include "adv_climb.h"
#include "adv_rng.h"
#include <string.h>

static int range(adv_climb_t *g, int lo, int hi) { return lo + (int)(adv_rand(&g->rng) % (unsigned)(hi - lo + 1)); }
static int max_i(int a, int b) { return a > b ? a : b; }
static int min_i(int a, int b) { return a < b ? a : b; }

int adv_climb_hold(const adv_climb_t *g, int r, int s)
{
    if (r < 0 || r > g->gen_top || r < g->gen_top - ADV_CLIMB_RING + 1) return CLIMB_NONE;
    return (g->grid[r % ADV_CLIMB_RING] >> (s * 2)) & 3;
}
bool adv_climb_canteen(const adv_climb_t *g, int r, int s)
{
    return r >= 0 && r <= g->gen_top && r > g->gen_top - ADV_CLIMB_RING && ((g->grid[r % ADV_CLIMB_RING] >> (4 + s)) & 1);
}
static void set_hold(adv_climb_t *g, int r, int s, int t)
{
    uint8_t *c = &g->grid[r % ADV_CLIMB_RING];
    *c = (uint8_t)((*c & ~(3u << (s * 2))) | ((unsigned)t << (s * 2)));
}
static bool solid(const adv_climb_t *g, int r, int s)
{
    int t = adv_climb_hold(g, r, s);
    return t == CLIMB_NORMAL || t == CLIMB_ICE;
}
static int fragile_percent(int h) { return h < 12 ? 0 : min_i(22, 4 + h / 12); }
static int ice_percent(int h) { return h < 80 ? 0 : min_i(25, 5 + (h - 80) / 10); }
static int both_percent(int h) { return max_i(25, 50 - h / 6); }
static int rock_interval(const adv_climb_t *g)
{
    uint32_t cut = g->score * 3u / 5u;   // score never approaches 2^32/3 in a real round
    return cut >= 180 ? 120 : max_i(120, 300 - (int)cut);
}
static int kind(adv_climb_t *g, int h)
{
    int v = (int)(adv_rand(&g->rng) % 100), f = fragile_percent(h), i = ice_percent(h);
    return v < f ? CLIMB_FRAGILE : v < f + i ? CLIMB_ICE : CLIMB_NORMAL;
}

static void generate(adv_climb_t *g)
{
    int k = ++g->gen_top;
    g->grid[k % ADV_CLIMB_RING] = 0;
    if (k <= 4) g->grid[k % ADV_CLIMB_RING] = CLIMB_NORMAL | (CLIMB_NORMAL << 2);   // starter ladder
    else if ((int)(adv_rand(&g->rng) % 100) < both_percent(k)) {
        int left = kind(g, k);
        set_hold(g, k, 0, left);
        int right = kind(g, k);
        set_hold(g, k, 1, right);
    } else {
        int side = (int)(adv_rand(&g->rng) & 1);   // sequenced: side is drawn before the kind
        set_hold(g, k, side, kind(g, k));
    }
    int j = k - 3;   // every hold keeps a move onto a hold that cannot crumble
    if (j >= 0)
        for (int s = 0; s < 2; s++)
            if (adv_climb_hold(g, j, s) && !solid(g, j + 1, 1 - s) && !solid(g, j + 2, s) && !solid(g, k, s))
                set_hold(g, k, s, CLIMB_NORMAL);
    if (g->canteen_next > 0) g->canteen_next--;
    bool a = solid(g, k, 0), b = solid(g, k, 1);
    if (g->canteen_next <= 0 && k >= 20 && (a || b)) {
        int s = a && b ? (int)(adv_rand(&g->rng) & 1) : a ? 0 : 1;
        g->grid[k % ADV_CLIMB_RING] |= (uint8_t)(1u << (4 + s));
        g->canteen_next = range(g, 24, 36);
    }
}

void adv_climb_start(adv_climb_t *g, uint32_t seed)
{
    memset(g, 0, sizeof(*g));
    g->rng = seed; g->res = ADV_RESOURCE_MAX; g->press = -1; g->canteen_next = 30; g->rock_next = 240;
    g->grid[0] = CLIMB_NORMAL | (CLIMB_NORMAL << 2);
    while (g->gen_top < ADV_CLIMB_AHEAD) generate(g);
}

int adv_climb_hand_y(const adv_climb_t *g)
{
    if (g->act == CLIMB_IDLE) return g->row * ADV_CLIMB_ROW;
    int done = g->act_len - g->act_t;
    return g->from_row * ADV_CLIMB_ROW + (g->to_row - g->from_row) * ADV_CLIMB_ROW * done / g->act_len;
}
int adv_climb_body_side(const adv_climb_t *g)
{
    if (g->act == CLIMB_SWITCH && g->act_t * 2 > g->act_len) return g->from_side;
    return g->act == CLIMB_IDLE ? g->side : g->to_side;
}

static void begin(adv_climb_t *g, int act, int len, int to_row, int to_side)
{
    g->act = act; g->act_t = g->act_len = len; g->from_row = g->row; g->from_side = g->side;
    g->to_row = to_row; g->to_side = to_side; g->fragile_t = 0;
}
static void slide(adv_climb_t *g)
{
    int floor = max_i(0, g->gen_top - ADV_CLIMB_FLOOR), r = g->row, s = g->side;
    for (int t = r - 1; t >= floor && t >= r - 3; t--) {
        if (adv_climb_hold(g, t, s)) { begin(g, CLIMB_SLIDE, ADV_CLIMB_SLIDE, t, s); return; }
        if (adv_climb_hold(g, t, 1 - s)) { begin(g, CLIMB_SLIDE, ADV_CLIMB_SLIDE, t, 1 - s); return; }
    }
    begin(g, CLIMB_SLIDE, ADV_CLIMB_SLIDE, r, s);
}
static void feedback(adv_climb_t *g, int message, int frames, int cue)
{
    g->message = message; g->feedback = frames; g->cue = cue;
}
static void act(adv_climb_t *g, int intent)
{
    int to_side = intent == 1 ? 1 - g->side : g->side, to_row = g->row + intent;
    if (adv_climb_hold(g, to_row, to_side))
        begin(g, intent == 1 ? CLIMB_SWITCH : CLIMB_JUMP, intent == 1 ? ADV_CLIMB_SWITCH : ADV_CLIMB_JUMP, to_row, to_side);
    else { g->misses++; g->res -= ADV_CLIMB_MISS; feedback(g, CLIMB_MSG_MISS, 60, 7); slide(g); }
}
static void land(adv_climb_t *g)
{
    bool was_slide = g->act == CLIMB_SLIDE;
    g->row = g->to_row; g->side = g->to_side; g->act = CLIMB_IDLE; g->act_t = g->act_len = 0;
    if (was_slide) return;
    if ((uint32_t)g->row > g->score) {
        uint32_t gained = (uint32_t)g->row - g->score, before = g->score / 50;
        g->score = (uint32_t)g->row;
        g->res = (int)min_i(ADV_RESOURCE_MAX, g->res + ADV_CLIMB_GAIN * (int)gained); g->cue = 1;
        if (g->score / 50 > before) { g->cheer = ADV_CLIMB_CHEER; feedback(g, CLIMB_MSG_MILESTONE, 90, 6); }
    }
    if (adv_climb_canteen(g, g->row, g->side)) {
        g->grid[g->row % ADV_CLIMB_RING] &= (uint8_t)~(1u << (4 + g->side));
        g->res = min_i(ADV_RESOURCE_MAX, g->res + ADV_CLIMB_CANTEEN); g->canteens++;
        feedback(g, CLIMB_MSG_CANTEEN, 60, 6);
    }
    if (adv_climb_hold(g, g->row, g->side) == CLIMB_FRAGILE) g->fragile_t = ADV_CLIMB_FRAGILE;
}

static void rocks(adv_climb_t *g)
{
    if (g->score >= ADV_CLIMB_ROCK_START && --g->rock_next <= 0) {
        for (int i = 0; i < ADV_CLIMB_ROCKS; i++) {
            adv_climb_rock_t *r = &g->rocks[i];
            if (r->on) continue;
            r->on = 1; r->side = adv_rand(&g->rng) % 100 < 60 ? g->side : 1 - g->side;
            r->y = (g->row + ADV_CLIMB_ROCK_SPAWN) * ADV_CLIMB_ROW;
            break;
        }
        g->rock_next = rock_interval(g) + range(g, 0, 60);
    }
    int hand = adv_climb_hand_y(g), side = adv_climb_body_side(g);
    for (int i = 0; i < ADV_CLIMB_ROCKS; i++) {
        adv_climb_rock_t *r = &g->rocks[i];
        if (!r->on) continue;
        r->y -= ADV_CLIMB_ROCK_V;
        if (r->y < (g->row - 6) * ADV_CLIMB_ROW) { r->on = 0; continue; }
        if (!g->invuln && r->side == side && r->y <= hand + ADV_CLIMB_BODY_HI && r->y + ADV_CLIMB_ROCK_H >= hand - ADV_CLIMB_BODY_LO) {
            r->on = 0; g->res -= ADV_CLIMB_HIT; g->hits++; g->invuln = ADV_CLIMB_INVULN; g->queue = 0;
            feedback(g, CLIMB_MSG_HIT, 60, 7);
            if (g->act != CLIMB_SLIDE) {
                if (g->act != CLIMB_IDLE) {   // an interrupted move resolves to the nearer end
                    bool first = g->act_t * 2 > g->act_len;
                    g->row = first ? g->from_row : g->to_row; g->side = first ? g->from_side : g->to_side;
                }
                slide(g);
            }
        }
    }
}

void adv_climb_step(adv_climb_t *g, const adv_input_t *input)
{
    g->tick++; g->cue = 0;
    if (g->invuln > 0) g->invuln--;
    if (g->cheer > 0) g->cheer--;
    if (g->feedback > 0) g->feedback--;
    if (g->over) return;
    int intent = 0;
    if (input->ok_down) g->press = 0;
    else if (g->press >= 0 && g->press < 255) g->press++;
    if (input->ok_up && g->press >= 0) {
        intent = g->press < ADV_CLIMB_TAP ? 1 : g->press >= ADV_CLIMB_CHARGE3 ? 3 : 2;
        g->press = -1;
    }
    if (intent) g->queue = intent;
    if (g->act != CLIMB_IDLE && --g->act_t <= 0) land(g);
    if (g->act == CLIMB_IDLE && g->queue) { int q = g->queue; g->queue = 0; g->cheer = 0; act(g, q); }
    if (g->act == CLIMB_IDLE && g->fragile_t > 0 && --g->fragile_t == 0) {
        set_hold(g, g->row, g->side, CLIMB_NONE); g->crumbles++;
        feedback(g, CLIMB_MSG_CRUMBLE, 60, 7); slide(g);
    }
    while (g->gen_top < max_i(g->row, g->to_row) + ADV_CLIMB_AHEAD) generate(g);
    bool icy = g->act == CLIMB_IDLE && adv_climb_hold(g, g->row, g->side) == CLIMB_ICE;
    g->drain_acc += icy ? ADV_CLIMB_ICE_DRAIN : ADV_CLIMB_DRAIN;
    while (g->drain_acc >= 60) { g->res--; g->drain_acc -= 60; }
    rocks(g);
    if (g->res <= 0) { g->res = 0; g->over = 1; g->cue = 8; }
}

static void start_game(void *state, uint32_t seed) { adv_climb_start(state, seed); }
static void step_game(void *state, const adv_input_t *input) { adv_climb_step(state, input); }
static adv_status_t status_game(const void *state)
{
    const adv_climb_t *g = state;
    return (adv_status_t){g->score, g->res, g->over != 0, (uint8_t)g->cue};
}
const adv_game_t adv_climb_game = {"climb", sizeof(adv_climb_t), start_game, step_game, status_game};
