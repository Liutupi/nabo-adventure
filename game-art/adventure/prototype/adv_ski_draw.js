// SKI V2 G1 renderer (browser). Uses the existing ski_a frames and ski props; ramps, ice and the
// avalanche are procedural. No sprite rotation or mirroring, so the firmware can draw the same thing.
(function (root) {
  'use strict';
  const S = root.AdvSki, K = S.K, T = S.T, W = K.W, H = K.H, NY = K.NABO_Y;
  const img = new Map(), clips = new Map(), props = new Map();
  async function load(base = '../art/') {
    const inline = root.SKI_SPRITES;
    const manifest = inline ? inline.manifest : await (await fetch(base + 'ski-manifest.json')).json();
    const want = new Set();
    for (const c of manifest.animations) if (c.skin === 'ski_a') { clips.set(c.name, c); c.runtime_frames.forEach(p => want.add(p)); }
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
    const [ax, ay] = a.anchor || [im.width >> 1, im.height]; c.drawImage(im, Math.round(x - ax), Math.round(y - ay));
  }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(20,40,70,.85)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }

  function slope(c, wy, vt) {
    const gr = c.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#f4f8fc'); gr.addColorStop(1, '#dfe9f4'); c.fillStyle = gr; c.fillRect(0, 0, W, H);
    // snow texture and old tracks scroll with the run
    const top = wy - NY;
    for (let i = Math.floor(top / 14) - 1; i < (top + H) / 14 + 1; i++) {
      for (let k = 0; k < 3; k++) {
        const h = hash(i * 7 + k * 131), x = h * W, y = i * 14 - top + hash(i * 3 + k) * 14;
        c.fillStyle = h < .5 ? 'rgba(160,185,215,.35)' : 'rgba(255,255,255,.9)'; c.fillRect(x | 0, y | 0, h < .5 ? 3 : 2, 1);
      }
    }
    c.strokeStyle = 'rgba(170,195,225,.35)'; c.lineWidth = 1;
    for (let k = 0; k < 3; k++) { c.beginPath(); for (let y = -10; y <= H + 10; y += 10) { const wy2 = y + top, x = 60 + k * 100 + Math.sin(wy2 * 0.012 + k * 2) * 30; y === -10 ? c.moveTo(x, y) : c.lineTo(x, y); } c.stroke(); }
  }

  function objects(c, g, layer) {           // layer 0: flat things under NABO; 1: standing things, back to front
    const top = (g.y >> 8) - NY, list = g.objs.filter(o => o.type && o.y - top > -70 && o.y - top < H + 70).sort((a, b) => a.y - b.y);
    for (const o of list) {
      const y = o.y - top;
      if (layer === 0) {
        if (o.type === T.ICE) { c.fillStyle = 'rgba(170,225,245,.7)'; c.beginPath(); c.roundRect(o.x - K.ICE_HALF, y, K.ICE_HALF * 2, K.ICE_LEN, 14); c.fill(); c.strokeStyle = 'rgba(255,255,255,.9)'; c.beginPath(); c.moveTo(o.x - 18, y + 14); c.lineTo(o.x + 4, y + 30); c.stroke(); }
        if (o.type === T.KICKER) { c.fillStyle = '#bcd3ea'; c.beginPath(); c.moveTo(o.x - 20, y - 14); c.lineTo(o.x + 20, y - 14); c.lineTo(o.x + 24, y + 2); c.lineTo(o.x - 24, y + 2); c.fill(); c.fillStyle = '#ffffff'; c.fillRect(o.x - 20, y - 14, 40, 5); c.fillStyle = '#e8573f'; c.fillRect(o.x - 3, y - 13, 6, 3); }
        continue;
      }
      if (o.type === T.GATE_RED) prop(c, 'ski/props/gate-red', o.x, y);
      else if (o.type === T.GATE_BLUE) prop(c, 'ski/props/gate-blue', o.x, y);
      else if (o.type === T.TREE) prop(c, 'ski/props/pine-large', o.x, y);
      else if (o.type === T.PINE) prop(c, 'ski/shared/pine-small', o.x, y);
      else if (o.type === T.MOGUL) prop(c, 'ski/shared/snow-mogul', o.x, y);
      else if (o.type === T.DRIFT) prop(c, 'ski/shared/snow-drift', o.x, y);
    }
  }

  function nabo(c, g, phase, vt) {
    const x = g.x >> 8;
    let name = 'straight', f = Math.floor(vt / 6) % 6, lift = 0;
    if (g.vx < -170) { name = 'lean_left'; f = Math.floor(vt / 8) % 4; } else if (g.vx > 170) { name = 'lean_right'; f = Math.floor(vt / 8) % 4; }
    if (g.air > 0) {
      const t = g.airMax - g.air, T2 = g.airMax, peak = g.airMax > 30 ? 26 : g.airMax > 12 ? 10 : 4;
      lift = Math.round(4 * peak * t * (T2 - t) / (T2 * T2)); name = 'jump'; f = Math.min(5, Math.floor(t * 6 / T2));
      if (g.spinT > 0) { const k = Math.floor((K.SPIN - g.spinT) / 6) % 4; name = ['lean_left', 'straight', 'lean_right', 'straight'][k]; f = 1; }
    }
    if (g.crash > 0) { name = 'fall'; f = Math.min(7, Math.floor((K.CRASH - g.crash) / 5)); lift = 0; }
    if (phase === 'RESULT' || g.over) { name = 'fall'; f = 7; }
    c.fillStyle = 'rgba(60,90,130,.25)'; c.beginPath(); c.ellipse(x, NY + 1, 15 - lift / 4, 4, 0, 0, 7); c.fill();
    actor(c, name, f, x, NY - lift);
    if (g.spinT > 0) { c.strokeStyle = 'rgba(255,215,90,.9)'; c.lineWidth = 2; c.beginPath(); c.arc(x, NY - lift - 30, 26, (vt * .4) % 6.28, (vt * .4) % 6.28 + 4); c.stroke(); }
  }

  function avalanche(c, g, vt) {
    const gapPx = Math.max(0, S.gap(g) >> 8), front = NY - Math.round(gapPx * (NY + 40) / K.AVAL_CAP);
    if (front < -36) return;
    const top = (g.y >> 8);
    c.fillStyle = '#ffffff'; c.fillRect(0, 0, W, Math.max(0, front));
    for (let x = -10; x < W + 20; x += 16) {
      const h = hash(Math.floor(x / 16) * 13), r = 14 + h * 12, y = front + Math.sin((top + x) * 0.05 + vt * 0.15 + h * 6) * 5;
      c.fillStyle = h < .5 ? '#ffffff' : '#eef3fa'; c.beginPath(); c.arc(x, y, r, 0, 7); c.fill();
      c.fillStyle = 'rgba(150,175,205,.35)'; c.beginPath(); c.arc(x + 3, y + 5, r * .6, 0, 3.14); c.fill();
    }
    for (let i = 0; i < 18; i++) { const h = hash(i * 31 + (vt >> 2)), px = h * W, py = front + 10 + hash(i * 7 + vt) * 30; c.fillStyle = 'rgba(255,255,255,.9)'; c.fillRect(px, py, 2, 2); }
  }

  function hud(c, g, vt) {
    const pct = g.res / 1000, low = pct < .3;
    const Y = H - 26;          // bottom strip: the avalanche owns the top of the screen
    c.fillStyle = 'rgba(20,40,70,.78)'; c.fillRect(0, Y, W, 26);
    text(c, '雪崩', 8, Y + 8, 10, '#ffffff', 'left', 700, null);
    c.fillStyle = 'rgba(255,255,255,.18)'; c.fillRect(34, Y + 5, 86, 7);
    c.fillStyle = low ? (vt % 20 < 10 ? '#ff6a4a' : '#ffb2a0') : pct < .6 ? '#ffc34a' : '#8fe0a8'; c.fillRect(34, Y + 5, 86 * pct, 7);
    text(c, '速度', 8, Y + 19, 10, '#ffffff', 'left', 700, null);
    c.fillStyle = 'rgba(255,255,255,.18)'; c.fillRect(34, Y + 17, 86, 5); c.fillStyle = '#7ec8ff'; c.fillRect(34, Y + 17, 86 * Math.min(1, g.flow / K.FLOW_MAX), 5);
    const m = S.mult(g);
    if (g.combo >= 2) text(c, `${g.combo}连` + (m > 1 ? ` ×${m}` : ''), 136, Y + 13, 11, m > 1 ? '#ffd34a' : '#ffffff', 'left', 900, null);
    text(c, `${g.meters} m`, 236, Y + 13, 10, '#c8dcf5', 'right', 700, null);
    text(c, String(g.score), W - 8, Y + 13, 18, '#ffffff', 'right', 900, null);
  }

  const SECTION = [null, ['旗门密集', '连过旗门越滑越快'], ['进入树林', '小心大树'], ['跳台公园', '起跳后按中键转体'], ['冰面', '转向变慢'], ['起雾了', '看不清远处']];
  function fx(c, g) {
    const top = (g.y >> 8) - NY, F = S.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      const a = Math.max(0, 1 - e.t / 60); c.globalAlpha = a;
      if (e.kind === F.GATE) text(c, '+' + e.val, e.x, e.y - e.t * .4, 12, '#ffd34a', 'center');
      else if (e.kind === F.MISS) text(c, '漏门', e.x, e.y - e.t * .3, 12, '#ff8a6a', 'center');
      else if (e.kind === F.CRASH) text(c, '撞树了！', e.x, e.y - 50, 14, '#ff8a6a', 'center');
      else if (e.kind === F.STUMBLE) text(c, '绊了一下', e.x, e.y - 50, 12, '#ffb08a', 'center');
      else if (e.kind === F.WIPE) text(c, '没转完就落地', e.x, e.y - 66, 12, '#ff8a6a', 'center');
      else if (e.kind === F.LAND) text(c, `转体 +${e.val}`, e.x, e.y - 60 - e.t * .3, 14, '#ffd34a', 'center');
      else if (e.kind === F.KICK) text(c, '起跳！按中键转体', e.x, e.y - 74, 11, '#ffffff', 'center');
      else if (e.kind === F.NEAR) text(c, '好险', e.x, e.y - 56 - e.t * .3, 11, '#9fd8ff', 'center');
      else if (e.kind === F.SECTION && SECTION[e.val]) {
        const slide = e.t < 10 ? (10 - e.t) * 20 : 0; c.globalAlpha = Math.min(1, (70 - e.t) / 15);
        c.fillStyle = 'rgba(20,40,70,.7)'; c.fillRect(0, 160, W, 40);
        text(c, SECTION[e.val][0], W / 2 + slide, 173, 16, '#ffd34a', 'center', 900, null); text(c, SECTION[e.val][1], W / 2 + slide, 191, 10, '#ffffff', 'center', 700, null);
      }
      c.globalAlpha = 1;
    }
  }

  function title(c, vt, best) {
    const fake = S.start(1); fake.y = vt * 600; fake.x = (160 + Math.round(Math.sin(vt * .03) * 60)) << 8; fake.vx = Math.round(Math.cos(vt * .03) * 400);
    slope(c, fake.y >> 8, vt); nabo(c, fake, 'TITLE', vt);
    c.fillStyle = 'rgba(20,40,70,.55)'; c.fillRect(0, 110, W, 130);
    text(c, '雪崩速降', W / 2, 132, 26, '#ffffff', 'center');
    text(c, '◀ 左转   ● 跳 / 空中转体   ▶ 右转', W / 2, 162, 11, '#d6e8ff', 'center', 700, null);
    text(c, '过旗门、做转体越滑越快，别让雪崩追上', W / 2, 182, 11, '#d6e8ff', 'center', 700, null);
    if (best) text(c, '最佳 ' + best, W - 10, 18, 11, '#ffd34a', 'right');
    if (vt % 60 < 42) text(c, '按 ● 开始', W / 2, 214, 13, '#ffffff', 'center');
  }

  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    slope(c, g.y >> 8, vt); objects(c, g, 0);
    // standing objects above NABO's feet are behind him, the rest in front
    const top = (g.y >> 8) - NY, behind = { ...g, objs: g.objs.map(o => (o.type && o.y - top <= NY ? o : { type: 0 })) }, front = { ...g, objs: g.objs.map(o => (o.type && o.y - top > NY ? o : { type: 0 })) };
    objects(c, behind, 1); nabo(c, g, phase, vt); objects(c, front, 1);
    if (g.section === S.SEC.FOG) { const gr = c.createLinearGradient(0, NY + 30, 0, H); gr.addColorStop(0, 'rgba(240,245,250,0)'); gr.addColorStop(.35, 'rgba(240,245,250,.92)'); gr.addColorStop(1, 'rgba(240,245,250,1)'); c.fillStyle = gr; c.fillRect(0, NY + 30, W, H); }
    avalanche(c, g, vt); fx(c, g); hud(c, g, vt);
    if (phase === 'READY') { const n = Math.ceil(info.countdown / 60); text(c, n > 0 ? String(n) : '冲！', W / 2, 140, 34, '#ffffff', 'center'); text(c, '雪崩从后面追来了', W / 2, 172, 11, '#ffffff', 'center', 700); }
    if (phase === 'PAUSE') {
      c.fillStyle = 'rgba(20,40,70,.75)'; c.fillRect(0, 0, W, H); text(c, '暂停', W / 2, 70, 24, '#ffffff', 'center');
      [['●', '继续'], ['◀', '重来'], ['▶▶', '双击回地图']].forEach(([k, s], i) => text(c, `${k}  ${s}`, W / 2, 112 + i * 22, 12, '#d6e8ff', 'center', 700, null));
    }
    if (phase === 'RESULT') {
      const k = Math.min(1, phaseT / 30); c.fillStyle = `rgba(20,40,70,${.75 * k})`; c.fillRect(0, 0, W, H);
      if (phaseT > 20) {
        text(c, '被雪崩追上了', W / 2, 36, 12, '#c8dcf5', 'center', 700, null);
        text(c, String(g.score), W / 2, 80, 40, '#ffffff', 'center');
        if (g.score >= best && g.score > 0) text(c, '新纪录!', W / 2 + 76, 62, 12, '#ffd34a', 'center');
        text(c, `${g.meters} 米 · 旗门 ${g.passed}/${g.passed + g.misses} · 转体 ${g.tricks} · 最长 ${g.best} 连`, W / 2, 120, 10, '#d6e8ff', 'center', 700, null);
        if (phaseT > 50 && vt % 60 < 42) text(c, '● 再来一局', W / 2, 200, 13, '#ffffff', 'center');
      }
    }
  }
  root.AdvSkiDraw = { load, draw };
})(window);
