"""1x 240x320 screens assembled with the actual newly exported UI pieces."""
from PIL import Image, ImageDraw
import json
from ui_assets_common import ART, OUT, image, rgba, SLICE_NAMES, render_nine, tiled_paste
from ui_assets_art import source_character


class Screen:
    def __init__(self, assets, fonts):
        self.assets, self.fonts = assets, fonts
        self.canvas = image((240, 320), 'bg')
        self.draw = ImageDraw.Draw(self.canvas)
        self.selected=[]
        self.layout={'space':'native 240x320; text positions are ink top-left, derive C baseline from generated glyph metrics',
                     'dynamic_text':[],'cards':[],'assets':[],'numbers':[]}

    def paste(self, name, xy):
        self.canvas.alpha_composite(self.assets.load(name),xy);self.layout['assets'].append({'path':name,'xy':list(xy)})
    def text(self, xy, label, size=12, color=None, align='left'):
        if color is None:color='white' if any(x<=xy[0]<=x+w and y<=xy[1]<y+h for x,y,w,h in self.selected) else 'ink'
        bounds=self.fonts.text(self.canvas,xy,label,size,color,align)
        self.layout['dynamic_text'].append({'fixture_text':label,'anchor_xy':list(xy),'ink_box':bounds,'size_px':size,
             'font':'NotoSansSC-Bold' if size>=16 else 'SourceHanSansCN-Medium','weight':700 if size>=16 else 500,
             'color':rgba(color)[:3],'color_name':color,'align':align})
        return bounds

    def card(self, xy, size, family='info', state='normal'):
        corner = 16 if family == 'popup' else 12
        pieces = {name: self.assets.load(f'cards/{family}/{state}/{name}.png') for name in SLICE_NAMES}
        self.canvas.alpha_composite(render_nine(pieces, size, corner), xy)
        if state in ('selected','current'):self.selected.append((*xy,*size))
        self.layout['cards'].append({'family':family,'state':state,'xy':list(xy),'size':list(size),
                                    'dynamic_text':'#fffaf0' if state in ('selected','current') else '#203849'})

    def bars(self, title, hint, right='章 1/24',world=None):
        self.paste('bars/top.png', (0, 0)); self.paste('bars/bottom.png', (0, 290))
        self.text((20, 6), title, 18, 'white')
        if world:self.text((108,10),world,12,'white')
        self.text((226, 11), right, 12, 'paper', 'right')
        self.text((120, 300), hint, 12, 'paper', 'center')

    def character(self, center, foot, height=48):
        name='idle' if height==48 else 'cheer' if height==72 else None
        if name:
            m=json.loads((ART/'manifest.json').read_text('utf-8'));entry=next(e for e in m['animations'] if e['skin']=='travel' and e['name']==name)
            sprite=Image.open(ART/entry['runtime_frames'][0]).convert('RGBA');a=entry['runtime_anchor']
            self.canvas.alpha_composite(sprite,(center-a[0],foot-a[1]))
        else:
            source=ART/'frames/travel/masters/idle/000.png';sprite=source_character(source,height,63)
            self.canvas.alpha_composite(sprite,(center-sprite.width//2,foot-height))

    def resource(self, xy, fraction=3, low=False):
        self.paste('resources/bar-frame.png', xy)
        tile = self.assets.load(f'resources/{"low-fill" if low else "fill"}.png')
        tiled_paste(self.canvas, tile, (xy[0]+2, xy[1]+2, xy[0]+2+124*fraction//4, xy[1]+8))

    def number(self, label, xy, height=36):
        self.layout['numbers'].append({'fixture_text':str(label),'xy':list(xy),'height':height,'font':'Montserrat-Bold sprite digits'})
        x, y = xy
        for char in str(label):
            bitmap = self.assets.load(f'numbers/{height}/{"plus" if char == "+" else char}.png')
            self.canvas.alpha_composite(bitmap, (x, y)); x += bitmap.width-1

    def save(self, name):
        folder = OUT / 'preview'; folder.mkdir(parents=True, exist_ok=True)
        self.canvas.save(folder / f'{name}.png', optimize=True)
        (folder/f'{name}.layout.json').write_text(json.dumps(self.layout,ensure_ascii=False,indent=2)+'\n','utf-8')


def build_previews(assets, fonts):
    # Same adv_path world geometry as the production map: POST above JUMP,
    # KIOSK below, 112px slots. Only background gradients are program preview.
    screen=Screen(assets,fonts)
    ground=ImageDraw.Draw(screen.canvas)
    anchors=[(64,(150,200,110)),(176,(246,226,180)),(288,(40,120,160))]
    for y in range(32,290):
        left,right=(anchors[0],anchors[1]) if y<=176 else (anchors[1],anchors[2])
        t=max(0,min(112,y-left[0]));rgb=tuple(a+(b-a)*t//112 for a,b in zip(left[1],right[1]))
        ground.line((0,y,239,y),fill=(*rgb,255))
    for ax,ay,bx,by in [(160,64,80,176),(80,176,160,288)]:
        for k in range(1,6):screen.paste('map/footprints-forward.png',(ax+(bx-ax)*k//6-5,ay+(by-ay)*k//6-5))
    for node,station,title,open_,here in [((160,64),'post','小火车',False,False),((80,176),'jump','跳一跳',True,True),((160,288),'kiosk','护照亭',True,False)]:
        x,y=node;landmark=Image.open(ART/f'map/landmarks/{station}.png').convert('RGBA')
        screen.canvas.alpha_composite(landmark,(x-48,y-83))
        screen.paste('map/station-current.png' if here else 'map/station-unlocked.png' if open_ else 'map/station-locked.png',(x-24,y-14))
        cx=x+25 if x<120 else x-137;cy=y-26
        screen.card((cx,cy),(112,52),state='current' if here else 'normal')
        screen.text((cx+8,cy+8),title,16)
        if here:
            screen.paste('map/stamp-bronze.png',(cx+8,cy+30));screen.text((cx+104,cy+30),'12',12,align='right')
        else:screen.text((cx+8,cy+30),'护照 · 设置' if station=='kiosk' else '需深潜铜章',12,'muted')
    screen.character(80,191)
    screen.bars('冒险地图','上 / 下移动   OK 进入',world='小镇');screen.save('map')

    screen=Screen(assets,fonts)
    screen.paste('passport/header.png',(12,40));screen.text((224,48),'01 / 24',12,'muted','right')
    names=('跳一跳','深潜','小火车','萤火虫','登山','滑雪','热气球','太空')
    for i,name in enumerate(names):
        x=12+(i%2)*112;y=70+(i//2)*54;selected=i==0;ink='white' if selected else 'ink'
        screen.paste('passport/grid-current.png' if selected else 'passport/grid-normal.png',(x,y))
        screen.text((x+8,y+8),name,16,ink)
        if i>1:
            screen.paste('passport/locked-mask.png',(x,y));screen.text((x+8,y+30),'未解锁',12,'muted')
        else:
            if i==0:screen.paste('map/stamp-bronze.png',(x+8,y+30))
            screen.text((x+96,y+30),'12' if selected else '0',12,ink,'right')
    screen.bars('冒险护照','上 / 下翻阅   OK 返回','PASSPORT');screen.save('passport')

    screen = Screen(assets, fonts)
    screen.paste('wordmarks/post.png', (20, 42))
    landmark = ART / 'map/landmarks/post.png'
    if landmark.exists(): screen.canvas.alpha_composite(Image.open(landmark).convert('RGBA'), (77, 116))
    screen.character(45, 201, 56)
    screen.card((16, 207), (208, 76))
    for i, (name, score) in enumerate((('bronze', 5), ('silver', 12), ('gold', 25))):
        screen.paste(f'map/stamp-{name}.png', (48+i*64, 218)); screen.text((56+i*64, 242), str(score), align='center')
    screen.text((120, 261), '最佳 0', align='center')
    screen.bars('小火车', 'OK 出发   上键返回', '第 03 站'); screen.save('post-title')

    screen = Screen(assets, fonts)
    screen.card((16, 44), (208, 237), 'popup')
    screen.text((32, 57), 'POST · 小火车')
    screen.text((120,81),'本局成绩',18,align='center');screen.number('12',(92,111))
    screen.paste('labels/new-record.png', (84, 157)); screen.character(63, 251, 56)
    screen.text((111, 205), '最佳 12', 16)
    for i, name in enumerate(('bronze', 'silver', 'empty')): screen.paste(f'map/stamp-{name}.png', (112+i*29, 233))
    screen.text((120, 259), '距金章还差 13', align='center')
    screen.bars('旅途结算', 'OK 再来   上键返回', '第 03 站'); screen.save('result')

    screen = Screen(assets, fonts)
    for i, label in enumerate(('冒险护照', '设置', '返回地图')):
        screen.card((16, 65+i*60), (208, 48), 'menu', 'selected' if i == 0 else 'normal')
        screen.text((120, 80+i*60), label, 16, align='center')
    screen.text((120, 259), '每一站，都是新的印记', align='center')
    screen.bars('护照亭', '上 / 下选择   OK 确认'); screen.save('kiosk')

    screen = Screen(assets, fonts)
    for i, (label, value) in enumerate((('音量', '70'), ('亮度', '80'), ('休眠', '5 分钟'), ('扬声器', '开启'))):
        screen.card((16, 46+i*50), (208, 42), 'menu', 'selected' if i == 0 else 'normal')
        screen.text((27, 59+i*50), label, 16); screen.text((211, 60+i*50), value, 16, align='right')
    screen.resource((56, 264), 3)
    screen.bars('设置', 'OK 调整   上键返回'); screen.save('settings')

    screen = Screen(assets, fonts)
    screen.card((16, 56), (208, 210), 'popup'); screen.text((120, 81), '设备状态', 18, align='center')
    for i, line in enumerate(('电池 85%', '电压 3980 mV', '离线冒险 · 无需联网', '声音与亮度可在设置调整')):
        screen.text((32, 123+i*30), line)
    screen.bars('状态', 'OK 返回'); screen.save('status')

    screen = Screen(assets, fonts)
    screen.card((24, 86), (192, 142), 'popup'); screen.text((120, 108), '休息一下', 18, align='center')
    screen.text((120, 148), 'OK 继续', 16, align='center')
    screen.text((120, 180), '下键重新开始', 12, align='center')
    screen.bars('小火车', '上键返回地图', '暂停'); screen.save('pause')

    for name, title, number in (('ready', '准备出发', '3'), ('end', '本局结束', '0')):
        screen = Screen(assets, fonts)
        screen.card((24, 96), (192, 132), 'popup'); screen.text((120, 115), title, 18, align='center')
        screen.number(number, (105, 158))
        screen.bars('小火车', '正在准备' if name == 'ready' else '正在结算', 'POST'); screen.save(name)

    screen = Screen(assets, fonts)
    screen.card((24, 57), (192, 218), 'popup')
    screen.text((120,75),'新的旅途印章',18,align='center')
    screen.paste('stamps/ink-pad.png',(88,120))
    source=Image.open(ART/'stamps/post.png').convert('RGBA');stamp=Image.new('RGBA',source.size,rgba('silver'))
    stamp.putalpha(source.getchannel('A'));screen.canvas.alpha_composite(stamp,(72,104))
    screen.text((120,211),'小火车 · 银章',16,align='center')
    screen.text((120,247),'解锁第二款服装',align='center')
    screen.bars('旅途盖章', 'OK 收下这枚章'); screen.save('stamp')

    screen = Screen(assets, fonts)
    resources = [('stamina', '体力'), ('oxygen', '氧气'), ('steam', '蒸汽'), ('spirit', '精神'),
                 ('temperature', '体温'), ('hot-air', '热气'), ('fuel', '燃料')]
    for i, (name, label) in enumerate(resources):
        y = 45+i*34
        screen.paste(f'resources/icons/{name}.png', (18, y)); screen.text((43, y+1), label)
        screen.resource((91, y+3), 1 if i == 4 else 3, i == 4)
    screen.bars('旅途资源', '资源归零，本局结束'); screen.save('resources')

    names = ('map', 'passport', 'post-title', 'result', 'kiosk', 'settings', 'status', 'pause', 'ready', 'end', 'stamp', 'resources')
    contact = image((240*4, 320*3), 'bg')
    for i, name in enumerate(names): contact.alpha_composite(Image.open(OUT / f'preview/{name}.png').convert('RGBA'), ((i % 4)*240, (i//4)*320))
    contact.save(OUT / 'preview/screens-1x.png', optimize=True)
    return list(names)
