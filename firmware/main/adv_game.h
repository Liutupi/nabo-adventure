#pragma once
// Contract between the adventure shell and a game. The shell owns the title, countdown, pause,
// result, stamps, resource bar and saving; a game only runs the "playing" part. step() runs at a
// fixed 60 Hz and must be deterministic for a given seed and input sequence (golden traces).
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ADV_RESOURCE_MAX 1000

// Button edges since the previous step, plus what is held now.
typedef struct {
    uint8_t ok_down, ok_up, up_down, down_down, down_up;
    uint8_t ok_held, down_held;
} adv_input_t;

typedef struct {
    uint32_t score;     // the game's main result, larger is better
    int resource;       // 0..ADV_RESOURCE_MAX, drawn by the shell
    bool over;          // the resource ran out; the shell plays END, then RESULT
    uint8_t cue;        // adv_cue_t raised by the last step, 0 for none
} adv_status_t;

typedef struct {
    const char *id;             // station id, also the NVS best key suffix
    size_t state_size;          // the shell allocates this much on entering the station
    void (*start)(void *state, uint32_t seed);
    void (*step)(void *state, const adv_input_t *in);
    adv_status_t (*status)(const void *state);
} adv_game_t;

#ifdef __cplusplus
}
#endif
