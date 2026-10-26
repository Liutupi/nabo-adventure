"""Check the actual legacy factory, permanent reserve and complete opening cost."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'firmware/tools/adventure-budget.json'
FACTORY=2031616

def growth_budget(app_bytes,profile):
 if type(app_bytes) is not int or not 0<app_bytes<=FACTORY:raise ValueError('Application exceeds the actual legacy factory')
 if profile.get('schema')!='nabo-adventure-growth-budget-v1' or not profile.get('authorization'):raise ValueError('Missing approved growth budget')
 if profile.get('permanent_reserve_bytes')!=64*1024:raise ValueError('Approved permanent64KiB reserve changed')
 games=profile.get('future_games',{})
 if set(games)!={'sky','climb'}:raise ValueError('Both remaining games require explicit allocations')
 for name,entry in games.items():
  if entry.get('allocation_bytes')!=72*1024 or entry.get('state') not in ('reserved','integrated'):
   raise ValueError('Invalid or reduced allocation for '+name)
 held={name:entry['allocation_bytes'] for name,entry in games.items() if entry['state']=='reserved'}
 permanent=profile['permanent_reserve_bytes'];reserve=permanent+sum(held.values())
 if app_bytes>FACTORY-reserve:raise ValueError('App consumes protected repair or pending-game growth allocations')
 return {'reserve_bytes':reserve,'permanent_reserve_bytes':permanent,'future_game_reserve_bytes':sum(held.values()),
         'future_games_reserved_bytes':held,'remaining_after_reserve_bytes':FACTORY-app_bytes-reserve}
def check(build):
 data=(Path(build)/'nabo-adventure.bin').read_bytes();factory=FACTORY
 profile_bytes=PROFILE.read_bytes();growth=growth_budget(len(data),json.loads(profile_bytes))
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
         'free_bytes':factory-len(data),**growth,'budget_profile_sha256':hashlib.sha256(profile_bytes).hexdigest(),
         'opening_bytes':opening['combined_estimate_c3'],'opening_limit_bytes':limit,'status':'PASS'}
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path);a=ap.parse_args();print(json.dumps(check(a.build),indent=2))
