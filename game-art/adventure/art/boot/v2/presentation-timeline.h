#pragma once
#include <stdint.h>
typedef struct {uint16_t at_ms; uint8_t frame; uint8_t reserved;} boot_v2_pose_t;
_Static_assert(sizeof(boot_v2_pose_t)==4,"boot schedule layout");
static const boot_v2_pose_t boot_v2_schedule[] = {
 {0,0,0},
 {167,1,0},
 {333,2,0},
 {583,3,0},
 {750,4,0},
 {833,5,0},
 {917,6,0},
 {1000,7,0},
 {1167,8,0},
 {1250,9,0},
 {1333,10,0},
 {1417,11,0},
 {1500,12,0},
 {1583,13,0},
 {1750,14,0},
 {1833,15,0},
 {1917,16,0},
 {2000,17,0},
 {2167,18,0},
 {2333,19,0},
 {2417,20,0},
 {2500,21,0},
 {2750,22,0},
 {2917,23,0},
 {3000,24,0},
 {3083,25,0},
 {3250,26,0},
 {3333,27,0},
 {3417,28,0},
 {3583,29,0},
 {3750,30,0},
 {3917,31,0},
 {4083,0,0},
 {4250,0,0},
};
typedef struct {uint32_t duration_ms,voice_start_ms,voice_end_us;uint16_t poses,fps;} boot_v2_meta_t;
_Static_assert(sizeof(boot_v2_meta_t)==16,"boot metadata layout");
static const boot_v2_meta_t boot_v2_meta={4417,1400,4090625,34,12};
