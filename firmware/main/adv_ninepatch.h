#pragma once
// Immutable row-major 3x3 tiles. Corners stay unscaled; edges/center repeat.
#include "adv_sprite.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct { const adv_sprite_t *tile[9]; } adv_ninepatch_t;
bool adv_ninepatch_valid(const adv_ninepatch_t *patch);
bool adv_ninepatch_row(const adv_ninepatch_t *patch, unsigned width, unsigned height,
                       unsigned y, unsigned x0, unsigned x1, uint16_t *row);
#ifdef __cplusplus
}
#endif
