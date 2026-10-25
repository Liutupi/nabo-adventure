// Optional ASan/UBSan check. Run command is in docs/SPRITES.md. No device I/O.
#include "adv_sprite.h"
#include <assert.h>
#include <string.h>

static uint32_t rng = 9;
static uint32_t next(void) { rng = rng * 1664525u + 1013904223u; return rng; }

int main(void)
{
    const uint16_t palette[] = {0, 0xffff};
    const uint16_t keys[] = {0, 0};
    uint32_t rows[4];
    uint8_t data[512], out[258];
    adv_sprite_t s = {256, 1, 2, 2, 4, sizeof(data), palette, keys, rows, data};
    // Known keyframe + sparse delta, including erasing and inheriting opaque pixels.
    const uint8_t good[] = {255, 1, 1, 1, 1, 0, 255, 64};
    memcpy(data, good, sizeof(good));
    rows[0] = 0; rows[1] = 4; rows[2] = 4; rows[3] = 8;
    assert(adv_sprite_row(&s, 1, 0, out + 1, 256));
    assert(out[1] == 0 && out[256] == 1);
    for (unsigned round = 0; round < 50000; round++) {
        for (unsigned i = 0; i < sizeof(data); i++) data[i] = (uint8_t)(next() >> 16);
        for (unsigned i = 0; i < 4; i++) rows[i] = next() % 530;
        if (round & 1) { rows[0] = 0; rows[1] = rows[2] = 256; rows[3] = 512; }
        memset(out, 173, sizeof(out));
        (void)adv_sprite_row(&s, round & 1, 0, out + 1, 256);
        assert(out[0] == 173 && out[257] == 173);
    }
    return 0;
}
