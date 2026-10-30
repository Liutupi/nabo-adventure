// Host shim for test_adv_model.py: drives the production shell model and prints its state with
// the same keys and order as view() in game-art/adventure/prototype/adv_core.js.
#include <stdio.h>
#include <string.h>
#include "adv_demo.h"
#include "adv_model.h"
#include "adv_space.h"

static adv_model_t model;

void host_new(uint32_t seed, const uint32_t *best, uint32_t seen, int volume, int brightness, int sleep, int speaker)
{
    adv_free(&model);
    cg_settings_t s = {volume, brightness, sleep, speaker != 0};
    adv_init(&model, seed, &s, best, seen);
}

int host_event(int button, int event) { return adv_event(&model, (adv_btn_t)button, (adv_ev_t)event); }
int host_steps(int n)
{
    int fx = 0;
    for (int i = 0; i < n; i++) fx |= adv_step(&model);
    return fx;
}
int host_legacy(uint32_t best) { return adv_legacy_done(&model, best); }
void host_test(int on) { model.test = on != 0; }
int host_cue(void) { return model.cue; }
int host_test_open(int station) {return adv_test_open(&model,station);}
int host_practice_open(void) {return adv_practice_open(&model);}
uint32_t host_awards(void) {return adv_earned(&model);}
int host_is_unlocked(int station) {return adv_unlocked(&model,station);}

int host_snapshot(char *out, int size)
{
    const adv_model_t *m = &model;
    int n = snprintf(out, size, "{\"page\":%d,\"cursor\":%d,\"kiosk\":%d,\"passport\":%d,\"from\":%d,"
                     "\"cfg\":[%d,%d,%d,%d,%d,%d,%d],\"best\":[",
                     m->page, m->cursor, m->kiosk, m->passport, m->passport_from, m->cfg.page,
                     m->cfg.settings_cursor, m->cfg.editing, m->cfg.settings.volume, m->cfg.settings.brightness,
                     m->cfg.settings.sleep_seconds, m->cfg.settings.speaker ? 1 : 0);
    for (int i = 0; i < ADV_STATIONS; i++) n += snprintf(out + n, size - n, "%s%u", i ? "," : "", (unsigned)m->best[i]);
    n += snprintf(out + n, size - n, "],\"seen\":%u,\"stamp\":%d,\"held\":%u,", (unsigned)m->seen, m->stamp, m->held);
    if (m->in_session)
        n += snprintf(out + n, size - n, "\"session\":[%d,%d,%d,%u,%d],", m->station, m->phase, m->t,
                      (unsigned)m->seed, m->record ? 1 : 0);
    else n += snprintf(out + n, size - n, "\"session\":null,");
    if (m->in_session && m->phase != ADV_TITLE) {
        if(m->station>=3){
            size_t words=adv_station[m->station].game->state_size/4;const int32_t *w=m->game;
            n+=snprintf(out+n,size-n,"\"game\":[");
            for(size_t i=0;i<words;i++)n+=snprintf(out+n,size-n,"%s%lld",i?",":"",i<3?(long long)(uint32_t)w[i]:(long long)w[i]);
            return n+snprintf(out+n,size-n,"]}");
        }
        const adv_demo_t *g = m->game;
        n += snprintf(out + n, size - n, "\"game\":[%d,%d,%d,%d,%u,%d,%d,%d,%d]}", g->p, g->v, g->zc, g->zh,
                      (unsigned)g->score, g->res, g->over, g->hit, g->miss);
    } else n += snprintf(out + n, size - n, "\"game\":null}");
    return n;
}
