// Jump versus model (see adv_vs.h). Comments stay ASCII: every non-ASCII character in adv_*.c
// ends up in the collection font subsets.
#include "adv_vs.h"
#include <string.h>

#define HELLO_LOBBY_MS 300
#define HELLO_BUSY_MS 1000
#define PEER_TTL_MS 3000
#define INVITE_RESEND_MS 700
#define WAIT_TIMEOUT_MS 15000
#define INVITED_TTL_MS 3000
#define COUNTDOWN_MS 3000
#define START_RESEND_MS 200
#define STATE_MS 250
#define RESULT_STATE_MS 500
#define LOST_MS 4000
#define NOTICE_MS 4000

static const uint8_t kZero[6];

static uint32_t rnd(uint32_t *s)
{
    uint32_t t = (*s += 0x6D2B79F5u);
    t = (t ^ (t >> 15)) * (t | 1u);
    t ^= t + (t ^ (t >> 7)) * (t | 61u);
    return t ^ (t >> 14);
}
static bool after(uint32_t now, uint32_t at) { return (int32_t)(now - at) >= 0; }
static void put32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24); }
static void put16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static uint32_t get32(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }
static uint16_t get16(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
static uint8_t checksum(const uint8_t *p) { unsigned s = 0; for (int i = 0; i < ADV_VS_PACKET - 1; i++) s += p[i]; return (uint8_t)(s ^ 0xA5); }

void adv_vs_encode(uint8_t out[ADV_VS_PACKET], int type, const uint8_t to[6], uint32_t session, uint32_t seed,
                   adv_vs_side_t side, bool busy, uint16_t delay, uint16_t seq, uint8_t game)
{
    memset(out, 0, ADV_VS_PACKET);
    out[0] = 'N'; out[1] = 'J'; out[2] = ADV_VS_VERSION; out[3] = (uint8_t)type;
    memcpy(out + 4, to ? to : kZero, 6);
    put32(out + 10, session); put32(out + 14, seed); put32(out + 18, side.score); put16(out + 22, side.steps);
    out[24] = side.over; out[25] = busy; put16(out + 26, delay); put16(out + 28, seq); out[30] = game;
    out[ADV_VS_PACKET - 1] = checksum(out);
}

bool adv_vs_valid(const uint8_t *d, int len)
{
    return d && len == ADV_VS_PACKET && d[0] == 'N' && d[1] == 'J' && d[2] == ADV_VS_VERSION &&
           d[3] >= VS_MSG_HELLO && d[3] <= VS_MSG_BYE && d[24] <= 1 && d[25] <= 1 && d[30] >= 1 && d[30] <= 8 && d[ADV_VS_PACKET - 1] == checksum(d);
}

void adv_vs_name(const uint8_t mac[6], char out[12])
{
    static const char hex[] = "0123456789ABCDEF";
    memcpy(out, "NABO-", 5);
    out[5] = hex[mac[4] >> 4]; out[6] = hex[mac[4] & 15]; out[7] = hex[mac[5] >> 4]; out[8] = hex[mac[5] & 15];
    out[9] = 0;
}

static void send(adv_vs_t *vs, int type, const uint8_t *to, uint16_t delay)
{
    if (!vs->radio || vs->nout >= ADV_VS_OUTBOX) return;
    adv_vs_out_t *o = &vs->out[vs->nout++];
    bool busy = vs->page != VS_LOBBY && vs->page != VS_PICK;
    memcpy(o->to, to ? to : (const uint8_t[6]){255, 255, 255, 255, 255, 255}, 6);
    adv_vs_encode(o->data, type, to, vs->session, vs->seed, vs->mine, busy, delay, ++vs->seq, vs->game ? vs->game : 1);
}

bool adv_vs_pop(adv_vs_t *vs, adv_vs_out_t *out)
{
    if (!vs->nout) return false;
    *out = vs->out[0];
    memmove(vs->out, vs->out + 1, (size_t)(--vs->nout) * sizeof(vs->out[0]));
    return true;
}

static void go(adv_vs_t *vs, adv_vs_page_t page, uint32_t now)
{
    vs->page = page;
    vs->page_at = now;
    vs->hello_at = now;   // announce a busy/idle change promptly
}

static void notice(adv_vs_t *vs, adv_vs_note_t note, uint32_t now)
{
    vs->note = note;
    vs->bot = false;
    go(vs, VS_NOTICE, now);
}

void adv_vs_init(adv_vs_t *vs, const uint8_t me[6], bool radio, uint32_t rng, uint32_t now, int game)
{
    memset(vs, 0, sizeof(*vs));
    memcpy(vs->me, me, 6);
    vs->radio = radio;
    vs->rng = rng ? rng : 1;
    vs->game = game >= 1 && game <= 8 ? (uint8_t)game : 0;
    vs->pick = vs->game ? vs->game - 1 : 0;
    go(vs, vs->game ? VS_LOBBY : VS_PICK, now);
}

int adv_vs_countdown(const adv_vs_t *vs, uint32_t now)
{
    if (vs->page != VS_COUNTDOWN || after(now, vs->go_at)) return 0;
    return (int)((vs->go_at - now + 999) / 1000);
}

static void begin_countdown(adv_vs_t *vs, uint32_t seed, uint32_t session, uint32_t delay, uint32_t now)
{
    vs->seed = seed;
    vs->session = session;
    vs->go_at = now + delay;
    vs->resend_at = now;
    vs->start_acked = vs->bot || !vs->host ? true : false;
    memset(&vs->mine, 0, sizeof(vs->mine));
    memset(&vs->theirs, 0, sizeof(vs->theirs));
    memset(&vs->sent, 0, sizeof(vs->sent));
    vs->outcome = VS_PENDING;
    vs->want_again = vs->they_again = vs->opp_gone = false;
    vs->heard_at = now;
    vs->state_at = now;
    go(vs, VS_COUNTDOWN, now);
}

static void host_start(adv_vs_t *vs, uint32_t now)
{
    vs->host = true;
    begin_countdown(vs, rnd(&vs->rng) | 1u, rnd(&vs->rng) | 1u, COUNTDOWN_MS, now);
}

static void back_to_lobby(adv_vs_t *vs, uint32_t now)
{
    vs->bot = vs->accepted = vs->host = false;
    vs->note = VS_NOTE_NONE;
    vs->cursor = 0;
    go(vs, vs->game ? VS_LOBBY : VS_PICK, now);
}

int adv_vs_key(adv_vs_t *vs, int button, int event, uint32_t now)
{
    if (vs->page == VS_LOBBY && button == ADV_VS_UP && event == ADV_VS_LONG) {   // back to the game list
        vs->cursor = 0;
        go(vs, VS_PICK, now);
        return VS_FX_REDRAW;
    }
    if (event != ADV_VS_CLICK) return 0;
    switch (vs->page) {
    case VS_PICK:
        if (button == ADV_VS_UP) vs->pick = (vs->pick + 7) % 8;
        else if (button == ADV_VS_DOWN) vs->pick = (vs->pick + 1) % 8;
        else { vs->game = (uint8_t)(vs->pick + 1); vs->cursor = 0; go(vs, VS_LOBBY, now); }
        return VS_FX_REDRAW;
    case VS_LOBBY: {
        int n = vs->npeers + 1;
        if (button == ADV_VS_UP) vs->cursor = (vs->cursor + n - 1) % n;
        else if (button == ADV_VS_DOWN) vs->cursor = (vs->cursor + 1) % n;
        else if (vs->cursor == 0) { vs->bot = true; host_start(vs, now); return VS_FX_START | VS_FX_REDRAW; }
        else {
            const adv_vs_peer_t *p = &vs->peers[vs->cursor - 1];
            if (p->busy) return 0;
            memcpy(vs->opp, p->mac, 6);
            vs->host = true;
            vs->resend_at = now;
            go(vs, VS_WAIT, now);
            send(vs, VS_MSG_INVITE, vs->opp, 0);
        }
        return VS_FX_REDRAW;
    }
    case VS_WAIT:
        if (button == ADV_VS_OK) { send(vs, VS_MSG_CANCEL, vs->opp, 0); back_to_lobby(vs, now); return VS_FX_REDRAW; }
        return 0;
    case VS_INVITED:
        if (vs->accepted) return 0;
        if (button == ADV_VS_OK) {
            vs->accepted = true;
            vs->resend_at = now;
            send(vs, VS_MSG_ACCEPT, vs->opp, 0);
        } else if (button == ADV_VS_DOWN) {
            back_to_lobby(vs, now);   // first, so the decline carries busy=0 ("declined", not "busy")
            send(vs, VS_MSG_DECLINE, vs->opp, 0);
        }
        return VS_FX_REDRAW;
    case VS_RESULT:
        if (button == ADV_VS_OK) {
            if (vs->bot) { host_start(vs, now); return VS_FX_START | VS_FX_REDRAW; }
            if (vs->opp_gone || vs->want_again) return 0;
            vs->want_again = true;
            vs->resend_at = now;
            send(vs, VS_MSG_AGAIN, vs->opp, 0);
            if (vs->host && vs->they_again) { host_start(vs, now); return VS_FX_START | VS_FX_REDRAW; }
        } else if (button == ADV_VS_DOWN) {
            if (!vs->bot && !vs->opp_gone) send(vs, VS_MSG_BYE, vs->opp, 0);
            back_to_lobby(vs, now);
        }
        return VS_FX_REDRAW;
    case VS_NOTICE:
        if (button == ADV_VS_OK) { back_to_lobby(vs, now); return VS_FX_REDRAW; }
        return 0;
    default: return 0;
    }
}

static void touch_peer(adv_vs_t *vs, const uint8_t mac[6], bool busy, uint8_t game, uint32_t now)
{
    for (int i = 0; i < vs->npeers; i++)
        if (!memcmp(vs->peers[i].mac, mac, 6)) { vs->peers[i].seen = now; vs->peers[i].busy = busy; vs->peers[i].game = game; return; }
    if (vs->npeers >= ADV_VS_PEERS) return;
    adv_vs_peer_t *p = &vs->peers[vs->npeers++];
    memcpy(p->mac, mac, 6);
    p->seen = now;
    p->busy = busy;
    p->game = game;
}

int adv_vs_packet(adv_vs_t *vs, const uint8_t mac[6], const uint8_t *d, int len, uint32_t now)
{
    if (!adv_vs_valid(d, len) || !memcmp(mac, vs->me, 6)) return 0;
    if (memcmp(d + 4, kZero, 6) && memcmp(d + 4, vs->me, 6)) return 0;   // unicast for someone else
    int type = d[3];
    uint32_t session = get32(d + 10);
    bool busy = d[25];
    touch_peer(vs, mac, type == VS_MSG_HELLO ? busy : true, d[30], now);
    if (type == VS_MSG_HELLO) return vs->page == VS_LOBBY ? VS_FX_REDRAW : 0;
    bool from_opp = !vs->bot && !memcmp(mac, vs->opp, 6);
    if (from_opp) vs->heard_at = now;

    if (type == VS_MSG_INVITE) {
        if (vs->page == VS_LOBBY || vs->page == VS_PICK) {
            vs->game = d[30];   // the inviter chooses the game
            memcpy(vs->opp, mac, 6);
            vs->host = vs->accepted = false;
            vs->heard_at = now;
            go(vs, VS_INVITED, now);
            return VS_FX_REDRAW;
        }
        if (!from_opp) { uint8_t to[6]; memcpy(to, mac, 6); send(vs, VS_MSG_DECLINE, to, 0); }
        return 0;
    }
    if (!from_opp) return 0;
    switch (type) {
    case VS_MSG_CANCEL:
        if (vs->page == VS_INVITED) { notice(vs, VS_NOTE_CANCELLED, now); return VS_FX_REDRAW; }
        return 0;
    case VS_MSG_DECLINE:
        if (vs->page == VS_WAIT) { notice(vs, busy ? VS_NOTE_BUSY : VS_NOTE_DECLINED, now); return VS_FX_REDRAW; }
        return 0;
    case VS_MSG_ACCEPT:
        if (vs->page == VS_WAIT) { host_start(vs, now); send(vs, VS_MSG_START, vs->opp, COUNTDOWN_MS); return VS_FX_START | VS_FX_REDRAW; }
        return 0;
    case VS_MSG_START:
        if ((vs->page == VS_INVITED && vs->accepted) || (vs->page == VS_RESULT && vs->want_again && !vs->host)) {
            uint16_t delay = get16(d + 26);
            vs->host = false;
            vs->game = d[30];
            begin_countdown(vs, get32(d + 14), session, delay > COUNTDOWN_MS ? COUNTDOWN_MS : delay, now);
            send(vs, VS_MSG_STATE, vs->opp, 0);
            return VS_FX_START | VS_FX_REDRAW;
        }
        return 0;
    case VS_MSG_STATE:
        if (session != vs->session) return 0;
        if (vs->page == VS_COUNTDOWN || vs->page == VS_PLAY || vs->page == VS_RESULT) {
            vs->start_acked = true;
            uint32_t score = get32(d + 18);
            // Scores only grow and "over" never clears within a session: drop stale/reordered packets.
            if (score >= vs->theirs.score) vs->theirs.score = score;
            uint16_t steps = get16(d + 22);
            if (steps >= vs->theirs.steps) vs->theirs.steps = steps;
            vs->theirs.over |= d[24];
            return VS_FX_REDRAW;
        }
        return 0;
    case VS_MSG_AGAIN:
        if (vs->page == VS_RESULT && session == vs->session) {
            vs->they_again = true;
            if (vs->host && vs->want_again) { host_start(vs, now); send(vs, VS_MSG_START, vs->opp, COUNTDOWN_MS); return VS_FX_START | VS_FX_REDRAW; }
            return VS_FX_REDRAW;
        }
        return 0;
    case VS_MSG_BYE:
        if (vs->page == VS_WAIT || vs->page == VS_INVITED) { notice(vs, VS_NOTE_CANCELLED, now); return VS_FX_REDRAW; }
        if (vs->page == VS_COUNTDOWN || vs->page == VS_PLAY) { notice(vs, VS_NOTE_LEFT, now); return VS_FX_REDRAW; }
        if (vs->page == VS_RESULT) { vs->opp_gone = true; return VS_FX_REDRAW; }
        return 0;
    default: return 0;
    }
}

void adv_vs_opponent(adv_vs_t *vs, adv_vs_side_t theirs, uint32_t now)
{
    if (!vs->bot) return;
    vs->theirs = theirs;
    vs->heard_at = now;
}

static adv_vs_outcome_t decide(const adv_vs_side_t *me, const adv_vs_side_t *them)
{
    if (me->over && them->over)
        return me->score > them->score ? VS_WIN : me->score < them->score ? VS_LOSE : VS_DRAW;
    if (them->over && me->score > them->score) return VS_WIN;
    if (me->over && them->score > me->score) return VS_LOSE;
    return VS_PENDING;
}

int adv_vs_tick(adv_vs_t *vs, uint32_t now, adv_vs_side_t mine)
{
    int fx = 0;
    for (int i = 0; i < vs->npeers;)
        if (after(now, vs->peers[i].seen + PEER_TTL_MS)) {
            vs->peers[i] = vs->peers[--vs->npeers];
            fx |= VS_FX_REDRAW;
        } else i++;
    if (vs->cursor > vs->npeers) vs->cursor = vs->npeers;
    if (after(now, vs->hello_at)) {
        send(vs, VS_MSG_HELLO, NULL, 0);
        vs->hello_at = now + (vs->page == VS_LOBBY || vs->page == VS_PICK ? HELLO_LOBBY_MS : HELLO_BUSY_MS);
    }
    bool live = !vs->bot && (vs->page == VS_COUNTDOWN || vs->page == VS_PLAY);
    if (live && after(now, vs->heard_at + LOST_MS)) { notice(vs, VS_NOTE_LOST, now); return fx | VS_FX_REDRAW; }
    switch (vs->page) {
    case VS_WAIT:
        if (after(now, vs->page_at + WAIT_TIMEOUT_MS)) { send(vs, VS_MSG_CANCEL, vs->opp, 0); notice(vs, VS_NOTE_NO_ANSWER, now); return fx | VS_FX_REDRAW; }
        if (after(now, vs->resend_at + INVITE_RESEND_MS)) { vs->resend_at = now; send(vs, VS_MSG_INVITE, vs->opp, 0); }
        break;
    case VS_INVITED:
        if (after(now, vs->heard_at + INVITED_TTL_MS + (vs->accepted ? 2000 : 0))) { notice(vs, VS_NOTE_CANCELLED, now); return fx | VS_FX_REDRAW; }
        if (vs->accepted && after(now, vs->resend_at + 500)) { vs->resend_at = now; send(vs, VS_MSG_ACCEPT, vs->opp, 0); }
        break;
    case VS_COUNTDOWN:
        if (vs->host && !vs->bot && !vs->start_acked && after(now, vs->resend_at + START_RESEND_MS)) {
            vs->resend_at = now;
            send(vs, VS_MSG_START, vs->opp, (uint16_t)(after(now, vs->go_at) ? 0 : vs->go_at - now));
        }
        if (!vs->bot && after(now, vs->state_at + STATE_MS)) { vs->state_at = now; send(vs, VS_MSG_STATE, vs->opp, 0); }
        if (after(now, vs->go_at)) { go(vs, VS_PLAY, now); fx |= VS_FX_GO | VS_FX_REDRAW; }
        else fx |= VS_FX_REDRAW * (adv_vs_countdown(vs, now) != adv_vs_countdown(vs, now - 20));
        break;
    case VS_PLAY: {
        vs->mine = mine;
        bool changed = mine.score != vs->sent.score || mine.over != vs->sent.over;
        if (!vs->bot && (changed || after(now, vs->state_at + STATE_MS))) {
            vs->state_at = now;
            vs->sent = mine;
            send(vs, VS_MSG_STATE, vs->opp, 0);
        }
        vs->outcome = decide(&vs->mine, &vs->theirs);
        if (vs->outcome != VS_PENDING) {
            if (vs->outcome == VS_WIN) vs->wins++;
            else if (vs->outcome == VS_LOSE) vs->losses++;
            else vs->draws++;
            if (!vs->bot) { vs->state_at = now; send(vs, VS_MSG_STATE, vs->opp, 0); }
            go(vs, VS_RESULT, now);
            fx |= VS_FX_END | VS_FX_REDRAW;
        }
        break;
    }
    case VS_RESULT:
        if (vs->bot) break;
        if (!vs->opp_gone && after(now, vs->heard_at + LOST_MS)) { vs->opp_gone = true; fx |= VS_FX_REDRAW; }
        if (!vs->opp_gone && after(now, vs->state_at + RESULT_STATE_MS)) {
            vs->state_at = now;
            send(vs, vs->want_again ? VS_MSG_AGAIN : VS_MSG_STATE, vs->opp, 0);
        }
        break;
    case VS_NOTICE:
        if (after(now, vs->page_at + NOTICE_MS)) { back_to_lobby(vs, now); fx |= VS_FX_REDRAW; }
        break;
    default: break;
    }
    return fx;
}

void adv_vs_leave(adv_vs_t *vs)
{
    vs->nout = 0;
    if (!vs->bot && vs->page != VS_LOBBY && vs->page != VS_PICK && vs->page != VS_NOTICE) send(vs, VS_MSG_BYE, vs->opp, 0);
}

void adv_vs_ghost_start(adv_vs_ghost_t *ghost, uint32_t seed, uint32_t bronze, uint32_t gold, uint32_t now)
{
    uint32_t r = seed ^ 0x6057ACEu;
    ghost->start = now;
    ghost->duration = 30000 + rnd(&r) % 60000;            // 30..90 s
    ghost->target = bronze + (gold > bronze ? rnd(&r) % (gold - bronze + 1) : 0);
}

adv_vs_side_t adv_vs_ghost_tick(const adv_vs_ghost_t *ghost, uint32_t now)
{
    uint32_t t = now - ghost->start;
    adv_vs_side_t s = {0, 0, false};
    if (t >= ghost->duration) { s.score = ghost->target; s.over = true; return s; }
    // Ease-in: early points come slowly, like a real run building combos.
    uint64_t f = (uint64_t)t * t / ghost->duration;
    s.score = (uint32_t)((uint64_t)ghost->target * f / ghost->duration);
    s.steps = (uint16_t)(t / 1000);
    return s;
}

adv_vs_side_t adv_vs_side_of(const nabo_jump_t *g)
{
    adv_vs_side_t s = {g->score, (uint16_t)(g->steps > 65535 ? 65535 : g->steps), g->phase >= JUMP_FALLING};
    return s;
}

// ---------- NABO sparring bot ----------

void adv_vs_bot_start(adv_vs_bot_t *bot, uint32_t seed, uint32_t now)
{
    memset(bot, 0, sizeof(*bot));
    nabo_jump_reset(&bot->game, seed, 0);
    bot->rng = seed ^ 0x5EED0B07u;
    bot->act_at = now;
}

adv_vs_side_t adv_vs_bot_tick(adv_vs_bot_t *bot, uint32_t now)
{
    nabo_jump_t *g = &bot->game;
    nabo_jump_tick(g, now);
    if (g->phase == JUMP_READY && bot->state == 0) {
        bot->act_at = now + 380 + rnd(&bot->rng) % 520;   // look, then press
        bot->state = 1;
    } else if (bot->state == 1 && g->phase == JUMP_READY && after(now, bot->act_at)) {
        nabo_jump_press(g, now);
        int ideal = (g->gap - 4) * 1000 / 150;
        int spread = 70 + (g->steps < 30 ? g->steps : 30) * 3;
        int hold = ideal + (int)(rnd(&bot->rng) % (unsigned)(2 * spread + 1)) - spread;
        bot->act_at = now + (uint32_t)(hold < 20 ? 20 : hold);
        bot->state = 2;
    } else if (bot->state == 2 && after(now, bot->act_at)) {
        nabo_jump_release(g, now);
        bot->state = 0;
    }
    return adv_vs_side_of(g);
}
