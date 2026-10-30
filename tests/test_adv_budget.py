"""Enforce the approved pools: one game's work cannot consume the other game's budget."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from check_adventure_budget import growth_budget,FACTORY
class GrowthBudget(unittest.TestCase):
 def setUp(self):
  self.profile=json.loads((ROOT/'firmware/tools/adventure-budget.json').read_text('utf-8'))
  for entry in self.profile['future_games'].values():entry['state']='reserved'
 def test_current_candidate_protects_both_future_games(self):
  r=growth_budget(1812256,self.profile)
  self.assertEqual(r['future_games_reserved_bytes'],{'sky':73728,'climb':73728})
  self.assertEqual((r['permanent_reserve_bytes'],r['remaining_after_reserve_bytes']),(65536,6368))
 def test_exact_pool_boundary_and_one_byte_over(self):
  cap=FACTORY-65536-2*73728;growth_budget(cap,self.profile)
  with self.assertRaises(ValueError):growth_budget(cap+1,self.profile)
 def test_integrating_sky_does_not_release_climb_allocation(self):
  p=copy.deepcopy(self.profile);p['future_games']['sky']['state']='integrated'
  cap=FACTORY-65536-73728
  self.assertEqual(growth_budget(cap,p)['future_games_reserved_bytes'],{'climb':73728})
  with self.assertRaises(ValueError):growth_budget(cap+1,p)
 def test_both_integrated_still_preserve_repairs(self):
  for v in self.profile['future_games'].values():v['state']='integrated'
  growth_budget(FACTORY-65536,self.profile)
  with self.assertRaises(ValueError):growth_budget(FACTORY-65536+1,self.profile)
 def test_missing_or_reduced_allocations_are_rejected(self):
  for field in ('sky','climb'):
   p=copy.deepcopy(self.profile);del p['future_games'][field]
   with self.assertRaises(ValueError):growth_budget(1812256,p)
   p=copy.deepcopy(self.profile);p['future_games'][field]['allocation_bytes']-=1
   with self.assertRaises(ValueError):growth_budget(1812256,p)
 def test_invalid_policy_and_application_sizes_are_rejected(self):
  for size in (0,-1,FACTORY+1,True):
   with self.assertRaises(ValueError):growth_budget(size,self.profile)
  self.profile['permanent_reserve_bytes']=0
  with self.assertRaises(ValueError):growth_budget(1812256,self.profile)

 def test_live_profile_marks_only_landed_v2_games_integrated(self):
  p=json.loads((ROOT/'firmware/tools/adventure-budget.json').read_text('utf-8'))
  self.assertEqual({game:entry['state'] for game,entry in p['future_games'].items()},{'sky':'integrated','climb':'integrated'})
