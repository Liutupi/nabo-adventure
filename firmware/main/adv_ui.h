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
uint32_t adv_ui_staging_bytes(void); // V2 landscape buffers, released on leaving
bool adv_ui_overflow(void);         // the last frame ran out of ops or glyphs
int adv_ui_width(void);
int adv_ui_height(void);
// Legacy 跳一跳 page (its own row renderer, from the NABO games collection).
void adv_jump_draw(const nabo_jump_t *game, uint32_t ms, bool full);
void adv_jump_invalidate(void);
// Versus overlay on the jump page: opponent line at the top right, game-over card text and footer.
// Pass opp=NULL to return to the normal medal/best overlay.
// footer=NULL keeps the default play hint; a footer is drawn in red (the rule that matters right now).
void adv_jump_versus(const char *opp, const char *opp_state, const char *card_title, const char *card_line,
                     const char *footer);
// Versus room pages (lobby, invitations, countdown, result).
// Versus race on a landscape session game: a small opponent pill and, when one side has finished,
// a red banner with the pass-to-win rule. NULL/empty clears.
void adv_ui_versus_overlay(const char *pill, const char *banner);
struct adv_vs_t;
void adv_ui_draw_versus(const struct adv_vs_t *vs, uint32_t ms);

#ifdef __cplusplus
}
#endif
