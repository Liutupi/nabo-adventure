// Read-only NIGHT V2 diagnostics for tools/smoke_night.py; opening/injected input stays guarded by test mode.
#include <stdio.h>
#include "adv_night_debug.h"
#include "adv_night.h"

void adv_night_debug(const adv_model_t *model)
{
    if (!model->in_session || model->station != 4 || !model->game) { puts("@error NIGHT not active"); return; }
    const adv_night_t *g = model->game;
    flockfile(stdout);
    printf("@night {\"tick\":%u,\"score\":%u,\"res\":%d,\"over\":%d,\"light\":%d,\"x\":%d,\"gait\":%d,\"stun\":%d,\"swing\":%d,"
           "\"combo\":%d,\"caught\":%d,\"meter\":%d,\"need\":%d,\"bursts\":%d,\"event\":%d,\"whiffs\":%d,\"trips\":%d,\"owl_hits\":%d,"
           "\"moth_hits\":%d,\"last_swing\":%d,\"flies\":[",
           (unsigned)g->tick, (unsigned)g->score, (int)g->res, (int)g->over, (int)g->light, (int)g->x, (int)g->gait, (int)g->stun,
           (int)g->swing, (int)g->combo, (int)g->caught, (int)g->meter, adv_night_meter_full(g), (int)g->bursts, (int)g->event,
           (int)g->whiffs, (int)g->trips, (int)g->owl_hits, (int)g->moth_hits, (int)g->last_swing);
    int n = 0;
    for (int i = 0; i < ADV_NIGHT_FLIES; i++) {
        const adv_night_fly_t *f = &g->flies[i];
        if (f->type) printf("%s[%d,%d,%d,%d,%d,%d,%d]", n++ ? "," : "", (int)f->type, (int)f->x, (int)f->base_y, (int)f->amp, (int)f->ph, (int)f->freq, (int)f->vx);
    }
    printf("],\"moths\":[");
    n = 0;
    for (int i = 0; i < ADV_NIGHT_MOTHS; i++) if (g->moths[i].rr) printf("%s[%d,%d]", n++ ? "," : "", (int)g->moths[i].x, (int)g->moths[i].y);
    printf("],\"roots\":[");
    n = 0;
    for (int i = 0; i < ADV_NIGHT_ROOTS; i++) if (g->roots[i].state) printf("%s[%d,%d]", n++ ? "," : "", (int)g->roots[i].x, (int)g->roots[i].state);
    printf("],\"owls\":[");
    n = 0;
    for (int i = 0; i < ADV_NIGHT_OWLS; i++) if (g->owls[i].live) printf("%s[%d,%d]", n++ ? "," : "", (int)g->owls[i].tx, (int)g->owls[i].t);
    puts("]}");
    funlockfile(stdout);
}
