"""Shared source palettes protected by actual transformed SKI head masks."""
import numpy as np
from PIL import Image,ImageChops
from rig_render import transformed


def head_masks(rig,art,reports):
    source=Image.new('RGBA',(256,256))
    for p in rig['common_head']:
        im=Image.open(art/p['path']).convert('RGBA')
        im.putalpha(ImageChops.multiply(im.getchannel('A'),Image.open(art/p['local_alpha_mask'])))
        source.alpha_composite(im)
    return [transformed(source,np.array(r['head_matrix'])).getchannel('A') for r in reports]


def quantize(frames,masks,colours=63):
    """Weight the same original head after each rigid transform, wherever it is."""
    cloud=[]
    for frame,mask in zip(frames,masks):
        a=np.asarray(frame);opaque=a[:,:,3]>=128;head=opaque&(np.asarray(mask)>=128)
        assert head.any(),'Head mask unexpectedly empty'
        cloud.extend(a[:,:,:3][opaque]);cloud.extend(a[:,:,:3][head]);cloud.extend(a[:,:,:3][head])
    pal=Image.fromarray(np.array(cloud,np.uint8).reshape(-1,1,3),'RGB').quantize(colors=colours,method=Image.Quantize.MEDIANCUT)
    palette=pal.getpalette()[:colours*3];rgb=np.array(palette,np.int32).reshape(-1,3)
    outputs=[];errors=[];headerrors=[]
    for frame,mask in zip(frames,masks):
        a=np.asarray(frame);opaque=a[:,:,3]>=128;pixels=a[:,:,:3][opaque].astype(np.int32);nearest=[]
        for start in range(0,len(pixels),8192):
            nearest.extend(((pixels[start:start+8192,None,:]-rgb[None,:,:])**2).sum(axis=2).argmin(axis=1)+1)
        indices=np.zeros(a.shape[:2],np.uint8);indices[opaque]=nearest
        indexed=Image.fromarray(indices,'P');indexed.putpalette([0,0,0]+palette+[0]*(768-(colours+1)*3));indexed.info['transparency']=0
        rgba=indexed.convert('RGBA');delta=np.abs(np.asarray(rgba)[:,:,:3].astype(float)-a[:,:,:3])
        head=opaque&(np.asarray(mask)>=128);errors.append(float(delta[opaque].mean()));headerrors.append(float(delta[head].mean()))
        outputs.append(rgba)
    return outputs,{'palette_size_including_transparency':colours+1,'alpha_threshold':128,
        'palette_rgb':[[0,0,0]]+rgb.tolist(),'palette_index_0_transparent':True,
        'max_rgb_mean_absolute_error':max(errors),'mean_rgb_absolute_error':sum(errors)/len(errors),
        'head_rgb_mean_absolute_error':sum(headerrors)/len(headerrors),'per_frame_head_rgb_mae':headerrors,
        'protected_head_sampling_weight':3,'head_protection':'actual immutable head alpha after the frame rigid transform; not a fixed top-row window'}
