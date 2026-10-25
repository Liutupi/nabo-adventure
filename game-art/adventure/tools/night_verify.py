"""Independent saved-file, source-head, continuity, palette and codec gates for NIGHT."""
import base64
import io
import json
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageChops,ImageDraw
from night_config import ART,RIG,PREVIEW,ANIMS,SOURCE,FOREST
from night_export import sha,write_json
from night_source import mask
from rig_preview import font


def load(path):return Image.open(path).convert('RGBA')


def inspect():
    manifest=json.loads((ART/'night-manifest.json').read_text('utf-8'))
    rig=json.loads((RIG/'rig.json').read_text('utf-8'))
    quality=json.loads((PREVIEW/'motion-quality.json').read_text('utf-8'));checks=[]
    for skin in SOURCE:
      assert sha(ART/f'games/night/source/{skin}-source.png')==SOURCE[skin]['sha256']
      for facing,view in rig['views'][skin].items():
        original=load(ART/view['contract']['head_common']);expected=Image.new('RGBA',(256,256))
        original.putalpha(ImageChops.multiply(original.getchannel('A'),mask([(0,0),(256,0),(256,93),(137,93),(137,100),(121,100),(121,93),(0,93)])))
        expected.alpha_composite(original,(0,40))
        assert np.array_equal(np.asarray(expected),np.asarray(load(ART/view['parts']['head']['raster'])))
        for part in view['parts'].values():
            path=ART/part['raster'];assert sha(path)==part['sha256']
            element=ET.parse(path.with_suffix('.svg')).find('{http://www.w3.org/2000/svg}image')
            href=element.attrib.get('{http://www.w3.org/1999/xlink}href') or element.attrib['href']
            embedded=load(io.BytesIO(base64.b64decode(href.split(',')[1])))
            assert np.array_equal(np.asarray(embedded),np.asarray(load(path)))
    for entry in manifest['animations']:
        key=(entry['skin'],entry['name']);frames=[]
        if key[0]!='night_shared':assert len(entry['runtime_frames'])==ANIMS[key[1]]['count']
        for field,hfield,size in [('runtime_frames','runtime_sha256',entry['runtime_canvas']),
                                  ('frames','frame_sha256',[256,256]),('masters','master_sha256',[256,256])]:
            if field not in entry:continue
            colours=set()
            for p,h in zip(entry[field],entry[hfield]):
                assert sha(ART/p)==h;im=load(ART/p);assert list(im.size)==size
                if field!='masters':
                    a=np.asarray(im);assert set(np.unique(a[:,:,3]))<={0,255}
                    colours.update(map(tuple,a.reshape(-1,4)))
                if field=='runtime_frames':frames.append(im)
            if field!='masters':assert len(colours)<=64,(key,field,len(colours))
        if entry['skin']=='night_shared':continue
        reports=quality['skins'][key[0]]['motions'][key[1]]['reports']
        assert all(r['head_expression_transform_identical'] for r in reports)
        if key[1] in ['catch','lift_jar']:
            peak=max(reports,key=lambda r:r['pose']['raise_amount'])
            assert peak['jar_opening'][1]<peak['head_core_bbox'][1],(key,'jar opening must clear the hat at peak')
        if not entry['loop']:assert np.array_equal(np.asarray(frames[0]),np.asarray(frames[-1]))
        arrays=[np.asarray(im).astype(float) for im in frames]
        diffs=[float(np.abs(b-a).mean()) for a,b in zip(arrays,arrays[1:])]
        wrap=float(np.abs(arrays[-1]-arrays[0]).mean())
        if entry['loop']:assert wrap<=max(diffs)+.01
        checks.append({'skin':key[0],'action':key[1],'frames':len(frames),'runtime_canvas':entry['runtime_canvas'],
                       'max_adjacent_rgba_mae':max(diffs),'wrap_rgba_mae':wrap,'passed':True})
    pack=json.loads((PREVIEW/'generated-c/adv_assets_generated.json').read_text('utf-8'))
    assert pack['source_manifests_sha256']['night-manifest.json']==sha(ART/'night-manifest.json')
    assert pack['production_c']['verified_frames']==98
    assert pack['groups']['night']['static_bytes_estimate_c3']<=260*1024
    write_json(PREVIEW/'packing-validation.json',{'passed':True,'source_manifest_sha256':sha(ART/'night-manifest.json'),
        'groups':pack['groups'],'python_verified_frames':pack['python_verified_frames'],'production_c':pack['production_c'],
        'command':'CC=D:/nabo-passport-tools/w64devkit/bin/gcc.exe; python tools/build_adventure_assets.py --group night --output game-art/adventure/art/preview/night/generated-c --verify-c',
        'acceptance':'host-only, no device artwork acceptance implied','linker_padding_and_final_elf':'not measured'})
    result={'passed':True,'character_clips':len(checks),'character_frames':sum(c['frames'] for c in checks),
            'frozen_head_core_reused':True,'svg_embedded_pixels_equal_png':True,'checks':checks,
            'visual_gate':'contacts actually inspected; see QA.md for limitations and repairs, no user acceptance claimed'}
    write_json(PREVIEW/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}))


def overview():
    m=json.loads((ART/'night-manifest.json').read_text('utf-8'));entries={(e['skin'],e['name']):e for e in m['animations']}
    out=Image.new('RGB',(1840,1890),FOREST);d=ImageDraw.Draw(out)
    for row,name in enumerate(ANIMS):
      for col,skin in enumerate(SOURCE):
        e=entries[skin,name];paths=e['runtime_frames'];ids=range(len(paths))
        d.text((col*920+8,row*270+4),skin+' '+name+' / actual target + 2x nearest',font=font(13),fill='white')
        for i in ids:
            im=load(ART/paths[i]);x=col*920+10+i*115;y=row*270+25
            out.paste(im,(x,y),im);zoom=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
            out.paste(zoom,(x,y+85),zoom)
    out.save(PREVIEW/'all-actions-overview.png')


if __name__=='__main__':inspect();overview()
