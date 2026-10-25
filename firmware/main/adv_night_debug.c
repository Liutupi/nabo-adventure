// Read-only diagnostics; opening/injected input remains guarded by test mode.
#include <stdio.h>
#include "adv_night_debug.h"
#include "adv_night.h"

void adv_night_debug(const adv_model_t *model)
{
    if(!model->in_session||model->station!=4||!model->game){puts("@error NIGHT not active");return;}
    const adv_night_t *g=model->game;
    flockfile(stdout);
    printf("@night {\"tick\":%u,\"score\":%u,\"res\":%d,\"over\":%d,\"lane\":%d,\"x\":%d,\"move\":%d,\"cooldown\":%d,\"cast\":%d,\"misses\":%d,\"target\":%d,\"interval\":%d,\"escaped\":%d,\"bugs\":[",
           (unsigned)g->tick,(unsigned)g->score,(int)g->res,(int)g->over,(int)g->lane,(int)g->x,(int)g->move,
           (int)g->cooldown,(int)g->cast,(int)g->misses,adv_night_target(g),adv_night_interval(g),(int)g->escaped);
    for(int i=0;i<ADV_NIGHT_CAP;i++){
        const adv_night_bug_t *b=&g->bugs[i];
        printf("%s[%d,%d,%d,%d,%d,%d]",i?",":"",(int)b->type,(int)b->x,(int)b->base_y,(int)b->lane,(int)b->phase,(int)b->age);
    }
    puts("]}");funlockfile(stdout);
}
