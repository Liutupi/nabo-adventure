"""Re-render frozen V2a in an owned temporary folder; never overwrite its images."""
import json
import tempfile
import shutil
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import boot_v2_sources as source
import boot_v2_render as renderer
from boot_v2_motion import KEYS
from rig_preview import quantize


def main():
 art=source.ART;out=source.OUT;manifest_path=art/'boot-v2-manifest.json'
 before=source.sha(manifest_path);m=json.loads(manifest_path.read_text('utf-8'))
 assert m['package']=='boot-v2a-preview';e=m['animations'][0];timeline=m['timeline']
 actual=[source.sha(art/p) for p in e['runtime_frames']];assert actual==e['runtime_sha256']
 for name,digest in m['provenance'].items():
  path=source.BASE.parents[1]/name;assert source.sha(path)==digest,(path,'source drift')
 targets=[art/p for p in e['runtime_frames']]+[manifest_path]
 locked={str(p):source.sha(p) for p in targets}
 old=(source.OUT,source.SRC,source.PREVIEW,renderer.OUT,renderer.SRC,renderer.PREVIEW)
 try:
  with tempfile.TemporaryDirectory(prefix='.v2a-reproduce-',dir=out) as temp:
   work=Path(temp);assert work.resolve().is_relative_to(out.resolve())
   scratch=work/'source';scratch.mkdir();preview=work/'preview';preview.mkdir()
   for filename in ('s-welcome-hand-reference.png','s-welcome-hand-3p25.png'):
    shutil.copyfile(source.SRC/filename,scratch/filename)
   source.OUT=renderer.OUT=work;source.SRC=renderer.SRC=scratch;source.PREVIEW=renderer.PREVIEW=preview
   prepared=renderer.prepare();masters=[renderer.render(prepared,i)[0] for i in range(len(KEYS))]
   box=source.union(masters);scale=120/208
   size=[round((box[2]-box[0])*scale),round((box[3]-box[1])*scale)]
   sampled=[im.crop(box).resize(tuple(size),Image.Resampling.LANCZOS) for im in masters]
   frames,_=quantize(sampled,colours=48,protect_head=round(100*scale));assert size==e['runtime_canvas']
   signatures=[]
   for i,frame in enumerate(frames):
    frozen=Image.open(art/e['runtime_frames'][timeline['pose_frame_indices'][i]]).convert('RGBA')
    assert np.array_equal(np.asarray(frame),np.asarray(frozen)),(i,KEYS[i][1],'pixel mismatch')
    signatures.append(hashlib.sha256(frame.tobytes()).hexdigest())
 finally:
  source.OUT,source.SRC,source.PREVIEW,renderer.OUT,renderer.SRC,renderer.PREVIEW=old
 assert all(source.sha(Path(p))==digest for p,digest in locked.items())
 report=dict(source_manifest_sha256=before,logical_poses_equal=34,unique_runtime_images_equal=len(set(signatures)),
  rgba_bytes_equal=True,png_source_hashes_unchanged=True,reproduction='Original sources -> same rigid rig -> same 120px sample -> same 48-colour quantization',
  output_boundary='Only temporary source/rig copies inside boot/v2; frozen runtime PNGs and manifest not overwritten',
  note='UI and MP4 source timing unchanged; this verifies character PNG reproducibility, not subjective acting acceptance.')
 (source.PREVIEW/'repro-v2a.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps(report,indent=2))


if __name__=='__main__':main()
