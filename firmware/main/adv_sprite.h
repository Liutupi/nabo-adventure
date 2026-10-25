#pragma once
// Immutable flash-backed indexed sprites. Palette index 0 is transparent.
// adv-row-rle-v3 (uint16 offsets) also reads v1 run-only and v2 literal rows.
// A nonzero count is a legacy (count 1..255, index) run. A zero count escapes
// (0, length 1..255, literal indices...). Row byte lengths may be odd.
// Index 64 inherits the previous frame; index 0 explicitly clears a pixel.
// Keyframes forbid inheritance. At most 7 delta frames follow a keyframe.
// Rows decode without a framebuffer, allocation or mirroring.
// adv-row-rle-v3 stores row offsets as uint16, so one sprite piece holds at most
// 65535 data bytes; the packer rejects anything larger instead of truncating.
// v4: when row_count/(height+1) physical frames < frame_count, keys[] holds the
// key schedule for the physical frames followed by a logical->physical frame map,
// so an identical repeated frame is stored once.
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define ADV_SPRITE_MAX_SIDE 256
#define ADV_SPRITE_KEY_INTERVAL 8
#define ADV_SPRITE_INHERIT 64
#define ADV_SPRITE_MAX_DATA 65535u

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint16_t width, height, frame_count, palette_size;  // palette_size includes transparency
    uint32_t row_count, data_size;
    const uint16_t *palette;   // native RGB565, at most 64 entries
    const uint16_t *keys;      // physical frame -> nearest preceding keyframe [, logical -> physical]
    const uint16_t *rows;      // frame * (height + 1) + row -> data offset
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
