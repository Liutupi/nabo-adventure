"""Check the actual legacy factory, permanent reserve and complete opening cost."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def check(build):
 data=(Path(build)/'nabo-adventure.bin').read_bytes();factory=2031616;reserve=352*1024
 if len(data)>factory-reserve:raise ValueError('App consumes the permanent352KiB legacy-factory reserve')
 report=json.loads((ROOT/'firmware/main/generated/adv_assets_generated.json').read_text('utf-8'))
 opening=report['startup_composition'];selection=json.loads((ROOT/'game-art/adventure/art/boot/selection.json').read_text('utf-8'))
 video=selection.get('kind')=='mpeg1-ip';limit=(224 if video else 160)*1024
 if opening['limit_bytes']!=limit or opening['combined_estimate_c3']>limit:raise ValueError('Complete opening exceeds its explicit profile budget')
 if video:
  art=ROOT/'game-art/adventure/art';manifest=(art/selection['manifest']).resolve()
  if not manifest.is_relative_to(art.resolve()) or hashlib.sha256(manifest.read_bytes()).hexdigest()!=selection['sha256']:raise ValueError('Unbound video manifest')
  v=json.loads(manifest.read_text('utf-8'));size=32
  for name in ('movie','poster'):
   entry=v[name];path=(art/entry['path']).resolve()
   if not path.is_relative_to(art.resolve()):raise ValueError('Video path escapes art directory')
   blob=path.read_bytes()
   if len(blob)!=entry['bytes'] or hashlib.sha256(blob).hexdigest()!=entry['sha256']:raise ValueError('Unbound video bytes')
   size+=len(blob)
  if size!=opening['boot_video_bytes'] or opening['combined_estimate_c3']!=size+opening['ui_assets_estimate_c3']:raise ValueError('Video/poster/UI were not fully charged')
 return {'app_sha256':hashlib.sha256(data).hexdigest(),'app_bytes':len(data),'physical_factory_bytes':factory,
         'free_bytes':factory-len(data),'reserve_bytes':reserve,'remaining_after_reserve_bytes':factory-len(data)-reserve,
         'opening_bytes':opening['combined_estimate_c3'],'opening_limit_bytes':limit,'status':'PASS'}
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path);a=ap.parse_args();print(json.dumps(check(a.build),indent=2))
