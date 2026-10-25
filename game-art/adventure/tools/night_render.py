"""Deterministic seated NIGHT source-pixel skeleton and upright held-jar constraint."""
import math
import numpy as np
from PIL import Image
from rig_render import translate,turn,transformed
from night_config import ART,PIVOTS,ORDER


def pose(name,index,count):
    phase=2*math.pi*index/count
    key={'torso':.4*math.sin(phase),'head_nod':0,'raise_amount':0,'bob':0}
    if name in ['move_left','move_right']:
        key['torso']=[0,-1.5,1.0,0][index]*(-1 if name=='move_right' else 1)
        key['bob']=[0,-1,-1,0][index]
    elif name in ['catch','lift_jar']:
        reach=([0,.55,1,.65,.2,0] if name=='catch' else [0,.45,.9,1,.7,0])[index]
        key.update(torso=35*reach,upper_l=145*reach,forearm_l=68*reach,
                   upper_r=-5*reach,forearm_r=-4*reach,raise_amount=reach)
    elif name=='yawn':
        y=[0,.3,.8,1,.55,0][index]
        key.update(torso=1.3*y,upper_r=112*y,forearm_r=114*y,head_nod=3*y)
    elif name=='cheer':
        y=[0,.25,.7,1,.9,.55,.15,0][index]
        key.update(torso=-2*y,upper_r=-53*y,forearm_r=-54*y,head_nod=0,bob=-2*y)
    elif name!='seat_idle':raise ValueError(name)
    return key


def render(rig,skin,facing,name,index,count,debug=False):
    view=rig['views'][skin][facing];parts=view['parts'];key=pose(name,index,count)
    root=translate(0,key['bob']);torso=root@turn(key['torso'],PIVOTS['torso'])
    hem=1.2*math.sin(2*math.pi*index/count) if name=='seat_idle' else 1.2*math.sin(math.pi*index/(count-1))
    matrices={'legs':root,'torso':torso,'hem':torso@turn(hem,PIVOTS['hem']),
              'collar':torso,'head':torso@translate(0,round(key['head_nod']))}
    matrices['expression']=matrices['head']
    for side in ['l','r']:
        matrices['upper_'+side]=torso@turn(key.get('upper_'+side,0),PIVOTS['upper_'+side])
        matrices['forearm_'+side]=matrices['upper_'+side]@turn(key.get('forearm_'+side,0),PIVOTS['forearm_'+side])
    # The jar remains upright, with a continuously changing support grip as the
    # hand turns from a side grip into a bottom support near the overhead catch.
    grip=matrices['forearm_l']@np.array([110.,188.,1.])
    destination=grip[:2]+[9,1-14*key['raise_amount']]
    matrices['jar']=translate(destination[0]-119,destination[1]-189)
    out=Image.new('RGBA',(256,256))
    layers=[]
    for part in ORDER:
        im=Image.open(ART/parts[part]['raster']).convert('RGBA')
        moved=transformed(im,matrices[part]);layers.append((part,moved));out.alpha_composite(moved)
    a=np.asarray(out)[:,:,3];ys,xs=np.where(a>=128)
    # Seated foot/root registration is constant even when upper body reaches.
    dy=224-int(ys.max()+1)
    final=Image.new('RGBA',(256,256));final.alpha_composite(out,(0,dy))
    jar_open=matrices['jar']@np.array([119.,171.,1.]);jar_open[1]+=dy
    report={'index':index,'pose':key,'core_bbox':[int(xs.min()),int(ys.min()+dy),int(xs.max()+1),224],
            'jar_opening':[float(jar_open[0]),float(jar_open[1])],
            'head_source_sha256':view['contract']['head_sha256'],
            'head_expression_transform_identical':bool(np.array_equal(matrices['head'],matrices['expression'])),
            'source_pixels_not_redrawn':True,'jar_world_rotation_degrees':0}
    report['ground_compensation_y']=dy
    report['head_matrix']=matrices['head'].tolist()
    ha=np.asarray(dict(layers)['head'])[:,:,3];hy,hx=np.where(ha>=128)
    report['head_core_bbox']=[int(hx.min()),int(hy.min()+dy),int(hx.max()+1),int(hy.max()+1+dy)]
    return (final,report,layers) if debug else (final,report)
