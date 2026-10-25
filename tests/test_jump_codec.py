"""Every original pixel/sample must survive the seekable asset codecs exactly."""
import ctypes
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from host_tools import CC,SHARED_EXPORT,unload_library
ROOT=Path(__file__).resolve().parents[1];BOARD=ROOT/'firmware/main'
sys.path.insert(0,str(ROOT/'tools'))
from compress_jump_assets import build

class JumpCodec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();target=Path(cls.temp.name)/'codec.dll'
        subprocess.run([CC,'-std=c11','-O2','-shared',SHARED_EXPORT,'-Wall','-Wextra','-Werror',str(BOARD/'nabo_jump_codec.c'),'-o',str(target)],check=True)
        cls.lib=ctypes.CDLL(str(target))
        for name,kind in [('nabo_jump_decode_platform',ctypes.c_uint16),('nabo_jump_decode_pcm_block',ctypes.c_int16)]:
            f=getattr(cls.lib,name);f.restype=ctypes.c_bool
            f.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint]+([ctypes.c_uint] if name.endswith('platform') else [])+[ctypes.POINTER(kind),ctypes.c_size_t]
        cls.pixels=(BOARD/'jump_sprites.bin').read_bytes();cls.pcm=(BOARD/'jump_sounds.bin').read_bytes()
        cls.raw_pixels=(ROOT/'game-art/jump/source/jump_sprites.raw.bin').read_bytes();cls.raw_pcm=(ROOT/'game-art/jump/source/jump_sounds.pcm.bin').read_bytes()
    @classmethod
    def tearDownClass(cls):unload_library(cls.lib._handle);cls.temp.cleanup()
    def platform(self,data,skin=0,y=0,capacity=96):
        out=(ctypes.c_uint16*98)(*([0x5aa5]*98));pointer=ctypes.cast(ctypes.byref(out,2),ctypes.POINTER(ctypes.c_uint16))
        ok=self.lib.nabo_jump_decode_platform(ctypes.create_string_buffer(data),len(data),skin,y,pointer,capacity)
        self.assertEqual((out[0],out[-1]),(0x5aa5,0x5aa5));return ok,list(out)[1:-1]
    def audio(self,data,block=0,capacity=256):
        out=(ctypes.c_int16*258)(*([0x5aa5]*258));pointer=ctypes.cast(ctypes.byref(out,2),ctypes.POINTER(ctypes.c_int16))
        ok=self.lib.nabo_jump_decode_pcm_block(ctypes.create_string_buffer(data),len(data),block,pointer,capacity)
        self.assertEqual((out[0],out[-1]),(0x5aa5,0x5aa5));return ok,list(out)[1:-1]
    def test_sources_are_the_original_accepted_assets(self):
        self.assertEqual(hashlib.sha256(self.raw_pixels).hexdigest(),'6d361d6df49837c33a015421e27df1cf5215365131449b1d887f715a8cfbaf61')
        self.assertEqual(hashlib.sha256(self.raw_pcm).hexdigest(),'5f8613c19ec519ec38fed11e6ac8599a6dc3553a33136c3a79f89f1617f0cbde')
    def test_all_platform_rows_and_character_pixels_are_exact(self):
        for skin in range(6):
            for y in range(96):
                ok,row=self.platform(self.pixels,skin,y);self.assertTrue(ok)
                self.assertEqual(row,list(struct.unpack_from('<96H',self.raw_pixels,(skin*96+y)*192)))
        character=struct.unpack_from('<I',self.pixels,16)[0]
        self.assertEqual(self.pixels[character:],self.raw_pixels[6*96*96*2:])
    def test_every_pcm_sample_decodes_exactly_in_arbitrary_block_order(self):
        count,block_size,blocks=struct.unpack_from('<IHH',self.pcm,4)
        expected=struct.unpack('<'+'h'*count,self.raw_pcm);self.assertEqual(block_size,256)
        for block in list(range(blocks))[::2]+list(range(blocks))[1::2]:
            ok,values=self.audio(self.pcm,block);self.assertTrue(ok)
            n=min(256,count-block*256);self.assertEqual(values[:n],list(expected[block*256:block*256+n]))
            self.assertEqual(values[n:],[0]*(256-n))
    def test_build_is_reproducible_and_saves_over160000_bytes(self):
        files,report=build()
        for path,data in files.items():self.assertEqual((ROOT/path).read_bytes(),data,path)
        self.assertGreater(report['data_bytes_saved'],160000)
    def test_pixel_decoder_rejects_truncation_bad_offsets_tokens_and_small_buffers(self):
        for length in [0,3,23,len(self.pixels)-1]:self.assertFalse(self.platform(self.pixels[:length])[0])
        self.assertFalse(self.platform(self.pixels,6)[0]);self.assertFalse(self.platform(self.pixels,y=96)[0]);self.assertFalse(self.platform(self.pixels,capacity=95)[0])
        for offset,blob in [(0,b'BAD!'),(24,struct.pack('<I',0xffffffff)),(24+4,struct.pack('<I',0))]:
            data=bytearray(self.pixels);data[offset:offset+len(blob)]=blob;self.assertFalse(self.platform(bytes(data))[0])
        data=bytearray(self.pixels);start=struct.unpack_from('<I',data,24)[0];data[start]=0
        self.assertFalse(self.platform(bytes(data))[0])
    def test_pcm_decoder_rejects_malformed_headers_and_offsets_without_overrun(self):
        for length in [0,3,15,len(self.pcm)-1]:self.assertFalse(self.audio(self.pcm[:length])[0])
        self.assertFalse(self.audio(self.pcm,99999)[0]);self.assertFalse(self.audio(self.pcm,capacity=255)[0])
        for offset,blob in [(0,b'BAD!'),(4,b'\0'*4),(16,struct.pack('<I',0xffffffff)),(20,struct.pack('<I',0))]:
            data=bytearray(self.pcm);data[offset:offset+len(blob)]=blob;self.assertFalse(self.audio(bytes(data))[0])
        data=bytearray(self.pcm);start=struct.unpack_from('<I',data,16)[0];data[start]=16
        self.assertFalse(self.audio(bytes(data))[0])
    def test_pcm_raw_tiny_blocks_overflow_and_padding_are_checked(self):
        def stream(count,payload):return struct.pack('<4sIHHIII',b'JPC1',count,256,1,24,24,24+len(payload))+payload
        for values in [[-32768],[32767,-32768,0]]:
            ok,actual=self.audio(stream(len(values),b'\xff'+struct.pack('<'+'h'*len(values),*values)));self.assertTrue(ok);self.assertEqual(actual[:len(values)],values)
        self.assertFalse(self.audio(stream(3,b'\0'+struct.pack('<hh',32767,32767)+b'\xc0'))[0])
        self.assertFalse(self.audio(stream(3,b'\0'+struct.pack('<hh',0,0)+b'\x01'))[0])
        self.assertFalse(self.audio(stream(3,b'\0'+struct.pack('<hh',0,0)+b'\0\0'))[0])

if __name__=='__main__':unittest.main()
