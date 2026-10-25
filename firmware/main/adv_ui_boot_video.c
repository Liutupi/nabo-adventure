#include "adv_ui_boot_video.h"
#include "adv_video.h"
#include "adv_boot_video_data.h"
static adv_video_t *s_video;
static bool s_movie,s_failed;
static uint32_t s_generation;
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
        const uint8_t *data=initial?adv_boot_video_movie:adv_boot_video_poster;
        size_t size=initial?adv_boot_video_movie_bytes:adv_boot_video_poster_bytes;
        s_video=adv_video_open(data,size,208,272);
        if(!s_video||!adv_video_next(s_video)){ui_boot_video_close();s_failed=true;}
    }
    if(s_video){
        unsigned target=initial?(unsigned)(((uint64_t)elapsed*ADV_BOOT_VIDEO_FPS+ADV_BOOT_VIDEO_FPS-1)/1000u):0;
        if(target>=ADV_BOOT_VIDEO_FRAMES)target=ADV_BOOT_VIDEO_FRAMES-1;
        while(adv_video_frame(s_video)<target&&s_movie){
            if(!adv_video_next(s_video))break;
        }
        ag_rows(g,adv_video_row,s_video,s_generation*256+adv_video_frame(s_video));
    }else{
        ag_band(g,0,320,ag_rgb(9,18,43),ag_rgb(14,31,62));
    }
    return true;
}
