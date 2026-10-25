"""Four complete sample screens, shared geometry and content across directions."""
from ui_primitives import Board


def map_screen(b):
    b.background()
    b.footsteps([(160, 78), (133, 106), (106, 131), (80, 159), (84, 202), (116, 236), (160, 270)])
    b.node(160, 64, 'locked')
    area = b.card(16, 41, 116, 56, ticket=True)
    b.text(24, 49, '小火车', 16, within=area)
    b.text(24, 75, '需深潜铜章', 12, 'muted', within=area)
    b.node(80, 176, 'current')
    b.character(80, 174, 48)
    area = b.card(112, 132, 112, 72, selected=True)
    b.text(120, 140, '跳一跳', 16, within=area)
    b.text(120, 164, '最佳 12', 12, within=area)
    for tier in range(3): b.medal(128+tier*21, 190, tier, tier == 0, 5)
    b.poly([(106, 166), (112, 160), (112, 172)], 'accent')
    b.text(80, 214, '当前位置', 12, 'ink', 'center')
    b.node(160, 284, icon='kiosk')
    area = b.card(16, 244, 112, 38)
    b.text(24, 254, '护照亭', 16, within=area)
    if b.mode == 'paper':
        b.ellipse((178, 219, 225, 266), None, 'accent')
        b.line([(182, 227), (221, 259)], 'accent')
        b.text(202, 236, '旅途', 12, 'accent', 'center')
    elif b.mode == 'sticker':
        b.envelope(190, 228, 26, 20, 'select')
        b.star(215, 221, 6, 'accent')
    else:
        b.ellipse((178, 220, 224, 266), None, 'line')
        b.star(201, 243, 14, 'accent')
    b.bars('冒险地图', '上 / 下移动   OK 进入')


def passport_screen(b):
    b.background()
    b.card(12, 40, 216, 246, ticket=True)
    b.line([(120, 48), (120, 257)], 'line')
    b.text(24, 48, '旅途印记', 12)
    b.text(216, 48, '01', 12, 'muted', 'right')
    names = ['跳一跳', '深潜', '小火车', '萤火虫', '登山', '滑雪', '热气球', '太空']
    for i, name in enumerate(names):
        x, y = 18+(i % 2)*108, 68+(i//2)*48
        selected, locked = i == 0, i > 1
        area = b.card(x, y, 96, 46, selected=selected)
        b.text(x+8, y+8, name, 12, 'muted' if locked else 'ink', within=area)
        if locked:
            b.rect((x+6, y+24, x+89, y+40), 'seal')
            b.text(x+9, y+24, '未解锁', 12, 'muted', within=area)
            b.lock(x+72, y+7)
        else:
            for tier in range(3): b.medal(x+13+tier*16, y+31, tier, selected and tier == 0, 4)
            b.text(x+85, y+26, '12' if selected else '0', 12, align='right', within=area)
    b.line([(25, 261), (215, 261)], 'line')
    b.text(120, 264, '距银章还差 13', 12, align='center', within=(20, 48, 220, 278))
    b.bars('冒险护照', '上 / 下翻阅   OK 返回')


def title_screen(b):
    b.background()
    b.card(20, 42, 200, 127, ticket=True)
    b.text(120, 51, '铁路平原', 12, 'muted', 'center')
    b.text(120, 73, 'POST', 18, 'accent', 'center')
    b.text(120, 99, '小火车', 18, align='center')
    b.character(53, 162, 48)
    b.train(97, 125)
    b.envelope(169, 137, 24, 18, 'select')
    b.line([(88, 166), (199, 166)], 'ink')
    area = b.card(16, 183, 208, 92)
    b.text(24, 191, '送信盖章，继续旅程', 12, within=area)
    for tier, (x, score) in enumerate(((56, 5), (120, 12), (184, 25))):
        b.medal(x, 221, tier, True, 10)
        b.text(x, 239, str(score), 12, align='center')
    b.text(120, 253, '最佳 0', 12, align='center', within=area)
    b.bars('小火车', 'OK 出发   上键返回', count='第 03 站')


def result_screen(b):
    b.background()
    area = b.card(16, 43, 208, 235, ticket=True)
    b.text(32, 55, 'POST · 小火车', 12, within=area)
    b.text(208, 55, '03', 12, 'muted', 'right', within=area)
    for x in range(27, 213, 9): b.line([(x, 79), (x+3, 79)], 'line')
    b.text(120, 92, '本局成绩', 12, align='center')
    b.rect((78, 112, 162, 145), 'select', 'accent')
    b.text(120, 119, '12', 18, align='center')
    b.rect((78, 155, 162, 178), 'accent', radius=3 if b.mode == 'sticker' else 0)
    b.text(120, 161, '新纪录', 12, 'bar' if b.mode == 'stars' else 'paper', 'center')
    b.line([(32, 190), (208, 190)], 'line')
    b.character(63, 254, 56)
    b.text(111, 202, '最佳 12', 16)
    for tier in range(3): b.medal(121+tier*29, 235, tier, tier < 2, 7)
    b.text(120, 256, '距金章还差 13', 12, align='center', within=area)
    b.bars('旅途结算', 'OK 再来   上键返回', count='第 03 站')


SCENES = {'map': map_screen, 'passport': passport_screen, 'post-title': title_screen, 'result': result_screen}
