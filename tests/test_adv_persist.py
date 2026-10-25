"""Execute the production NVS policy with a recording in-memory NVS backend."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'firmware/main'

NVS = r'''
#pragma once
#include <stdint.h>
typedef int esp_err_t;
typedef int nvs_handle_t;
#define ESP_OK 0
#define NVS_READONLY 0
#define NVS_READWRITE 1
const char *esp_err_to_name(esp_err_t);
esp_err_t nvs_open(const char *, int, nvs_handle_t *);
void nvs_close(nvs_handle_t);
esp_err_t nvs_get_u32(nvs_handle_t, const char *, uint32_t *);
esp_err_t nvs_get_i32(nvs_handle_t, const char *, int32_t *);
esp_err_t nvs_get_u8(nvs_handle_t, const char *, uint8_t *);
esp_err_t nvs_set_u32(nvs_handle_t, const char *, uint32_t);
esp_err_t nvs_set_i32(nvs_handle_t, const char *, int32_t);
esp_err_t nvs_set_u8(nvs_handle_t, const char *, uint8_t);
esp_err_t nvs_commit(nvs_handle_t);
'''

HARNESS = r'''
#include <string.h>
#include "adv_persist.h"
#include "nvs.h"
typedef struct { char key[16]; uint32_t value; } entry_t;
static entry_t entries[32];
static int count, writes, commits, opens, fail;
static adv_model_t model;
const char *esp_err_to_name(esp_err_t e) { (void)e; return "mock error"; }
esp_err_t nvs_open(const char *name, int mode, nvs_handle_t *h) {
    if (strcmp(name, "nabo_ui")) return 1;
    opens += mode == NVS_READWRITE; *h = 1; return 0;
}
void nvs_close(nvs_handle_t h) { (void)h; }
static void put(const char *key, uint32_t value) {
    int i; for (i = 0; i < count && strcmp(entries[i].key, key); i++);
    if (i == count) { strcpy(entries[count++].key, key); }
    entries[i].value = value;
}
esp_err_t nvs_get_u32(nvs_handle_t h, const char *key, uint32_t *value) {
    (void)h;
    for (int i = 0; i < count; i++) if (!strcmp(entries[i].key, key)) {
        *value = entries[i].value; return 0;
    }
    return 1;
}
esp_err_t nvs_get_i32(nvs_handle_t h, const char *key, int32_t *v) {
    uint32_t value; int err = nvs_get_u32(h, key, &value); if (!err) *v = (int32_t)value; return err;
}
esp_err_t nvs_get_u8(nvs_handle_t h, const char *key, uint8_t *v) {
    uint32_t value; int err = nvs_get_u32(h, key, &value); if (!err) *v = (uint8_t)value; return err;
}
esp_err_t nvs_set_u32(nvs_handle_t h, const char *key, uint32_t v) {
    (void)h; writes++; if (fail) return 1; put(key, v); return 0;
}
esp_err_t nvs_set_i32(nvs_handle_t h, const char *key, int32_t v) { return nvs_set_u32(h, key, (uint32_t)v); }
esp_err_t nvs_set_u8(nvs_handle_t h, const char *key, uint8_t v) { return nvs_set_u32(h, key, v); }
esp_err_t nvs_commit(nvs_handle_t h) { (void)h; commits++; return fail; }
void host_reset(void) {
    adv_free(&model); count = writes = commits = opens = fail = 0;
    put("jump_best", 12); put("dive_best", 2400); put("adv_b_post", 6); put("adv_seen", 1);
    put("volume", 60); put("brightness", 80); put("sleep", 300); put("speaker", 1);
    adv_persist_set_test(false); adv_persist_restore(&model, 1);
}
int host_writes(void) { return writes; }
int host_opens(void) { return opens; }
int host_commits(void) { return commits; }
void host_fail(int value) { fail = value; }
uint32_t host_value(const char *key) { uint32_t v = 0; nvs_get_u32(1, key, &v); return v; }
void host_settings(void) {
    model.cfg.settings.volume = 10; model.cfg.settings.brightness = 20;
    model.cfg.settings.sleep_seconds = 60; model.cfg.settings.speaker = false;
    adv_persist_settings(&model.cfg.settings);
}
void host_fake_progress(void) {
    model.best[1] = 999; model.best[2] = 888; model.best[3] = 777; model.seen = 0xffffff;
    adv_persist_u32("adv_seen", model.seen); adv_persist_u32("adv_b_post", model.best[3]);
}
void host_leave_test(void) {
    // Runtime keeps writes suppressed while closing games, restores durable state,
    // then reenables writes. Execute the same production restoration here.
    adv_persist_restore(&model, 2); adv_persist_set_test(false);
}
uint32_t host_model_best(int station) { return model.best[station]; }
uint32_t host_model_seen(void) { return model.seen; }
int host_model_volume(void) { return model.cfg.settings.volume; }
void host_save_restored(void) {
    adv_persist_jump(model.best[1]); adv_persist_settings(&model.cfg.settings);
    adv_persist_u32("adv_seen", model.seen); adv_persist_u32("adv_b_post", model.best[3]);
}
'''


class Persistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        folder = Path(cls.tmp.name)
        (folder / 'nvs.h').write_text(NVS, 'utf-8')
        (folder / 'esp_log.h').write_text('#define ESP_LOGE(...) ((void)0)\n', 'utf-8')
        (folder / 'harness.c').write_text(HARNESS, 'utf-8')
        library = folder / 'adv_persist.dll'
        sources = ['adv_persist.c', 'adv_model.c', 'adv_stations.c', 'adv_demo.c',
                   'collection_model.c', 'nabo_dive_model.c']
        subprocess.run([CC, '-std=gnu11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra',
                        '-Werror', '-Wno-unused-parameter', '-I', str(folder), '-I', str(BOARD),
                        *[str(BOARD / s) for s in sources], str(folder / 'harness.c'), '-lm',
                        '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.adv_persist_set_test.argtypes = [ctypes.c_bool]
        cls.lib.adv_persist_jump.argtypes = [ctypes.c_uint32]
        cls.lib.adv_persist_u32.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
        cls.lib.adv_persist_u8.argtypes = [ctypes.c_char_p, ctypes.c_uint8]
        cls.lib.host_value.argtypes = [ctypes.c_char_p]

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def setUp(self):
        self.lib.host_reset()

    def test_jump_over_repeated_frames_save_once_per_new_best(self):
        for _ in range(1200):
            self.lib.adv_persist_jump(25)
        self.assertEqual(self.lib.host_writes(), 1)
        self.assertEqual(self.lib.host_commits(), 1)
        self.lib.adv_persist_jump(24)
        self.lib.adv_persist_jump(26)
        self.assertEqual(self.lib.host_writes(), 2)
        self.assertEqual(self.lib.host_value(b'jump_best'), 26)

    def test_failed_jump_save_is_retried(self):
        self.lib.host_fail(1)
        self.lib.adv_persist_jump(25)
        self.lib.host_fail(0)
        self.lib.adv_persist_jump(25)
        self.assertEqual(self.lib.host_writes(), 2)
        self.assertEqual(self.lib.host_value(b'jump_best'), 25)

    def test_test_mode_blocks_shell_dive_tutorial_and_settings(self):
        self.lib.adv_persist_set_test(True)
        self.lib.adv_persist_jump(999)
        self.lib.adv_persist_u32(b'dive_best', 999999)
        self.lib.adv_persist_u8(b'dive_dashed', 1)
        self.lib.host_settings()
        self.lib.host_fake_progress()
        self.assertEqual(self.lib.host_writes(), 0)
        self.assertEqual(self.lib.host_opens(), 0)
        self.assertEqual(self.lib.host_commits(), 0)

    def test_leaving_test_restores_state_before_writes_resume(self):
        self.lib.adv_persist_set_test(True)
        self.lib.host_settings()
        self.lib.host_fake_progress()
        self.lib.adv_persist_jump(999)
        self.lib.adv_persist_u32(b'dive_best', 999999)
        self.lib.host_leave_test()
        self.assertEqual(self.lib.host_writes(), 0)
        self.assertEqual(self.lib.host_model_best(1), 12)
        self.assertEqual(self.lib.host_model_best(3), 6)
        self.assertEqual(self.lib.host_model_seen(), 1)
        self.assertEqual(self.lib.host_model_volume(), 60)
        self.lib.host_save_restored()
        self.assertEqual(self.lib.host_value(b'jump_best'), 12)
        self.assertEqual(self.lib.host_value(b'dive_best'), 2400)
        self.assertEqual(self.lib.host_value(b'adv_b_post'), 6)
        self.assertEqual(self.lib.host_value(b'adv_seen'), 1)
        self.assertEqual(self.lib.host_value(b'volume'), 60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
