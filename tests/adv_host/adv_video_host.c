#include <stdlib.h>
#include <stddef.h>
#include <stdint.h>
static int calls,live,fail_after=-1;
#if defined(__GNUC__) && !defined(__clang__)
__attribute__((noipa))
#endif
static void *test_alloc(size_t n){
    int at=calls++;
    if(at==fail_after)return NULL;
    void *p=malloc(n);if(p)live++;return p;
}
static void test_free(void *p){if(p){live--;free(p);}}
#define PLM_MALLOC test_alloc
#define PLM_FREE test_free
#define PLM_REALLOC realloc
#include "../../firmware/main/adv_video.c"
int host_alloc_calls(void){return calls;}
int host_alloc_live(void){return live;}
void host_alloc_fail(int n){calls=0;fail_after=n;}
uint32_t host_yuv_hash(adv_video_t *v){
    uint32_t h=2166136261u;
    const plm_plane_t *planes[]={&v->image->y,&v->image->cb,&v->image->cr};
    for(int p=0;p<3;p++)for(unsigned i=0;i<planes[p]->width*planes[p]->height;i++)h=(h^planes[p]->data[i])*16777619u;
    return h;
}
static int reference_sample(const plm_plane_t *p,unsigned fx,unsigned fy){
 unsigned x=fx>>8,y=fy>>8,nx=x+1<p->width?x+1:x,ny=y+1<p->height?y+1:y;
 unsigned a=fx&255,b=fy&255;
 const uint8_t *r0=p->data+y*p->width,*r1=p->data+ny*p->width;
 unsigned top=r0[x]*(256-a)+r0[nx]*a,bottom=r1[x]*(256-a)+r1[nx]*a;
 return (int)((top*(256-b)+bottom*b+32768)>>16);
}
int host_reference_frame(adv_video_t *v){
 uint16_t actual[240];
 for(int y=0;y<320;y++){
  adv_video_row(v,y,0,240,actual);
  for(int x=0;x<240;x++){
   unsigned fx=v->fx[x],fy=v->fy[y];plm_frame_t *f=v->image;
   int lum=reference_sample(&f->y,fx,fy)-16,cb=reference_sample(&f->cb,fx>>1,fy>>1)-128,cr=reference_sample(&f->cr,fx>>1,fy>>1)-128;
   int r=clamp((298*lum+409*cr+128)>>8),g=clamp((298*lum-100*cb-208*cr+128)>>8),b=clamp((298*lum+516*cb+128)>>8);
   uint16_t expected=(uint16_t)((r>>3)<<11|(g>>2)<<5|(b>>3));
   if(actual[x]!=expected)return y*240+x+1;
  }
 }
 return 0;
}
