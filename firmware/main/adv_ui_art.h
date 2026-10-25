#pragma once
#include "adv_gfx.h"
#include "generated/adv_assets_catalog.h"

void ui_art(ag_t *g, const char *id, unsigned frame, int x, int y);
void ui_art_anchor(ag_t *g, const char *id, uint32_t elapsed_ms, int x, int y);
void ui_art_frame_anchor(ag_t *g, const char *id, unsigned frame, int x, int y);
void ui_art_tint(ag_t *g, const char *id, int x, int y, uint16_t color);
void ui_art_dim(ag_t *g, const char *id, int x, int y);
void ui_paper(ag_t *g);
void ui_card(ag_t *g, int x, int y, int w, int h, bool selected, bool disabled);
void ui_popup(ag_t *g, int x, int y, int w, int h);
int ui_number(ag_t *g, const char *value, int height, int x, int y, nt_align_t align);
int ui_number_tint(ag_t *g, const char *value, int height, int x, int y, nt_align_t align, uint16_t color);
