# IDF reads component requirements once in CMake script mode, where
# CONFIGURE_DEPENDS is unavailable. The normal configure tracks new assets.
if(CMAKE_SCRIPT_MODE_FILE)
    file(GLOB ADV_GENERATED "${CMAKE_CURRENT_SOURCE_DIR}/generated/*.c")
else()
    file(GLOB ADV_GENERATED CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/generated/*.c")
endif()
idf_component_register(
    SRCS
        ${ADV_GENERATED}
        "adv_boot.c"
        "adv_boot_motion.c"
        "adv_video.c"
        "adv_ui_boot_video.c"
        "adv_demo.c"
        "adv_gfx.c"
        "adv_main.c"
        "adv_model.c"
        "adv_post.c"
        "adv_night.c"
        "adv_night_debug.c"
        "adv_ui_night.c"
        "adv_ui_post.c"
        "adv_ui_post_session.c"
        "adv_ninepatch.c"
        "adv_persist.c"
        "adv_shapes.c"
        "adv_sound.c"
        "adv_sprite.c"
        "adv_stations.c"
        "adv_text.c"
        "adv_ui.c"
        "adv_ui_animation.c"
        "adv_ui_art.c"
        "adv_ui_jump.c"
        "adv_ui_map.c"
        "adv_ui_session.c"
        "collection_font_12.c"
        "collection_font_16.c"
        "collection_font_18.c"
        "collection_model.c"
        "collection_portrait.c"
        "nabo_dive.c"
        "nabo_dive_anim.c"
        "nabo_dive_draw.c"
        "nabo_dive_model.c"
        "nabo_dive_render.c"
        "nabo_dive_sound.c"
        "nabo_dive_sprites.c"
        "nabo_dive_text.c"
        "nabo_jump_model.c"
        "nabo_jump_rig.c"
        "nabo_jump_sound.c"
        "nabo_jump_codec.c"
        "nabo_menu_font_16.c"
        "nabo_mono_font_12.c"
        "nabo_poster_font_28.c"
        "nabo_poster_font_48.c"
        "nabo_ui_font_18.c"
    INCLUDE_DIRS "." "generated"
    REQUIRES bsp lvgl esp_lcd esp_timer nvs_flash esp_rom
    EMBED_FILES "jump_sprites.bin" "jump_sounds.bin" "adv_boot_voice.wav"
)
target_compile_options(${COMPONENT_LIB} PRIVATE -O2)
