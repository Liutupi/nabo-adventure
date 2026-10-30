#pragma once
#include "adv_ui_internal.h"
// The approved G3 320x240 layout shared by all six landscape games.
void ui_v2_title(ag_t *g,const adv_model_t *m);
void ui_v2_ready(ag_t *g,const adv_model_t *m);
void ui_v2_pause(ag_t *g);
void ui_v2_result(ag_t *g,const adv_model_t *m,uint32_t elapsed_ms,const char *cause,const char *line1,const char *line2);
void ui_v2_text(ag_t *g,const char *s,int x,int cy,int size,nt_align_t align,uint16_t color);

void ui_v2_hud(ag_t *g,const char *label,int res,uint32_t score,int combo,int mult);
