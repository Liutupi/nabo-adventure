#include "adv_ui_animation.h"
static bool s_initial;
static uint32_t s_start_ms;
void adv_ui_boot_begin(uint32_t now_ms) { s_start_ms = now_ms; s_initial = true; }
void adv_ui_boot_end(void) { s_initial = false; }
bool adv_ui_boot_initial(void) { return s_initial; }
uint32_t adv_ui_boot_elapsed(uint32_t now_ms) { return now_ms - s_start_ms; }
