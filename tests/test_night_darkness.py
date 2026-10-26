"""Validate the production row shader against independently evaluated ring geometry."""
import ctypes,math,random,subprocess,tempfile,unittest
from pathlib import Path
from host_tools import CC,SHARED_EXPORT,unload_library
ROOT=Path(__file__).resolve().parents[1]
PCT=(50,64,77,89,100,116);K=(16,13,10,8,6,4,2)
class Darkness(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();folder=Path(cls.tmp.name)
  code=(ROOT/'firmware/main/adv_ui_night.c').read_text('utf-8')
  # Compile the actual production implementation, without the rest of the UI.
  shader=code[code.index('typedef struct { int jx'):code.index('static void pines')]
  source=folder/'shader.c';source.write_text('#include <stdint.h>\n#include <stdlib.h>\n#include <stdbool.h>\n'+shader+
   '\nvoid host_dark(int jx,int jy,int r,int y,int x0,int x1,uint16_t *row){s_dark=(dark_t){jx,jy,r};dark_row(&s_dark,y,x0,x1,row);}\n','utf-8')
  library=folder/'shader.dll'
  subprocess.run([CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror',str(source),'-o',str(library)],check=True)
  cls.lib=ctypes.CDLL(str(library));cls.lib.host_dark.argtypes=[ctypes.c_int]*6+[ctypes.c_void_p]
 @classmethod
 def tearDownClass(cls):unload_library(cls.lib._handle);cls.tmp.cleanup()
 @staticmethod
 def reference(jx,jy,r,y,x,color):
  dy2=(y-jy)**2;level=6
  for i,pct in enumerate(PCT):
   radius=r*pct//100
   # The original integer shader starts its square-root at bit 14, so its
   # horizontal half-width is capped at 255 even for a full-screen burst.
   if dy2<radius*radius and abs(x-jx)<=min(255,math.isqrt(radius*radius-dy2)):
    level=i;break
  k=K[level]
  return (((color>>11)*k//16)<<11)|((((color>>5)&63)*k//16)<<5)|((color&31)*k//16)
 def compare(self,jx,jy,r,y,x0,x1,colors):
  pixels=(ctypes.c_uint16*(len(colors)+2))(0x1357,*colors,0x2468)
  self.lib.host_dark(jx,jy,r,y,x0,x1,ctypes.byref(pixels,2))
  expected=[self.reference(jx,jy,r,y,x,c) for x,c in zip(range(x0,x1),colors)]
  self.assertEqual(list(pixels)[1:-1],expected,(jx,jy,r,y,x0,x1))
  self.assertEqual((pixels[0],pixels[-1]),(0x1357,0x2468))
 def test_every_rgb565_color_for_every_brightness_factor(self):
  # Horizontal radius 100: choose positions strictly within each ring.
  for x in (0,56,70,83,94,108,140):
   for start in range(0,65536,256):
    for c in range(start,start+256):
     pixels=(ctypes.c_uint16*1)(c);self.lib.host_dark(0,0,100,0,x,x+1,pixels)
     self.assertEqual(pixels[0],self.reference(0,0,100,0,x,c))
 def test_clipping_tangencies_full_burst_and_random_screen_rows(self):
  rng=random.Random(4242)
  cases=[(80,185,r,y,0,320) for r in (0,1,34,120,184,1000) for y in (0,1,64,93,119,135,184,185,186,219,239)]
  cases +=[(rng.randint(-30,350),rng.randint(-20,260),rng.randint(1,220),rng.randrange(240),rng.randrange(160),rng.randrange(160,321)) for _ in range(600)]
  for jx,jy,r,y,x0,x1 in cases:self.compare(jx,jy,r,y,x0,x1,[rng.randrange(65536) for _ in range(x1-x0)])
