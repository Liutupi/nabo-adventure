"""Opaque span shortcuts must retain the original coverage and clipping pixels."""
import ctypes,random,subprocess,tempfile,unittest
from pathlib import Path
from host_tools import CC,SHARED_EXPORT,unload_library
ROOT=Path(__file__).resolve().parents[1];BOARD=ROOT/'firmware/main'
class ShapeRows(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();folder=Path(cls.tmp.name);source=folder/'rows.c'
  source.write_text('''#include "adv_gfx.h"
void tri(int cx,int cy,int size,int up,int color,int y,int x0,int x1,uint16_t *row){
 ag_op_t op={.x0=cx-size,.y0=cy-size,.x1=cx+size+1,.y1=cy+size+1};
 op.u.tri.cx=cx;op.u.tri.cy=cy;op.u.tri.size=size;op.u.tri.up=up;op.u.tri.color=color;
 ag_paint_tri(&op,y,x0,x1,row);
}
void rect(int x,int y,int w,int h,int color,int yy,int x0,int x1,uint16_t *row){
 ag_op_t op={.x0=x,.y0=y,.x1=x+w,.y1=y+h};
 op.u.rect.x=x;op.u.rect.y=y;op.u.rect.w=w;op.u.rect.h=h;op.u.rect.fill=color;op.u.rect.alpha=255;
 ag_paint_rect(&op,yy,x0,x1,row);
}
''','utf-8')
  libpath=folder/'shapes.dll'
  subprocess.run([CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror','-I',str(ROOT/'tests/adv_host'),'-I',str(BOARD),str(source),str(BOARD/'adv_shapes.c'),str(BOARD/'adv_text.c'),'-o',str(libpath)],check=True)
  cls.lib=ctypes.CDLL(str(libpath));cls.lib.tri.argtypes=[ctypes.c_int]*8+[ctypes.c_void_p];cls.lib.rect.argtypes=[ctypes.c_int]*8+[ctypes.c_void_p]
 @classmethod
 def tearDownClass(cls):unload_library(cls.lib._handle);cls.tmp.cleanup()
 @staticmethod
 def blend(dst,src,a):
  r=(((src>>11)-(dst>>11))*a//256)+(dst>>11)
  g=(((((src>>5)&63)-((dst>>5)&63))*a)//256)+((dst>>5)&63)
  b=(((src&31)-(dst&31))*a//256)+(dst&31)
  return (r<<11)|(g<<5)|b
 def test_triangle_rows_equal_original_formula_at_edges_and_clips(self):
  rng=random.Random(77)
  for _ in range(900):
   cx=rng.randrange(-200,520);cy=rng.randrange(-100,340);size=rng.randrange(1,251);up=rng.randrange(2);color=rng.randrange(65536)
   y=cy+rng.randrange(-size,size+1);x0=rng.randrange(160);x1=rng.randrange(160,321)
   before=[rng.randrange(65536) for _ in range(x1-x0)];pixels=(ctypes.c_uint16*(x1-x0+2))(0x1357,*before,0x2468)
   self.lib.tri(cx,cy,size,up,color,y,x0,x1,ctypes.byref(pixels,2));want=before[:];k=y-(cy-size//2)
   if 0<=k<size:
    half=(k if up else size-1-k)*16*2//3+8
    for x in range(max(x0,cx-size),min(x1,cx+size+1)):
     cov=max(0,min(16,half-abs((x-cx)*16)+8))*16
     if cov:want[x-x0]=self.blend(before[x-x0],color,cov)
   self.assertEqual(list(pixels)[1:-1],want,(cx,cy,size,up,y,x0,x1))
   self.assertEqual((pixels[0],pixels[-1]),(0x1357,0x2468))
 def test_solid_rectangle_rows_equal_original_integer_coverage(self):
  rng=random.Random(99)
  for _ in range(800):
   x=rng.randrange(-120,260);y=rng.randrange(-40,200);w=rng.randrange(1,361);h=rng.randrange(1,261);color=rng.randrange(65536)
   yy=y+rng.randrange(-2,h+3);x0=rng.randrange(160);x1=rng.randrange(160,321)
   before=[rng.randrange(65536) for _ in range(x1-x0)];pixels=(ctypes.c_uint16*(x1-x0+2))(0x1357,*before,0x2468)
   self.lib.rect(x,y,w,h,color,yy,x0,x1,ctypes.byref(pixels,2));want=before[:]
   if y<=yy<y+h:
    for xx in range(max(x0,x),min(x1,x+w)):want[xx-x0]=color
   self.assertEqual(list(pixels)[1:-1],want,(x,y,w,h,yy,x0,x1))
   self.assertEqual((pixels[0],pixels[-1]),(0x1357,0x2468))
