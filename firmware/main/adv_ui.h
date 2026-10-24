#pragma once
// Adventure screens drawn straight to the panel through adv_gfx (LVGL is not used).
#include <stdbool.h>
#include <stdint.h>
#include "adv_model.h"
#include "nabo_jump_model.h"

#ifdef __cplusplus
extern "C" {
#endif

bool adv_ui_open(void);
void adv_ui_close(void);
void adv_ui_draw(const adv_model_t *m, uint32_t ms, int battery, int battery_mv);
void adv_ui_invalidate(void);
void adv_ui_capture(void);          // the next frame is also printed as @cap lines
uint32_t adv_ui_bytes(void);        // pixel bytes sent by the last frame
bool adv_ui_overflow(void);         // the last frame ran out of ops or glyphs
// Legacy 跳一跳 page (its own row renderer, from the NABO games collection).
void adv_jump_draw(const nabo_jump_t *game, uint32_t ms, bool full);

#ifdef __cplusplus
}
#endif
