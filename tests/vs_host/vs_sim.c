// Two adv_vs instances talking through a simulated ESP-NOW link (latency, loss, reorder, cut).
// Each side's "player" is the NABO bot with its own error RNG, so real jump games decide scores.
// Prints one JSON line per scenario; tests/test_adv_versus.py checks them.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "adv_vs.h"

#define MAXQ 256
typedef struct { uint32_t at; int to; uint8_t from[6]; uint8_t data[ADV_VS_PACKET]; } pkt_t;
static pkt_t q[MAXQ];
static int nq;
static uint32_t net_rng = 12345;
static int loss_pct, cut_from = -1;   // cut_from: side whose packets are no longer delivered
static unsigned sent_count;

static uint32_t r32(void) { net_rng ^= net_rng << 13; net_rng ^= net_rng >> 17; net_rng ^= net_rng << 5; return net_rng; }

typedef struct {
    adv_vs_t vs;
    adv_vs_bot_t player;     // the human stand-in
    bool playing;
    int fx_seen;
} side_t;
static side_t S[2];
static const uint8_t MAC[2][6] = {{0x98, 0xC3, 0x77, 0xF4, 0xA9, 0x58}, {0x98, 0xC3, 0x77, 0x11, 0x22, 0x33}};

static void apply_fx(int i, int fx, uint32_t now)
{
    S[i].fx_seen |= fx;
    if (fx & VS_FX_START) {
        adv_vs_bot_start(&S[i].player, S[i].vs.seed, now);
        S[i].player.rng ^= 0x1234567u * (unsigned)(i + 1) + S[i].vs.session;   // different hands, same course
        S[i].playing = false;
    }
    if (fx & VS_FX_GO) { S[i].playing = true; S[i].player.act_at = now; }
    if (fx & VS_FX_END) S[i].playing = false;
}

static void pump(int i, uint32_t now)
{
    adv_vs_out_t o;
    while (adv_vs_pop(&S[i].vs, &o)) {
        sent_count++;
        if (cut_from == i) continue;
        if ((int)(r32() % 100) < loss_pct) continue;
        if (nq >= MAXQ) continue;
        pkt_t *p = &q[nq++];
        p->at = now + 2 + r32() % 18;   // 2..19 ms, so packets may reorder
        p->to = 1 - i;
        memcpy(p->from, MAC[i], 6);
        memcpy(p->data, o.data, ADV_VS_PACKET);
    }
}

static void deliver(uint32_t now)
{
    for (int k = 0; k < nq;) {
        if ((int32_t)(now - q[k].at) >= 0) {
            pkt_t p = q[k];
            q[k] = q[--nq];
            apply_fx(p.to, adv_vs_packet(&S[p.to].vs, p.from, p.data, ADV_VS_PACKET, now), now);
        } else k++;
    }
}

static void step(uint32_t now)
{
    deliver(now);
    for (int i = 0; i < 2; i++) {
        adv_vs_side_t mine = {0};
        if (S[i].vs.page == VS_PLAY && S[i].playing) mine = adv_vs_bot_tick(&S[i].player, now);
        else if (S[i].vs.page == VS_PLAY || S[i].vs.page == VS_RESULT) mine = adv_vs_side_of(&S[i].player.game);
        apply_fx(i, adv_vs_tick(&S[i].vs, now, mine), now);
        pump(i, now);
    }
}

static uint32_t run_until(uint32_t now, uint32_t limit, int (*done)(void))
{
    for (uint32_t t = 0; t < limit; t += 10) {
        now += 10;
        step(now);
        if (done && done()) break;
    }
    return now;
}

static void key(int i, int b, uint32_t now) { apply_fx(i, adv_vs_key(&S[i].vs, b, ADV_VS_CLICK, now), now); pump(i, now); }

static int both_see(void) { return S[0].vs.npeers == 1 && S[1].vs.npeers == 1; }
static int b_invited(void) { return S[1].vs.page == VS_INVITED; }
static int both_counting(void) { return S[0].vs.page == VS_COUNTDOWN && S[1].vs.page == VS_COUNTDOWN; }
static int both_result(void) { return S[0].vs.page == VS_RESULT && S[1].vs.page == VS_RESULT && S[0].vs.theirs.over + S[1].vs.theirs.over >= 0; }
static int a_notice(void) { return S[0].vs.page == VS_NOTICE; }

static void reset_world(int loss)
{
    memset(S, 0, sizeof(S)); nq = 0; loss_pct = loss; cut_from = -1; sent_count = 0;
    adv_vs_init(&S[0].vs, MAC[0], true, 111, 1000, 6);
    adv_vs_init(&S[1].vs, MAC[1], true, 222, 1000, 0);
}

// Lobby -> invite -> accept -> countdown. Returns time.
static uint32_t pair(uint32_t now)
{
    now = run_until(now, 3000, both_see);
    S[0].vs.cursor = 1;
    key(0, ADV_VS_OK, now);
    now = run_until(now, 3000, b_invited);
    key(1, ADV_VS_OK, now);
    return run_until(now, 3000, both_counting);
}

static const char *oname(adv_vs_outcome_t o) { return o == VS_WIN ? "win" : o == VS_LOSE ? "lose" : o == VS_DRAW ? "draw" : "pending"; }

int main(void)
{
    // 1. discovery, pairing, same course, synchronized start
    reset_world(0);
    uint32_t now = pair(1000);
    int32_t go_skew = (int32_t)(S[0].vs.go_at - S[1].vs.go_at);
    printf("{\"case\":\"pair\",\"a\":%d,\"b\":%d,\"seed_eq\":%d,\"session_eq\":%d,\"go_skew\":%d,\"a_host\":%d,\"b_host\":%d,\"games\":[%d,%d]}\n",
           S[0].vs.page, S[1].vs.page, S[0].vs.seed == S[1].vs.seed, S[0].vs.session == S[1].vs.session, (int)go_skew,
           S[0].vs.host, S[1].vs.host, S[0].vs.game, S[1].vs.game);

    // 2. many full matches with 10% loss and reordering: outcomes must mirror, scores agree.
    int consistent = 0, matches = 0, stuck = 0, wins_a = 0, draws = 0, rematch_ok = 0;
    uint32_t max_score = 0;
    reset_world(10);
    now = pair(1000);
    for (int m = 0; m < 40; m++) {
        now = run_until(now, 600000, both_result);
        if (!both_result()) { stuck++; break; }
        // let final STATE packets settle
        now = run_until(now, 1500, NULL);
        matches++;
        adv_vs_outcome_t a = S[0].vs.outcome, b = S[1].vs.outcome;
        bool mirror = (a == VS_WIN && b == VS_LOSE) || (a == VS_LOSE && b == VS_WIN) || (a == VS_DRAW && b == VS_DRAW);
        bool scores = S[0].vs.theirs.score == S[1].vs.mine.score && S[1].vs.theirs.score == S[0].vs.mine.score;
        consistent += mirror && scores;
        wins_a += a == VS_WIN; draws += a == VS_DRAW;
        if (S[0].vs.mine.score > max_score) max_score = S[0].vs.mine.score;
        if (!(mirror && scores))
            fprintf(stderr, "mismatch m=%d a=%s b=%s a:%u/%u b:%u/%u\n", m, oname(a), oname(b), (unsigned)S[0].vs.mine.score,
                    (unsigned)S[0].vs.theirs.score, (unsigned)S[1].vs.mine.score, (unsigned)S[1].vs.theirs.score);
        uint32_t old_seed = S[0].vs.seed;
        key(1, ADV_VS_OK, now);           // guest asks first, then host
        now = run_until(now, 300, NULL);
        key(0, ADV_VS_OK, now);
        now = run_until(now, 3000, both_counting);
        rematch_ok += both_counting() && S[0].vs.seed == S[1].vs.seed && S[0].vs.seed != old_seed;
    }
    printf("{\"case\":\"matches\",\"matches\":%d,\"consistent\":%d,\"stuck\":%d,\"rematch_ok\":%d,\"wins_a\":%d,\"draws\":%d,\"max_score\":%u,\"tallies_a\":[%u,%u,%u],\"tallies_b\":[%u,%u,%u]}\n",
           matches, consistent, stuck, rematch_ok, wins_a, draws, (unsigned)max_score, S[0].vs.wins, S[0].vs.losses, S[0].vs.draws,
           S[1].vs.wins, S[1].vs.losses, S[1].vs.draws);

    // 3. link cut mid-game: the survivor gives up after ~4 s, never claims a win
    reset_world(0);
    now = pair(1000);
    now = run_until(now, 5000, NULL);
    cut_from = 1;
    uint32_t cut_at = now;
    now = run_until(now, 8000, a_notice);
    printf("{\"case\":\"cut\",\"a\":%d,\"note\":%d,\"after_ms\":%u,\"a_wins\":%u}\n", S[0].vs.page, S[0].vs.note,
           (unsigned)(now - cut_at), S[0].vs.wins);

    // 4. opponent leaves deliberately (double UP -> BYE)
    reset_world(0);
    now = pair(1000);
    now = run_until(now, 4000, NULL);
    adv_vs_leave(&S[1].vs); pump(1, now);
    now = run_until(now, 500, a_notice);
    printf("{\"case\":\"bye\",\"a\":%d,\"note\":%d}\n", S[0].vs.page, S[0].vs.note);

    // 5. decline
    reset_world(0);
    now = run_until(1000, 3000, both_see);
    S[0].vs.cursor = 1; key(0, ADV_VS_OK, now);
    now = run_until(now, 3000, b_invited);
    key(1, ADV_VS_DOWN, now);
    now = run_until(now, 500, a_notice);
    printf("{\"case\":\"decline\",\"a\":%d,\"note\":%d,\"b\":%d}\n", S[0].vs.page, S[0].vs.note, S[1].vs.page);

    // 6. unanswered invitation times out
    reset_world(0);
    now = run_until(1000, 3000, both_see);
    S[0].vs.cursor = 1; key(0, ADV_VS_OK, now);
    now = run_until(now, 20000, a_notice);
    printf("{\"case\":\"no_answer\",\"a\":%d,\"note\":%d,\"b\":%d}\n", S[0].vs.page, S[0].vs.note, S[1].vs.page);

    // 7. packet validation
    uint8_t p[ADV_VS_PACKET];
    adv_vs_side_t z = {7, 3, false};
    adv_vs_encode(p, VS_MSG_STATE, NULL, 1, 2, z, false, 0, 1, 1);
    int ok = adv_vs_valid(p, ADV_VS_PACKET);
    p[18] ^= 1;
    int bad_sum = adv_vs_valid(p, ADV_VS_PACKET);
    p[18] ^= 1;
    int short_len = adv_vs_valid(p, ADV_VS_PACKET - 1);
    char name[12]; adv_vs_name(MAC[0], name);
    printf("{\"case\":\"packet\",\"ok\":%d,\"bad_sum\":%d,\"short\":%d,\"name\":\"%s\"}\n", ok, bad_sum, short_len, name);

    // 7b. game list: DOWN x3 + OK picks station 4; long UP in the lobby returns to the list
    {
        adv_vs_t v;
        adv_vs_init(&v, MAC[0], true, 5, 0, 0);
        int start = v.page;
        for (int i = 0; i < 3; i++) adv_vs_key(&v, ADV_VS_DOWN, ADV_VS_CLICK, 10);
        adv_vs_key(&v, ADV_VS_OK, ADV_VS_CLICK, 20);
        int lobby = v.page, game = v.game;
        adv_vs_key(&v, ADV_VS_UP, ADV_VS_LONG, 30);
        int back = v.page;
        adv_vs_key(&v, ADV_VS_UP, ADV_VS_CLICK, 40);   // wraps 3 -> 2
        printf("{\"case\":\"pick\",\"start\":%d,\"lobby\":%d,\"game\":%d,\"back\":%d,\"pick\":%d}\n", start, lobby, game, back, v.pick);
        adv_vs_ghost_t gh;
        adv_vs_ghost_start(&gh, 77, 300, 2500, 1000);
        adv_vs_side_t mid = adv_vs_ghost_tick(&gh, 1000 + gh.duration / 2), end = adv_vs_ghost_tick(&gh, 1000 + gh.duration);
        printf("{\"case\":\"ghost\",\"target\":%u,\"duration\":%u,\"mid\":%u,\"mid_over\":%d,\"end\":%u,\"end_over\":%d}\n",
               (unsigned)gh.target, (unsigned)gh.duration, (unsigned)mid.score, mid.over, (unsigned)end.score, end.over);
    }

    // 8. NABO practice without radio: bot scores and every round ends
    adv_vs_t vs; adv_vs_bot_t bot, me;
    adv_vs_init(&vs, MAC[0], false, 9, 0, 1);
    unsigned rounds = 0, ended = 0, sent_without_radio = 0, total = 0, lo = 0xFFFFFFFF, hi = 0;
    now = 0;
    for (int r = 0; r < 60; r++) {
        int fx = adv_vs_key(&vs, ADV_VS_OK, ADV_VS_CLICK, now);   // lobby cursor 0 / result OK -> practice
        if (!(fx & VS_FX_START)) break;
        adv_vs_bot_start(&bot, vs.seed, now);
        adv_vs_bot_start(&me, vs.seed, now); me.rng ^= 0xABCDEF;
        rounds++;
        for (uint32_t t = 0; t < 900000; t += 10) {
            now += 10;
            adv_vs_side_t mine = {0};
            if (vs.page == VS_PLAY) { mine = adv_vs_bot_tick(&me, now); adv_vs_opponent(&vs, adv_vs_bot_tick(&bot, now), now); }
            fx = adv_vs_tick(&vs, now, mine);
            adv_vs_out_t o; while (adv_vs_pop(&vs, &o)) sent_without_radio++;
            if (fx & VS_FX_END) {
                ended++;
                adv_vs_side_t b = adv_vs_bot_tick(&bot, now);
                while (!b.over) { now += 10; b = adv_vs_bot_tick(&bot, now); }
                total += b.score; if (b.score < lo) lo = b.score; if (b.score > hi) hi = b.score;
                break;
            }
        }
        if (vs.page != VS_RESULT) break;
    }
    printf("{\"case\":\"practice\",\"rounds\":%u,\"ended\":%u,\"radio_packets\":%u,\"bot_avg\":%u,\"bot_min\":%u,\"bot_max\":%u}\n",
           rounds, ended, sent_without_radio, rounds ? total / rounds : 0, lo, hi);
    return 0;
}
