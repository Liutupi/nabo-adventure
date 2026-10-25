#include "adv_boot_motion.h"
#include "adv_boot_presentation.h"

bool adv_boot_motion_enabled(void) { return ADV_BOOT_PRESENTATION_SELECTED != 0; }
uint32_t adv_boot_motion_duration(void) { return adv_boot_presentation_meta.duration_ms; }
const char *adv_boot_motion_asset_id(void) { return ADV_BOOT_PRESENTATION_ASSET_ID; }
uint16_t adv_boot_motion_event_count(void) { return adv_boot_presentation_meta.poses; }
uint16_t adv_boot_motion_frame_count(void) { return ADV_BOOT_PRESENTATION_FRAME_COUNT; }
uint32_t adv_boot_motion_voice_start_ms(void) { return adv_boot_presentation_meta.voice_start_ms; }
uint32_t adv_boot_motion_voice_end_us(void) { return adv_boot_presentation_meta.voice_end_us; }

uint8_t adv_boot_motion_frame(uint32_t elapsed_ms)
{
    uint16_t count = adv_boot_presentation_meta.poses;
    if (!ADV_BOOT_PRESENTATION_SELECTED || !count) return 0;
    // Upper-bound search over uint16 timestamps. Keeping elapsed_ms uint32
    // prevents long cover holds from wrapping back into an earlier gesture.
    uint16_t lo = 0, hi = count;
    while (lo < hi) {
        uint16_t mid = (uint16_t)(lo + (hi - lo) / 2);
        if (adv_boot_poses[mid].at_ms <= elapsed_ms) lo = (uint16_t)(mid + 1);
        else hi = mid;
    }
    return adv_boot_poses[lo ? lo - 1 : 0].frame;
}
