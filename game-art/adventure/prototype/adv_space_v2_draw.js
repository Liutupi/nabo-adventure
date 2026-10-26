// SPACE V2 G1 renderer (browser). Lander layers, crew frames, flag, can and asteroid come from the existing
// space art; the moonscape, pads, flames and HUD are procedural. No sprite rotation or mirroring.
(function (root) {
  'use strict';
  const S = root.AdvSpaceV2, K = S.K, W = K.W, H = K.H;
  const img = new Map(), clips = new Map(), props = new Map();
  async function load(base = '../art/') {
    const inline = root.SPACE_V2_SPRITES;
    const manifest = inline ? inline.manifest : await (await fetch(base + 'space-manifest.json')).json();
    const want = new Set();
    for (const c of manifest.animations) if (c.skin === 'space_a') { clips.set(c.name, c); c.runtime_frames.forEach(p => want.add(p)); }
    for (const a of manifest.assets) { props.set(a.id, a); want.add(a.path); }
    await Promise.all([...want].map(async p => { const im = new Image(); im.src = inline ? inline.files[p] : base + p; await im.decode(); img.set(p, im); }));
  }
  const hash = n => { n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b); n ^= n >>> 13; n = Math.imul(n, 0xc2b2ae35); return ((n ^ n >>> 16) >>> 0) / 4294967296; };
  function crew(c, name, f, x, y) {
    const clip = clips.get(name); if (!clip) return;
    const im = img.get(clip.runtime_frames[Math.max(0, Math.min(clip.runtime_frames.length - 1, f))]);
    if (im) c.drawImage(im, Math.round(x - clip.runtime_anchor[0]), Math.round(y - clip.runtime_anchor[1]));
  }
  function prop(c, id, x, y) { const a = props.get(id), im = a && img.get(a.path); if (!im) return; const [ax, ay] = a.anchor || [0, 0]; c.drawImage(im, Math.round(x - ax), Math.round(y - ay)); }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(5,8,24,.85)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  const PADC = [null, '#7fe0c0', '#ffd34a', '#ff8a5a'];

  function sky(c, cam, vt) {
    const gr = c.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#05071a'); gr.addColorStop(1, '#151a3a'); c.fillStyle = gr; c.fillRect(0, 0, W, H);
    for (let i = 0; i < 60; i++) { const x = ((hash(i) * 1200 - cam * 0.08) % 1200 + 1200) % 1200 - 440; if (x < 0 || x > W) continue; c.globalAlpha = .4 + .6 * hash(i * 7 + (vt >> 5)); c.fillStyle = '#e8ecff'; c.fillRect(x | 0, (hash(i + 50) * 150) | 0, 1, 1); }
    c.globalAlpha = 1;
    const ex = 262 - (cam * 0.02) % 40; c.fillStyle = '#2d6fd0'; c.beginPath(); c.arc(ex, 40, 16, 0, 7); c.fill();
    c.fillStyle = '#5fbf7a'; c.beginPath(); c.arc(ex - 5, 36, 6, 0, 7); c.arc(ex + 6, 46, 4, 0, 7); c.fill();
  }
  function moon(c, g, cam) {
    c.fillStyle = '#7d8598'; c.beginPath(); c.moveTo(0, H);
    for (let x = 0; x <= W; x += 4) c.lineTo(x, S.ground(g.seed, cam + x)); c.lineTo(W, H); c.fill();
    c.strokeStyle = '#a9b0c2'; c.lineWidth = 2; c.beginPath();
    for (let x = 0; x <= W; x += 4) { const y = S.ground(g.seed, cam + x); x ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke();
    for (let i = Math.floor(cam / 37) - 1; i < (cam + W) / 37 + 1; i++) {         // craters and pebbles
      const h = hash(i * 17 + g.seed), x = i * 37 - cam + h * 20, y = S.ground(g.seed, Math.round(x + cam)) + 8 + hash(i * 5) * 20;
      c.fillStyle = 'rgba(70,76,94,.8)'; c.beginPath(); c.ellipse(x, y, 4 + h * 6, 2 + h * 2, 0, 0, 7); c.fill();
    }
  }
  function pads(c, g, cam, vt) {
    const c0 = Math.floor(cam / K.CHUNK) - 1;
    for (let ch = c0; ch <= c0 + 3; ch++) {
      const p = S.pad(g.seed, ch); if (!p) continue;
      const w = S.PAD[p.type].w, x = p.x - cam; if (x < -80 || x > W + 80) continue;
      c.fillStyle = '#3a4258'; c.fillRect(x - w / 2, p.y, w, 7); c.fillStyle = '#566079'; c.fillRect(x - w / 2, p.y, w, 2);
      c.fillStyle = PADC[p.type]; c.globalAlpha = .55 + .45 * Math.abs(Math.sin(vt * .08 + ch)); c.fillRect(x - w / 2 + 4, p.y + 3, w - 8, 2); c.globalAlpha = 1;
      c.fillStyle = '#ffe9a0'; c.fillRect(x - w / 2, p.y - 3, 3, 3); c.fillRect(x + w / 2 - 3, p.y - 3, 3, 3);
      if (ch <= g.bestChunk && !(ch === g.padChunk && g.phase === S.PH.LANDED && g.phaseT < 40)) prop(c, 'space/props/flag', x + w / 2 - 10, p.y);
      else if (ch > g.bestChunk) text(c, '×' + S.PAD[p.type].mult, x, p.y + 16, 12, PADC[p.type], 'center');
    }
  }
  function cans(c, g, cam, vt) {
    const c0 = Math.floor(cam / K.CHUNK) - 1;
    for (let ch = c0; ch <= c0 + 3; ch++) {
      const f = S.can(g.seed, ch); if (!f) continue;
      const bit = ch - g.canBase; if (bit >= 0 && bit <= 30 && (g.canMask >>> bit) & 1) continue;
      const x = f.x - cam, y = f.y + Math.round(Math.sin(vt * .07 + ch) * 3); if (x < -20 || x > W + 20) continue;
      c.fillStyle = 'rgba(120,230,255,.18)'; c.beginPath(); c.arc(x, y - 12, 14, 0, 7); c.fill(); prop(c, 'space/props/fuel-can', x, y);
    }
  }
  function rocks(c, g, cam, vt) {
    for (const r of g.rocks) {
      if (!r.live) continue;
      const x = (r.x >> 8) - cam, y = r.y >> 8;
      if (y < 8) { text(c, '!', x, 14, 16, '#ff6a4a', 'center'); continue; }
      c.strokeStyle = 'rgba(255,170,90,.6)'; c.lineWidth = 3; c.beginPath(); c.moveTo(x, y - 14); c.lineTo(x - r.vx / 12, y - 14 - r.vy / 12); c.stroke();
      prop(c, 'space/props/asteroid', x, y);
    }
  }
  function lander(c, g, cam, phase, vt) {
    let x = (g.x >> 8) - cam, y = g.y >> 8, name = g.flame ? 'jet' : 'cabin_idle', f = Math.floor(vt / 6) % (g.flame ? 4 : 6), outside = false;
    if (g.phase === S.PH.CRASHED) { x += (g.phaseT >> 1) % 2 ? 2 : -2; name = 'hard_land'; f = Math.min(7, Math.floor((K.CRASH_T - g.phaseT) * 8 / K.CRASH_T)); }
    else if (g.phase === S.PH.LANDED && g.phaseT < K.TAKEOFF_T && g.padChunk === g.bestChunk && g.hops) {
      if (g.phaseT < 22) { name = 'land'; f = Math.floor(g.phaseT / 4); } else { outside = true; name = 'plant_flag'; f = Math.floor((g.phaseT - 22) / 6); }
    }
    if (g.flame) { c.fillStyle = 'rgba(255,160,60,.55)'; c.beginPath(); c.arc(x, y + 8, 10 + (vt % 3), 0, 7); c.fill(); c.fillStyle = '#ffe6a0'; c.beginPath(); c.moveTo(x - 6, y + 2); c.lineTo(x + 6, y + 2); c.lineTo(x, y + 10 + g.flame); c.fill(); }
    if (g.sideR) { c.fillStyle = 'rgba(160,220,255,.8)'; c.beginPath(); c.arc(x - 46, y - 27, 6 + (vt % 2), 0, 7); c.fill(); }
    if (g.sideL) { c.fillStyle = 'rgba(160,220,255,.8)'; c.beginPath(); c.arc(x + 45, y - 27, 6 + (vt % 2), 0, 7); c.fill(); }
    if (g.invuln && (vt >> 2) % 2) c.globalAlpha = .5;
    prop(c, 'space/lander/back', x, y); if (!outside) crew(c, name, f, x, y - 22); prop(c, 'space/lander/front', x, y);
    c.globalAlpha = 1;
    if (outside) crew(c, name, f, x + 60, y);
  }
  function dark(c, g, cam) {
    const x = (g.x >> 8) - cam, y = (g.y >> 8) - 40, gr = c.createRadialGradient(x, y, 40, x, y, 150);
    gr.addColorStop(0, 'rgba(0,0,8,0)'); gr.addColorStop(1, 'rgba(0,0,8,.88)'); c.fillStyle = gr; c.fillRect(0, 0, W, H);
  }
  function hud(c, g, vt) {
    const Y = H - 24, pct = g.fuel / K.FUEL_MAX, low = pct < .25;
    c.fillStyle = 'rgba(8,12,32,.82)'; c.fillRect(0, Y, W, 24);
    text(c, '燃料', 8, Y + 12, 10, '#ffffff', 'left', 700, null);
    c.fillStyle = 'rgba(255,255,255,.15)'; c.fillRect(34, Y + 8, 90, 8);
    c.fillStyle = low ? (vt % 20 < 10 ? '#ff6a4a' : '#ffb2a0') : pct < .5 ? '#ffc34a' : '#7fe0c0'; c.fillRect(34, Y + 8, 90 * pct, 8);
    const m = S.streakMult(g); text(c, `${g.hops} 站` + (m > 1 ? ` ×${m}` : ''), 134, Y + 12, 11, m > 1 ? '#ffd34a' : '#ffffff', 'left', 900, null);
    const nxt = S.pad(g.seed, g.bestChunk + 1), d = Math.max(0, Math.round((nxt.x - (g.x >> 8)) / 10));
    text(c, `下一站 ×${S.PAD[nxt.type].mult} ${d}m`, 246, Y + 12, 10, PADC[nxt.type], 'right', 700, null);
    text(c, String(g.score), W - 8, Y + 12, 16, '#ffffff', 'right', 900, null);
    const sx = nxt.x - S.camX(g); if (sx > W - 6) text(c, '▶', W - 10, nxt.y - 20, 14, PADC[nxt.type], 'center');
  }
  const EVENT = [null, ['流星雨', '看顶上的感叹号，躲开陨石'], ['太阳风', '一直往右推'], ['低重力', '下落变慢，喷气更省'], ['月夜', '只看得清身边']];
  function fx(c, g, cam) {
    const F = S.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      const a = Math.max(0, 1 - e.t / 60), x = e.x - cam; c.globalAlpha = a;
      if (e.kind === F.LAND) text(c, '着陆 +' + e.val, x, e.y - e.t * .3, 14, '#ffffff', 'center');
      else if (e.kind === F.PERFECT) text(c, '完美着陆 +' + e.val, x, e.y - e.t * .3, 14, '#ffd34a', 'center');
      else if (e.kind === F.CRASH) text(c, ['', '太快了，硬着陆', '没落在着陆台', '被陨石砸中'][e.val] || '', x, e.y - 110, 13, '#ff8a6a', 'center');
      else if (e.kind === F.CAN) text(c, '燃料 +', x, e.y - 30 - e.t * .3, 11, '#7fe0ff', 'center');
      else if (e.kind === F.OLD_PAD) text(c, '这一站来过了', x, e.y, 11, '#c8d2f0', 'center');
      else if (e.kind === F.EVENT && EVENT[e.val]) {
        const slide = e.t < 10 ? (10 - e.t) * 20 : 0; c.globalAlpha = Math.min(1, (70 - e.t) / 15);
        c.fillStyle = 'rgba(8,12,32,.7)'; c.fillRect(0, 54, W, 40);
        text(c, EVENT[e.val][0], W / 2 + slide, 67, 16, '#ffd34a', 'center', 900, null); text(c, EVENT[e.val][1], W / 2 + slide, 85, 10, '#ffffff', 'center', 700, null);
      }
      c.globalAlpha = 1;
    }
  }
  function title(c, vt, best) {
    const g = S.start(1); g.x = (160 + vt) << 8; g.y = (178 + Math.round(Math.sin(vt * .05) * 8)) << 8; g.phase = S.PH.FLY; g.flame = vt % 40 < 10 ? 6 : 0;
    const cam = S.camX(g); sky(c, cam, vt); moon(c, g, cam); pads(c, g, cam, vt); lander(c, g, cam, 'TITLE', vt);
    c.fillStyle = 'rgba(8,12,32,.6)'; c.fillRect(0, 0, W, 86);
    text(c, '月面跳跳', W / 2, 24, 24, '#ffffff', 'center');
    text(c, '◀ 左喷   ● 点按主引擎（一下一下地喷）   ▶ 右喷', W / 2, 52, 10, '#c8d2f0', 'center', 700, null);
    text(c, '一站一站跳过月面，平稳落在着陆台上加油得分', W / 2, 70, 10, '#c8d2f0', 'center', 700, null);
    if (best) text(c, '最佳 ' + best, W - 8, 100, 11, '#ffd34a', 'right');
    if (vt % 60 < 42) text(c, '按 ● 开始', W / 2, 106, 13, '#ffffff', 'center');
  }
  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    const cam = S.camX(g);
    sky(c, cam, vt); moon(c, g, cam); pads(c, g, cam, vt); cans(c, g, cam, vt); lander(c, g, cam, phase, vt); rocks(c, g, cam, vt);
    if (g.event === S.EV.DARK) dark(c, g, cam);
    if (g.event === S.EV.WIND) for (let i = 0; i < 10; i++) { const x = (hash(i) * W + vt * 3) % W, y = hash(i + 9) * 180; c.fillStyle = 'rgba(255,220,150,.35)'; c.fillRect(x, y, 10, 1); }
    fx(c, g, cam); hud(c, g, vt);
    if (phase === 'READY') { const n = Math.ceil(info.countdown / 60); text(c, n > 0 ? String(n) : '出发！', W / 2, 60, 30, '#ffffff', 'center'); text(c, '点按 ● 起飞，飞到下一个着陆台', W / 2, 90, 11, '#ffffff', 'center', 700); }
    if (phase === 'PAUSE') {
      c.fillStyle = 'rgba(8,12,32,.78)'; c.fillRect(0, 0, W, H); text(c, '暂停', W / 2, 70, 24, '#ffffff', 'center');
      [['●', '继续'], ['◀', '重来'], ['▶▶', '双击回地图']].forEach(([k, s], i) => text(c, `${k}  ${s}`, W / 2, 112 + i * 22, 12, '#c8d2f0', 'center', 700, null));
    }
    if (phase === 'RESULT') {
      const k = Math.min(1, phaseT / 30); c.fillStyle = `rgba(8,12,32,${.78 * k})`; c.fillRect(0, 0, W, H);
      if (phaseT > 20) {
        text(c, '燃料用完了', W / 2, 36, 12, '#c8d2f0', 'center', 700, null);
        text(c, String(g.score), W / 2, 80, 40, '#ffffff', 'center');
        if (g.score >= best && g.score > 0) text(c, '新纪录!', W / 2 + 80, 62, 12, '#ffd34a', 'center');
        text(c, `${g.hops} 站 · 完美 ${g.perfect} · 燃料罐 ${g.cans} · 摔 ${g.crashes} 次`, W / 2, 120, 10, '#c8d2f0', 'center', 700, null);
        if (phaseT > 50 && vt % 60 < 42) text(c, '● 再来一局', W / 2, 200, 13, '#ffffff', 'center');
      }
    }
  }
  root.AdvSpaceV2Draw = { load, draw };
})(window);
