"""Measure the entire candidate plus current UI with the real row-RLE and C decoder."""
import json
import argparse
import hashlib
import sys
import tempfile
from pathlib import Path
from boot_v2_sources import ART,BASE,OUT,PREVIEW,sha

ROOT=BASE.parents[1];sys.path.insert(0,str(ROOT/'tools'))
from adventure_assets_manifest import Resource,validate,load_resources,verify_sources_unchanged
from adventure_assets_emit import emit_sprites,emit_catalog
from adventure_assets_verify import verify_c
from build_adventure_assets import budgets
from boot_v2_optimize import optimal_keys_pack


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--intern-ui',action='store_true');parser.add_argument('--optimal-keys',action='store_true');args=parser.parse_args()
 path=ART/'boot-v2-manifest.json';manifest=json.loads(path.read_text('utf-8'));e=manifest['animations'][0];t=manifest['timeline']
 resource=Resource('travel/welcome_v2','boot_v2',[ART/p for p in e['runtime_frames']],e['runtime_sha256'],
  tuple(e['runtime_canvas']),tuple(e['runtime_anchor']),fps=12,loop=False,startup=True)
 validate(resource);ui_resources,ui_hashes,ui=load_resources(ART,('ui',));resources=sorted([resource,*ui_resources],key=lambda r:r.id)
 rows=['#pragma once','#include <stdint.h>',
  'typedef struct {uint16_t at_ms; uint8_t frame; uint8_t reserved;} boot_v2_pose_t;',
  '_Static_assert(sizeof(boot_v2_pose_t)==4,"boot schedule layout");',
  'static const boot_v2_pose_t boot_v2_schedule[] = {']
 rows.extend(f' {{{ms},{idx},0}},' for ms,idx in zip(t['pose_start_ms'],t['pose_frame_indices']))
 rows+=['};','typedef struct {uint32_t duration_ms,voice_start_ms,voice_end_us;uint16_t poses,fps;} boot_v2_meta_t;',
  '_Static_assert(sizeof(boot_v2_meta_t)==16,"boot metadata layout");',
  f'static const boot_v2_meta_t boot_v2_meta={{4417,1400,4090625,{len(t["pose_start_ms"])},12}};']
 (OUT/'presentation-timeline.h').write_text('\n'.join(rows)+'\n','utf-8')
 with tempfile.TemporaryDirectory(prefix='.boot-v2-c-',dir=OUT) as temp:
  folder=Path(temp);assert folder.resolve().is_relative_to(OUT.resolve())
  import adventure_assets_emit as emitter
  import generate_adv_sprites as codec
  original_emitter_pack,original_codec_pack=emitter.pack,codec.pack
  if args.optimal_keys:emitter.pack=codec.pack=optimal_keys_pack
  aliases={};canonical=[];fingerprints={}
  for item in resources:
   fingerprint=(item.group,item.size,hashlib.sha256(b''.join(im.tobytes() for im in item.images)).hexdigest())
   if args.intern_ui and item.group=='ui' and fingerprint in fingerprints:aliases[item.id]=fingerprints[fingerprint]
   else:canonical.append(item);fingerprints[fingerprint]=item
  originals=emit_sprites(canonical,folder);pieces=[]
  for item in resources:
   source=aliases.get(item.id,item)
   for piece in originals:
    if piece['resource'] is source:
     offset=[piece['offset'][i]-source.offset[i]+item.offset[i] for i in range(2)]
     pieces.append({**piece,'resource':item,'offset':tuple(offset)})
  catalog=emit_catalog(resources,pieces,folder,ui)
  measured=budgets(resources,pieces,ui,catalog);c=verify_c(resources,pieces,catalog,folder)
  if args.intern_ui:
   seen=set()
   for piece in pieces:
    if piece['symbol'] in seen:
     g=measured[piece['resource'].group];g['rle_bytes']-=piece['report']['data_bytes'];g['table_bytes']-=piece['report']['table_bytes'];g['descriptor_catalog_estimate_c3']-=32
    seen.add(piece['symbol'])
   for g in measured.values():g['static_bytes_estimate_c3']=g['rle_bytes']+g['table_bytes']+g['descriptor_catalog_estimate_c3']
  verify_sources_unchanged(ART,ui_resources,ui_hashes)
  assert all(sha(p)==h for p,h in zip(resource.paths,resource.hashes))
  emitter.pack,codec.pack=original_emitter_pack,original_codec_pack
 timeline_bytes=4*len(t['pose_start_ms'])+16
 boot=measured['boot_v2']['static_bytes_estimate_c3'];ui_bytes=measured['ui']['static_bytes_estimate_c3']
 total=boot+ui_bytes+timeline_bytes
 report=dict(source_manifest_sha256=sha(path),groups=measured,unique_runtime_frames=len(e['runtime_frames']),logical_events=len(t['pose_start_ms']),
  extra_timeline_table_bytes=timeline_bytes,combined_ui_boot_and_timeline_bytes=total,limit_bytes=163840,within_limit=total<=163840,
  compared_with_root_ui62109=dict(ui_bytes=62109,total_bytes=62109+boot+timeline_bytes),production_c=c,
  ui_source_hashes=ui_hashes,decoder_sha256=sha(ROOT/'firmware/main/adv_sprite.c'),timeline_header_sha256=sha(OUT/'presentation-timeline.h'),
  ui_interning=dict(enabled=args.intern_ui,aliased_resources=len(aliases),aliases={k:v.id for k,v in aliases.items()},
   implementation_boundary='Preview-local wrapper only; global production emitter unchanged and needs root integration if selected'),
  optimal_keys=dict(enabled=args.optimal_keys,format='unchanged adv-row-rle-v1',decoder_changes=False,
   boundary='Preview-process encoder override only; root must integrate/test the encoder to claim formal production budget'),
  boundary='RLE/table bytes exact; C3 catalog estimates exclude linker padding. Final ELF and on-device acting are pending. No shared generated files written.')
 name=('packing-intern-ui-optimal-keys.json' if args.intern_ui else 'packing-optimal-keys.json') if args.optimal_keys else ('packing-intern-ui.json' if args.intern_ui else 'packing-validation.json')
 (PREVIEW/name).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
