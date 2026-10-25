"""Read back SKY files independently; assert source identity, target contacts and C binding."""
import base64
import io
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageChops,ImageDraw
from sky_config import ART,RIG,GAME,PREVIEW,SOURCES,SKIN_ANIMS,ANIMS,HEAD_LOCKS,SKY
from sky_rig import sha,dump
from rig_render import transformed
from rig_preview import font


def load(path):return Image.open(path).convert('RGBA')


def embedded_equals(svgpath,pngpath):
    node=ET.parse(svgpath).find('{http://www.w3.org/2000/svg}image')
    embedded=load(io.BytesIO(base64.b64decode(node.attrib['href'].split(',')[1])))
    assert np.array_equal(np.asarray(embedded),np.asarray(load(pngpath)))


def main():
    m=json.loads((ART/'sky-manifest.json').read_text('utf-8'));rig=json.loads((RIG/'rig.json').read_text('utf-8'))
    q=json.loads((PREVIEW/'motion-quality.json').read_text('utf-8'));a={(e['skin'],e['name']):e for e in m['animations']}
    localmask=Image.open(RIG/'local-head-garment-exclusion.png');heads=[]
    for name,file in [('head','head'),('expression','expression_neutral')]:
        p=ART/f'rig/common/front/{file}.png';assert sha(p)==HEAD_LOCKS[file]
        expected=load(p);expected.putalpha(ImageChops.multiply(expected.getchannel('A'),localmask))
        assert np.array_equal(np.asarray(expected),np.asarray(load(RIG/f'{name}.png')))
        embedded_equals(RIG/f'{name}.svg',RIG/f'{name}.png');heads.append(expected)
    for skin in SOURCES:
        assert sha(GAME/f'source/{skin}-source.png')==SOURCES[skin]['sha256']
        original=load(RIG/skin/'wardrobe.png')
        for name,part in rig['skins'][skin]['parts'].items():
            p=ART/part['raster'];assert sha(p)==part['sha256']
            if name in ['head','expression']:continue
            expected=original.copy();expected.putalpha(ImageChops.multiply(original.getchannel('A'),Image.open(ART/part['mask'])))
            assert np.array_equal(np.asarray(expected),np.asarray(load(p)))
            embedded_equals(ART/part['svg'],p)
    checks=[];quantization={}
    for e in m['animations']:
        skin,name=e['skin'],e['name'];runtime=[]
        for field,hfield,size in [('frames','frame_sha256',[256,256]),('masters','master_sha256',[256,256]),
                                  ('runtime_frames','runtime_sha256',e['runtime_canvas'])]:
            if field not in e:continue
            colours=set()
            for p,h in zip(e[field],e[hfield]):
                assert sha(ART/p)==h;im=load(ART/p);assert list(im.size)==size;data=np.asarray(im)
                if field!='masters':
                    assert set(np.unique(data[:,:,3]))<={0,255};colours.update(map(tuple,data.reshape(-1,4)))
                if field=='runtime_frames':runtime.append(im)
            if field!='masters':assert len(colours)<=64,(skin,name,field,len(colours))
        if skin=='sky_props':continue
        assert name in SKIN_ANIMS[skin] and len(runtime)==ANIMS[name]['count']
        neutral=load(ART/a[skin,'idle']['runtime_frames'][0]) if e['target_height_px']==40 else runtime[0]
        if not e['loop']:
            assert np.array_equal(np.asarray(runtime[0]),np.asarray(neutral))
            assert np.array_equal(np.asarray(runtime[-1]),np.asarray(neutral))
        for i,p in enumerate(e['masters']):
            report=q['skins'][skin][name]['reports'][i];matrix=np.array(report['head_matrix'])
            expected=transformed(heads[0],matrix);expected.alpha_composite(transformed(heads[1],matrix))
            want=np.asarray(expected);got=np.asarray(load(ART/p));yy,xx=np.indices(want.shape[:2])
            protected=(want[:,:,3]>=250)&(yy<90)
            delta=np.abs(want[:,:,:3].astype(int)-got[:,:,:3].astype(int))
            assert int(delta[protected].max())<=1,(skin,name,i,'face-source pixels drifted')
            assert report['head_expression_matrix_identical'] and not report['redrawn_face']
        arrays=[np.asarray(im).astype(float) for im in runtime]
        diffs=[float(np.abs(b-a).mean()) for a,b in zip(arrays,arrays[1:])]
        wrap=float(np.abs(arrays[-1]-arrays[0]).mean())
        if e['loop']:assert wrap<=max(diffs)+.01
        checks.append({'skin':skin,'name':name,'count':len(runtime),'max_adjacent_rgba_mae':max(diffs),
                       'wrap_rgba_mae':wrap,'source_face_not_redrawn':True,'passed':True})
        quantization[skin+'/'+name]={'formal_head_mae':e['formal_quantization']['head_rgb_mean_absolute_error'],
                                  'runtime_head_mae':e['runtime_quantization']['head_rgb_mean_absolute_error']}
    grips=[]
    for name in ['heat','vent']:
        e=a['sky_a',name];rope=a['sky_props',name+'_controls']
        for i in [1,2,3,4]:
            pixel=rope['control_points'][i][name]['grip'];colour=load(ART/e['runtime_frames'][i]).getpixel(tuple(pixel))
            assert colour[3]==255 and colour[0]>colour[1]*1.05 and colour[1]>colour[2],(name,i,colour,'grip not on source skin pixel')
            grips.append({'action':name,'index':i,'point':pixel,'character_RGBA':colour,'distance_to_visible_hand_pixel':0})
    for asset in m['assets']:
        p=ART/asset['path'];assert sha(p)==asset['sha256'];assert list(load(p).size)==asset['size']
        embedded_equals(ART/asset['source_svg'],p)
    assert len(set(a['sky_props','bird']['runtime_sha256']))==4
    pack=json.loads((PREVIEW/'generated-c/adv_assets_generated.json').read_text('utf-8'))
    assert pack['source_manifests_sha256']['sky-manifest.json']==sha(ART/'sky-manifest.json')
    assert pack['production_c']['verified_frames']==77 and pack['groups']['sky']['static_bytes_estimate_c3']<=260*1024
    dump(PREVIEW/'packing-validation.json',{'passed':True,'manifest_sha256':sha(ART/'sky-manifest.json'),
        'groups':pack['groups'],'python_verified_frames':pack['python_verified_frames'],'production_c':pack['production_c'],
        'command':'CC=D:/nabo-passport-tools/w64devkit/bin/gcc.exe; python tools/build_adventure_assets.py --group sky --output game-art/adventure/art/preview/sky/generated-c --verify-c',
        'acceptance':'host-only; actual device gameplay and final ELF not measured'})
    dump(PREVIEW/'verification.json',{'passed':True,'character_clips':len(checks),'character_frames':sum(c['count'] for c in checks),
        'shared_head_locked':True,'svg_embedded_pixels_match':True,'checks':checks,'quantization_errors':quantization,
        'control_hand_contacts':grips,'minimum_visual_review':'all character contacts and actual-size layered scenes inspected; no user/hardware approval implied'})
    print('SKY independent checks passed:',len(checks),'clips;',len(grips),'exact visible-skin rope contacts')


def overview():
    m=json.loads((ART/'sky-manifest.json').read_text('utf-8'));entries=[e for e in m['animations'] if e['skin']!='sky_props']
    out=Image.new('RGB',(1200,len(entries)*270),SKY);d=ImageDraw.Draw(out)
    for row,e in enumerate(entries):
        d.text((8,row*270+3),e['skin']+' '+e['name']+' / actual target + 2x nearest',font=font(13),fill='#253f4e')
        for i,p in enumerate(e['runtime_frames']):
            im=load(ART/p);x=i*145+8;y=row*270+24
            out.paste(im,(x,y),im);zoom=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
            out.paste(zoom,(x,y+76),zoom)
    out.save(PREVIEW/'all-actions-overview.png')


if __name__=='__main__':main();overview()
