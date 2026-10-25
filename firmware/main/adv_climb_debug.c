// Read-only diagnostics; opening/injected input remains guarded by test mode.
#include <stdio.h>
#include "adv_climb_debug.h"
#include "adv_climb.h"

void adv_climb_debug(const adv_model_t *model)
{
    if(!model->in_session||model->station!=5||!model->game){puts("@error CLIMB not active");return;}
    const adv_climb_t *g=model->game;
    flockfile(stdout);
    printf("@climb {\"tick\":%u,\"score\":%u,\"res\":%d,\"over\":%d,\"row\":%d,\"side\":%d,\"act\":%d,\"press\":%d,\"queue\":%d,"
           "\"fragile\":%d,\"hits\":%d,\"misses\":%d,\"crumbles\":%d,\"canteens\":%d,\"holds\":[",
           (unsigned)g->tick,(unsigned)g->score,(int)g->res,(int)g->over,(int)g->row,(int)g->side,(int)g->act,(int)g->press,
           (int)g->queue,(int)g->fragile_t,(int)g->hits,(int)g->misses,(int)g->crumbles,(int)g->canteens);
    for(int r=g->row;r<=g->row+5;r++)printf("%s[%d,%d]",r>g->row?",":"",adv_climb_hold(g,r,0),adv_climb_hold(g,r,1));
    printf("],\"rocks\":[");
    for(int i=0;i<ADV_CLIMB_ROCKS;i++)printf("%s[%d,%d,%d]",i?",":"",(int)g->rocks[i].on,(int)g->rocks[i].side,(int)g->rocks[i].y);
    puts("]}");funlockfile(stdout);
}
