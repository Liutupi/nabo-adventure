// CLIMB V2 G1 renderer (browser only). NABO uses the existing climb_a frames unchanged (no rotation/mirroring/scaling);
// holds, rock, canteen and wall tiles are the existing climb props. Lane cliff edges, far peaks, flags, the rope and
// the night light are procedural. Everything here can be drawn by the firmware renderer as-is.
(function (root) {
  'use strict';
  const S = root.AdvClimbV2, K = S.K, HD = S.H, W = K.W, H = K.H, NY = K.NY;
  const img = new Map(), clips = new Map(), props = new Map();
  const EXTRA = ['space-v2/bg-cloud-far.png', 'space-v2/bg-cirrus.png'];
  async function load(base = '../art/') {
    const inline = root.CLIMB_SPRITES;
    const manifest = inline ? inline.manifest : await (await fetch(base + 'climb-manifest.json')).json();
    const want = new Set(EXTRA);
    for (const c of manifest.animations) if (c.skin === 'climb_a') { clips.set(c.name, c); c.runtime_frames.forEach(p => want.add(p)); }
    for (const a of manifest.assets) { props.set(a.id, a); want.add(a.path); }
    await Promise.all([...want].map(async p => { const im = new Image(); im.src = inline ? inline.files[p] : base + p; await im.decode(); img.set(p, im); }));
  }
  const hash = n => { n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b); n ^= n >>> 13; n = Math.imul(n, 0xc2b2ae35); return ((n ^ n >>> 16) >>> 0) / 4294967296; };
  function actor(c, name, f, x, y) {
    const clip = clips.get(name); if (!clip) return;
    const im = img.get(clip.runtime_frames[Math.max(0, Math.min(clip.runtime_frames.length - 1, f))]);
    if (im) c.drawImage(im, Math.round(x - clip.runtime_anchor[0]), Math.round(y - clip.runtime_anchor[1]));
  }
  function prop(c, id, x, y) {
    const a = props.get(id), im = a && img.get(a.path); if (!im) return;
    const [ax, ay] = a.anchor || [im.width >> 1, im.height >> 1]; c.drawImage(im, Math.round(x - ax), Math.round(y - ay));
  }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(30,34,52,.88)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  const camRow = g => g.row - (g.tween > 0 ? g.tween / K.TWEEN : 0) * (g.stun ? -1 : 1);
  const rowY = (g, r) => NY - 31 - (r - camRow(g)) * K.STEP;   // climb_a grip contact is (∓23, -41) from the anchor at NY + 10
  const WALL = [52, 268];

  function backdrop(c, g, vt) {
    const hgt = camRow(g), sky = c.createLinearGradient(0, 0, 0, H);
    const high = Math.min(1, hgt / 240);
    sky.addColorStop(0, high > .5 ? '#3d6fb8' : '#6aa8e8'); sky.addColorStop(1, high > .5 ? '#cfe3f6' : '#e9f4fb'); c.fillStyle = sky; c.fillRect(0, 0, W, H);
    const ci = img.get(EXTRA[1]); if (ci) { c.globalAlpha = .6; c.drawImage(ci, -((vt * .1) % 320), 20); c.drawImage(ci, 320 - ((vt * .1) % 320), 20); c.globalAlpha = 1; }
    // far peaks sink slowly as NABO climbs: depth without a new bitmap
    const base = 200 + Math.min(120, hgt * .35);
    c.fillStyle = '#9fb6d6';
    for (let i = -1; i < 6; i++) { const x = i * 70 + 20, h = 60 + hash(i + 3) * 50; c.beginPath(); c.moveTo(x - 50, base); c.lineTo(x, base - h); c.lineTo(x + 50, base); c.fill(); c.fillStyle = '#ffffff'; c.beginPath(); c.moveTo(x - 12, base - h + 14); c.lineTo(x, base - h); c.lineTo(x + 12, base - h + 14); c.fill(); c.fillStyle = '#9fb6d6'; }
    const cf = img.get(EXTRA[0]); if (cf) { const y = base - 30; c.globalAlpha = .8; c.drawImage(cf, -((vt * .25) % 320), y); c.drawImage(cf, 320 - ((vt * .25) % 320), y); c.globalAlpha = 1; }
  }
  function wall(c, g) {
    const top = camRow(g) * K.STEP, band = h => (h < 60 * K.STEP ? 'grey' : h < 140 * K.STEP ? 'cold' : 'snow');
    const off = Math.floor(top) % 32;
    for (let ty = -32; ty < H + 32; ty += 32) {
      const worldY = top + (H - ty);
      for (let tx = WALL[0]; tx < WALL[1]; tx += 32) {
        const id = `climb/tiles/${band(worldY)}-${(hash(Math.floor(worldY / 32) * 17 + tx) * 2) | 0}`, a = props.get(id), im = a && img.get(a.path);
        if (im) c.drawImage(im, tx, ty + off);
      }
    }
    // ragged cliff edges
    c.fillStyle = 'rgba(40,46,64,.55)';
    for (let y = -8; y < H + 8; y += 8) { const k = Math.floor((top - y) / 8); c.fillRect(WALL[0] - 2 + Math.round(hash(k) * 6), y + (off % 8), 4, 8); c.fillRect(WALL[1] - 4 - Math.round(hash(k + 99) * 6), y + (off % 8), 4, 8); }
    // push the rock texture back so holds pop; lanes get a faint chalk band so the two routes read at a glance
    c.fillStyle = 'rgba(22,28,44,.42)'; c.fillRect(WALL[0], 0, WALL[1] - WALL[0], H);
    for (const lx of K.LANE_X) { c.fillStyle = 'rgba(255,255,255,.07)'; c.fillRect(lx - 34, 0, 68, H); }
  }

  function holds(c, g, vt) {
    const r0 = Math.floor(camRow(g)) - 4, r1 = r0 + 14;
    // chalk route line per lane: joins consecutive holds so each lane reads as one path
    c.lineWidth = 2;
    for (let l = 0; l < 2; l++) {
      c.strokeStyle = l === g.lane ? 'rgba(255,255,255,.22)' : 'rgba(255,255,255,.1)'; c.beginPath(); let pen = false;
      for (let r = Math.max(0, r0); r <= Math.min(r1, g.genRow - 1); r++) {
        const h = S.holdAt(g, r, l), x = S.holdX(r, l), y = rowY(g, r);
        if (!h) { pen = false; continue; }
        if (pen) c.lineTo(x, y); else c.moveTo(x, y); pen = true;
      }
      c.stroke();
    }
    for (let r = Math.max(0, r0); r <= r1; r++) {
      if (r > g.genRow - 1) break;
      const y = rowY(g, r), o = S.rowAt(g, r);
      if (y < -20 || y > H + 20) continue;
      for (let l = 0; l < 2; l++) {
        const h = l ? o.h1 : o.h0, it = l ? o.i1 : o.i0, x = S.holdX(r, l);
        if (!h) { c.fillStyle = 'rgba(30,30,40,.35)'; c.fillRect(K.LANE_X[l] - 2, y - 6, 3, 12); continue; }
        const next = l === g.lane && r === g.row + 1 && !g.trav;
        if (next) { c.strokeStyle = `rgba(255,230,120,${.6 + .4 * Math.sin(vt * .3)})`; c.lineWidth = 2; c.beginPath(); c.arc(x, y, 13, 0, 7); c.stroke(); text(c, S.sideOf(r, l) ? '▶' : '◀', x + (S.sideOf(r, l) ? 20 : -20), y, 10, '#ffe680', 'center', 900); }
        c.fillStyle = h === HD.ICE ? 'rgba(150,220,255,.35)' : h === HD.FRAGILE ? 'rgba(255,170,110,.32)' : 'rgba(255,240,200,.28)'; c.beginPath(); c.ellipse(x, y + 1, 13, 10, 0, 0, 7); c.fill();
        prop(c, h === HD.ICE ? 'climb/props/hold-ice' : h === HD.FRAGILE ? 'climb/props/hold-fragile' : 'climb/props/hold-normal', x, y);
        if (h === HD.FRAGILE && l === g.lane && r === g.row && g.crumble > 0 && (vt >> 1 & 1)) { c.fillStyle = 'rgba(120,80,50,.6)'; c.fillRect(x - 6, y + 6, 2, 3 + (K.CRUMBLE - g.crumble) / 6); }
        if (it === S.ITEM.CANTEEN) prop(c, 'climb/props/canteen', x + (S.sideOf(r, l) ? -16 : 16), y + 8);
        if (it === S.ITEM.FLAG) { const fx2 = x + (S.sideOf(r, l) ? -16 : 16); c.fillStyle = '#6b4a32'; c.fillRect(fx2, y - 14, 2, 20); c.fillStyle = '#e8473a'; c.beginPath(); c.moveTo(fx2 + 2, y - 14); c.lineTo(fx2 + 13, y - 10 + Math.sin(vt * .2) * 2); c.lineTo(fx2 + 2, y - 6); c.fill(); }
      }
    }
  }

  function nabo(c, g, phase, vt) {
    const side = S.sideOf(g.row, g.lane), dir = side ? 'right' : 'left';
    let x = K.LANE_X[g.lane], y = NY + 10, name = 'grip_idle_' + dir, f = (vt >> 3) % 6;
    if (g.trav > 0) { const p = 1 - g.trav / K.TRAVERSE, to = K.LANE_X[g.lane ^ 1]; x = Math.round(x + (to - x) * p); y -= Math.round(Math.sin(p * Math.PI) * 10); name = 'jump_' + (to > K.LANE_X[g.lane] ? 'right' : 'left'); f = Math.min(5, (p * 6) | 0); }
    else if (g.stun > 0) { name = 'slide_' + dir; f = Math.min(5, (K.STUN - g.stun) >> 2); }
    else if (g.ice > 0) { name = 'charge_' + dir; f = Math.min(3, (K.ICE_HOLD - g.ice) >> 2); }
    else if (g.tween > 0) { name = 'switch_grab_' + dir; f = Math.min(5, K.TWEEN - g.tween); }
    if (phase === 'RESULT') { name = 'settlement_cheer'; f = 7; x = 160; y = NY + 14; }
    // belay rope down to the last anchor
    c.strokeStyle = '#d0573f'; c.lineWidth = 1; c.beginPath(); c.moveTo(x + 4, y - 18); c.quadraticCurveTo(x + 14, y + 40, x - 6, H + 4); c.stroke();
    if (g.invuln && (vt >> 2 & 1)) c.globalAlpha = .5;
    actor(c, name, f, x, y); c.globalAlpha = 1;
    if (g.ice > 0) { const p = 1 - g.ice / K.ICE_HOLD, hx = S.holdX(g.row, g.lane), hy = rowY(g, g.row); c.strokeStyle = '#bfefff'; c.lineWidth = 3; c.beginPath(); c.arc(hx, hy, 14, -Math.PI / 2, -Math.PI / 2 + p * 6.283); c.stroke(); text(c, '按住', hx, hy - 22, 9, '#e6f8ff', 'center', 800); }
  }

  function rocks(c, g, vt) {
    for (const k of g.rocks) {
      if (!k.on) continue;
      const x = K.LANE_X[k.lane];
      if (k.t > 0) {
        const a = k.t < 30 ? (vt >> 2 & 1 ? .5 : .2) : .18;
        c.fillStyle = `rgba(255,90,60,${a})`; c.fillRect(x - 26, 18, 52, NY - 30);
        c.fillStyle = '#ff5a3c'; c.beginPath(); c.moveTo(x, 20); c.lineTo(x + 9, 36); c.lineTo(x - 9, 36); c.fill(); text(c, '!', x, 30, 10, '#ffffff', 'center', 900, null);
      } else prop(c, 'climb/props/falling-rock', x + Math.round(Math.sin(k.y * .2) * 2), k.y);
    }
  }

  function hud(c, g, vt) {
    const pct = g.res / 1000, low = pct < .25;
    c.fillStyle = 'rgba(30,34,52,.66)'; c.fillRect(0, 0, W, 18);
    text(c, '握力', 6, 9, 10, '#ffffff', 'left', 700, null);
    c.fillStyle = 'rgba(255,255,255,.2)'; c.fillRect(32, 5, 74, 8);
    c.fillStyle = low ? (vt % 20 < 10 ? '#ff5a4a' : '#ffb0a0') : pct < .5 ? '#ffc34a' : '#8fe0a8'; c.fillRect(32, 5, 74 * pct, 8);
    const m = S.mult(g);
    if (g.combo >= 3) text(c, `节奏 ${g.combo}` + (m > 1 ? ` ×${m}` : ''), 160, 9, 11, m > 1 ? '#ffd34a' : '#ffffff', 'center', 900, null);
    text(c, `${g.meters} m`, W - 52, 9, 10, '#cfe0f5', 'right', 700, null);
    text(c, String(g.score), W - 6, 9, 14, '#ffffff', 'right', 900, null);
  }

  const SECTION = [null, ['落石区', '看到红色警告就换线'], ['冰壁', '冰点要按住抓牢'], ['碎石段', '碎石点别停留'], ['入夜', '只看得清身边'], ['冲刺', '节奏分翻倍']];
  function fx(c, g) {
    const F = S.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      c.globalAlpha = Math.max(0, 1 - e.t / 60);
      if (e.kind === F.SLIP) text(c, '打滑', e.x, e.y - e.t * .3, 12, '#ff9a7a', 'center');
      else if (e.kind === F.ROCK) text(c, '被落石砸到！', e.x, e.y - 10, 13, '#ff7a5a', 'center');
      else if (e.kind === F.CRUMBLE) text(c, '碎了！', e.x, e.y - e.t * .3, 12, '#ffb07a', 'center');
      else if (e.kind === F.NOHOLD) text(c, '这条线断了 · 按 ● 换线', e.x, e.y, 10, '#ffe0a0', 'center');
      else if (e.kind === F.CANTEEN) text(c, '+握力', e.x, e.y - e.t * .3, 11, '#a8f0c0', 'center');
      else if (e.kind === F.FLAG) text(c, '+' + e.val, e.x, e.y - e.t * .4, 12, '#ffd34a', 'center');
      else if (e.kind === F.NEAR) text(c, '好险', e.x, e.y - e.t * .3, 11, '#bfe6ff', 'center');
      else if (e.kind === F.RHYTHM) text(c, `${e.val} 连节奏!`, 160, 44 - e.t * .2, 14, '#ffd34a', 'center');
      else if (e.kind === F.SECTION && SECTION[e.val]) {
        const slide = e.t < 10 ? (10 - e.t) * 20 : 0; c.globalAlpha = Math.min(1, (70 - e.t) / 15);
        c.fillStyle = 'rgba(30,34,52,.7)'; c.fillRect(0, 190, W, 36);
        text(c, SECTION[e.val][0], W / 2 + slide, 201, 15, '#ffd34a', 'center', 900, null); text(c, SECTION[e.val][1], W / 2 + slide, 217, 10, '#ffffff', 'center', 700, null);
      }
      c.globalAlpha = 1;
    }
  }
  function night(c, g) {
    if (g.section !== S.SEC.NIGHT) return;
    const x = K.LANE_X[g.lane], gr = c.createRadialGradient(x, NY - 30, 30, x, NY - 30, 120);
    gr.addColorStop(0, 'rgba(10,14,34,0)'); gr.addColorStop(1, 'rgba(10,14,34,.9)'); c.fillStyle = gr; c.fillRect(0, 0, W, H);
  }

  function keyRow(c, y, items) {
    items.forEach(([k, s], i) => { const x = 60 + i * 100; c.fillStyle = 'rgba(255,255,255,.16)'; c.beginPath(); c.roundRect(x - 44, y - 11, 88, 22, 8); c.fill(); text(c, `${k} ${s}`, x, y, 11, '#ffffff', 'center', 800, null); });
  }
  function title(c, vt, best) {
    const fake = S.start(5); fake.row = (vt >> 4); fake.tween = K.TWEEN - ((vt >> 2) & 3); while (fake.genRow <= fake.row + K.AHEAD) { fake.genRow++; }
    for (let r = 0; r < K.ROWS; r++) Object.assign(fake.rows[r], { h0: 1, h1: r % 5 ? 1 : 2, i0: 0, i1: 0 });
    backdrop(c, fake, vt); wall(c, fake); holds(c, fake, vt); nabo(c, fake, 'TITLE', vt);
    c.fillStyle = 'rgba(30,34,52,.6)'; c.fillRect(0, 150, W, 90);
    text(c, '双线攀岩', W / 2, 52, 26, '#ffffff', 'center');
    text(c, '左右手跟着抓点交替，断路和落石就换线', W / 2, 82, 11, '#eef4ff', 'center', 700);
    keyRow(c, 176, [['◀', '左手'], ['●', '换线'], ['▶', '右手']]);
    if (best) text(c, '最佳 ' + best, W - 8, 12, 11, '#ffd34a', 'right');
    if (vt % 60 < 42) text(c, '按 ● 开始', W / 2, 214, 13, '#ffffff', 'center');
  }

  let shake = 0, lastSlip = 0;
  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    if (g.slips !== lastSlip) { shake = 8; lastSlip = g.slips; }
    c.save(); if (shake > 0) { shake--; c.translate(shake & 1 ? 2 : -2, 0); }
    backdrop(c, g, vt); wall(c, g); holds(c, g, vt); rocks(c, g, vt); nabo(c, g, phase, vt); night(c, g);
    c.restore();
    fx(c, g); hud(c, g, vt);
    if (phase === 'READY') { const n = Math.ceil(info.countdown / 60); text(c, n > 0 ? String(n) : '爬！', W / 2, 110, 32, '#ffffff', 'center'); text(c, '跟着黄圈里的箭头按左右', W / 2, 140, 11, '#ffffff', 'center', 700); }
    if (phase === 'PAUSE') {
      c.fillStyle = 'rgba(30,34,52,.78)'; c.fillRect(0, 0, W, H); text(c, '暂停', W / 2, 70, 24, '#ffffff', 'center');
      [['●', '继续'], ['◀', '重来'], ['▶▶', '双击回地图']].forEach(([k, s], i) => text(c, `${k}  ${s}`, W / 2, 112 + i * 22, 12, '#e0e8ff', 'center', 700, null));
    }
    if (phase === 'RESULT') {
      const k = Math.min(1, phaseT / 30); c.fillStyle = `rgba(30,34,52,${.74 * k})`; c.fillRect(0, 0, W, H);
      if (phaseT > 20) {
        const shown = Math.min(g.score, Math.round(g.score * Math.min(1, (phaseT - 20) / 40)));
        text(c, '握力用完，安全绳接住了你', W / 2, 32, 12, '#e0e8ff', 'center', 700, null);
        text(c, String(shown), W / 2, 72, 40, '#ffffff', 'center');
        if (g.score >= best && g.score > 0 && phaseT > 60) text(c, '新纪录!', W / 2 + 80, 54, 12, '#ffd34a', 'center');
        text(c, `${g.meters} 米 · 最长节奏 ${g.best} · 旗子 ${g.flags} · 水壶 ${g.canteens}`, W / 2, 112, 10, '#e0e8ff', 'center', 700, null);
        text(c, `打滑 ${g.slips} · 落石 ${g.rockHits} · 好险 ${g.nearMiss}`, W / 2, 130, 10, '#c4cde8', 'center', 700, null);
        if (phaseT > 60 && vt % 60 < 42) text(c, '● 再来一局', W / 2, 228, 13, '#ffffff', 'center');
      }
    }
  }
  root.AdvClimbV2Draw = { load, draw };
})(window);
