"""Rear-view joint posing with bound boot/board and mitten/pole contact points."""
import numpy as np
from PIL import Image,ImageChops
from rig_render import translate,turn,transformed
from ski_config import ART,GAME,RIG,CANVAS,pose


def render(rig,skin,name,index,debug=False):
 spec=rig['skins'][skin];parts=spec['parts'];key=pose(name,index)
 fall_report={}
 if name=='fall':
  from ski_fall import root
  root_matrix,fall_report=root(rig,skin,key,ART)
 else:root_matrix=translate(0,-key['lift'])
 matrices={'root':root_matrix}
 def matrix(part):
  if part not in matrices:
   p=parts[part];m=matrix(p['parent'])@turn(key['angles'].get(part,0),p['pivot'])
   if part=='torso':m=translate(0,key['torso_slump'])@m
   matrices[part]=m
  return matrices[part]
 layers={n:transformed(Image.open(ART/p['raster']).convert('RGBA'),matrix(n)) for n,p in parts.items()}
 neck=matrix('torso')@np.array([*rig['body_neck_bind'],1]);hx,hy=map(int,np.rint(neck[:2]-rig['head_reference_neck']))
 hm=matrix('torso')@translate(*np.subtract(rig['body_neck_bind'],rig['head_reference_neck'])) if name=='fall' else translate(hx,hy)
 head=Image.new('RGBA',CANVAS)
 for p in rig['common_head']:
  im=Image.open(ART/p['path']).convert('RGBA');im.putalpha(ImageChops.multiply(im.getchannel('A'),Image.open(ART/p['local_alpha_mask'])))
  if name=='fall':head.alpha_composite(im)
  else:head.alpha_composite(transformed(im,hm))
 if name=='fall':head=transformed(head,hm)
 layers['head']=head;goggles=Image.new('RGBA',CANVAS)
 if skin=='ski_a':goggles.alpha_composite(Image.open(RIG/'skins/ski_a/goggles.png'))
 layers['goggles']=transformed(goggles,hm)
 canvas=Image.new('RGBA',CANVAS);contact_reports={};gear_reports={};gear_layers={};factor=208/56
 def accessory(filename,point,anchor,parent,extra_angle=0):
  im=Image.open(GAME/'props'/filename).convert('RGBA');size=tuple(round(v*factor) for v in im.size)
  im=im.resize(size,Image.Resampling.LANCZOS);local=Image.new('RGBA',CANVAS)
  offset=(round(point[0]-anchor[0]*factor),round(point[1]-anchor[1]*factor));local.alpha_composite(im,offset)
  result=transformed(local,matrix(parent)@turn(extra_angle,point));return result
 if key['skis']:
  for side,word,anchor in (('l','left',[25,3]),('r','right',[7,3])):
   contact=spec['foot_contacts'][side];bone='shin_foot_'+side
   board=accessory('ski-'+word+'.png',contact,anchor,bone);canvas.alpha_composite(board);gear_layers['ski_'+side]=board
   world=matrix(bone)@np.array([*contact,1]);x,y=map(int,np.rint(world[:2]));region=(slice(max(0,y-4),min(256,y+5)),slice(max(0,x-4),min(256,x+5)))
   bootmask=np.asarray(layers[bone].getchannel('A'))>=128;boardmask=np.asarray(board.getchannel('A'))>=128
   overlap=int(np.count_nonzero(bootmask[region]&boardmask[region]))
   contact_reports[side]=dict(source_contact=contact,world_contact=[float(v) for v in world[:2]],
    same_parent_transform=True,actual_boot_board_overlap_pixels=overlap,board_bbox=board.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox())
 if key['poles']:
  for side in ('l','r'):
   grip=spec['grips'][side];bone='forearm_hand_'+side;counter=0
   if name=='finish':counter=-sum(key['angles'].get(n,0) for n in ('torso','upper_arm_'+side,bone))
   if name=='fall':
    desired=-22*key['fall_envelope'] if side=='l' else -80*key['fall_envelope']
    counter=desired-key['fall_pitch']-sum(key['angles'].get(n,0) for n in ('torso','upper_arm_'+side,bone))
   pole=accessory('pole.png',grip,[2,3],bone,counter)
   canvas.alpha_composite(pole);gear_layers['pole_'+side]=pole;world=matrix(bone)@np.array([*grip,1]);x,y=map(int,np.rint(world[:2]))
   region=(slice(max(0,y-5),min(256,y+6)),slice(max(0,x-5),min(256,x+6)))
   hand=np.asarray(layers[bone].getchannel('A'))>=128;pm=np.asarray(pole.getchannel('A'))>=128
   gear_reports[side]=dict(world_grip=[float(v) for v in world[:2]],actual_mitten_pole_overlap_pixels=int(np.count_nonzero(hand[region]&pm[region])),
    pole_bbox=pole.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox())
 for part in rig['draw_order']:
  if part=='head':
   # Keep retained identity RGB exact, including the alpha-253 source edge;
   # clothing behind it must not tint face pixels during compositing.
   hm_mask=layers[part].getchannel('A').point(lambda x:255 if x else 0)
   canvas.paste(layers[part],(0,0),hm_mask)
  else:canvas.alpha_composite(layers[part])
 box=canvas.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
 report=dict(frame=index,keyframe=key,head_translation=[hx,hy],head_rigid_integer_translation=name!='fall' or not key['fall_pitch'],
  head_matrix=hm.tolist(),head_and_expression_same_rigid_matrix=True,head_determinant=float(np.linalg.det(hm[:2,:2])),fall=fall_report,
  boot_board_contacts=contact_reports,mitten_pole_contacts=gear_reports,bbox=list(box),
  no_clipping=box[0]>0 and box[1]>0 and box[2]<256 and box[3]<256)
 if name=='fall':
  palm=np.asarray(layers['forearm_hand_r']);ys,xs=np.where(palm[:,:,3]>=128);bottom=int(ys.max())
  choices=sorted(int(x) for x in xs[ys==bottom]);cx=choices[0]
  report['snow_contact']={'active':index in (3,4),'feature':'right mitten outer edge','formal_edge':[cx,bottom+1],
   'sample_pixel':[cx,bottom],'actual_mitten_alpha':int(palm[bottom,cx,3]),
   'gear_alpha_at_sample':{n:int(np.asarray(im)[bottom,cx,3]) for n,im in gear_layers.items()},
   'ground_edge_y':234,'gap_px':234-(bottom+1)}
 return (canvas,report,layers,gear_layers) if debug else (canvas,report)
