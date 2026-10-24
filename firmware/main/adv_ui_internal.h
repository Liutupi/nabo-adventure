#pragma once
// Shared palette, fonts and helpers of the adventure screens (see game-art/adventure/UI_DESIGN.md).
#include "adv_gfx.h"
#include "adv_model.h"

LV_FONT_DECLARE(collection_font_12)
LV_FONT_DECLARE(collection_font_16)
LV_FONT_DECLARE(collection_font_18)
LV_FONT_DECLARE(nabo_poster_font_28)
LV_FONT_DECLARE(nabo_poster_font_48)
LV_FONT_DECLARE(nabo_mono_font_12)

#define UI_INK 0x1927      // night navy: text on light, panels
#define UI_PAPER 0xef3b    // warm paper: text on dark, cards
#define UI_GOLD 0xfd70
#define UI_WHITE 0xffff
#define UI_DIM 0x7bef
#define UI_LOCK 0x7bd1
#define UI_RED 0xe28a
#define UI_BRONZE 0xcbe6
#define UI_SILVER 0xc639
#define UI_GOLDSTAMP 0xfe69

enum { UI_SCENE_COVER = 1, UI_SCENE_MAP, UI_SCENE_KIOSK, UI_SCENE_PASSPORT, UI_SCENE_SETTINGS, UI_SCENE_STATUS,
       UI_SCENE_STAMP, UI_SCENE_TITLE, UI_SCENE_PLAY, UI_SCENE_RESULT };

static inline uint16_t ui_tier_color(int tier) { return tier == 0 ? UI_BRONZE : tier == 1 ? UI_SILVER : UI_GOLDSTAMP; }

// Header bar (0..32) and footer bar (288..320) shared by every shell page.
void ui_header(ag_t *g, const char *title, const char *right);
void ui_footer(ag_t *g, const char *hint);
// Three stamp dots of a station at (x, cy), radius r; earned ones filled with their tier colour.
void ui_stamps(ag_t *g, const adv_model_t *m, int station, int x, int cy, int r, int gap);
int ui_stamp_count(const adv_model_t *m);

void ui_draw_map(ag_t *g, const adv_model_t *m);
void ui_draw_passport(ag_t *g, const adv_model_t *m);
void ui_draw_stamp(ag_t *g, const adv_model_t *m);
void ui_draw_session(ag_t *g, const adv_model_t *m);
