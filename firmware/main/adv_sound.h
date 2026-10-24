#pragma once
// Short synthesized cues for the adventure shell (16 kHz mono, triangle wave, no samples).
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const uint16_t (*notes)[2];   // {Hz, ms}; 0 Hz is a rest; {0, 0} ends
    int note, left, length;       // samples left in the current note and its length
    uint32_t phase, step;         // Q16 phase accumulator
} adv_sound_t;

void adv_sound_start(adv_sound_t *s, int cue);   // adv_cue_t; replaces whatever is playing
void adv_sound_fill(adv_sound_t *s, int16_t *pcm, size_t frames);

#ifdef __cplusplus
}
#endif
