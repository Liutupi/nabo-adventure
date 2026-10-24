// NABO 的冒险之旅: offline launcher. The shell model (adv_model.c) owns pages and sessions; this
// file feeds it buttons and 60 Hz steps, persists progress, plays cues and hosts the two legacy
// games (跳一跳, 深潜). Game PCM, page lifetimes and codec I/O share one owner lock.
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include "adv_model.h"
#include "adv_sound.h"
#include "adv_ui.h"
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
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "nabo_dive.h"
#include "nabo_dive_model.h"
#include "nabo_jump_model.h"
#include "nabo_jump_sound.h"
#include "nvs.h"
#include "nvs_flash.h"

#define TAG "NABO-Adventure"
#define CHUNK 320
#define STEP_US 16667
#define NVS_NS "nabo_ui"   // shared with the NABO games collection: settings and records carry over
#define STATION_JUMP 1
#define STATION_DIVE 2

typedef struct { bool command; int button, event; uint32_t ms; char line[96]; } input_t;
typedef enum { OWNER_SHELL, OWNER_JUMP, OWNER_DIVE } owner_t;

static QueueHandle_t s_inputs;
static SemaphoreHandle_t s_audio_lock;
static adv_model_t s_model;
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

// ---------- persistence ----------

static uint32_t read_u32(nvs_handle_t h, const char *key)
{
    uint32_t v = 0;
    nvs_get_u32(h, key, &v);
    return v;
}

static void best_key(char *out, size_t size, int station) { snprintf(out, size, "adv_b_%s", adv_station[station].id); }

static void load(cg_settings_t *s, uint32_t best[ADV_STATIONS], uint32_t *seen)
{
    *s = (cg_settings_t){.volume = 70, .brightness = 80, .sleep_seconds = 300, .speaker = true};
    memset(best, 0, sizeof(uint32_t) * ADV_STATIONS);
    *seen = 0;
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return;
    int32_t v; uint8_t b;
    if (nvs_get_i32(h, "volume", &v) == ESP_OK) s->volume = v;
    if (nvs_get_i32(h, "brightness", &v) == ESP_OK) s->brightness = v;
    if (nvs_get_i32(h, "sleep", &v) == ESP_OK) s->sleep_seconds = v;
    if (nvs_get_u8(h, "speaker", &b) == ESP_OK) s->speaker = b != 0;
    best[STATION_JUMP] = read_u32(h, "jump_best");
    best[STATION_DIVE] = (uint32_t)dive_depth_m((float)read_u32(h, "dive_best"));   // stored in pixels
    for (int i = STATION_DIVE + 1; i < ADV_STATIONS; i++) {
        char key[16];
        best_key(key, sizeof(key), i);
        best[i] = read_u32(h, key);
    }
    *seen = read_u32(h, "adv_seen");
    nvs_close(h);
    cg_sanitize(s);
}

static void save_u32(const char *key, uint32_t value)
{
    if (s_test) return;   // scripted runs never touch records
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) {
        err = nvs_set_u32(h, key, value);
        if (!err) err = nvs_commit(h);
        nvs_close(h);
    }
    report_error(key, err);
}

static void save_settings(void)
{
    const cg_settings_t *s = &s_model.cfg.settings;
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) {
        err = nvs_set_i32(h, "volume", s->volume);
        if (!err) err = nvs_set_i32(h, "brightness", s->brightness);
        if (!err) err = nvs_set_i32(h, "sleep", s->sleep_seconds);
        if (!err) err = nvs_set_u8(h, "speaker", s->speaker);
        if (!err) err = nvs_commit(h);
        nvs_close(h);
    }
    report_error("settings save", err);
}

static void save_jump_best(void)
{
    if (s_jump.best > s_model.best[STATION_JUMP]) save_u32("jump_best", s_jump.best);
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
    if (fx & ADV_FX_CUE) atomic_store(&s_cue, s_model.cue);
    if (fx & ADV_FX_APPLY_SETTINGS) apply_settings();
    if (fx & ADV_FX_SAVE_SETTINGS) save_settings();
    if (fx & ADV_FX_SAVE_PROGRESS) save_u32("adv_seen", s_model.seen);
    if (fx & ADV_FX_SAVE_BEST) {
        char key[16];
        best_key(key, sizeof(key), s_model.station);
        save_u32(key, s_model.best[s_model.station]);
    }
    if (fx & ADV_FX_NOMEM) ESP_LOGE(TAG, "session allocation failed; heap=%u", (unsigned)esp_get_free_heap_size());
    if (fx & ADV_FX_OPEN_LEGACY) set_owner(s_model.cursor == STATION_DIVE ? OWNER_DIVE : OWNER_JUMP);
}

// A legacy game asked to leave: hand its record to the shell.
static void legacy_back(void)
{
    uint32_t best;
    if (s_owner == OWNER_JUMP) {
        save_jump_best();
        best = s_jump.best;
    } else {
        nvs_handle_t h;
        best = 0;
        if (nvs_open(NVS_NS, NVS_READONLY, &h) == ESP_OK) { best = (uint32_t)dive_depth_m((float)read_u32(h, "dive_best")); nvs_close(h); }
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
        save_jump_best();
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
    printf("@adv {\"page\":%d,\"owner\":%d,\"cursor\":%d,\"station\":%d,\"phase\":%d,\"score\":%u,\"res\":%d,"
           "\"seen\":%u,\"stamps\":%d,\"test\":%d,\"heap\":%u,\"largest\":%u,\"bytes\":%u,\"overflow\":%d,\"best\":[",
           s_model.page, s_owner, s_model.cursor, s_model.in_session ? s_model.station : -1,
           s_model.in_session ? s_model.phase : -1, (unsigned)st.score, st.resource, (unsigned)s_model.seen,
           __builtin_popcount(adv_earned(&s_model)), s_test, (unsigned)esp_get_free_heap_size(),
           (unsigned)heap_caps_get_largest_free_block(MALLOC_CAP_8BIT), (unsigned)adv_ui_bytes(), adv_ui_overflow());
    for (int i = 0; i < ADV_STATIONS; i++) printf("%s%u", i ? "," : "", (unsigned)s_model.best[i]);
    puts("]}");
}

static void inject(int button, int event)
{
    input_t in = {.button = button, .event = event, .ms = (uint32_t)(esp_timer_get_time() / 1000)};
    handle_button(&in);
}

static void command(const char *line)
{
    if (!strcmp(line, ">adv.status")) status();
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
        s_test = s_model.test = line[10] == '1';
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
    if (s_owner == OWNER_DIVE) nabo_dive_close();
    else { if (s_owner == OWNER_JUMP) save_jump_best(); adv_ui_close(); }
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
    if (s_jump.phase == JUMP_OVER) save_jump_best();
    adv_jump_draw(&s_jump, ms, false);
}

static void adventure_task(void *arg)
{
    (void)arg;
    int battery = -1, mv = -1;
    int64_t battery_at = 0;
    bool dirty = true;
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
    load(&settings, best, &seen);
    adv_init(&s_model, esp_random(), &settings, best, seen);
    ESP_ERROR_CHECK(bsp_display_init());
    report_error("battery", bsp_battery_init());
    s_audio_ok = bsp_audio_init() == ESP_OK && bsp_audio_set_format(16000, 16, 1) == ESP_OK;
    if (!s_audio_ok) ESP_LOGW(TAG, "codec unavailable; running silently");
    atomic_store(&s_jump_cue, -1);
    if (!adv_ui_open()) { ESP_LOGE(TAG, "launcher allocation failed"); return; }
    s_last_input_us = s_step_us = esp_timer_get_time();
    adv_ui_draw(&s_model, (uint32_t)(s_last_input_us / 1000), -1, -1);
    apply_settings();
    if (xTaskCreate(audio_task, "adv_audio", 4096, NULL, 5, NULL) != pdPASS ||
        xTaskCreate(adventure_task, "adv_ui", 10240, NULL, 4, NULL) != pdPASS ||
        xTaskCreate(serial_task, "adv_serial", 4096, NULL, 3, NULL) != pdPASS) {
        ESP_LOGE(TAG, "task allocation failed"); esp_restart();
    }
    ESP_ERROR_CHECK(bsp_button_init(on_button, NULL));
    ESP_LOGI(TAG, "adventure ready; heap=%u", (unsigned)esp_get_free_heap_size());
}
