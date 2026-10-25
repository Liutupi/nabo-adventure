"""32px native decorative tiles: six motifs per world, no baked gradients/glow."""
from shared_static_canvas import Canvas, pine
import math

TILESETS={
 'deep-sea':['seaweed','bubble-chain','coral-fan','shell','sea-rock','current-wave'],
 'harbor':['wave-line','wave-crest','dock-planks','rope-coil','mooring-post','buoy'],
 'town':['red-roof','street-lamp','flowerbed','cobble-path','window-box','bunting'],
 'rail':['rail-straight','rail-crossing','wheat','telegraph-pole','trackside-grass','mail-sign'],
 'night-forest':['tree-canopy','shrub','fern','fireflies','mushrooms','branch'],
 'mountain':['rock-face','snowcap-rock','snow-drift','ridge','young-pine','ice-crystals'],
 'ski':['snow-pine','gate-poles','snow-track','snow-drift','snow-mound','small-spruce'],
 'sky':['cloud-large','cloud-small','cloud-chain','wind-ribbon','feather','bird-silhouette'],
 'space':['star-field','asteroid','ring-planet','orbit-dots','comet','crater'],
}
REPEAT={'current-wave':'x','wave-line':'x','wind-ribbon':'x','dock-planks':'x','cobble-path':'xy',
        'rail-straight':'y','snow-track':'y','star-field':'xy','cloud-chain':'x'}
ALIASES={('ski','snow-drift'):('mountain','snow-drift')}


def leaf(c,points,color='teal'):
 c.poly(points,color,width=1)


def cloud(c,x=0,y=0,small=False):
 pts=[(3,23),(2,18),(5,14),(10,14),(11,9),(16,7),(21,10),(22,13),(27,14),(30,18),(29,23)]
 def project(points):
  if small:points=[(round(16+(a-16)*.76),round(17+(b-17)*.76)) for a,b in points]
  return [(a+x,b+y) for a,b in points]
 c.poly(project(pts),'paper',width=1)
 c.poly(project([(4,20),(28,20),(29,23),(3,23)]),'silver',None)
 c.line(project([(6,23),(27,23)]),'ink',1)


def tile(world,name,colors):
 c=Canvas(32,colors);c.layer(world+'-'+name)
 if name=='seaweed':
  for x,y in [(8,9),(16,4),(23,10)]:
   c.line([(x,29),(x-2,y+9),(x+2,y)],'teal',2)
   leaf(c,[(x-1,y+13),(x-7,y+8),(x-7,y+4),(x-2,y+8)])
   leaf(c,[(x,y+19),(x+6,y+15),(x+7,y+9),(x+2,y+13)])
 elif name=='bubble-chain':
  for x,y,r in [(10,23,5),(21,14,4),(13,5,3)]:
   c.ellipse((x-r,y-r,x+r,y+r),None,'blue',1)
   c.arc((x-r+1,y-r+1,x+r-1,y+r-1),190,285,'paper',1)
 elif name=='coral-fan':
  for points in [[(16,29),(16,15),(8,8),(8,3)],[(16,20),(24,12),(25,5)],
                 [(16,25),(5,19),(3,13)],[(16,15),(15,5)],[(21,16),(27,17),(28,12)]]:
   c.line(points,'ink',4);c.line(points,'accent',2)
  c.line([(10,29),(22,29)],'bronze',2)
 elif name=='shell':
  c.poly([(4,24),(3,17),(8,9),(16,6),(24,9),(29,17),(28,24),(19,27),(12,27)],'paper',width=1)
  for x,y in [(7,13),(12,9),(20,9),(26,14)]:c.line([(16,25),(x,y)],'line',1)
  c.rect((12,24,20,28),'gold',width=1,radius=2)
 elif name in ('sea-rock','rock-face'):
  c.poly([(3,25),(5,14),(14,7),(25,11),(29,24),(23,28),(10,28)],'muted',width=1)
  c.poly([(14,8),(20,17),(28,24),(23,27),(17,25)],'line',None)
  c.line([(6,22),(13,17),(20,19)],'shadow',1)
 elif name in ('current-wave','wave-line','wind-ribbon'):
  col='blue' if world=='deep-sea' else 'paper'
  for y,phase in [(11,0),(21,math.pi)]:
   pts=[(x,y if x<3 or x>28 else y+round(3*math.sin(4*math.pi*x/31+phase))) for x in range(32)]
   c.line(pts,col,2)
 elif name=='wave-crest':
  c.poly([(2,25),(5,17),(11,9),(18,6),(25,8),(28,14),(24,18),(19,16),(20,12),
          (15,13),(12,19),(16,24),(28,24),(29,28),(2,28)],'blue',width=1)
  c.line([(6,17),(12,10),(18,8),(24,10),(25,14)],'paper',2)
 elif name=='dock-planks':
  c.rect((0,6,31,26),'bronze',width=1)
  c.line([(1,13),(30,13)],'ink',1);c.line([(1,20),(30,20)],'ink',1)
  for x,y in [(9,8),(22,15),(13,22)]:
   c.line([(x,y),(x,y+3)],'muted',1);c.line([(x+3,y+2),(x+8,y+2)],'gold',1)
 elif name=='rope-coil':
  for r in (11,7,3):c.ellipse((16-r,16-r,16+r,16+r),None,'bronze',2)
  c.line([(24,24),(29,28),(27,29)],'ink',2);c.line([(25,24),(29,27)],'gold',1)
 elif name=='mooring-post':
  c.ellipse((6,23,27,29),'line',width=1)
  c.rect((12,8,22,25),'bronze',width=1)
  c.ellipse((11,5,23,11),'gold',width=1)
  c.line([(9,14),(25,17),(10,20),(25,22)],'paper',2)
 elif name=='buoy':
  c.line([(17,3),(17,10)],'ink',2)
  c.poly([(18,3),(27,6),(18,9)],'accent',width=1)
  c.poly([(10,11),(23,11),(26,22),(7,22)],'paper',width=1)
  c.rect((9,17,24,21),'accent',None)
  c.ellipse((5,21,28,27),'gold',width=1)
 elif name=='red-roof':
  c.rect((6,16,27,29),'paper',width=1)
  c.poly([(2,17),(16,4),(30,17)],'accent',width=1)
  c.line([(8,14),(24,14),(20,10),(11,10)],'bronze',1)
  c.rect((13,19,20,29),'blue',width=1)
  c.rect((6,21,10,25),'gold',width=1)
 elif name=='street-lamp':
  c.rect((14,13,17,29),'muted',width=1)
  c.rect((10,28,22,30),'bronze',width=1,radius=1)
  c.poly([(9,7),(22,7),(20,16),(11,16)],'select',width=1)
  c.poly([(8,7),(15,2),(23,7)],'ink',None)
  c.line([(15,8),(15,15)],'gold',1)
 elif name in ('flowerbed','window-box'):
  if name=='window-box':
   c.rect((5,3,27,24),'line',width=1)
   c.rect((8,6,24,21),'blue',width=1)
   c.line([(16,6),(16,21)],'paper',1);c.line([(8,14),(24,14)],'paper',1)
  c.rect((4,23,28,29),'bronze',width=1,radius=2)
  for x,y,col in [(9,17,'accent'),(17,15,'gold'),(25,18,'accent')]:
   c.line([(x,24),(x,y)],'teal',2)
   c.ellipse((x-3,y-3,x+3,y+3),col,width=1)
   c.rect((x,y,x+1,y+1),'paper',None)
 elif name=='cobble-path':
  for y in (3,12,21):
   for x in (2,12,22):c.rect((x,y,x+7,y+6),'line' if (x+y)%3 else 'shadow',width=1,radius=2)
 elif name=='bunting':
  c.line([(2,7),(15,10),(29,7)],'ink',1)
  for x,y,col in [(4,8,'accent'),(13,10,'blue'),(22,9,'gold')]:
   c.poly([(x,y),(x+6,y),(x+3,y+9)],col,width=1)
 elif name in ('rail-straight','rail-crossing'):
  for y in (6,22):c.rect((3,y,28,y+4),'bronze',width=1)
  for x in (9,21):
   c.line([(x,0 if name=='rail-straight' else 3),(x,31 if name=='rail-straight' else 29)],'ink',3)
   c.line([(x,0 if name=='rail-straight' else 3),(x,31 if name=='rail-straight' else 29)],'silver',1)
  if name=='rail-crossing':
   c.line([(3,8),(28,26)],'ink',4);c.line([(3,8),(28,26)],'silver',2)
 elif name=='wheat':
  for x,y in [(8,11),(16,4),(24,12)]:
   c.line([(x,29),(x,y)],'muted',1)
   for dy in (2,7,12):
    c.ellipse((x-5,y+dy,x,y+dy+5),'gold',None)
    c.ellipse((x,y+dy-2,x+5,y+dy+3),'select',None)
 elif name=='telegraph-pole':
  c.rect((14,3,17,30),'bronze',width=1)
  c.line([(5,8),(27,8)],'ink',3);c.line([(7,15),(25,15)],'ink',3)
  for x,y in [(7,5),(15,5),(24,5),(9,12),(22,12)]:c.rect((x,y,x+2,y+4),'silver',None)
 elif name in ('trackside-grass','shrub','fern'):
  for x,y in [(7,16),(15,8),(24,16)]:
   c.line([(16,29),(x,y)],'ink',2)
   leaf(c,[(x,y),(x-4,y-4),(x-4,y+3),(x+1,y+9)])
   leaf(c,[(x,y+7),(x+6,y+2),(x+4,y+11)])
  if name=='shrub':
   for x,y in [(10,22),(20,24)]:c.ellipse((x-2,y-2,x+2,y+2),'accent',None)
 elif name=='mail-sign':
  c.rect((14,17,17,29),'bronze',width=1)
  c.rect((4,5,28,19),'paper',width=1,radius=2)
  c.poly([(8,9),(24,9),(24,16),(8,16)],'select',width=1)
  c.line([(9,10),(16,14),(23,10)],'accent',1)
 elif name=='tree-canopy':
  c.rect((14,20,18,30),'bronze',width=1)
  c.poly([(2,16),(6,10),(11,9),(12,3),(19,3),(23,9),(28,11),(30,18),
          (25,24),(17,24),(12,27),(4,23)],'teal',width=1)
  c.poly([(20,10),(26,13),(28,18),(23,22),(15,23),(17,18)],'blue',None)
 elif name=='fireflies':
  for x,y in [(7,8),(23,13),(13,25)]:
   c.ellipse((x-2,y-2,x+2,y+2),'gold',None)
   c.line([(x-3,y-4),(x,y-1),(x+3,y-4)],'paper',1)
 elif name=='mushrooms':
  for x,y,r in [(11,16,8),(24,22,5)]:
   c.rect((x-2,y,x+2,29),'paper',width=1)
   c.ellipse((x-r,y-r,x+r,y+r//2),'accent',width=1)
   c.ellipse((x-3,y-4,x,y-1),'paper',None)
 elif name=='branch':
  c.line([(4,27),(14,17),(23,6)],'ink',4);c.line([(4,27),(14,17),(23,6)],'bronze',2)
  leaf(c,[(13,18),(6,13),(7,8),(13,11)])
  leaf(c,[(20,11),(25,11),(29,6),(24,6)])
 elif name in ('snowcap-rock','snow-mound'):
  c.poly([(3,27),(5,16),(14,8),(24,11),(29,26),(22,29),(10,29)],'blue',width=1)
  c.poly([(5,16),(14,8),(24,11),(27,18),(21,17),(17,20),(12,17),(8,20)],'white',width=1)
 elif name=='snow-drift':
  c.poly([(3,24),(7,19),(14,18),(19,13),(25,14),(29,20),(28,27),(5,28)],'white',width=1)
  c.line([(6,25),(13,23),(19,24),(26,20)],'silver',1)
 elif name=='ridge':
  c.poly([(2,27),(10,10),(16,17),(23,5),(30,27)],'blue',width=1)
  c.poly([(23,5),(18,15),(22,13),(25,16),(28,17)],'white',None)
  c.poly([(10,10),(7,16),(10,15),(13,17)],'paper',None)
 elif name in ('young-pine','snow-pine','small-spruce'):
  pine(c,16,3,27,name!='young-pine')
 elif name=='ice-crystals':
  for x,y,r in [(10,12,8),(23,24,6)]:
   c.line([(x-r,y),(x+r,y)],'silver',1);c.line([(x,y-r),(x,y+r)],'silver',1)
   c.line([(x-r+2,y-r+2),(x+r-2,y+r-2)],'paper',1)
   c.line([(x-r+2,y+r-2),(x+r-2,y-r+2)],'paper',1)
 elif name=='gate-poles':
  for x in (6,25):c.line([(x,4),(x,29)],'ink',2)
  c.poly([(7,7),(24,7),(24,17),(7,17)],'accent',width=1)
  c.line([(16,8),(16,16)],'paper',1)
 elif name=='snow-track':
  for x in (10,21):
   c.line([(x,0),(x,31)],'silver',2)
   c.line([(x+2,0),(x+2,31)],'white',1)
 elif name in ('cloud-large','cloud-small'):cloud(c,small=name=='cloud-small')
 elif name=='cloud-chain':
  for y,col in [(15,'paper'),(22,'silver')]:
   c.line([(x,y+round(3*math.cos(2*math.pi*x/31))) for x in range(32)],col,2)
 elif name=='feather':
  c.poly([(7,25),(9,15),(18,5),(25,3),(27,8),(21,20),(12,26)],'paper',width=1)
  c.line([(5,29),(23,8)],'bronze',1)
  for x,y in [(12,22),(16,17),(20,12)]:c.line([(x,y),(x+6,y-1)],'line',1)
 elif name=='bird-silhouette':
  c.poly([(3,10),(11,13),(16,18),(22,12),(29,9),(25,16),(18,23),(14,23),(7,17)],'ink',None)
 elif name=='star-field':
  c.star(9,9,5,'paper',None);c.star(25,23,4,'gold',None)
  for x,y in [(23,5),(6,26),(17,18)]:c.rect((x,y,x+1,y+1),'select',None)
 elif name in ('asteroid','crater'):
  c.poly([(4,12),(11,5),(22,4),(28,12),(27,24),(18,29),(8,26),(2,20)],'line',width=1)
  for box in [(8,9,15,16),(19,18,25,24),(8,22,12,26)]:c.ellipse(box,'muted',width=1)
  c.line([(17,7),(23,9)],'paper',1)
 elif name=='ring-planet':
  c.ellipse((7,5,26,25),'bronze',width=1)
  c.line([(8,13),(24,13)],'gold',2);c.line([(8,18),(24,18)],'line',2)
  c.arc((4,12,28,26),0,180,'ink',4);c.arc((4,12,28,26),0,180,'paper',2)
 elif name=='orbit-dots':
  c.arc((4,7,28,25),0,345,'blue',1)
  c.ellipse((12,12,19,19),'gold',width=1)
  for x,y in [(4,14),(22,22),(20,7)]:c.ellipse((x-2,y-2,x+2,y+2),'paper',None)
 elif name=='comet':
  c.poly([(7,24),(26,5),(23,17),(13,29)],'gold',width=1)
  c.poly([(10,23),(23,10),(17,23)],'paper',None)
  c.ellipse((4,20,14,30),'paper',width=1)
 else:raise ValueError((world,name))
 return c
