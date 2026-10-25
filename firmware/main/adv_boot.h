#pragma once
// One-shot cover narration read directly from immutable Flash WAV bytes.
// Caller must hold the SAME audio_lock around open/tick/fill/stop and context
// reads. No internal synchronization, heap, RTOS, display or IRAM code is used.
// Keep WAV storage alive and immutable until stop (normally linker-embedded).
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ADV_BOOT_DELAY_MS 1400u

typedef struct {
    const uint8_t *wav;
    size_t data_offset, sample_count, position;
    uint32_t start_ms;      // when the visual cover sequence became visible
    bool started;          // stays true after natural completion; prevents replay
    bool active;           // pending or playing; false after completion/cancel
} adv_boot_t;

// Reinitializes even on failure. Requires one fmt + one nonempty data chunk,
// PCM1/mono/16000 Hz/16 bit, correct byte rate/alignment, complete RIFF bounds
// and padding. Unknown complete chunks are allowed. Nothing plays until tick.
bool adv_boot_open(adv_boot_t *boot, const void *wav, size_t bytes, uint32_t visual_start_ms);
void adv_boot_tick(adv_boot_t *boot, uint32_t now_ms);
// pcm already contains cues. During voice samples only, cue/4 + original voice
// is clamped to int16. Beyond the last voice sample the existing cue is untouched.
// Only fill advances position. Calling fill before the delay leaves pcm untouched.
void adv_boot_fill(adv_boot_t *boot, int16_t *pcm, size_t frames);
// Leaving the cover must call stop under audio_lock, cancelling pending/playing
// audio immediately. Later ticks/fills cannot restart it; another open can.
void adv_boot_stop(adv_boot_t *boot);
// Unsigned monotonic millisecond subtraction supports one uint32 clock wrap.
// Available after natural audio completion for cover animation; 0 after stop.
uint32_t adv_boot_elapsed(const adv_boot_t *boot, uint32_t now_ms);

#ifdef __cplusplus
}
#endif
