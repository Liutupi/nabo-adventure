"""Execute the production I2S shutdown helper with recording public-driver stubs."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'firmware/components/bsp/src/bsp_audio.c'


def production_function(source, name):
    start = source.index('static esp_err_t ' + name + '(')
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


PREAMBLE = r'''
#include <stdbool.h>
#include <stddef.h>
typedef int esp_err_t;
typedef struct channel { bool enabled; int query_error, disable_error, queries, stops; } channel_t;
typedef channel_t *i2s_chan_handle_t;
typedef struct { bool is_enabled; } i2s_chan_info_t;
#define ESP_OK 0
#define ESP_FAIL 1
#define ESP_ERR_INVALID_STATE 2
#define TAG "bsp_audio"
static channel_t channels[2];
static i2s_chan_handle_t s_tx, s_rx;
static int errors;
#define ESP_LOGE(...) (++errors)
static const char *esp_err_to_name(esp_err_t e) { (void)e; return "driver error"; }
static esp_err_t i2s_channel_get_info(i2s_chan_handle_t ch, i2s_chan_info_t *info) {
    ch->queries++;
    if (ch->query_error) return ch->query_error;
    info->is_enabled = ch->enabled; return ESP_OK;
}
static esp_err_t i2s_channel_disable(i2s_chan_handle_t ch) {
    ch->stops++;
    if (ch->disable_error) return ch->disable_error;
    if (!ch->enabled) { errors++; return ESP_ERR_INVALID_STATE; }
    ch->enabled = false; return ESP_OK;
}
'''

HARNESS = r'''
void host_reset(int tx, int rx) {
    channels[0] = (channel_t){.enabled = tx > 0};
    channels[1] = (channel_t){.enabled = rx > 0};
    s_tx = tx < 0 ? NULL : &channels[0]; s_rx = rx < 0 ? NULL : &channels[1]; errors = 0;
}
void host_query_error(int channel, int error) { channels[channel].query_error = error; }
void host_disable_error(int channel, int error) { channels[channel].disable_error = error; }
int host_shutdown(void) { return audio_disable_i2s_channels(); }
int host_stops(int channel) { return channels[channel].stops; }
int host_queries(int channel) { return channels[channel].queries; }
int host_enabled(int channel) { return channels[channel].enabled; }
int host_errors(void) { return errors; }
'''


class AudioSleep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        folder = Path(cls.tmp.name)
        body = production_function(SOURCE.read_text('utf-8'), 'audio_disable_i2s_channels')
        (folder / 'shutdown.c').write_text(PREAMBLE + body + HARNESS, 'utf-8')
        library = folder / 'audio_sleep.dll'
        subprocess.run([CC, '-std=c11', '-O2', '-shared', SHARED_EXPORT, '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-function', str(folder / 'shutdown.c'), '-o', str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))

    @classmethod
    def tearDownClass(cls):
        unload_library(cls.lib._handle)
        cls.tmp.cleanup()

    def test_sleep_then_prepare_are_idempotent_without_driver_errors(self):
        self.lib.host_reset(1, 1)
        self.assertEqual(self.lib.host_shutdown(), 0)
        self.assertEqual(self.lib.host_shutdown(), 0)
        self.assertEqual([self.lib.host_stops(i) for i in (0, 1)], [1, 1])
        self.assertEqual([self.lib.host_enabled(i) for i in (0, 1)], [0, 0])
        self.assertEqual(self.lib.host_errors(), 0)

    def test_channels_already_stopped_by_codec_close_are_not_disabled_again(self):
        self.lib.host_reset(0, 0)
        self.assertEqual(self.lib.host_shutdown(), 0)
        self.assertEqual([self.lib.host_stops(i) for i in (0, 1)], [0, 0])
        self.assertEqual([self.lib.host_queries(i) for i in (0, 1)], [1, 1])
        self.assertEqual(self.lib.host_errors(), 0)

    def test_only_remaining_enabled_channel_is_stopped(self):
        self.lib.host_reset(0, 1)
        self.assertEqual(self.lib.host_shutdown(), 0)
        self.assertEqual([self.lib.host_stops(i) for i in (0, 1)], [0, 1])

    def test_query_failure_is_propagated_and_does_not_skip_other_channel(self):
        self.lib.host_reset(1, 1)
        self.lib.host_query_error(0, 9)
        self.assertEqual(self.lib.host_shutdown(), 9)
        self.assertEqual([self.lib.host_stops(i) for i in (0, 1)], [0, 1])
        self.assertEqual(self.lib.host_enabled(0), 1)
        self.assertEqual(self.lib.host_errors(), 1)

    def test_real_disable_failure_and_invalid_state_are_never_swallowed(self):
        for error in (1, 2, 7):
            with self.subTest(error=error):
                self.lib.host_reset(1, 1)
                self.lib.host_disable_error(0, error)
                self.assertEqual(self.lib.host_shutdown(), error)
                self.assertEqual(self.lib.host_enabled(0), 1)
                self.assertEqual(self.lib.host_enabled(1), 0)
                self.assertEqual(self.lib.host_errors(), 1)

    def test_partial_failure_can_retry_without_repeating_successful_stop(self):
        self.lib.host_reset(1, 1)
        self.lib.host_disable_error(0, 7)
        self.assertEqual(self.lib.host_shutdown(), 7)
        self.lib.host_disable_error(0, 0)
        self.assertEqual(self.lib.host_shutdown(), 0)
        self.assertEqual([self.lib.host_stops(i) for i in (0, 1)], [2, 1])

    def test_missing_channels_need_no_driver_calls(self):
        self.lib.host_reset(-1, -1)
        self.assertEqual(self.lib.host_shutdown(), 0)
        self.assertEqual([self.lib.host_queries(i) for i in (0, 1)], [0, 0])
        self.assertEqual([self.lib.host_stops(i) for i in (0, 1)], [0, 0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
