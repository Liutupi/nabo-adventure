// NVS policy shared with the legacy games. Test runs never write user state.
#include "adv_persist.h"
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include "esp_log.h"
#include "nabo_dive_model.h"
#include "nvs.h"

#define TAG "NABO-Save"
#define NVS_NS "nabo_ui"
static atomic_bool s_test;
static uint32_t s_jump_saved;

void adv_persist_set_test(bool enabled) { atomic_store(&s_test, enabled); }
bool adv_persist_test(void) { return atomic_load(&s_test); }

static uint32_t read_u32(nvs_handle_t h, const char *key)
{
    uint32_t value = 0;
    nvs_get_u32(h, key, &value);
    return value;
}

void adv_persist_load(cg_settings_t *s, uint32_t best[ADV_STATIONS], uint32_t *seen)
{
    *s = (cg_settings_t){.volume = 70, .brightness = 80, .sleep_seconds = 300, .speaker = true};
    memset(best, 0, sizeof(uint32_t) * ADV_STATIONS);
    *seen = 0;
    s_jump_saved = 0;
    nvs_handle_t h;
    if (nvs_open(NVS_NS, NVS_READONLY, &h) != ESP_OK) return;
    int32_t value; uint8_t flag;
    if (nvs_get_i32(h, "volume", &value) == ESP_OK) s->volume = value;
    if (nvs_get_i32(h, "brightness", &value) == ESP_OK) s->brightness = value;
    if (nvs_get_i32(h, "sleep", &value) == ESP_OK) s->sleep_seconds = value;
    if (nvs_get_u8(h, "speaker", &flag) == ESP_OK) s->speaker = flag != 0;
    best[1] = s_jump_saved = read_u32(h, "jump_best");
    best[2] = (uint32_t)dive_depth_m((float)read_u32(h, "dive_best"));
    for (int i = 3; i < ADV_STATIONS; i++) {
        char key[16];
        snprintf(key, sizeof(key), "adv_b_%s", adv_station[i].id);
        best[i] = read_u32(h, key);
    }
    *seen = read_u32(h, "adv_seen");
    nvs_close(h);
    cg_sanitize(s);
}

void adv_persist_restore(adv_model_t *model, uint32_t seed)
{
    cg_settings_t settings;
    uint32_t best[ADV_STATIONS], seen;
    adv_persist_load(&settings, best, &seen);
    adv_free(model);
    adv_init(model, seed, &settings, best, seen);
}

static esp_err_t finish(nvs_handle_t h, esp_err_t err, const char *key)
{
    if (err == ESP_OK) err = nvs_commit(h);
    nvs_close(h);
    if (err != ESP_OK) ESP_LOGE(TAG, "%s: %s", key, esp_err_to_name(err));
    return err;
}

static esp_err_t store_u32(const char *key, uint32_t value)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) return finish(h, nvs_set_u32(h, key, value), key);
    ESP_LOGE(TAG, "%s: %s", key, esp_err_to_name(err));
    return err;
}

void adv_persist_u32(const char *key, uint32_t value)
{
    if (!adv_persist_test()) (void)store_u32(key, value);
}

void adv_persist_u8(const char *key, uint8_t value)
{
    if (adv_persist_test()) return;
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) (void)finish(h, nvs_set_u8(h, key, value), key);
    else ESP_LOGE(TAG, "%s: %s", key, esp_err_to_name(err));
}

void adv_persist_settings(const cg_settings_t *s)
{
    if (adv_persist_test()) return;
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) {
        err = nvs_set_i32(h, "volume", s->volume);
        if (!err) err = nvs_set_i32(h, "brightness", s->brightness);
        if (!err) err = nvs_set_i32(h, "sleep", s->sleep_seconds);
        if (!err) err = nvs_set_u8(h, "speaker", s->speaker);
        (void)finish(h, err, "settings");
    } else ESP_LOGE(TAG, "settings: %s", esp_err_to_name(err));
}

void adv_persist_jump(uint32_t best)
{
    if (!adv_persist_test() && best > s_jump_saved && store_u32("jump_best", best) == ESP_OK)
        s_jump_saved = best;
}
