"""Reproduce BOOT-V3-01 technical composition with an explicitly supplied FFmpeg7.1.

Writes a separate candidate folder; production selection is a distinct reviewed step.
"""
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageChops,__version__ as PILLOW_VERSION
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'game-art/adventure/art'
RAW_SHA='e0458f49a90cfee5fc08bcde0fcca64180c361895850a3d4015a3d74d2558543'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(ff,*args):subprocess.run([str(ff),'-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)
def prepare(ff,output):
 ff=Path(ff).resolve();output=Path(output).resolve()
 raw=ART/'grok-handoff/boot-v3/output/BOOT-V3-01-welcome-master.mp4'
 if sha(raw)!=RAW_SHA:raise ValueError('Grok source differs from reviewed original')
 version=subprocess.check_output([str(ff),'-version'],text=True).splitlines()[0]
 if 'version 7.1' not in version:raise ValueError('Reviewed encoder requires FFmpeg7.1')
 if output.exists() and any(output.iterdir()):raise ValueError('Candidate output must be empty')
 output.mkdir(parents=True,exist_ok=True)
 bg=Image.open(ART/'boot/v3/background-master.png').convert('RGBA').resize((240,320),Image.Resampling.LANCZOS)
 title=Image.open(ART/'boot/v3/title-master.png').convert('RGBA').resize((224,102),Image.Resampling.LANCZOS).crop((0,0,224,82))
 private=ROOT/'private';private.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='boot-v3-',dir=private) as tmp:
  folder=Path(tmp);decoded=folder/'raw';composed=folder/'scene';decoded.mkdir();composed.mkdir()
  run(ff,'-i',raw,'-map','0:v:0','-an','-fps_mode','passthrough',decoded/'%04d.png')
  frames=sorted(decoded.glob('*.png'))
  if len(frames)!=145 or Image.open(frames[0]).size!=(960,960):raise ValueError('Raw clip dimensions/frame count differ')
  for i,path in enumerate(frames[::2]):
   im=Image.open(path).convert('RGB');r,g,b=im.split();rb=ImageChops.lighter(r,b);excess=ImageChops.subtract(g,rb)
   alpha=excess.point(lambda v:255 if v<=20 else 0 if v>=70 else (70-v)*255//50)
   clean=ImageChops.darker(g,ImageChops.add(rb,Image.new('L',im.size,10)))
   hero=Image.merge('RGBA',(r,clean,b,alpha)).crop((140,90,954,960)).resize((193,206),Image.Resampling.LANCZOS)
   view=bg.copy();view.alpha_composite(hero,(23,10));view.alpha_composite(title,(8,202));view.convert('RGB').save(composed/f'{i:03}.png')
  # Header24fps is MPEG1 syntax; the manifest explicitly exposes73 frames at12fps.
  encoding=['-vf','scale=208:272:flags=lanczos','-an','-c:v','mpeg1video','-bf','0','-mbd','rd','-trellis','2','-q:v','10']
  movie=output/'boot-welcome.m1v';poster=output/'cover-poster.m1v'
  run(ff,'-framerate','24','-i',composed/'%03d.png',*encoding,'-g','24','-f','mpeg1video',movie)
  run(ff,'-framerate','24','-i',composed/'072.png',*encoding,'-g','1','-frames:v','1','-f','mpeg1video',poster)
  Image.open(composed/'072.png').save(output/'poster.png')
  for p in (movie,poster):
   data=p.read_bytes()
   if not data.endswith(b'\0\0\1\xb7'):p.write_bytes(data+b'\0\0\1\xb7')
 report={'raw_source_sha256':RAW_SHA,'encoder':version,'encoder_sha256':sha(ff),'pillow':PILLOW_VERSION,
         'operations':'fixed crop/key/despill/resample/composite only; original art and Grok master retained; no audio',
         'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in (movie,poster,output/'poster.png')}}
 (output/'reproduction.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');return report
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--ffmpeg',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();print(json.dumps(prepare(a.ffmpeg,a.output),indent=2))
