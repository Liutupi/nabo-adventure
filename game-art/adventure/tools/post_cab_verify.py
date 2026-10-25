"""Independent saved-image checks for cab clearance and a visibly attached cord."""
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from post_config import ART,GAME,PREVIEW
from post_rig import sha
from rig_render import translate,turn,transformed


def pixels(path):return np.asarray(Image.open(path).convert('RGBA'))


def check_cab(manifest,head,reports):
    cab=next(a for a in manifest['assets'] if a['id']=='post/props/locomotive-body')
    cord=next(e for e in manifest['animations'] if e['skin']=='post_props' and e['name']=='whistle-cord')
    whistle=next(e for e in manifest['animations'] if e['skin']=='post_a' and e['name']=='whistle')
    assert cab['size']==[96,88] and cab['driver_chest']==[25,49]
    assert cord['canvas']==cord['runtime_canvas']==[96,88]
    assert cord['anchor']==cord['runtime_anchor']==cab['anchor']==[48,81]
    assert len(cord['contacts'])==len(cord['runtime_frames'])==6 and not cord['loop'] and cord['fps']==12
    roof=np.array(cab['whistle_roof_anchor']);assert all(c['roof_anchor']==list(roof) for c in cord['contacts'])
    body=pixels(ART/cab['path']);front=pixels(GAME/'props/cab-foreground.png')
    hclear=[];contacts=[]
    for entry in manifest['animations']:
        if entry['skin']=='post_props' or entry['target_height_px']!=40:continue
        assert entry['runtime_canvas']==[36,40] and entry['runtime_anchor']==[22,40], 'Do not shrink actors to fit the cab'
        rr=entry['runtime_quantization'];box=rr['source_bbox'];origin=np.array(cab['driver_chest'])-entry['runtime_anchor']
        for i,report in enumerate(reports[entry['skin'],entry['name']]['frame_reports']):
            hx,hy=report['head_translation'];source=Image.new('RGBA',(256,256));source.alpha_composite(head,(hx,hy))
            alpha=np.asarray(source.crop(box).resize(tuple(entry['runtime_canvas']),Image.Resampling.LANCZOS))[:,:,3]>=128
            ys,xs=np.where(alpha);xs=xs+origin[0];ys=ys+origin[1];left,top,right,bottom=cab['cab_window']
            assert xs.min()>=left and xs.max()<right and ys.min()>=top and ys.max()<bottom,(entry['name'],i,'head outside window')
            assert not np.any(body[ys,xs,3]),(entry['name'],i,'solid cab geometry intersects head')
            assert not np.any(front[ys,xs,3]),(entry['name'],i,'foreground hides head')
            actor=pixels(ART/entry['runtime_frames'][i]);scene=pixels(PREVIEW/f'post_a-whistle-cab-{i:03d}.png') if entry is whistle else None
            if scene is not None:
                assert np.array_equal(scene[ys,xs,:3],actor[ys-origin[1],xs-origin[0],:3]),'Actual assembled head pixels changed'
            hclear.append(dict(skin=entry['skin'],name=entry['name'],frame=i,head_bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],
                               roof_clearance_px=int(ys.min()-cab['roof_bottom_y']),head_cab_overlap=0,head_hidden_by_foreground=0))
    union=set()
    rig=json.loads((ART/manifest['rig']).read_text('utf-8'));parts=rig['skins']['post_a']['parts']
    assert rig['cab_attachment']['driver_chest']==cab['driver_chest'] and rig['cab_attachment']['window']==cab['cab_window']
    assert rig['cab_attachment']['roof_pulley']==list(roof)
    assert parts['forearm_hand_l']['grip_point']==[96,161]
    glove=Image.open(ART/parts['forearm_hand_l']['raster']).convert('RGBA')
    assert np.asarray(glove)[161,96,3]>0,'Named source grip is not on the source glove'
    for i,(path,digest,source,source_hash,c) in enumerate(zip(cord['runtime_frames'],cord['runtime_sha256'],cord['source_svg'],cord['source_sha256'],cord['contacts'])):
        assert sha(ART/path)==digest and sha(ART/source)==source_hash
        data=pixels(ART/path);assert data.shape==(88,96,4) and set(np.unique(data[:,:,3]))=={0,255}
        union.update(map(tuple,data.reshape(-1,4)));assert len(union)<=cord['color_limit']<=16
        svg=ET.parse(ART/source).getroot();assert svg.attrib['viewBox']=='0 0 96 88'
        lines=svg.findall('.//{http://www.w3.org/2000/svg}polyline')
        report=reports['post_a','whistle']['frame_reports'][i];p=report['grip_xy']
        matrices={'root':translate(*report['keyframe']['shift'])}
        def matrix(name):
            if name not in matrices:
                part=parts[name];matrices[name]=matrix(part['parent'])@turn(report['keyframe']['angles'].get(name,0),part['pivot'])
            return matrices[name]
        transformed_grip=matrix('forearm_hand_l')@np.array([96,161,1])
        assert np.array_equal(np.rint(transformed_grip[:2]).astype(int),p),'Saved grip disagrees with source-bone transform'
        rr=whistle['runtime_quantization'];origin=np.array(cab['driver_chest'])-whistle['runtime_anchor']
        expected=[round(origin[k]+(p[k]-rr['source_bbox'][k])*rr['scale']) for k in range(2)]
        expected[1]=min(expected[1],cab['driver_chest'][1]-1)
        hand=np.array(c['hand_contact']);assert list(hand)==expected and c['source_grip_xy']==p
        endpoints=' '.join(f'{x},{y}' for x,y in (roof,hand))
        assert len(lines)==2 and all(line.attrib['points']==endpoints for line in lines)
        assert data[roof[1],roof[0],3]==255 and data[hand[1],hand[0],3]==255
        actor=pixels(ART/whistle['runtime_frames'][i]);local=hand-origin
        assert actor[local[1],local[0],3]==255,'Cord endpoint misses the actual opaque glove'
        glove_pose=transformed(glove,matrix('forearm_hand_l'));mask=glove_pose.getchannel('A')
        mask_data=np.asarray(mask);mask_data=np.array(mask_data);mask_data[160:]=0
        mask=Image.fromarray(mask_data).crop(rr['source_bbox']).resize(tuple(whistle['runtime_canvas']),Image.Resampling.LANCZOS)
        gx,gy=map(int,local);neighborhood=np.asarray(mask)[max(0,gy-1):gy+2,max(0,gx-1):gx+2]
        assert (neighborhood>=128).any(),'The contact is actor alpha, but not the transformed glove layer'
        assert c['state'] in ('rest','approach','grasp','pull','release')
        # Effective visible cord after actor and sill occlusion; a transparent
        # attachment hidden entirely behind the head would fail this test.
        actor_mask=np.zeros((88,96),bool);actor_mask[origin[1]:origin[1]+40,origin[0]:origin[0]+36]=actor[:,:,3]>0
        visible=(data[:,:,3]>0)&~actor_mask&~(front[:,:,3]>0)
        assert np.count_nonzero(visible)>12,(i,'cord not visible in actual composition')
        assert visible[roof[1],roof[0]],'Roof endpoint hidden'
        # A visible handle rim must remain within 2px of the glove contact.
        hx,hy=map(int,hand);rim=visible[max(0,hy-2):hy+3,max(0,hx-2):hx+3]
        assert rim.any(),(i,'no visible handle adjacent to glove')
        contacts.append(dict(frame=i,roof_anchor=list(map(int,roof)),hand_contact=list(map(int,hand)),
                             visible_cord_pixels=int(visible.sum()),endpoint_on_opaque_glove=True,visible_handle_rim=True))
    # The hand moves down from grasp to pull; the roof does not move.
    assert contacts[3]['hand_contact'][1]>contacts[2]['hand_contact'][1]
    result=dict(passed=True,actor_height_unchanged=40,head_clearance_frames=len(hclear),head_checks=hclear,
                cord_frames=6,cord_contacts=contacts,coordinate_space=cord['coordinate_space'],
                actual_composition='wheel/body/cord/actor/foreground',source_manifest_sha256=sha(ART/'post-manifest.json'))
    (PREVIEW/'cab-contact-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    return result
