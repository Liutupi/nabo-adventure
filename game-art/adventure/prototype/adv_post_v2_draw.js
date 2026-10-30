// POST V2 G1 renderer (browser only). Train, wheels, cab, NABO (post_a), carriage, envelopes, sheep, cow and far
// mountains are the existing POST art at native size (no scaling/mirroring). Nets, mail cranes, signals, the bridge
// in a limit zone, smoke, sparks and the speedometer are procedural. Clouds reuse SPACE V2 backdrops.
(function (root) {
  'use strict';
  const S = root.AdvPostV2, K = S.K, T = S.T, W = K.W, H = K.H, RAIL = K.RAIL;
  const img = new Map(), clips = new Map(), props = new Map();
  const EXTRA = ['space-v2/bg-cloud-far.png', 'space-v2/bg-cirrus.png'];
  async function load(base = '../art/') {
    const inline = root.POST_SPRITES;
    const manifest = inline ? inline.manifest : await (await fetch(base + 'post-manifest.json')).json();
    const want = new Set(EXTRA);
    for (const c of manifest.animations) if (c.skin === 'post_a' || c.skin === 'post_props') { clips.set(c.skin + '/' + c.name, c); c.runtime_frames.forEach(p => want.add(p)); }
    for (const a of manifest.assets) { props.set(a.id, a); want.add(a.path); }
    await Promise.all([...want].map(async p => { const im = new Image(); im.src = inline ? inline.files[p] : base + p; await im.decode(); img.set(p, im); }));
  }
  const hash = n => { n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b); n ^= n >>> 13; n = Math.imul(n, 0xc2b2ae35); return ((n ^ n >>> 16) >>> 0) / 4294967296; };
  function anim(c, id, f, x, y) {
    const clip = clips.get(id); if (!clip) return;
    const im = img.get(clip.runtime_frames[Math.max(0, Math.min(clip.runtime_frames.length - 1, f))]);
    if (im) c.drawImage(im, Math.round(x - clip.runtime_anchor[0]), Math.round(y - clip.runtime_anchor[1]));
  }
  function prop(c, id, x, y) {          // top-left placement, like the V1 renderer
    const a = props.get('post/' + id), im = a && img.get(a.path); if (im) c.drawImage(im, Math.round(x), Math.round(y));
  }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(32,46,58,.88)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  function tile(c, path, scroll, y, alpha = 1) {
    const im = img.get(path); if (!im) return; c.globalAlpha = alpha;
    const off = ((Math.floor(scroll) % im.width) + im.width) % im.width;
    for (let x = -off; x < W; x += im.width) c.drawImage(im, x, y);
    c.globalAlpha = 1;
  }

  function backdrop(c, g, vt) {
    const d = g.dist / 256, night = g.section === S.SEC.NIGHT, gr = c.createLinearGradient(0, 0, 0, RAIL);
    gr.addColorStop(0, night ? '#1d2a4a' : '#78b8d8'); gr.addColorStop(1, night ? '#3d4a6a' : '#d8ecd8'); c.fillStyle = gr; c.fillRect(0, 0, W, RAIL);
    tile(c, EXTRA[1], d * .05, 16, night ? .25 : .7);
    tile(c, EXTRA[0], d * .1, 40, night ? .3 : .9);
    const fm = props.get('post/tiles/far-mountains'); if (fm) tile(c, fm.path, d * .2, 116);
    // mid hills and hedgerows: procedural, two speeds for depth
    c.fillStyle = night ? '#2f4a3a' : '#88bf6a';
    for (let x = -((d * .45) % 80) - 80; x < W + 80; x += 80) { const k = Math.floor((d * .45 + x) / 80); c.beginPath(); c.ellipse(x, 160, 60, 16 + hash(k) * 10, 0, Math.PI, 0); c.fill(); }
    c.fillStyle = night ? '#2a4434' : '#94ca6a'; c.fillRect(0, 150, W, RAIL - 150);
    c.fillStyle = night ? '#24392c' : '#6fa255';
    for (let x = -((d * .7) % 46); x < W; x += 46) { const k = Math.floor((d * .7 + x) / 46); if (hash(k) < .5) { c.beginPath(); c.arc(x + 10, 176, 9, 0, 7); c.arc(x + 20, 174, 11, 0, 7); c.fill(); } }
  }
  function track(c, g, zones) {
    const d = g.dist / 256;
    c.fillStyle = '#a99a7c'; c.fillRect(0, RAIL - 4, W, H - RAIL + 4);
    c.fillStyle = '#8f8266'; for (let x = -(d % 7); x < W; x += 7) c.fillRect(x, RAIL + 6 + ((x * 7) & 3), 3, 2);
    for (const [x0, x1] of zones) {      // a bridge over a stream marks the limit zone
      c.fillStyle = '#5aa0c8'; c.fillRect(x0, RAIL + 2, x1 - x0, H - RAIL);
      c.fillStyle = '#7ec0e0'; for (let x = x0; x < x1; x += 12) c.fillRect(x + ((g.tick >> 2) % 12), RAIL + 22, 6, 1);
      c.strokeStyle = '#6b4a32'; c.lineWidth = 2; for (let x = x0; x < x1; x += 20) { c.beginPath(); c.moveTo(x, RAIL); c.lineTo(x + 10, H); c.moveTo(x + 20, RAIL); c.lineTo(x + 10, H); c.stroke(); }
    }
    const tr = props.get('post/tiles/track-straight'); if (tr) tile(c, tr.path, d, RAIL - 32 + 4);
  }

  function events(c, g, vt) {
    const cam = S.cam(g), zones = [];
    for (const e of g.ev) if (e.type === T.LIMIT) zones.push([e.x - cam, e.x + e.b - cam]);
    return zones;
  }
  function trackside(c, g, vt, layer) {        // layer 0: behind the train, 1: in front (animals off the track)
    const cam = S.cam(g);
    for (const e of g.ev) {
      if (!e.type) continue;
      const x = e.x - cam; if (x < -90 || x > W + 60) continue;
      if (layer === 0 && e.type === T.NET) {
        c.fillStyle = '#5a4030'; c.fillRect(x - 1, RAIL - 46, 3, 46); c.fillRect(x - 10, RAIL - 4, 20, 4);
        const col = ['#c95d50', '#407d9e', '#d7ac49', '#54865b'][e.a];
        c.strokeStyle = e.done === 1 ? '#9fe0a0' : col; c.lineWidth = 2; c.beginPath(); c.ellipse(x, RAIL - 52, 9, 4, 0, 0, 7); c.stroke();
        c.strokeStyle = 'rgba(255,255,255,.7)'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - 9, RAIL - 52); c.lineTo(x - 3, RAIL - 40); c.lineTo(x + 3, RAIL - 40); c.lineTo(x + 9, RAIL - 52); c.stroke();
        if (e.done === 1) prop(c, 'props/envelope-' + ['red', 'blue', 'yellow', 'green'][e.a], x - 16, RAIL - 62);
      } else if (layer === 0 && e.type === T.CRANE) {
        c.fillStyle = '#3a4a5a'; c.fillRect(x + 14, RAIL - 74, 3, 74); c.fillRect(x - 2, RAIL - 74, 19, 3);
        if (!e.done) { c.strokeStyle = '#3a4a5a'; c.lineWidth = 1; c.beginPath(); c.moveTo(x, RAIL - 71); c.lineTo(x, RAIL - 64); c.stroke(); c.fillStyle = '#c8a56a'; c.beginPath(); c.roundRect(x - 7, RAIL - 64, 14, 16, 4); c.fill(); c.fillStyle = '#8a6a3a'; c.fillRect(x - 5, RAIL - 58, 10, 2); }
      } else if (layer === 0 && e.type === T.LIMIT) {
        c.fillStyle = '#5a4030'; c.fillRect(x - 1, RAIL - 40, 2, 40);
        c.fillStyle = '#ffd34a'; c.beginPath(); c.moveTo(x, RAIL - 60); c.lineTo(x + 14, RAIL - 46); c.lineTo(x, RAIL - 32); c.lineTo(x - 14, RAIL - 46); c.fill();
        c.strokeStyle = '#3a2a1a'; c.lineWidth = 1; c.stroke(); text(c, String(S.kmh(e.a)), x, RAIL - 46, 10, '#2a1a0a', 'center', 900, null);
        const ex = e.x + e.b - cam; if (ex < W + 20) { c.fillStyle = '#5a4030'; c.fillRect(ex - 1, RAIL - 34, 2, 34); c.fillStyle = '#ffffff'; c.fillRect(ex - 7, RAIL - 40, 14, 9); c.fillStyle = '#54865b'; c.fillRect(ex - 5, RAIL - 37, 10, 3); }
      } else if (layer === 0 && e.type === T.SIGNAL) {
        const red = e.t < 0 || g.tick - e.t < e.a;
        c.fillStyle = '#2a3440'; c.fillRect(x - 1, RAIL - 62, 3, 62); c.beginPath(); c.roundRect(x - 6, RAIL - 76, 13, 24, 4); c.fill();
        c.fillStyle = red ? '#ff4a3a' : '#5a2a2a'; c.beginPath(); c.arc(x, RAIL - 70, 4, 0, 7); c.fill();
        c.fillStyle = red ? '#2a4a2a' : '#5aff7a'; c.beginPath(); c.arc(x, RAIL - 58, 4, 0, 7); c.fill();
        if (red) { c.fillStyle = 'rgba(255,74,58,.25)'; c.beginPath(); c.arc(x, RAIL - 70, 9, 0, 7); c.fill(); c.fillStyle = '#ff4a3a'; c.fillRect(x - 10, RAIL - 2, 20, 3); }
        else { c.fillStyle = 'rgba(90,255,122,.25)'; c.beginPath(); c.arc(x, RAIL - 58, 9, 0, 7); c.fill(); }
      } else if (e.type === T.ANIMAL) {
        const age = e.t >= 0 ? g.tick - e.t : 0, on = e.t < 0 || age < e.a;
        if ((layer === 0) !== on) continue;
        const y = RAIL + 4 + (on ? 0 : Math.min(26, age - e.a)), id = e.b ? 'props/cow' : 'props/sheep', w = e.b ? 48 : 40, h = e.b ? 34 : 28;
        prop(c, id, x - w / 2, y - h);
        if (on && x > K.FRONT_X && x - K.FRONT_X < 220) text(c, '!', x, y - h - 8, 12, '#ff6a4a', 'center', 900);
      }
    }
  }

  function train(c, g, phase, vt, st) {
    const x = K.LOCO_X, left = x - 48, top = RAIL - 81 + 4, wheelF = Math.floor(g.dist / 256 / 6) % 4;
    // carriage (mail van) behind
    const cv = props.get('post/props/carriage'); if (cv) c.drawImage(img.get(cv.path), left - 66, RAIL - 44 + 4);
    for (let k = 0; k < Math.min(g.bags, 5); k++) { const bx = left - 58 + k * 11, by = RAIL - 52; c.fillStyle = '#c8a56a'; c.beginPath(); c.roundRect(bx, by, 10, 12, 3); c.fill(); c.fillStyle = '#8a6a3a'; c.fillRect(bx + 2, by + 2, 6, 2); }
    // smoke: more and faster with speed
    const n = 2 + (g.v >> 8);
    for (let i = 0; i < n; i++) {
      const age = ((vt * (1 + g.v / 512)) + i * 23) % 60, sx = x + 22 - age * (0.4 + g.v / 900), sy = top + 10 - age * .55;
      c.fillStyle = `rgba(245,245,240,${.75 - age / 80})`; c.beginPath(); c.arc(sx, sy, 3 + age / 9, 0, 7); c.fill();
    }
    anim(c, 'post_props/wheel-cycle', wheelF, x, RAIL + 4);
    prop(c, 'props/locomotive-body', left, top);
    let action = 'idle', f = (vt >> 3) % 6;
    if (st.hurt > 0) { action = 'hit'; f = Math.min(5, (24 - st.hurt) >> 2); }
    else if (st.throwT > 0) { action = st.throwT > 12 ? 'throw' : 'delivered'; f = Math.min(5, (st.throwT > 12 ? 24 - st.throwT : 12 - st.throwT) >> 1); }
    if (phase === 'RESULT') { action = 'delivered'; f = 5; }
    anim(c, 'post_a/' + action, f, left + 25, top + 49);
    prop(c, 'props/cab-foreground', left, top);
    if (g.braking && g.v > 60) for (let i = 0; i < 4; i++) { c.fillStyle = i & 1 ? '#ffd34a' : '#ff8a3a'; c.fillRect(x - 30 + i * 18 + (vt * 3 + i * 7) % 6, RAIL + 2 - (vt + i) % 4, 2, 2); }
    if (g.v >= 720) { c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 1; for (let i = 0; i < 5; i++) { const y = 70 + hash(i * 7) * 120, x0 = W - ((vt * 9 + i * 71) % (W + 40)); c.beginPath(); c.moveTo(x0, y); c.lineTo(x0 + 26, y); c.stroke(); } }
  }

  // the throw window: a bracket at the mail door that lights up when a net or crane is inside it
  function doorCue(c, g, vt) {
    const cam = S.cam(g); let bd = 1e9, best = null;
    for (const e of g.ev) if ((e.type === T.NET || e.type === T.CRANE) && !e.done) { const d = Math.abs(e.x - cam - K.DOOR_X); if (d < bd) { bd = d; best = e; } }
    if (!best || bd > 70) return;
    const can = best.type === T.CRANE || g.bags > 0, inW = bd <= K.WINDOW, perfect = bd <= K.PERFECT;
    const col = !can ? 'rgba(255,255,255,.35)' : perfect ? '#ffd34a' : inW ? '#9fe0a0' : 'rgba(255,255,255,.75)';
    c.strokeStyle = col; c.lineWidth = 2; const y = RAIL - (best.type === T.CRANE ? 58 : 50);
    c.beginPath(); c.moveTo(K.DOOR_X - K.WINDOW, y - 8); c.lineTo(K.DOOR_X - K.WINDOW, y + 8); c.moveTo(K.DOOR_X + K.WINDOW, y - 8); c.lineTo(K.DOOR_X + K.WINDOW, y + 8); c.stroke();
    if (inW && can) text(c, best.type === T.CRANE ? '抓!' : '扔!', K.DOOR_X, y - 18, 11, col, 'center', 900);
    if (!can && bd < 40) text(c, '没邮袋了 · 去吊架抓', K.DOOR_X, y - 18, 9, '#ffe0a0', 'center', 800);
  }

  function hud(c, g, vt) {
    const pct = g.res / 1000, low = pct < .25;
    c.fillStyle = 'rgba(32,46,58,.7)'; c.fillRect(0, 0, W, 18);
    text(c, '时刻表', 6, 9, 10, '#ffffff', 'left', 700, null);
    c.fillStyle = 'rgba(255,255,255,.2)'; c.fillRect(42, 5, 70, 8);
    c.fillStyle = low ? (vt % 20 < 10 ? '#ff5a4a' : '#ffb0a0') : pct < .5 ? '#ffc34a' : '#7fd0e0'; c.fillRect(42, 5, 70 * pct, 8);
    for (let k = 0; k < K.BAGS_MAX; k++) { c.fillStyle = k < g.bags ? '#f2e3c6' : 'rgba(255,255,255,.18)'; c.fillRect(122 + k * 10, 5, 8, 8); if (k < g.bags) { c.fillStyle = '#c95d50'; c.fillRect(125 + k * 10, 8, 2, 2); } }
    const m = S.mult(g);
    text(c, `×${m}`, 196, 9, 11, m >= 3 ? '#ffd34a' : '#ffffff', 'center', 900, null);
    if (g.combo >= 2) text(c, `${g.combo}连`, 222, 9, 10, '#ffe9a0', 'center', 800, null);
    text(c, String(g.score), W - 6, 9, 14, '#ffffff', 'right', 900, null);
    // speedometer, bottom right: tiers and the active speed limit
    const cx = W - 36, cy = H - 8, r = 28, ang = v => Math.PI + Math.PI * v / K.VMAX;
    c.fillStyle = 'rgba(32,46,58,.75)'; c.beginPath(); c.arc(cx, cy, r + 5, Math.PI, 0); c.fill();
    [[0, 420, '#9ab0c0'], [420, 720, '#7fd0e0'], [720, K.VMAX, '#ffd34a']].forEach(([a, b, col]) => { c.strokeStyle = col; c.lineWidth = 4; c.beginPath(); c.arc(cx, cy, r, ang(a), ang(b)); c.stroke(); });
    if (g.zone) { c.strokeStyle = '#ff4a3a'; c.lineWidth = 3; const a = ang(g.zone); c.beginPath(); c.moveTo(cx + Math.cos(a) * (r - 7), cy + Math.sin(a) * (r - 7)); c.lineTo(cx + Math.cos(a) * (r + 5), cy + Math.sin(a) * (r + 5)); c.stroke(); }
    const a = ang(g.v); c.strokeStyle = g.over_t ? (vt & 4 ? '#ff4a3a' : '#ffffff') : '#ffffff'; c.lineWidth = 2; c.beginPath(); c.moveTo(cx, cy); c.lineTo(cx + Math.cos(a) * (r - 4), cy + Math.sin(a) * (r - 4)); c.stroke();
    text(c, String(S.kmh(g.v)), cx, cy - 10, 10, '#ffffff', 'center', 900, null);
    text(c, ['', '慢车', '快车', '特快'][S.tierOf(g.v)], cx - r - 10, cy - 4, 9, S.tierOf(g.v) === 3 ? '#ffd34a' : '#e0f0ff', 'right', 800);
  }

  const SECTION = [null, ['小镇', '站台密集，连着扔'], ['山区', '限速桥多，提前刹车'], ['牧场', '牛羊常过铁路'], ['夜车', '看信号灯'], ['下坡', '车会自己变快']];
  function fx(c, g) {
    const F = S.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      c.globalAlpha = Math.max(0, 1 - e.t / 60);
      if (e.kind === F.NET) text(c, '+' + e.val, e.x, e.y - e.t * .4, 12, '#ffd34a', 'center');
      else if (e.kind === F.PERFECT) { text(c, '正中网心!', e.x, e.y - 14 - e.t * .4, 11, '#ffffff', 'center'); text(c, '+' + e.val, e.x, e.y - e.t * .4, 13, '#ffd34a', 'center'); }
      else if (e.kind === F.CRANE) text(c, '抓到邮袋 +' + e.val, e.x, e.y - e.t * .4, 11, '#e9ffd0', 'center');
      else if (e.kind === F.WASTE) text(c, '扔早了/扔晚了', e.x, e.y - e.t * .3, 10, '#ffb08a', 'center');
      else if (e.kind === F.SKIP) text(c, '漏站', e.x, e.y, 11, '#ffb08a', 'center');
      else if (e.kind === F.RED) text(c, '冲红灯！', e.x, e.y, 13, '#ff6a4a', 'center');
      else if (e.kind === F.DERAIL) text(c, '超速，急停！', e.x, e.y - 20, 13, '#ff6a4a', 'center');
      else if (e.kind === F.ANIMAL) text(c, '撞到牛羊了', e.x, e.y, 12, '#ff8a6a', 'center');
      else if (e.kind === F.OVER) { c.globalAlpha = 1; text(c, `限速 ${e.val} · 刹车!`, e.x, e.y + 20, 11, '#ffd34a', 'center'); }
      else if (e.kind === F.NEAR) text(c, '好险', e.x, e.y - e.t * .3, 11, '#bfe6ff', 'center');
      else if (e.kind === F.TIER) text(c, ['', '', '快车 ×2', '特快 ×3'][e.val], e.x, e.y - e.t * .3, 12, '#ffd34a', 'center');
      else if (e.kind === F.SECTION && SECTION[e.val]) {
        const slide = e.t < 10 ? (10 - e.t) * 20 : 0; c.globalAlpha = Math.min(1, (70 - e.t) / 15);
        c.fillStyle = 'rgba(32,46,58,.7)'; c.fillRect(0, 30, W, 36);
        text(c, SECTION[e.val][0], W / 2 + slide, 41, 15, '#ffd34a', 'center', 900, null); text(c, SECTION[e.val][1], W / 2 + slide, 57, 10, '#ffffff', 'center', 700, null);
      }
      c.globalAlpha = 1;
    }
  }
  function nightShade(c, g) {
    if (g.section !== S.SEC.NIGHT) return;
    c.fillStyle = 'rgba(8,12,30,.55)'; c.fillRect(0, 0, W, H);
    const gr = c.createRadialGradient(K.FRONT_X + 50, RAIL - 20, 10, K.FRONT_X + 50, RAIL - 20, 120);
    gr.addColorStop(0, 'rgba(255,240,180,.35)'); gr.addColorStop(1, 'rgba(255,240,180,0)'); c.fillStyle = gr; c.fillRect(K.FRONT_X, RAIL - 120, 200, 160);
  }

  const st = { throwT: 0, hurt: 0, lastD: 0, lastC: 0, lastHits: 0, shake: 0 };
  const UIT = { name: '邮政快车', pitch: '不停车收发邮袋，快车分高，限速和红灯要刹住', keys: [['◀', '刹车'], ['●', '扔/抓邮袋'], ['▶', '加速']], th: [150, 500, 1200], ink: '32,46,58', go: '发车！', tip: '邮袋进了车门两边的括号就按 ●' };
  function title(c, vt, best) {
    const fake = S.start(9); fake.dist = vt * 600; fake.v = 600;
    backdrop(c, fake, vt); track(c, fake, []); train(c, fake, 'TITLE', vt, { throwT: 0, hurt: 0 });
    root.AdvV2UI.title(c, { ...UIT, best }, vt);
  }
  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    const hurts = g.reds + g.derails + g.animals + g.wasted + g.skipped;
    if (g.delivered + g.cranes !== st.lastD) { st.throwT = 24; st.lastD = g.delivered + g.cranes; }
    if (hurts !== st.lastHits) { st.hurt = 24; st.shake = 10; st.lastHits = hurts; }
    if (st.throwT > 0) st.throwT--; if (st.hurt > 0) st.hurt--;
    c.save(); if (st.shake > 0) { st.shake--; c.translate(st.shake & 1 ? 2 : -2, st.shake & 2 ? 1 : 0); }
    backdrop(c, g, vt); const zones = events(c, g, vt); track(c, g, zones); trackside(c, g, vt, 0); train(c, g, phase, vt, st); trackside(c, g, vt, 1); nightShade(c, g); doorCue(c, g, vt);
    c.restore();
    fx(c, g); hud(c, g, vt);
    const U = root.AdvV2UI;
    if (phase === 'READY') U.ready(c, UIT, info.countdown);
    if (phase === 'PAUSE') U.pause(c, UIT);
    if (phase === 'RESULT') U.result(c, UIT, { cause: '时刻表用完，今天的班次结束了', score: g.score, best: info.bestBefore ?? best, th: UIT.th,
      lines: [`送达 ${g.delivered} 袋 · 正中 ${g.perfects} · 抓袋 ${g.cranes} · 最长 ${g.best} 连`, `${g.meters} 米 · 冲红灯 ${g.reds} · 超速 ${g.derails} · 撞牛羊 ${g.animals}`] }, phaseT, vt);
  }
  root.AdvPostV2Draw = { load, draw };
})(window);
