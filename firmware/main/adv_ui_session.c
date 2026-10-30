// The six landscape games share cards; each owns its themed play field.
#include "adv_ui_internal.h"
void ui_draw_session(ag_t *g,const adv_model_t *m)
{
    switch(m->station){
    case 3:ui_draw_post_v2_session(g,m);return;
    case 4:ui_draw_night_session(g,m);return;
    case 5:ui_draw_climb_v2_session(g,m);return;
    case 6:ui_draw_ski_session(g,m);return;
    case 7:ui_draw_sky_v2_session(g,m);return;
    case 8:ui_draw_space_session(g,m);return;
    default:ag_begin(g,UI_SCENE_TITLE);ui_paper(g);return;
    }
}
