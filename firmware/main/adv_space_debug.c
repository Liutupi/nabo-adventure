// Read-only V2 telemetry. No state injection, score writes or unlock commands.
#include <stdio.h>
#include "adv_space_debug.h"
#include "adv_space.h"
void adv_space_debug(const adv_model_t *m)
{
    if(!m->in_session||m->station!=8||!m->game){puts("@error SPACE not active");return;}
    const adv_space_t *g=m->game;flockfile(stdout);
    printf("@space {\"tick\":%u,\"score\":%u,\"res\":%d,\"over\":%d,\"mode\":%d,\"modeT\":%d,\"win\":%d,"
           "\"alt\":%d,\"v\":%d,\"x\":%d,\"vx\":%d,\"fuel\":%d,\"hull\":%d,\"heat\":%d,\"boostT\":%d,\"lastBoost\":%d,"
           "\"ign\":%d,\"sep\":%d,\"sepT\":%d,\"tli\":%d,\"tliT\":%d,\"tliHit\":%d,\"push\":%d,"
           "\"lx\":%d,\"ly\":%d,\"lvx\":%d,\"lvy\":%d,\"pad\":%d,\"landings\":%d,\"objs\":[",
           (unsigned)g->tick,(unsigned)g->score,(int)g->res,(int)g->over,(int)g->mode,(int)g->modeT,(int)g->win,
           (int)g->alt,(int)g->v,(int)g->x,(int)g->vx,(int)g->fuel,(int)g->hull,(int)g->heat,(int)g->boostT,(int)g->lastBoost,
           (int)g->ign,(int)g->sep,(int)g->sepT,(int)g->tli,(int)g->tliT,(int)g->tliHit,(int)g->push,
           (int)g->lx,(int)g->ly,(int)g->lvx,(int)g->lvy,(int)g->pad,(int)g->landings);
    int n=0;
    for(int i=0;i<ADV_SPACE_OBJS;i++)if(g->objs[i].type){const adv_space_obj_t *o=&g->objs[i];printf("%s[%d,%d,%d,%d,%d,%d]",n++?",":"",(int)o->type,(int)o->x,(int)o->y,(int)o->vx,(int)o->state,(int)o->done);}
    puts("]}");funlockfile(stdout);
}
