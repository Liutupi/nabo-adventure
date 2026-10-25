#include "adv_post_view.h"
static adv_post_t game;
void host_post_new(uint32_t seed) {adv_post_start(&game,seed);}
void host_post_step(unsigned mask)
{
    adv_input_t in={0};uint8_t *p=(uint8_t *)&in;
    for(int i=0;i<7;i++)p[i]=(mask>>i)&1;
    adv_post_step(&game,&in);
}
void host_post_values(int64_t *out) {post_values(&game,out);}
adv_post_t *host_post_state(void) {return &game;}
int host_post_size(void) {return sizeof(game);}
