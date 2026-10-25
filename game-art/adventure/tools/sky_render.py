"""SKY half-body source-pixel action transforms; control rope geometry follows palms."""
import math
import numpy as np
from PIL import Image,ImageDraw
from sky_config import ART,PIVOTS,ORDER
from rig_render import translate,turn,transformed


def pose(name,index,count):
    phase=2*math.pi*index/count
    key={'torso':0,'shift':[0,0],'scarf':2*math.sin(.4),'active_rope':None}
    if name=='idle':
        key.update(upper_l=.8*math.sin(phase),upper_r=-.8*math.sin(phase),scarf=2*math.sin(phase+.4))
    elif name=='heat':
        key.update(upper_l=[0,36,65,48,20,0][index],forearm_l=[0,66,100,90,45,0][index],
                   scarf=2*math.sin(.4)+[-0,2,4,3,1,0][index],active_rope='heat' if index in [1,2,3,4] else None)
    elif name=='vent':
        key.update(upper_r=-[0,32,62,44,18,0][index],forearm_r=-[0,66,100,87,42,0][index],
                   scarf=2*math.sin(.4)+[0,-2,-4,-3,-1,0][index],active_rope='vent' if index in [1,2,3,4] else None)
    elif name=='hit':
        r=[0,-1,.75,-.4,.15,0][index]
        key.update(torso=6*r,upper_l=-10*r,upper_r=10*r,forearm_l=-5*r,forearm_r=5*r,
                   scarf=2*math.sin(.4)+14*r,shift=[round(-2*r),0])
    elif name=='receive_stamp':
        r=[0,.65,1,0][index]
        key.update(upper_l=55*r,forearm_l=65*r,scarf=2*math.sin(.4)+3*r)
    elif name=='settlement_cheer':
        r=[0,.28,.76,1,.9,.55,.16,0][index]
        key.update(upper_l=65*r,forearm_l=100*r,upper_r=-8*r,forearm_r=-10*r,scarf=2*math.sin(.4)+6*r)
    else:raise ValueError(name)
    return key


def render(rig,skin,name,index,count,debug=False):
    key=pose(name,index,count);root=translate(*key['shift']);torso=root@turn(key['torso'],PIVOTS['torso'])
    matrices={'legs':root,'torso':torso,'scarf':torso@turn(key['scarf'],PIVOTS['scarf']),
              'collar':torso,'head':torso,'expression':torso}
    for side in ['l','r']:
        matrices['upper_'+side]=torso@turn(key.get('upper_'+side,0),PIVOTS['upper_'+side])
        matrices['forearm_'+side]=matrices['upper_'+side]@turn(key.get('forearm_'+side,0),PIVOTS['forearm_'+side])
    out=Image.new('RGBA',(256,256));layers=[]
    for namepart in ORDER:
        source=Image.open(ART/rig['skins'][skin]['parts'][namepart]['raster']).convert('RGBA')
        im=transformed(source,matrices[namepart]);out.alpha_composite(im);layers.append((namepart,im))
    if name!='settlement_cheer':
        alpha=out.getchannel('A');ImageDraw.Draw(alpha).rectangle((0,160,255,255),fill=0);out.putalpha(alpha)
    palms={side:(matrices['forearm_'+side]@np.array([96. if side=='l' else 159.,163.,1.]))[:2].tolist() for side in ['l','r']}
    report={'index':index,'pose':key,'palms':palms,'head_matrix':matrices['head'].tolist(),
            'head_expression_matrix_identical':True,'head_rgb_source':'rig/common/front/head.png','redrawn_face':False,
            'half_body_trim_y':None if name=='settlement_cheer' else 160,'rope_contact':key['active_rope'],
            'rope_endpoints':{'heat':palms['l'] if key['active_rope']=='heat' else [68.,138.],
                              'vent':palms['r'] if key['active_rope']=='vent' else [196.,138.]}}
    return (out,report,layers) if debug else (out,report)


def rope_frame(report,geometry):
    w,h=geometry['canvas'];bbox=geometry['bbox'];scale=geometry['scale']
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im);points={}
    for name,start in [('heat',(68,bbox[1])),('vent',(196,bbox[1]))]:
        end=report['rope_endpoints'][name]
        start=[round((start[0]-bbox[0])*scale),0]
        endpoint=[round((end[0]-bbox[0])*scale),round((end[1]-bbox[1])*scale)]
        d.line((*start,*endpoint),fill='#745b44' if name=='heat' else '#405b67',width=1)
        d.line((endpoint[0]-1,endpoint[1],endpoint[0]+1,endpoint[1]),fill='#303f49',width=1)
        points[name]={'start':start,'grip':endpoint}
    return im,points
