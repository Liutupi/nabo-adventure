#pragma once
#include <string.h>
#include "adv_climb.h"
// Same order as adv_climb.js view(): fields, 32 row bytes, 4 rocks, hand y, body side.
#define CLIMB_VALUES (30 + ADV_CLIMB_RING + ADV_CLIMB_ROCKS * 3 + 2)
static inline void climb_values(const adv_climb_t *g, int64_t *out)
{
    _Static_assert(sizeof(*g) == 200, "CLIMB snapshot ABI");
    int32_t raw[30];memcpy(raw, g, sizeof(raw));
    int n = 0;
    for (int i = 0; i < 30; i++) out[n++] = i < 3 ? (int64_t)(uint32_t)raw[i] : raw[i];
    for (int i = 0; i < ADV_CLIMB_RING; i++) out[n++] = g->grid[i];
    for (int i = 0; i < ADV_CLIMB_ROCKS; i++) { out[n++] = g->rocks[i].on; out[n++] = g->rocks[i].side; out[n++] = g->rocks[i].y; }
    out[n++] = adv_climb_hand_y(g); out[n++] = adv_climb_body_side(g);
}
