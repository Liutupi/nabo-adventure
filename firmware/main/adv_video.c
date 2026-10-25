#include "adv_video.h"
#include <stdlib.h>
#include <string.h>
#define PL_MPEG_IMPLEMENTATION
#define PLM_NO_STDIO
#define PLM_VIDEO_IP_ONLY
#include "third_party/pl_mpeg/pl_mpeg.h"

struct adv_video {
    plm_buffer_t *buffer;
    plm_video_t *decoder;
    plm_frame_t *image;
    unsigned frame,width,height;
    uint16_t fx[240];
    uint32_t fy[320];
};

adv_video_t *adv_video_open(const uint8_t *data,size_t size,unsigned w,unsigned h)
{
    // The fixed-size profile must be checked before the decoder can allocate.
    if(!data||size<12||w!=208||h!=272||memcmp(data,"\0\0\1\xb3",4)||
       (((unsigned)data[4]<<4)|(data[5]>>4))!=w||
       (((unsigned)(data[5]&15)<<8)|data[6])!=h)return NULL;
    adv_video_t *v=calloc(1,sizeof(*v));
    if(!v)return NULL;
    v->buffer=plm_buffer_create_with_memory((uint8_t *)data,size,FALSE);
    if(v->buffer)v->decoder=plm_video_create_with_buffer(v->buffer,FALSE);
    if(!v->decoder||!v->decoder->has_sequence_header){
        adv_video_close(v);return NULL;
    }
    v->width=w;v->height=h;
    for(unsigned x=0;x<240;x++)v->fx[x]=(uint16_t)(x*((w-1)<<8)/239);
    for(unsigned y=0;y<320;y++)v->fy[y]=y*((h-1)<<8)/319;
    return v;
}

void adv_video_close(adv_video_t *v)
{
    if(!v)return;
    if(v->decoder)plm_video_destroy(v->decoder);
    if(v->buffer)plm_buffer_destroy(v->buffer);
    free(v);
}

bool adv_video_next(adv_video_t *v)
{
    if(!v)return false;
    plm_frame_t *image=plm_video_decode(v->decoder);
    if(!image)return false;
    if(v->image)v->frame++;
    v->image=image;return true;
}

unsigned adv_video_frame(const adv_video_t *v){return v?v->frame:0;}
size_t adv_video_reference_bytes(const adv_video_t *v){return v?(size_t)v->width*v->height*3:0;}

static void vertical(const plm_plane_t *p,unsigned fy,uint16_t *values)
{
    unsigned y=fy>>8,ny=y+1<p->height?y+1:y,b=fy&255;
    const uint8_t *r0=p->data+y*p->width,*r1=p->data+ny*p->width;
    for(unsigned x=0;x<p->width;x++)values[x]=(uint16_t)((int)r0[x]*256+((int)r1[x]-r0[x])*(int)b);
}
static inline __attribute__((always_inline)) int horizontal(const uint16_t *values,unsigned x,unsigned nx,int fraction)
{
    int left=values[x];
    return (left*256+((int)values[nx]-left)*fraction+32768)>>16;
}
static int clamp(int v){return v<0?0:v>255?255:v;}
void adv_video_row(const void *ctx,int y,int x0,int x1,uint16_t *row)
{
    const adv_video_t *v=ctx;
    if(!v||!v->image||!row||y<0||y>=320||x0<0||x1>240||x0>=x1)return;
    unsigned fy=v->fy[y];const plm_frame_t *f=v->image;
    // Vertical-first separable bilinear sampling is algebraically identical.
    // Cache one native row per plane (832B stack), outside the output-pixel loop.
    uint16_t luma[208],blue[104],red[104];
    vertical(&f->y,fy,luma);vertical(&f->cb,fy>>1,blue);vertical(&f->cr,fy>>1,red);
    for(int x=x0;x<x1;x++){
        unsigned fx=v->fx[x],lx=fx>>8,cx=fx>>9;
        unsigned ln=lx+(lx<207),cn=cx+(cx<103);int la=fx&255,ca=(fx>>1)&255;
        int lum=horizontal(luma,lx,ln,la)-16;
        int cb=horizontal(blue,cx,cn,ca)-128,cr=horizontal(red,cx,cn,ca)-128;
        int r=clamp((298*lum+409*cr+128)>>8),g=clamp((298*lum-100*cb-208*cr+128)>>8);
        int b=clamp((298*lum+516*cb+128)>>8);
        row[x-x0]=(uint16_t)((r>>3)<<11|(g>>2)<<5|(b>>3));
    }
}
