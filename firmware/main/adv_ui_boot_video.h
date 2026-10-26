#pragma once
#include "adv_gfx.h"
bool ui_boot_video_draw(ag_t *g,uint32_t elapsed,bool initial);
void ui_boot_video_close(void);
typedef struct { uint32_t frames,skipped,last_frame,elapsed_ms; } ui_boot_video_stats_t;
ui_boot_video_stats_t ui_boot_video_stats(void);
void ui_boot_video_did_flush(void);
bool ui_boot_video_pending(uint32_t elapsed);
