#pragma once
#include <string.h>
#include "adv_night.h"
#define NIGHT_VALUES 73
static inline void night_values(const adv_night_t *g,int64_t *out)
{
    _Static_assert(sizeof(*g)==71*4,"NIGHT snapshot ABI");
    int32_t raw[71];memcpy(raw,g,sizeof(raw));
    for(int i=0;i<71;i++)out[i]=i<3?(int64_t)(uint32_t)raw[i]:raw[i];
    out[71]=adv_night_target(g);out[72]=adv_night_speed(g);
}
