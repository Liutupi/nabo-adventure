#include "adv_sprite.h"

// Logical frame -> physical frame, or -1 when the descriptor or map is invalid.
static int physical_frame(const adv_sprite_t *s, unsigned frame)
{
    if (!s || !s->palette || !s->keys || !s->rows || !s->data ||
        !s->width || s->width > ADV_SPRITE_MAX_SIDE ||
        !s->height || s->height > ADV_SPRITE_MAX_SIDE ||
        !s->palette_size || s->palette_size > 64 || frame >= s->frame_count ||
        s->data_size > ADV_SPRITE_MAX_DATA || s->row_count % (s->height + 1u)) return -1;
    uint32_t physical = s->row_count / (s->height + 1u);
    if (!physical || physical > s->frame_count) return -1;
    if (physical == s->frame_count) return (int)frame;
    unsigned mapped = s->keys[physical + frame];
    return mapped < physical ? (int)mapped : -1;
}

static bool key_schedule_valid(const adv_sprite_t *s, unsigned frame)
{
    unsigned key = s->keys[frame];
    if (key > frame || frame - key >= ADV_SPRITE_KEY_INTERVAL || s->keys[key] != key) return false;
    for (unsigned f = key; f <= frame; f++)
        if (s->keys[f] != key) return false;
    return true;
}

bool adv_sprite_frame_valid(const adv_sprite_t *s, unsigned frame)
{
    int p = physical_frame(s, frame);
    return p >= 0 && key_schedule_valid(s, (unsigned)p);
}

bool adv_sprite_row(const adv_sprite_t *s, unsigned frame, unsigned y,
                    uint8_t *out, size_t capacity)
{
    int physical = physical_frame(s, frame);
    if (!out || physical < 0 || !key_schedule_valid(s, (unsigned)physical) || y >= s->height || capacity < s->width)
        return false;
    frame = (unsigned)physical;
    unsigned key = s->keys[frame];
    for (unsigned f = key; f <= frame; f++) {
        uint32_t row = f * (s->height + 1u) + y;
        uint32_t start = s->rows[row], end = s->rows[row + 1];
        if (start > end || end > s->data_size) return false;
        unsigned x = 0;
        uint32_t p = start;
        while (p < end) {
            if (end - p < 2) return false;
            unsigned count = s->data[p++], value = s->data[p++];
            if (count) {
                if (count > s->width - x ||
                    (value >= s->palette_size && value != ADV_SPRITE_INHERIT) ||
                    (value == ADV_SPRITE_INHERIT && f == key)) return false;
                for (unsigned i = 0; i < count; i++, x++)
                    if (value != ADV_SPRITE_INHERIT) out[x] = (uint8_t)value;
            } else {
                unsigned length = value;
                if (!length || length > s->width - x || length > end - p) return false;
                /* Validate the complete literal before writing its first pixel. */
                for (unsigned i = 0; i < length; i++) {
                    unsigned v = s->data[p + i];
                    if ((v >= s->palette_size && v != ADV_SPRITE_INHERIT) ||
                        (v == ADV_SPRITE_INHERIT && f == key)) return false;
                }
                for (unsigned i = 0; i < length; i++, x++)
                    if (s->data[p + i] != ADV_SPRITE_INHERIT) out[x] = s->data[p + i];
                p += length;
            }
        }
        if (x != s->width) return false;
    }
    return true;
}
