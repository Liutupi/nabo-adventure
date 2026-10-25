"""Losslessly pack original jump pixels/PCM; decode every value before writing.

JPS1 stores independent RGB565 PackBits rows and unchanged character RGB.
JPC1 stores independently seekable256-sample second-order Rice blocks.
No palette reduction, resampling, gain, trimming or source artwork changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
BLOCK=256
def sha(data):return hashlib.sha256(data).hexdigest()

def row_encode(row):
    out=bytearray();i=0
    while i<len(row):
        n=1
        while i+n<len(row) and row[i+n]==row[i] and n<127:n+=1
        if n>=2:out.extend([128|n,row[i]&255,row[i]>>8]);i+=n
        else:
            values=[row[i]];i+=1
            while i<len(row) and len(values)<127:
                if i+1<len(row) and row[i]==row[i+1]:break
                values.append(row[i]);i+=1
            out.append(len(values))
            for value in values:out.extend(struct.pack('<H',value))
    return bytes(out)

def row_decode(data):
    out=[];i=0
    while i<len(data):
        token=data[i];i+=1;n=token&127
        if not n:raise ValueError('zero row token')
        if token&128:
            value=struct.unpack_from('<H',data,i)[0];i+=2;out.extend([value]*n)
        else:out.extend(struct.unpack_from('<'+'H'*n,data,i));i+=2*n
    if i!=len(data) or len(out)!=96:raise ValueError('invalid row length')
    return out

def sprites(raw):
    assert len(raw)==6*96*96*2+36*64*3
    chunks=[]
    for pos in range(0,6*96*96*2,192):
        row=struct.unpack_from('<96H',raw,pos);encoded=row_encode(row)
        assert row_decode(encoded)==list(row)
        chunks.append(encoded)
    offset=24+(len(chunks)+1)*4;offsets=[offset]
    for chunk in chunks:offsets.append(offsets[-1]+len(chunk))
    character=raw[6*96*96*2:];total=offsets[-1]+len(character)
    data=struct.pack('<4sHHHHIII',b'JPS1',96,96,6,0,offset,offsets[-1],total)
    data+=struct.pack('<'+'I'*len(offsets),*offsets)+b''.join(chunks)+character
    assert len(data)==total and data[offsets[-1]:]==character
    return data,offsets[-1]

class Bits:
    def __init__(self):self.data=bytearray();self.value=self.count=0
    def bit(self,value):
        self.value=(self.value<<1)|value;self.count+=1
        if self.count==8:self.data.append(self.value);self.value=self.count=0
    def finish(self):
        if self.count:self.data.append(self.value<<(8-self.count))
        return bytes(self.data)

def pcm_encode(values):
    raw=b'\xff'+struct.pack('<'+'h'*len(values),*values)
    if len(values)<2:return raw
    diffs=[values[i]-2*values[i-1]+values[i-2] for i in range(2,len(values))]
    unsigned=[2*d if d>=0 else -2*d-1 for d in diffs]
    k=min(range(16),key=lambda k:sum((u>>k)+1+k for u in unsigned))
    if 5+(sum((u>>k)+1+k for u in unsigned)+7)//8>=len(raw):return raw
    bits=Bits()
    for value in unsigned:
        for _ in range(value>>k):bits.bit(1)
        bits.bit(0)
        for bit in reversed(range(k)):bits.bit((value>>bit)&1)
    return bytes([k])+struct.pack('<hh',*values[:2])+bits.finish()

def pcm_decode(data,count):
    if data[0]==255:return list(struct.unpack('<'+'h'*count,data[1:]))
    k=data[0];out=list(struct.unpack_from('<hh',data,1));position=40
    def bit():
        nonlocal position
        value=(data[position//8]>>(7-position%8))&1;position+=1;return value
    while len(out)<count:
        q=0
        while bit():q+=1
        rem=0
        for _ in range(k):rem=rem*2+bit()
        u=(q<<k)|rem;delta=(u//2) if not u&1 else -(u//2)-1
        value=2*out[-1]-out[-2]+delta
        assert -32768<=value<=32767;out.append(value)
    assert (position+7)//8==len(data)
    return out

def audio(raw):
    values=struct.unpack('<'+'h'*(len(raw)//2),raw);chunks=[]
    for pos in range(0,len(values),BLOCK):
        source=values[pos:pos+BLOCK];encoded=pcm_encode(source)
        assert pcm_decode(encoded,len(source))==list(source)
        chunks.append(encoded)
    offset=16+(len(chunks)+1)*4;offsets=[offset]
    for chunk in chunks:offsets.append(offsets[-1]+len(chunk))
    data=struct.pack('<4sIHHI',b'JPC1',len(values),BLOCK,len(chunks),offset)
    data+=struct.pack('<'+'I'*len(offsets),*offsets)+b''.join(chunks)
    return data,len(values),sum(chunk[0]==255 for chunk in chunks)

def build():
    source=ROOT/'game-art/jump/source'
    raw_pixels=(source/'jump_sprites.raw.bin').read_bytes();raw_pcm=(source/'jump_sounds.pcm.bin').read_bytes()
    pixels,character=sprites(raw_pixels);pcm,count,raw_blocks=audio(raw_pcm)
    report={'format_pixels':'JPS1','format_audio':'JPC1','lossless':True,
      'pixels':{'source_bytes':len(raw_pixels),'source_sha256':sha(raw_pixels),'packed_bytes':len(pixels),'packed_sha256':sha(pixels),'character_offset':character,'rows_verified':576},
      'pcm':{'source_bytes':len(raw_pcm),'source_sha256':sha(raw_pcm),'packed_bytes':len(pcm),'packed_sha256':sha(pcm),'samples_verified':count,'block_samples':BLOCK,'raw_blocks':raw_blocks}}
    report['data_bytes_saved']=len(raw_pixels)+len(raw_pcm)-len(pixels)-len(pcm)
    header=('// Generated by tools/compress_jump_assets.py; source assets remain untouched.\n#pragma once\n'
       f'#define JUMP_PACKED_SPRITES_BYTES {len(pixels)}u\n#define JUMP_CHARACTER_OFFSET {character}u\n'
       f'#define JUMP_PACKED_SOUND_BYTES {len(pcm)}u\n#define JUMP_PCM_SAMPLES {count}u\n#define JUMP_PCM_BLOCK_SAMPLES {BLOCK}u\n')
    return {'firmware/main/jump_sprites.bin':pixels,'firmware/main/jump_sounds.bin':pcm,
      'firmware/main/jump_codec_generated.h':header.encode(),
      'game-art/jump/codec.json':(json.dumps(report,indent=2)+'\n').encode()},report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    files,report=build()
    for relative,data in files.items():
        target=ROOT/relative
        if args.check:
            if not target.exists() or target.read_bytes()!=data:raise ValueError('Stale compressed jump asset: '+relative)
        else:
            temporary=target.with_name(target.name+'.tmp');temporary.write_bytes(data);temporary.replace(target)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
