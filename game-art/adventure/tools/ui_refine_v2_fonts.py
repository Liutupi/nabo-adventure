"""Verified original open-font files, native 1x rasterization and audit metrics."""
import hashlib
import json
from pathlib import Path
import struct
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'game-art/adventure/art';OUT=ART/'ui/design/refinement-v2'
SOURCES={
 'bold':{'path':'C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf','sha256':'d1961be1161ea1be08496c920862d06ea5c23a757628f4fd69368de1d9f51bed','family':'Noto Sans SC','weight':700},
 'medium':{'path':str(ROOT.parent/'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf'),'sha256':'a94e558a2fe972bee4f46bce0843abff37063fd68c33f1e7d9058f6f09432b01','family':'Source Han Sans CN','weight':500},
 'latin':{'path':str(ROOT.parent/'table-undercover/repo/xiaozhi-esp32/managed_components/lvgl__lvgl/tests/src/test_files/fonts/Montserrat-Bold.ttf'),'sha256':'06a0e623bbaf4a0237f1d605affa269f9e431ff50c7143dcbb47b815edaba9bd','family':'Montserrat','weight':700},
}
P=json.loads((ART/'ui/design/round3/01-passport/palette.json').read_text('utf-8'))
P.update(coolgray='#60707a',rule='#dcdcd3',surface='#f1eee5')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb(c):return tuple(bytes.fromhex(P.get(c,c).lstrip('#')))
def color(c):return (*rgb(c),255)
def write_json(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')


def metadata(path):
    data=Path(path).read_bytes();tables={}
    for i in range(struct.unpack_from('>H',data,4)[0]):
        tag,_,off,length=struct.unpack_from('>4sIII',data,12+i*16);tables[tag.decode()]=(off,length)
    start=tables['name'][0];_,count,storage=struct.unpack_from('>HHH',data,start);names={}
    for i in range(count):
        platform,encoding,language,nameid,length,off=struct.unpack_from('>HHHHHH',data,start+6+12*i)
        if nameid not in (0,1,2,4,5,8,13,14):continue
        raw=data[start+storage+off:start+storage+off+length]
        text=raw.decode('utf-16-be' if platform in (0,3) else 'mac_roman',errors='replace')
        names.setdefault(str(nameid),set()).add(text)
    return {'names':{k:sorted(v) for k,v in names.items()},'weight':struct.unpack_from('>H',data,tables['OS/2'][0]+4)[0],
            'fsType':struct.unpack_from('>H',data,tables['OS/2'][0]+8)[0],'variable':'fvar' in tables}


class Type:
    def __init__(self):
        self.fonts={};self.runs=[];self.sources={}
        for key,s in SOURCES.items():
            if sha(s['path'])!=s['sha256']:raise ValueError('Verified original font changed: '+s['path'])
            info=metadata(s['path'])
            if info['fsType']!=0 or info['variable']:raise ValueError('Only verified static embeddable original files are used')
            if not any('OFL' in x or 'Open Font License' in x for n in ('13','14') for x in info['names'].get(n,[])):
                raise ValueError('Missing explicit open-font licensing metadata')
            self.sources[key]={**s,**info,'operation':'read original file for preview; no font conversion or redistribution'}

    def get(self,key,size):
        pair=(key,size)
        if pair not in self.fonts:self.fonts[pair]=ImageFont.truetype(SOURCES[key]['path'],size)
        return self.fonts[pair]

    def mask(self,text,key,size,tracking=0):
        font=self.get(key,size)
        for c in text:
            if c.isspace():continue
            if bytes(font.getmask(c))==bytes(font.getmask(chr(0x10ffff))):raise ValueError('Missing real glyph: '+c)
        if not tracking:
            box=font.getbbox(text);mask=Image.new('L',(max(1,box[2]-box[0]),max(1,box[3]-box[1])))
            ImageDraw.Draw(mask).text((-box[0],-box[1]),text,font=font,fill=255);return mask
        heights=[font.getbbox(c) for c in text];adv=[round(font.getlength(c)) for c in text]
        top=min(b[1] for b in heights);bottom=max(b[3] for b in heights)
        mask=Image.new('L',(sum(adv)+tracking*(len(text)-1),bottom-top));d=ImageDraw.Draw(mask);x=0
        for c,a in zip(text,adv):d.text((x,-top),c,font=font,fill=255);x+=a+tracking
        return mask

    def draw(self,canvas,xy,text,size=16,key='bold',ink='ink',paper='white',align='left',tracking=0,slot=None):
        mask=self.mask(text,key,size,tracking);x,y=xy
        if align=='center':x-=mask.width//2
        if align=='right':x-=mask.width
        box=[x,y,x+mask.width,y+mask.height]
        if x<0 or y<0 or box[2]>canvas.width or box[3]>canvas.height:raise ValueError(('clipped text',text,box))
        if slot and not (x>=slot[0]+8 and y>=slot[1]+8 and box[2]<=slot[2]-8 and box[3]<=slot[3]-8):
            raise ValueError(('text violates 8px padding',text,box,slot))
        fore,back=rgb(ink),rgb(paper);mid=tuple((a+b+1)//2 for a,b in zip(fore,back))
        # Three coverage values consume two bits and add only one edge color.
        edge=mask.point(lambda a:255 if 43<=a<213 else 0);solid=mask.point(lambda a:255 if a>=213 else 0)
        canvas.paste((*mid,255),(x,y),edge);canvas.paste((*fore,255),(x,y),solid)
        self.runs.append({'text':text,'font':key,'size_px':size,'weight':SOURCES[key]['weight'],'tracking_px':tracking,
                          'ink_box':box,'slot':slot,'coverage_levels':[0,128,255]})
        return box
