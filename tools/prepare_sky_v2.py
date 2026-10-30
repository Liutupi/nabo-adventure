"""Derive only SKY V2's mechanical balloon parts at 2/3 size; NABO frames stay untouched."""
import hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'game-art/adventure/art'
if __name__=='__main__':
 path=ART/'sky-manifest.json';manifest=json.loads(path.read_text('utf-8'))
 manifest['assets']=[a for a in manifest['assets'] if not a['id'].startswith('sky/v2/')]
 for name in ('envelope','basket_front','basket_back'):
  original=next(a for a in manifest['assets'] if a['id']=='sky/'+name)
  source=ART/original['path'];image=Image.open(source).convert('RGBA')
  size=tuple((d*2+1)//3 for d in image.size)
  # Nearest-neighbour keeps the original, bounded palette and binary alpha.
  # The production renderer uses these exact native-size machine parts.
  image=image.resize(size,Image.Resampling.NEAREST)
  relative=f'games/sky/v2/{name}.png';target=ART/relative;target.parent.mkdir(exist_ok=True);image.save(target)
  manifest['assets'].append({'id':'sky/v2/'+name,'path':relative,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'size':list(size),'anchor':[size[0]//2,0],'color_limit':original['color_limit'],'derived_from':original['path'],'source_sha256':original['sha256'],'recipe':'prepare_sky_v2.py: nearest, 2/3, binary alpha; machine part only'})
 path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\r\n')
