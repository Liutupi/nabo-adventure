// Read-only V2 diagnostics; test-mode ownership guards remain in adv_main.c.
#include <stdio.h>
#include "adv_climb_debug.h"
#include "adv_climb_v2.h"
void adv_climb_debug(const adv_model_t *model)
{
    if(!model->in_session||model->station!=5||!model->game){puts("@error CLIMB not active");return;}
    const adv_climb_v2_t *g=model->game;flockfile(stdout);
    printf("@climb {\"v2\":1,\"tick\":%u,\"score\":%u,\"res\":%d,\"over\":%d,\"row\":%d,\"lane\":%d,\"trav\":%d,\"ice\":%d,\"stun\":%d,\"combo\":%d,\"holds\":[",
           (unsigned)g->tick,(unsigned)g->score,(int)g->res,(int)g->over,(int)g->row,(int)g->lane,(int)g->trav,(int)g->ice,(int)g->stun,(int)g->combo);
    for(int r=g->row;r<=g->row+5;r++){const adv_climb_v2_row_t *o=&g->rows[r%CLIMB_V2_ROWS];printf("%s[%d,%d]",r>g->row?",":"",(int)o->h0,(int)o->h1);}
    printf("],\"rocks\":[");for(int i=0;i<CLIMB_V2_ROCKS;i++)printf("%s[%d,%d,%d,%d]",i?",":"",(int)g->rocks[i].on,(int)g->rocks[i].lane,(int)g->rocks[i].t,(int)g->rocks[i].y);
    puts("]}");funlockfile(stdout);
}
