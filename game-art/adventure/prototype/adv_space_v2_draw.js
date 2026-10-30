// SPACE V2「火箭登月」renderer (browser, G1). Painted layers come from tools/paint_space_v2.py
// (art/space-v2/*), NABO's cockpit and landing frames and the lander from the existing space art.
// No sprite rotation; the only mirrored images are props (plane, comet), never NABO.
(function (root) {
  'use strict';
  const S = root.AdvSpaceV2, K = S.K, T = S.T, W = K.W, H = K.H, RY = K.RY;
  const img = new Map(), art = new Map(), clips = new Map();
  async function load(base = '../art/') {
    const inline = root.SPACE_V2_SPRITES;
    const painted = inline ? inline.painted : await (await fetch(base + 'space-v2-manifest.json')).json();
    const space = inline ? inline.space : await (await fetch(base + 'space-manifest.json')).json();
    const want = new Set();
    for (const a of painted.assets) { art.set(a.id, a); want.add(a.path); }
    for (const a of space.assets) { art.set(a.id, a); want.add(a.path); }
    for (const c of space.animations) if (c.skin === 'space_a') { clips.set(c.name, c); c.runtime_frames.forEach(p => want.add(p)); }
    await Promise.all([...want].map(async p => { const im = new Image(); im.src = inline ? inline.files[p] : base + p; await im.decode(); img.set(p, im); }));
  }
  const hash = n => { n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b); n ^= n >>> 13; n = Math.imul(n, 0xc2b2ae35); return ((n ^ n >>> 16) >>> 0) / 4294967296; };
  function put(c, id, x, y) { const a = art.get(id), im = a && img.get(a.path); if (!im) return; const [ax, ay] = a.anchor || [0, 0]; c.drawImage(im, Math.round(x - ax), Math.round(y - ay)); }
  function crew(c, name, f, x, y) {
    const clip = clips.get(name); if (!clip) return;
    const im = img.get(clip.runtime_frames[Math.max(0, Math.min(clip.runtime_frames.length - 1, f))]);
    if (im) c.drawImage(im, Math.round(x - clip.runtime_anchor[0]), Math.round(y - clip.runtime_anchor[1]));
  }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(6,10,30,.85)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  const mixc = (a, b, t) => { const p = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16)); const A = p(a), B = p(b); return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',')})`; };
  // sky keyed to altitude: [alt, top, horizon]
  const SKY = [[0, '#1e2a5c', '#f2a66e'], [900, '#2f63b8', '#d9b9a0'], [1800, '#3a80d4', '#a9d6f5'], [4000, '#2a5cb8', '#79b4ec'],
    [6200, '#13205a', '#3c56a8'], [8200, '#070a26', '#1a2050'], [99999, '#04051a', '#0b0e2a']];
  function skyAt(alt) {
    for (let i = 0; i < SKY.length - 1; i++) if (alt < SKY[i + 1][0]) { const t = (alt - SKY[i][0]) / (SKY[i + 1][0] - SKY[i][0]); return [mixc(SKY[i][1], SKY[i + 1][1], t), mixc(SKY[i][2], SKY[i + 1][2], t)]; }
    return [SKY.at(-1)[1], SKY.at(-1)[2]];
  }

  // ---------------------------------------------------------------- backdrop by altitude
  function backdrop(c, alt, vt) {
    const [top, low] = skyAt(alt), gr = c.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, top); gr.addColorStop(1, low); c.fillStyle = gr; c.fillRect(0, 0, W, H);
    const starA = Math.min(1, Math.max(0, (alt - 4800) / 3000));
    if (starA > 0) for (let i = 0; i < 90; i++) {
      const x = hash(i) * W, y = ((hash(i + 300) * 400 + alt * 0.02) % 400) - 80; if (y < 0 || y > H) continue;
      c.globalAlpha = starA * (.4 + .6 * hash(i * 3 + (vt >> 4))); c.fillStyle = i % 7 ? '#e8ecff' : '#ffd9a8'; c.fillRect(x | 0, y | 0, i % 11 ? 1 : 2, i % 11 ? 1 : 2);
    }
    c.globalAlpha = 1;
    if (alt < 2600) {                                           // dawn sun over the sea
      const sy = 154 + alt * 0.35, g2 = c.createRadialGradient(250, sy, 4, 250, sy, 70);
      g2.addColorStop(0, 'rgba(255,230,170,.9)'); g2.addColorStop(1, 'rgba(255,190,120,0)'); c.fillStyle = g2; c.fillRect(150, sy - 80, 200, 160);
      c.fillStyle = '#ffe6a6'; c.beginPath(); c.arc(250, sy, 13, Math.PI, 0); c.fill();
    }
    if (alt > 11000 && alt < 99999) {                            // the Moon grows as the target
      const k = Math.min(1, (alt - 11000) / 8000), id = k < .38 ? 'space-v2/bg/moon-32' : k < .75 ? 'space-v2/bg/moon-64' : 'space-v2/bg/moon-128';
      put(c, id, 250 - k * 60, 40 + k * 10);
    }
    if (alt > 8600) put(c, 'space-v2/bg/nebula', 0, 120 + (alt - 8600) * 0.05 + 40);
    if (alt > 7000 && alt < 12200) put(c, 'space-v2/bg/earth-limb', 0, H + 4 + (alt - 7000) * 0.024);
    if (alt > 9800 && alt < 12000) put(c, 'space-v2/bg/station', 70 + (alt - 9800) * 0.06, 60 + (alt - 9800) * 0.07);
    for (const [a, id, p] of [[4300, 'cirrus', .8], [5100, 'cirrus', .8], [5900, 'cirrus', .8]]) { const y = RY - (a - alt) * p; if (y > -10 && y < H + 60) put(c, 'space-v2/bg/' + id, ((a * 7) % 120) - 60, y); }
    for (const [a, p] of [[6100, .55], [7000, .55]]) { const y = RY - (a - alt) * p + 40; if (y > -10 && y < H + 140) put(c, 'space-v2/bg/aurora', 0, y); }
    for (let i = 0; i < 12; i++) {                              // far, air-tinted clouds behind everything
      const a = 300 + i * 420, y = RY - (a - alt) * 0.3 + 10; if (y < -10 || y > H + 60) continue;
      const off = Math.round(hash(i + 40) * 300); put(c, 'space-v2/bg/cloud-far', -off, y); put(c, 'space-v2/bg/cloud-far', 320 - off, y);
    }
    for (const [i, a] of [600, 1100, 1600, 2100, 2600, 3100, 3600, 4100, 4500].entries()) {
      const y = RY - (a - alt) * 0.7 + 50; if (y < -10 || y > H + 110) continue;
      const off = Math.round(hash(i) * 200), id = i % 2 ? 'space-v2/bg/cloud-b' : 'space-v2/bg/cloud-a';
      put(c, id, -off, y); put(c, id, 320 - off, y);
    }
    if (alt < 900) put(c, 'space-v2/bg/launch-far', 0, 196 + alt * 0.35);
    if (alt < 260) put(c, 'space-v2/bg/launch-near', 0, 240 + alt);
  }

  // ---------------------------------------------------------------- world objects
  const onScreen = (g, y) => RY - (y - (g.alt >> 8));
  function objects(c, g, vt) {
    for (const o of g.objs) {
      if (!o.type) continue;
      const x = o.x >> 8, y = onScreen(g, o.y);
      if (o.state > 0 && o.type !== T.STORM) {                 // edge warning before a fast crosser enters
        if ((vt >> 3) % 2) { const ex = x < 0 ? 10 : W - 10; c.fillStyle = 'rgba(255,90,60,.9)'; c.beginPath(); c.moveTo(ex, y - 8); c.lineTo(ex + (x < 0 ? 10 : -10), y); c.lineTo(ex, y + 8); c.fill(); text(c, '!', ex + (x < 0 ? -2 : 2), y, 12, '#ffffff', 'center'); }
        continue;
      }
      if (y < -60 || y > H + 60) continue;
      switch (o.type) {
        case T.BIRDS: put(c, 'space-v2/props/birds-' + ((vt >> 3) & 1), x, y); break;
        case T.PLANE: put(c, o.vx > 0 ? 'space-v2/props/plane' : 'space-v2/props/plane-left', x, y); break;
        case T.BALLOON: put(c, 'space-v2/props/balloon', x, y); break;
        case T.STORM: {
          put(c, 'space-v2/props/storm-cloud', x, y);
          if (o.state > 12) { if ((vt >> 2) % 2) { c.strokeStyle = 'rgba(255,240,150,.55)'; c.setLineDash([4, 6]); c.beginPath(); c.moveTo(x, y + 20); c.lineTo(x, H); c.stroke(); c.setLineDash([]); } }
          else if (o.state > 0) { c.strokeStyle = '#fffbe0'; c.lineWidth = 3; c.beginPath(); let yy = y + 18, xx = x; c.moveTo(xx, yy); while (yy < H) { yy += 14; xx = x + (hash(yy + vt) - .5) * 18; c.lineTo(xx, yy); } c.stroke(); c.lineWidth = 1; c.fillStyle = 'rgba(255,255,230,.25)'; c.fillRect(0, 0, W, H); }
          break;
        }
        case T.GUST: case T.JET: {
          const dir = o.vx, col = o.type === T.JET ? 'rgba(170,200,255,.55)' : 'rgba(255,255,255,.6)';
          for (let i = 0; i < 9; i++) { const yy = y - 4 - i * 6, xx = ((hash(i + o.y) * W + vt * 4 * dir) % W + W) % W; c.fillStyle = col; c.fillRect(xx, yy, 18, 1); c.fillRect(xx + (dir > 0 ? 16 : 0), yy - 1, 2, 3); }
          break;
        }
        case T.STAR: { const tw = 1 + ((vt >> 3) % 2); c.fillStyle = 'rgba(255,220,90,.35)'; c.beginPath(); c.arc(x, y, 9, 0, 7); c.fill(); c.fillStyle = '#ffd34a'; c.beginPath(); for (let k = 0; k < 10; k++) { const r = k % 2 ? 2.6 : 6 + tw, a = -Math.PI / 2 + k * Math.PI / 5; c.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } c.fill(); break; }
        case T.FUEL: c.fillStyle = 'rgba(120,230,255,.25)'; c.beginPath(); c.arc(x, y - 4, 13, 0, 7); c.fill(); put(c, 'space/props/fuel-can', x, y + 8); break;
        case T.REPAIR: put(c, 'space-v2/props/repair', x, y); break;
        case T.RING: { c.strokeStyle = o.done ? 'rgba(160,255,210,.25)' : 'rgba(120,255,200,.9)'; c.lineWidth = 3; c.beginPath(); c.ellipse(x, y, 18, 7, 0, 0, 7); c.stroke(); c.lineWidth = 1; break; }
        case T.SAT: put(c, 'space-v2/props/satellite', x, y); break;
        case T.JUNK: put(c, 'space-v2/props/junk', x, y); break;
        case T.ROCK: put(c, 'space/props/asteroid', x, y + 14); break;
        case T.METEOR: { c.strokeStyle = 'rgba(255,150,70,.75)'; c.lineWidth = 4; c.beginPath(); c.moveTo(x, y); c.lineTo(x - o.vx / 10, y - 26); c.stroke(); c.lineWidth = 1; put(c, 'space/props/asteroid', x, y + 14); break; }
        case T.COMET: put(c, o.vx < 0 ? 'space-v2/props/comet' : 'space-v2/props/comet-right', x, y); break;
      }
    }
  }

  // ---------------------------------------------------------------- the rocket
  const trail = [];
  function rocket(c, g, vt, on) {
    const x = g.x >> 8, lean = g.vx < -220 ? '-left' : g.vx > 220 ? '-right' : '';
    const flame = on ? 8 + (vt % 3) * 2 + (g.boostT ? 10 : 0) : 0;
    if (on && vt % 2 === 0) trail.push({ x: x + (Math.random() - .5) * 4, y: RY + 6, r: 3, t: 0 });
    for (const p of trail) { p.t++; p.y += 1.5 + (g.v >> 8); p.r += .35; }
    while (trail.length && trail[0].t > 40) trail.shift();
    const alt = g.alt >> 8;
    for (const p of trail) { c.fillStyle = alt < 6000 ? `rgba(230,230,240,${.5 - p.t / 90})` : `rgba(180,200,255,${.35 - p.t / 120})`; c.beginPath(); c.arc(p.x, p.y, p.r, 0, 7); c.fill(); }
    if (g.sep < 2 && g.mode === S.MODE.FLY || g.mode === S.MODE.IGNITE) put(c, 'space-v2/props/booster', x, RY + 14);
    const base = g.sep < 2 ? RY + 30 : RY + 2;
    if (flame) {
      c.fillStyle = 'rgba(255,150,60,.5)'; c.beginPath(); c.ellipse(x, base + flame / 2, 6, flame / 2 + 4, 0, 0, 7); c.fill();
      c.fillStyle = '#ffd36b'; c.beginPath(); c.moveTo(x - 4, base); c.lineTo(x + 4, base); c.lineTo(x, base + flame); c.fill();
      c.fillStyle = '#ffffff'; c.beginPath(); c.moveTo(x - 2, base); c.lineTo(x + 2, base); c.lineTo(x, base + flame / 2); c.fill();
    }
    if (g.boostT > 0) { c.strokeStyle = `rgba(140,230,255,${.4 + .4 * ((vt >> 1) % 2)})`; c.lineWidth = 2; c.beginPath(); c.ellipse(x, RY - 22, 14, 28, 0, 0, 7); c.stroke(); c.lineWidth = 1;
      for (let i = 0; i < 8; i++) { c.fillStyle = 'rgba(255,255,255,.6)'; c.fillRect(hash(i + vt) * W, hash(i * 7 + vt) * H, 1, 12); } }
    if (g.heat > 450 && alt < K.Z2) { c.fillStyle = `rgba(255,${200 - (g.heat >> 3)},80,${Math.min(.8, g.heat / 1200)})`; c.beginPath(); c.ellipse(x, RY - 40, 8, 6, 0, Math.PI, 0); c.fill(); }
    if (!g.invuln || (vt >> 2) % 2) put(c, 'space-v2/props/rocket' + lean, x, RY + 2);
  }

  // ---------------------------------------------------------------- landing finale
  function landing(c, g, vt, phase) {
    const gr = c.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#03041a'); gr.addColorStop(1, '#10132e'); c.fillStyle = gr; c.fillRect(0, 0, W, H);
    for (let i = 0; i < 80; i++) { c.fillStyle = '#dfe4ff'; c.globalAlpha = .3 + .7 * hash(i + (vt >> 5)); c.fillRect(hash(i) * W, hash(i + 9) * 150, 1, 1); } c.globalAlpha = 1;
    c.fillStyle = '#2f6fd0'; c.beginPath(); c.arc(70, 46, 15, 0, 7); c.fill(); c.fillStyle = '#5fbf7a'; c.beginPath(); c.arc(64, 42, 5, 0, 7); c.arc(76, 52, 4, 0, 7); c.fill();
    c.fillStyle = 'rgba(150,200,255,.25)'; c.beginPath(); c.arc(70, 46, 19, 0, 7); c.fill();
    put(c, 'space-v2/bg/lunar-surface', 0, H);
    const px = g.pad;
    c.fillStyle = '#3a4258'; c.fillRect(px - K.PAD_HALF, K.GROUND, K.PAD_HALF * 2, 6); c.fillStyle = (vt >> 4) % 2 ? '#7fe0c0' : '#3fa080'; c.fillRect(px - K.PAD_HALF + 3, K.GROUND + 2, K.PAD_HALF * 2 - 6, 2);
    for (const s of [-1, 1]) { c.fillStyle = (vt >> 3) % 2 ? '#ffe97a' : '#a08a3a'; c.fillRect(px + s * K.PAD_HALF - 1, K.GROUND - 3, 3, 3); }
    const x = g.lx >> 8, y = g.ly >> 8, ending = g.mode === S.MODE.ENDING;
    if (!ending && (phase === 'PLAY' || phase === 'READY')) { c.strokeStyle = 'rgba(127,224,192,.4)'; c.setLineDash([3, 5]); c.beginPath(); c.moveTo(px, 60); c.lineTo(px, K.GROUND - 4); c.stroke(); c.setLineDash([]); }
    if (g.boostT > 0) { c.fillStyle = '#ffd36b'; c.beginPath(); c.moveTo(x - 6, y + 2); c.lineTo(x + 6, y + 2); c.lineTo(x, y + 14 + (vt % 3) * 2); c.fill(); }
    put(c, 'space/lander/back', x, y);
    let name = g.boostT ? 'jet' : 'cabin_idle', f = (vt >> 3) % 4, out = false;
    if (ending) { if (g.modeT < 30) { name = 'land'; f = g.modeT >> 2; } else if (g.modeT < 100) { out = true; name = 'plant_flag'; f = (g.modeT - 30) >> 3; } else { out = true; name = 'settlement_cheer'; f = (g.modeT - 100) >> 2; } }
    if (!out) crew(c, name, f, x, y - 22);
    put(c, 'space/lander/front', x, y);
    if (out) { const nx = x < 200 ? x + 62 : x - 62; crew(c, name, f, nx, K.GROUND); if (name !== 'plant_flag' || f >= 4) put(c, 'space/props/flag', nx + 10, K.GROUND); }
    if (!ending && phase === 'PLAY') {
      const h = K.GROUND - y, vy = g.lvy, ok = vy <= K.SAFE_VY;
      text(c, `高度 ${Math.max(0, h)}  下降速度 ${(vy / 100).toFixed(1)}`, W / 2, 16, 11, ok ? '#7fe0c0' : '#ff8a6a', 'center', 700);
      if (h < 90 && !ok) text(c, '太快了！点中键反推', W / 2, 34, 12, '#ff8a6a', 'center');
    }
  }

  // ---------------------------------------------------------------- HUD and timing gauges
  function cockpit(c, g, vt) {
    c.fillStyle = 'rgba(6,10,30,.75)'; c.beginPath(); c.roundRect(4, 4, 62, 62, 10); c.fill();
    c.save(); c.beginPath(); c.roundRect(7, 7, 56, 56, 8); c.clip();
    const gr = c.createLinearGradient(0, 7, 0, 63); gr.addColorStop(0, '#1b2350'); gr.addColorStop(1, '#2f3a72'); c.fillStyle = gr; c.fillRect(7, 7, 56, 56);
    const hurtRecent = g.invuln > K.INVULN - 30, win = g.mode === S.MODE.ENDING;
    const name = win ? 'settlement_cheer' : hurtRecent ? 'hard_land' : (g.boostT || g.mode === S.MODE.IGNITE && g.ign) ? 'jet' : 'cabin_idle';
    crew(c, name, (vt >> 3) % (name === 'jet' ? 4 : 6), 35, win ? 78 : 66);
    c.restore();
    c.strokeStyle = hurtRecent ? '#ff6a4a' : '#8ea6e8'; c.lineWidth = 2; c.beginPath(); c.roundRect(7, 7, 56, 56, 8); c.stroke(); c.lineWidth = 1;
  }
  // display distance: 12 km of weather, 100 km to the edge of space, low orbit, then out to the Moon (384,400 km)
  function kmAt(alt) {
    if (alt < K.Z1) return Math.round(alt * 12 / K.Z1);
    if (alt < K.Z2) return 12 + Math.round((alt - K.Z1) * 88 / (K.Z2 - K.Z1));
    if (alt < K.Z3) return 100 + Math.round((alt - K.Z2) * 1900 / (K.Z3 - K.Z2));
    return Math.min(384400, 2000 + Math.round((alt - K.Z3) * 382400 / (K.Z4 - K.Z3)));
  }
  function bar(c, x, y, w, pct, col) { c.fillStyle = 'rgba(255,255,255,.15)'; c.fillRect(x, y, w, 6); c.fillStyle = col; c.fillRect(x, y, w * Math.max(0, Math.min(1, pct)), 6); }
  function hud(c, g, vt) {
    const Y = H - 24; c.fillStyle = 'rgba(6,10,30,.82)'; c.fillRect(0, Y, W, 24);
    const f = g.fuel / K.FUEL_MAX;
    text(c, '燃料', 6, Y + 8, 9, '#ffffff', 'left', 700, null); bar(c, 30, Y + 5, 70, f, f < .25 ? ((vt >> 3) % 2 ? '#ff6a4a' : '#ffb2a0') : f < .5 ? '#ffc34a' : '#7fe0c0');
    if (g.mode !== S.MODE.LAND) { text(c, '温度', 6, Y + 18, 9, '#ffffff', 'left', 700, null); bar(c, 30, Y + 15, 70, g.heat / K.HEAT_MAX, g.heat > 700 ? '#ff6a4a' : '#ffae45'); }
    for (let i = 0; i < K.HULL; i++) { c.fillStyle = i < g.hull ? '#7fe0c0' : 'rgba(255,255,255,.15)'; c.beginPath(); c.roundRect(108 + i * 13, Y + 6, 10, 12, 2); c.fill(); }
    const m = S.mult(g); if (g.combo >= 2) text(c, `${g.combo}连` + (m > 1 ? ` ×${m}` : ''), 152, Y + 12, 11, m > 1 ? '#ffd34a' : '#ffffff', 'left', 900, null);
    const km = g.mode >= S.MODE.LAND ? '月面' : `${kmAt(g.alt >> 8).toLocaleString()} km`;
    text(c, km, 248, Y + 12, 10, '#c8d2f0', 'right', 700, null);
    text(c, String(g.score), W - 6, Y + 12, 16, '#ffffff', 'right', 900, null);
    // journey strip: where we are between the Earth and the Moon
    const prog = g.mode >= S.MODE.LAND ? 1 : Math.min(1, (g.alt >> 8) / K.Z4);
    c.fillStyle = 'rgba(255,255,255,.2)'; c.fillRect(74, 8, 170, 2); c.fillStyle = '#7fd6ff'; c.fillRect(74, 8, 170 * prog, 2);
    for (const z of [K.Z1, K.Z2, K.Z3]) c.fillRect(74 + 170 * z / K.Z4, 6, 1, 6);
    c.fillStyle = '#2f6fd0'; c.beginPath(); c.arc(70, 9, 4, 0, 7); c.fill(); c.fillStyle = '#d9d6cc'; c.beginPath(); c.arc(248, 9, 4, 0, 7); c.fill();
    c.fillStyle = '#ffffff'; c.fillRect(74 + 170 * prog - 1, 4, 3, 10);
  }
  function gaugePanel(c, title, hint, needle, green, yellow, vt) {
    c.fillStyle = 'rgba(6,10,30,.8)'; c.beginPath(); c.roundRect(70, 72, 180, 66, 10); c.fill();
    text(c, title, 160, 86, 14, '#ffd34a', 'center', 900, null); text(c, hint, 160, 128, 10, '#ffffff', 'center', 700, null);
    const x0 = 86, w = 148, y = 102;
    c.fillStyle = '#5a2a2a'; c.fillRect(x0, y, w, 12);
    c.fillStyle = '#7a6a2a'; c.fillRect(x0 + w * yellow[0] / 100, y, w * (yellow[1] - yellow[0]) / 100, 12);
    c.fillStyle = '#2f9a6a'; c.fillRect(x0 + w * green[0] / 100, y, w * (green[1] - green[0]) / 100, 12);
    c.fillStyle = '#ffffff'; c.fillRect(x0 + w * needle / 100 - 1, y - 4, 3, 20);
  }
  function timing(c, g, vt) {
    if (g.mode === S.MODE.IGNITE) {
      gaugePanel(c, '点火', `中键按在绿区 · 点亮 ${g.ign}/3 台发动机`, S.gauge(g.modeT), [72, 88], [60, 100], vt);
      for (let i = 0; i < 3; i++) { c.fillStyle = i < g.ign ? '#ffb84a' : 'rgba(255,255,255,.2)'; c.beginPath(); c.arc(140 + i * 20, 152, 5, 0, 7); c.fill(); }
      const t = Math.max(0, Math.ceil((K.IGN_T - g.modeT) / 60)); text(c, `T-${t}`, 160, 60, 14, '#ffffff', 'center');
    } else if (g.sep === 1) gaugePanel(c, '一级分离！', '指针扫到绿区时按中键', Math.min(100, Math.trunc(g.sepT * 100 / K.SEP_T)), [71, 85], [60, 96], vt);
    else if (g.tli === 1) {
      c.fillStyle = 'rgba(6,10,30,.8)'; c.beginPath(); c.roundRect(70, 72, 180, 66, 10); c.fill();
      text(c, '地月转移点火', 160, 86, 14, '#ffd34a', 'center', 900, null); text(c, '光圈收到中间时按中键 ×3', 160, 128, 10, '#ffffff', 'center', 700, null);
      for (let i = 0; i < 3; i++) {
        const at = K.TLI_LEAD + i * K.TLI_BEAT, d = at - g.tliT, cx = 120 + i * 40;
        c.strokeStyle = 'rgba(255,255,255,.5)'; c.beginPath(); c.arc(cx, 108, 7, 0, 7); c.stroke();
        if (i < g.tliHit) { c.fillStyle = '#7fe0c0'; c.beginPath(); c.arc(cx, 108, 6, 0, 7); c.fill(); }
        else if (d > -12 && d < 40) { c.strokeStyle = '#ffd34a'; c.lineWidth = 2; c.beginPath(); c.arc(cx, 108, 7 + Math.max(0, d) * .5, 0, 7); c.stroke(); c.lineWidth = 1; }
      }
    }
  }
  const ZONE = [null, ['发射升空', '左右躲开鸟群和飞机，中键加速'], ['冲出大气层', '加速太多会过热；穿过极光环降温'], ['进入太空', '躲开卫星和太空垃圾；加速时护盾能撞碎小碎片'], ['奔向月球', '流星雨来了'], ['登月舱分离', '点按中键反推，左右对准着陆台']];
  function fx(c, g) {
    const F = S.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      const a = Math.max(0, 1 - e.t / 70); c.globalAlpha = a; const rise = e.t * .4;
      if (e.kind === F.STAR || e.kind === F.RING || e.kind === F.NEAR || e.kind === F.SMASH) text(c, (e.kind === F.NEAR ? '擦边 +' : e.kind === F.SMASH ? '撞碎 +' : '+') + e.val, e.x, e.y - 14 - rise, 12, e.kind === F.RING ? '#7fffd0' : '#ffd34a', 'center');
      else if (e.kind === F.FUEL) text(c, '燃料 +', e.x, e.y - 14 - rise, 11, '#7fd6ff', 'center');
      else if (e.kind === F.REPAIR) text(c, '修好一格', e.x, e.y - 14 - rise, 11, '#7fe0c0', 'center');
      else if (e.kind === F.HIT) { text(c, ['', '撞上了！', '被闪电劈中！', '过热！'][e.val] || '撞上了！', e.x, e.y - 50, 14, '#ff8a6a', 'center'); if (e.t < 8) { c.fillStyle = 'rgba(255,80,60,.25)'; c.fillRect(0, 0, W, H); } }
      else if (e.kind === F.OVERHEAT) text(c, '过热', e.x, e.y - 40, 12, '#ff8a6a', 'center');
      else if (e.kind === F.TIMING || e.kind === F.SEP) text(c, ['偏了', '不错', '完美！'][e.val], 160, 60 - rise, 16, ['#ff8a6a', '#ffffff', '#ffd34a'][e.val], 'center');
      else if (e.kind === F.LANDED) text(c, e.val === 2 ? '完美登月！' : '登月成功！', 160, 70, 22, '#ffd34a', 'center');
      else if (e.kind === F.CRASH) text(c, '摔了！再来一次', e.x, e.y, 14, '#ff8a6a', 'center');
      else if (e.kind === F.ZONE && ZONE[e.val]) {
        const slide = e.t < 10 ? (10 - e.t) * 20 : 0; c.globalAlpha = Math.min(1, (70 - e.t) / 15);
        c.fillStyle = 'rgba(6,10,30,.7)'; c.fillRect(0, 150, W, 40);
        text(c, ZONE[e.val][0], W / 2 + slide, 163, 16, '#ffd34a', 'center', 900, null); text(c, ZONE[e.val][1], W / 2 + slide, 181, 10, '#ffffff', 'center', 700, null);
      }
      c.globalAlpha = 1;
    }
  }

  const UIT = { name: '火箭登月', pitch: '点火、分离、奔月、着陆，关键时刻按 ●', keys: [['◀', '左移'], ['●', '加速/时机'], ['▶', '右移']], th: [1500, 3500, 6000], ink: '6,10,30', go: '点火！', tip: '准备发射' };
  function title(c, vt, best) {
    backdrop(c, 0, vt);
    const g = S.start(1); rocket(c, g, vt, false);
    root.AdvV2UI.title(c, { ...UIT, best }, vt);
  }

  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    if (g.mode === S.MODE.LAND || g.mode === S.MODE.ENDING || (g.mode === S.MODE.LOST && g.lvy + g.ly > 0)) landing(c, g, vt, phase);
    else {
      const alt = g.alt >> 8; backdrop(c, alt, vt); objects(c, g, vt);
      rocket(c, g, vt, g.mode === S.MODE.FLY || (g.mode === S.MODE.IGNITE && g.ign > 0));
      if (g.mode === S.MODE.IGNITE && g.ign > 0) { for (let i = 0; i < 6 * g.ign; i++) { c.fillStyle = `rgba(240,240,245,${.6 - i / 40})`; c.beginPath(); c.arc(160 + (hash(i + vt) - .5) * 90, RY + 34 + hash(i * 3) * 20, 6 + hash(i * 5 + vt) * 10, 0, 7); c.fill(); } }
      if (g.sep === 2 && g.fx.some(e => e.kind === S.FX.SEP)) { const e = g.fx.find(e => e.kind === S.FX.SEP); put(c, 'space-v2/props/booster', (g.x >> 8) - e.t * .6, RY + 20 + e.t * 2.4); }
    }
    timing(c, g, vt); fx(c, g); cockpit(c, g, vt); hud(c, g, vt);
    const U = root.AdvV2UI;
    if (phase === 'READY') U.ready(c, { ...UIT, go: '准备发射', tip: '' }, 0);
    if (phase === 'PAUSE') U.pause(c, UIT);
    if (phase === 'RESULT') U.result(c, UIT, { cause: g.win ? '登月成功！' : (g.fuel <= 0 ? '燃料耗尽' : '火箭受损，任务中止'), score: g.score, best: info.bestBefore ?? best, th: UIT.th,
      lines: [`${g.win ? '384,400' : kmAt(g.alt >> 8).toLocaleString()} km · 星星 ${g.stars} · 擦边 ${g.near} · 完美 ${g.perfects}`], retry: '● 再来一次' }, phaseT, vt);
  }
  root.AdvSpaceV2Draw = { load, draw };
})(window);
