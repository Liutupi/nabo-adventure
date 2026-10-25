// Canvas copy of the firmware screens (firmware/main/adv_ui*.c): same coordinates and colours,
// browser fonts instead of the bitmap fonts. Layout reference only; the rules live in adv_core.js.
(function (root) {
  'use strict';
  const hex565 = v => `rgb(${(v >> 11) * 255 / 31 | 0},${((v >> 5) & 63) * 255 / 63 | 0},${(v & 31) * 255 / 31 | 0})`;
  const rgb = (r, g, b) => `rgb(${r},${g},${b})`;
  const INK = hex565(0x1927), PAPER = hex565(0xef3b), GOLD = hex565(0xfd70), WHITE = '#fff', DIM = hex565(0x7bef);
  const LOCK = hex565(0x7bd1), RED = hex565(0xe28a);
  const TIER = [hex565(0xcbe6), hex565(0xc639), hex565(0xfe69)];
  const STATION_COLOR = [[240, 196, 92], [240, 150, 80], [80, 200, 230], [230, 90, 70], [200, 230, 90],
    [150, 170, 200], [110, 170, 240], [250, 160, 190], [170, 140, 250]];
  const WORLD = [[6, 20, 52], [40, 120, 160], [246, 226, 180], [150, 200, 110], [24, 48, 60], [150, 170, 200],
    [225, 236, 248], [140, 200, 250], [16, 10, 40]];
  const F = {
    f12: '500 12px "Noto Sans SC"', f16: '500 16px "Noto Sans SC"', f18: '500 18px "Noto Sans SC"',
    p28: '28px "Archivo Black"', p48: '48px "Archivo Black"', m12: '700 12px "Space Mono"',
  };
  const portrait = new Image();
  portrait.src = '../../../docs/images/ui/cover.png';   // the firmware cover holds the approved portrait

  let c;
  function band(y, h, top, bottom) {
    const g = c.createLinearGradient(0, y, 0, y + h);
    g.addColorStop(0, top); g.addColorStop(1, bottom);
    c.fillStyle = g; c.fillRect(0, y, 240, h);
  }
  function rect(x, y, w, h, r, fill, alpha, line, lw) {
    c.beginPath(); c.roundRect(x, y, w, h, Math.min(r, w / 2, h / 2));
    if (alpha) { c.globalAlpha = alpha / 255; c.fillStyle = fill; c.fill(); c.globalAlpha = 1; }
    if (lw) { c.lineWidth = lw; c.strokeStyle = line; c.beginPath(); c.roundRect(x + lw / 2, y + lw / 2, w - lw, h - lw, Math.max(0, r - lw / 2)); c.stroke(); }
  }
  const circle = (x, y, r, fill, alpha, line, lw) => rect(x - r, y - r, 2 * r, 2 * r, r, fill, alpha, line, lw);
  function text(font, s, x, y, align, color) {
    c.font = F[font]; c.textAlign = align; c.textBaseline = 'alphabetic'; c.fillStyle = color; c.fillText(s, x, y);
  }
  function tri(x, y, size, up, color) {
    c.fillStyle = color; c.beginPath();
    const h = size, w = size * 2 / 3;
    if (up) { c.moveTo(x, y - h / 2); c.lineTo(x + w, y + h / 2); c.lineTo(x - w, y + h / 2); }
    else { c.moveTo(x, y + h / 2); c.lineTo(x + w, y - h / 2); c.lineTo(x - w, y - h / 2); }
    c.fill();
  }
  function glow(x, y, r, color) {
    const g = c.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color.replace('rgb', 'rgba').replace(')', ',0.7)')); g.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = g; c.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
  function header(title, right) {
    rect(0, 0, 240, 32, 0, INK, 235); text('f16', title, 12, 22, 'left', PAPER);
    if (right) text('f16', right, 228, 22, 'right', GOLD);
  }
  function footer(hint) { rect(0, 290, 240, 30, 0, INK, 235); text('f12', hint, 120, 310, 'center', PAPER); }
  function stamps(A, m, s, x, cy, r, gap) {
    const e = A.earned(m);
    for (let t = 0; t < 3; t++) { const on = e & A.bit(s, t); circle(x + t * gap, cy, r, TIER[t], on ? 255 : 0, on ? INK : DIM, 1); }
  }
  const stampCount = (A, m) => { let e = A.earned(m), n = 0; while (e) { n += e & 1; e >>>= 1; } return n; };

  function cover(A, m) {
    band(0, 200, rgb(28, 36, 86), rgb(118, 120, 170)); band(200, 120, rgb(118, 120, 170), rgb(244, 196, 150));
    glow(120, 196, 70, GOLD);
    text('p28', 'NABO', 120, 58, 'center', WHITE); text('p28', 'ADVENTURE', 120, 90, 'center', GOLD);
    text('f18', 'NABO 的冒险之旅', 120, 120, 'center', PAPER);
    circle(120, 196, 54, PAPER, 255, INK, 3);
    if (portrait.complete && portrait.naturalWidth) c.drawImage(portrait, 78, 154, 84, 84, 78, 154, 84, 84);
    text('m12', `STAMPS ${stampCount(A, m)}/24`, 120, 276, 'center', INK);
    rect(60, 284, 120, 26, 13, GOLD, 255, INK, 2); text('f16', '按 OK 出发', 120, 302, 'center', INK);
  }

  const MAP_TOP = 120, SLOT = 112, MAP_H = MAP_TOP + 8 * SLOT + 140;
  const wy = i => MAP_TOP + (8 - i) * SLOT, nx = i => i % 2 ? 160 : 80;
  function map(A, m) {
    let cam = wy(A.PATH.indexOf(m.cursor)) - 176; cam = Math.max(0, Math.min(MAP_H - 320, cam));
    band(-cam, wy(8), rgb(5, 3, 20), rgb(...WORLD[8]));
    for (let i = 8; i > 0; i--) band(wy(i) - cam, SLOT, rgb(...WORLD[i]), rgb(...WORLD[i - 1]));
    band(wy(0) - cam, MAP_H - wy(0), rgb(...WORLD[0]), rgb(2, 8, 24));
    for (let i = 0; i < 8; i++)
      for (let k = 1; k <= 5; k++) {
        const x = nx(i) + (nx(i + 1) - nx(i)) * k / 6 | 0, y = (wy(i) + (wy(i + 1) - wy(i)) * k / 6 | 0) - cam;
        if (y > 30 && y < 290) circle(x, y, 3, WHITE, 220, INK, 1);
      }
    for (let i = 0; i < 9; i++) {
      const s = A.PATH[i], x = nx(i), y = wy(i) - cam;
      if (y < 10 || y > 310) continue;
      const st = A.STATION[s], open = A.unlocked(m, s), here = s === m.cursor;
      if (here) { glow(x, y, 34, GOLD); circle(x, y, 22, GOLD, 0, GOLD, 2); }
      circle(x, y, 17, open ? rgb(...STATION_COLOR[s]) : LOCK, 255, INK, 2);
      text('f18', s === 0 ? '护' : open ? String(s) : '?', x, y + 7, 'center', INK);
      const cx = x < 120 ? x + 25 : x - 25 - 112;
      rect(cx, y - 20, 112, 40, 8, PAPER, 235, here ? GOLD : INK, here ? 2 : 1);
      text('f16', st.cn, cx + 8, y - 2, 'left', open ? INK : LOCK);
      if (s === 0) text('f12', '护照 · 设置', cx + 8, y + 15, 'left', INK);
      else if (!open) text('f12', '未解锁', cx + 8, y + 15, 'left', LOCK);
      else { stamps(A, m, s, cx + 13, y + 10, 4, 11); text('m12', String(m.best[s]), cx + 104, y + 14, 'right', INK); }
      if (here) {
        rect(x - 22, y - 43, 44, 16, 8, GOLD, 255, INK, 1); text('m12', 'NABO', x, y - 31, 'center', INK);
        tri(x, y - 23, 6, false, INK);
      }
    }
    header(`冒险地图 · ${A.STATION[m.cursor].world}`, `章 ${stampCount(A, m)}/24`);
    if (m.cursor === 0) footer('OK 进入护照亭 · 上/下 走');
    else if (!A.unlocked(m, m.cursor)) footer(`拿到${A.STATION[m.cursor - 1].cn}的铜章后解锁`);
    else footer('OK 进入 · 长按OK 护照 · 上/下 走');
  }

  function kiosk(A, m) {
    band(0, 320, rgb(246, 226, 180), rgb(232, 176, 120));
    header('护照亭', `章 ${stampCount(A, m)}/24`);
    text('f18', '欢迎来到小镇护照亭', 120, 72, 'center', INK);
    text('f12', '盖过的章都收在冒险护照里', 120, 94, 'center', INK);
    ['冒险护照', '设置', '返回地图'].forEach((s, i) => {
      const on = i === m.kiosk, y = 124 + i * 46;
      rect(30, y, 180, 36, 10, on ? GOLD : PAPER, 255, INK, on ? 2 : 1); text('f18', s, 120, y + 25, 'center', INK);
    });
    footer('上/下选择 · OK确认 · 长按上返回');
  }

  function passport(A, m) {
    band(0, 320, rgb(30, 40, 74), rgb(58, 36, 70));
    header('冒险护照', `章 ${stampCount(A, m)}/24`);
    for (let i = 0; i < 8; i++) {
      const s = i + 1, x = i % 2 ? 124 : 12, y = 38 + (i >> 1) * 57, on = i === m.passport, open = A.unlocked(m, s);
      rect(x, y, 104, 52, 8, open ? PAPER : rgb(70, 70, 90), 255, on ? GOLD : INK, on ? 3 : 1);
      rect(x + 4, y + 4, 6, 44, 3, rgb(...STATION_COLOR[s]), open ? 255 : 90);
      text('f16', A.STATION[s].cn, x + 16, y + 21, 'left', open ? INK : LOCK);
      stamps(A, m, s, x + 22, y + 37, 5, 13);
      text('m12', String(m.best[s]), x + 98, y + 41, 'right', open ? INK : LOCK);
    }
    const s = m.passport + 1, e = A.earned(m);
    let t = 0; while (t < 3 && (e & A.bit(s, t))) t++;
    const name = A.STATION[s].cn;
    text('f16', t === 3 ? `${name} · 三枚章已集齐` : `${name} · 最佳 ${m.best[s]} · ${['铜章', '银章', '金章'][t]} ${A.threshold(s, t)}`,
      120, 282, 'center', PAPER);
    footer('上/下 查看 · OK 返回');
  }

  function stamp(A, m) {
    const s = (m.stamp / 3 | 0) + 1, t = m.stamp % 3, st = A.STATION[s];
    band(0, 320, INK, rgb(46, 30, 64));
    text('f18', '获得新印章', 120, 52, 'center', GOLD); text('f16', `${st.world} · ${st.cn}`, 120, 78, 'center', PAPER);
    glow(120, 162, 86, TIER[t]); circle(120, 162, 60, TIER[t], 255, INK, 3); circle(120, 162, 50, TIER[t], 0, INK, 1);
    text('p28', st.en, 120, 172, 'center', INK); text('f18', ['铜章', '银章', '金章'][t], 120, 246, 'center', TIER[t]);
    text('f16', t === 0 && s + 1 < 9 ? `解锁下一站：${A.STATION[s + 1].cn}` : t === 1 ? '解锁第二款服装' : '护照金章', 120, 272, 'center', PAPER);
    footer('OK 收下');
  }

  function settings(A, m) {
    const cfg = m.cfg;
    band(0, 320, INK, rgb(40, 34, 70));
    if (cfg.page === A.CG.STATUS) {
      text('p28', 'STATUS', 120, 39, 'center', GOLD); text('f18', 'NABO 的冒险之旅', 120, 94, 'center', PAPER);
      text('m12', 'prototype', 120, 119, 'center', GOLD); text('f16', '按任意键返回设置', 120, 305, 'center', PAPER);
      return;
    }
    text('p28', 'SETTINGS', 120, 39, 'center', GOLD);
    text('f16', cfg.editing >= 0 ? '上/下调整 · OK保存' : '声音 · 显示 · 休眠', 120, 69, 'center', PAPER);
    const v = cfg.s;
    ['音量', '亮度', '扬声器', '自动休眠', '设备状态', '返回'].forEach((name, i) => {
      const on = i === cfg.cursor, y = 93 + 30 * i;
      rect(16, y, 208, 27, 5, on ? GOLD : INK, 255, hex565(0x42ec), on ? 1 : 0);
      text('f18', name, 26, y + 21, 'left', on ? INK : PAPER);
      const value = [`${v.volume}%`, `${v.brightness}%`, v.speaker ? '开' : '关', v.sleep ? `${v.sleep}秒` : '不休眠', '', ''][i];
      text('f16', value, 214, y + 20, 'right', on ? INK : PAPER);
    });
    text('f16', cfg.editing >= 0 ? '长按上取消本次调整' : '长按上返回护照亭', 120, 305, 'center', PAPER);
  }

  function legacy(A, m) {
    band(0, 320, rgb(28, 36, 86), rgb(60, 50, 90));
    text('p28', A.STATION[m.cursor].en, 120, 120, 'center', WHITE);
    text('f18', `${A.STATION[m.cursor].cn}（固件里的现成游戏）`, 120, 160, 'center', PAPER);
    text('f12', '原型不模拟；在右侧填成绩后点“离开”', 120, 200, 'center', PAPER);
  }

  function session(A, m) {
    const s = m.session, st = A.STATION[s.station], [r, g, b] = STATION_COLOR[s.station];
    if(s.station===3){root.AdvPostDraw.session(c,m,A);return;}
    band(0, 320, rgb(r / 5 | 0, g / 5 | 0, (b / 4 | 0) + 20), rgb(r / 2 | 0, g / 2 | 0, b / 2 | 0));
    if (s.phase === A.PHASE.TITLE) {
      text('f12', st.world, 120, 44, 'center', PAPER); text('p28', st.en, 120, 80, 'center', WHITE);
      text('f18', st.cn, 120, 108, 'center', GOLD);
      if (st.placeholder) { rect(80, 120, 80, 20, 10, GOLD, 255, INK, 1); text('f12', '占位关卡', 120, 135, 'center', INK); }
      if(s.station===3){
        text('f12','先看待送的第一封信',120,132,'center',PAPER);
        text('f12','蒸汽空了结束',120,150,'center',PAPER);
        text('f12','下键 分步练习',120,173,'center',GOLD);
      }
      const e = A.earned(m);
      for (let t = 0; t < 3; t++) {
        const x = 60 + t * 60, on = e & A.bit(s.station, t);
        circle(x, 182, 18, TIER[t], on ? 255 : 40, on ? INK : TIER[t], 2);
        text('m12', String(A.threshold(s.station, t)), x, 218, 'center', PAPER);
      }
      text('f18', `最佳 ${m.best[s.station]}`, 120, 254, 'center', PAPER); footer('OK 开始 · 双击上 回地图');
      return;
    }
    const d = s.game;
    if(s.station===3)root.AdvPostDraw.draw(c,d);
    else {
    text('f16', '占位关卡', 120, 108, 'center', PAPER);
    text('f12', '正式玩法和美术完成后替换', 120, 128, 'center', DIM);
    const zx = 20 + (d.zc - d.zh) * 200 / 1000 | 0, zw = d.zh * 400 / 1000 | 0, mx = 20 + d.p * 200 / 1000 | 0;
    rect(16, 180, 208, 20, 10, INK, 200, d.miss ? RED : PAPER, d.miss ? 2 : 1);
    rect(zx, 182, zw, 16, 8, rgb(r, g, b), 230);
    if (d.hit) glow(mx, 190, 26, GOLD);
    rect(mx - 3, 174, 6, 32, 3, WHITE, 255, INK, 1); tri(mx, 214, 10, true, WHITE);
    text('f12', '色块里按 OK 得分 · 按错扣四分之一', 120, 248, 'center', PAPER);
    }
    rect(0, 0, 240, 34, 0, INK, 210); text('f12', st.res, 10, 21, 'left', PAPER);
    rect(40, 12, 124, 10, 5, rgb(20, 24, 40), 255, PAPER, 1);
    const w = d.res * 120 / 1000 | 0;
    if (w > 0) rect(42, 14, w, 6, 3, d.res < 250 ? RED : rgb(r, g, b), 255);
    text('p28', String(d.score), 230, 29, 'right', WHITE);
    const card = (y, h) => { rect(0, 34, 240, 286, 0, INK, 150); rect(24, y, 192, h, 14, PAPER, 250, INK, 2); };
    if(s.phase===A.PHASE.PLAY)footer('双击上回地图 · 长按上暂停');
    if (s.phase === A.PHASE.READY) {
      glow(120, 150, 50, GOLD); text('p48', String(Math.ceil(s.t / 60)), 120, 168, 'center', WHITE);
      text('f18', '准备', 120, 270, 'center', PAPER);
    } else if (s.phase === A.PHASE.END) {
      rect(70, 136, 100, 40, 12, INK, 230, RED, 2); text('f18', '结束', 120, 163, 'center', PAPER);
    } else if (s.phase === A.PHASE.PAUSE) {
      card(80, 160); text('f18', '暂停', 120, 112, 'center', INK); text('f16', 'OK 继续', 120, 148, 'center', INK);
      text('f16', '下 重新开始', 120, 178, 'center', INK); text('f16', '双击上 回地图', 120, 208, 'center', INK);
    } else if (s.phase === A.PHASE.RESULT) {
      card(60, 200); text('f16', '本局成绩', 120, 88, 'center', INK); text('p48', String(d.score), 120, 142, 'center', INK);
      if (s.record) { rect(82, 152, 76, 20, 10, GOLD, 255, INK, 1); text('f12', m.test ? '测试不记录' : '新纪录', 120, 167, 'center', INK); }
      text('f16', `最佳 ${m.best[s.station]}`, 120, 194, 'center', INK);
      stamps(A, m, s.station, 92, 226, 9, 28); footer('OK 再来一局 · 双击上 回地图');
    }
  }

  function draw(ctx, m, A) {
    if(m.page===A.PAGE.SESSION&&m.session.station===4&&root.AdvNightDraw){root.AdvNightDraw.session(ctx,m,A,performance.now());return;}
    c = ctx;
    c.clearRect(0, 0, c.canvas.width, c.canvas.height);
    [cover, map, kiosk, passport, settings, stamp, legacy, session][m.page](A, m);
  }

  root.AdvDraw = { draw };
})(this);
