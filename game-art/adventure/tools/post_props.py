"""Native editable POST scenery; no character drawing and no generated animation."""
import json
import math
from PIL import Image
from shared_static_canvas import Canvas
from post_config import ART,GAME
from post_rig import sha


def build_props():
 colors=json.loads((ART/'ui/design/round3/01-passport/palette.json').read_text('utf-8'))
 assets=[];animations=[]
 def save(c,name,size,kind='prop',anchor=None,**extra):
  folder=GAME/('tiles' if kind=='tile' else 'props');folder.mkdir(parents=True,exist_ok=True)
  c.image=c.image.crop((0,0,*size));c.root.set('width',str(size[0]));c.root.set('height',str(size[1]))
  c.root.set('viewBox',f'0 0 {size[0]} {size[1]}');path=folder/(name+'.png');c.save(path)
  entry=dict(id=name,category=kind,path=path.relative_to(ART).as_posix(),size=list(size),
   source_svg=path.with_suffix('.svg').relative_to(ART).as_posix(),anchor=anchor or [size[0]//2,size[1]],
   sha256=sha(path),source_sha256=sha(path.with_suffix('.svg')),**extra)
  assets.append(entry);return entry
 # Locomotive points right. A transparent cab opening is kept for the driver.
 c=Canvas(96,colors);c.layer('underframe-and-boiler')
 c.rect((6,58,92,69),'bronze',width=2,radius=3)
 c.rect((39,31,86,59),'teal',width=3,radius=11)
 c.rect((75,29,85,58),'blue',width=2,radius=4)
 c.line([(45,36),(70,36)],'paper',2);c.line([(46,51),(73,51)],'line',2)
 c.rect((63,17,72,32),'bronze',width=2)
 c.poly([(59,14),(76,14),(73,20),(63,20)],'ink',width=1)
 c.rect((83,26,91,35),'gold',width=2,radius=3)
 c.rect((45,25,53,34),'gold',width=2,radius=3)
 c.poly([(88,56),(94,67),(84,67)],'accent',width=2)
 c.layer('cab-rear-roof-and-pillars')
 c.rect((6,7,9,55),'blue',width=2)
 c.rect((39,7,44,55),'blue',width=2)
 c.poly([(2,6),(7,1),(43,1),(48,6)],'accent',width=2)
 c.rect((9,49,42,62),'blue',width=2)
 c.rect((13,53,37,59),'teal',width=1)
 save(c,'locomotive-body',(96,88),anchor=[48,81],cab_window=[10,8,39,49],driver_chest=[25,49],
      roof_bottom_y=7,whistle_roof_anchor=[12,7],coordinate_space='locomotive top-left, native pixels; window right/bottom exclusive',
      composition_order=['wheel-cycle','locomotive-body','whistle-cord','NABO-halfbody','cab-foreground'])
 c=Canvas(96,colors);c.layer('cab-foreground-sill')
 c.rect((8,49,43,62),'blue',width=2);c.line([(11,49),(39,49)],'gold',2)
 c.rect((13,53,37,59),'teal',width=1)
 save(c,'cab-foreground',(96,88),anchor=[48,81])
 wheelpaths=[]
 for frame in range(4):
  c=Canvas(96,colors);c.layer('rotating-spokes')
  phase=frame*math.pi/2
  for x,r in ((23,10),(52,11),(78,9)):
   c.ellipse((x-r,69-r,x+r,69+r),'ink',width=1)
   c.ellipse((x-r+2,71-r,x+r-2,67+r),'bronze',width=1)
   for spoke in range(5):
    a=phase+spoke*2*math.pi/5
    c.line([(x,69),(round(x+math.cos(a)*(r-3)),round(69+math.sin(a)*(r-3)))],'paper',1)
   c.ellipse((x-2,67,x+2,71),'silver',width=1)
  c.layer('coupling-rod')
  dx,dy=round(5*math.cos(phase)),round(5*math.sin(phase))
  c.line([(23+dx,69+dy),(52+dx,69+dy),(78+dx,69+dy)],'silver',3)
  for x in (23,52,78):c.ellipse((x+dx-1,68+dy,x+dx+1,70+dy),'gold',None)
  wheelpaths.append(save(c,f'wheel-{frame:03d}',(96,88),anchor=[48,81])['path'])
 animations.append(dict(name='wheel-cycle',skin='post_props',facing='right',fps=12,loop=True,
  frames=wheelpaths,runtime_frames=wheelpaths,canvas=[96,88],runtime_canvas=[96,88],anchor=[48,81],runtime_anchor=[48,81]))
 c=Canvas(64,colors);c.layer('wagon-and-letter-mount')
 c.rect((3,12,58,32),'bronze',width=2,radius=2)
 for x in (7,20,33,46):c.line([(x,15),(x,29)],'line',1)
 c.rect((1,29,62,35),'ink',width=1)
 for x in (14,47):c.ellipse((x-6,31,x+6,43),'ink',width=1);c.ellipse((x-3,34,x+3,40),'silver',None)
 c.line([(1,33),(0,33)],'ink',2)
 save(c,'carriage',(64,48),anchor=[32,44],letter_mount=[32,9])
 for name,fill in zip(('red','blue','yellow','green','orange','gray'),('accent','blue','gold','teal','bronze','silver')):
  c=Canvas(32,colors);c.layer('envelope-'+name)
  c.rect((2,3,29,20),fill,width=2,radius=2)
  c.line([(3,19),(13,10),(18,10),(28,19)],'ink',1)
  c.poly([(3,4),(15,13),(28,4)],fill,width=1)
  c.rect((23,6,26,9),'paper',None)
  save(c,'envelope-'+name,(32,24),anchor=[16,12],semantic_color=name)
 # Separate periodic iron rails and periodic wood sleepers allow engine composition.
 for name in ('rails','sleepers','track-straight'):
  c=Canvas(32,colors);c.layer(name)
  if name!='rails':
   for x in (3,19):c.rect((x,2,x+7,29),'bronze',width=1);c.line([(x+2,5),(x+2,26)],'line',1)
  if name!='sleepers':
   for y in (7,23):c.rect((0,y,31,y+3),'ink',None);c.line([(0,y),(31,y)],'silver',1)
  save(c,name,(32,32),'tile',repeat_axes='x')
 c=Canvas(64,colors);c.layer('fork-ties')
 for x in range(5,61,11):
  c.line([(x,28),(x,46)],'bronze',4)
  y=36-round((x/63)**1.5*25);c.line([(x-3,y-8),(x+3,y+9)],'bronze',4)
 c.layer('fork-rails')
 for dy in (-6,6):
  c.line([(0,36+dy),(63,36+dy)],'ink',3);c.line([(0,35+dy),(63,35+dy)],'silver',1)
  pts=[(x,36+dy-round((x/63)**1.5*25)) for x in range(64)]
  c.line(pts,'ink',3);c.line([(x,y-1) for x,y in pts],'silver',1)
 c.ellipse((20,32,26,38),'gold',width=1)
 save(c,'track-fork',(64,56),'tile',anchor=[32,36],entry=[0,36],exits=[[63,36],[63,11]])
 c=Canvas(80,{k:'#FFFFFF' for k in colors});c.layer('single-tint-station-platform')
 c.rect((4,42,75,50),'ink',None,radius=2)
 for x in (14,62):c.rect((x,17,x+3,42),'ink',None)
 c.rect((7,4,72,25),None,width=2,radius=3)
 c.line([(15,18),(24,10),(32,18)],width=2)
 c.line([(38,11),(63,11)],width=2);c.line([(38,17),(57,17)],width=2)
 save(c,'station-platform-mask',(80,56),tintable=True,color_limit=2,sign_center=[40,14])
 c=Canvas(40,colors);c.layer('sheep-legs-and-face')
 for x in (10,25):c.rect((x,18,x+3,27),'ink',None)
 c.ellipse((3,8,32,22),'paper',width=1)
 for x,y in ((9,8),(17,6),(24,8)):c.ellipse((x-5,y-4,x+5,y+5),'white',width=1)
 c.ellipse((27,10,37,21),'muted',width=1);c.line([(31,12),(36,8)],'ink',2)
 c.ellipse((34,13,35,14),'white',None);c.line([(4,13),(1,10)],'paper',2)
 save(c,'sheep',(40,32),anchor=[20,28])
 c=Canvas(48,colors);c.layer('cow-silhouette')
 for x in (10,31):c.rect((x,23,x+4,33),'ink',None)
 c.rect((6,8,37,26),'paper',width=2,radius=7)
 c.poly([(13,9),(23,10),(25,16),(20,21),(12,18)],'ink',None)
 c.ellipse((32,9,45,25),'paper',width=2);c.ellipse((34,18,46,27),'seal',width=1)
 c.line([(34,10),(32,5)],'bronze',2);c.line([(41,10),(43,5)],'bronze',2)
 c.ellipse((40,13,41,14),'ink',None);c.line([(6,12),(2,18),(3,23)],'ink',2)
 save(c,'cow',(48,36),anchor=[24,34])
 c=Canvas(32,colors);c.layer('coal-chunks')
 for pts in ([(2,20),(7,10),(15,13),(19,22)],[(10,20),(16,6),(25,10),(29,22)],[(1,22),(8,17),(16,22)]):
  c.poly(pts,'ink',width=1);c.line(pts[:3],'blue',1)
 save(c,'coal-pile',(32,24),anchor=[16,23])
 c=Canvas(96,colors);c.layer('far-mountains-single-silhouette')
 c.poly([(0,30),(14,15),(23,22),(39,5),(50,19),(61,11),(79,25),(89,18),(95,30)],'blue',None)
 save(c,'far-mountains',(96,32),'tile',parallax='engine only; no baked translation',repeat_axes='x')
 return assets,animations
