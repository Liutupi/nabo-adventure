#!/usr/bin/env python3
"""Author native SVG/HTML community layouts around unchanged production-C screens."""
import argparse,hashlib,html,json,shutil
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/community/v0.1.0'
BG='#090916';PANEL='#14172A';INK='#F6F4FF';MUTED='#B8C4D8';CYAN='#39E6DF';GOLD='#F5CE67'
sources={}
def source(name):
    p=ROOT/'docs/images/ui'/name
    sources[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(Image.open(p).size),'kind':'production-C host render; demonstration data'}
    return '../../images/ui/'+name
def text(x,y,s,size=32,color=INK,anchor='start',font='Body'):
    return f'<text data-copy="{html.escape(s,quote=True)}" x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="700" fill="{color}" text-anchor="{anchor}">{html.escape(s)}</text>'
def box(x,y,w,h,fill=PANEL,stroke='#31415B',r=22):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
def screen(name,x,y,w):
    href=source(name);iw,ih=sources[name]['size'];h=w*ih/iw
    return box(x-10,y-10,w+20,h+20,'#040813','#405972',16)+f'<image data-screen="{name}" x="{x}" y="{y}" width="{w}" height="{h}" href="{href}" style="image-rendering:pixelated"/>'
def base(n,english,title,sub):
    s=f'<rect width="1080" height="1440" fill="{BG}"/>'
    s+='<defs><pattern id="dots" width="30" height="30" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#21465A" opacity=".4"/></pattern></defs><rect width="1080" height="1440" fill="url(#dots)"/>'
    s+=text(60,65,'NABO / ADVENTURE',23,CYAN,font='Mono')+text(1020,65,f'{n:02d} / 05',23,MUTED,'end','Mono')
    s+=f'<path d="M60 97H1020M60 1350H1020" stroke="#354257"/>'
    s+=text(60,151,english,22,GOLD,font='Mono')+text(60,250,title,70)+text(64,314,sub,30,MUTED)
    s+=text(60,1394,'v0.1.0 · 公开预览版',22,MUTED)
    s+=text(1020,1394,'生产C界面预览 · 含演示数据',21,MUTED,'end')
    return s
def save(name,s):
    css="""@font-face{font-family:Body;src:url('assets/NotoSansSC-Bold.otf')}@font-face{font-family:Mono;src:url('assets/SpaceMono-Bold.ttf')}*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1440px;overflow:hidden;background:#090916}svg{display:block}text{font-synthesis:none}"""
    page=f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{name}</title><style>{css}</style><body><svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">{s}</svg></body></html>'
    (OUT/(name+'.html')).write_text(page,'utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cover',type=Path,required=True)
    ap.add_argument('--font',type=Path,default=Path('C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf'));a=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);assets=OUT/'assets';assets.mkdir(exist_ok=True)
    if a.cover.resolve()!=(OUT/'01-cover.png').resolve():shutil.copy2(a.cover,OUT/'01-cover.png')
    if a.font.resolve()!=(assets/'NotoSansSC-Bold.otf').resolve():shutil.copy2(a.font,assets/'NotoSansSC-Bold.otf')
    shutil.copy2(ROOT/'firmware/main/font-licenses/NotoSansSC-Bold-OFL.txt',assets/'NotoSansSC-OFL.txt')
    mono=assets/'SpaceMono-Bold.ttf'
    if not mono.exists():shutil.copy2(ROOT.parent/'nabo-sound-lab/tools/fonts/SpaceMono-Bold.ttf',mono)
    shutil.copy2(ROOT/'firmware/main/OFL-SpaceMono.txt',assets/'SpaceMono-OFL.txt')
    s=base(2,'EIGHT STOPS / ONE PASSPORT','八站，一本冒险护照。','拿到上一站铜章，下一站就向你开放。')
    s+=text(270,385,'沿地图出发',32,CYAN,'middle')+text(810,385,'把旅程盖成印章',32,GOLD,'middle')
    s+=screen('map-town.png',90,420,360)+screen('passport.png',630,420,360)
    s+=box(60,950,960,290)
    for i,label in enumerate(('01 跳一跳','02 深潜','03 小火车','04 萤火虫之夜','05 登山','06 雪崩速降','07 热气球','08 火箭登月')):
        x=100+(i%2)*480;y=1010+(i//2)*62;s+=text(x,y,label,31,CYAN if i%2==0 else INK)
    s+=text(540,1300,'8款游戏 × 铜 / 银 / 金 = 24枚冒险印章',31,GOLD,'middle');save('02-passport',s)

    s=base(3,'FIND THE RHYTHM / ESCAPE THE AVALANCHE','追光，或迎着雪坡冲。','两款横屏玩法：三键朝下，左右移动，中键行动。')
    for y,title,tag,image,lines in [
        (370,'萤火虫之夜','罐子的光，就是体力。','night-swing.png',('左键慢走 / 右键小跑','中键挥罐，满能量双击放光','躲飞蛾、树根和猫头鹰','光耗尽，本局结束')),
        (830,'雪崩速降','旗门与跳台，把雪崩甩远。','ski-gate.png',('左右转弯 / 中键跳跃','冲上跳台，空中点按转体','连过旗门提速，避开大树','被雪崩追上，本局结束'))]:
        s+=box(60,y,960,414);s+=text(86,y+53,title,42,CYAN)+text(86,y+98,tag,26,MUTED)
        s+=screen(image,86,y+137,360)
        for k,line in enumerate(lines):s+=text(490,y+158+k*66,line,26,INK if k<3 else GOLD)
    s+=text(540,1305,'长按中键暂停 · 暂停后双击右键回地图',30,GOLD,'middle');save('03-night-ski',s)

    s=base(4,'IGNITION / ORBIT / MOON LANDING','这次，真的飞向月球。','点火、分离、奔月，再把登月舱稳稳落下。')
    for (x,y),image,title,line in zip(((75,380),(575,380),(75,810),(575,810)),
        ('space-ignite.png','space-ascent.png','space-transfer.png','space-landed.png'),
        ('01 点火与分离','02 躲开障碍','03 地月转移','04 反推着陆'),
        ('中键对准绿区，抓住时机','左右移动，留意燃料与船体','跟着光圈节奏，完成点火','点按中键反推，对准着陆台')):
        s+=screen(image,x,y,430)+text(x,y+365,title,32,CYAN)+text(x,y+409,line,24,MUTED)
    s+=text(540,1300,'燃料耗尽或船体归零会失败；平稳落台完成登月。',28,GOLD,'middle');save('04-rocket',s)

    s=base(5,'THREE BUTTONS / EIGHT WAYS TO PLAY','三个按键，就能出发。','地图上 / 下选择，OK进入；每款都有自己的玩法。')
    s+=box(60,370,960,345)
    s+=text(92,424,'萤火虫 / 雪崩速降 / 火箭：顺时针横拿',31,CYAN)
    for x,title,sub in ((125,'左','原OK键'),(435,'中','原下键'),(745,'右','原上键')):
        s+=box(x,462,210,92,'#203348','#43B9C4',46)+text(x+105,520,title,43,INK,'middle')+text(x+105,601,sub,25,MUTED,'middle')
    s+=text(540,660,'中键开始 / 主动作 · 长按暂停 · 暂停后双击右键返回',27,GOLD,'middle')
    s+=text(60,785,'还有熟悉的小挑战，一站接一站。',37,INK)
    s+=screen('jump.png',82,830,210)+screen('dive-title-return.png',404,830,210)+screen('post-ready-to-send.png',704,870,280)
    s+=text(187,1163,'跳一跳',31,CYAN,'middle')+text(509,1163,'深潜',31,CYAN,'middle')+text(844,1163,'小火车送信',31,CYAN,'middle')
    s+=text(187,1216,'按住蓄力，松开跳',24,MUTED,'middle')+text(509,1216,'换向与俯冲，躲障碍',24,MUTED,'middle')+text(844,1216,'看轨道，抓准送信时机',24,MUTED,'middle')
    s+=text(540,1302,'离线游玩 · 最佳纪录保存 · 自动休眠',31,GOLD,'middle');save('05-controls',s)
    manifest={'version':'v0.1.0','ordered_images':['01-cover.png','02-passport.jpg','03-night-ski.jpg','04-rocket.jpg','05-controls.jpg'],
      'cover_method':'Built-in image_gen, source identity and approved explorer reference; targeted title correction',
      'detail_method':'Native SVG/HTML typesetting around unchanged production-C images; not device photography',
      'series_references':['nabo-fortune/docs/community/v0.1.2/01-cover.png','nabo-sound-lab/docs/community/v0.2.0-preview.1/01-cover.png'],
      'sources':sources,'font_sha256':hashlib.sha256(a.font.read_bytes()).hexdigest(),'status':'HTML authored; PNG export and visual QA pending'}
    (OUT/'graphics-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(OUT),'html_pages':4,'cover_size':Image.open(OUT/'01-cover.png').size},ensure_ascii=False))

if __name__=='__main__':main()
