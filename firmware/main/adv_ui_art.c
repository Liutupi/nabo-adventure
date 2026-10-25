// Small flash catalog adapter. Coordinates refer to the declared native canvases.
#include "adv_ui_art.h"

static void record(ag_t *g, const adv_asset_record_t *a, unsigned frame, int x, int y, bool tint, uint16_t color)
{
    if (!a) return;
    for (unsigned i = 0; i < a->piece_count; i++) {
        const adv_asset_piece_t *p = &a->pieces[i];
        unsigned count = p->sprite->frame_count;
        unsigned f = frame < count ? frame : count - 1;
        if (tint) ag_sprite_tint(g, p->sprite, f, x + p->x, y + p->y, color);
        else ag_sprite(g, p->sprite, f, x + p->x, y + p->y);
    }
}

void ui_art(ag_t *g, const char *id, unsigned frame, int x, int y)
{
    record(g, adv_assets_find(id), frame, x, y, false, 0);
}

void ui_art_anchor(ag_t *g, const char *id, uint32_t elapsed_ms, int x, int y)
{
    const adv_asset_record_t *a = adv_assets_find(id);
    if (!a || !a->piece_count) return;
    unsigned count = a->pieces[0].sprite->frame_count;
    unsigned frame = (uint32_t)((uint64_t)elapsed_ms * a->fps / 1000);
    if (a->loop) frame %= count;
    record(g, a, frame, x - a->anchor_x, y - a->anchor_y, false, 0);
}

void ui_art_tint(ag_t *g, const char *id, int x, int y, uint16_t color)
{
    record(g, adv_assets_find(id), 0, x, y, true, color);
}

void ui_art_dim(ag_t *g, const char *id, int x, int y)
{
    const adv_asset_record_t *a = adv_assets_find(id);
    if (!a) return;
    for (unsigned i = 0; i < a->piece_count; i++) {
        const adv_asset_piece_t *p = &a->pieces[i];
        ag_sprite_dim(g, p->sprite, 0, x + p->x, y + p->y);
    }
}

void ui_paper(ag_t *g)
{
    ag_band(g, 0, 320, ADV_ASSETS_UI_BG, ADV_ASSETS_UI_BG);
    ag_rect(g, 5, 32, 1, 258, 0, ADV_ASSETS_UI_LINE, 255, 0, 0);
    ag_rect(g, 234, 32, 1, 258, 0, ADV_ASSETS_UI_LINE, 255, 0, 0);
}

void ui_card(ag_t *g, int x, int y, int w, int h, bool selected, bool disabled)
{
    const adv_ninepatch_t *p = disabled ? &adv_assets_patch_menu_disabled :
        selected ? &adv_assets_patch_menu_selected : &adv_assets_patch_menu_normal;
    ag_ninepatch(g, p, x, y, w, h);
}

void ui_popup(ag_t *g, int x, int y, int w, int h)
{
    ag_ninepatch(g, &adv_assets_patch_popup_normal, x, y, w, h);
}

int ui_number(ag_t *g, const char *value, int height, int x, int y, nt_align_t align)
{
    const adv_asset_digit_t *digits = height == 36 ? adv_assets_digits_36 : adv_assets_digits_20;
    int width = 0;
    for (const char *s = value; *s; s++)
        for (unsigned i = 0; i < 12; i++) if (digits[i].glyph == (uint8_t)*s) width += digits[i].advance;
    int pen = x - (align == NT_ALIGN_RIGHT ? width : align == NT_ALIGN_CENTER ? width / 2 : 0);
    for (const char *s = value; *s; s++)
        for (unsigned i = 0; i < 12; i++) if (digits[i].glyph == (uint8_t)*s) {
            record(g, digits[i].asset, 0, pen, y, false, 0);
            pen += digits[i].advance;
        }
    return width;
}
