"""Compile the production boot pose lookup against real, validated candidate data."""
from bisect import bisect_right
from contextlib import contextmanager
import copy
import ctypes
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from host_tools import CC, SHARED_EXPORT, unload_library

ROOT=Path(__file__).resolve().parents[1];BOARD=ROOT/'firmware/main'
ART=ROOT/'game-art/adventure/art';sys.path.insert(0,str(ROOT/'tools'))
from adventure_assets_manifest import digest,load_resources
from generate_boot_presentation import generate,read_presentation,DEFAULT_OUTPUT
from build_adventure_assets import startup_budget


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')


@contextmanager
def compiled(header):
    library=header.parent/'motion.dll'
    subprocess.run([CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror',
                    '-I',str(header.parent),'-I',str(BOARD),str(BOARD/'adv_boot_motion.c'),'-o',str(library)],
                   check=True,capture_output=True,text=True)
    lib=ctypes.CDLL(str(library));lib.adv_boot_motion_enabled.restype=ctypes.c_bool
    lib.adv_boot_motion_frame.argtypes=[ctypes.c_uint32];lib.adv_boot_motion_frame.restype=ctypes.c_uint8
    lib.adv_boot_motion_asset_id.restype=ctypes.c_char_p
    for name in ('duration','voice_start_ms','voice_end_us'):getattr(lib,'adv_boot_motion_'+name).restype=ctypes.c_uint32
    for name in ('event_count','frame_count'):getattr(lib,'adv_boot_motion_'+name).restype=ctypes.c_uint16
    try:yield lib
    finally:unload_library(lib._handle)


class BootMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate=json.loads((ART/'boot-v2-manifest.json').read_text('utf-8'))
        cls.legacy=json.loads((ART/'manifest.json').read_text('utf-8'))

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
        self.art=self.folder/'adventure/art';self.art.mkdir(parents=True)
        self.value=copy.deepcopy(self.candidate);self.path=self.art/'boot-v2-manifest.json'
        write(self.path,self.value);write(self.art/'manifest.json',self.legacy)
        paths={p for m in (self.value,self.legacy) for e in m['animations'] for p in e['runtime_frames']}
        for relative in paths:
            destination=self.art/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ART/relative,destination)
        audio=self.art.parent/'audio';audio.mkdir();shutil.copyfile(ART.parent/'audio/boot-welcome.wav',audio/'boot-welcome.wav')
        self.header=self.folder/'private/adv_boot_presentation.h'

    def tearDown(self):self.tmp.cleanup()

    def save(self):
        # The candidate intentionally declares the same timeline in three places.
        for presentation in (self.value.get('presentation'),self.value['animations'][0].get('presentation')):
            if presentation:presentation['timeline']=copy.deepcopy(self.value['timeline'])
        write(self.path,self.value)

    def select(self,**extra):
        write(self.art/'boot/selection.json',{'version':1,'manifest':'boot-v2-manifest.json','sha256':digest(self.path),**extra})

    def test_real_candidate_all_event_boundaries_and_permanent_neutral_hold_execute_production_c(self):
        result=generate(self.art,self.header,'boot-v2-manifest.json');p=read_presentation(self.art,'boot-v2-manifest.json')
        self.assertEqual(result['table_bytes'],len(p.starts)*4+16)
        with compiled(self.header) as c:
            self.assertTrue(c.adv_boot_motion_enabled())
            self.assertEqual(c.adv_boot_motion_asset_id().decode(),p.resource.id)
            self.assertEqual(c.adv_boot_motion_duration(),p.duration_ms)
            self.assertEqual(c.adv_boot_motion_event_count(),len(p.starts))
            self.assertEqual(c.adv_boot_motion_frame_count(),len(p.resource.paths))
            self.assertEqual(c.adv_boot_motion_voice_start_ms(),1400)
            self.assertEqual(c.adv_boot_motion_voice_end_us(),4090625)
            times={0,1399,1400,1401,p.duration_ms-1,p.duration_ms,p.duration_ms+1,65535,65536,0xffffffff}
            for at in p.starts:times.update((max(0,at-1),at,at+1))
            for at in sorted(times):
                expected=p.frames[max(0,bisect_right(p.starts,at)-1)]
                self.assertEqual(c.adv_boot_motion_frame(at),expected,at)
            self.assertEqual(c.adv_boot_motion_frame(0xffffffff),0)
            self.assertGreaterEqual(p.frames.count(0),2,'Real schedule repeats the stored neutral frame')

    def test_no_selection_keeps_all_ten_legacy_animations_and_emits_disabled_c(self):
        resources,dependencies,_=load_resources(self.art,('travel',))
        self.assertEqual(len(resources),10);self.assertEqual(set(dependencies),{'manifest.json'})
        self.assertEqual([r.id for r in resources if r.startup],['travel/welcome'])
        self.assertIsNone(read_presentation(self.art));result=generate(self.art,self.header)
        self.assertFalse(result['enabled']);self.assertEqual(result['table_bytes'],0)
        with compiled(self.header) as c:
            self.assertFalse(c.adv_boot_motion_enabled());self.assertIsNone(c.adv_boot_motion_asset_id())
            self.assertEqual(c.adv_boot_motion_event_count(),0);self.assertEqual(c.adv_boot_motion_duration(),0)
            self.assertEqual([c.adv_boot_motion_frame(t) for t in (0,1400,65536,0xffffffff)],[0]*4)

    def test_selection_replaces_only_startup_and_binds_manifest_voice_and_schedule_budget(self):
        before,_,_=load_resources(self.art,('travel',));self.select()
        after,dependencies,_=load_resources(self.art,('travel',))
        self.assertEqual(set(dependencies),{'manifest.json','boot/selection.json','boot-v2-manifest.json','../audio/boot-welcome.wav'})
        original={r.id:(r.hashes,r.size,r.anchor,r.fps,r.loop) for r in before if not r.startup}
        current={r.id:(r.hashes,r.size,r.anchor,r.fps,r.loop) for r in after if not r.startup}
        self.assertEqual(original,current);self.assertEqual(len(current),9)
        actor=next(r for r in after if r.startup);self.assertEqual(actor.id,'travel/welcome_v2')
        self.assertEqual(actor.presentation_bytes,len(self.value['timeline']['pose_start_ms'])*4+16)
        budget=startup_budget(after,[],{'ui':{'static_bytes_estimate_c3':123}})
        self.assertEqual(budget['presentation_table_bytes'],actor.presentation_bytes)
        self.assertGreater(budget['startup_actor_estimate_c3'],actor.presentation_bytes)
        self.assertEqual(budget['combined_estimate_c3'],budget['startup_actor_estimate_c3']+123)
        self.assertTrue(generate(self.art,self.header)['enabled'])

    def test_explicit_candidate_cannot_enable_the_production_header(self):
        previous=DEFAULT_OUTPUT.read_bytes() if DEFAULT_OUTPUT.exists() else None
        with self.assertRaisesRegex(ValueError,'private --output'):generate(self.art,DEFAULT_OUTPUT,'boot-v2-manifest.json')
        with self.assertRaisesRegex(ValueError,'private --output'):
            generate(self.art,BOARD/'generated/unselected-candidate.h','boot-v2-manifest.json')
        self.assertEqual(DEFAULT_OUTPUT.read_bytes() if DEFAULT_OUTPUT.exists() else None,previous)
        self.assertFalse((self.art/'boot/selection.json').exists())

    def test_storage_permutation_keeps_all_logical_images_and_event_times(self):
        original=read_presentation(self.art,'boot-v2-manifest.json')
        order=[0,*reversed(range(1,len(original.resource.paths)))]
        self.select(storage_order=order)
        selected=read_presentation(self.art)
        self.assertEqual(selected.starts,original.starts)
        self.assertEqual(selected.duration_ms,original.duration_ms)
        self.assertEqual(selected.table_bytes,original.table_bytes)
        self.assertEqual([selected.resource.hashes[f] for f in selected.frames],
                         [original.resource.hashes[f] for f in original.frames])
        self.assertEqual([selected.resource.paths[f] for f in selected.frames],
                         [original.resource.paths[f] for f in original.frames])
        generate(self.art,self.header)
        with compiled(self.header) as c:
            for at,frame in zip(selected.starts,selected.frames):
                self.assertEqual(c.adv_boot_motion_frame(at),frame)
            self.assertEqual(c.adv_boot_motion_frame(0xffffffff),0)

    def test_storage_order_requires_exact_permutation_and_fixed_neutral(self):
        count=len(self.value['animations'][0]['runtime_frames'])
        valid=list(range(count))
        cases=[valid[:-1],valid+[count],valid[:-1]+[0],[*range(1,count),0],
               [False,*valid[1:]],[0.0,*valid[1:]],'0,1',[-1,*valid[1:]]]
        for order in cases:
            with self.subTest(order=order):
                self.select(storage_order=order)
                with self.assertRaisesRegex(ValueError,'storage_order'):
                    read_presentation(self.art)

    def test_bad_selection_sha_path_version_and_missing_actor_are_rejected(self):
        for patch in ({'sha256':'0'*64},{'manifest':'../escape.json'},{'version':True},{'version':2}):
            with self.subTest(patch=patch):
                self.select(**patch)
                with self.assertRaises(ValueError):load_resources(self.art,('travel',))
        self.select();legacy=copy.deepcopy(self.legacy)
        legacy['animations']=[e for e in legacy['animations'] if e['name']!='welcome'];write(self.art/'manifest.json',legacy)
        with self.assertRaisesRegex(ValueError,'exactly one'):load_resources(self.art,('travel',))

    def test_invalid_times_indices_counts_loop_and_final_hold_are_rejected(self):
        cases=[('start',lambda t:t['pose_start_ms'].__setitem__(0,1)),
               ('duplicate',lambda t:t['pose_start_ms'].__setitem__(1,0)),
               ('descending',lambda t:t['pose_start_ms'].__setitem__(2,1)),
               ('uint16',lambda t:t['pose_start_ms'].__setitem__(1,65536)),
               ('float',lambda t:t['pose_start_ms'].__setitem__(1,1.5)),
               ('boolean',lambda t:t['pose_start_ms'].__setitem__(1,True)),
               ('uint8',lambda t:t['pose_frame_indices'].__setitem__(1,256)),
               ('storage-index',lambda t:t['pose_frame_indices'].__setitem__(1,255)),
               ('negative-frame',lambda t:t['pose_frame_indices'].__setitem__(1,-1)),
               ('frame-bool',lambda t:t['pose_frame_indices'].__setitem__(1,True)),
               ('short-indices',lambda t:t['pose_frame_indices'].pop()),
               ('final-not-neutral',lambda t:t['pose_frame_indices'].__setitem__(-1,1)),
               ('zero-final-hold',lambda t:t.__setitem__('total_duration_ms',t['pose_start_ms'][-1])),
               ('duration-overflow',lambda t:t.__setitem__('total_duration_ms',65536)),
               ('metadata-count',lambda t:t.__setitem__('logical_pose_count',999)),
               ('pose-duration',lambda t:t['duration_ms'].__setitem__(0,1))]
        for name,mutate in cases:
            with self.subTest(name=name):
                self.value=copy.deepcopy(self.candidate);mutate(self.value['timeline']);self.save()
                with self.assertRaises(ValueError):read_presentation(self.art,'boot-v2-manifest.json')
        self.value=copy.deepcopy(self.candidate);self.value['animations'][0]['loop']=True;self.save()
        with self.assertRaisesRegex(ValueError,'nonlooping'):read_presentation(self.art,'boot-v2-manifest.json')

    def test_wrong_frame_sha_canvas_alpha_and_duplicate_timeline_are_rejected(self):
        self.value['animations'][0]['runtime_sha256'][0]='0'*64;self.save()
        with self.assertRaisesRegex(ValueError,'SHA256'):read_presentation(self.art,'boot-v2-manifest.json')
        self.value=copy.deepcopy(self.candidate);self.value['animations'][0]['runtime_canvas'][0]+=1;self.save()
        with self.assertRaisesRegex(ValueError,'canvas'):read_presentation(self.art,'boot-v2-manifest.json')
        from PIL import Image
        self.value=copy.deepcopy(self.candidate);entry=self.value['animations'][0];path=self.art/entry['runtime_frames'][0]
        im=Image.open(path).convert('RGBA');im.putpixel((0,0),(0,0,0,128));im.save(path)
        entry['runtime_sha256'][0]=digest(path);self.save()
        with self.assertRaisesRegex(ValueError,'Nonbinary alpha'):read_presentation(self.art,'boot-v2-manifest.json')
        shutil.copyfile(ART/entry['runtime_frames'][0],path);self.value=copy.deepcopy(self.candidate);self.save()
        self.value['presentation']['timeline']['voice_start_ms']=123;write(self.path,self.value)
        with self.assertRaisesRegex(ValueError,'disagree'):read_presentation(self.art,'boot-v2-manifest.json')

    def test_voice_sha_path_and_sample_derived_times_are_required(self):
        for field,value in (('voice_start_ms',1399),('voice_end_ms',4090.5),('voice_duration_ms',2691),('voice_end_ms',float('nan'))):
            with self.subTest(field=field,value=value):
                self.value=copy.deepcopy(self.candidate);self.value['timeline'][field]=value;self.save()
                with self.assertRaises(ValueError):read_presentation(self.art,'boot-v2-manifest.json')
        for patch in ({'sha256':'0'*64},{'path':'../../outside.wav'}):
            self.value=copy.deepcopy(self.candidate);self.value['voice'].update(patch);self.save()
            with self.assertRaises(ValueError):read_presentation(self.art,'boot-v2-manifest.json')

    def test_validation_failure_leaves_existing_header_unchanged(self):
        generate(self.art,self.header,'boot-v2-manifest.json');before=self.header.read_bytes()
        self.value['timeline']['pose_start_ms'][0]=5;self.save()
        with self.assertRaises(ValueError):generate(self.art,self.header,'boot-v2-manifest.json')
        self.assertEqual(self.header.read_bytes(),before)


if __name__=='__main__':unittest.main(verbosity=2)
