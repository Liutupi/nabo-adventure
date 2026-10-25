#!/usr/bin/env python3
"""Build round-four shared static art at native size; no character drawing or firmware writes."""
from pathlib import Path
import argparse
import hashlib
import json
import re
from PIL import Image,ImageDraw,ImageFont
from shared_static_tiles import TILESETS,ALIASES,REPEAT,tile
from shared_static_landmarks import NAMES,landmark
from shared_static_marks import ICONS,stamp,icon

HERE=Path(__file__).resolve().parent
BASE=HERE.parent;ROOT=BASE.parents[1];ART=BASE/'art';PREVIEW=ART/'preview/shared-static'
PALETTE=ART/'ui/design/round3/01-passport/palette.json'
WORLD_ORDER=list(TILESETS)
WORLD_CN=['深海','港口','小镇','铁路平原','夜林','雪山','雪坡','云端','太空']
STATION_WORLD=dict(kiosk='harbor',jump='town',dive='deep-sea',post='rail',night='night-forest',
                   climb='mountain',ski='ski',sky='sky',space='space')
ICON_WORLD=dict(oxygen='deep-sea',stamina='town',steam='rail',spirit='night-forest',
                warmth='ski',**{'hot-air':'sky'},fuel='space')
FONT_SHA='a94e558a2fe972bee4f46bce0843abff37063fd68c33f1e7d9058f6f09432b01'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pixels(image):return image.get_flattened_data() if hasattr(image,'get_flattened_data') else image.getdata()
def relative(path):return Path(path).relative_to(ART).as_posix()
def rgb565(rgb):return ((rgb[0]>>3)<<11)|((rgb[1]>>2)<<5)|(rgb[2]>>3)
def expanded(value):return ((value>>11)*255//31,((value>>5)&63)*255//63,(value&31)*255//31)


def current_backgrounds():
 path=ROOT/'firmware/main/adv_ui_map.c';source=path.read_text('utf-8')
 block=re.search(r'WORLD\[ADV_STATIONS\]\s*=\s*\{(.*?)\};',source,re.S)
 assert block,'Actual WORLD palette no longer matches the source contract'
 rows=[tuple(map(int,row)) for row in re.findall(r'\{\s*(\d+),\s*(\d+),\s*(\d+)\s*\}',block[1])]
 assert len(rows)==9
 return {name:dict(source_rgb=list(rgb),rgb565=f'0x{rgb565(rgb):04x}',
                   preview_rgb=list(expanded(rgb565(rgb)))) for name,rgb in zip(WORLD_ORDER,rows)},path


def current_ui_colors():
 path=ROOT/'firmware/main/adv_ui_internal.h';source=path.read_text('utf-8');colors={}
 for name in ('UI_INK','UI_BRONZE'):
  match=re.search(r'#define\s+'+name+r'\s+(0x[0-9a-fA-F]+)',source)
  assert match,'Actual UI preview color no longer matches the source contract: '+name
  colors[name]=int(match[1],16)
 return colors,path


def flatten(image,bg,tint=None):
 result=Image.new('RGB',image.size,tuple(bg) if isinstance(bg,list) else bg)
 if tint:result.paste(tint,(0,0,image.width,image.height),image.getchannel('A'))
 else:result.paste(image,(0,0),image)
 return result


def text(draw,xy,message,size=14,color='#203849'):
 draw.text(xy,message,font=ImageFont.truetype(str(FONT),size),fill=color)


def verify(asset):
 image=Image.open(ART/asset['path']).convert('RGBA');size=image.width
 visible={pixel[:3] for pixel in pixels(image) if pixel[3]}
 allcolors=set(pixels(image));alpha=image.getchannel('A');bbox=alpha.getbbox()
 errors=[]
 if image.size!=tuple(asset['size']):errors.append('size')
 if not visible or len(allcolors)>asset['color_limit']:errors.append('color count')
 if set(pixels(alpha))!={0,255}:errors.append('binary transparent alpha')
 if asset['category']=='stamp' and visible!={(255,255,255)}:errors.append('stamp must be single white')
 wrap=asset.get('repeat_axes','')
 margins=[bbox[0],bbox[1],size-bbox[2],size-bbox[3]]
 if 'x' not in wrap and (margins[0]<1 or margins[2]<1):errors.append('horizontal crop margin')
 if 'y' not in wrap and (margins[1]<1 or margins[3]<1):errors.append('vertical crop margin')
 seams={}
 if 'x' in wrap:
  seams['x']=image.crop((0,0,1,size)).tobytes()==image.crop((size-1,0,size,size)).tobytes()
 if 'y' in wrap:
  seams['y']=image.crop((0,0,size,1)).tobytes()==image.crop((0,size-1,size,size)).tobytes()
 if not all(seams.values()):errors.append('repeat seam')
 asset['qa']=dict(passed=not errors,errors=errors,rgba_colors=len(allcolors),visible_colors=len(visible),
                  alpha_values=sorted(set(pixels(alpha))),bbox=list(bbox),margins=margins,seams=seams)
 asset['sha256']=sha(ART/asset['path']);asset['source_sha256']=sha(ART/asset['source_svg'])
 return not errors


def write_previews(assets,backgrounds,palette):
 for asset in assets:
  image=Image.open(ART/asset['path']).convert('RGBA');asset['previews']={}
  for world in asset['worlds']:
   path=PREVIEW/asset['category']/(asset['id'].replace('/','-')+'-'+world+'.png')
   path.parent.mkdir(parents=True,exist_ok=True)
   tint=expanded(UI_COLORS['UI_BRONZE']) if asset['category']=='stamp' else None
   flatten(image,backgrounds[world]['preview_rgb'],tint).save(path)
   asset['previews'][world]=relative(path)
  if asset['category'] in ('stamp','icon'):
   path=PREVIEW/asset['category']/(asset['id'].replace('/','-')+'-ui-ink.png')
   flatten(image,expanded(UI_COLORS['UI_INK'])).save(path);asset['previews']['ui_ink']=relative(path)
  if asset.get('repeat_axes'):
   repeat=Image.new('RGBA',(image.width*3,image.height*3))
   for y in range(3):
    for x in range(3):repeat.paste(image,(x*image.width,y*image.height))
   path=PREVIEW/'repeats'/(asset['id'].replace('/','-')+'.png');path.parent.mkdir(exist_ok=True)
   flatten(repeat,backgrounds[asset['worlds'][0]]['preview_rgb']).save(path)
   asset['previews']['repeat_3x3_native']=relative(path)


def contact_tiles(assets,worlds,backgrounds):
 board=Image.new('RGB',(960,9*142));d=ImageDraw.Draw(board)
 byid={a['id']:a for a in assets}
 for row,world in enumerate(WORLD_ORDER):
  bg=backgrounds[world]['preview_rgb'];fg='#fff0cd' if sum(bg)<350 else '#203849'
  for col,assetid in enumerate(worlds[world]):
   x,y=col*160,row*142;d.rectangle((x,y,x+159,y+141),fill=tuple(bg))
   image=Image.open(ART/byid[assetid]['path']).convert('RGBA')
   board.paste(image,(x+10,y+54),image)
   large=image.resize((64,64),Image.Resampling.NEAREST);board.paste(large,(x+74,y+38),large)
   text(d,(x+8,y+112),assetid.split('/')[-1],12,fg)
   if col==0:text(d,(x+8,y+7),WORLD_CN[row]+' · 32px / 2×',13,fg)
 board.save(PREVIEW/'tiles-contact.png')


def contact_landmarks(assets,backgrounds):
 board=Image.new('RGB',(960,810));d=ImageDraw.Draw(board)
 for i,asset in enumerate(a for a in assets if a['category']=='landmark'):
  x,y=i%3*320,i//3*270;bg=backgrounds[asset['worlds'][0]]['preview_rgb']
  d.rectangle((x,y,x+319,y+217),fill=tuple(bg));d.rectangle((x,y+218,x+319,y+269),fill='#e7d5ad')
  image=Image.open(ART/asset['path']).convert('RGBA')
  board.paste(image,(x+12,y+80),image)
  large=image.resize((192,192),Image.Resampling.NEAREST);board.paste(large,(x+117,y+12),large)
  text(d,(x+12,y+223),NAMES[asset['station']],17)
  text(d,(x+12,y+248),'96px 1× / 2× · actual world ground',12,'#756b55')
 board.save(PREVIEW/'landmarks-contact.png')


def contact_marks(assets,palette,backgrounds=None):
 seals=[a for a in assets if a['category']=='stamp'];board=Image.new('RGB',(960,810));d=ImageDraw.Draw(board)
 for i,asset in enumerate(seals):
  bg=backgrounds[asset['worlds'][0]]['preview_rgb'] if backgrounds else expanded(UI_COLORS['UI_INK'])
  x,y=i%3*320,i//3*270;d.rectangle((x,y,x+319,y+217),fill=tuple(bg))
  d.rectangle((x,y+218,x+319,y+269),fill=palette['bg'])
  image=Image.open(ART/asset['path']).convert('RGBA')
  if backgrounds:
   mask=image.getchannel('A');image=Image.new('RGBA',image.size,expanded(UI_COLORS['UI_BRONZE']));image.putalpha(mask)
  board.paste(image,(x+12,y+80),image)
  large=image.resize((192,192),Image.Resampling.NEAREST);board.paste(large,(x+117,y+12),large)
  text(d,(x+12,y+223),NAMES[asset['station']].split(' / ')[0]+' · 单白线邮戳',16)
  caption='96px 1× / 2× · actual world, UI_BRONZE tint' if backgrounds else '96px 1× / 2× · outer lettering left empty'
  text(d,(x+12,y+248),caption,12,'#756b55')
 board.save(PREVIEW/('stamps-world-contact.png' if backgrounds else 'stamps-contact.png'))
 icons=[a for a in assets if a['category']=='icon'];board=Image.new('RGB',(980,230),palette['bg']);d=ImageDraw.Draw(board)
 for i,asset in enumerate(icons):
  bg=backgrounds[asset['worlds'][0]]['preview_rgb'] if backgrounds else expanded(UI_COLORS['UI_INK'])
  x=i*140;d.rectangle((x,0,x+139,163),fill=tuple(bg))
  image=Image.open(ART/asset['path']).convert('RGBA');board.paste(image,(x+12,126),image)
  large=image.resize((96,96),Image.Resampling.NEAREST);board.paste(large,(x+30,20),large)
  text(d,(x+12,173),ICONS[asset['resource']],18)
  text(d,(x+12,203),'16px 1× / 6×',12,'#756b55')
 board.save(PREVIEW/('icons-world-contact.png' if backgrounds else 'icons-contact.png'))


def contact_repeats(assets):
 repeats=[a for a in assets if a.get('repeat_axes')];board=Image.new('RGB',(1024,260*((len(repeats)+3)//4)),'#e7d5ad');d=ImageDraw.Draw(board)
 for i,asset in enumerate(repeats):
  x,y=i%4*256,i//4*260;image=Image.open(ART/asset['previews']['repeat_3x3_native'])
  board.paste(image.resize((192,192),Image.Resampling.NEAREST),(x+32,y+8))
  text(d,(x+12,y+211),asset['id'].split('/')[-1],15)
  text(d,(x+12,y+237),'3×3 repeat · axes '+asset['repeat_axes'],12,'#756b55')
 board.save(PREVIEW/'repeat-seams-contact.png')


def main():
 global FONT,UI_COLORS
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--font',type=Path,default=ROOT.parent/'nabo-fortune/tools/fonts/SourceHanSansCN-Medium.otf')
 args=parser.parse_args();FONT=args.font;assert sha(FONT)==FONT_SHA,'Preview font must match established Source Han source'
 palette=json.loads(PALETTE.read_text('utf-8'));backgrounds,bgsource=current_backgrounds();assets=[];worlds={}
 UI_COLORS,uipath=current_ui_colors()
 PREVIEW.mkdir(parents=True,exist_ok=True)
 def add(canvas,identifier,path,category,worldlist,limit,**extra):
  target=ART/path;canvas.save(target)
  entry=dict(id=identifier,path=path,source_svg=relative(target.with_suffix('.svg')),category=category,
             size=[canvas.size]*2,color_limit=limit,worlds=worldlist,**extra)
  assets.append(entry);return entry
 for world,names in TILESETS.items():
  worlds[world]=[]
  for name in names:
   if (world,name) in ALIASES:
    srcworld,srcname=ALIASES[world,name];identifier=f'tiles/{srcworld}/{srcname}'
    next(a for a in assets if a['id']==identifier)['worlds'].append(world)
   else:
    identifier=f'tiles/{world}/{name}'
    add(tile(world,name,palette),identifier,f'map/tiles/{world}/{name}.png','tile',[world],16,
        repeat_axes=REPEAT.get(name,''),anchor=[16,31])
   worlds[world].append(identifier)
 for name in NAMES:
  add(landmark(name,palette),'landmark/'+name,f'map/landmarks/{name}.png','landmark',
      [STATION_WORLD[name]],32,station=name,anchor=[48,88])
  add(stamp(name,palette),'stamp/'+name,f'stamps/{name}.png','stamp',
      [STATION_WORLD[name]],2,station=name,tintable=True,lettering='none; annulus reserved for engine',anchor=[48,48])
 for name in ICONS:
  add(icon(name,palette),'icon/'+name,f'icons/{name}.png','icon',[ICON_WORLD[name]],8,resource=name,anchor=[8,8])
 passed=all([verify(asset) for asset in assets]);group_colors={}
 for world,ids in worlds.items():
  group=set()
  for identifier in ids:group.update(pixels(Image.open(ART/next(a['path'] for a in assets if a['id']==identifier))))
  group_colors[world]=len(group);passed=passed and len(group)<=16
 write_previews(assets,backgrounds,palette)
 contact_tiles(assets,worlds,backgrounds);contact_landmarks(assets,backgrounds)
 contact_marks(assets,palette);contact_marks(assets,palette,backgrounds);contact_repeats(assets)
 sources=[PALETTE,bgsource,uipath,FONT,*[HERE/name for name in ('build_shared_static.py','shared_static_canvas.py','shared_static_landmarks.py','shared_static_tiles.py','shared_static_marks.py')]]
 manifest=dict(version=1,stage='round4-shared-static',status='agent_checked; user artwork review pending',
  design='selected round3 01-passport; original native pixel art, editable SVG companions; no generated or redrawn NABO',
  palette=dict(path=relative(PALETTE),sha256=sha(PALETTE),visible_colors=sorted(set(palette.values()))),
  backgrounds=backgrounds,background_source=dict(path=bgsource.relative_to(ROOT).as_posix(),sha256=sha(bgsource),
    note='Current WORLD raw RGB is converted through RGB565 before preview. Kiosk path index1 currently uses harbor ground.'),
  ui_preview_colors={name:dict(rgb565=f'0x{value:04x}',preview_rgb=list(expanded(value))) for name,value in UI_COLORS.items()},
  worlds=worlds,assets=assets,counts=dict(worlds=9,logical_tiles=54,unique_tiles=53,landmarks=9,stamps=9,icons=7,unique_assets=len(assets)),
  qa=dict(passed=passed,world_tile_group_rgba_colors=group_colors,seams_checked='Exact RGBA edge bytes for declared repeat axes; 3x3 previews included',
    clipping_checked='Transparent margin except intentionally periodic tile edges',visual_review='See preview/shared-static/QA.md'),
  provenance={str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path):sha(path) for path in sources})
 (ART/'shared-static-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
 report=dict(passed=passed,counts=manifest['counts'],world_tile_group_rgba_colors=group_colors,
             failures=[dict(id=a['id'],errors=a['qa']['errors']) for a in assets if not a['qa']['passed']])
 (PREVIEW/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if not passed:raise SystemExit('Shared static QA failed')


if __name__=='__main__':main()
