#include "adv_ui_boot_video.h"
#include "adv_video.h"
#include "adv_boot_video_data.h"
static adv_video_t *s_video;
static bool s_movie,s_failed;
static uint32_t s_generation;
static ui_boot_video_stats_t s_stats;
static uint32_t s_elapsed;
static uint32_t s_advanced_at;
static unsigned target_frame(uint32_t elapsed)
{
    uint64_t target=((uint64_t)elapsed*ADV_BOOT_VIDEO_FPS+ADV_BOOT_VIDEO_FPS-1)/1000u;
    return target<ADV_BOOT_VIDEO_FRAMES?(unsigned)target:ADV_BOOT_VIDEO_FRAMES-1;
}
bool ui_boot_video_pending(uint32_t elapsed)
{
    return s_video&&s_movie&&!s_failed&&adv_video_frame(s_video)<target_frame(elapsed);
}
ui_boot_video_stats_t ui_boot_video_stats(void){return s_stats;}
void ui_boot_video_did_flush(void)
{
    if(!s_video||!s_movie)return;
    uint32_t frame=adv_video_frame(s_video);
    if(s_stats.frames&&frame==s_stats.last_frame)return;
    s_stats.skipped+=s_stats.frames?frame-s_stats.last_frame-1:frame;
    s_stats.frames++;s_stats.last_frame=frame;s_stats.elapsed_ms=s_elapsed;
}
void ui_boot_video_close(void)
{
    adv_video_close(s_video);s_video=NULL;s_failed=false;s_generation++;
}
bool ui_boot_video_draw(ag_t *g,uint32_t elapsed,bool initial)
{
    if(!ADV_BOOT_VIDEO_ENABLED)return false;
    if(s_video&&s_movie!=initial)ui_boot_video_close();
    if(!s_video&&!s_failed){
        s_movie=initial;
        if(initial){s_stats=(ui_boot_video_stats_t){0};s_advanced_at=UINT32_MAX;}
        const uint8_t *data=initial?adv_boot_video_movie:adv_boot_video_poster;
        size_t size=initial?adv_boot_video_movie_bytes:adv_boot_video_poster_bytes;
        s_video=adv_video_open(data,size,208,272);
        if(!s_video||!adv_video_next(s_video)){ui_boot_video_close();s_failed=true;}
    }
    if(s_video){
        s_elapsed=elapsed;
        // A slow I frame may leave the clock ahead. Submit every source pose;
        // catch up across flushes instead of decoding past unseen gestures.
        // A repeated full/capture redraw at the same timestamp must be stable.
        if(initial&&ui_boot_video_pending(elapsed)&&s_advanced_at!=elapsed){
            adv_video_next(s_video);s_advanced_at=elapsed;
        }
        for(unsigned b=0;b<ADV_VIDEO_BANDS;b++)
            ag_rows_region(g,adv_video_row,s_video,b*ADV_VIDEO_BAND_HEIGHT,(b+1)*ADV_VIDEO_BAND_HEIGHT,
                           s_generation*256+adv_video_band_generation(s_video,b));
    }else{
        ag_band(g,0,320,ag_rgb(9,18,43),ag_rgb(14,31,62));
    }
    return true;
}
