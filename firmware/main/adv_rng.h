#pragma once
// mulberry32, identical to rand() in game-art/adventure/prototype/adv_core.js.
#include <stdint.h>

static inline uint32_t adv_rand(uint32_t *state)
{
    uint32_t t = (*state += 0x6D2B79F5u);
    t = (t ^ (t >> 15)) * (t | 1u);
    t ^= t + (t ^ (t >> 7)) * (t | 61u);
    return t ^ (t >> 14);
}
