#include "adv_sound.h"
#include <string.h>
#include "adv_model.h"

#define RATE 16000
#define PEAK 5000   // well under full scale: the speaker needs headroom even at 100% volume

static const uint16_t MOVE[][2] = {{1200, 25}, {0, 0}};
static const uint16_t ENTER[][2] = {{660, 50}, {990, 70}, {0, 0}};
static const uint16_t DENY[][2] = {{220, 70}, {0, 30}, {196, 90}, {0, 0}};
static const uint16_t STAMP[][2] = {{523, 80}, {659, 80}, {784, 80}, {1047, 220}, {0, 0}};
static const uint16_t BACK[][2] = {{880, 45}, {550, 70}, {0, 0}};
static const uint16_t HIT[][2] = {{1320, 40}, {1760, 50}, {0, 0}};
static const uint16_t MISS[][2] = {{180, 120}, {0, 0}};
static const uint16_t OVER[][2] = {{440, 110}, {330, 110}, {220, 220}, {0, 0}};
static const uint16_t GO[][2] = {{880, 60}, {1175, 110}, {0, 0}};

static const uint16_t (*const CUES[])[2] = {NULL, MOVE, ENTER, DENY, STAMP, BACK, HIT, MISS, OVER, GO};

static void begin_note(adv_sound_t *s)
{
    const uint16_t *n = s->notes[s->note];
    s->length = s->left = n[1] * RATE / 1000;
    s->step = (uint32_t)n[0] * 65536u / RATE * 65536u;
    if (!s->length) s->notes = NULL;
}

void adv_sound_start(adv_sound_t *s, int cue)
{
    memset(s, 0, sizeof(*s));
    if (cue <= 0 || cue >= (int)(sizeof(CUES) / sizeof(CUES[0]))) return;
    s->notes = CUES[cue];
    begin_note(s);
}

void adv_sound_fill(adv_sound_t *s, int16_t *pcm, size_t frames)
{
    for (size_t i = 0; i < frames; i++) {
        if (!s->notes) { pcm[i] = 0; continue; }
        int v = 0;
        if (s->step) {
            uint32_t p = s->phase >> 16;                        // 0..65535 over one period
            int tri = p < 32768 ? (int)p * 2 - 32768 : 98303 - (int)p * 2;
            int env = s->left * 256 / s->length;                // linear decay per note
            if (s->length - s->left < 32) env = env * (s->length - s->left) / 32;   // no click at the start
            v = tri / 8 * PEAK / 4096 * env / 256;
            s->phase += s->step;
        }
        pcm[i] = (int16_t)v;
        if (--s->left <= 0) { s->note++; begin_note(s); }
    }
}
