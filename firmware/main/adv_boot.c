#include "adv_boot.h"
#include <string.h>

static uint16_t u16(const uint8_t *p) { return (uint16_t)p[0] | (uint16_t)p[1] << 8; }
static uint32_t u32(const uint8_t *p)
{
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

void adv_boot_stop(adv_boot_t *boot) { if (boot) memset(boot, 0, sizeof(*boot)); }

bool adv_boot_open(adv_boot_t *boot, const void *wav, size_t bytes, uint32_t visual_start_ms)
{
    if (!boot) return false;
    adv_boot_stop(boot);
    if (!wav || bytes < 12) return false;
    const uint8_t *p = wav;
    if (memcmp(p, "RIFF", 4) || memcmp(p + 8, "WAVE", 4) || u32(p + 4) != bytes - 8) return false;
    bool have_fmt = false, have_data = false;
    size_t data_offset = 0, sample_count = 0;
    for (size_t offset = 12; offset < bytes;) {
        if (bytes - offset < 8) return false;
        size_t length = u32(p + offset + 4), payload = offset + 8;
        if (length > bytes - payload) return false;
        size_t next = payload + length;
        if (length & 1u) {
            if (next == bytes) return false;  // mandatory RIFF word-alignment pad
            next++;
        }
        if (!memcmp(p + offset, "fmt ", 4)) {
            if (have_fmt || length < 16) return false;
            const uint8_t *fmt = p + payload;
            if (u16(fmt) != 1 || u16(fmt + 2) != 1 || u32(fmt + 4) != 16000 ||
                u32(fmt + 8) != 32000 || u16(fmt + 12) != 2 || u16(fmt + 14) != 16) return false;
            // PCM fmt extensions carry a cbSize field; it must describe all extra bytes.
            if (length != 16 && (length < 18 || u16(fmt + 16) != length - 18)) return false;
            have_fmt = true;
        } else if (!memcmp(p + offset, "data", 4)) {
            if (have_data || !length || (length & 1u)) return false;
            data_offset = payload;
            sample_count = length / 2;
            have_data = true;
        }
        offset = next;
    }
    if (!have_fmt || !have_data) return false;
    *boot = (adv_boot_t){.wav = p, .data_offset = data_offset, .sample_count = sample_count,
                         .start_ms = visual_start_ms, .active = true};
    return true;
}

uint32_t adv_boot_elapsed(const adv_boot_t *boot, uint32_t now_ms)
{
    return boot && boot->wav ? now_ms - boot->start_ms : 0;
}

void adv_boot_tick(adv_boot_t *boot, uint32_t now_ms)
{
    if (boot && boot->active && !boot->started && adv_boot_elapsed(boot, now_ms) >= ADV_BOOT_DELAY_MS)
        boot->started = true;
}

void adv_boot_fill(adv_boot_t *boot, int16_t *pcm, size_t frames)
{
    if (!boot || !pcm || !boot->active || !boot->started) return;
    for (size_t i = 0; i < frames && boot->position < boot->sample_count; i++) {
        const uint8_t *p = boot->wav + boot->data_offset + boot->position * 2;
        int32_t voice = u16(p);
        if (voice >= 32768) voice -= 65536;
        int32_t mixed = voice + (int32_t)pcm[i] / 4;
        pcm[i] = (int16_t)(mixed > 32767 ? 32767 : mixed < -32768 ? -32768 : mixed);
        boot->position++;
    }
    if (boot->position == boot->sample_count) boot->active = false;
}
