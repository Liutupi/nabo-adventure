// NABO 的冒险之旅: offline launcher. The shell model (adv_model.c) owns pages and sessions; this
// file feeds it buttons and 60 Hz steps, persists progress, plays cues and hosts the two legacy
// games (跳一跳, 深潜). Game PCM, page lifetimes and codec I/O share one owner lock.
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include "adv_boot.h"
#include "adv_model.h"
#include "adv_post_v2.h"
#include "adv_night_debug.h"
#include "adv_space_debug.h"
#include "adv_climb_debug.h"
#include "adv_ui_boot_video.h"
#include "adv_persist.h"
#include "adv_sound.h"
#include "adv_ui.h"
#include "adv_gfx.h"
#include "adv_ui_animation.h"
#include "adv_boot_motion.h"
#include "bsp_audio.h"
#include "bsp_battery.h"
#include "bsp_button.h"
#include "bsp_display.h"
#include "bsp_i2c.h"
#include "bsp_pins.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_random.h"
#include "esp_heap_caps.h"
#include "adv_link.h"
#include "adv_vs.h"
#include "esp_sleep.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "nabo_dive.h"
#include "nabo_dive_model.h"
#include "nabo_jump_model.h"
#include "nabo_jump_sound.h"
#include "nvs_flash.h"

#define TAG "NABO-Adventure"
#define CHUNK 320
#define STEP_US 16667
#define STATION_JUMP 1
#define STATION_DIVE 2

typedef struct { bool command; int button, event; uint32_t ms; char line[96]; } input_t;
typedef enum { OWNER_SHELL, OWNER_JUMP, OWNER_DIVE, OWNER_VERSUS } owner_t;

static QueueHandle_t s_inputs;
static SemaphoreHandle_t s_audio_lock;
static adv_model_t s_model;
static adv_boot_t s_boot;
static bool s_boot_closed;
extern const uint8_t boot_wav_start[] asm("_binary_adv_boot_voice_wav_start");
extern const uint8_t boot_wav_end[] asm("_binary_adv_boot_voice_wav_end");
static owner_t s_owner = OWNER_SHELL;        // who draws and who feeds PCM
static nabo_jump_t s_jump;
// Versus room: the shared jump game above is "my" race; the bot is NABO (practice) or, with
// >vs.auto=1, also drives my own race for unattended two-badge tests.
static adv_vs_t s_vs;
static adv_vs_bot_t s_vs_bot, s_vs_self;
static int s_vs_open_game;   // 0: start on the game list
static bool s_vs_auto, s_vs_dirty;
static int s_vs_send_fail;
static adv_vs_page_t s_vs_drawn = (adv_vs_page_t)-1;
static int s_vs_count = -1;
// Landscape session races (station 3..8) run the real game inside s_model (adv_versus_race).
static adv_vs_ghost_t s_vs_ghost;
static atomic_bool s_vs_shell_audio;
static int64_t s_vs_step_us;
static uint32_t s_vs_draw_ms;
static void handle_fx(int fx);
static void legacy_back(void);
static void dive_button(const input_t *in);
static bool versus_session(void) { return s_vs.game >= 3 && s_vs.game <= 8; }
// DIVE races run the dive task, which owns the panel: the room's renderer is closed meanwhile.
static bool s_vs_diving;
static atomic_bool s_vs_dive_audio;
static bool s_audio_ok, s_test;
static atomic_bool s_overflow;
static atomic_int s_jump_cue, s_cue;
static atomic_bool s_post_horn;
static unsigned s_held, s_swallowed;
static int64_t s_last_input_us, s_step_us;
static uint32_t s_draw_frames,s_draw_us,s_draw_max_us;

static void report_error(const char *what, esp_err_t err)
{
    if (err != ESP_OK) ESP_LOGE(TAG, "%s: %s", what, esp_err_to_name(err));
}

static void best_key(char *out, size_t size, int station) { snprintf(out, size, "%s", adv_persist_best_key(station)); }

static void stop_boot(void)
{
    if (s_boot_closed) return;
    xSemaphoreTake(s_audio_lock, portMAX_DELAY);
    adv_boot_stop(&s_boot);
    xSemaphoreGive(s_audio_lock);
    s_boot_closed = true;
    adv_ui_boot_end();
}

static void apply_settings(void)
{
    const cg_settings_t *s = &s_model.cfg.settings;
    xSemaphoreTake(s_audio_lock, portMAX_DELAY);
    if (s_audio_ok) bsp_audio_set_volume(s->speaker ? s->volume : 0);
    xSemaphoreGive(s_audio_lock);
    bsp_display_backlight(s->brightness);
}

// ---------- versus room ----------

_Static_assert((int)ADV_LINK_PACKET_BYTES == (int)ADV_VS_PACKET, "versus packets ride the link as-is");
_Static_assert((int)BSP_BTN_UP == (int)ADV_VS_UP && (int)BSP_BTN_DOWN == (int)ADV_VS_DOWN && (int)BSP_BTN_OK == (int)ADV_VS_OK, "button ids");
_Static_assert((int)BSP_BTN_CLICK == (int)ADV_VS_CLICK && (int)BSP_BTN_PRESS == (int)ADV_VS_PRESS && (int)BSP_BTN_RELEASE == (int)ADV_VS_RELEASE, "event ids");

static uint32_t now_ms(void) { return (uint32_t)(esp_timer_get_time() / 1000); }

static void versus_open(int game)
{
    uint8_t mac[6];
    bool radio = adv_link_begin();
    adv_link_mac(mac);
    adv_vs_init(&s_vs, mac, radio, esp_random(), now_ms(), game);
    atomic_store(&s_vs_shell_audio, false);
    s_vs_auto = false;
    s_vs_send_fail = 0;
    s_vs_drawn = (adv_vs_page_t)-1;
    s_vs_dirty = true;
    memset(&s_jump, 0, sizeof(s_jump));
    adv_jump_versus(NULL, NULL, NULL, NULL, NULL);
    ESP_LOGI(TAG, "versus open radio=%d err=%s heap=%u largest=%u", radio, adv_link_error(),
             (unsigned)esp_get_free_heap_size(), (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_8BIT));
}

// Flush the outbox for a short moment (the BYE matters), then release the radio.
static void versus_flush(int budget_ms)
{
    for (int t = 0; t < budget_ms && s_vs.nout; t += 5) {
        if (adv_link_send(s_vs.out[0].to, s_vs.out[0].data, ADV_VS_PACKET)) { adv_vs_out_t o; adv_vs_pop(&s_vs, &o); }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}

static void race_stop(void)
{
    if (s_vs_diving) {
        nabo_dive_close();
        s_vs_diving = false;
        atomic_store(&s_vs_dive_audio, false);
        if (!adv_ui_open()) ESP_LOGE(TAG, "versus: room renderer did not reopen");
        adv_ui_invalidate();
        s_vs_drawn = (adv_vs_page_t)-1;
        return;
    }
    if (!s_model.versus) return;
    adv_versus_stop(&s_model);
    adv_ui_versus_overlay(NULL, NULL);
    atomic_store(&s_vs_shell_audio, false);
    adv_ui_invalidate();
}

static void versus_close(void)
{
    race_stop();
    adv_vs_leave(&s_vs);
    versus_flush(60);
    adv_link_end();
    adv_jump_versus(NULL, NULL, NULL, NULL, NULL);
    memset(&s_jump, 0, sizeof(s_jump));
    ESP_LOGI(TAG, "versus closed heap=%u largest=%u", (unsigned)esp_get_free_heap_size(),
             (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_8BIT));
}

static nabo_jump_t *versus_game(void) { return s_vs_auto ? &s_vs_self.game : &s_jump; }

static void versus_fx(int fx, uint32_t ms)
{
    if (fx & VS_FX_START) {
        int character = s_jump.character;
        nabo_jump_reset(&s_jump, s_vs.seed, 0);
        s_jump.character = character;
        adv_vs_bot_start(&s_vs_bot, s_vs.seed, ms);
        adv_vs_bot_start(&s_vs_self, s_vs.seed, ms);
        s_vs_self.rng ^= esp_random();
        s_vs_self.game.character = character;
        if (s_vs.game >= 3) adv_vs_ghost_start(&s_vs_ghost, s_vs.seed, adv_threshold(s_vs.game, 0), adv_threshold(s_vs.game, 2), ms);
    }
    if ((fx & VS_FX_GO) && versus_session()) {
        handle_fx(adv_versus_race(&s_model, s_vs.game, s_vs.seed));
        if (s_vs.bot) adv_vs_ghost_start(&s_vs_ghost, s_vs.seed, adv_threshold(s_vs.game, 0), adv_threshold(s_vs.game, 2), ms);
        atomic_store(&s_vs_shell_audio, true);
        s_vs_step_us = esp_timer_get_time();
        s_vs_draw_ms = 0;
        adv_ui_invalidate();
    } else if ((fx & VS_FX_GO) && s_vs.game == 2) {
        if (s_vs.bot) adv_vs_ghost_start(&s_vs_ghost, s_vs.seed, adv_threshold(2, 0), adv_threshold(2, 2), ms);
        adv_ui_close();
        nabo_dive_versus(true, s_vs.seed);
        s_vs_diving = nabo_dive_open(bsp_display_io(), bsp_display_panel(), s_vs.seed);
        if (s_vs_diving) {
            atomic_store(&s_vs_dive_audio, true);
            nabo_dive_autopilot(s_vs_auto);
        } else {
            ESP_LOGE(TAG, "versus: dive did not open heap=%u", (unsigned)esp_get_free_heap_size());
            nabo_dive_versus(false, 0);
            (void)adv_ui_open();
        }
    } else if (fx & VS_FX_GO) { atomic_store(&s_jump_cue, 0); adv_jump_invalidate(); }
    if (fx & VS_FX_END) atomic_store(&s_jump_cue, s_vs.outcome == VS_WIN ? 2 : 4);
    if (fx) s_vs_dirty = true;
}

static void versus_button(const input_t *in)
{
    if (s_vs.page == VS_PLAY && s_vs.game == 2) {
        if (s_vs_diving && !s_vs_auto && !(in->button == BSP_BTN_UP)) dive_button(in);   // no pause in a race
        return;
    }
    if (s_vs.page == VS_PLAY && versus_session()) {
        // UP is a play key in the landscape games; long DOWN (their pause key) leaves the race.
        if (in->button == BSP_BTN_DOWN && in->event == BSP_BTN_LONG) { legacy_back(); return; }
        if (!s_vs_auto) handle_fx(adv_event(&s_model, (adv_btn_t)in->button, (adv_ev_t)in->event));
        return;
    }
    if (s_vs.page == VS_PLAY && !s_vs_auto) {
        if (in->button == BSP_BTN_OK && s_jump.phase < JUMP_FALLING) {
            if (in->event == BSP_BTN_PRESS) {
                nabo_jump_press(&s_jump, in->ms);
                if (nabo_jump_charging(&s_jump)) atomic_store(&s_jump_cue, 5);
            } else if (in->event == BSP_BTN_RELEASE) {
                nabo_jump_release(&s_jump, in->ms);
                atomic_store(&s_jump_cue, s_jump.phase == JUMP_FLYING ? 1 : 0);
            }
        } else if (in->event == BSP_BTN_CLICK && in->button == BSP_BTN_DOWN) s_jump.character = 1 - s_jump.character;
        return;
    }
    versus_fx(adv_vs_key(&s_vs, in->button, in->event, in->ms), in->ms);
}

static void versus_tick(uint32_t ms)
{
    nabo_jump_t *game = versus_game();
    adv_vs_side_t mine = {0};
    if (s_vs_auto) s_last_input_us = esp_timer_get_time();   // unattended test: no auto-sleep mid-race
    bool race = s_vs.page == VS_PLAY && versus_session() && s_model.versus;
    if (race) {
        int64_t us = esp_timer_get_time();
        for (int steps = 0; us - s_vs_step_us >= STEP_US && steps < 4; steps++) {
            handle_fx(adv_step(&s_model) & ~ADV_FX_REDRAW);
            s_vs_step_us += STEP_US;
        }
        if (us - s_vs_step_us >= STEP_US) s_vs_step_us = us;
        adv_status_t st = adv_game_status(&s_model);
        mine.score = st.score;
        mine.over = s_model.phase != ADV_PLAY;
        if (s_vs.bot) adv_vs_opponent(&s_vs, adv_vs_ghost_tick(&s_vs_ghost, ms), ms);
    } else if (s_vs.page == VS_PLAY && s_vs.game == 2) {
        int depth = 0;
        bool over = !s_vs_diving;   // a dive that could not open counts as finished at 0 m
        if (s_vs_diving) nabo_dive_versus_state(&depth, &over);
        mine.score = (uint32_t)depth;
        mine.over = over;
        if (s_vs.bot) adv_vs_opponent(&s_vs, adv_vs_ghost_tick(&s_vs_ghost, ms), ms);
    } else if (s_vs.page == VS_PLAY && !versus_session()) {
        if (s_vs_auto) (void)adv_vs_bot_tick(&s_vs_self, ms);
        else {
            jump_phase_t before = s_jump.phase;
            nabo_jump_tick(&s_jump, ms);
            if (s_jump.sound) {
                s_jump.sound = false;
                atomic_store(&s_jump_cue, s_jump.pending_charge && !s_jump.pending_released ? 5 : s_jump.centered ? 2 : 3);
            }
            if (before == JUMP_SCROLLING && s_jump.phase == JUMP_FLYING) atomic_store(&s_jump_cue, 1);
            if (s_jump.phase == JUMP_FALLING && before != JUMP_FALLING) atomic_store(&s_jump_cue, 4);
        }
        mine = adv_vs_side_of(game);
        if (s_vs.bot) adv_vs_opponent(&s_vs, adv_vs_bot_tick(&s_vs_bot, ms), ms);
    } else if (s_vs.page == VS_RESULT && !versus_session()) mine = adv_vs_side_of(game);
    adv_link_rx_t rx;
    int fx = 0;
    while (adv_link_poll(&rx)) fx |= adv_vs_packet(&s_vs, rx.mac, rx.data, ADV_LINK_PACKET_BYTES, ms);
    fx |= adv_vs_tick(&s_vs, ms, mine);
    versus_fx(fx, ms);
    // Event trace for real-match diagnosis: one line whenever the page, an "over" flag or the outcome moves.
    static int last_page = -1, last_outcome = -1, last_over = -1;
    if (s_vs.page != VS_PLAY && (s_model.versus || s_vs_diving)) race_stop();   // result, notice or a lost link
    int over_bits = s_vs.mine.over | s_vs.theirs.over << 1;
    if (s_vs.page != last_page || s_vs.outcome != last_outcome || over_bits != last_over) {
        printf("@vsev {\"ms\":%lu,\"game\":%d,\"page\":%d,\"note\":%d,\"session\":%u,\"mine\":[%u,%d],\"theirs\":[%u,%d],\"outcome\":%d}\n",
               (unsigned long)ms, s_vs.game, s_vs.page, s_vs.note, (unsigned)s_vs.session, (unsigned)s_vs.mine.score,
               s_vs.mine.over, (unsigned)s_vs.theirs.score, s_vs.theirs.over, s_vs.outcome);
        last_page = s_vs.page; last_outcome = s_vs.outcome; last_over = over_bits;
    }
    if (s_vs.nout) {
        if (adv_link_send(s_vs.out[0].to, s_vs.out[0].data, ADV_VS_PACKET)) { adv_vs_out_t o; adv_vs_pop(&s_vs, &o); s_vs_send_fail = 0; }
        else if (++s_vs_send_fail > 40) { adv_vs_out_t o; adv_vs_pop(&s_vs, &o); s_vs_send_fail = 0; }   // never wedge the outbox
    }
    int64_t draw_start = esp_timer_get_time();
    if (s_vs.page == VS_PLAY && s_vs_diving) {   // the dive task draws; hand it the two lines
        char pill[40], banner[64] = "";
        const char *who = s_vs.bot ? "NABO" : "对手";
        // The dive's text layouts hold at most 16 glyphs (DIVE_TEXT_MAX_GLYPHS): keep these short.
        snprintf(pill, sizeof(pill), "%s %lu m%s", who, (unsigned long)s_vs.theirs.score, s_vs.theirs.over ? " 已结束" : "");
        if (s_vs.mine.over && !s_vs.theirs.over)
            snprintf(banner, sizeof(banner), "%s要超过 %lu m 才赢", who, (unsigned long)s_vs.mine.score);
        else if (!s_vs.mine.over && s_vs.theirs.over)
            snprintf(banner, sizeof(banner), "超过 %lu m 你就赢", (unsigned long)s_vs.theirs.score);
        nabo_dive_versus_text(pill, banner);
        s_vs_drawn = VS_PLAY;
        return;
    }
    if (race) {
        if (ms - s_vs_draw_ms < 33) return;   // the landscape renderers are heavy: 30 fps like the shell
        s_vs_draw_ms = ms;
        char pill[40], banner[64] = "";
        const char *who = s_vs.bot ? "NABO" : "对手";
        snprintf(pill, sizeof(pill), "%s %lu%s", who, (unsigned long)s_vs.theirs.score, s_vs.theirs.over ? " · 已结束" : "");
        if (s_vs.mine.over && !s_vs.theirs.over)
            snprintf(banner, sizeof(banner), "%s要超过 %lu 分才算赢", who, (unsigned long)s_vs.mine.score);
        else if (!s_vs.mine.over && s_vs.theirs.over)
            snprintf(banner, sizeof(banner), "%s结束了！超过 %lu 分你就赢", who, (unsigned long)s_vs.theirs.score);
        adv_ui_versus_overlay(pill, banner);
        adv_ui_draw(&s_model, ms, 100, 4000);
        s_vs_drawn = VS_PLAY;
    } else if (s_vs.page == VS_PLAY) {
        // Spell the asymmetric moment out on both screens: whoever falls first waits, the other
        // keeps jumping and must pass the fallen score to win (falling short or level ends it too).
        char opp[32], state[32], title[32], line[48], footer[48] = "";
        const char *who = s_vs.bot ? "NABO" : "对手";
        unsigned long mine_score = (unsigned long)game->score, theirs = (unsigned long)s_vs.theirs.score;
        bool fallen = game->phase >= JUMP_FALLING;
        snprintf(opp, sizeof(opp), "%s %lu 分", who, theirs);
        snprintf(state, sizeof(state), "%s", s_vs.theirs.over ? "已经掉下去了" : "还在跳");
        snprintf(title, sizeof(title), "你掉下去了");
        snprintf(line, sizeof(line), "%s %lu 分，还在跳", who, theirs);
        if (fallen && !s_vs.theirs.over) snprintf(footer, sizeof(footer), "%s要超过 %lu 分才算赢", who, mine_score);
        else if (!fallen && s_vs.theirs.over) snprintf(footer, sizeof(footer), "%s掉了！超过 %lu 分你就赢", who, theirs);
        adv_jump_versus(opp, state, title, line, footer[0] ? footer : NULL);
        if (s_vs_drawn != VS_PLAY) adv_jump_invalidate();
        adv_jump_draw(game, ms, false);
        s_vs_drawn = VS_PLAY;
    } else {
        if (s_vs_drawn == VS_PLAY) adv_ui_invalidate();   // the race wrote the panel directly
        int count = adv_vs_countdown(&s_vs, ms);
        if (s_vs_dirty || s_vs.page != s_vs_drawn || count != s_vs_count) {
            adv_ui_draw_versus(&s_vs, ms);
            s_vs_drawn = s_vs.page;
            s_vs_count = count;
            s_vs_dirty = false;
        } else return;
    }
    s_draw_us = (uint32_t)(esp_timer_get_time() - draw_start);
    s_draw_frames++;
    if (s_draw_us > s_draw_max_us) s_draw_max_us = s_draw_us;
}

static void versus_status(void)
{
    if (s_owner != OWNER_VERSUS) { puts("@error versus not open"); return; }
    uint32_t rx, drop, fail;
    adv_link_stats(&rx, &drop, &fail);
    char me[12], opp[12];
    adv_vs_name(s_vs.me, me); adv_vs_name(s_vs.opp, opp);
    flockfile(stdout);
    printf("@vs {\"game\":%d,\"page\":%d,\"note\":%d,\"radio\":%d,\"me\":\"%s\",\"opp\":\"%s\",\"peers\":[", s_vs.game,
           s_vs.page, s_vs.note, s_vs.radio, me, opp);
    for (int i = 0; i < s_vs.npeers; i++) { char n[12]; adv_vs_name(s_vs.peers[i].mac, n); printf("%s\"%s\"", i ? "," : "", n); }
    printf("],\"cursor\":%d,\"host\":%d,\"bot\":%d,\"auto\":%d,\"seed\":%u,\"session\":%u,\"mine\":[%u,%u,%d],"
           "\"theirs\":[%u,%u,%d],\"outcome\":%d,\"again\":[%d,%d],\"gone\":%d,\"tally\":[%u,%u,%u],"
           "\"rx\":%u,\"drop\":%u,\"fail\":%u,\"heap\":%u,\"largest\":%u}\n",
           s_vs.cursor, s_vs.host, s_vs.bot, s_vs_auto, (unsigned)s_vs.seed, (unsigned)s_vs.session,
           (unsigned)s_vs.mine.score, s_vs.mine.steps, s_vs.mine.over, (unsigned)s_vs.theirs.score, s_vs.theirs.steps,
           s_vs.theirs.over, s_vs.outcome, s_vs.want_again, s_vs.they_again, s_vs.opp_gone, s_vs.wins, s_vs.losses,
           s_vs.draws, (unsigned)rx, (unsigned)drop, (unsigned)fail, (unsigned)esp_get_free_heap_size(),
           (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_8BIT));
    funlockfile(stdout);
}

// ---------- pages ----------

// Closes whatever owns the panel and opens what the model now shows. No audio fill can observe
// freed game state or continue across the switch.
static void set_owner(owner_t next)
{
    xSemaphoreTake(s_audio_lock, portMAX_DELAY);
    adv_boot_stop(&s_boot); s_boot_closed = true;
    adv_ui_boot_end();
    if (s_owner == OWNER_VERSUS && next != OWNER_VERSUS) versus_close();
    if (s_owner == OWNER_DIVE) nabo_dive_close();
    else adv_ui_close();
    bool ok;
    if (next == OWNER_DIVE) ok = nabo_dive_open(bsp_display_io(), bsp_display_panel(), esp_random());
    else {
        ok = adv_ui_open();
        if (next == OWNER_JUMP) {
            nabo_jump_reset(&s_jump, esp_random(), s_model.best[STATION_JUMP]);
            atomic_store(&s_jump_cue, 0);
        }
        if (ok && next == OWNER_VERSUS) versus_open(s_vs_open_game);
    }
    if (!ok) {
        ESP_LOGE(TAG, "owner %d failed to open; back to the map", next);
        next = OWNER_SHELL;
        s_model.page = ADV_PAGE_MAP;
        if (!adv_ui_open()) { xSemaphoreGive(s_audio_lock); esp_restart(); return; }
    }
    s_owner = next;
    s_swallowed |= s_held;
    xSemaphoreGive(s_audio_lock);
    ESP_LOGI(TAG, "owner=%d page=%d heap=%u", s_owner, s_model.page, (unsigned)esp_get_free_heap_size());
}

static void handle_fx(int fx)
{
    bool horn=false; // POST V2 has no held whistle action.
    atomic_store(&s_post_horn,horn);
    if (s_model.page != ADV_PAGE_COVER) stop_boot();
    if (fx & ADV_FX_CUE) atomic_store(&s_cue, s_model.cue);
    if (fx & ADV_FX_APPLY_SETTINGS) apply_settings();
    if (fx & ADV_FX_SAVE_SETTINGS) adv_persist_settings(&s_model.cfg.settings);
    if (fx & ADV_FX_SAVE_PROGRESS) adv_persist_u32("adv_seen", s_model.seen);
    if (fx & ADV_FX_SAVE_BEST) {
        char key[16];
        best_key(key, sizeof(key), s_model.station);
        adv_persist_u32(key, s_model.best[s_model.station]);
    }
    if (fx & ADV_FX_NOMEM) ESP_LOGE(TAG, "session allocation failed; heap=%u", (unsigned)esp_get_free_heap_size());
    if (fx & ADV_FX_OPEN_LEGACY) set_owner(s_model.cursor == STATION_DIVE ? OWNER_DIVE : OWNER_JUMP);
    if (fx & ADV_FX_OPEN_VERSUS) set_owner(OWNER_VERSUS);
}

// A legacy game asked to leave: hand its record to the shell.
static void legacy_back(void)
{
    uint32_t best;
    if (s_owner == OWNER_VERSUS) {   // a race is not a record attempt: back to the kiosk, nothing saved
        race_stop();
        set_owner(OWNER_SHELL);
        handle_fx(adv_versus_done(&s_model));
        adv_ui_invalidate();
        return;
    }
    if (s_owner == OWNER_JUMP) {
        adv_persist_jump(s_jump.best);
        best = s_jump.best;
    } else {
        cg_settings_t settings; uint32_t saved[ADV_STATIONS], seen;
        adv_persist_load(&settings, saved, &seen);
        best = saved[STATION_DIVE];
    }
    set_owner(OWNER_SHELL);
    handle_fx(adv_legacy_done(&s_model, best));
    adv_ui_invalidate();
}

// ---------- input ----------

static void on_button(bsp_btn_t button, bsp_btn_ev_t event, void *user)
{
    (void)user;
    input_t in = {.button = button, .event = event, .ms = (uint32_t)(esp_timer_get_time() / 1000)};
    if (xQueueSend(s_inputs, &in, 0) != pdTRUE) atomic_store(&s_overflow, true);
}

static void jump_button(const input_t *in)
{
    if (in->button == BSP_BTN_OK) {
        if (in->event == BSP_BTN_PRESS) {
            nabo_jump_press(&s_jump, in->ms);
            if (nabo_jump_charging(&s_jump)) atomic_store(&s_jump_cue, 5);
        } else if (in->event == BSP_BTN_RELEASE) {
            nabo_jump_release(&s_jump, in->ms);
            atomic_store(&s_jump_cue, s_jump.phase == JUMP_FLYING ? 1 : 0);
        }
    } else if (in->event == BSP_BTN_CLICK && in->button == BSP_BTN_DOWN) s_jump.character = 1 - s_jump.character;
    else if (in->event == BSP_BTN_LONG && in->button == BSP_BTN_DOWN) {
        adv_persist_jump(s_jump.best);
        nabo_jump_reset(&s_jump, esp_random(), s_jump.best);
        adv_ui_invalidate();
    }
}

static void dive_button(const input_t *in)
{
    if (in->button == BSP_BTN_UP && in->event == BSP_BTN_CLICK) nabo_dive_key(MUSE_MENU_UP);
    else if ((in->button == BSP_BTN_OK || in->button == BSP_BTN_DOWN) &&
             (in->event == BSP_BTN_PRESS || in->event == BSP_BTN_RELEASE))
        nabo_dive_button(in->button == BSP_BTN_OK ? NABO_DIVE_BUTTON_OK : NABO_DIVE_BUTTON_DOWN,
                         in->event == BSP_BTN_PRESS, in->ms);
}

static void handle_button(const input_t *in)
{
    s_last_input_us = esp_timer_get_time();
    unsigned bit = 1u << in->button;
    if (in->event == BSP_BTN_PRESS) { s_held |= bit; s_swallowed &= ~bit; }
    if (in->event == BSP_BTN_RELEASE) s_held &= ~bit;
    if (s_swallowed & bit) {
        // Keep the model's held mask honest even for swallowed buttons.
        if (in->event == BSP_BTN_RELEASE) s_model.held &= ~bit;
        return;
    }
    bool landscape_race = s_owner == OWNER_VERSUS && s_vs.page == VS_PLAY && versus_session();
    if(s_owner!=OWNER_SHELL&&!landscape_race&&adv_game_map_key((adv_btn_t)in->button,(adv_ev_t)in->event)) {legacy_back();return;}
    if (s_owner == OWNER_JUMP) jump_button(in);
    else if (s_owner == OWNER_VERSUS) versus_button(in);
    else if (s_owner == OWNER_DIVE) dive_button(in);
    else handle_fx(adv_event(&s_model, (adv_btn_t)in->button, (adv_ev_t)in->event));
}

// ---------- serial diagnostics ----------
static void link_probe(void)
{
    size_t h0 = heap_caps_get_free_size(MALLOC_CAP_8BIT), l0 = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);
    bool ok = adv_link_begin();
    size_t h1 = heap_caps_get_free_size(MALLOC_CAP_8BIT), l1 = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);
    uint8_t pkt[ADV_LINK_PACKET_BYTES] = {'N', 'A', 'B', 'O'};
    bool sent = ok && adv_link_send(NULL, pkt, sizeof pkt);
    vTaskDelay(pdMS_TO_TICKS(200));
    adv_link_end();
    size_t h2 = heap_caps_get_free_size(MALLOC_CAP_8BIT), l2 = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);
    printf("@link ok=%d sent=%d err=%s before=%u/%u on=%u/%u after=%u/%u\n", ok, sent, adv_link_error(),
           (unsigned)h0, (unsigned)l0, (unsigned)h1, (unsigned)l1, (unsigned)h2, (unsigned)l2);
}


static void status(void)
{
    adv_status_t st = adv_game_status(&s_model);
    flockfile(stdout);  // keep independent legacy-game logs out of this JSON line
    printf("@adv {\"page\":%d,\"owner\":%d,\"cursor\":%d,\"station\":%d,\"phase\":%d,\"score\":%u,\"res\":%d,"
           "\"seen\":%u,\"stamps\":%d,\"test\":%d,\"heap\":%u,\"largest\":%u,\"bytes\":%u,\"overflow\":%d,\"frames\":%u,\"draw_us\":%u,\"draw_max_us\":%u,\"best\":[",
           s_model.page, s_owner, s_model.cursor, s_model.in_session ? s_model.station : -1,
           s_model.in_session ? s_model.phase : -1, (unsigned)st.score, st.resource, (unsigned)s_model.seen,
           __builtin_popcount(adv_earned(&s_model)), s_test, (unsigned)esp_get_free_heap_size(),
           (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_8BIT), (unsigned)adv_ui_bytes(), adv_ui_overflow(),
           (unsigned)s_draw_frames,(unsigned)s_draw_us,(unsigned)s_draw_max_us);
    for (int i = 0; i < ADV_STATIONS; i++) printf("%s%u", i ? "," : "", (unsigned)s_model.best[i]);
    ui_boot_video_stats_t boot=ui_boot_video_stats();
    printf("],\"view_w\":%d,\"view_h\":%d,\"boot_frames\":%u,\"boot_skipped\":%u,\"boot_last\":%u,\"boot_elapsed_ms\":%u}\n",
           adv_ui_width(),adv_ui_height(),(unsigned)boot.frames,(unsigned)boot.skipped,(unsigned)boot.last_frame,(unsigned)boot.elapsed_ms);
    funlockfile(stdout);
}

static void post_status(void)
{
    if(!s_model.in_session||s_model.station!=3||!s_model.game){puts("@error POST not active");return;}
    const adv_post_v2_t *g=s_model.game;flockfile(stdout);
    printf("@post {\"v2\":1,\"tick\":%u,\"score\":%u,\"res\":%d,\"over\":%d,\"speed\":%d,\"dist\":%d,\"bags\":%d,\"delivered\":%d,\"perfects\":%d,\"cranes\":%d,\"reds\":%d,\"derails\":%d,\"zone\":%d,\"events\":[",
           (unsigned)g->tick,(unsigned)g->score,(int)g->res,(int)g->over,(int)g->v,(int)g->dist,(int)g->bags,(int)g->delivered,(int)g->perfects,(int)g->cranes,(int)g->reds,(int)g->derails,(int)g->zone);
    for(int i=0;i<POST_V2_EVENTS;i++){const adv_post_v2_event_t *e=&g->ev[i];printf("%s[%d,%d,%d,%d,%d,%d]",i?",":"",(int)e->type,(int)e->x,(int)e->a,(int)e->b,(int)e->t,(int)e->done);}
    puts("]}");funlockfile(stdout);
}

static void inject(int button, int event)
{
    input_t in = {.button = button, .event = event, .ms = (uint32_t)(esp_timer_get_time() / 1000)};
    handle_button(&in);
}

static void set_test(bool enabled)
{
    if (enabled == s_test) return;
    atomic_store(&s_post_horn,false);
    stop_boot();
    // Keep every writer suppressed until the legacy task has stopped and its test
    // state is discarded. Leaving test mode reloads durable settings/progress.
    adv_persist_set_test(true);
    if (s_owner != OWNER_SHELL) legacy_back();
    if (!enabled) {
        xSemaphoreTake(s_audio_lock, portMAX_DELAY);
        adv_persist_restore(&s_model, esp_random());
        memset(&s_jump, 0, sizeof(s_jump));
        s_held = 0; s_swallowed = 7;
        xSemaphoreGive(s_audio_lock);
        apply_settings();
        adv_ui_invalidate();
    }
    s_test = s_model.test = enabled;
    adv_persist_set_test(enabled);
    s_last_input_us = s_step_us = esp_timer_get_time();
}

static void diagnostic_open(const char *name)
{
    if (!s_test || s_owner != OWNER_SHELL || s_model.page != ADV_PAGE_MAP) {
        puts("@error open requires test mode and the map"); return;
    }
    static const char *const shell[]={"post","night","climb","ski","sky","space"};int station=-1;
    for(int i=0;i<6;i++)if(!strcmp(name,shell[i]))station=3+i;
    if(station>=3) {
        handle_fx(adv_test_open(&s_model,station));
        s_draw_frames=s_draw_us=s_draw_max_us=0;
        if(!s_model.in_session)puts("@error game test entry failed");
        else printf("@adv open=%s\n",name);
        s_last_input_us=s_step_us=esp_timer_get_time();return;
    }
    station = !strcmp(name, "jump") ? STATION_JUMP : !strcmp(name, "dive") ? STATION_DIVE : -1;
    if (station < 0) { puts("@error unknown game"); return; }
    // This diagnostic bypasses the map unlock check without touching model rules
    // or adding fake records. The ordinary owner/return lifecycle stays in use.
    s_model.cursor = station;
    s_model.page = ADV_PAGE_LEGACY;
    set_owner(station == STATION_JUMP ? OWNER_JUMP : OWNER_DIVE);
    s_last_input_us = esp_timer_get_time();
    if (s_owner == OWNER_SHELL) puts("@error game open failed");
    else printf("@adv open=%s\n", name);
}

static void command(const char *line)
{
    if (!strcmp(line, ">adv.status")) status();
    else if (!strcmp(line, ">adv.link")) link_probe();
    else if (!strcmp(line, ">vs.status")) versus_status();
    else if (!strcmp(line, ">vs.auto=1") || !strcmp(line, ">vs.auto=0")) {
        if (s_owner != OWNER_VERSUS) puts("@error versus not open");
        else { s_vs_auto = line[9] == '1'; printf("@vs auto=%d\n", s_vs_auto); }
    }
    else if (!strcmp(line, ">vs.open") || !strncmp(line, ">vs.open=", 9)) {
        int game = line[8] == '=' ? atoi(line + 9) : 1;
        if (s_owner != OWNER_SHELL || s_model.page != ADV_PAGE_MAP) puts("@error vs.open requires the map");
        else if (game < 1 || game > 8) puts("@error vs.open=<1..8>");
        else { s_vs_open_game = game; s_model.page = ADV_PAGE_LEGACY; set_owner(OWNER_VERSUS); s_vs_open_game = 0; puts("@vs open"); }
    }
    else if(!strcmp(line,">adv.profile")){if(s_test){ag_profile_next();puts("@adv profiling=1");}else puts("@error profile requires test mode");}
    else if(!strcmp(line,">post.status"))post_status();
    else if(!strcmp(line,">night.status"))adv_night_debug(&s_model);
    else if(!strcmp(line,">space.status"))adv_space_debug(&s_model);
    else if(!strcmp(line,">climb.status"))adv_climb_debug(&s_model);
    else if(!strcmp(line,">adv.practice=post")) puts("@error POST V2: use middle key to start");
    else if (!strncmp(line, ">adv.open=", 10)) diagnostic_open(line + 10);
    else if (!strncmp(line, ">adv.key=", 9)) {
        static const struct { const char *name; int button, event; } keys[] = {
            {"up", BSP_BTN_UP, BSP_BTN_CLICK}, {"down", BSP_BTN_DOWN, BSP_BTN_CLICK}, {"ok", BSP_BTN_OK, BSP_BTN_CLICK},
            {"long_up", BSP_BTN_UP, BSP_BTN_LONG}, {"double_up", BSP_BTN_UP, BSP_BTN_DOUBLE},
            {"double_down", BSP_BTN_DOWN, BSP_BTN_DOUBLE},
            {"long_ok", BSP_BTN_OK, BSP_BTN_LONG}, {"long_down", BSP_BTN_DOWN, BSP_BTN_LONG},
        };
        for (size_t i = 0; i < sizeof(keys) / sizeof(keys[0]); i++)
            if (!strcmp(line + 9, keys[i].name)) { inject(keys[i].button, keys[i].event); return; }
        puts("@error unknown key");
    } else if (!strncmp(line, ">adv.edge=", 10)) {
        int button, pressed;
        if (sscanf(line + 10, "%d,%d", &button, &pressed) == 2 && button >= 0 && button <= 2 && (pressed == 0 || pressed == 1))
            inject(button, pressed ? BSP_BTN_PRESS : BSP_BTN_RELEASE);
    } else if (!strcmp(line, ">adv.capture")) {
        if (s_owner == OWNER_DIVE) puts("@error capture not available in DIVE");
        else adv_ui_capture();
    } else if (!strncmp(line, ">adv.test=", 10)) {
        // Test mode: nothing is saved, and the model never raises a record save.
        set_test(line[10] == '1');
        printf("@adv test=%d\n", s_test);
    } else puts("@error unknown command");
}

static void serial_task(void *arg)
{
    (void)arg;
    char line[96]; size_t used = 0;
    for (;;) {
        int c = getchar();
        if (c == EOF) { clearerr(stdin); vTaskDelay(pdMS_TO_TICKS(20)); continue; }
        if (c == '\n' || c == '\r') {
            line[used] = 0;
            if (used && line[0] == '>') {
                input_t in = {.command = true}; memcpy(in.line, line, used + 1);
                if (xQueueSend(s_inputs, &in, 0) != pdTRUE) puts("@error command queue full");
            }
            used = 0;
        } else if (used + 1 < sizeof(line)) line[used++] = (char)c;
        else used = 0;
    }
}

// ---------- audio ----------

static void audio_task(void *arg)
{
    (void)arg;
    int16_t pcm[CHUNK];
    nabo_jump_sound_t jump_audio = {0};
    adv_sound_t cue_audio = {0};
    int last_cue=0;
    for (;;) {
        xSemaphoreTake(s_audio_lock, portMAX_DELAY);
        memset(pcm, 0, sizeof(pcm));
        if (s_owner == OWNER_DIVE || (s_owner == OWNER_VERSUS && atomic_load(&s_vs_dive_audio))) nabo_dive_audio_fill(pcm, CHUNK);
        else if (s_owner == OWNER_JUMP || (s_owner == OWNER_VERSUS && !atomic_load(&s_vs_shell_audio))) {
            int cue = atomic_exchange(&s_jump_cue, -1);
            if (cue >= 0) nabo_jump_sound_start(&jump_audio, cue, 1);
            nabo_jump_sound_fill(&jump_audio, pcm, CHUNK);
        } else {
            int cue = atomic_exchange(&s_cue, 0);
            if (cue > 0){adv_sound_start(&cue_audio,cue);last_cue=cue;}
            if(last_cue==ADV_CUE_WHISTLE&&!atomic_load(&s_post_horn)){adv_sound_start(&cue_audio,0);last_cue=0;}
            adv_sound_fill(&cue_audio, pcm, CHUNK);
            adv_boot_tick(&s_boot, (uint32_t)(esp_timer_get_time() / 1000));
            adv_boot_fill(&s_boot, pcm, CHUNK);
        }
        bool delay = !s_audio_ok || bsp_audio_write(pcm, sizeof(pcm)) != ESP_OK;
        xSemaphoreGive(s_audio_lock);
        // A higher-priority producer must block after giving the mutex so a waiting UI task can
        // acquire it before the next PCM chunk. One tick fits inside the I2S DMA buffer.
        vTaskDelay(delay ? pdMS_TO_TICKS(20) : 1);
    }
}

// ---------- sleep and main loop ----------

static void sleep_now(void)
{
    if (s_held || bsp_button_read_mv() < BSP_BTN_MV_RELEASED_MIN) return;
    xSemaphoreTake(s_audio_lock, portMAX_DELAY);
    adv_boot_stop(&s_boot); s_boot_closed = true;
    adv_ui_boot_end();
    if (s_owner == OWNER_VERSUS) versus_close();
    if (s_owner == OWNER_DIVE) nabo_dive_close();
    else { if (s_owner == OWNER_JUMP) adv_persist_jump(s_jump.best); adv_ui_close(); }
    bsp_display_backlight(0);
    int level = 0;
    if (bsp_button_prepare_deep_sleep(&level) != ESP_OK || !level) esp_restart();
    report_error("wake GPIO", esp_sleep_enable_gpio_wakeup_on_hp_periph_powerdown(1ULL << BSP_BTN_GPIO, ESP_GPIO_WAKEUP_GPIO_LOW));
    report_error("battery sleep", bsp_battery_sleep());
    if (s_audio_ok) {
        report_error("codec sleep", bsp_audio_sleep());
        report_error("I2S sleep", bsp_audio_prepare_deep_sleep());
    }
    report_error("I2C sleep", bsp_i2c_prepare_deep_sleep());
    report_error("panel sleep", bsp_display_prepare_deep_sleep());
    esp_deep_sleep_start();
    esp_restart();
}

static void jump_tick(uint32_t ms)
{
    jump_phase_t before = s_jump.phase;
    nabo_jump_tick(&s_jump, ms);
    if (s_jump.sound) {
        s_jump.sound = false;
        atomic_store(&s_jump_cue, s_jump.pending_charge && !s_jump.pending_released ? 5 : s_jump.centered ? 2 : 3);
    }
    if (before == JUMP_SCROLLING && s_jump.phase == JUMP_FLYING) atomic_store(&s_jump_cue, 1);
    if (s_jump.phase == JUMP_FALLING && before != JUMP_FALLING) atomic_store(&s_jump_cue, 4);
    if (s_jump.phase == JUMP_OVER) adv_persist_jump(s_jump.best);
    int64_t draw_start = esp_timer_get_time();
    adv_jump_draw(&s_jump, ms, false);
    s_draw_us = (uint32_t)(esp_timer_get_time() - draw_start);
    s_draw_frames++;
    if (s_draw_us > s_draw_max_us) s_draw_max_us = s_draw_us;
}

static void adventure_task(void *arg)
{
    (void)arg;
    int battery = -1, mv = -1;
    int64_t battery_at = 0;
    bool dirty = true;
    uint32_t last_ui_frame = UINT32_MAX;
    unsigned last_boot_pose = UINT16_MAX;
    uint32_t last_draw_ms=0;
    for (;;) {
        if (atomic_exchange(&s_overflow, false)) {
            ESP_LOGE(TAG, "input overflow; cancelling held actions");
            xQueueReset(s_inputs); s_held = 0; s_swallowed = 7; s_model.held = 0;
            if (s_owner != OWNER_SHELL) legacy_back();
        }
        input_t input;
        while (xQueueReceive(s_inputs, &input, 0) == pdTRUE) {
            if (input.command) command(input.line); else handle_button(&input);
            dirty = true;
        }
        int64_t us = esp_timer_get_time();
        uint32_t ms = (uint32_t)(us / 1000);
        if (us - battery_at >= 5000000) { battery = bsp_battery_soc(); mv = bsp_battery_mv(); battery_at = us; }
        if (s_owner == OWNER_JUMP) jump_tick(ms);
        else if (s_owner == OWNER_VERSUS) versus_tick(ms);
        else if (s_owner == OWNER_SHELL) {
            uint32_t ui_frame = ms / 1000u * 12u + ms % 1000u * 12u / 1000u;
            if (ui_frame != last_ui_frame) { dirty = true; last_ui_frame = ui_frame; }
            if(s_model.page==ADV_PAGE_COVER&&adv_ui_boot_initial()&&
               ui_boot_video_pending(adv_ui_boot_elapsed(ms)))dirty=true;
            if (s_model.page == ADV_PAGE_COVER && adv_ui_boot_initial() && adv_boot_motion_enabled()) {
                unsigned pose = adv_boot_motion_frame(adv_ui_boot_elapsed(ms));
                if (pose != last_boot_pose) { dirty = true; last_boot_pose = pose; }
            }
            // Fixed 60 Hz model steps; never more than a few to catch up after a slow frame.
            int steps = 0;
            while (us - s_step_us >= STEP_US && steps < 4) {
                int fx = adv_step(&s_model);
                handle_fx(fx);
                if (fx & ADV_FX_REDRAW) dirty = true;
                s_step_us += STEP_US;
                steps++;
            }
            if (us - s_step_us >= STEP_US) s_step_us = us;
            bool game=s_model.page==ADV_PAGE_SESSION&&(s_model.station==3||s_model.station==4);
            if (dirty&&(!game||ms-last_draw_ms>=33)) {
                int64_t draw_start=esp_timer_get_time();
                adv_ui_draw(&s_model, ms, battery, mv);dirty=false;last_draw_ms=ms;
                s_draw_us=(uint32_t)(esp_timer_get_time()-draw_start);s_draw_frames++;
                if(s_draw_us>s_draw_max_us)s_draw_max_us=s_draw_us;
            }
        }
        if (s_model.cfg.settings.sleep_seconds > 0 &&
            us - s_last_input_us > (int64_t)s_model.cfg.settings.sleep_seconds * 1000000) sleep_now();
        bool boot_pending=s_owner==OWNER_SHELL&&s_model.page==ADV_PAGE_COVER&&adv_ui_boot_initial()&&
                          ui_boot_video_pending(adv_ui_boot_elapsed((uint32_t)(esp_timer_get_time()/1000)));
        // The V2 renderer already spends most of its frame composing pixels.
        // Yield one tick during play; retain the fixed 60 Hz simulation above.
        bool v2_play=s_owner==OWNER_SHELL&&s_model.page==ADV_PAGE_SESSION&&s_model.phase==ADV_PLAY&&
                     (s_model.station>=3&&s_model.station<=8);
        vTaskDelay(pdMS_TO_TICKS(boot_pending||v2_play?1:s_owner == OWNER_SHELL && s_model.page == ADV_PAGE_SESSION ? 5 : 10));
    }
}

void app_main(void)
{
    // Preserve old settings/records. Never erase NVS to mask an initialization error.
    ESP_ERROR_CHECK(nvs_flash_init());
    s_inputs = xQueueCreate(32, sizeof(input_t));
    s_audio_lock = xSemaphoreCreateMutex();
    if (!s_inputs || !s_audio_lock) { ESP_LOGE(TAG, "startup allocation failed"); return; }
    cg_settings_t settings;
    uint32_t best[ADV_STATIONS], seen;
    adv_persist_load(&settings, best, &seen);
    adv_init(&s_model, esp_random(), &settings, best, seen);
    ESP_ERROR_CHECK(bsp_display_init());
    report_error("battery", bsp_battery_init());
    s_audio_ok = bsp_audio_init() == ESP_OK && bsp_audio_set_format(16000, 16, 1) == ESP_OK;
    if (!s_audio_ok) ESP_LOGW(TAG, "codec unavailable; running silently");
    atomic_store(&s_jump_cue, -1);
    if (!adv_ui_open()) { ESP_LOGE(TAG, "launcher allocation failed"); return; }
    s_last_input_us = s_step_us = esp_timer_get_time();
    adv_ui_boot_begin((uint32_t)(s_last_input_us / 1000));
    adv_ui_draw(&s_model, (uint32_t)(s_last_input_us / 1000), -1, -1);
    apply_settings();
    uint32_t visual_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    adv_ui_boot_begin(visual_start_ms);
    if (!adv_boot_open(&s_boot, boot_wav_start, (size_t)(boot_wav_end - boot_wav_start),
                       visual_start_ms))
        ESP_LOGW(TAG, "boot narration unavailable; cover remains playable");
    if (xTaskCreate(audio_task, "adv_audio", 4096, NULL, 5, NULL) != pdPASS ||
        xTaskCreate(adventure_task, "adv_ui", 10240, NULL, 4, NULL) != pdPASS ||
        xTaskCreate(serial_task, "adv_serial", 4096, NULL, 3, NULL) != pdPASS) {
        ESP_LOGE(TAG, "task allocation failed"); esp_restart();
    }
    ESP_ERROR_CHECK(bsp_button_init(on_button, NULL));
    ESP_LOGI(TAG, "adventure ready; heap=%u", (unsigned)esp_get_free_heap_size());
}
