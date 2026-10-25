#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "adv_sprite.h"
#include "adv_ninepatch.h"
typedef struct { const adv_sprite_t *sprite; int16_t x, y; } adv_asset_piece_t;
typedef struct {
    const char *id;
    const adv_asset_piece_t *pieces;
    uint16_t piece_count, width, height;
    int16_t anchor_x, anchor_y;
    uint16_t fps;
    bool loop;
} adv_asset_record_t;
typedef struct { uint8_t glyph; const adv_asset_record_t *asset; uint16_t advance; } adv_asset_digit_t;
extern const adv_asset_record_t adv_assets_catalog[];
extern const size_t adv_assets_catalog_count;
const adv_asset_record_t *adv_assets_find(const char *id);
extern const uint16_t adv_assets_ui_palette[];
extern const size_t adv_assets_ui_palette_count;

extern const adv_ninepatch_t adv_assets_patch_menu_normal;
extern const adv_ninepatch_t adv_assets_patch_menu_selected;
extern const adv_ninepatch_t adv_assets_patch_menu_disabled;
extern const adv_ninepatch_t adv_assets_patch_info_normal;
extern const adv_ninepatch_t adv_assets_patch_info_current;
extern const adv_ninepatch_t adv_assets_patch_popup_normal;
extern const adv_asset_digit_t adv_assets_digits_36[12];
extern const adv_asset_digit_t adv_assets_digits_20[12];
#define ADV_ASSETS_UI_BG ((uint16_t)0xffde)
#define ADV_ASSETS_UI_PAPER ((uint16_t)0xffde)
#define ADV_ASSETS_UI_INK ((uint16_t)0x21c9)
#define ADV_ASSETS_UI_MUTED ((uint16_t)0x638f)
#define ADV_ASSETS_UI_LINE ((uint16_t)0xdefa)
#define ADV_ASSETS_UI_SHADOW ((uint16_t)0xdefa)
#define ADV_ASSETS_UI_BAR ((uint16_t)0x21c9)
#define ADV_ASSETS_UI_BAR_TEXT ((uint16_t)0xffde)
#define ADV_ASSETS_UI_ACCENT ((uint16_t)0xb268)
#define ADV_ASSETS_UI_SELECT ((uint16_t)0x21c9)
#define ADV_ASSETS_UI_TEAL ((uint16_t)0x3c0f)
#define ADV_ASSETS_UI_BLUE ((uint16_t)0x4392)
#define ADV_ASSETS_UI_BRONZE ((uint16_t)0xbb87)
#define ADV_ASSETS_UI_SILVER ((uint16_t)0x9d54)
#define ADV_ASSETS_UI_GOLD ((uint16_t)0xd527)
#define ADV_ASSETS_UI_WHITE ((uint16_t)0xffde)
#define ADV_ASSETS_UI_SEAL ((uint16_t)0xf77c)
#define ADV_ASSETS_UI_SURFACE ((uint16_t)0xf77c)
#define ADV_ASSETS_UI_EDGE_90999D ((uint16_t)0x94d3)
#define ADV_ASSETS_UI_EDGE_DBA39A ((uint16_t)0xdd13)
#define ADV_ASSETS_UI_EDGE_A9AFB0 ((uint16_t)0xad76)
#define ADV_ASSETS_UI_EDGE_899397 ((uint16_t)0x8c92)
#define ADV_ASSETS_UI_EDGE_B0B5B5 ((uint16_t)0xb5b6)
