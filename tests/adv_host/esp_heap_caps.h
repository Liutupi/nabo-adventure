#pragma once
#include <stdlib.h>
#define MALLOC_CAP_DMA 1
#define MALLOC_CAP_INTERNAL 2
extern size_t host_caps_fail_size;
static inline void *heap_caps_malloc(size_t n,int caps)
{
    (void)caps;
    if(n==host_caps_fail_size){host_caps_fail_size=0;return NULL;}
    return malloc(n);
}
