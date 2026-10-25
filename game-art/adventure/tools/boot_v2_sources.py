"""Audited original three-expression heads and an existing NABO open palm."""
import json
import hashlib
import io
import base64
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont

BASE=Path(__file__).resolve().parents[1];ART=BASE/'art';OUT=ART/'boot/v2';SRC=OUT/'source';PREVIEW=ART/'preview/boot-v2'
SW=Path(r'D:\AI PASSPORT XIAOZHI\nabo-sound-lab\game-art\soundlab\grok-clips\S-WELCOME.mp4')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def svg(image,name,metadata):
 data=io.BytesIO();image.save(data,'PNG');encoded=base64.b64encode(data.getvalue()).decode('ascii')
 return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">\n'
  f'<title>{name}: source-pixel rig layer</title><metadata>'+json.dumps(metadata)+'</metadata>\n'
  f'<image width="256" height="256" href="data:image/png;base64,{encoded}"/></svg>\n')


def union(frames):
 mask=np.maximum.reduce([np.asarray(f.getchannel('A'))>=128 for f in frames]);y,x=np.where(mask)
 return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]


def text(draw,xy,message,size=14,fill='#203849'):
 font=BASE.parents[1].parent/'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf'
 draw.text(xy,message,font=ImageFont.truetype(str(font),size),fill=fill)


def palm_pixels(frame_path,cropbox,size,name,wrist,timestamp):
 raw=Image.open(frame_path).convert('RGB');crop=raw.crop(cropbox);rgb=np.asarray(crop).astype(int)
 skin=(rgb[:,:,0]>=150)&(rgb[:,:,1]>=90)&(rgb[:,:,2]>=65)&(rgb[:,:,0]>rgb[:,:,1])&(rgb[:,:,0]>rgb[:,:,2])
 alpha=np.asarray(Image.fromarray(skin.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))).copy()
 alpha[(rgb[:,:,1]>rgb[:,:,0]*1.25)&(rgb[:,:,1]>rgb[:,:,2]*1.25)]=0
 if name=='palm-half':
  yy,_=np.indices(alpha.shape)
  # This frame's pink source cuff begins beside the wrist at y406. Exclude it
  # by alpha only; the fingers' genuine pink shadows above that row stay intact.
  alpha[((yy+cropbox[1]>=406)&(rgb[:,:,2]>rgb[:,:,1]))|(yy+cropbox[1]>=425)]=0
 active=alpha>0;seen=np.zeros(active.shape,bool);best=[]
 for sy,sx in zip(*np.where(active)):
  if seen[sy,sx]:continue
  pending=[(int(sy),int(sx))];seen[sy,sx]=True;component=[]
  while pending:
   y,x=pending.pop();component.append((y,x))
   for dy in (-1,0,1):
    for dx in (-1,0,1):
     yy,xx=y+dy,x+dx
     if 0<=yy<active.shape[0] and 0<=xx<active.shape[1] and active[yy,xx] and not seen[yy,xx]:
      seen[yy,xx]=True;pending.append((yy,xx))
  if len(component)>len(best):best=component
 cleaned=np.zeros_like(alpha)
 for y,x in best:cleaned[y,x]=alpha[y,x]
 crop=crop.convert('RGBA');crop.putalpha(Image.fromarray(cleaned));crop.save(SRC/(name+'-source-roi.png'))
 small=crop.resize(tuple(size),Image.Resampling.LANCZOS);path=SRC/(name+'.png');small.save(path)
 return dict(path=path.relative_to(ART).as_posix(),sha256=sha(path),source_video=str(SW),source_video_sha256=sha(SW),
  timestamp_s=timestamp,frame_size=list(raw.size),roi=cropbox,frame_sha256=sha(frame_path),size=size,wrist_anchor=wrist,
  extraction='Original skin and adjacent source outline, largest connected component; alpha-only removal of green/backdrop; no new fingers, cuff or headphones')


def build():
 SRC.mkdir(parents=True,exist_ok=True);PREVIEW.mkdir(parents=True,exist_ok=True)
 strip_path=ART/'reference/nabo-idle.png';assert sha(strip_path)=='c63575691d15220e8d6fafdab911a10767a5fc1c13925992dbd10e3a5e93d3fa'
 strip=Image.open(strip_path).convert('RGB');heads=[]
 for index,name in enumerate(('open','half','closed')):
  raw=strip.crop((index*224,0,(index+1)*224,224)).convert('RGBA');rgb=np.asarray(raw).astype(int)
  yy,xx=np.indices((224,224));visible=rgb[:,:,:3].max(2)>10
  skin=(rgb[:,:,0]>rgb[:,:,1]+5)&(rgb[:,:,0]>rgb[:,:,2]+10)&(rgb[:,:,1]>40)
  backdrop=np.zeros(visible.shape,bool);pending=[(0,0)];backdrop[0,0]=True
  while pending:
   y,x=pending.pop()
   for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
    ny,nx=y+dy,x+dx
    if 0<=ny<224 and 0<=nx<224 and not backdrop[ny,nx] and not visible[ny,nx]:
     backdrop[ny,nx]=True;pending.append((ny,nx))
  keep=(~backdrop)&(yy<=163)&((yy<150)|((xx>=93)&(xx<=130)&skin))
  raw.putalpha(Image.fromarray(keep.astype('uint8')*255));layer=Image.new('RGBA',(256,256))
  layer.alpha_composite(raw.resize((123,123),Image.Resampling.LANCZOS),(66,9))
  path=SRC/('head-'+name+'.png');layer.save(path)
  meta=dict(source='reference/nabo-idle.png',source_sha256=sha(strip_path),source_frame=index,source_cell=[index*224,0,(index+1)*224,224],
   sampling=dict(size=[123,123],paste=[66,9]),mask='RGB-black backdrop excluded; y150..163 only original warm neck/face pixels, no doctor coat')
  path.with_suffix('.svg').write_text(svg(layer,'native-'+name,meta),'utf-8');heads.append(dict(name=name,path=path.relative_to(ART).as_posix(),sha256=sha(path),**meta))
 # Real opening hand at 3.25s bridges the earlier closed hand and the 3.65s open palm.
 palm=palm_pixels(SRC/'s-welcome-hand-reference.png',[638,158,774,354],[19,28],'palm-open',[12,27],3.65)
 half=palm_pixels(SRC/'s-welcome-hand-3p25.png',[674,250,792,434],[17,26],'palm-half',[9,24],3.25)
 half['additional_alpha_mask']='Original pink cuff excluded at source y>=406 where B>G; y>=425 removed. Wrist registered at original source (736.5,419.8).'
 result=dict(native_heads=heads,palm=palm,half_palm=half,identity_policy='Official native three-expression NABO head; no generated face. Frozen common files unchanged.',
  expression_boundary='Whole registered head variants are used; no eye fragment pasted into a different face')
 (SRC/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
 # Actual tiny head and palm fit board, kept as evidence rather than an automatic identity pass.
 board=Image.new('RGB',(1190,300),'#e1ecf8');d=ImageDraw.Draw(board)
 for i,h in enumerate(heads):
  im=Image.open(ART/h['path']).convert('RGBA');board.paste(im,(i*256,30),im);d.text((i*256+8,8),h['name']+' native source',fill='#203849')
 for x,record,label in ((800,palm,'open'),(1000,half,'half-open')):
  small=Image.open(ART/record['path']);large=small.resize((small.width*8,small.height*8),Image.Resampling.NEAREST)
  board.paste(large,(x,40),large);d.text((x,8),'existing '+label+' / 8x',fill='#203849')
 board.save(PREVIEW/'source-parts-review.png')
 return result


if __name__=='__main__':build()
