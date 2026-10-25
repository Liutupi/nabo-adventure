"""Validate saved pixel layers, formal/runtime delivery and actual transition endpoints."""
import base64
import io
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from build_travel_rig import ART,RIG,EXPECTED_SOURCE,digest


def colours(images):
    return len(set().union(*(set(map(tuple,np.asarray(f).reshape((-1,4)))) for f in images)))


def verify():
    rig=json.loads((RIG/'rig.json').read_text('utf-8'))
    manifest=json.loads((ART/'manifest.json').read_text('utf-8'))
    assert digest(RIG/rig['source'])==rig['source_sha256']==EXPECTED_SOURCE
    svg_count=0
    for facing,view in rig['views'].items():
        reference=np.asarray(Image.open(RIG/view['reference']).convert('RGBA'))
        for name,part in view['parts'].items():
            data=np.asarray(Image.open(RIG/part['raster']).convert('RGBA'))
            visible=data[:,:,3]>0
            assert np.array_equal(data[:,:,:3][visible],reference[:,:,:3][visible]),(facing,name)
            assert digest(RIG/part['raster'])==part['rgba_sha256']
            node=ET.parse(RIG/part['svg']).find('{http://www.w3.org/2000/svg}image')
            embedded=base64.b64decode(node.attrib['{http://www.w3.org/1999/xlink}href'].split(',',1)[1])
            assert np.array_equal(np.asarray(Image.open(io.BytesIO(embedded)).convert('RGBA')),data)
            svg_count+=1
    results=[];loaded={};runtime_groups={}
    counts={'idle':8,'walk_left':8,'walk_right':8,'cheer':8,'sad':6,'welcome':16,
            'turn_left':6,'turn_right':6,'turn_front_from_left':6,'turn_front_from_right':6}
    for a in manifest['animations']:
        name=a['name'];frames=[Image.open(ART/p).convert('RGBA') for p in a['frames']]
        runtime=[Image.open(ART/p).convert('RGBA') for p in a['runtime_frames']]
        assert len(frames)==len(runtime)==counts[name]
        assert a['fps']==12 and a['anchor']==[128,224]
        assert [digest(ART/p) for p in a['frames']]==a['frame_sha256']
        assert [digest(ART/p) for p in a['masters']]==a['master_sha256']
        assert [digest(ART/p) for p in a['runtime_frames']]==a['runtime_sha256']
        assert colours(frames)<=64 and colours(runtime)<=64
        for f in frames+runtime:
            assert set(np.unique(np.asarray(f)[:,:,3])).issubset({0,255})
        for f in frames:
            assert f.size==(256,256)
            y,x=np.where(np.asarray(f)[:,:,3]>=128)
            assert y.max()<224 and y.min()>0 and x.min()>0 and x.max()<255
        assert all(list(f.size)==a['runtime_canvas'] and f.height==a['target_height_px'] for f in runtime)
        assert a['runtime_anchor'][1]==a['target_height_px']
        loaded[name]=(a,frames,runtime)
        runtime_groups.setdefault(a['runtime_group'],[]).extend(runtime)
        results.append({'name':name,'frames':len(frames),'formal_rgba_colours':colours(frames),
                        'runtime_rgba_colours':colours(runtime),'runtime_canvas':a['runtime_canvas'],
                        'runtime_anchor':a['runtime_anchor'],'binary_alpha':True,'hashes_match':True})
    for name,images in runtime_groups.items():
        assert colours(images)<=64,name
        assert len({f.size for f in images})==1,name
        union=np.maximum.reduce([np.asarray(f)[:,:,3] for f in images])
        y,x=np.where(union>=128)
        assert y.max()-y.min()+1==images[0].height,(name,'runtime envelope')
    endpoints=[]
    for side in ['left','right']:
        idle=loaded['idle'][2][0];walk=loaded['walk_'+side][2][0]
        turn=loaded['turn_'+side][2];back=loaded['turn_front_from_'+side][2]
        for f,expected in [(turn[0],idle),(turn[-1],walk),(back[0],walk),(back[-1],idle)]:
            assert np.array_equal(np.asarray(f),np.asarray(expected)),side
        endpoints.append({'side':side,'all_four_turn_endpoints_pixel_identical':True})
    assert colours(loaded['welcome'][2])<=49
    assert loaded['welcome'][0]['runtime_rle_budget']['total_unaligned_bytes']<=100*1024
    result={'source_hash_matches_lock':True,'svg_layers_match_raster_pixels':svg_count,
            'all_parts_rgb_match_normalized_source':True,'mirror_used':False,'animations':results,
            'transitions':endpoints,'visual_acceptance':'not implied by technical validation'}
    (ART/'preview/travel/verification.json').write_text(json.dumps(result,indent=2)+'\n','utf-8')
    print(json.dumps({'source_hash_matches_lock':True,'svg_layers':svg_count,'animations':len(results),
                      'formal_frames':sum(x['frames'] for x in results),'runtime_frames':sum(x['frames'] for x in results),
                      'turn_endpoints_pixel_identical':True},indent=2))
    return result


if __name__=='__main__':verify()
