#pragma once
// Immutable one-shot pose selection. elapsed_ms is time since the cover became
// visible, shared with adv_boot_elapsed; the final neutral pose holds forever.
// No allocation, RTOS, clock reads or mutable playback state. The shell must stop
// narration when leaving the cover; this visual lookup cannot start audio.
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

bool adv_boot_motion_enabled(void);
uint8_t adv_boot_motion_frame(uint32_t elapsed_ms);
uint32_t adv_boot_motion_duration(void);
const char *adv_boot_motion_asset_id(void);
uint16_t adv_boot_motion_event_count(void);
uint16_t adv_boot_motion_frame_count(void);
uint32_t adv_boot_motion_voice_start_ms(void);
uint32_t adv_boot_motion_voice_end_us(void);

#ifdef __cplusplus
}
#endif
