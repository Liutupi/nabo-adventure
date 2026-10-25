"""Copy only used legacy glyphs, retaining every original pixel and metric."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'game-art/adventure/font-source'
NAMES=('nabo_menu_font_16','nabo_ui_font_18')
FIELDS=('bitmap_index','adv_w','box_w','box_h','ofs_x','ofs_y')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def region(text,name):
 m=re.search(r'\b'+name+r'\[\]\s*=\s*\{(.*?)\n\};',text,re.S)
 if not m:raise ValueError('Missing font array '+name)
 return m
def numbers(value):
 value=re.sub(r'/\*.*?\*/','',value,flags=re.S)
 return [int(v,0) for v in re.findall(r'0x[0-9a-fA-F]+|\b\d+\b',value)]
def parse(text):
 bitmap=bytes(numbers(region(text,'glyph_bitmap').group(1)))
 descriptors=[]
 for block in re.findall(r'\{([^{}]+)\}',region(text,'glyph_dsc').group(1)):
  fields={k:int(v) for k,v in re.findall(r'\.(\w+)\s*=\s*(-?\d+)',block)}
  if set(fields)!=set(FIELDS):raise ValueError('Unexpected glyph fields')
  descriptors.append(fields)
 unicode=numbers(region(text,'unicode_list_1').group(1))
 # The two immutable source files use exactly these two unkerned maps.
 if '.range_start = 32, .range_length = 95, .glyph_id_start = 1' not in text or '.range_start = 183,' not in text or '.bitmap_format = 0,' not in text or '.kern_dsc = NULL,' not in text:
  raise ValueError('Unsupported font source contract')
 chars=[None,*map(chr,range(32,127)),*(chr(183+c) for c in unicode)]
 if len(chars)!=len(descriptors):raise ValueError('Glyph/map count mismatch')
 result={}
 for char,d in zip(chars,descriptors):
  count=(d['box_w']*d['box_h']+1)//2;offset=d['bitmap_index']
  data=bitmap[offset:offset+count]
  if len(data)!=count:raise ValueError('Truncated glyph')
  result[char]=({k:d[k] for k in FIELDS if k!='bitmap_index'},data)
 return result
def used_chars():
 text=(ROOT/'firmware/main/nabo_dive_render.c').read_text('utf-8')
 # Include all literal characters conservatively, even literals drawn by other fonts.
 literals=re.findall(r'"((?:[^"\\]|\\.)*)"',text)
 return set(map(chr,range(32,127)))|{c for s in literals for c in s if ord(c)>126}
def subset(text,keep):
 old=parse(text)
 if keep-set(old):raise ValueError('Source lacks requested glyphs')
 chosen=[None,*sorted(keep,key=ord)];bitmap=bytearray();blocks=[];descriptors=[]
 for c in chosen:
  metric,data=old[c];descriptor={'bitmap_index':len(bitmap),**metric};bitmap.extend(data)
  blocks.append(('    /* U+%04X */'%ord(c) if c else '    /* missing glyph */')+'\n    '+', '.join('0x%02x'%v for v in data)+(',' if data else ''))
  descriptors.append('    {'+', '.join('.%s = %d'%(k,descriptor[k]) for k in FIELDS)+'},')
 for name,value in [('glyph_bitmap','\n'+'\n'.join(blocks)),('glyph_dsc','\n'+'\n'.join(descriptors)),('unicode_list_1','\n    '+', '.join('0x%x'%(ord(c)-183) for c in chosen[96:]))]:
  m=region(text,name);text=text[:m.start(1)]+value+text[m.end(1):]
 text=re.sub(r'\.list_length = 525,',f'.list_length = {len(chosen)-96},',text)
 new=parse(text)
 if any(new[c]!=old[c] for c in chosen):raise ValueError('Subset changed pixels or metrics')
 return '\n'.join(line.rstrip() for line in text.splitlines())+'\n',len(bitmap),len(chosen)-1
def main():
 keep=used_chars();report={'policy':'Original 4bpp pixels and all metrics retained; unused glyphs only removed','source_files':{},'outputs':{}}
 for name in NAMES:
  p=SOURCE/(name+'.c');text=p.read_text('utf-8');result,size,count=subset(text,keep)
  out=ROOT/'firmware/main'/(name+'.c');out.write_text('/* Lossless used-glyph subset; regenerate with tools/subset_legacy_fonts.py. */\n'+result,'utf-8',newline='\n')
  report['source_files'][p.relative_to(ROOT).as_posix()]=sha(p)
  report['outputs'][name]={'sha256':sha(out),'glyphs':count,'bitmap_bytes':size,'source_glyphs':len(parse(text))-1}
 (ROOT/'firmware/tools/legacy-font-subsets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
