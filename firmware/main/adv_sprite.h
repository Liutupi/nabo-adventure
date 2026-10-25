#pragma once
// Immutable flash-backed indexed sprites. Palette index 0 is transparent.
// Each row is (run length 1..255, palette index) pairs. Index 64 inherits pixels
// from the previous frame; zero explicitly clears them. At most 7 delta frames
// follow a keyframe. Rows decode without a framebuffer, allocation or mirroring.
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define ADV_SPRITE_MAX_SIDE 256
#define ADV_SPRITE_KEY_INTERVAL 8
#define ADV_SPRITE_INHERIT 64

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint16_t width, height, frame_count, palette_size;  // palette_size includes transparency
    uint32_t row_count, data_size;
    const uint16_t *palette;   // native RGB565, at most 64 entries
    const uint16_t *keys;      // frame -> nearest preceding keyframe
    const uint32_t *rows;      // frame * (height + 1) + row -> data offset
    const uint8_t *data;
} adv_sprite_t;

// Asset arrays must have their declared sizes and stay immutable/alive while
// referenced by a display list. Invalid metadata/streams return false.
bool adv_sprite_frame_valid(const adv_sprite_t *sprite, unsigned frame);
bool adv_sprite_row(const adv_sprite_t *sprite, unsigned frame, unsigned y,
                    uint8_t *out, size_t capacity);

#ifdef __cplusplus
}
#endif
