#pragma once
#include <stdbool.h>
#include <stdint.h>
// UI task owns this visual clock; audio has its separate locked adv_boot_t.
void adv_ui_boot_begin(uint32_t now_ms);
void adv_ui_boot_end(void);
bool adv_ui_boot_initial(void);
uint32_t adv_ui_boot_elapsed(uint32_t now_ms);
