#include "adv_model.h"
#include <stdlib.h>
#include <string.h>
#include "adv_rng.h"

static void cue(adv_model_t *m, adv_cue_t c) { m->cue = c; m->fx |= ADV_FX_CUE; }

uint32_t adv_stamp_bit(int station, int tier) { return 1u << ((station - 1) * 3 + tier); }

uint32_t adv_earned(const adv_model_t *m)
{
    uint32_t e = 0;
    for (int s = 1; s < ADV_STATIONS; s++)
        for (int tier = 0; tier < 3; tier++)
            if (m->best[s] >= adv_threshold(s, tier)) e |= adv_stamp_bit(s, tier);
    return e;
}

bool adv_unlocked(const adv_model_t *m, int station)
{
    if (station <= ADV_START_STATION) return true;
    return m->best[station - 1] >= adv_threshold(station - 1, 0);
}

void adv_init(adv_model_t *m, uint32_t seed, const cg_settings_t *settings, const uint32_t best[ADV_STATIONS],
              uint32_t seen)
{
    memset(m, 0, sizeof(*m));
    m->page = ADV_PAGE_COVER;
    m->cursor = ADV_START_STATION;
    m->passport_from = ADV_PAGE_MAP;
    cg_init(&m->cfg, settings);
    m->cfg.page = CG_SETTINGS;
    memcpy(m->best, best, sizeof(m->best));
    m->seen = seen;
    m->stamp = -1;
    m->rng = seed;
}

static void end_session(adv_model_t *m)
{
    free(m->game);
    m->game = NULL;
    m->in_session = false;
}

void adv_free(adv_model_t *m) { end_session(m); }

// Shows the lowest new stamp, or lands on the map.
static void to_map(adv_model_t *m)
{
    end_session(m);
    uint32_t pending = adv_earned(m) & ~m->seen;
    if (pending) {
        m->stamp = __builtin_ctz(pending);
        m->page = ADV_PAGE_STAMP;
        cue(m, ADV_CUE_STAMP);
    } else {
        m->stamp = -1;
        m->page = ADV_PAGE_MAP;
    }
}

static const adv_game_t *session_game(const adv_model_t *m) { return adv_station[m->station].game; }

adv_status_t adv_game_status(const adv_model_t *m)
{
    if (!m->in_session || !m->game) return (adv_status_t){0};
    return session_game(m)->status(m->game);
}

static void start_run(adv_model_t *m)
{
    m->seed = adv_rand(&m->rng);
    session_game(m)->start(m->game, m->seed);
    m->phase = ADV_READY;
    m->t = ADV_READY_STEPS;
    m->record = false;
    memset(&m->input, 0, sizeof(m->input));
    cue(m, ADV_CUE_ENTER);
}

static void move_cursor(adv_model_t *m, int dir)
{
    // NABO may step onto the first locked station to look at it, but never past it.
    int j = adv_path_index(m->cursor) + dir;
    if (j < 0 || j >= ADV_STATIONS || (!adv_unlocked(m, m->cursor) && !adv_unlocked(m, adv_path[j]))) {
        cue(m, ADV_CUE_DENY);
        return;
    }
    m->cursor = adv_path[j];
    cue(m, ADV_CUE_MOVE);
}

static void enter_station(adv_model_t *m)
{
    int s = m->cursor;
    if (s == ADV_KIOSK) { m->page = ADV_PAGE_KIOSK; m->kiosk = 0; cue(m, ADV_CUE_ENTER); return; }
    if (!adv_unlocked(m, s)) { cue(m, ADV_CUE_DENY); return; }
    if (adv_station[s].kind == ADV_KIND_LEGACY) {
        m->page = ADV_PAGE_LEGACY;
        m->fx |= ADV_FX_OPEN_LEGACY;
        cue(m, ADV_CUE_ENTER);
        return;
    }
    void *game = calloc(1, adv_station[s].game->state_size);
    if (!game) { m->fx |= ADV_FX_NOMEM; cue(m, ADV_CUE_DENY); return; }
    m->game = game;
    m->in_session = true;
    m->station = s;
    m->phase = ADV_TITLE;
    m->t = 0;
    m->seed = 0;
    m->record = false;
    m->page = ADV_PAGE_SESSION;
    cue(m, ADV_CUE_ENTER);
}

static void open_passport(adv_model_t *m, adv_page_t from)
{
    m->page = ADV_PAGE_PASSPORT;
    m->passport = 0;
    m->passport_from = from;
    cue(m, ADV_CUE_ENTER);
}

static bool is_back(adv_btn_t b, adv_ev_t e) { return b == ADV_BTN_UP && (e == ADV_EV_LONG || e == ADV_EV_DOUBLE); }

static void session_event(adv_model_t *m, adv_btn_t b, adv_ev_t e)
{
    bool click = e == ADV_EV_CLICK;
    switch (m->phase) {
    case ADV_TITLE:
    case ADV_RESULT:
        if (b == ADV_BTN_OK && click) start_run(m);
        else if (is_back(b, e)) { cue(m, ADV_CUE_BACK); to_map(m); }
        break;
    case ADV_PLAY:
        if (b == ADV_BTN_UP && e == ADV_EV_LONG) { m->phase = ADV_PAUSE; cue(m, ADV_CUE_BACK); break; }
        if (e == ADV_EV_PRESS) {
            if (b == ADV_BTN_OK) m->input.ok_down = 1;
            if (b == ADV_BTN_UP) m->input.up_down = 1;
            if (b == ADV_BTN_DOWN) m->input.down_down = 1;
        } else if (e == ADV_EV_RELEASE) {
            if (b == ADV_BTN_OK) m->input.ok_up = 1;
            if (b == ADV_BTN_DOWN) m->input.down_up = 1;
        }
        break;
    case ADV_PAUSE:
        if (b == ADV_BTN_OK && click) {
            m->phase = ADV_PLAY;
            memset(&m->input, 0, sizeof(m->input));
            cue(m, ADV_CUE_GO);
        } else if (b == ADV_BTN_DOWN && click) start_run(m);
        else if (is_back(b, e)) { cue(m, ADV_CUE_BACK); to_map(m); }
        break;
    default: break;   // READY and END ignore buttons
    }
}

static void settings_event(adv_model_t *m, adv_btn_t b, adv_ev_t e)
{
    int key = -1;
    if (e == ADV_EV_CLICK) key = b == ADV_BTN_UP ? CG_UP : b == ADV_BTN_DOWN ? CG_DOWN : CG_OK;
    else if (is_back(b, e)) key = CG_BACK;
    if (key < 0) return;
    int r = cg_key(&m->cfg, (cg_key_t)key);
    if (r & CG_CHANGED) m->fx |= ADV_FX_APPLY_SETTINGS;
    if (r & CG_SAVE) m->fx |= ADV_FX_SAVE_SETTINGS;
    if (m->cfg.page == CG_HOME) { m->page = ADV_PAGE_KIOSK; cue(m, ADV_CUE_BACK); }
    else cue(m, ADV_CUE_MOVE);
}

int adv_event(adv_model_t *m, adv_btn_t b, adv_ev_t e)
{
    m->fx = ADV_FX_REDRAW;
    m->cue = ADV_CUE_NONE;
    if (e == ADV_EV_PRESS) m->held |= 1u << b;
    if (e == ADV_EV_RELEASE) m->held &= ~(1u << b);
    bool click = e == ADV_EV_CLICK;
    switch (m->page) {
    case ADV_PAGE_COVER:
        if (b == ADV_BTN_OK && click) { cue(m, ADV_CUE_ENTER); to_map(m); }
        break;
    case ADV_PAGE_MAP:
        if (click && b == ADV_BTN_UP) move_cursor(m, 1);
        else if (click && b == ADV_BTN_DOWN) move_cursor(m, -1);
        else if (click && b == ADV_BTN_OK) enter_station(m);
        else if (b == ADV_BTN_OK && e == ADV_EV_LONG) open_passport(m, ADV_PAGE_MAP);
        else if (is_back(b, e)) { m->page = ADV_PAGE_COVER; cue(m, ADV_CUE_BACK); }
        break;
    case ADV_PAGE_KIOSK:
        if (click && (b == ADV_BTN_UP || b == ADV_BTN_DOWN)) {
            m->kiosk = (m->kiosk + (b == ADV_BTN_UP ? 2 : 1)) % 3;
            cue(m, ADV_CUE_MOVE);
        } else if (click && b == ADV_BTN_OK) {
            if (m->kiosk == 0) open_passport(m, ADV_PAGE_KIOSK);
            else if (m->kiosk == 1) {
                m->page = ADV_PAGE_SETTINGS;
                m->cfg.page = CG_SETTINGS;
                m->cfg.settings_cursor = 0;
                m->cfg.editing = -1;
                cue(m, ADV_CUE_ENTER);
            } else { cue(m, ADV_CUE_BACK); to_map(m); }
        } else if (is_back(b, e)) { cue(m, ADV_CUE_BACK); to_map(m); }
        break;
    case ADV_PAGE_PASSPORT:
        if (click && (b == ADV_BTN_UP || b == ADV_BTN_DOWN)) {
            m->passport = (m->passport + (b == ADV_BTN_UP ? 7 : 1)) % 8;
            cue(m, ADV_CUE_MOVE);
        } else if ((click && b == ADV_BTN_OK) || is_back(b, e)) {
            cue(m, ADV_CUE_BACK);
            if (m->passport_from == ADV_PAGE_KIOSK) m->page = ADV_PAGE_KIOSK;
            else to_map(m);
        }
        break;
    case ADV_PAGE_SETTINGS: settings_event(m, b, e); break;
    case ADV_PAGE_STAMP:
        if (b == ADV_BTN_OK && click) {
            m->seen |= 1u << m->stamp;
            m->fx |= ADV_FX_SAVE_PROGRESS;
            to_map(m);
            if (m->page == ADV_PAGE_MAP) cue(m, ADV_CUE_ENTER);
        }
        break;
    case ADV_PAGE_SESSION: session_event(m, b, e); break;
    default: break;   // LEGACY: the platform routes buttons to the legacy game
    }
    return m->fx;
}

int adv_legacy_done(adv_model_t *m, uint32_t best)
{
    m->fx = 0;
    m->cue = ADV_CUE_NONE;
    if (m->page != ADV_PAGE_LEGACY) return 0;
    if (best > m->best[m->cursor]) m->best[m->cursor] = best;
    to_map(m);
    m->fx |= ADV_FX_REDRAW;
    return m->fx;
}

int adv_step(adv_model_t *m)
{
    m->fx = 0;
    m->cue = ADV_CUE_NONE;
    if (m->page != ADV_PAGE_SESSION || !m->in_session) return 0;
    const adv_game_t *game = session_game(m);
    if (m->phase == ADV_READY) {
        if (--m->t == 0) { m->phase = ADV_PLAY; cue(m, ADV_CUE_GO); }
        m->fx |= ADV_FX_REDRAW;
    } else if (m->phase == ADV_PLAY) {
        adv_input_t in = m->input;
        in.ok_held = (m->held >> ADV_BTN_OK) & 1;
        in.down_held = (m->held >> ADV_BTN_DOWN) & 1;
        memset(&m->input, 0, sizeof(m->input));
        game->step(m->game, &in);
        adv_status_t st = game->status(m->game);
        if (st.cue) cue(m, (adv_cue_t)st.cue);
        if (st.over) { m->phase = ADV_END; m->t = ADV_END_STEPS; }
        m->fx |= ADV_FX_REDRAW;
    } else if (m->phase == ADV_END) {
        adv_input_t none = {0};
        game->step(m->game, &none);
        if (--m->t == 0) {
            m->phase = ADV_RESULT;
            uint32_t score = game->status(m->game).score;
            if (score > m->best[m->station]) {
                m->record = true;
                if (!m->test) { m->best[m->station] = score; m->fx |= ADV_FX_SAVE_BEST; }
            }
        }
        m->fx |= ADV_FX_REDRAW;
    }
    return m->fx;
}
