"""Ski-native editable gear/scenery and shared frozen snow references."""
import json
from PIL import Image
from shared_static_canvas import Canvas,pine
from post_rig import sha
from ski_config import ART,GAME


def build_props():
 colors=json.loads((ART/'ui/design/round3/01-passport/palette.json').read_text('utf-8'));assets=[]
 def save(c,name,size,category='prop',anchor=None,**extra):
  folder=GAME/('tiles' if category=='tile' else 'props');folder.mkdir(parents=True,exist_ok=True)
  c.image=c.image.crop((0,0,*size));c.root.set('width',str(size[0]));c.root.set('height',str(size[1]))
  c.root.set('viewBox',f'0 0 {size[0]} {size[1]}');path=folder/(name+'.png');c.save(path)
  a=dict(id='ski/'+('tiles/' if category=='tile' else 'props/')+name,path=path.relative_to(ART).as_posix(),
   source_svg=path.with_suffix('.svg').relative_to(ART).as_posix(),sha256=sha(path),source_sha256=sha(path.with_suffix('.svg')),
   size=list(size),anchor=anchor or [size[0]//2,size[1]],color_limit=16,**extra);assets.append(a);return a
 for side in ('left','right'):
  c=Canvas(32,colors);c.layer('separate-ski-no-lettering')
  points=[(29,2),(2,7)] if side=='left' else [(2,2),(29,7)]
  c.line(points,'ink',5);c.line(points,'accent' if side=='left' else 'gold',3)
  c.ellipse((0,5,5,9),'accent',width=1) if side=='left' else c.ellipse((27,5,31,9),'gold',width=1)
  anchor=[25,3] if side=='left' else [7,3]
  c.line([(anchor[0]-2,anchor[1]),(anchor[0]+2,anchor[1])],'paper',1)
  save(c,'ski-'+side,(32,10),anchor=anchor,attachment='boot sole; independently drawn geometry, character never mirrored')
 c=Canvas(24,colors);c.layer('pole-grip-shaft-and-basket')
 c.line([(2,2),(2,22)],'ink',1);c.line([(1,3),(3,3)],'bronze',3)
 c.line([(0,19),(4,19)],'blue',1);save(c,'pole',(5,24),anchor=[2,3])
 c=Canvas(64,colors);c.layer('large-snow-pine-trunk-and-tiered-branches')
 c.rect((28,44,35,59),'bronze',width=2)
 c.poly([(32,3),(21,19),(26,18),(14,32),(20,31),(8,49),(56,49),(44,31),(50,32),(39,18),(43,19)],'teal',width=2)
 c.poly([(32,5),(40,19),(37,18),(46,31),(41,30),(53,47),(33,47)],'blue',None)
 c.layer('snow-on-three-branch-tiers')
 c.poly([(32,4),(23,17),(30,14),(34,18),(40,18)],'white',width=1)
 c.poly([(26,18),(20,26),(27,25),(32,28),(37,25),(44,27),(39,20),(34,22),(30,19)],'white',width=1)
 c.poly([(20,31),(16,38),(22,37),(28,40),(34,37),(42,40),(48,40),(44,33),(39,35),(32,32),(26,35)],'white',width=1)
 c.ellipse((18,56,48,61),'white',width=1);save(c,'pine-large',(64,64),anchor=[32,60])
 for color in ('red','blue'):
  c=Canvas(64,colors);c.layer('gate-poles-and-banner-'+color)
  for x in (6,56):
   c.line([(x,3),(x+1,53)],'ink',3);c.line([(x,4),(x,51)],'silver',1)
   c.ellipse((x-3,50,x+4,54),'white',width=1)
  c.poly([(7,7),(56,7),(56,26),(7,24)],'accent' if color=='red' else 'blue',width=2)
  c.line([(12,11),(12,20)],'paper',2)
  c.line([(18,11),(18,20)],'paper',2)
  save(c,'gate-'+color,(64,56),anchor=[32,52],passage=[[9,29],[54,29]])
 c=Canvas(64,colors);c.layer('hot-cocoa-cabin')
 c.rect((12,25,54,53),'bronze',width=2)
 for y in (31,39,47):c.line([(14,y),(52,y)],'line',1)
 c.poly([(6,27),(30,7),(61,28)],'accent',width=2)
 c.poly([(9,24),(30,7),(56,24),(45,22),(35,15),(29,19),(22,18)],'white',width=1)
 c.rect((39,8,46,20),'ink',width=1);c.rect((22,33,36,54),'paper',width=2)
 c.rect((40,34,49,42),'gold',width=1);c.line([(44,35),(44,41)],'ink',1)
 c.layer('cocoa-mug-sign')
 c.rect((3,29,25,45),'paper',width=1,radius=2)
 c.rect((7,33,17,41),'bronze',width=1,radius=1);c.arc((15,34,21,39),270,450,'ink',1)
 c.line([(10,31),(9,28),(11,26)],'ink',1);c.line([(15,31),(14,28),(16,26)],'ink',1)
 c.ellipse((10,52,57,58),'white',width=1)
 save(c,'hot-cocoa-cabin',(64,64),anchor=[32,58],pickup_anchor=[30,54])
 c=Canvas(96,colors);c.layer('finish-arch-columns-and-snow')
 for x in (8,79):
  c.rect((x,16,x+8,75),'bronze',width=2)
  for y in range(22,74,12):c.rect((x+2,y,x+6,y+5),'accent',None)
  c.ellipse((x-3,72,x+13,78),'white',width=1)
 c.poly([(6,18),(21,6),(73,6),(90,18),(90,29),(6,29)],'paper',width=2)
 c.poly([(9,17),(22,8),(72,8),(86,17)],'white',None)
 c.layer('chequered-finish-no-text')
 for y in range(17,27,5):
  for x in range(20,78,6):
   if ((x-20)//6+(y-17)//5)%2==0:c.rect((x,y,x+5,y+4),'ink',None)
 save(c,'finish-arch',(96,88),anchor=[48,77],passage=[[19,64],[77,64]])
 # Direct references keep CLIMB and SKI genuinely on one frozen snow source.
 for name,path in (('snow-drift','map/tiles/mountain/snow-drift.png'),('snow-mogul','map/tiles/ski/snow-mound.png'),
                   ('pine-small','map/tiles/ski/snow-pine.png'),('snow-ground','map/tiles/mountain/ice-crystals.png')):
  p=ART/path;assets.append(dict(id='ski/shared/'+name,path=path,sha256=sha(p),size=list(Image.open(p).size),
   source_svg=p.with_suffix('.svg').relative_to(ART).as_posix(),source_sha256=sha(p.with_suffix('.svg')),
   anchor=[16,31],color_limit=16,shared_source=True,shared_manifest='shared-static-manifest.json'))
 return assets
