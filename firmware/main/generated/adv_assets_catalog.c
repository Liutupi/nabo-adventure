#include "adv_assets_catalog.h"
#include <string.h>
#include "adv_assets_climb_a_charge_left__p0.h"
#include "adv_assets_climb_a_charge_right__p0.h"
#include "adv_assets_climb_a_grip_idle_left__p0.h"
#include "adv_assets_climb_a_grip_idle_right__p0.h"
#include "adv_assets_climb_a_jump_left__p0.h"
#include "adv_assets_climb_a_jump_right__p0.h"
#include "adv_assets_climb_a_settlement_cheer__p0.h"
#include "adv_assets_climb_a_slide_left__p0.h"
#include "adv_assets_climb_a_slide_right__p0.h"
#include "adv_assets_climb_a_summit_cheer_left__p0.h"
#include "adv_assets_climb_a_summit_cheer_right__p0.h"
#include "adv_assets_climb_a_switch_grab_left__p0.h"
#include "adv_assets_climb_a_switch_grab_right__p0.h"
#include "adv_assets_game_climb_props_canteen__p0.h"
#include "adv_assets_game_climb_props_falling_rock__p0.h"
#include "adv_assets_game_climb_props_hold_fragile__p0.h"
#include "adv_assets_game_climb_props_hold_ice__p0.h"
#include "adv_assets_game_climb_props_hold_normal__p0.h"
#include "adv_assets_game_climb_shared_snow_drift__p0.h"
#include "adv_assets_game_climb_shared_snow_mound__p0.h"
#include "adv_assets_game_climb_tiles_cold_0__p0.h"
#include "adv_assets_game_climb_tiles_cold_1__p0.h"
#include "adv_assets_game_climb_tiles_grey_0__p0.h"
#include "adv_assets_game_climb_tiles_grey_1__p0.h"
#include "adv_assets_game_climb_tiles_snow_0__p0.h"
#include "adv_assets_game_climb_tiles_snow_1__p0.h"
#include "adv_assets_game_night_glass_jar__p0.h"
#include "adv_assets_game_night_grass_00__p0.h"
#include "adv_assets_game_night_grass_01__p0.h"
#include "adv_assets_game_night_grass_02__p0.h"
#include "adv_assets_game_night_grass_03__p0.h"
#include "adv_assets_game_night_jar_glow__p0.h"
#include "adv_assets_game_night_tree_shadow_00__p0.h"
#include "adv_assets_game_night_tree_shadow_01__p0.h"
#include "adv_assets_game_night_tree_shadow_02__p0.h"
#include "adv_assets_game_night_tree_shadow_03__p0.h"
#include "adv_assets_game_post_props_cab_foreground__p0.h"
#include "adv_assets_game_post_props_carriage__p0.h"
#include "adv_assets_game_post_props_coal_pile__p0.h"
#include "adv_assets_game_post_props_cow__p0.h"
#include "adv_assets_game_post_props_envelope_blue__p0.h"
#include "adv_assets_game_post_props_envelope_gray__p0.h"
#include "adv_assets_game_post_props_envelope_green__p0.h"
#include "adv_assets_game_post_props_envelope_orange__p0.h"
#include "adv_assets_game_post_props_envelope_red__p0.h"
#include "adv_assets_game_post_props_envelope_yellow__p0.h"
#include "adv_assets_game_post_props_locomotive_body__p0.h"
#include "adv_assets_game_post_props_sheep__p0.h"
#include "adv_assets_game_post_props_station_platform_mask__p0.h"
#include "adv_assets_game_post_props_wheel_000__p0.h"
#include "adv_assets_game_post_props_wheel_001__p0.h"
#include "adv_assets_game_post_props_wheel_002__p0.h"
#include "adv_assets_game_post_props_wheel_003__p0.h"
#include "adv_assets_game_post_tiles_far_mountains__p0.h"
#include "adv_assets_game_post_tiles_rails__p0.h"
#include "adv_assets_game_post_tiles_sleepers__p0.h"
#include "adv_assets_game_post_tiles_track_fork__p0.h"
#include "adv_assets_game_post_tiles_track_straight__p0.h"
#include "adv_assets_game_ski_props_finish_arch__p0.h"
#include "adv_assets_game_ski_props_gate_blue__p0.h"
#include "adv_assets_game_ski_props_gate_red__p0.h"
#include "adv_assets_game_ski_props_hot_cocoa_cabin__p0.h"
#include "adv_assets_game_ski_props_pine_large__p0.h"
#include "adv_assets_game_ski_props_pole__p0.h"
#include "adv_assets_game_ski_props_ski_left__p0.h"
#include "adv_assets_game_ski_props_ski_right__p0.h"
#include "adv_assets_game_ski_shared_pine_small__p0.h"
#include "adv_assets_game_ski_shared_snow_drift__p0.h"
#include "adv_assets_game_ski_shared_snow_ground__p0.h"
#include "adv_assets_game_ski_shared_snow_mogul__p0.h"
#include "adv_assets_game_sky_basket_back__p0.h"
#include "adv_assets_game_sky_basket_front__p0.h"
#include "adv_assets_game_sky_burner__p0.h"
#include "adv_assets_game_sky_cloud_00__p0.h"
#include "adv_assets_game_sky_cloud_01__p0.h"
#include "adv_assets_game_sky_cloud_02__p0.h"
#include "adv_assets_game_sky_cloud_03__p0.h"
#include "adv_assets_game_sky_controls_idle__p0.h"
#include "adv_assets_game_sky_envelope__p0.h"
#include "adv_assets_game_sky_stamp__p0.h"
#include "adv_assets_game_sky_thundercloud__p0.h"
#include "adv_assets_game_space_lander_back__p0.h"
#include "adv_assets_game_space_lander_front__p0.h"
#include "adv_assets_game_space_props_asteroid__p0.h"
#include "adv_assets_game_space_props_flag__p0.h"
#include "adv_assets_game_space_props_fuel_can__p0.h"
#include "adv_assets_game_space_props_landing_pad__p0.h"
#include "adv_assets_game_space_tiles_lunar_0__p0.h"
#include "adv_assets_game_space_tiles_lunar_1__p0.h"
#include "adv_assets_game_space_tiles_lunar_2__p0.h"
#include "adv_assets_night_a_catch__p0.h"
#include "adv_assets_night_a_cheer__p0.h"
#include "adv_assets_night_a_lift_jar__p0.h"
#include "adv_assets_night_a_move_left__p0.h"
#include "adv_assets_night_a_move_right__p0.h"
#include "adv_assets_night_a_seat_idle__p0.h"
#include "adv_assets_night_a_yawn__p0.h"
#include "adv_assets_night_shared_moth__p0.h"
#include "adv_assets_post_a_delivered__p0.h"
#include "adv_assets_post_a_hit__p0.h"
#include "adv_assets_post_a_idle__p0.h"
#include "adv_assets_post_a_settlement_cheer__p0.h"
#include "adv_assets_post_a_throw__p0.h"
#include "adv_assets_post_a_whistle__p0.h"
#include "adv_assets_post_props_wheel_cycle__p0.h"
#include "adv_assets_post_props_whistle_cord__p0.h"
#include "adv_assets_ski_a_fall__p0.h"
#include "adv_assets_ski_a_finish__p0.h"
#include "adv_assets_ski_a_jump__p0.h"
#include "adv_assets_ski_a_lean_left__p0.h"
#include "adv_assets_ski_a_lean_right__p0.h"
#include "adv_assets_ski_a_settlement_cheer__p0.h"
#include "adv_assets_ski_a_straight__p0.h"
#include "adv_assets_sky_a_heat__p0.h"
#include "adv_assets_sky_a_hit__p0.h"
#include "adv_assets_sky_a_idle__p0.h"
#include "adv_assets_sky_a_receive_stamp__p0.h"
#include "adv_assets_sky_a_settlement_cheer__p0.h"
#include "adv_assets_sky_a_vent__p0.h"
#include "adv_assets_sky_props_bird__p0.h"
#include "adv_assets_sky_props_heat_controls__p0.h"
#include "adv_assets_sky_props_vent_controls__p0.h"
#include "adv_assets_space_a_cabin_idle__p0.h"
#include "adv_assets_space_a_hard_land__p0.h"
#include "adv_assets_space_a_jet__p0.h"
#include "adv_assets_space_a_land__p0.h"
#include "adv_assets_space_a_plant_flag__p0.h"
#include "adv_assets_space_a_settlement_cheer__p0.h"
#include "adv_assets_static_icon_fuel__p0.h"
#include "adv_assets_static_icon_hot_air__p0.h"
#include "adv_assets_static_icon_oxygen__p0.h"
#include "adv_assets_static_icon_spirit__p0.h"
#include "adv_assets_static_icon_stamina__p0.h"
#include "adv_assets_static_icon_steam__p0.h"
#include "adv_assets_static_icon_warmth__p0.h"
#include "adv_assets_static_landmark_climb__p0.h"
#include "adv_assets_static_landmark_dive__p0.h"
#include "adv_assets_static_landmark_jump__p0.h"
#include "adv_assets_static_landmark_kiosk__p0.h"
#include "adv_assets_static_landmark_night__p0.h"
#include "adv_assets_static_landmark_post__p0.h"
#include "adv_assets_static_landmark_ski__p0.h"
#include "adv_assets_static_landmark_sky__p0.h"
#include "adv_assets_static_landmark_space__p0.h"
#include "adv_assets_static_stamp_climb__p0.h"
#include "adv_assets_static_stamp_dive__p0.h"
#include "adv_assets_static_stamp_jump__p0.h"
#include "adv_assets_static_stamp_kiosk__p0.h"
#include "adv_assets_static_stamp_night__p0.h"
#include "adv_assets_static_stamp_post__p0.h"
#include "adv_assets_static_stamp_ski__p0.h"
#include "adv_assets_static_stamp_sky__p0.h"
#include "adv_assets_static_stamp_space__p0.h"
#include "adv_assets_static_tiles_deep_sea_bubble_chain__p0.h"
#include "adv_assets_static_tiles_deep_sea_coral_fan__p0.h"
#include "adv_assets_static_tiles_deep_sea_current_wave__p0.h"
#include "adv_assets_static_tiles_deep_sea_sea_rock__p0.h"
#include "adv_assets_static_tiles_deep_sea_seaweed__p0.h"
#include "adv_assets_static_tiles_deep_sea_shell__p0.h"
#include "adv_assets_static_tiles_harbor_buoy__p0.h"
#include "adv_assets_static_tiles_harbor_dock_planks__p0.h"
#include "adv_assets_static_tiles_harbor_mooring_post__p0.h"
#include "adv_assets_static_tiles_harbor_rope_coil__p0.h"
#include "adv_assets_static_tiles_harbor_wave_crest__p0.h"
#include "adv_assets_static_tiles_harbor_wave_line__p0.h"
#include "adv_assets_static_tiles_mountain_ice_crystals__p0.h"
#include "adv_assets_static_tiles_mountain_ridge__p0.h"
#include "adv_assets_static_tiles_mountain_snow_drift__p0.h"
#include "adv_assets_static_tiles_mountain_snowcap_rock__p0.h"
#include "adv_assets_static_tiles_mountain_young_pine__p0.h"
#include "adv_assets_static_tiles_night_forest_branch__p0.h"
#include "adv_assets_static_tiles_night_forest_fern__p0.h"
#include "adv_assets_static_tiles_night_forest_fireflies__p0.h"
#include "adv_assets_static_tiles_night_forest_mushrooms__p0.h"
#include "adv_assets_static_tiles_night_forest_shrub__p0.h"
#include "adv_assets_static_tiles_night_forest_tree_canopy__p0.h"
#include "adv_assets_static_tiles_rail_mail_sign__p0.h"
#include "adv_assets_static_tiles_rail_rail_crossing__p0.h"
#include "adv_assets_static_tiles_rail_rail_straight__p0.h"
#include "adv_assets_static_tiles_rail_telegraph_pole__p0.h"
#include "adv_assets_static_tiles_rail_wheat__p0.h"
#include "adv_assets_static_tiles_ski_gate_poles__p0.h"
#include "adv_assets_static_tiles_ski_small_spruce__p0.h"
#include "adv_assets_static_tiles_ski_snow_track__p0.h"
#include "adv_assets_static_tiles_sky_bird_silhouette__p0.h"
#include "adv_assets_static_tiles_sky_cloud_chain__p0.h"
#include "adv_assets_static_tiles_sky_cloud_large__p0.h"
#include "adv_assets_static_tiles_sky_cloud_small__p0.h"
#include "adv_assets_static_tiles_sky_feather__p0.h"
#include "adv_assets_static_tiles_space_asteroid__p0.h"
#include "adv_assets_static_tiles_space_comet__p0.h"
#include "adv_assets_static_tiles_space_orbit_dots__p0.h"
#include "adv_assets_static_tiles_space_ring_planet__p0.h"
#include "adv_assets_static_tiles_space_star_field__p0.h"
#include "adv_assets_static_tiles_town_bunting__p0.h"
#include "adv_assets_static_tiles_town_cobble_path__p0.h"
#include "adv_assets_static_tiles_town_flowerbed__p0.h"
#include "adv_assets_static_tiles_town_red_roof__p0.h"
#include "adv_assets_static_tiles_town_street_lamp__p0.h"
#include "adv_assets_static_tiles_town_window_box__p0.h"
#include "adv_assets_travel_cheer__p0.h"
#include "adv_assets_travel_idle__p0.h"
#include "adv_assets_travel_sad__p0.h"
#include "adv_assets_travel_turn_front_from_left__p0.h"
#include "adv_assets_travel_turn_front_from_right__p0.h"
#include "adv_assets_travel_turn_left__p0.h"
#include "adv_assets_travel_turn_right__p0.h"
#include "adv_assets_travel_walk_left__p0.h"
#include "adv_assets_travel_walk_right__p0.h"
#include "adv_assets_ui_bars_bottom__p0.h"
#include "adv_assets_ui_bars_top__p0.h"
#include "adv_assets_ui_cards_info_current_bottom__p0.h"
#include "adv_assets_ui_cards_info_current_bottom_left__p0.h"
#include "adv_assets_ui_cards_info_current_bottom_right__p0.h"
#include "adv_assets_ui_cards_info_current_center__p0.h"
#include "adv_assets_ui_cards_info_current_left__p0.h"
#include "adv_assets_ui_cards_info_current_right__p0.h"
#include "adv_assets_ui_cards_info_current_top_left__p0.h"
#include "adv_assets_ui_cards_info_current_top_right__p0.h"
#include "adv_assets_ui_cards_info_normal_bottom__p0.h"
#include "adv_assets_ui_cards_info_normal_bottom_left__p0.h"
#include "adv_assets_ui_cards_info_normal_bottom_right__p0.h"
#include "adv_assets_ui_cards_info_normal_center__p0.h"
#include "adv_assets_ui_cards_info_normal_left__p0.h"
#include "adv_assets_ui_cards_info_normal_top_left__p0.h"
#include "adv_assets_ui_cards_info_normal_top_right__p0.h"
#include "adv_assets_ui_cards_popup_normal_bottom__p0.h"
#include "adv_assets_ui_cards_popup_normal_bottom_left__p0.h"
#include "adv_assets_ui_cards_popup_normal_bottom_right__p0.h"
#include "adv_assets_ui_cards_popup_normal_left__p0.h"
#include "adv_assets_ui_cards_popup_normal_top_left__p0.h"
#include "adv_assets_ui_cards_popup_normal_top_right__p0.h"
#include "adv_assets_ui_labels_new_record__p0.h"
#include "adv_assets_ui_labels_placeholder__p0.h"
#include "adv_assets_ui_labels_test_no_record__p0.h"
#include "adv_assets_ui_map_footprints_backward__p0.h"
#include "adv_assets_ui_map_footprints_forward__p0.h"
#include "adv_assets_ui_map_lock__p0.h"
#include "adv_assets_ui_map_stamp_bronze__p0.h"
#include "adv_assets_ui_map_stamp_empty__p0.h"
#include "adv_assets_ui_map_stamp_gold__p0.h"
#include "adv_assets_ui_map_stamp_silver__p0.h"
#include "adv_assets_ui_map_station_current__p0.h"
#include "adv_assets_ui_map_station_locked__p0.h"
#include "adv_assets_ui_map_station_unlocked__p0.h"
#include "adv_assets_ui_map_temporary_position_marker__p0.h"
#include "adv_assets_ui_numbers_20_0__p0.h"
#include "adv_assets_ui_numbers_20_1__p0.h"
#include "adv_assets_ui_numbers_20_2__p0.h"
#include "adv_assets_ui_numbers_20_3__p0.h"
#include "adv_assets_ui_numbers_20_4__p0.h"
#include "adv_assets_ui_numbers_20_5__p0.h"
#include "adv_assets_ui_numbers_20_6__p0.h"
#include "adv_assets_ui_numbers_20_7__p0.h"
#include "adv_assets_ui_numbers_20_8__p0.h"
#include "adv_assets_ui_numbers_20_9__p0.h"
#include "adv_assets_ui_numbers_20_m__p0.h"
#include "adv_assets_ui_numbers_20_plus__p0.h"
#include "adv_assets_ui_numbers_36_0__p0.h"
#include "adv_assets_ui_numbers_36_1__p0.h"
#include "adv_assets_ui_numbers_36_2__p0.h"
#include "adv_assets_ui_numbers_36_3__p0.h"
#include "adv_assets_ui_numbers_36_4__p0.h"
#include "adv_assets_ui_numbers_36_5__p0.h"
#include "adv_assets_ui_numbers_36_6__p0.h"
#include "adv_assets_ui_numbers_36_7__p0.h"
#include "adv_assets_ui_numbers_36_8__p0.h"
#include "adv_assets_ui_numbers_36_9__p0.h"
#include "adv_assets_ui_numbers_36_m__p0.h"
#include "adv_assets_ui_numbers_36_plus__p0.h"
#include "adv_assets_ui_passport_grid_current__p0.h"
#include "adv_assets_ui_passport_grid_normal__p0.h"
#include "adv_assets_ui_passport_header__p0.h"
#include "adv_assets_ui_passport_locked_mask__p0.h"
#include "adv_assets_ui_passport_page_tile__p0.h"
#include "adv_assets_ui_resources_bar_frame__p0.h"
#include "adv_assets_ui_resources_fill__p0.h"
#include "adv_assets_ui_resources_fill_left_cap__p0.h"
#include "adv_assets_ui_resources_fill_right_cap__p0.h"
#include "adv_assets_ui_resources_icons_fuel__p0.h"
#include "adv_assets_ui_resources_icons_hot_air__p0.h"
#include "adv_assets_ui_resources_icons_oxygen__p0.h"
#include "adv_assets_ui_resources_icons_spirit__p0.h"
#include "adv_assets_ui_resources_icons_stamina__p0.h"
#include "adv_assets_ui_resources_icons_steam__p0.h"
#include "adv_assets_ui_resources_icons_temperature__p0.h"
#include "adv_assets_ui_resources_low_fill__p0.h"
#include "adv_assets_ui_stamps_ink_pad__p0.h"
#include "adv_assets_ui_wordmarks_climb__p0.h"
#include "adv_assets_ui_wordmarks_dive__p0.h"
#include "adv_assets_ui_wordmarks_jump__p0.h"
#include "adv_assets_ui_wordmarks_night__p0.h"
#include "adv_assets_ui_wordmarks_post__p0.h"
#include "adv_assets_ui_wordmarks_ski__p0.h"
#include "adv_assets_ui_wordmarks_sky__p0.h"
#include "adv_assets_ui_wordmarks_space__p0.h"
static const adv_asset_piece_t adv_assets_climb_a_charge_left__pieces[] = {
    {&adv_assets_climb_a_charge_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_charge_right__pieces[] = {
    {&adv_assets_climb_a_charge_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_grip_idle_left__pieces[] = {
    {&adv_assets_climb_a_grip_idle_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_grip_idle_right__pieces[] = {
    {&adv_assets_climb_a_grip_idle_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_jump_left__pieces[] = {
    {&adv_assets_climb_a_jump_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_jump_right__pieces[] = {
    {&adv_assets_climb_a_jump_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_settlement_cheer__pieces[] = {
    {&adv_assets_climb_a_settlement_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_slide_left__pieces[] = {
    {&adv_assets_climb_a_slide_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_slide_right__pieces[] = {
    {&adv_assets_climb_a_slide_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_summit_cheer_left__pieces[] = {
    {&adv_assets_climb_a_summit_cheer_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_summit_cheer_right__pieces[] = {
    {&adv_assets_climb_a_summit_cheer_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_switch_grab_left__pieces[] = {
    {&adv_assets_climb_a_switch_grab_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_climb_a_switch_grab_right__pieces[] = {
    {&adv_assets_climb_a_switch_grab_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_props_canteen__pieces[] = {
    {&adv_assets_game_climb_props_canteen__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_props_falling_rock__pieces[] = {
    {&adv_assets_game_climb_props_falling_rock__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_props_hold_fragile__pieces[] = {
    {&adv_assets_game_climb_props_hold_fragile__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_props_hold_ice__pieces[] = {
    {&adv_assets_game_climb_props_hold_ice__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_props_hold_normal__pieces[] = {
    {&adv_assets_game_climb_props_hold_normal__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_shared_snow_drift__pieces[] = {
    {&adv_assets_game_climb_shared_snow_drift__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_shared_snow_mound__pieces[] = {
    {&adv_assets_game_climb_shared_snow_mound__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_tiles_cold_0__pieces[] = {
    {&adv_assets_game_climb_tiles_cold_0__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_tiles_cold_1__pieces[] = {
    {&adv_assets_game_climb_tiles_cold_1__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_tiles_grey_0__pieces[] = {
    {&adv_assets_game_climb_tiles_grey_0__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_tiles_grey_1__pieces[] = {
    {&adv_assets_game_climb_tiles_grey_1__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_tiles_snow_0__pieces[] = {
    {&adv_assets_game_climb_tiles_snow_0__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_climb_tiles_snow_1__pieces[] = {
    {&adv_assets_game_climb_tiles_snow_1__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_glass_jar__pieces[] = {
    {&adv_assets_game_night_glass_jar__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_grass_00__pieces[] = {
    {&adv_assets_game_night_grass_00__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_grass_01__pieces[] = {
    {&adv_assets_game_night_grass_01__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_grass_02__pieces[] = {
    {&adv_assets_game_night_grass_02__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_grass_03__pieces[] = {
    {&adv_assets_game_night_grass_03__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_jar_glow__pieces[] = {
    {&adv_assets_game_night_jar_glow__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_tree_shadow_00__pieces[] = {
    {&adv_assets_game_night_tree_shadow_00__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_tree_shadow_01__pieces[] = {
    {&adv_assets_game_night_tree_shadow_01__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_tree_shadow_02__pieces[] = {
    {&adv_assets_game_night_tree_shadow_02__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_night_tree_shadow_03__pieces[] = {
    {&adv_assets_game_night_tree_shadow_03__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_cab_foreground__pieces[] = {
    {&adv_assets_game_post_props_cab_foreground__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_carriage__pieces[] = {
    {&adv_assets_game_post_props_carriage__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_coal_pile__pieces[] = {
    {&adv_assets_game_post_props_coal_pile__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_cow__pieces[] = {
    {&adv_assets_game_post_props_cow__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_envelope_blue__pieces[] = {
    {&adv_assets_game_post_props_envelope_blue__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_envelope_gray__pieces[] = {
    {&adv_assets_game_post_props_envelope_gray__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_envelope_green__pieces[] = {
    {&adv_assets_game_post_props_envelope_green__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_envelope_orange__pieces[] = {
    {&adv_assets_game_post_props_envelope_orange__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_envelope_red__pieces[] = {
    {&adv_assets_game_post_props_envelope_red__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_envelope_yellow__pieces[] = {
    {&adv_assets_game_post_props_envelope_yellow__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_locomotive_body__pieces[] = {
    {&adv_assets_game_post_props_locomotive_body__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_sheep__pieces[] = {
    {&adv_assets_game_post_props_sheep__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_station_platform_mask__pieces[] = {
    {&adv_assets_game_post_props_station_platform_mask__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_wheel_000__pieces[] = {
    {&adv_assets_game_post_props_wheel_000__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_wheel_001__pieces[] = {
    {&adv_assets_game_post_props_wheel_001__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_wheel_002__pieces[] = {
    {&adv_assets_game_post_props_wheel_002__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_props_wheel_003__pieces[] = {
    {&adv_assets_game_post_props_wheel_003__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_tiles_far_mountains__pieces[] = {
    {&adv_assets_game_post_tiles_far_mountains__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_tiles_rails__pieces[] = {
    {&adv_assets_game_post_tiles_rails__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_tiles_sleepers__pieces[] = {
    {&adv_assets_game_post_tiles_sleepers__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_tiles_track_fork__pieces[] = {
    {&adv_assets_game_post_tiles_track_fork__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_post_tiles_track_straight__pieces[] = {
    {&adv_assets_game_post_tiles_track_straight__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_finish_arch__pieces[] = {
    {&adv_assets_game_ski_props_finish_arch__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_gate_blue__pieces[] = {
    {&adv_assets_game_ski_props_gate_blue__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_gate_red__pieces[] = {
    {&adv_assets_game_ski_props_gate_red__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_hot_cocoa_cabin__pieces[] = {
    {&adv_assets_game_ski_props_hot_cocoa_cabin__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_pine_large__pieces[] = {
    {&adv_assets_game_ski_props_pine_large__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_pole__pieces[] = {
    {&adv_assets_game_ski_props_pole__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_ski_left__pieces[] = {
    {&adv_assets_game_ski_props_ski_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_props_ski_right__pieces[] = {
    {&adv_assets_game_ski_props_ski_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_shared_pine_small__pieces[] = {
    {&adv_assets_game_ski_shared_pine_small__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_shared_snow_drift__pieces[] = {
    {&adv_assets_game_ski_shared_snow_drift__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_shared_snow_ground__pieces[] = {
    {&adv_assets_game_ski_shared_snow_ground__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_ski_shared_snow_mogul__pieces[] = {
    {&adv_assets_game_ski_shared_snow_mogul__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_basket_back__pieces[] = {
    {&adv_assets_game_sky_basket_back__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_basket_front__pieces[] = {
    {&adv_assets_game_sky_basket_front__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_burner__pieces[] = {
    {&adv_assets_game_sky_burner__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_cloud_00__pieces[] = {
    {&adv_assets_game_sky_cloud_00__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_cloud_01__pieces[] = {
    {&adv_assets_game_sky_cloud_01__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_cloud_02__pieces[] = {
    {&adv_assets_game_sky_cloud_02__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_cloud_03__pieces[] = {
    {&adv_assets_game_sky_cloud_03__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_controls_idle__pieces[] = {
    {&adv_assets_game_sky_controls_idle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_envelope__pieces[] = {
    {&adv_assets_game_sky_envelope__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_stamp__pieces[] = {
    {&adv_assets_game_sky_stamp__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_sky_thundercloud__pieces[] = {
    {&adv_assets_game_sky_thundercloud__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_lander_back__pieces[] = {
    {&adv_assets_game_space_lander_back__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_lander_front__pieces[] = {
    {&adv_assets_game_space_lander_front__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_props_asteroid__pieces[] = {
    {&adv_assets_game_space_props_asteroid__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_props_flag__pieces[] = {
    {&adv_assets_game_space_props_flag__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_props_fuel_can__pieces[] = {
    {&adv_assets_game_space_props_fuel_can__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_props_landing_pad__pieces[] = {
    {&adv_assets_game_space_props_landing_pad__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_tiles_lunar_0__pieces[] = {
    {&adv_assets_game_space_tiles_lunar_0__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_tiles_lunar_1__pieces[] = {
    {&adv_assets_game_space_tiles_lunar_1__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_game_space_tiles_lunar_2__pieces[] = {
    {&adv_assets_game_space_tiles_lunar_2__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_catch__pieces[] = {
    {&adv_assets_night_a_catch__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_cheer__pieces[] = {
    {&adv_assets_night_a_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_lift_jar__pieces[] = {
    {&adv_assets_night_a_lift_jar__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_move_left__pieces[] = {
    {&adv_assets_night_a_move_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_move_right__pieces[] = {
    {&adv_assets_night_a_move_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_seat_idle__pieces[] = {
    {&adv_assets_night_a_seat_idle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_a_yawn__pieces[] = {
    {&adv_assets_night_a_yawn__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_night_shared_moth__pieces[] = {
    {&adv_assets_night_shared_moth__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_a_delivered__pieces[] = {
    {&adv_assets_post_a_delivered__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_a_hit__pieces[] = {
    {&adv_assets_post_a_hit__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_a_idle__pieces[] = {
    {&adv_assets_post_a_idle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_a_settlement_cheer__pieces[] = {
    {&adv_assets_post_a_settlement_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_a_throw__pieces[] = {
    {&adv_assets_post_a_throw__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_a_whistle__pieces[] = {
    {&adv_assets_post_a_whistle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_props_wheel_cycle__pieces[] = {
    {&adv_assets_post_props_wheel_cycle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_post_props_whistle_cord__pieces[] = {
    {&adv_assets_post_props_whistle_cord__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_fall__pieces[] = {
    {&adv_assets_ski_a_fall__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_finish__pieces[] = {
    {&adv_assets_ski_a_finish__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_jump__pieces[] = {
    {&adv_assets_ski_a_jump__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_lean_left__pieces[] = {
    {&adv_assets_ski_a_lean_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_lean_right__pieces[] = {
    {&adv_assets_ski_a_lean_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_settlement_cheer__pieces[] = {
    {&adv_assets_ski_a_settlement_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ski_a_straight__pieces[] = {
    {&adv_assets_ski_a_straight__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_a_heat__pieces[] = {
    {&adv_assets_sky_a_heat__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_a_hit__pieces[] = {
    {&adv_assets_sky_a_hit__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_a_idle__pieces[] = {
    {&adv_assets_sky_a_idle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_a_receive_stamp__pieces[] = {
    {&adv_assets_sky_a_receive_stamp__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_a_settlement_cheer__pieces[] = {
    {&adv_assets_sky_a_settlement_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_a_vent__pieces[] = {
    {&adv_assets_sky_a_vent__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_props_bird__pieces[] = {
    {&adv_assets_sky_props_bird__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_props_heat_controls__pieces[] = {
    {&adv_assets_sky_props_heat_controls__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_sky_props_vent_controls__pieces[] = {
    {&adv_assets_sky_props_vent_controls__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_space_a_cabin_idle__pieces[] = {
    {&adv_assets_space_a_cabin_idle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_space_a_hard_land__pieces[] = {
    {&adv_assets_space_a_hard_land__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_space_a_jet__pieces[] = {
    {&adv_assets_space_a_jet__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_space_a_land__pieces[] = {
    {&adv_assets_space_a_land__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_space_a_plant_flag__pieces[] = {
    {&adv_assets_space_a_plant_flag__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_space_a_settlement_cheer__pieces[] = {
    {&adv_assets_space_a_settlement_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_fuel__pieces[] = {
    {&adv_assets_static_icon_fuel__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_hot_air__pieces[] = {
    {&adv_assets_static_icon_hot_air__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_oxygen__pieces[] = {
    {&adv_assets_static_icon_oxygen__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_spirit__pieces[] = {
    {&adv_assets_static_icon_spirit__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_stamina__pieces[] = {
    {&adv_assets_static_icon_stamina__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_steam__pieces[] = {
    {&adv_assets_static_icon_steam__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_icon_warmth__pieces[] = {
    {&adv_assets_static_icon_warmth__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_climb__pieces[] = {
    {&adv_assets_static_landmark_climb__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_dive__pieces[] = {
    {&adv_assets_static_landmark_dive__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_jump__pieces[] = {
    {&adv_assets_static_landmark_jump__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_kiosk__pieces[] = {
    {&adv_assets_static_landmark_kiosk__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_night__pieces[] = {
    {&adv_assets_static_landmark_night__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_post__pieces[] = {
    {&adv_assets_static_landmark_post__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_ski__pieces[] = {
    {&adv_assets_static_landmark_ski__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_sky__pieces[] = {
    {&adv_assets_static_landmark_sky__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_landmark_space__pieces[] = {
    {&adv_assets_static_landmark_space__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_climb__pieces[] = {
    {&adv_assets_static_stamp_climb__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_dive__pieces[] = {
    {&adv_assets_static_stamp_dive__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_jump__pieces[] = {
    {&adv_assets_static_stamp_jump__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_kiosk__pieces[] = {
    {&adv_assets_static_stamp_kiosk__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_night__pieces[] = {
    {&adv_assets_static_stamp_night__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_post__pieces[] = {
    {&adv_assets_static_stamp_post__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_ski__pieces[] = {
    {&adv_assets_static_stamp_ski__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_sky__pieces[] = {
    {&adv_assets_static_stamp_sky__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_stamp_space__pieces[] = {
    {&adv_assets_static_stamp_space__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_deep_sea_bubble_chain__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_bubble_chain__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_deep_sea_coral_fan__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_coral_fan__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_deep_sea_current_wave__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_current_wave__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_deep_sea_sea_rock__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_sea_rock__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_deep_sea_seaweed__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_seaweed__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_deep_sea_shell__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_shell__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_harbor_buoy__pieces[] = {
    {&adv_assets_static_tiles_harbor_buoy__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_harbor_dock_planks__pieces[] = {
    {&adv_assets_static_tiles_harbor_dock_planks__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_harbor_mooring_post__pieces[] = {
    {&adv_assets_static_tiles_harbor_mooring_post__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_harbor_rope_coil__pieces[] = {
    {&adv_assets_static_tiles_harbor_rope_coil__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_harbor_wave_crest__pieces[] = {
    {&adv_assets_static_tiles_harbor_wave_crest__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_harbor_wave_line__pieces[] = {
    {&adv_assets_static_tiles_harbor_wave_line__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_mountain_ice_crystals__pieces[] = {
    {&adv_assets_static_tiles_mountain_ice_crystals__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_mountain_ridge__pieces[] = {
    {&adv_assets_static_tiles_mountain_ridge__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_mountain_rock_face__pieces[] = {
    {&adv_assets_static_tiles_deep_sea_sea_rock__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_mountain_snow_drift__pieces[] = {
    {&adv_assets_static_tiles_mountain_snow_drift__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_mountain_snowcap_rock__pieces[] = {
    {&adv_assets_static_tiles_mountain_snowcap_rock__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_mountain_young_pine__pieces[] = {
    {&adv_assets_static_tiles_mountain_young_pine__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_night_forest_branch__pieces[] = {
    {&adv_assets_static_tiles_night_forest_branch__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_night_forest_fern__pieces[] = {
    {&adv_assets_static_tiles_night_forest_fern__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_night_forest_fireflies__pieces[] = {
    {&adv_assets_static_tiles_night_forest_fireflies__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_night_forest_mushrooms__pieces[] = {
    {&adv_assets_static_tiles_night_forest_mushrooms__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_night_forest_shrub__pieces[] = {
    {&adv_assets_static_tiles_night_forest_shrub__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_night_forest_tree_canopy__pieces[] = {
    {&adv_assets_static_tiles_night_forest_tree_canopy__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_rail_mail_sign__pieces[] = {
    {&adv_assets_static_tiles_rail_mail_sign__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_rail_rail_crossing__pieces[] = {
    {&adv_assets_static_tiles_rail_rail_crossing__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_rail_rail_straight__pieces[] = {
    {&adv_assets_static_tiles_rail_rail_straight__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_rail_telegraph_pole__pieces[] = {
    {&adv_assets_static_tiles_rail_telegraph_pole__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_rail_trackside_grass__pieces[] = {
    {&adv_assets_static_tiles_night_forest_fern__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_rail_wheat__pieces[] = {
    {&adv_assets_static_tiles_rail_wheat__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_ski_gate_poles__pieces[] = {
    {&adv_assets_static_tiles_ski_gate_poles__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_ski_small_spruce__pieces[] = {
    {&adv_assets_static_tiles_ski_small_spruce__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_ski_snow_mound__pieces[] = {
    {&adv_assets_static_tiles_mountain_snowcap_rock__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_ski_snow_pine__pieces[] = {
    {&adv_assets_static_tiles_ski_small_spruce__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_ski_snow_track__pieces[] = {
    {&adv_assets_static_tiles_ski_snow_track__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_sky_bird_silhouette__pieces[] = {
    {&adv_assets_static_tiles_sky_bird_silhouette__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_sky_cloud_chain__pieces[] = {
    {&adv_assets_static_tiles_sky_cloud_chain__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_sky_cloud_large__pieces[] = {
    {&adv_assets_static_tiles_sky_cloud_large__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_sky_cloud_small__pieces[] = {
    {&adv_assets_static_tiles_sky_cloud_small__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_sky_feather__pieces[] = {
    {&adv_assets_static_tiles_sky_feather__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_sky_wind_ribbon__pieces[] = {
    {&adv_assets_static_tiles_harbor_wave_line__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_space_asteroid__pieces[] = {
    {&adv_assets_static_tiles_space_asteroid__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_space_comet__pieces[] = {
    {&adv_assets_static_tiles_space_comet__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_space_crater__pieces[] = {
    {&adv_assets_static_tiles_space_asteroid__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_space_orbit_dots__pieces[] = {
    {&adv_assets_static_tiles_space_orbit_dots__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_space_ring_planet__pieces[] = {
    {&adv_assets_static_tiles_space_ring_planet__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_space_star_field__pieces[] = {
    {&adv_assets_static_tiles_space_star_field__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_town_bunting__pieces[] = {
    {&adv_assets_static_tiles_town_bunting__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_town_cobble_path__pieces[] = {
    {&adv_assets_static_tiles_town_cobble_path__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_town_flowerbed__pieces[] = {
    {&adv_assets_static_tiles_town_flowerbed__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_town_red_roof__pieces[] = {
    {&adv_assets_static_tiles_town_red_roof__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_town_street_lamp__pieces[] = {
    {&adv_assets_static_tiles_town_street_lamp__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_static_tiles_town_window_box__pieces[] = {
    {&adv_assets_static_tiles_town_window_box__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_cheer__pieces[] = {
    {&adv_assets_travel_cheer__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_idle__pieces[] = {
    {&adv_assets_travel_idle__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_sad__pieces[] = {
    {&adv_assets_travel_sad__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_turn_front_from_left__pieces[] = {
    {&adv_assets_travel_turn_front_from_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_turn_front_from_right__pieces[] = {
    {&adv_assets_travel_turn_front_from_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_turn_left__pieces[] = {
    {&adv_assets_travel_turn_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_turn_right__pieces[] = {
    {&adv_assets_travel_turn_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_walk_left__pieces[] = {
    {&adv_assets_travel_walk_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_travel_walk_right__pieces[] = {
    {&adv_assets_travel_walk_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_bars_bottom__pieces[] = {
    {&adv_assets_ui_bars_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_bars_top__pieces[] = {
    {&adv_assets_ui_bars_top__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_bottom__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_bottom_left__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_bottom_right__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_center__pieces[] = {
    {&adv_assets_ui_cards_info_current_center__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_left__pieces[] = {
    {&adv_assets_ui_cards_info_current_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_right__pieces[] = {
    {&adv_assets_ui_cards_info_current_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_top__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_top_left__pieces[] = {
    {&adv_assets_ui_cards_info_current_top_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_current_top_right__pieces[] = {
    {&adv_assets_ui_cards_info_current_top_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_bottom__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_bottom_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_bottom_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_center__pieces[] = {
    {&adv_assets_ui_cards_info_normal_center__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_top__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_top_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_top_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_info_normal_top_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_top_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_bottom__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_bottom_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_bottom_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_center__pieces[] = {
    {&adv_assets_ui_cards_info_normal_center__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_top__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_top_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_top_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_disabled_top_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_top_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_bottom__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_bottom_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_bottom_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_center__pieces[] = {
    {&adv_assets_ui_cards_info_normal_center__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_top__pieces[] = {
    {&adv_assets_ui_cards_info_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_top_left__pieces[] = {
    {&adv_assets_ui_cards_info_normal_top_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_normal_top_right__pieces[] = {
    {&adv_assets_ui_cards_info_normal_top_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_bottom__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_bottom_left__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_bottom_right__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_center__pieces[] = {
    {&adv_assets_ui_cards_info_current_center__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_left__pieces[] = {
    {&adv_assets_ui_cards_info_current_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_right__pieces[] = {
    {&adv_assets_ui_cards_info_current_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_top__pieces[] = {
    {&adv_assets_ui_cards_info_current_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_top_left__pieces[] = {
    {&adv_assets_ui_cards_info_current_top_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_menu_selected_top_right__pieces[] = {
    {&adv_assets_ui_cards_info_current_top_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_bottom__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_bottom_left__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_bottom_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_bottom_right__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_bottom_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_center__pieces[] = {
    {&adv_assets_ui_cards_info_normal_center__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_left__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_right__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_top__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_bottom__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_top_left__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_top_left__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_cards_popup_normal_top_right__pieces[] = {
    {&adv_assets_ui_cards_popup_normal_top_right__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_labels_new_record__pieces[] = {
    {&adv_assets_ui_labels_new_record__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_labels_placeholder__pieces[] = {
    {&adv_assets_ui_labels_placeholder__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_labels_test_no_record__pieces[] = {
    {&adv_assets_ui_labels_test_no_record__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_footprints_backward__pieces[] = {
    {&adv_assets_ui_map_footprints_backward__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_footprints_forward__pieces[] = {
    {&adv_assets_ui_map_footprints_forward__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_lock__pieces[] = {
    {&adv_assets_ui_map_lock__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_stamp_bronze__pieces[] = {
    {&adv_assets_ui_map_stamp_bronze__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_stamp_empty__pieces[] = {
    {&adv_assets_ui_map_stamp_empty__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_stamp_gold__pieces[] = {
    {&adv_assets_ui_map_stamp_gold__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_stamp_silver__pieces[] = {
    {&adv_assets_ui_map_stamp_silver__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_station_current__pieces[] = {
    {&adv_assets_ui_map_station_current__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_station_locked__pieces[] = {
    {&adv_assets_ui_map_station_locked__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_station_unlocked__pieces[] = {
    {&adv_assets_ui_map_station_unlocked__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_map_temporary_position_marker__pieces[] = {
    {&adv_assets_ui_map_temporary_position_marker__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_0__pieces[] = {
    {&adv_assets_ui_numbers_20_0__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_1__pieces[] = {
    {&adv_assets_ui_numbers_20_1__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_2__pieces[] = {
    {&adv_assets_ui_numbers_20_2__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_3__pieces[] = {
    {&adv_assets_ui_numbers_20_3__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_4__pieces[] = {
    {&adv_assets_ui_numbers_20_4__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_5__pieces[] = {
    {&adv_assets_ui_numbers_20_5__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_6__pieces[] = {
    {&adv_assets_ui_numbers_20_6__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_7__pieces[] = {
    {&adv_assets_ui_numbers_20_7__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_8__pieces[] = {
    {&adv_assets_ui_numbers_20_8__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_9__pieces[] = {
    {&adv_assets_ui_numbers_20_9__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_m__pieces[] = {
    {&adv_assets_ui_numbers_20_m__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_20_plus__pieces[] = {
    {&adv_assets_ui_numbers_20_plus__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_0__pieces[] = {
    {&adv_assets_ui_numbers_36_0__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_1__pieces[] = {
    {&adv_assets_ui_numbers_36_1__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_2__pieces[] = {
    {&adv_assets_ui_numbers_36_2__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_3__pieces[] = {
    {&adv_assets_ui_numbers_36_3__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_4__pieces[] = {
    {&adv_assets_ui_numbers_36_4__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_5__pieces[] = {
    {&adv_assets_ui_numbers_36_5__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_6__pieces[] = {
    {&adv_assets_ui_numbers_36_6__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_7__pieces[] = {
    {&adv_assets_ui_numbers_36_7__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_8__pieces[] = {
    {&adv_assets_ui_numbers_36_8__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_9__pieces[] = {
    {&adv_assets_ui_numbers_36_9__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_m__pieces[] = {
    {&adv_assets_ui_numbers_36_m__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_numbers_36_plus__pieces[] = {
    {&adv_assets_ui_numbers_36_plus__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_passport_grid_current__pieces[] = {
    {&adv_assets_ui_passport_grid_current__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_passport_grid_normal__pieces[] = {
    {&adv_assets_ui_passport_grid_normal__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_passport_header__pieces[] = {
    {&adv_assets_ui_passport_header__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_passport_locked_mask__pieces[] = {
    {&adv_assets_ui_passport_locked_mask__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_passport_page_tile__pieces[] = {
    {&adv_assets_ui_passport_page_tile__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_bar_frame__pieces[] = {
    {&adv_assets_ui_resources_bar_frame__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_fill__pieces[] = {
    {&adv_assets_ui_resources_fill__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_fill_left_cap__pieces[] = {
    {&adv_assets_ui_resources_fill_left_cap__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_fill_right_cap__pieces[] = {
    {&adv_assets_ui_resources_fill_right_cap__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_fuel__pieces[] = {
    {&adv_assets_ui_resources_icons_fuel__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_hot_air__pieces[] = {
    {&adv_assets_ui_resources_icons_hot_air__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_oxygen__pieces[] = {
    {&adv_assets_ui_resources_icons_oxygen__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_spirit__pieces[] = {
    {&adv_assets_ui_resources_icons_spirit__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_stamina__pieces[] = {
    {&adv_assets_ui_resources_icons_stamina__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_steam__pieces[] = {
    {&adv_assets_ui_resources_icons_steam__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_icons_temperature__pieces[] = {
    {&adv_assets_ui_resources_icons_temperature__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_low_fill__pieces[] = {
    {&adv_assets_ui_resources_low_fill__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_low_fill_left_cap__pieces[] = {
    {&adv_assets_ui_resources_fill_left_cap__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_resources_low_fill_right_cap__pieces[] = {
    {&adv_assets_ui_resources_fill_right_cap__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_stamps_ink_pad__pieces[] = {
    {&adv_assets_ui_stamps_ink_pad__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_climb__pieces[] = {
    {&adv_assets_ui_wordmarks_climb__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_dive__pieces[] = {
    {&adv_assets_ui_wordmarks_dive__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_jump__pieces[] = {
    {&adv_assets_ui_wordmarks_jump__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_night__pieces[] = {
    {&adv_assets_ui_wordmarks_night__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_post__pieces[] = {
    {&adv_assets_ui_wordmarks_post__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_ski__pieces[] = {
    {&adv_assets_ui_wordmarks_ski__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_sky__pieces[] = {
    {&adv_assets_ui_wordmarks_sky__p0, 0, 0},
};
static const adv_asset_piece_t adv_assets_ui_wordmarks_space__pieces[] = {
    {&adv_assets_ui_wordmarks_space__p0, 0, 0},
};
const adv_asset_record_t adv_assets_catalog[] = {
    {"climb_a/charge_left", adv_assets_climb_a_charge_left__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/charge_right", adv_assets_climb_a_charge_right__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/grip_idle_left", adv_assets_climb_a_grip_idle_left__pieces, 1, 60, 65, 30, 62, 12, true},
    {"climb_a/grip_idle_right", adv_assets_climb_a_grip_idle_right__pieces, 1, 60, 65, 30, 62, 12, true},
    {"climb_a/jump_left", adv_assets_climb_a_jump_left__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/jump_right", adv_assets_climb_a_jump_right__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/settlement_cheer", adv_assets_climb_a_settlement_cheer__pieces, 1, 72, 78, 36, 75, 12, false},
    {"climb_a/slide_left", adv_assets_climb_a_slide_left__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/slide_right", adv_assets_climb_a_slide_right__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/summit_cheer_left", adv_assets_climb_a_summit_cheer_left__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/summit_cheer_right", adv_assets_climb_a_summit_cheer_right__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/switch_grab_left", adv_assets_climb_a_switch_grab_left__pieces, 1, 60, 65, 30, 62, 12, false},
    {"climb_a/switch_grab_right", adv_assets_climb_a_switch_grab_right__pieces, 1, 60, 65, 30, 62, 12, false},
    {"game/climb/props/canteen", adv_assets_game_climb_props_canteen__pieces, 1, 16, 24, 8, 24, 0, false},
    {"game/climb/props/falling-rock", adv_assets_game_climb_props_falling_rock__pieces, 1, 24, 24, 12, 24, 0, false},
    {"game/climb/props/hold-fragile", adv_assets_game_climb_props_hold_fragile__pieces, 1, 24, 20, 12, 9, 0, false},
    {"game/climb/props/hold-ice", adv_assets_game_climb_props_hold_ice__pieces, 1, 24, 20, 12, 9, 0, false},
    {"game/climb/props/hold-normal", adv_assets_game_climb_props_hold_normal__pieces, 1, 24, 20, 12, 9, 0, false},
    {"game/climb/shared/snow-drift", adv_assets_game_climb_shared_snow_drift__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/shared/snow-mound", adv_assets_game_climb_shared_snow_mound__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/tiles/cold-0", adv_assets_game_climb_tiles_cold_0__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/tiles/cold-1", adv_assets_game_climb_tiles_cold_1__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/tiles/grey-0", adv_assets_game_climb_tiles_grey_0__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/tiles/grey-1", adv_assets_game_climb_tiles_grey_1__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/tiles/snow-0", adv_assets_game_climb_tiles_snow_0__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/climb/tiles/snow-1", adv_assets_game_climb_tiles_snow_1__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/night/glass_jar", adv_assets_game_night_glass_jar__pieces, 1, 19, 37, 9, 37, 0, false},
    {"game/night/grass_00", adv_assets_game_night_grass_00__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/grass_01", adv_assets_game_night_grass_01__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/grass_02", adv_assets_game_night_grass_02__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/grass_03", adv_assets_game_night_grass_03__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/jar_glow", adv_assets_game_night_jar_glow__pieces, 1, 32, 32, 16, 16, 0, false},
    {"game/night/tree_shadow_00", adv_assets_game_night_tree_shadow_00__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/tree_shadow_01", adv_assets_game_night_tree_shadow_01__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/tree_shadow_02", adv_assets_game_night_tree_shadow_02__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/night/tree_shadow_03", adv_assets_game_night_tree_shadow_03__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/post/props/cab-foreground", adv_assets_game_post_props_cab_foreground__pieces, 1, 96, 88, 48, 81, 0, false},
    {"game/post/props/carriage", adv_assets_game_post_props_carriage__pieces, 1, 64, 48, 32, 44, 0, false},
    {"game/post/props/coal-pile", adv_assets_game_post_props_coal_pile__pieces, 1, 32, 24, 16, 23, 0, false},
    {"game/post/props/cow", adv_assets_game_post_props_cow__pieces, 1, 48, 36, 24, 34, 0, false},
    {"game/post/props/envelope-blue", adv_assets_game_post_props_envelope_blue__pieces, 1, 32, 24, 16, 12, 0, false},
    {"game/post/props/envelope-gray", adv_assets_game_post_props_envelope_gray__pieces, 1, 32, 24, 16, 12, 0, false},
    {"game/post/props/envelope-green", adv_assets_game_post_props_envelope_green__pieces, 1, 32, 24, 16, 12, 0, false},
    {"game/post/props/envelope-orange", adv_assets_game_post_props_envelope_orange__pieces, 1, 32, 24, 16, 12, 0, false},
    {"game/post/props/envelope-red", adv_assets_game_post_props_envelope_red__pieces, 1, 32, 24, 16, 12, 0, false},
    {"game/post/props/envelope-yellow", adv_assets_game_post_props_envelope_yellow__pieces, 1, 32, 24, 16, 12, 0, false},
    {"game/post/props/locomotive-body", adv_assets_game_post_props_locomotive_body__pieces, 1, 96, 88, 48, 81, 0, false},
    {"game/post/props/sheep", adv_assets_game_post_props_sheep__pieces, 1, 40, 32, 20, 28, 0, false},
    {"game/post/props/station-platform-mask", adv_assets_game_post_props_station_platform_mask__pieces, 1, 80, 56, 40, 56, 0, false},
    {"game/post/props/wheel-000", adv_assets_game_post_props_wheel_000__pieces, 1, 96, 88, 48, 81, 0, false},
    {"game/post/props/wheel-001", adv_assets_game_post_props_wheel_001__pieces, 1, 96, 88, 48, 81, 0, false},
    {"game/post/props/wheel-002", adv_assets_game_post_props_wheel_002__pieces, 1, 96, 88, 48, 81, 0, false},
    {"game/post/props/wheel-003", adv_assets_game_post_props_wheel_003__pieces, 1, 96, 88, 48, 81, 0, false},
    {"game/post/tiles/far-mountains", adv_assets_game_post_tiles_far_mountains__pieces, 1, 96, 32, 48, 32, 0, false},
    {"game/post/tiles/rails", adv_assets_game_post_tiles_rails__pieces, 1, 32, 32, 16, 32, 0, false},
    {"game/post/tiles/sleepers", adv_assets_game_post_tiles_sleepers__pieces, 1, 32, 32, 16, 32, 0, false},
    {"game/post/tiles/track-fork", adv_assets_game_post_tiles_track_fork__pieces, 1, 64, 56, 32, 36, 0, false},
    {"game/post/tiles/track-straight", adv_assets_game_post_tiles_track_straight__pieces, 1, 32, 32, 16, 32, 0, false},
    {"game/ski/props/finish-arch", adv_assets_game_ski_props_finish_arch__pieces, 1, 96, 88, 48, 77, 0, false},
    {"game/ski/props/gate-blue", adv_assets_game_ski_props_gate_blue__pieces, 1, 64, 56, 32, 52, 0, false},
    {"game/ski/props/gate-red", adv_assets_game_ski_props_gate_red__pieces, 1, 64, 56, 32, 52, 0, false},
    {"game/ski/props/hot-cocoa-cabin", adv_assets_game_ski_props_hot_cocoa_cabin__pieces, 1, 64, 64, 32, 58, 0, false},
    {"game/ski/props/pine-large", adv_assets_game_ski_props_pine_large__pieces, 1, 64, 64, 32, 60, 0, false},
    {"game/ski/props/pole", adv_assets_game_ski_props_pole__pieces, 1, 5, 24, 2, 3, 0, false},
    {"game/ski/props/ski-left", adv_assets_game_ski_props_ski_left__pieces, 1, 32, 10, 25, 3, 0, false},
    {"game/ski/props/ski-right", adv_assets_game_ski_props_ski_right__pieces, 1, 32, 10, 7, 3, 0, false},
    {"game/ski/shared/pine-small", adv_assets_game_ski_shared_pine_small__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/ski/shared/snow-drift", adv_assets_game_ski_shared_snow_drift__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/ski/shared/snow-ground", adv_assets_game_ski_shared_snow_ground__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/ski/shared/snow-mogul", adv_assets_game_ski_shared_snow_mogul__pieces, 1, 32, 32, 16, 31, 0, false},
    {"game/sky/basket_back", adv_assets_game_sky_basket_back__pieces, 1, 64, 10, 32, 2, 0, false},
    {"game/sky/basket_front", adv_assets_game_sky_basket_front__pieces, 1, 64, 28, 32, 2, 0, false},
    {"game/sky/burner", adv_assets_game_sky_burner__pieces, 1, 16, 12, 8, 6, 0, false},
    {"game/sky/cloud_00", adv_assets_game_sky_cloud_00__pieces, 1, 32, 32, 16, 26, 0, false},
    {"game/sky/cloud_01", adv_assets_game_sky_cloud_01__pieces, 1, 32, 32, 16, 25, 0, false},
    {"game/sky/cloud_02", adv_assets_game_sky_cloud_02__pieces, 1, 32, 32, 16, 24, 0, false},
    {"game/sky/cloud_03", adv_assets_game_sky_cloud_03__pieces, 1, 32, 32, 16, 23, 0, false},
    {"game/sky/controls_idle", adv_assets_game_sky_controls_idle__pieces, 1, 43, 40, 22, 40, 0, false},
    {"game/sky/envelope", adv_assets_game_sky_envelope__pieces, 1, 96, 96, 48, 94, 0, false},
    {"game/sky/stamp", adv_assets_game_sky_stamp__pieces, 1, 16, 20, 8, 10, 0, false},
    {"game/sky/thundercloud", adv_assets_game_sky_thundercloud__pieces, 1, 48, 32, 24, 29, 0, false},
    {"game/space/lander/back", adv_assets_game_space_lander_back__pieces, 1, 96, 96, 48, 92, 0, false},
    {"game/space/lander/front", adv_assets_game_space_lander_front__pieces, 1, 96, 96, 48, 92, 0, false},
    {"game/space/props/asteroid", adv_assets_game_space_props_asteroid__pieces, 1, 32, 28, 16, 28, 0, false},
    {"game/space/props/flag", adv_assets_game_space_props_flag__pieces, 1, 16, 28, 2, 28, 0, false},
    {"game/space/props/fuel-can", adv_assets_game_space_props_fuel_can__pieces, 1, 16, 24, 8, 24, 0, false},
    {"game/space/props/landing-pad", adv_assets_game_space_props_landing_pad__pieces, 1, 96, 24, 48, 24, 0, false},
    {"game/space/tiles/lunar-0", adv_assets_game_space_tiles_lunar_0__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/space/tiles/lunar-1", adv_assets_game_space_tiles_lunar_1__pieces, 1, 32, 32, 0, 0, 0, false},
    {"game/space/tiles/lunar-2", adv_assets_game_space_tiles_lunar_2__pieces, 1, 32, 32, 0, 0, 0, false},
    {"night_a/catch", adv_assets_night_a_catch__pieces, 1, 54, 56, 20, 56, 12, false},
    {"night_a/cheer", adv_assets_night_a_cheer__pieces, 1, 56, 72, 23, 72, 12, false},
    {"night_a/lift_jar", adv_assets_night_a_lift_jar__pieces, 1, 54, 56, 20, 56, 12, false},
    {"night_a/move_left", adv_assets_night_a_move_left__pieces, 1, 54, 56, 20, 56, 12, false},
    {"night_a/move_right", adv_assets_night_a_move_right__pieces, 1, 54, 56, 20, 56, 12, false},
    {"night_a/seat_idle", adv_assets_night_a_seat_idle__pieces, 1, 54, 56, 20, 56, 12, true},
    {"night_a/yawn", adv_assets_night_a_yawn__pieces, 1, 54, 56, 20, 56, 12, false},
    {"night_shared/moth", adv_assets_night_shared_moth__pieces, 1, 16, 16, 8, 13, 12, true},
    {"post_a/delivered", adv_assets_post_a_delivered__pieces, 1, 36, 40, 22, 40, 12, false},
    {"post_a/hit", adv_assets_post_a_hit__pieces, 1, 36, 40, 22, 40, 12, false},
    {"post_a/idle", adv_assets_post_a_idle__pieces, 1, 36, 40, 22, 40, 12, true},
    {"post_a/settlement_cheer", adv_assets_post_a_settlement_cheer__pieces, 1, 49, 72, 27, 72, 12, false},
    {"post_a/throw", adv_assets_post_a_throw__pieces, 1, 36, 40, 22, 40, 12, false},
    {"post_a/whistle", adv_assets_post_a_whistle__pieces, 1, 36, 40, 22, 40, 12, false},
    {"post_props/wheel-cycle", adv_assets_post_props_wheel_cycle__pieces, 1, 96, 88, 48, 81, 12, true},
    {"post_props/whistle-cord", adv_assets_post_props_whistle_cord__pieces, 1, 96, 88, 48, 81, 12, false},
    {"ski_a/fall", adv_assets_ski_a_fall__pieces, 1, 63, 68, 32, 60, 12, false},
    {"ski_a/finish", adv_assets_ski_a_finish__pieces, 1, 63, 68, 32, 60, 12, false},
    {"ski_a/jump", adv_assets_ski_a_jump__pieces, 1, 63, 68, 32, 60, 12, false},
    {"ski_a/lean_left", adv_assets_ski_a_lean_left__pieces, 1, 63, 68, 32, 60, 12, false},
    {"ski_a/lean_right", adv_assets_ski_a_lean_right__pieces, 1, 63, 68, 32, 60, 12, false},
    {"ski_a/settlement_cheer", adv_assets_ski_a_settlement_cheer__pieces, 1, 45, 72, 30, 72, 12, false},
    {"ski_a/straight", adv_assets_ski_a_straight__pieces, 1, 63, 68, 32, 60, 12, true},
    {"sky_a/heat", adv_assets_sky_a_heat__pieces, 1, 43, 40, 22, 40, 12, false},
    {"sky_a/hit", adv_assets_sky_a_hit__pieces, 1, 43, 40, 22, 40, 12, false},
    {"sky_a/idle", adv_assets_sky_a_idle__pieces, 1, 43, 40, 22, 40, 12, true},
    {"sky_a/receive_stamp", adv_assets_sky_a_receive_stamp__pieces, 1, 43, 40, 22, 40, 12, false},
    {"sky_a/settlement_cheer", adv_assets_sky_a_settlement_cheer__pieces, 1, 51, 72, 27, 72, 12, false},
    {"sky_a/vent", adv_assets_sky_a_vent__pieces, 1, 43, 40, 22, 40, 12, false},
    {"sky_props/bird", adv_assets_sky_props_bird__pieces, 1, 24, 20, 12, 12, 12, true},
    {"sky_props/heat_controls", adv_assets_sky_props_heat_controls__pieces, 1, 43, 40, 22, 40, 12, false},
    {"sky_props/vent_controls", adv_assets_sky_props_vent_controls__pieces, 1, 43, 40, 22, 40, 12, false},
    {"space_a/cabin_idle", adv_assets_space_a_cabin_idle__pieces, 1, 57, 57, 29, 56, 12, true},
    {"space_a/hard_land", adv_assets_space_a_hard_land__pieces, 1, 57, 57, 29, 56, 12, false},
    {"space_a/jet", adv_assets_space_a_jet__pieces, 1, 57, 57, 29, 56, 12, true},
    {"space_a/land", adv_assets_space_a_land__pieces, 1, 57, 57, 29, 56, 12, false},
    {"space_a/plant_flag", adv_assets_space_a_plant_flag__pieces, 1, 57, 57, 29, 56, 12, false},
    {"space_a/settlement_cheer", adv_assets_space_a_settlement_cheer__pieces, 1, 73, 73, 37, 72, 12, false},
    {"static/icon/fuel", adv_assets_static_icon_fuel__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/icon/hot-air", adv_assets_static_icon_hot_air__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/icon/oxygen", adv_assets_static_icon_oxygen__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/icon/spirit", adv_assets_static_icon_spirit__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/icon/stamina", adv_assets_static_icon_stamina__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/icon/steam", adv_assets_static_icon_steam__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/icon/warmth", adv_assets_static_icon_warmth__pieces, 1, 16, 16, 8, 8, 0, false},
    {"static/landmark/climb", adv_assets_static_landmark_climb__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/dive", adv_assets_static_landmark_dive__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/jump", adv_assets_static_landmark_jump__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/kiosk", adv_assets_static_landmark_kiosk__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/night", adv_assets_static_landmark_night__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/post", adv_assets_static_landmark_post__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/ski", adv_assets_static_landmark_ski__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/sky", adv_assets_static_landmark_sky__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/landmark/space", adv_assets_static_landmark_space__pieces, 1, 96, 96, 48, 88, 0, false},
    {"static/stamp/climb", adv_assets_static_stamp_climb__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/dive", adv_assets_static_stamp_dive__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/jump", adv_assets_static_stamp_jump__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/kiosk", adv_assets_static_stamp_kiosk__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/night", adv_assets_static_stamp_night__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/post", adv_assets_static_stamp_post__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/ski", adv_assets_static_stamp_ski__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/sky", adv_assets_static_stamp_sky__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/stamp/space", adv_assets_static_stamp_space__pieces, 1, 96, 96, 48, 48, 0, false},
    {"static/tiles/deep-sea/bubble-chain", adv_assets_static_tiles_deep_sea_bubble_chain__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/deep-sea/coral-fan", adv_assets_static_tiles_deep_sea_coral_fan__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/deep-sea/current-wave", adv_assets_static_tiles_deep_sea_current_wave__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/deep-sea/sea-rock", adv_assets_static_tiles_deep_sea_sea_rock__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/deep-sea/seaweed", adv_assets_static_tiles_deep_sea_seaweed__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/deep-sea/shell", adv_assets_static_tiles_deep_sea_shell__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/harbor/buoy", adv_assets_static_tiles_harbor_buoy__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/harbor/dock-planks", adv_assets_static_tiles_harbor_dock_planks__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/harbor/mooring-post", adv_assets_static_tiles_harbor_mooring_post__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/harbor/rope-coil", adv_assets_static_tiles_harbor_rope_coil__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/harbor/wave-crest", adv_assets_static_tiles_harbor_wave_crest__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/harbor/wave-line", adv_assets_static_tiles_harbor_wave_line__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/mountain/ice-crystals", adv_assets_static_tiles_mountain_ice_crystals__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/mountain/ridge", adv_assets_static_tiles_mountain_ridge__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/mountain/rock-face", adv_assets_static_tiles_mountain_rock_face__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/mountain/snow-drift", adv_assets_static_tiles_mountain_snow_drift__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/mountain/snowcap-rock", adv_assets_static_tiles_mountain_snowcap_rock__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/mountain/young-pine", adv_assets_static_tiles_mountain_young_pine__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/night-forest/branch", adv_assets_static_tiles_night_forest_branch__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/night-forest/fern", adv_assets_static_tiles_night_forest_fern__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/night-forest/fireflies", adv_assets_static_tiles_night_forest_fireflies__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/night-forest/mushrooms", adv_assets_static_tiles_night_forest_mushrooms__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/night-forest/shrub", adv_assets_static_tiles_night_forest_shrub__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/night-forest/tree-canopy", adv_assets_static_tiles_night_forest_tree_canopy__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/rail/mail-sign", adv_assets_static_tiles_rail_mail_sign__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/rail/rail-crossing", adv_assets_static_tiles_rail_rail_crossing__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/rail/rail-straight", adv_assets_static_tiles_rail_rail_straight__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/rail/telegraph-pole", adv_assets_static_tiles_rail_telegraph_pole__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/rail/trackside-grass", adv_assets_static_tiles_rail_trackside_grass__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/rail/wheat", adv_assets_static_tiles_rail_wheat__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/ski/gate-poles", adv_assets_static_tiles_ski_gate_poles__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/ski/small-spruce", adv_assets_static_tiles_ski_small_spruce__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/ski/snow-mound", adv_assets_static_tiles_ski_snow_mound__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/ski/snow-pine", adv_assets_static_tiles_ski_snow_pine__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/ski/snow-track", adv_assets_static_tiles_ski_snow_track__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/sky/bird-silhouette", adv_assets_static_tiles_sky_bird_silhouette__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/sky/cloud-chain", adv_assets_static_tiles_sky_cloud_chain__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/sky/cloud-large", adv_assets_static_tiles_sky_cloud_large__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/sky/cloud-small", adv_assets_static_tiles_sky_cloud_small__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/sky/feather", adv_assets_static_tiles_sky_feather__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/sky/wind-ribbon", adv_assets_static_tiles_sky_wind_ribbon__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/space/asteroid", adv_assets_static_tiles_space_asteroid__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/space/comet", adv_assets_static_tiles_space_comet__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/space/crater", adv_assets_static_tiles_space_crater__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/space/orbit-dots", adv_assets_static_tiles_space_orbit_dots__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/space/ring-planet", adv_assets_static_tiles_space_ring_planet__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/space/star-field", adv_assets_static_tiles_space_star_field__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/town/bunting", adv_assets_static_tiles_town_bunting__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/town/cobble-path", adv_assets_static_tiles_town_cobble_path__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/town/flowerbed", adv_assets_static_tiles_town_flowerbed__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/town/red-roof", adv_assets_static_tiles_town_red_roof__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/town/street-lamp", adv_assets_static_tiles_town_street_lamp__pieces, 1, 32, 32, 16, 31, 0, false},
    {"static/tiles/town/window-box", adv_assets_static_tiles_town_window_box__pieces, 1, 32, 32, 16, 31, 0, false},
    {"travel/cheer", adv_assets_travel_cheer__pieces, 1, 43, 72, 28, 72, 12, false},
    {"travel/idle", adv_assets_travel_idle__pieces, 1, 22, 48, 11, 48, 12, true},
    {"travel/sad", adv_assets_travel_sad__pieces, 1, 22, 48, 11, 48, 12, false},
    {"travel/turn_front_from_left", adv_assets_travel_turn_front_from_left__pieces, 1, 22, 48, 11, 48, 12, false},
    {"travel/turn_front_from_right", adv_assets_travel_turn_front_from_right__pieces, 1, 22, 48, 11, 48, 12, false},
    {"travel/turn_left", adv_assets_travel_turn_left__pieces, 1, 22, 48, 11, 48, 12, false},
    {"travel/turn_right", adv_assets_travel_turn_right__pieces, 1, 22, 48, 11, 48, 12, false},
    {"travel/walk_left", adv_assets_travel_walk_left__pieces, 1, 22, 48, 11, 48, 12, true},
    {"travel/walk_right", adv_assets_travel_walk_right__pieces, 1, 22, 48, 11, 48, 12, true},
    {"ui/bars/bottom", adv_assets_ui_bars_bottom__pieces, 1, 240, 30, 0, 0, 0, false},
    {"ui/bars/top", adv_assets_ui_bars_top__pieces, 1, 240, 32, 0, 0, 0, false},
    {"ui/cards/info/current/bottom", adv_assets_ui_cards_info_current_bottom__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/info/current/bottom-left", adv_assets_ui_cards_info_current_bottom_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/current/bottom-right", adv_assets_ui_cards_info_current_bottom_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/current/center", adv_assets_ui_cards_info_current_center__pieces, 1, 8, 8, 0, 0, 0, false},
    {"ui/cards/info/current/left", adv_assets_ui_cards_info_current_left__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/info/current/right", adv_assets_ui_cards_info_current_right__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/info/current/top", adv_assets_ui_cards_info_current_top__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/info/current/top-left", adv_assets_ui_cards_info_current_top_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/current/top-right", adv_assets_ui_cards_info_current_top_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/normal/bottom", adv_assets_ui_cards_info_normal_bottom__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/info/normal/bottom-left", adv_assets_ui_cards_info_normal_bottom_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/normal/bottom-right", adv_assets_ui_cards_info_normal_bottom_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/normal/center", adv_assets_ui_cards_info_normal_center__pieces, 1, 8, 8, 0, 0, 0, false},
    {"ui/cards/info/normal/left", adv_assets_ui_cards_info_normal_left__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/info/normal/right", adv_assets_ui_cards_info_normal_right__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/info/normal/top", adv_assets_ui_cards_info_normal_top__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/info/normal/top-left", adv_assets_ui_cards_info_normal_top_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/info/normal/top-right", adv_assets_ui_cards_info_normal_top_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/disabled/bottom", adv_assets_ui_cards_menu_disabled_bottom__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/menu/disabled/bottom-left", adv_assets_ui_cards_menu_disabled_bottom_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/disabled/bottom-right", adv_assets_ui_cards_menu_disabled_bottom_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/disabled/center", adv_assets_ui_cards_menu_disabled_center__pieces, 1, 8, 8, 0, 0, 0, false},
    {"ui/cards/menu/disabled/left", adv_assets_ui_cards_menu_disabled_left__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/menu/disabled/right", adv_assets_ui_cards_menu_disabled_right__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/menu/disabled/top", adv_assets_ui_cards_menu_disabled_top__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/menu/disabled/top-left", adv_assets_ui_cards_menu_disabled_top_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/disabled/top-right", adv_assets_ui_cards_menu_disabled_top_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/normal/bottom", adv_assets_ui_cards_menu_normal_bottom__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/menu/normal/bottom-left", adv_assets_ui_cards_menu_normal_bottom_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/normal/bottom-right", adv_assets_ui_cards_menu_normal_bottom_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/normal/center", adv_assets_ui_cards_menu_normal_center__pieces, 1, 8, 8, 0, 0, 0, false},
    {"ui/cards/menu/normal/left", adv_assets_ui_cards_menu_normal_left__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/menu/normal/right", adv_assets_ui_cards_menu_normal_right__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/menu/normal/top", adv_assets_ui_cards_menu_normal_top__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/menu/normal/top-left", adv_assets_ui_cards_menu_normal_top_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/normal/top-right", adv_assets_ui_cards_menu_normal_top_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/selected/bottom", adv_assets_ui_cards_menu_selected_bottom__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/menu/selected/bottom-left", adv_assets_ui_cards_menu_selected_bottom_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/selected/bottom-right", adv_assets_ui_cards_menu_selected_bottom_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/selected/center", adv_assets_ui_cards_menu_selected_center__pieces, 1, 8, 8, 0, 0, 0, false},
    {"ui/cards/menu/selected/left", adv_assets_ui_cards_menu_selected_left__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/menu/selected/right", adv_assets_ui_cards_menu_selected_right__pieces, 1, 12, 8, 0, 0, 0, false},
    {"ui/cards/menu/selected/top", adv_assets_ui_cards_menu_selected_top__pieces, 1, 8, 12, 0, 0, 0, false},
    {"ui/cards/menu/selected/top-left", adv_assets_ui_cards_menu_selected_top_left__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/menu/selected/top-right", adv_assets_ui_cards_menu_selected_top_right__pieces, 1, 12, 12, 0, 0, 0, false},
    {"ui/cards/popup/normal/bottom", adv_assets_ui_cards_popup_normal_bottom__pieces, 1, 8, 16, 0, 0, 0, false},
    {"ui/cards/popup/normal/bottom-left", adv_assets_ui_cards_popup_normal_bottom_left__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/cards/popup/normal/bottom-right", adv_assets_ui_cards_popup_normal_bottom_right__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/cards/popup/normal/center", adv_assets_ui_cards_popup_normal_center__pieces, 1, 8, 8, 0, 0, 0, false},
    {"ui/cards/popup/normal/left", adv_assets_ui_cards_popup_normal_left__pieces, 1, 16, 8, 0, 0, 0, false},
    {"ui/cards/popup/normal/right", adv_assets_ui_cards_popup_normal_right__pieces, 1, 16, 8, 0, 0, 0, false},
    {"ui/cards/popup/normal/top", adv_assets_ui_cards_popup_normal_top__pieces, 1, 8, 16, 0, 0, 0, false},
    {"ui/cards/popup/normal/top-left", adv_assets_ui_cards_popup_normal_top_left__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/cards/popup/normal/top-right", adv_assets_ui_cards_popup_normal_top_right__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/labels/new-record", adv_assets_ui_labels_new_record__pieces, 1, 72, 24, 0, 0, 0, false},
    {"ui/labels/placeholder", adv_assets_ui_labels_placeholder__pieces, 1, 88, 24, 0, 0, 0, false},
    {"ui/labels/test-no-record", adv_assets_ui_labels_test_no_record__pieces, 1, 96, 24, 0, 0, 0, false},
    {"ui/map/footprints-backward", adv_assets_ui_map_footprints_backward__pieces, 1, 10, 10, 0, 0, 0, false},
    {"ui/map/footprints-forward", adv_assets_ui_map_footprints_forward__pieces, 1, 10, 10, 0, 0, 0, false},
    {"ui/map/lock", adv_assets_ui_map_lock__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/map/stamp-bronze", adv_assets_ui_map_stamp_bronze__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/map/stamp-empty", adv_assets_ui_map_stamp_empty__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/map/stamp-gold", adv_assets_ui_map_stamp_gold__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/map/stamp-silver", adv_assets_ui_map_stamp_silver__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/map/station-current", adv_assets_ui_map_station_current__pieces, 1, 48, 40, 24, 24, 0, false},
    {"ui/map/station-locked", adv_assets_ui_map_station_locked__pieces, 1, 48, 40, 24, 24, 0, false},
    {"ui/map/station-unlocked", adv_assets_ui_map_station_unlocked__pieces, 1, 48, 40, 24, 24, 0, false},
    {"ui/map/temporary-position-marker", adv_assets_ui_map_temporary_position_marker__pieces, 1, 32, 20, 0, 0, 0, false},
    {"ui/numbers/20/0", adv_assets_ui_numbers_20_0__pieces, 1, 23, 20, 0, 0, 0, false},
    {"ui/numbers/20/1", adv_assets_ui_numbers_20_1__pieces, 1, 16, 20, 0, 0, 0, false},
    {"ui/numbers/20/2", adv_assets_ui_numbers_20_2__pieces, 1, 21, 20, 0, 0, 0, false},
    {"ui/numbers/20/3", adv_assets_ui_numbers_20_3__pieces, 1, 20, 20, 0, 0, 0, false},
    {"ui/numbers/20/4", adv_assets_ui_numbers_20_4__pieces, 1, 23, 20, 0, 0, 0, false},
    {"ui/numbers/20/5", adv_assets_ui_numbers_20_5__pieces, 1, 21, 20, 0, 0, 0, false},
    {"ui/numbers/20/6", adv_assets_ui_numbers_20_6__pieces, 1, 22, 20, 0, 0, 0, false},
    {"ui/numbers/20/7", adv_assets_ui_numbers_20_7__pieces, 1, 21, 20, 0, 0, 0, false},
    {"ui/numbers/20/8", adv_assets_ui_numbers_20_8__pieces, 1, 22, 20, 0, 0, 0, false},
    {"ui/numbers/20/9", adv_assets_ui_numbers_20_9__pieces, 1, 22, 20, 0, 0, 0, false},
    {"ui/numbers/20/m", adv_assets_ui_numbers_20_m__pieces, 1, 33, 20, 0, 0, 0, false},
    {"ui/numbers/20/plus", adv_assets_ui_numbers_20_plus__pieces, 1, 21, 20, 0, 0, 0, false},
    {"ui/numbers/36/0", adv_assets_ui_numbers_36_0__pieces, 1, 37, 36, 0, 0, 0, false},
    {"ui/numbers/36/1", adv_assets_ui_numbers_36_1__pieces, 1, 23, 36, 0, 0, 0, false},
    {"ui/numbers/36/2", adv_assets_ui_numbers_36_2__pieces, 1, 32, 36, 0, 0, 0, false},
    {"ui/numbers/36/3", adv_assets_ui_numbers_36_3__pieces, 1, 33, 36, 0, 0, 0, false},
    {"ui/numbers/36/4", adv_assets_ui_numbers_36_4__pieces, 1, 37, 36, 0, 0, 0, false},
    {"ui/numbers/36/5", adv_assets_ui_numbers_36_5__pieces, 1, 32, 36, 0, 0, 0, false},
    {"ui/numbers/36/6", adv_assets_ui_numbers_36_6__pieces, 1, 35, 36, 0, 0, 0, false},
    {"ui/numbers/36/7", adv_assets_ui_numbers_36_7__pieces, 1, 34, 36, 0, 0, 0, false},
    {"ui/numbers/36/8", adv_assets_ui_numbers_36_8__pieces, 1, 36, 36, 0, 0, 0, false},
    {"ui/numbers/36/9", adv_assets_ui_numbers_36_9__pieces, 1, 34, 36, 0, 0, 0, false},
    {"ui/numbers/36/m", adv_assets_ui_numbers_36_m__pieces, 1, 54, 36, 0, 0, 0, false},
    {"ui/numbers/36/plus", adv_assets_ui_numbers_36_plus__pieces, 1, 32, 36, 0, 0, 0, false},
    {"ui/passport/grid-current", adv_assets_ui_passport_grid_current__pieces, 1, 104, 52, 0, 0, 0, false},
    {"ui/passport/grid-normal", adv_assets_ui_passport_grid_normal__pieces, 1, 104, 52, 0, 0, 0, false},
    {"ui/passport/header", adv_assets_ui_passport_header__pieces, 1, 216, 24, 0, 0, 0, false},
    {"ui/passport/locked-mask", adv_assets_ui_passport_locked_mask__pieces, 1, 104, 52, 0, 0, 0, false},
    {"ui/passport/page-tile", adv_assets_ui_passport_page_tile__pieces, 1, 32, 32, 0, 0, 0, false},
    {"ui/resources/bar-frame", adv_assets_ui_resources_bar_frame__pieces, 1, 128, 10, 0, 0, 0, false},
    {"ui/resources/fill", adv_assets_ui_resources_fill__pieces, 1, 8, 6, 0, 0, 0, false},
    {"ui/resources/fill-left-cap", adv_assets_ui_resources_fill_left_cap__pieces, 1, 3, 10, 0, 0, 0, false},
    {"ui/resources/fill-right-cap", adv_assets_ui_resources_fill_right_cap__pieces, 1, 3, 10, 0, 0, 0, false},
    {"ui/resources/icons/fuel", adv_assets_ui_resources_icons_fuel__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/icons/hot-air", adv_assets_ui_resources_icons_hot_air__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/icons/oxygen", adv_assets_ui_resources_icons_oxygen__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/icons/spirit", adv_assets_ui_resources_icons_spirit__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/icons/stamina", adv_assets_ui_resources_icons_stamina__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/icons/steam", adv_assets_ui_resources_icons_steam__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/icons/temperature", adv_assets_ui_resources_icons_temperature__pieces, 1, 16, 16, 0, 0, 0, false},
    {"ui/resources/low-fill", adv_assets_ui_resources_low_fill__pieces, 1, 8, 6, 0, 0, 0, false},
    {"ui/resources/low-fill-left-cap", adv_assets_ui_resources_low_fill_left_cap__pieces, 1, 3, 10, 0, 0, 0, false},
    {"ui/resources/low-fill-right-cap", adv_assets_ui_resources_low_fill_right_cap__pieces, 1, 3, 10, 0, 0, 0, false},
    {"ui/stamps/ink-pad", adv_assets_ui_stamps_ink_pad__pieces, 1, 64, 64, 0, 0, 0, false},
    {"ui/wordmarks/climb", adv_assets_ui_wordmarks_climb__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/dive", adv_assets_ui_wordmarks_dive__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/jump", adv_assets_ui_wordmarks_jump__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/night", adv_assets_ui_wordmarks_night__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/post", adv_assets_ui_wordmarks_post__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/ski", adv_assets_ui_wordmarks_ski__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/sky", adv_assets_ui_wordmarks_sky__pieces, 1, 200, 80, 0, 0, 0, false},
    {"ui/wordmarks/space", adv_assets_ui_wordmarks_space__pieces, 1, 200, 80, 0, 0, 0, false},
};
const size_t adv_assets_catalog_count = sizeof(adv_assets_catalog)/sizeof(adv_assets_catalog[0]);
const adv_asset_record_t *adv_assets_find(const char *id) {
    if (!id) return NULL;
    for (size_t i=0; i<adv_assets_catalog_count; i++)
        if (!strcmp(id, adv_assets_catalog[i].id)) return &adv_assets_catalog[i];
    return NULL;
}
const adv_ninepatch_t adv_assets_patch_menu_normal = {{&adv_assets_ui_cards_info_normal_top_left__p0, &adv_assets_ui_cards_info_normal_bottom__p0, &adv_assets_ui_cards_info_normal_top_right__p0, &adv_assets_ui_cards_info_normal_left__p0, &adv_assets_ui_cards_info_normal_center__p0, &adv_assets_ui_cards_info_normal_left__p0, &adv_assets_ui_cards_info_normal_bottom_left__p0, &adv_assets_ui_cards_info_normal_bottom__p0, &adv_assets_ui_cards_info_normal_bottom_right__p0}};
const adv_ninepatch_t adv_assets_patch_menu_selected = {{&adv_assets_ui_cards_info_current_top_left__p0, &adv_assets_ui_cards_info_current_bottom__p0, &adv_assets_ui_cards_info_current_top_right__p0, &adv_assets_ui_cards_info_current_left__p0, &adv_assets_ui_cards_info_current_center__p0, &adv_assets_ui_cards_info_current_right__p0, &adv_assets_ui_cards_info_current_bottom_left__p0, &adv_assets_ui_cards_info_current_bottom__p0, &adv_assets_ui_cards_info_current_bottom_right__p0}};
const adv_ninepatch_t adv_assets_patch_menu_disabled = {{&adv_assets_ui_cards_info_normal_top_left__p0, &adv_assets_ui_cards_info_normal_bottom__p0, &adv_assets_ui_cards_info_normal_top_right__p0, &adv_assets_ui_cards_info_normal_left__p0, &adv_assets_ui_cards_info_normal_center__p0, &adv_assets_ui_cards_info_normal_left__p0, &adv_assets_ui_cards_info_normal_bottom_left__p0, &adv_assets_ui_cards_info_normal_bottom__p0, &adv_assets_ui_cards_info_normal_bottom_right__p0}};
const adv_ninepatch_t adv_assets_patch_info_normal = {{&adv_assets_ui_cards_info_normal_top_left__p0, &adv_assets_ui_cards_info_normal_bottom__p0, &adv_assets_ui_cards_info_normal_top_right__p0, &adv_assets_ui_cards_info_normal_left__p0, &adv_assets_ui_cards_info_normal_center__p0, &adv_assets_ui_cards_info_normal_left__p0, &adv_assets_ui_cards_info_normal_bottom_left__p0, &adv_assets_ui_cards_info_normal_bottom__p0, &adv_assets_ui_cards_info_normal_bottom_right__p0}};
const adv_ninepatch_t adv_assets_patch_info_current = {{&adv_assets_ui_cards_info_current_top_left__p0, &adv_assets_ui_cards_info_current_bottom__p0, &adv_assets_ui_cards_info_current_top_right__p0, &adv_assets_ui_cards_info_current_left__p0, &adv_assets_ui_cards_info_current_center__p0, &adv_assets_ui_cards_info_current_right__p0, &adv_assets_ui_cards_info_current_bottom_left__p0, &adv_assets_ui_cards_info_current_bottom__p0, &adv_assets_ui_cards_info_current_bottom_right__p0}};
const adv_ninepatch_t adv_assets_patch_popup_normal = {{&adv_assets_ui_cards_popup_normal_top_left__p0, &adv_assets_ui_cards_popup_normal_bottom__p0, &adv_assets_ui_cards_popup_normal_top_right__p0, &adv_assets_ui_cards_popup_normal_left__p0, &adv_assets_ui_cards_info_normal_center__p0, &adv_assets_ui_cards_popup_normal_left__p0, &adv_assets_ui_cards_popup_normal_bottom_left__p0, &adv_assets_ui_cards_popup_normal_bottom__p0, &adv_assets_ui_cards_popup_normal_bottom_right__p0}};
const adv_asset_digit_t adv_assets_digits_36[] = {
    {48, &adv_assets_catalog[297], 36},
    {49, &adv_assets_catalog[298], 22},
    {50, &adv_assets_catalog[299], 31},
    {51, &adv_assets_catalog[300], 32},
    {52, &adv_assets_catalog[301], 36},
    {53, &adv_assets_catalog[302], 31},
    {54, &adv_assets_catalog[303], 34},
    {55, &adv_assets_catalog[304], 33},
    {56, &adv_assets_catalog[305], 35},
    {57, &adv_assets_catalog[306], 33},
    {109, &adv_assets_catalog[307], 53},
    {43, &adv_assets_catalog[308], 31},
};
const adv_asset_digit_t adv_assets_digits_20[] = {
    {48, &adv_assets_catalog[285], 22},
    {49, &adv_assets_catalog[286], 15},
    {50, &adv_assets_catalog[287], 20},
    {51, &adv_assets_catalog[288], 19},
    {52, &adv_assets_catalog[289], 22},
    {53, &adv_assets_catalog[290], 20},
    {54, &adv_assets_catalog[291], 21},
    {55, &adv_assets_catalog[292], 20},
    {56, &adv_assets_catalog[293], 21},
    {57, &adv_assets_catalog[294], 21},
    {109, &adv_assets_catalog[295], 32},
    {43, &adv_assets_catalog[296], 20},
};
const uint16_t adv_assets_ui_palette[] = {8649, 15375, 17298, 25487, 35986, 38099, 40276, 44406, 45672, 46518, 48007, 54567, 56595, 57082, 63356, 65502};
const size_t adv_assets_ui_palette_count = 16;
