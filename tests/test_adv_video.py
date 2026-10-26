"""Execute every real boot frame, allocation failure, and independent 3-reference path."""
import ctypes,subprocess,tempfile,unittest,sys,json,hashlib
from pathlib import Path
from host_tools import CC,SHARED_EXPORT,unload_library
ROOT=Path(__file__).resolve().parents[1];BOARD=ROOT/'firmware/main';ART=ROOT/'game-art/adventure/art'
sys.path.insert(0,str(ROOT/'tools'))
from generate_boot_video import stream,read_video
class Video(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.libs=[]
  for three in (False,True):
   path=Path(cls.tmp.name)/('three.dll' if three else 'two.dll')
   command=[CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror']
   if three:command+=['-DPLM_VIDEO_THREE_REFERENCE']
   subprocess.run(command+[str(ROOT/'tests/adv_host/adv_video_host.c'),str(BOARD/'generated/adv_boot_video_data.c'),'-o',str(path)],check=True,capture_output=True,text=True)
   lib=ctypes.CDLL(str(path));cls.libs.append(lib)
   lib.adv_video_open.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint,ctypes.c_uint];lib.adv_video_open.restype=ctypes.c_void_p
   lib.adv_video_close.argtypes=[ctypes.c_void_p];lib.adv_video_next.argtypes=[ctypes.c_void_p];lib.adv_video_next.restype=ctypes.c_bool
   lib.adv_video_row.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p]
   lib.adv_video_reference_bytes.argtypes=[ctypes.c_void_p];lib.adv_video_reference_bytes.restype=ctypes.c_size_t
   lib.adv_video_band_generation.argtypes=[ctypes.c_void_p,ctypes.c_uint];lib.adv_video_band_generation.restype=ctypes.c_uint32
   lib.host_yuv_hash.argtypes=[ctypes.c_void_p];lib.host_yuv_hash.restype=ctypes.c_uint32
   lib.host_reference_frame.argtypes=[ctypes.c_void_p]
   lib.host_alloc_fail.argtypes=[ctypes.c_int]
  cls.data=(ART/'boot/v3/runtime/boot-welcome.m1v').read_bytes()
 @classmethod
 def tearDownClass(cls):
  for lib in cls.libs:unload_library(lib._handle)
  cls.tmp.cleanup()
 def setUp(self):
  for lib in self.libs:lib.host_alloc_fail(-1);self.assertEqual(lib.host_alloc_live(),0)
 def test_all73_frames_match_three_reference_decoder_and_never_write_input_or_allocate_per_frame(self):
  hashes=[]
  for lib in self.libs:
   data=ctypes.create_string_buffer(self.data);v=lib.adv_video_open(data,len(self.data),208,272);self.assertTrue(v)
   calls=lib.host_alloc_calls();frames=[]
   while lib.adv_video_next(v):frames.append(lib.host_yuv_hash(v))
   self.assertEqual(len(frames),73);self.assertGreater(len(set(frames)),65)
   self.assertEqual(lib.host_alloc_calls(),calls)
   self.assertEqual(data.raw[:-1],self.data,'Flash-backed elementary stream must stay immutable')
   held=lib.host_yuv_hash(v)
   for _ in range(3):self.assertFalse(lib.adv_video_next(v));self.assertEqual(lib.host_yuv_hash(v),held)
   lib.adv_video_close(v);self.assertEqual(lib.host_alloc_live(),0);hashes.append(frames)
  self.assertEqual(hashes[0],hashes[1],'Two-buffer I/P rotation must equal independent three-reference path for every YCbCr pixel')
 def test_unchanged_band_generations_never_hide_changed_pixels_including_skipped_draws(self):
  lib=self.libs[0];data=ctypes.create_string_buffer(self.data)
  v=lib.adv_video_open(data,len(self.data),208,272);self.assertTrue(v)
  previous=None;displayed=None;frame=0;changed=0
  while lib.adv_video_next(v):
   rows=[]
   for y in range(320):
    row=(ctypes.c_uint16*240)();lib.adv_video_row(v,y,0,240,row);rows.append(bytes(row))
   bands=[b''.join(rows[b*16:(b+1)*16]) for b in range(20)]
   generations=[lib.adv_video_band_generation(v,b) for b in range(20)]
   for earlier in (previous,displayed):
    if earlier:
     for b in range(20):
      if earlier[0][b]==generations[b]:self.assertEqual(earlier[1][b],bands[b],f'frame {frame}, band {b}')
   if previous:changed+=sum(a!=b for a,b in zip(previous[0],generations))
   previous=(generations,bands)
   # The compositor may draw after several decoded frames. A later matching
   # sample must not erase damage accumulated since the last presented image.
   if frame%5==0:displayed=previous
   frame+=1
  held=[lib.adv_video_band_generation(v,b) for b in range(20)]
  self.assertFalse(lib.adv_video_next(v))
  self.assertEqual(held,[lib.adv_video_band_generation(v,b) for b in range(20)])
  self.assertEqual(lib.adv_video_band_generation(v,20),0)
  self.assertEqual(frame,73);self.assertLess(changed,72*20*0.8,'Real static rows should avoid at least 20% of redraws')
  lib.adv_video_close(v);self.assertEqual(lib.host_alloc_live(),0)
 def test_each_allocation_failure_cleans_up_and_reports_unavailable(self):
  lib=self.libs[0];data=ctypes.create_string_buffer(self.data)
  for fail in range(4):
   lib.host_alloc_fail(fail);v=lib.adv_video_open(data,len(self.data),208,272)
   self.assertFalse(v,fail);self.assertEqual(lib.host_alloc_live(),0,fail)
 def test_optimized_bilinear_matches_original_for_all5606400_pixels(self):
  lib=self.libs[0];data=ctypes.create_string_buffer(self.data);v=lib.adv_video_open(data,len(self.data),208,272)
  self.assertTrue(v);count=0
  while lib.adv_video_next(v):
   self.assertEqual(lib.host_reference_frame(v),0,f'frame{count}');count+=1
  lib.adv_video_close(v);self.assertEqual(count,73)
 def test_invalid_header_and_dimensions_are_rejected_before_decoder_allocation(self):
  lib=self.libs[0]
  for data,w,h in [(self.data,144,192),(b'no',208,272),(b'bad!'+self.data[4:],208,272)]:
   b=ctypes.create_string_buffer(data);self.assertFalse(lib.adv_video_open(b,len(data),w,h))
  self.assertEqual(lib.host_alloc_calls(),0)
 def test_row_bounds_and_partial_clips_equal_full_row_without_overwrites(self):
  lib=self.libs[0];data=ctypes.create_string_buffer(self.data);v=lib.adv_video_open(data,len(self.data),208,272)
  self.assertTrue(v);self.assertTrue(lib.adv_video_next(v));self.assertEqual(lib.adv_video_reference_bytes(v),169728)
  full=(ctypes.c_uint16*240)();partial=(ctypes.c_uint16*242)(*([0xabcd]*242))
  for y in (0,1,159,255,300,319):
   lib.adv_video_row(v,y,0,240,full);lib.adv_video_row(v,y,20,220,ctypes.byref(partial,2))
   self.assertEqual(list(partial)[1:201],list(full)[20:220]);self.assertEqual(partial[0],0xabcd);self.assertTrue(all(x==0xabcd for x in list(partial)[201:]))
  self.assertNotEqual(list(full),[0]*240)
  lib.adv_video_close(v);self.assertEqual(lib.host_alloc_live(),0)
 def test_poster_is_one_independent_intra_frame_and_repeated_opens_release_all_references(self):
  lib=self.libs[0];data=ctypes.create_string_buffer((ART/'boot/v3/runtime/cover-poster.m1v').read_bytes())
  for _ in range(12):
   v=lib.adv_video_open(data,len(data)-1,208,272);self.assertTrue(v);self.assertTrue(lib.adv_video_next(v));self.assertFalse(lib.adv_video_next(v));lib.adv_video_close(v)
   self.assertEqual(lib.host_alloc_live(),0)
 def test_manifest_binds_voice_sources_and_charges_both_movie_and_static_poster(self):
  selected=read_video();v=selected['value'];self.assertEqual(v['logical_fps'],12)
  self.assertEqual(selected['bytes'],sum(v[k]['bytes'] for k in ('movie','poster'))+32)
  self.assertEqual(v['timeline']['terminal_frame'],72);self.assertEqual(v['timeline']['voice_end_ms'],4090.625)
  report=json.loads((BOARD/'generated/adv_assets_generated.json').read_text('utf-8'))['startup_composition']
  self.assertEqual(report['boot_video_bytes'],selected['bytes']);self.assertEqual(report['combined_estimate_c3'],report['ui_assets_estimate_c3']+selected['bytes'])
  self.assertLessEqual(report['combined_estimate_c3'],report['limit_bytes'])
 def test_compiled_flash_arrays_equal_selected_media_byte_for_byte(self):
  lib=self.libs[0]
  for name in ('movie','poster'):
   file='boot-welcome.m1v' if name=='movie' else 'cover-poster.m1v'
   data=(ART/'boot/v3/runtime'/file).read_bytes();symbol='adv_boot_video_'+name
   size=ctypes.c_size_t.in_dll(lib,symbol+'_bytes').value
   self.assertEqual(size,len(data));self.assertEqual(bytes((ctypes.c_uint8*size).in_dll(lib,symbol)),data)
 def test_profile_rejects_b_frames_wrong_dimensions_missing_frame_or_end_marker(self):
  stream(self.data,73)
  picture=self.data.index(b'\0\0\1\0')+4;bad=bytearray(self.data);bad[picture+1]=(bad[picture+1]&~56)|24
  dim=bytearray(self.data);dim[4]^=1
  for data,frames in [(bad,73),(dim,73),(self.data,72),(self.data[:-4],73)]:
   with self.assertRaises(ValueError):stream(bytes(data),frames)
