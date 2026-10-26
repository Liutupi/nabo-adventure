// NIGHT V2 G1 renderer (browser only). Scenery is procedural placeholder; NABO uses the
// V1 night_a frames as a stand-in until the Grok motion pass (G2) replaces them.
(function (root) {
  'use strict';
  const N = root.AdvNight, K = N.K, W = K.W, H = K.H, GY = K.GROUND;
  const img = new Map(), clips = new Map();
  let dark = null, dctx = null;

  async function load(base = '../art/') {
    const inline = root.NIGHT_V2_SPRITES;
    const manifest = inline ? inline.manifest : await (await fetch(base + 'manifest.json')).json();
    const want = new Set();
    for (const c of manifest.animations) if (c.skin === 'travel' && ['walk_right', 'sad', 'cheer'].includes(c.name)) { clips.set(c.name, c); c.runtime_frames.forEach(p => want.add(p)); }
    await Promise.all([...want].map(async p => { const im = new Image(); im.src = inline ? inline.files[p] : base + p; await im.decode(); img.set(p, im); }));
    dark = document.createElement('canvas'); dark.width = W; dark.height = H; dctx = dark.getContext('2d');
  }

  const hash = n => { n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b); n ^= n >>> 13; n = Math.imul(n, 0xc2b2ae35); return ((n ^ n >>> 16) >>> 0) / 4294967296; };
  function sprite(c, name, frame, x, y, rot = 0, alpha = 1) {
    const clip = clips.get(name); if (!clip) return;
    const f = clip.runtime_frames[Math.max(0, Math.min(clip.runtime_frames.length - 1, frame))], im = img.get(f); if (!im) return;
    c.save(); c.globalAlpha = alpha; c.translate(Math.round(x), Math.round(y)); if (rot) c.rotate(rot);
    c.drawImage(im, -clip.runtime_anchor[0], -clip.runtime_anchor[1]); c.restore();
  }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = true) {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = 'rgba(6,8,24,.85)'; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  function glow(c, x, y, r, rgb, a) {
    const g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${rgb},${a})`); g.addColorStop(1, `rgba(${rgb},0)`);
    c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
  }

  // ---------------------------------------------------------------- scenery
  function scenery(c, cam, t) {
    const sky = c.createLinearGradient(0, 0, 0, GY); sky.addColorStop(0, '#070b24'); sky.addColorStop(.6, '#142152'); sky.addColorStop(1, '#22306a');
    c.fillStyle = sky; c.fillRect(0, 0, W, GY);
    for (let i = 0; i < 46; i++) {           // stars, very slow parallax
      const sx = ((hash(i) * 900 - cam * 0.04) % 900 + 900) % 900 - 290, sy = hash(i + 99) * 120;
      if (sx < 0 || sx > W) continue; c.globalAlpha = .35 + .65 * Math.abs(Math.sin(t * 0.03 + i)); c.fillStyle = '#dfe6ff'; c.fillRect(sx | 0, sy | 0, 1, 1);
    }
    c.globalAlpha = 1;
    glow(c, 262, 40, 46, '210,220,255', .22); c.fillStyle = '#eef0d8'; c.beginPath(); c.arc(262, 40, 15, 0, 7); c.fill();
    c.fillStyle = '#d5d7bd'; c.beginPath(); c.arc(257, 36, 3, 0, 7); c.arc(267, 45, 2, 0, 7); c.fill();
    // far hills
    c.fillStyle = '#18234d'; c.beginPath(); c.moveTo(0, GY);
    for (let x = 0; x <= W; x += 8) { const wx = x + cam * 0.18; c.lineTo(x, 132 + Math.sin(wx * 0.011) * 14 + Math.sin(wx * 0.027) * 6); }
    c.lineTo(W, GY); c.fill();
    // mid pines
    const layer = (par, spacing, base, hgt, col, seed) => {
      c.fillStyle = col; const off = cam * par, first = Math.floor(off / spacing) - 1;
      for (let i = first; i < first + W / spacing + 3; i++) {
        const x = i * spacing - off + hash(i * 31 + seed) * spacing * .6, h = hgt * (.7 + hash(i + seed) * .6);
        c.beginPath(); c.moveTo(x, base - h); c.lineTo(x - h * .32, base); c.lineTo(x + h * .32, base); c.fill();
        c.fillRect(x - 1.5, base - 2, 3, 6);
      }
    };
    layer(0.35, 38, 176, 62, '#121a3c', 7);
    layer(0.6, 52, 196, 84, '#0c1430', 13);
    // ground
    c.fillStyle = '#0b1a1c'; c.fillRect(0, GY - 4, W, H - GY + 4);
    c.fillStyle = '#123026'; c.fillRect(0, GY - 4, W, 3);
    const first = Math.floor(cam / 9) - 1;
    for (let i = first; i < first + W / 9 + 3; i++) {
      const x = i * 9 - cam, h = 3 + hash(i * 7) * 6; c.fillStyle = hash(i) < .5 ? '#1b4433' : '#163a2c';
      c.fillRect(x | 0, GY - 3 - h, 2, h); c.fillRect((x + 3) | 0, GY - 2 - h * .6, 1, h * .6);
    }
    // path pebbles
    c.fillStyle = '#1c2a2e';
    for (let i = Math.floor(cam / 23) - 1; i < cam / 23 + 16; i++) if (hash(i * 13) < .6) c.fillRect((i * 23 - cam + hash(i) * 12) | 0, GY + 6 + hash(i * 5) * 26, 3, 2);
  }

  function roots(c, g) {
    const cam = N.camX(g) / 256;
    for (const rt of g.roots) {
      if (!rt.state) continue;
      const x = rt.x - cam; if (x < -30 || x > W + 30) continue;
      c.strokeStyle = rt.state === 2 ? '#5a3a24' : '#7a4f2c'; c.lineWidth = 3; c.lineCap = 'round';
      c.beginPath(); c.moveTo(x - rt.w, GY + 1); c.quadraticCurveTo(x - rt.w * .3, GY - 9, x + 2, GY - 3); c.quadraticCurveTo(x + rt.w * .6, GY - 8, x + rt.w, GY + 2); c.stroke();
      c.strokeStyle = '#a06a3c'; c.lineWidth = 1; c.beginPath(); c.moveTo(x - rt.w * .6, GY - 3); c.lineTo(x - rt.w * .2, GY - 6); c.stroke();
    }
  }

  // ---------------------------------------------------------------- actors
  function nabo(c, g, phase, vt) {
    const x = g.screen / 256, y = GY + 1, wx = g.x / 256;
    let name = 'walk_right', f = Math.floor(wx / (g.gait === 2 ? 7 : 5)) % 8, rot = 0, bob = 0;
    if (phase === 'RESULT' || g.over) { name = 'sad'; f = Math.min(5, Math.floor(vt / 8)); }
    else if (g.stun > 0) { f = 3; rot = g.stunKind === 1 ? 0.9 * Math.min(1, (54 - g.stun) / 6) * Math.min(1, g.stun / 14) : Math.sin(vt * .8) * .15; }
    else { bob = g.gait === 2 ? -Math.abs(Math.sin(wx * .2)) * 2 : 0; if (g.gait === 2) rot = .1; if (g.gait === 0) rot = -.06; }
    c.fillStyle = 'rgba(0,0,0,.35)'; c.beginPath(); c.ellipse(x + 1, y + 1, 11, 3, 0, 0, 7); c.fill();
    sprite(c, name, f, x, y + bob, rot);
    // jar on a short pole: idle carry, or the swing arc that is the real catch window
    if (!(phase === 'RESULT' || g.over) && !(g.stun > 0 && g.stunKind === 1)) {
      const hx = x + 5, hy = y - 24 + bob;
      let ang = -0.5 + Math.sin(wx * .12) * .12;                       // carried, bobbing
      if (g.swing > 0) { const age = K.SWING - g.swing; ang = age < K.SWING_ON ? -0.5 - age * .45 : -1.9 + Math.min(1, (age - K.SWING_ON) / (K.SWING_OFF - K.SWING_ON)) * 2.9; }
      const L = g.swing > 0 ? 26 : 18, jx = hx + Math.cos(ang) * L, jy = hy + Math.sin(ang) * L;
      c.strokeStyle = '#8a6a48'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(hx, hy); c.lineTo(jx, jy); c.stroke();
      c.fillStyle = 'rgba(210,235,255,.55)'; c.strokeStyle = '#d8e8ff'; c.lineWidth = 1; c.beginPath(); c.roundRect(jx - 3.5, jy - 1, 7, 9, 2); c.fill(); c.stroke();
      c.fillStyle = `rgba(255,236,150,${.4 + g.light / 1600000})`; c.fillRect(jx - 2, jy + 3, 4, 4);
      jarAt = [jx, jy + 4];
    } else jarAt = [x, y - 14];
    // swing trail = the actual net reach
    if (g.swing > 0) {
      const age = K.SWING - g.swing, on = age >= K.SWING_ON && age <= K.SWING_OFF;
      const a1 = -1.9 + Math.min(1, Math.max(0, age - K.SWING_ON) / (K.SWING_OFF - K.SWING_ON)) * 2.9;
      if (age >= K.SWING_ON) { c.strokeStyle = on ? 'rgba(255,244,200,.8)' : 'rgba(255,244,200,.22)'; c.lineWidth = on ? 4 : 2;
        c.beginPath(); c.arc(x + 5, y - 24 + bob, 30, Math.max(-1.9, a1 - 1.4), a1); c.stroke(); }
    }
  }
  let jarAt = [0, 0];
  function jarPos() { return jarAt; }

  function flies(c, g, vt) {
    const cam = N.camX(g) / 256;
    g.flies.forEach((f, i) => {
      if (!f.type) return;
      const x = f.x / 256 - cam, y = N.flyY(f, g.tick); if (x < -10 || x > W + 10) return;
      const tw = .6 + .4 * Math.sin(vt * .25 + i * 1.7);
      if (f.type === 2) { glow(c, x, y, 16, '255,200,60', .55 * tw + .25); c.fillStyle = '#fff3b0'; c.fillRect(x - 2, y - 2, 4, 4); c.fillStyle = '#ffd34a'; c.fillRect(x - 1, y - 3, 2, 6); }
      else { glow(c, x, y, 10, '190,255,120', .55 * tw); c.fillStyle = '#efffc8'; c.fillRect(x - 1, y - 1, 3, 3); }
    });
    for (const m of g.moths) {
      if (!m.rr) continue;
      const x = m.x / 256 - cam, y = m.y / 256, flap = Math.sin(vt * .9 + m.a / 2000) > 0;
      c.fillStyle = '#b8b2c8'; c.fillRect(x - 1, y - 1, 2, 4);
      c.fillStyle = '#8c86a3'; if (flap) { c.fillRect(x - 5, y - 3, 4, 3); c.fillRect(x + 1, y - 3, 4, 3); } else { c.fillRect(x - 4, y, 3, 3); c.fillRect(x + 1, y, 3, 3); }
    }
  }

  function owls(c, g, vt) {
    const cam = N.camX(g) / 256;
    for (const o of g.owls) {
      if (!o.live) continue;
      const tx = o.tx / 256 - cam;
      if (o.t > 0) {                  // ground warning that sharpens as the dive nears
        const k = 1 - o.t / K.OWL_WARN, pulse = (Math.sin(vt * (.25 + k * .5)) + 1) / 2;
        c.strokeStyle = `rgba(255,${120 - k * 80},70,${.35 + .5 * pulse})`; c.lineWidth = 2;
        c.beginPath(); c.ellipse(tx, GY + 3, 24 - k * 8, 5 - k * 1.5, 0, 0, 7); c.stroke();
        if (o.t < 70) text(c, '!', tx, GY - 18 - pulse * 3, 16, '#ff8a5a', 'center');
      }
      const tt = -o.t;                 // owl silhouette: glide in from top right, swoop, leave
      let ox, oy;
      if (o.t > 30) { if (o.t > 60) continue; const k = (60 - o.t) / 30; ox = tx + 160 - k * 100; oy = -20 + k * 70; }
      else if (o.t > 0) { const k = (30 - o.t) / 30; ox = tx + 60 - k * 60; oy = 50 + k * k * (GY - 72); }
      else { ox = tx - tt * 4; oy = GY - 22 - tt * 4; }
      const wing = Math.sin(vt * .6) * 6;
      c.fillStyle = '#05060f'; c.beginPath(); c.ellipse(ox, oy, 9, 11, 0, 0, 7); c.fill();
      c.beginPath(); c.moveTo(ox - 6, oy - 2); c.lineTo(ox - 24, oy - 8 + wing); c.lineTo(ox - 8, oy + 6); c.fill();
      c.beginPath(); c.moveTo(ox + 6, oy - 2); c.lineTo(ox + 24, oy - 8 + wing); c.lineTo(ox + 8, oy + 6); c.fill();
      c.fillStyle = '#ffcf4a'; c.fillRect(ox - 5, oy - 5, 3, 3); c.fillRect(ox + 2, oy - 5, 3, 3);
    }
  }

  function darkness(c, g, vt) {
    const [jx, jy] = jarPos(g), R = N.radius(g);
    dctx.globalCompositeOperation = 'source-over'; dctx.clearRect(0, 0, W, H);
    dctx.fillStyle = 'rgba(3,5,16,.9)'; dctx.fillRect(0, 0, W, H);
    dctx.globalCompositeOperation = 'destination-out';
    const flick = 1 + Math.sin(vt * .21) * .03 + Math.sin(vt * .53) * .02;
    const cut = (x, y, r, a) => { const gr = dctx.createRadialGradient(x, y, r * .25, x, y, r); gr.addColorStop(0, `rgba(0,0,0,${a})`); gr.addColorStop(1, 'rgba(0,0,0,0)'); dctx.fillStyle = gr; dctx.fillRect(x - r, y - r, r * 2, r * 2); };
    cut(jx, jy, R * flick, 1);
    const cam = N.camX(g) / 256;
    for (const f of g.flies) if (f.type) cut(f.x / 256 - cam, N.flyY(f, g.tick), f.type === 2 ? 24 : 13, .55);
    cut(262, 40, 70, .45);           // moonlit sky stays readable
    c.drawImage(dark, 0, 0);
    // warm jar glow on top
    glow(c, jx, jy, 30 + g.light * .00003, '255,214,110', .18 + g.light / 4000000);
    c.fillStyle = 'rgba(255,236,160,.9)'; c.fillRect(jx - 2, jy - 3, 5, 6);
  }

  // ---------------------------------------------------------------- HUD
  function hud(c, g, vt) {
    const low = g.light < 200000, pct = g.light / K.LIGHT_MAX;
    c.fillStyle = 'rgba(6,8,24,.55)'; c.beginPath(); c.roundRect(6, 6, 108, 28, 8); c.fill();
    // jar icon
    c.strokeStyle = '#cfe1ff'; c.lineWidth = 1.5; c.beginPath(); c.roundRect(13, 11, 12, 17, 3); c.stroke(); c.fillStyle = '#cfe1ff'; c.fillRect(14, 9, 10, 2);
    const col = pct > .45 ? '#ffe27a' : pct > .2 ? '#ffae45' : '#ff6a4a';
    c.fillStyle = col; c.globalAlpha = low && vt % 20 < 10 ? .35 : 1; c.fillRect(15, 27 - 14 * pct, 8, 14 * pct); c.globalAlpha = 1;
    c.fillStyle = 'rgba(255,255,255,.15)'; c.fillRect(31, 13, 76, 7); c.fillStyle = col; c.fillRect(31, 13, 76 * pct, 7);
    // burst meter
    const need = N.meterFull(g), m = Math.min(1, g.meter / need), full = g.meter >= need;
    c.fillStyle = 'rgba(255,255,255,.12)'; c.fillRect(31, 23, 76, 5);
    c.fillStyle = full ? (vt % 16 < 8 ? '#ffffff' : '#9fe8ff') : '#7fc8ff'; c.fillRect(31, 23, 76 * m, 5);
    if (full) text(c, '双击 ● 放光', 60, 44, 10, '#bff0ff', 'center');
    // score + combo
    text(c, String(g.score), W - 10, 20, 22, '#fff4c8', 'right');
    const mu = N.mult(g);
    if (g.combo >= 2) text(c, `${g.combo}连` + (mu > 1 ? ` ×${mu}` : ''), W - 10, 40, 11, mu > 1 ? '#ffd34a' : '#d6e2ff', 'right');
  }

  const EVENT_TEXT = [null, ['萤火虫潮!', '快跑起来多抓'], ['猫头鹰出没', '看地上的光圈，变速躲开'], ['起风了', '虫群往回飘']];
  function fx(c, g) {
    const cam = N.camX(g) / 256, F = N.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      const a = Math.max(0, 1 - e.t / 60), x = e.x - cam; c.globalAlpha = a;
      if (e.kind === F.FLY || e.kind === F.GOLD) text(c, '+' + e.val, x, e.y - e.t * .5, e.kind === F.GOLD ? 12 : 9, e.kind === F.GOLD ? '#ffd34a' : '#e8ffc0', 'center');
      else if (e.kind === F.MULTI) text(c, `一网 ${e.val} 只!`, x, e.y - e.t * .4, 13, '#ffe27a', 'center');
      else if (e.kind === F.MOTH) text(c, '飞蛾! 罐子暗了', x, e.y - 14 - e.t * .3, 10, '#c9b8ff', 'center');
      else if (e.kind === F.TRIP) text(c, '绊倒!', x, e.y - e.t * .3, 13, '#ff9a6a', 'center');
      else if (e.kind === F.OWL) text(c, '被猫头鹰吓到!', x, e.y, 12, '#ff9a6a', 'center');
      else if (e.kind === F.NEAR) text(c, '好险!', x, e.y - e.t * .3, 12, '#9fe8ff', 'center');
      else if (e.kind === F.BURST) { c.globalAlpha = a * .7; c.fillStyle = '#fff8d8'; c.fillRect(0, 0, W, H); }
      else if (e.kind === F.EVENT) {
        const [name, sub] = EVENT_TEXT[e.val], slide = e.t < 10 ? (10 - e.t) * 20 : 0;
        c.globalAlpha = Math.min(1, (70 - e.t) / 15); c.fillStyle = 'rgba(6,8,24,.6)'; c.fillRect(0, 78, W, 40);
        text(c, name, W / 2 + slide, 92, 17, '#ffe27a', 'center'); text(c, sub, W / 2 + slide, 110, 10, '#d6e2ff', 'center', 700);
      }
      c.globalAlpha = 1;
    }
  }

  // ---------------------------------------------------------------- screens
  function title(c, vt, best) {
    scenery(c, vt * .6, vt);
    for (let i = 0; i < 14; i++) { const x = (i * 47 + vt * (.3 + hash(i) * .4)) % (W + 20) - 10, y = 70 + hash(i * 3) * 90 + Math.sin(vt * .03 + i) * 12; glow(c, x, y, 10, '190,255,120', .5 + .3 * Math.sin(vt * .2 + i)); c.fillStyle = '#efffc8'; c.fillRect(x - 1, y - 1, 3, 3); }
    c.fillStyle = 'rgba(3,5,16,.35)'; c.fillRect(0, 0, W, H);
    sprite(c, 'walk_right', Math.floor(vt / 5) % 8, 70, GY + 1);
    glow(c, 82, GY - 20, 50, '255,214,110', .3);
    text(c, '萤火虫之夜', W / 2 + 30, 66, 28, '#fff1b8', 'center');
    text(c, 'V2 试玩原型', W / 2 + 30, 92, 10, '#9fb4e8', 'center', 700);
    const keys = [['◀', '慢走 / 刹车'], ['●', '挥罐 · 双击放光'], ['▶', '小跑']];
    keys.forEach(([k, s], i) => { const y = 126 + i * 18; c.fillStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.roundRect(150, y - 8, 18, 16, 4); c.fill(); text(c, k, 159, y, 10, '#fff', 'center', 900, false); text(c, s, 176, y, 10, '#d6e2ff', 'left', 700); });
    if (best) text(c, '最佳 ' + best, W - 10, 18, 11, '#ffd34a', 'right');
    if (vt % 60 < 42) text(c, '按 ● 开始', W / 2 + 30, 186, 13, '#ffffff', 'center');
  }

  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    scenery(c, N.camX(g) / 256, vt); roots(c, g); owls(c, g, vt); nabo(c, g, phase, phaseT);
    darkness(c, g, vt); flies(c, g, vt); fx(c, g); hud(c, g, vt);
    if (phase === 'READY') { const n = Math.ceil(info.countdown / 60); text(c, n > 0 ? String(n) : '走!', W / 2, 100, 34, '#fff1b8', 'center'); text(c, '罐子的光会慢慢变暗，抓萤火虫补光', W / 2, 134, 11, '#d6e2ff', 'center', 700); }
    if (phase === 'PAUSE') {
      c.fillStyle = 'rgba(3,5,16,.72)'; c.fillRect(0, 0, W, H); text(c, '暂停', W / 2, 70, 24, '#fff1b8', 'center');
      [['●', '继续'], ['◀', '重来'], ['▶▶', '双击回地图']].forEach(([k, s], i) => text(c, `${k}  ${s}`, W / 2, 112 + i * 22, 12, '#d6e2ff', 'center', 700));
    }
    if (phase === 'RESULT') {
      const k = Math.min(1, phaseT / 30); c.fillStyle = `rgba(3,5,16,${.75 * k})`; c.fillRect(0, 0, W, H);
      if (phaseT > 20) {
        const cause = ['罐子的光慢慢熄了', '一路狂奔，光晃没了', '挥空太多，光洒光了', '飞蛾扑灭了罐子', '绊了一跤，光灭了', '被猫头鹰吓灭了光'][g.lastLoss] || '';
        text(c, cause, W / 2, 40, 12, '#9fb4e8', 'center', 700);
        text(c, String(g.score), W / 2, 82, 40, '#fff1b8', 'center');
        if (g.score >= best && g.score > 0) text(c, '新纪录!', W / 2 + 70, 66, 12, '#ffd34a', 'center');
        text(c, `抓到 ${g.caught} 只 · 最长 ${g.maxCombo} 连 · 放光 ${g.bursts} 次 · ${Math.floor(g.tick / 60)} 秒`, W / 2, 120, 10, '#d6e2ff', 'center', 700);
        if (phaseT > 50 && vt % 60 < 42) text(c, '● 再来一局', W / 2, 200, 13, '#ffffff', 'center');
      }
    }
  }

  // Collection prototype (index.html) entry: same signature as the V1 renderer.
  let priorPhase = -1, priorSeed = -1, phaseStarted = 0;
  function session(c, m, A, ms) {
    const s = m.session; if (s.phase !== priorPhase || s.seed !== priorSeed) { priorPhase = s.phase; priorSeed = s.seed; phaseStarted = ms; }
    const phase = Object.keys(A.PHASE).find(k => A.PHASE[k] === s.phase), vt = Math.floor(ms * 60 / 1000), pt = Math.floor((ms - phaseStarted) * 60 / 1000);
    draw(c, s.game || N.start(0), phase === 'END' ? 'PLAY' : phase, vt, pt, m.best[4], { countdown: s.t });
  }
  root.AdvNightDraw = { load, draw, session };
})(window);
