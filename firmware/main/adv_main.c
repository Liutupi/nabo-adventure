// NABO 的冒险之旅: offline launcher. The shell model (adv_model.c) owns pages and sessions; this
// file feeds it buttons and 60 Hz steps, persists progress, plays cues and hosts the two legacy
// games (跳一跳, 深潜). Game PCM, page lifetimes and codec I/O share one owner lock.
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include "adv_boot.h"
#include "adv_model.h"
#include "adv_persist.h"
#include "adv_sound.h"
#include "adv_ui.h"
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
typedef enum { OWNER_SHELL, OWNER_JUMP, OWNER_DIVE } owner_t;

static QueueHandle_t s_inputs;
static SemaphoreHandle_t s_audio_lock;
static adv_model_t s_model;
static adv_boot_t s_boot;
static bool s_boot_closed;
extern const uint8_t boot_wav_start[] asm("_binary_adv_boot_voice_wav_start");
extern const uint8_t boot_wav_end[] asm("_binary_adv_boot_voice_wav_end");
static owner_t s_owner = OWNER_SHELL;        // who draws and who feeds PCM
static nabo_jump_t s_jump;
static bool s_audio_ok, s_test;
static atomic_bool s_overflow;
static atomic_int s_jump_cue, s_cue;
static unsigned s_held, s_swallowed;
static int64_t s_last_input_us, s_step_us;

static void report_error(const char *what, esp_err_t err)
{
    if (err != ESP_OK) ESP_LOGE(TAG, "%s: %s", what, esp_err_to_name(err));
}

static void best_key(char *out, size_t size, int station) { snprintf(out, size, "adv_b_%s", adv_station[station].id); }

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

// ---------- pages ----------

// Closes whatever owns the panel and opens what the model now shows. No audio fill can observe
// freed game state or continue across the switch.
static void set_owner(owner_t next)
{
    xSemaphoreTake(s_audio_lock, portMAX_DELAY);
    adv_boot_stop(&s_boot); s_boot_closed = true;
    adv_ui_boot_end();
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
}

// A legacy game asked to leave: hand its record to the shell.
static void legacy_back(void)
{
    uint32_t best;
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
    } else if (in->event == BSP_BTN_CLICK && in->button == BSP_BTN_UP) legacy_back();
    else if (in->event == BSP_BTN_CLICK && in->button == BSP_BTN_DOWN) s_jump.character = 1 - s_jump.character;
    else if (in->event == BSP_BTN_LONG && in->button == BSP_BTN_DOWN) {
        adv_persist_jump(s_jump.best);
        nabo_jump_reset(&s_jump, esp_random(), s_jump.best);
        adv_ui_invalidate();
    }
}

static void dive_button(const input_t *in)
{
    if (in->button == BSP_BTN_UP && in->event == BSP_BTN_LONG) { legacy_back(); return; }
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
    if (s_owner == OWNER_JUMP) jump_button(in);
    else if (s_owner == OWNER_DIVE) dive_button(in);
    else handle_fx(adv_event(&s_model, (adv_btn_t)in->button, (adv_ev_t)in->event));
}

// ---------- serial diagnostics ----------

static void status(void)
{
    adv_status_t st = adv_game_status(&s_model);
    flockfile(stdout);  // keep independent legacy-game logs out of this JSON line
    printf("@adv {\"page\":%d,\"owner\":%d,\"cursor\":%d,\"station\":%d,\"phase\":%d,\"score\":%u,\"res\":%d,"
           "\"seen\":%u,\"stamps\":%d,\"test\":%d,\"heap\":%u,\"largest\":%u,\"bytes\":%u,\"overflow\":%d,\"best\":[",
           s_model.page, s_owner, s_model.cursor, s_model.in_session ? s_model.station : -1,
           s_model.in_session ? s_model.phase : -1, (unsigned)st.score, st.resource, (unsigned)s_model.seen,
           __builtin_popcount(adv_earned(&s_model)), s_test, (unsigned)esp_get_free_heap_size(),
           (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_8BIT), (unsigned)adv_ui_bytes(), adv_ui_overflow());
    for (int i = 0; i < ADV_STATIONS; i++) printf("%s%u", i ? "," : "", (unsigned)s_model.best[i]);
    puts("]}");
    funlockfile(stdout);
}

static void inject(int button, int event)
{
    input_t in = {.button = button, .event = event, .ms = (uint32_t)(esp_timer_get_time() / 1000)};
    handle_button(&in);
}

static void set_test(bool enabled)
{
    if (enabled == s_test) return;
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
    int station = !strcmp(name, "jump") ? STATION_JUMP : !strcmp(name, "dive") ? STATION_DIVE : -1;
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
    else if (!strncmp(line, ">adv.open=", 10)) diagnostic_open(line + 10);
    else if (!strncmp(line, ">adv.key=", 9)) {
        static const struct { const char *name; int button, event; } keys[] = {
            {"up", BSP_BTN_UP, BSP_BTN_CLICK}, {"down", BSP_BTN_DOWN, BSP_BTN_CLICK}, {"ok", BSP_BTN_OK, BSP_BTN_CLICK},
            {"long_up", BSP_BTN_UP, BSP_BTN_LONG}, {"double_up", BSP_BTN_UP, BSP_BTN_DOUBLE},
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
    for (;;) {
        xSemaphoreTake(s_audio_lock, portMAX_DELAY);
        memset(pcm, 0, sizeof(pcm));
        if (s_owner == OWNER_DIVE) nabo_dive_audio_fill(pcm, CHUNK);
        else if (s_owner == OWNER_JUMP) {
            int cue = atomic_exchange(&s_jump_cue, -1);
            if (cue >= 0) nabo_jump_sound_start(&jump_audio, cue, 1);
            nabo_jump_sound_fill(&jump_audio, pcm, CHUNK);
        } else {
            int cue = atomic_exchange(&s_cue, 0);
            if (cue > 0) adv_sound_start(&cue_audio, cue);
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
    adv_jump_draw(&s_jump, ms, false);
}

static void adventure_task(void *arg)
{
    (void)arg;
    int battery = -1, mv = -1;
    int64_t battery_at = 0;
    bool dirty = true;
    uint32_t last_ui_frame = UINT32_MAX;
    unsigned last_boot_pose = UINT16_MAX;
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
        else if (s_owner == OWNER_SHELL) {
            uint32_t ui_frame = ms / 1000u * 12u + ms % 1000u * 12u / 1000u;
            if (ui_frame != last_ui_frame) { dirty = true; last_ui_frame = ui_frame; }
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
            if (dirty) { adv_ui_draw(&s_model, ms, battery, mv); dirty = false; }
        }
        if (s_model.cfg.settings.sleep_seconds > 0 &&
            us - s_last_input_us > (int64_t)s_model.cfg.settings.sleep_seconds * 1000000) sleep_now();
        vTaskDelay(pdMS_TO_TICKS(s_owner == OWNER_SHELL && s_model.page == ADV_PAGE_SESSION ? 5 : 10));
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
