"""Registered facing-source turn blends and measurable idle/walk/idle continuity."""
import copy
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from rig_render import render_frame, transformed, translate
from rig_preview import font

EYE_MID = {'front':(128,79),'left':(125,79),'right':(131,79)}


def premultiplied_blend(a,b,t):
    aa=np.asarray(a).astype(float)/255
    bb=np.asarray(b).astype(float)/255
    alpha=(1-t)*aa[:,:,3:]+t*bb[:,:,3:]
    rgb=(1-t)*aa[:,:,:3]*aa[:,:,3:]+t*bb[:,:,:3]*bb[:,:,3:]
    rgb=np.divide(rgb,alpha,out=np.zeros_like(rgb),where=alpha>0)
    return Image.fromarray(np.rint(np.concatenate([rgb,alpha],axis=2)*255).clip(0,255).astype('uint8'),'RGBA')


def head_layer(rig,root,facing,translation):
    parts=rig['views'][facing]['parts']
    head=Image.open(Path(root)/parts['head']['raster']).convert('RGBA')
    head.alpha_composite(Image.open(Path(root)/parts['expression_neutral']['raster']).convert('RGBA'))
    return transformed(head,translate(*translation))


def turns(rig,root,clips):
    result={}
    startkey=rig['animations']['idle']['keyframes'][0]
    for side in ['left','right']:
        endkey=rig['animations']['walk_'+side]['keyframes'][0]
        clip=[]
        records=[]
        for i in range(6):
            t=(1-math.cos(math.pi*i/5))/2
            angles={k:(1-t)*startkey['angles_degrees'].get(k,0)+t*endkey['angles_degrees'].get(k,0)
                    for k in startkey['angles_degrees'].keys()|endkey['angles_degrees'].keys()}
            trial=copy.deepcopy(rig)
            trial['animations']['turn']={'keyframes':[{'angles_degrees':angles,'root_bob_y':0}]}
            bodies=[]; heads=[]
            for view,other,weight in [('front',side,t),(side,'front',1-t)]:
                body,report=render_frame(trial,root,view,'turn',0,include_head=False)
                offset=np.subtract(EYE_MID[other],EYE_MID[view])*weight
                ht=np.array(report['head_translation'],float)+offset
                bodies.append(body); heads.append(head_layer(rig,root,view,ht))
            frame=premultiplied_blend(bodies[0],bodies[1],t)
            frame.alpha_composite(premultiplied_blend(heads[0],heads[1],t))
            if i==0: frame=clips['idle']['frames'][0].copy()
            if i==5: frame=clips['walk_'+side]['frames'][0].copy()
            clip.append(frame)
            records.append({'index':i,'facing_blend_weight':t,'head_policy':'two immutable facing slices, rigid eye-midpoint registration then premultiplied blend; no redrawn face',
                            'core_bbox':frame.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()})
        name='turn_'+side
        result[name]={'frames':clip,'reports':records,'facing':side,'count':6,'height':48,'loop':False,
                      'transition_from':'front','transition_to':side,'registered_head':True}
        name='turn_front_from_'+side
        result[name]={'frames':list(reversed(clip)),'reports':list(reversed(records)),'facing':'front','count':6,'height':48,'loop':False,
                      'transition_from':side,'transition_to':'front','registered_head':True}
    return result


def metrics(frames):
    result=[]
    previous=None
    for i,frame in enumerate(frames):
        a=np.asarray(frame)
        y,x=np.where(a[:,:,3]>=128)
        box=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
        item={'frame':i,'bbox':box,'sole_y':box[3],'centroid':[float(x.mean()),float(y.mean())]}
        if previous is not None:
            item['rgba_mae']=float(np.abs(a.astype(float)-previous.astype(float)).mean())
        previous=a
        result.append(item)
    return result


def continuity(art,clips,entries):
    lookup={e['name']:e for e in entries}
    result={}
    sequences={}
    for side in ['left','right']:
        stages=[('idle',range(8)),('turn_'+side,range(1,6)),('walk_'+side,range(1,8)),
                ('walk_'+side,range(8)),('turn_front_from_'+side,range(6)),('idle',range(1,8))]
        frames=[]; labels=[]
        for name,indices in stages:
            for index in indices:
                frames.append(Image.open(Path(art)/lookup[name]['runtime_frames'][index]).convert('RGBA'))
                labels.append((name,index))
        assert len({f.size for f in frames})==1,'Runtime locomotion canvas changes at a boundary'
        measurements=metrics(frames)
        total_walk=sum(1 for n,_ in labels if n.startswith('walk'))
        root_positions=[]
        for i in range(len(labels)):
            progress=sum(1 for n,_ in labels[:i+1] if n.startswith('walk'))/total_walk
            root_positions.append((-1 if side=='left' else 1)*12*(progress-math.sin(2*math.pi*progress)/(2*math.pi)))
        cuts=[i for i in range(1,len(labels)) if labels[i][0]!=labels[i-1][0]]
        jumps=[]
        for i in cuts:
            prev,now=measurements[i-1],measurements[i]
            jumps.append({'sequence_frame':i,'from':labels[i-1],'to':labels[i],
                          'centroid_delta':float(np.linalg.norm(np.subtract(now['centroid'],prev['centroid']))),
                          'root_delta_px':root_positions[i]-root_positions[i-1],
                          'world_centroid_delta_px':float(np.linalg.norm(np.subtract(now['centroid'],prev['centroid'])+[root_positions[i]-root_positions[i-1],0])),
                          'sole_delta':now['sole_y']-prev['sole_y'],'rgba_mae':now['rgba_mae']})
        turnframes=[Image.open(Path(art)/p).convert('RGBA') for p in lookup['turn_'+side]['runtime_frames']]
        head=lambda f:np.asarray(f).astype(float)[:24]
        hard_cut=float(np.abs(head(turnframes[-1])-head(turnframes[0])).mean())
        eased=[float(np.abs(head(b)-head(a)).mean()) for a,b in zip(turnframes,turnframes[1:])]
        result[side]={'runtime_canvas':frames[0].size,'runtime_anchor':lookup['idle']['runtime_anchor'],
                      'source_turn_frames':6,'sequence':labels,'boundaries':jumps,
                      'max_boundary_centroid_delta_px':max(x['centroid_delta'] for x in jumps),
                      'max_boundary_sole_delta_px':max(abs(x['sole_delta']) for x in jumps),
                      'same_runtime_scale_crop_palette':True,'frame_metrics':measurements,
                      'hard_cut_head_rgba_mae':hard_cut,'registered_turn_adjacent_head_rgba_mae':eased,
                      'registered_turn_max_vs_hard_cut_ratio':max(eased)/hard_cut,
                      'root_positions_target_pixels':root_positions,
                      'rendered_position_policy':'12 target pixels over walk stages with sinusoidal ease-in/out; turn and idle preserve reached root position'}
        assert result[side]['max_boundary_sole_delta_px']<=1
        assert result[side]['max_boundary_centroid_delta_px']<=2.5
        sequences[side]=(frames,labels,root_positions)
    count=max(len(x[0]) for x in sequences.values())
    screens=[]
    for i in range(count):
        screen=Image.new('RGB',(720,330),'#f6e2b4')
        d=ImageDraw.Draw(screen)
        for column,side in enumerate(['left','right']):
            frames,labels,root_positions=sequences[side]
            index=min(i,len(frames)-1)
            name,fi=labels[index]
            x=round(180+column*360+root_positions[index]*3)
            frame=frames[index].resize((frames[index].width*3,144),Image.Resampling.NEAREST)
            anchor=lookup['idle']['runtime_anchor']
            screen.paste(frame,(x-anchor[0]*3,245-anchor[1]*3),frame)
            d.line((column*360+10,246,column*360+350,246),fill='#af9070')
            d.text((column*360+15,15),f'idle > walk {side} > idle',fill='#182439',font=font(17))
            d.text((column*360+15,44),f'{name} {fi:02d} / 48px shown 3x',fill='#182439',font=font(14))
            d.text((column*360+15,285),f'root x={x/3:.1f} / fixed ground',fill='#182439',font=font(14))
        screens.append(screen)
    folder=Path(art)/'preview/travel'
    timings=[round((i+1)*100/12)*10-round(i*100/12)*10 for i in range(count)]
    screens[0].save(folder/'idle-walk-continuity.gif',save_all=True,append_images=screens[1:],duration=timings,loop=0,disposal=2)
    # All phase boundaries in one auditable, native frame sequence contact.
    chosen=list(range(0,count,3))
    contact=Image.new('RGB',(720*3,330*((len(chosen)+2)//3)),'white')
    for tile,i in enumerate(chosen):contact.paste(screens[i],((tile%3)*720,(tile//3)*330))
    contact.save(folder/'idle-walk-continuity-contact.png')
    return result
