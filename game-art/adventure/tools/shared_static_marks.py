"""Single-ink postal seals and tiny, distinct resource pictograms."""
from shared_static_canvas import Canvas,locomotive

ICONS={'oxygen':'氧气','stamina':'体力','steam':'蒸汽','spirit':'精神',
       'warmth':'体温','hot-air':'热气','fuel':'燃料'}


def stamp(name,colors):
 c=Canvas(96,{key:'#FFFFFF' for key in colors});c.layer('postal-ring-no-lettering')
 c.ellipse((3,3,92,92),None,width=2)
 c.ellipse((7,7,88,88),None,width=1)
 for x in (12,84):c.ellipse((x-2,46,x+2,50),'ink',None)
 c.layer('station-pictogram')
 if name=='kiosk':
  c.poly([(31,29),(42,31),(48,35),(54,31),(65,29),(65,66),(54,66),(48,70),(42,66),(31,66)],None,width=2)
  c.line([(48,35),(48,68)],width=2)
  c.line([(35,38),(42,39),(42,56),(35,55),(35,38)],width=1)
  c.star(57,45,6,'ink',None)
  c.line([(53,58),(61,58)],width=2)
 elif name=='jump':
  for x,y in [(28,56),(39,43),(51,30)]:
   c.poly([(x,y+5),(x+7,y),(x+21,y),(x+15,y+5),(x,y+5),(x,y+14),(x+15,y+14),(x+21,y+9),(x+21,y)],None,width=2)
   c.line([(x+15,y+5),(x+15,y+14)],width=2)
 elif name=='dive':
  c.ellipse((43,24,53,34),None,width=2)
  c.arc((31,32,65,66),180,360,width=2)
  c.line([(31,48),(31,64),(65,64),(65,48)],width=2)
  c.rect((28,64,68,70),None,width=2,radius=2)
  c.ellipse((39,42,57,60),None,width=2)
  c.arc((43,46,53,56),190,280,width=1)
 elif name=='post':
  locomotive(c,29,35,1.15,line_only=True)
  c.line([(26,65),(72,65)],width=2)
  c.ellipse((31,25,37,29),None,width=1);c.ellipse((39,21,47,27),None,width=1)
 elif name=='night':
  c.rect((35,27,61,34),None,width=2,radius=2)
  c.poly([(36,34),(60,34),(64,40),(64,64),(59,69),(37,69),(32,64),(32,40)],None,width=2)
  c.line([(37,41),(36,46),(36,59)],width=1)
  c.star(45,47,5,'ink',None);c.star(55,59,4,'ink',None)
 elif name=='climb':
  c.poly([(25,68),(41,40),(48,51),(57,32),(72,68)],None,width=2)
  c.line([(33,54),(41,49),(46,55)],width=1)
  c.line([(52,43),(57,39),(63,46)],width=1)
  c.line([(57,32),(57,23),(69,27),(57,30)],width=2)
 elif name=='ski':
  c.line([(29,31),(29,66),(35,70)],width=2)
  c.line([(67,31),(67,66),(61,70)],width=2)
  c.rect((31,32,65,42),None,width=2)
  c.line([(35,49),(59,69)],width=3)
  c.line([(61,49),(37,69)],width=3)
 elif name=='sky':
  c.ellipse((30,24,66,61),None,width=2)
  c.ellipse((39,24,57,61),None,width=1)
  c.line([(48,25),(48,60)],width=1)
  c.line([(35,53),(40,65),(56,65),(61,53)],width=2)
  c.rect((39,65,57,73),None,width=2,radius=1)
 elif name=='space':
  c.poly([(48,24),(38,36),(38,62),(58,62),(58,36)],None,width=2)
  c.line([(40,35),(56,35)],width=2)
  c.ellipse((42,40,54,52),None,width=2)
  c.poly([(38,55),(30,65),(38,64)],None,width=2)
  c.poly([(58,55),(66,65),(58,64)],None,width=2)
  c.line([(42,64),(42,71),(48,68),(54,71),(54,64)],width=2)
  c.star(29,42,3,'ink',None);c.star(68,30,3,'ink',None)
 else:raise ValueError(name)
 return c


def icon(name,colors):
 c=Canvas(16,colors);c.layer('resource-'+name)
 if name=='oxygen':
  c.rect((5,1,10,3),'silver',width=1,radius=1)
  c.rect((4,3,11,14),'blue',width=1,radius=3)
  c.rect((6,6,9,10),'paper',None,radius=1)
  c.line([(6,4),(6,5)],'white',1)
 elif name=='stamina':
  c.poly([(8,1),(3,8),(7,8),(6,14),(13,5),(9,5),(11,1)],'gold',width=1)
  c.line([(8,3),(6,6)],'paper',1)
 elif name=='steam':
  c.poly([(2,10),(2,6),(4,4),(6,4),(7,2),(10,2),(12,5),(14,6),(14,10)],'paper',width=1)
  c.line([(4,12),(4,14)],'silver',1)
  c.line([(8,12),(8,14)],'silver',1)
  c.line([(12,12),(12,14)],'silver',1)
 elif name=='spirit':
  c.ellipse((2,2,12,13),'blue',width=1)
  c.poly([(7,2),(10,4),(9,8),(6,10),(11,12),(13,8),(12,3)],'gold',None)
  c.star(10,5,3,'paper',None)
 elif name=='warmth':
  c.rect((6,1,10,11),'paper',width=1,radius=2)
  c.ellipse((4,8,12,14),'accent',width=1)
  c.rect((8,4,8,11),'accent',None)
  c.line([(11,3),(13,3),(13,6)],'gold',1)
 elif name=='hot-air':
  c.poly([(8,1),(7,5),(4,6),(3,10),(5,14),(11,14),(13,10),(11,6),(10,8),(9,4)],'accent',width=1)
  c.poly([(8,8),(6,11),(7,13),(10,12),(9,10)],'gold',None)
 elif name=='fuel':
  c.rect((4,1,10,4),'gold',width=1,radius=1)
  c.line([(6,2),(8,2)],'ink',1)
  c.poly([(4,4),(10,4),(12,6),(12,14),(3,14),(3,5)],'teal',width=1)
  c.line([(5,7),(10,12)],'silver',1)
  c.line([(10,7),(5,12)],'silver',1)
  c.line([(10,4),(12,2),(14,3)],'bronze',2)
 else:raise ValueError(name)
 return c
