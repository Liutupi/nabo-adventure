"""Replay the frozen POST palettes; avoid recolouring seven unrelated clips."""
import copy
import numpy as np
from PIL import Image


def fixed_palette(frames, report, protect_head=False):
    report=copy.deepcopy(report)
    palette=np.array(report['palette_rgb'][1:],dtype=np.int32)
    outputs=[];errors=[];head_errors=[]
    for frame in frames:
        data=np.asarray(frame);opaque=data[:,:,3]>=128
        rgb=data[:,:,:3][opaque].astype(np.int32);nearest=[]
        for start in range(0,len(rgb),8192):
            distance=((rgb[start:start+8192,None,:]-palette[None,:,:])**2).sum(axis=2)
            nearest.extend(distance.argmin(axis=1)+1)
        indices=np.zeros(data.shape[:2],dtype=np.uint8);indices[opaque]=nearest
        indexed=Image.fromarray(indices,'P')
        flat=[v for colour in report['palette_rgb'] for v in colour]
        indexed.putpalette(flat+[0]*(768-len(flat)));indexed.info['transparency']=0
        rgba=indexed.convert('RGBA');outputs.append(rgba)
        delta=np.abs(np.asarray(rgba)[:,:,:3].astype(float)-data[:,:,:3])
        errors.append(float(delta[opaque].mean()))
        protected=opaque.copy();protected[104 if protect_head is True else int(protect_head):]=False
        head_errors.append(float(delta[protected].mean()))
    report.update(max_rgb_mean_absolute_error=max(errors),mean_rgb_absolute_error=sum(errors)/len(errors),
                  head_rgb_mean_absolute_error=sum(head_errors)/len(head_errors))
    return outputs,report
