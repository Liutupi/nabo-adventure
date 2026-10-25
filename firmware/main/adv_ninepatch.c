#include "adv_ninepatch.h"

bool adv_ninepatch_valid(const adv_ninepatch_t *p)
{
    if (!p) return false;
    for (int i = 0; i < 9; i++)
        if (!adv_sprite_frame_valid(p->tile[i], 0)) return false;
    unsigned left = p->tile[0]->width, right = p->tile[2]->width;
    unsigned top = p->tile[0]->height, bottom = p->tile[6]->height;
    for (int i = 0; i < 3; i++) {
        if (p->tile[i * 3]->width != left || p->tile[i * 3 + 2]->width != right ||
            p->tile[i]->height != top || p->tile[6 + i]->height != bottom) return false;
    }
    return true;
}

bool adv_ninepatch_row(const adv_ninepatch_t *p, unsigned width, unsigned height,
                       unsigned y, unsigned x0, unsigned x1, uint16_t *row)
{
    if (!row || !adv_ninepatch_valid(p)) return false;
    unsigned left = p->tile[0]->width, right = p->tile[2]->width;
    unsigned top = p->tile[0]->height, bottom = p->tile[6]->height;
    if (width < left + right || height < top + bottom || y >= height || x0 > x1 || x1 > width)
        return false;
    int band = y < top ? 0 : y >= height - bottom ? 2 : 1;
    unsigned local_y = band == 0 ? y : band == 2 ? y - (height - bottom) : y - top;
    unsigned bounds[4] = {0, left, width - right, width};
    uint8_t indices[ADV_SPRITE_MAX_SIDE];
    for (int col = 0; col < 3; col++) {
        unsigned start = x0 > bounds[col] ? x0 : bounds[col];
        unsigned end = x1 < bounds[col + 1] ? x1 : bounds[col + 1];
        if (start >= end) continue;
        const adv_sprite_t *tile = p->tile[band * 3 + col];
        if (!adv_sprite_row(tile, 0, local_y % tile->height, indices, sizeof(indices))) return false;
        for (unsigned x = start; x < end; x++) {
            uint8_t index = indices[(x - bounds[col]) % tile->width];
            if (index) row[x - x0] = tile->palette[index];
        }
    }
    return true;
}
