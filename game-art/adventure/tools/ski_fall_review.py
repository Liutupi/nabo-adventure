"""Independent fall source/target contact, rigid-head and unchanged-other-poses audit."""
import json
import numpy as np
from PIL import Image,ImageChops
from ski_config import ART,RIG,PREVIEW,ROOT
from ski_render import render
from ski_rig import sha
from rig_render import transformed


def load(path):return Image.open(path).convert('RGBA')


def main():
    m=json.loads((ART/'ski-manifest.json').read_text('utf-8'));rig=json.loads((RIG/'rig.json').read_text('utf-8'))
    entry=next(e for e in m['animations'] if e['name']=='fall');raw=[];rt=[];frames=[];resampling=[]
    original_head=Image.new('RGBA',(256,256))
    for h in rig['common_head']:
        im=load(ART/h['path']);im.putalpha(ImageChops.multiply(im.getchannel('A'),Image.open(ART/h['local_alpha_mask'])))
        original_head.alpha_composite(im)
    for i in range(8):
        bitmap,report,layers,gear=render(rig,'ski_a','fall',i,True);raw.append(np.asarray(bitmap));runtime=load(ART/entry['runtime_frames'][i]);rt.append(np.asarray(runtime))
        assert np.array_equal(raw[-1],np.asarray(load(ART/entry['masters'][i])))
        matrix=np.array(report['head_matrix']);assert np.linalg.det(matrix[:2,:2])>0 and np.allclose(matrix[:2,:2].T@matrix[:2,:2],np.eye(2))
        inverse=np.linalg.inv(matrix)
        nearest=original_head.transform((256,256),Image.Transform.AFFINE,tuple(inverse[:2,:].reshape(-1)),resample=Image.Resampling.NEAREST)
        old=np.asarray(nearest);new=np.asarray(layers['head']);interior=(old[:,:,3]>=250)&(new[:,:,3]>=250)
        delta=np.abs(old[:,:,:3].astype(float)-new[:,:,:3].astype(float))
        resampling.append({'frame':i,'method':'bicubic rigid warp vs nearest source-pixel warp, opaque head interior',
                           'samples':int(interior.sum()),'rgb_mae_0_to_255':float(delta[interior].mean()),
                           'max_channel_delta':int(delta[interior].max())})
        contact=entry['fall_contract']['per_frame'][i];item={'index':i,'phase':contact['phase'],'pitch_degrees':contact['root']['rigid_pitch_degrees'],
            'root_shift':contact['root']['root_shift'],'formal_mitten_edge':report['snow_contact']['formal_edge'],'runtime_mitten_edge':contact['runtime_contact_edge'],
            'head_matrix':matrix.tolist(),'head_positive_rigid_determinant':float(np.linalg.det(matrix[:2,:2])),'no_clipping':report['no_clipping']}
        if i in (3,4):
            assert report['snow_contact']['active'] and report['snow_contact']['gap_px']==0
            assert report['snow_contact']['actual_mitten_alpha']>=128 and max(report['snow_contact']['gear_alpha_at_sample'].values())<128
            px=contact['runtime_sample_pixel'];rgba=runtime.getpixel(tuple(px))
            assert rgba[3]==255 and contact['runtime_mitten_alpha']>=128 and max(contact['runtime_gear_alpha'].values())<128
            assert contact['runtime_contact_edge']==[px[0],px[1]+1]
            item.update(runtime_sample=px,actual_runtime_RGBA=rgba,runtime_mitten_alpha=contact['runtime_mitten_alpha'],
                        runtime_gear_alpha=contact['runtime_gear_alpha'],snow_edge_gap_px=0)
        frames.append(item)
    assert np.array_equal(raw[0],raw[-1]) and np.array_equal(rt[0],rt[-1])
    straight=next(e for e in m['animations'] if e['skin']=='ski_a' and e['name']=='straight')
    assert np.array_equal(rt[0],np.asarray(load(ART/straight['runtime_frames'][0])))
    other={};old=ROOT/'private/quality-review/ski-fall-before/nonfall-master-sha.json'
    if old.is_file():
        baseline=json.loads(old.read_text('utf-8'));changed=[p for p,h in baseline.items() if sha(ART/p)!=h]
        assert not changed,changed;other={'nonfall_master_files_compared':len(baseline),'changed':changed}
    before=ROOT/'private/quality-review/ski-fall-before/ski-manifest.json'
    if before.is_file():
        oldmanifest=json.loads(before.read_text('utf-8'));old72=[e for e in oldmanifest['animations'] if e['target_height_px']==72]
        unchanged72=sum(sha(ART/p)==h for e in old72 for p,h in zip(e['runtime_frames'],e['runtime_sha256']))
        assert unchanged72==16;other['runtime72_files_unchanged']=unchanged72
    coordinates=[np.array(x['runtime_mitten_edge']) for x in frames]
    displacement=[float(np.linalg.norm(b-a)) for a,b in zip(coordinates,coordinates[1:])]
    result={'passed':True,'manifest_sha256':sha(ART/'ski-manifest.json'),'head_angles_degrees':[x['pitch_degrees'] for x in frames],
        'root_shifts':[x['root_shift'] for x in frames],'mitten_adjacent_displacements_runtime_px':displacement,
        'max_mitten_displacement_runtime_px':max(displacement),'neutral_endpoints_equal_saved_straight0':True,
        'snow_contact_frames':[3,4],'snow_contact_gap_runtime_px':0,'other_clips':other,'frames':frames,
        'rigid_resampling_measurements':resampling,
        'pose':'actual 62 degree rigid whole-body/face tumble, folded knees and25 degree lifted far board; mitten catches shared snow lip before pushing back to neutral',
        'pixel_boundary':'Original source files/RGB are unchanged. Fall rotates the head/neutral expression/cap/glasses together with bicubic resampling; source-to-target RGB equality is not claimed.',
        'logic_boundary':'native-size host slope playback and C decoder validation; no gameplay collision, input or hardware acceptance claimed'}
    (PREVIEW/'fall-repair.json').write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['frames']},indent=2))


if __name__=='__main__':main()
