#pragma once
// Shared palette, fonts and helpers of the adventure screens (see game-art/adventure/UI_DESIGN.md).
#include "adv_gfx.h"
#include "adv_model.h"
#include "adv_ui_art.h"

LV_FONT_DECLARE(collection_font_12)
LV_FONT_DECLARE(collection_font_16)
LV_FONT_DECLARE(collection_font_18)
LV_FONT_DECLARE(nabo_poster_font_28)
LV_FONT_DECLARE(nabo_poster_font_48)
LV_FONT_DECLARE(nabo_mono_font_12)

#define UI_INK ADV_ASSETS_UI_INK
#define UI_PAPER ADV_ASSETS_UI_PAPER
#define UI_GOLD ADV_ASSETS_UI_GOLD
#define UI_WHITE ADV_ASSETS_UI_WHITE
#define UI_DIM ADV_ASSETS_UI_MUTED
#define UI_LOCK ADV_ASSETS_UI_MUTED
#define UI_RED ADV_ASSETS_UI_ACCENT
#define UI_BRONZE ADV_ASSETS_UI_BRONZE
#define UI_SILVER ADV_ASSETS_UI_SILVER
#define UI_GOLDSTAMP ADV_ASSETS_UI_GOLD

enum { UI_SCENE_COVER = 1, UI_SCENE_MAP, UI_SCENE_KIOSK, UI_SCENE_PASSPORT, UI_SCENE_SETTINGS, UI_SCENE_STATUS,
       UI_SCENE_STAMP, UI_SCENE_TITLE, UI_SCENE_PLAY, UI_SCENE_RESULT };

static inline uint16_t ui_tier_color(int tier) { return tier == 0 ? UI_BRONZE : tier == 1 ? UI_SILVER : UI_GOLDSTAMP; }

// Header bar (0..32) and footer bar (288..320) shared by every shell page.
void ui_header(ag_t *g, const char *title, const char *right);
void ui_footer(ag_t *g, const char *hint);
// Three stamp dots of a station at (x, cy), radius r; earned ones filled with their tier colour.
void ui_stamps(ag_t *g, const adv_model_t *m, int station, int x, int cy, int r, int gap);
int ui_stamp_count(const adv_model_t *m);
uint32_t ui_millis(void);

void ui_draw_map(ag_t *g, const adv_model_t *m);
void ui_map_reset(void);
void ui_draw_passport(ag_t *g, const adv_model_t *m);
void ui_draw_stamp(ag_t *g, const adv_model_t *m);
void ui_draw_session(ag_t *g, const adv_model_t *m);
void ui_draw_post_session(ag_t *g,const adv_model_t *m);
