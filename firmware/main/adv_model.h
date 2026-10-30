#pragma once
// NABO 的冒险之旅 shell: cover, map, passport kiosk, passport, settings, stamp ceremony and the
// unified session (title, countdown, play, pause, end, result) for shell games. No display,
// audio or RTOS dependencies; the reference is game-art/adventure/prototype/adv_core.js.
#include <stdbool.h>
#include <stdint.h>
#include "adv_game.h"
#include "adv_stations.h"
#include "collection_model.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ADV_READY_STEPS 180   // 3 s countdown at 60 Hz
#define ADV_END_STEPS 120     // 2 s for the game's ending before the result

typedef enum { ADV_BTN_UP, ADV_BTN_DOWN, ADV_BTN_OK } adv_btn_t;
// Same values as bsp_btn_ev_t.
typedef enum { ADV_EV_PRESS, ADV_EV_CLICK, ADV_EV_DOUBLE, ADV_EV_LONG, ADV_EV_RELEASE } adv_ev_t;
typedef enum {
    ADV_PAGE_COVER, ADV_PAGE_MAP, ADV_PAGE_KIOSK, ADV_PAGE_PASSPORT, ADV_PAGE_SETTINGS,
    ADV_PAGE_STAMP, ADV_PAGE_LEGACY, ADV_PAGE_SESSION,
} adv_page_t;
typedef enum { ADV_TITLE, ADV_READY, ADV_PLAY, ADV_PAUSE, ADV_END, ADV_RESULT } adv_phase_t;
typedef enum {
    ADV_CUE_NONE, ADV_CUE_MOVE, ADV_CUE_ENTER, ADV_CUE_DENY, ADV_CUE_STAMP, ADV_CUE_BACK,
    ADV_CUE_HIT, ADV_CUE_MISS, ADV_CUE_OVER, ADV_CUE_GO, ADV_CUE_WHISTLE,
} adv_cue_t;
// Effects returned by adv_event / adv_step / adv_legacy_done for the platform to act on.
enum {
    ADV_FX_REDRAW = 1,
    ADV_FX_OPEN_LEGACY = 2,      // open adv_station[cursor] (jump or dive)
    ADV_FX_SAVE_PROGRESS = 4,    // persist seen stamps
    ADV_FX_SAVE_BEST = 8,        // persist best[session station]
    ADV_FX_SAVE_SETTINGS = 16,
    ADV_FX_APPLY_SETTINGS = 32,
    ADV_FX_CUE = 64,             // play cue
    ADV_FX_NOMEM = 128,          // a session could not allocate its game
};

typedef struct {
    adv_page_t page;
    int cursor;                  // station NABO stands on
    int kiosk, passport;         // menu cursors
    adv_page_t passport_from;
    cg_model_t cfg;              // settings and status pages (collection_model.c)
    uint32_t best[ADV_STATIONS];
    uint32_t seen;               // stamps already shown, bit (station - 1) * 3 + tier
    int stamp;                   // stamp bit on show, -1 for none
    uint32_t rng;
    unsigned held;               // buttons held, bit per adv_btn_t
    adv_input_t input;           // edges waiting for the next play step
    bool in_session;
    int station, phase, t;
    uint32_t seed;
    uint32_t best_before;        // score at run start, used by the result medal animation
    bool record;
    void *game;                  // calloc'd state of adv_station[station].game
    bool test;                   // scripted tests: never raise ADV_FX_SAVE_BEST
    int fx;
    adv_cue_t cue;
} adv_model_t;

void adv_init(adv_model_t *m, uint32_t seed, const cg_settings_t *settings, const uint32_t best[ADV_STATIONS],
              uint32_t seen);
void adv_free(adv_model_t *m);
int adv_event(adv_model_t *m, adv_btn_t button, adv_ev_t event);
bool adv_game_map_key(adv_btn_t button,adv_ev_t event); // all games: double UP only
int adv_step(adv_model_t *m);
// Test-only entry bypasses unlock, never changes any score or earned/seen stamp.
int adv_test_open(adv_model_t *m,int station);
int adv_practice_open(adv_model_t *m);
// The legacy game on the cursor closed; best is its best score in game units.
int adv_legacy_done(adv_model_t *m, uint32_t best);

uint32_t adv_stamp_bit(int station, int tier);
uint32_t adv_earned(const adv_model_t *m);
bool adv_unlocked(const adv_model_t *m, int station);
adv_status_t adv_game_status(const adv_model_t *m);

#ifdef __cplusplus
}
#endif
