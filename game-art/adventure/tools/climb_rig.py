"""CLIMB costume pixel slices. Shared NABO head pixels are read-only inputs."""
import base64
import hashlib
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw
from rig_render import translate, turn, transformed

ART = Path(__file__).resolve().parents[1] / 'art'
RIG = ART / 'rig/climb'
CANVAS = (256, 256)
ANCHOR = (128, 224)
WINDOWS = {'front': (140, 0, 620, 887), 'left': (640, 0, 1140, 887), 'right': (1170, 0, 1700, 887)}
LOCKS = {'climb_a': '0956c8dff4d7907ff8f554c264cc5211fc0131474dc82ac51ace13feb845ddce',
         'climb_b': '03bca26ce30e62318631b82aa1014a835042be69a8f9e009527cc7e6ee01ec73'}
# Screen-left/right limbs in each independently supplied view. All vertices editable.
PARTS = {
    'forearm_hand_l': ('upper_arm_l', (97, 138), [(82,132),(108,132),(110,162),(98,174),(82,169)]),
    'forearm_hand_r': ('upper_arm_r', (161, 138), [(149,132),(178,131),(178,170),(155,174),(148,151)]),
    'upper_arm_l': ('torso', (106,107), [(95,100),(114,104),(109,143),(84,146),(85,123)]),
    'upper_arm_r': ('torso', (150,107), [(143,104),(163,100),(175,124),(178,146),(151,146)]),
    'shin_foot_l': ('thigh_l', (115,194), [(0,189),(129,189),(129,256),(0,256)]),
    'shin_foot_r': ('thigh_r', (141,194), [(126,189),(256,189),(256,256),(126,256)]),
    'thigh_l': ('root', (116,165), [(0,161),(129,161),(129,201),(0,201)]),
    'thigh_r': ('root', (140,165), [(126,161),(256,161),(256,201),(126,201)]),
    'jacket_flap': ('torso', (108,150), [(98,147),(112,147),(113,164),(98,164)]),
    'torso': ('root', (128,165), None),
}
ORDER = ['backpack','thigh_l','shin_foot_l','thigh_r','shin_foot_r','upper_arm_l','forearm_hand_l',
         'upper_arm_r','forearm_hand_r','torso','jacket_flap','head','expression_neutral']


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', 'utf-8')


def svg(image, name, metadata):
    buffer=io.BytesIO(); image.save(buffer,'PNG')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
            f'<title>{name}: source pixel slice</title><metadata>{json.dumps(metadata)}</metadata>'
            '<image width="256" height="256" href="data:image/png;base64,'+
            base64.b64encode(buffer.getvalue()).decode()+'"/></svg>\n')


def normalize(source, view):
    tile=source.crop(WINDOWS[view]); a=np.array(tile.getchannel('A'))
    a[a<16]=0; tile.putalpha(Image.fromarray(a))
    # Tiny disconnected generator fringe is not a body landmark. Require a
    # substantial row/column rather than letting a lone speck rescale the body.
    core=a>128; ys=np.flatnonzero(core.sum(axis=1)>20); xs=np.flatnonzero(core.sum(axis=0)>20)
    if len(ys)==0 or len(xs)==0: raise ValueError('Missing costume core')
    x0,x1,y0,y1=int(xs[0]),int(xs[-1])+1,int(ys[0]),int(ys[-1])+1
    box=(max(0,x0-2),max(0,y0-2),min(tile.width,x1+2),min(tile.height,y1+2))
    scale=208/(y1-y0); cut=tile.crop(box)
    sampled=cut.resize((round(cut.width*scale),round(cut.height*scale)),Image.Resampling.LANCZOS)
    xy=(128-round((x0+x1-2*box[0])*scale/2),224-round((y1-box[1])*scale))
    result=Image.new('RGBA',CANVAS);result.alpha_composite(sampled,xy)
    # Generated heads are discarded entirely; frozen shared heads cover the neck.
    alpha=np.array(result.getchannel('A'));alpha[:96]=0;result.putalpha(Image.fromarray(alpha))
    return result, {'window':WINDOWS[view],'core_bbox':[x0,y0,x1,y1],'scale':scale,'paste':xy}


def shared_head(view):
    path=ART/'rig/common'/view/'head.png';head=Image.open(path).convert('RGBA')
    pixels=np.array(head); y=np.arange(256)[:,None]
    # Remove only inherited travel green collar at the local mask's bottom.
    # RGB remains untouched, face/hair/hat above row94 remain byte-identical.
    cloth=(y>=94)&(pixels[:,:,1].astype(int)>pixels[:,:,0].astype(int)+7)&(pixels[:,:,2].astype(int)>pixels[:,:,0].astype(int)+7)
    pixels[:,:,3][cloth]=0;pixels[:,:,3][98:]=0
    head=Image.fromarray(pixels)
    expr=Image.open(ART/'rig/common'/view/'expression_neutral.png').convert('RGBA')
    return head,expr,{'frozen_head':path.relative_to(ART).as_posix(),'frozen_head_sha256':digest(path),
                      'local_alpha_trim':'row>=98 and inherited teal cloth at row>=94 only; no RGB edits'}


def build():
    result={'canvas':CANVAS,'anchor':ANCHOR,'draw_order':ORDER,'skins':{},'mirror_allowed':False,
            'contact_contract':{'space':'formal canvas pixels, same fixed (128,224) root as frames',
                'grip_contact':'outer two-pixel band of transformed hand source (source y>=156)',
                'foot_contact':'mean of transformed sole bottom two rows, at bottom pixel edge',
                'wall_support':'primary screen-left hand/foot for left wall; screen-right for right wall',
                'engine_policy':'translate runtime_contact - runtime_anchor with world root; never recenter sprite'},
            'representation':'SVG wrappers of immutable sampled pixel layers; no vector face redraw',
            'identity_source':'reference/nabo-idle-original.png','identity_sha256':digest(ART/'reference/nabo-idle-original.png')}
    for skin,lock in LOCKS.items():
        path=ART/f'games/climb/masters/{skin}-three-views.png'
        if digest(path)!=lock:raise ValueError('Costume master SHA changed')
        source=Image.open(path).convert('RGBA'); views={}
        for view in WINDOWS:
            image,sampling=normalize(source,view); remaining=Image.new('L',CANVAS,255);parts={}
            folder=RIG/skin/view;folder.mkdir(parents=True,exist_ok=True)
            image.save(folder/'costume-sampled.png')
            rgb=np.array(image);yy=np.arange(256)[:,None]
            gold=(rgb[:,:,0].astype(float)>rgb[:,:,1]*1.12)&(rgb[:,:,1].astype(float)>rgb[:,:,2]*1.15)&(yy>=98)&(yy<151)
            if skin=='climb_b':gold[:]=False
            bagmask=Image.fromarray((gold*255).astype('uint8'))
            backpack=image.copy();backpack.putalpha(ImageChops.multiply(image.getchannel('A'),bagmask))
            png=folder/'backpack.png';backpack.save(png)
            parts['backpack']={'parent':'root','pivot':[128,135],'path':png.relative_to(RIG).as_posix(),'sha256':digest(png)}
            (folder/'backpack.svg').write_text(svg(backpack,'backpack',{'source_sha256':lock,'view':view,'mask':'ochre source pixels only'}),'utf-8')
            remaining=ImageChops.subtract(remaining,bagmask)
            for name,(parent,pivot,poly) in PARTS.items():
                mask=Image.new('L',CANVAS)
                if poly:ImageDraw.Draw(mask).polygon(poly,fill=255)
                else:mask=remaining.copy()
                mask=ImageChops.multiply(mask,remaining);remaining=ImageChops.subtract(remaining,mask)
                d=ImageDraw.Draw(mask)
                # Source-only overlaps cover elbow/knee and root socket seams.
                if name.startswith(('upper_arm','forearm')):
                    e=(97,138) if name.endswith('_l') else (161,138)
                    d.ellipse((e[0]-8,e[1]-8,e[0]+8,e[1]+8),fill=255)
                elif name.startswith(('thigh','shin')):
                    e=(115,194) if name.endswith('_l') else (141,194)
                    d.ellipse((e[0]-12,e[1]-12,e[0]+12,e[1]+12),fill=255)
                if name=='torso':
                    for x,y in ((106,107),(150,107),(116,165),(140,165)):
                        radius=7 if y<150 else 11
                        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)
                mask=ImageChops.subtract(mask,bagmask)
                layer=image.copy();layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
                png=folder/f'{name}.png';layer.save(png);mask.save(folder/f'{name}-mask.png')
                metadata={'parent':parent,'pivot':pivot,'polygon':poly,'source_sha256':lock,'part':name,'view':view}
                (folder/f'{name}.svg').write_text(svg(layer,name,metadata),'utf-8')
                parts[name]={**metadata,'path':png.relative_to(RIG).as_posix(),'sha256':digest(png)}
            head,expr,provenance=shared_head(view)
            for name,layer,parent in [('head',head,'root'),('expression_neutral',expr,'head')]:
                png=folder/f'{name}.png';layer.save(png)
                metadata={'parent':parent,'pivot':[128,97],'part':name,'view':view,**provenance}
                (folder/f'{name}.svg').write_text(svg(layer,name,metadata),'utf-8')
                parts[name]={**metadata,'path':png.relative_to(RIG).as_posix(),'sha256':digest(png)}
            views[view]={'parts':parts,'sampling':sampling}
        result['skins'][skin]={'master':path.relative_to(ART).as_posix(),'master_sha256':lock,'views':views}
    write_json(RIG/'rig.json',result)
    write_json(ART/'games/climb/masters/generation.json',{
        'method':'built-in imagegen costume edit from original identity and approved hiker board; shared-head rig replaces generated head',
        'identity':result['identity_source'],'identity_sha256':result['identity_sha256'],
        'approved_design':'design/round1/v2/01-hiker-design-board.png',
        'outputs':[{'skin':s,'path':v['master'],'sha256':v['master_sha256'],
                    'prompt':f'games/climb/masters/{s}-prompt.txt'} for s,v in result['skins'].items()],
        'user_acceptance':'not claimed; production pose review is separate'})
    return result


def trim_detached_cloth(canvas):
    """Alpha-only removal of tiny detached cut-slice crumbs, never head pixels."""
    pixels=np.array(canvas);mask=pixels[:,:,3]>=128;seen=mask.copy();removed=0
    for y,x in zip(*np.where(mask)):
        if not seen[y,x]:continue
        stack=[(int(y),int(x))];seen[y,x]=False;component=[]
        while stack:
            yy,xx=stack.pop();component.append((yy,xx))
            for Y,X in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                if 0<=Y<256 and 0<=X<256 and seen[Y,X]:seen[Y,X]=False;stack.append((Y,X))
        if len(component)<=64 and min(p[0] for p in component)>=98:
            for yy,xx in component:
                pixels[yy,xx,3]=0;removed+=1
                for Y,X in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                    if 0<=Y<256 and 0<=X<256 and not mask[Y,X]:pixels[Y,X,3]=0
    return Image.fromarray(pixels),removed


def render(rig,skin,view,angles,offset=(0,0)):
    parts=rig['skins'][skin]['views'][view]['parts'];matrices={'root':translate(*offset)}
    def matrix(name):
        if name not in matrices:
            p=parts[name];matrices[name]=matrix(p['parent'])@turn(angles.get(name,0),p['pivot'])
        return matrices[name]
    canvas=Image.new('RGBA',CANVAS);hands={};feet={}
    for name in ORDER:
        image=Image.open(RIG/parts[name]['path']).convert('RGBA')
        moved=transformed(image,matrix(name));canvas.alpha_composite(moved)
        if name.startswith('forearm_hand'):
            source=np.array(image);source[:156,:,3]=0
            silhouette=np.array(transformed(Image.fromarray(source),matrix(name)))[:,:,3]>=128
            ys,xs=np.where(silhouette)
            if len(xs):
                edge=xs.min() if view=='left' else xs.max() if view=='right' else float(xs.mean())
                selected=xs<=edge+2 if view=='left' else xs>=edge-2 if view=='right' else np.ones(xs.shape,dtype=bool)
                hands[name[-1]]=[round(float(xs[selected].mean())),round(float(ys[selected].mean()))]
        elif name.startswith('shin_foot'):
            ys,xs=np.where(np.array(moved)[:,:,3]>=128);selected=ys>=ys.max()-1
            feet[name[-1]]=[round(float(xs[selected].mean())),round(float(ys[selected].mean()))+1]
    if not np.array_equal(matrix('head'),matrix('expression_neutral')) or not np.array_equal(matrix('head')[:2,:2],np.eye(2)):
        raise ValueError('Shared head must have a rigid integer translation only')
    canvas,removed=trim_detached_cloth(canvas)
    # Fixed contractual root; do not independently recenter any frame or head.
    return canvas,{'view':view,'angles':angles,'head_translation':list(offset),'head_rigid':True,
                   'hand_contacts':hands,'foot_contacts':feet,
                   'alpha_only_detached_cloth_pixels_removed':removed,'frozen_head_sha256':parts['head']['frozen_head_sha256'],
                   'core_bbox':canvas.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()}
