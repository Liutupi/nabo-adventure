#pragma once
#include <string.h>
#include "adv_night.h"
#define NIGHT_VALUES 80
static inline void night_values(const adv_night_t *g,int64_t *out)
{
    _Static_assert(sizeof(*g)==78*4,"NIGHT snapshot ABI");
    int32_t raw[78];memcpy(raw,g,sizeof(raw));
    for(int i=0;i<78;i++)out[i]=i<3?(int64_t)(uint32_t)raw[i]:raw[i];
    out[78]=adv_night_target(g);out[79]=adv_night_interval(g);
}
