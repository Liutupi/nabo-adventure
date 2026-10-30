// SKY V2 G1 renderer (browser only). NABO uses the existing sky_a frames unchanged (no rotation/mirroring/scaling).
// The envelope and basket are drawn at 2/3 size: the firmware will need those two machine parts pre-scaled offline
// (new small PNGs, not the character). Houses, trees, wind streaks, letters and bolts are procedural.
// Backdrops reuse the SPACE V2 clouds and seaside town (already embedded in the firmware for the rocket stage).
(function (root) {
  'use strict';
  const S = root.AdvSkyV2, K = S.K, T = S.T, W = K.W, H = K.H, BX = K.BX;
  const img = new Map(), clips = new Map(), props = new Map();
  const BG = ['space-v2/bg-cloud-far.png', 'space-v2/bg-cirrus.png', 'space-v2/bg-cloud-a.png', 'space-v2/bg-cloud-b.png', 'space-v2/bg-launch-far.png'];
  let envSmall = null, basketFront = null, basketBack = null;
  async function load(base = '../art/') {
    const inline = root.SKY_SPRITES;
    const manifest = inline ? inline.manifest : await (await fetch(base + 'sky-manifest.json')).json();
    const want = new Set(BG);
    for (const c of manifest.animations) if (c.skin === 'sky_a' || c.name === 'bird') { clips.set(c.name, c); (c.runtime_frames || c.frames).forEach(p => want.add(p)); }
    for (const a of manifest.assets) { props.set(a.id, a); want.add(a.path); }
    await Promise.all([...want].map(async p => { const im = new Image(); im.src = inline ? inline.files[p] : base + p; await im.decode(); img.set(p, im); }));
    const scaled = (id, f) => { const im = img.get(props.get(id).path), cv = document.createElement('canvas'); cv.width = Math.round(im.width * f); cv.height = Math.round(im.height * f); const c = cv.getContext('2d'); c.imageSmoothingQuality = 'high'; c.drawImage(im, 0, 0, cv.width, cv.height); return cv; };
    envSmall = scaled('sky/envelope', 2 / 3); basketFront = scaled('sky/basket_front', 2 / 3); basketBack = scaled('sky/basket_back', 2 / 3);
  }
  const hash = n => { n = Math.imul(n ^ 0x9e3779b9, 0x85ebca6b); n ^= n >>> 13; n = Math.imul(n, 0xc2b2ae35); return ((n ^ n >>> 16) >>> 0) / 4294967296; };
  function actor(c, name, f, x, y) {
    const clip = clips.get(name); if (!clip) return;
    const fr = clip.runtime_frames || clip.frames, im = img.get(fr[Math.max(0, Math.min(fr.length - 1, f))]);
    const an = clip.runtime_anchor || [im.width >> 1, im.height];
    if (im) c.drawImage(im, Math.round(x - an[0]), Math.round(y - an[1]));
  }
  function prop(c, id, x, y) {
    const a = props.get(id), im = a && img.get(a.path); if (!im) return;
    c.drawImage(im, Math.round(x - im.width / 2), Math.round(y - im.height / 2));
  }
  function text(c, s, x, y, size, color, align = 'left', weight = 900, stroke = 'rgba(28,30,60,.85)') {
    c.font = `${weight} ${size}px "Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif`; c.textAlign = align; c.textBaseline = 'middle';
    if (stroke) { c.lineWidth = Math.max(2, size / 5); c.strokeStyle = stroke; c.lineJoin = 'round'; c.strokeText(s, x, y); }
    c.fillStyle = color; c.fillText(s, x, y);
  }
  function tile(c, path, scroll, y, alpha = 1) {
    const im = img.get(path); if (!im) return; c.globalAlpha = alpha;
    const off = ((Math.floor(scroll) % im.width) + im.width) % im.width;
    c.drawImage(im, -off, y); c.drawImage(im, im.width - off, y); c.globalAlpha = 1;
  }

  const SKY = { 0: ['#5e9fe0', '#a9d3f2', '#f8dcb4'], 3: ['#3b4a6e', '#6d7a99', '#b9a99a'], 4: ['#61a7e6', '#b5dcf6', '#fff0c8'], 5: ['#4f97de', '#9fcff3', '#e9f3f8'] };
  function backdrop(c, g, vt) {
    const pal = SKY[g.section] || SKY[0], gr = c.createLinearGradient(0, 0, 0, H);
    gr.addColorStop(0, pal[0]); gr.addColorStop(.55, pal[1]); gr.addColorStop(1, pal[2]); c.fillStyle = gr; c.fillRect(0, 0, W, H);
    const d = g.dist / 256;
    if (g.section === S.SEC.RAINBOW) {
      const cols = ['#ff7a6b', '#ffb35c', '#ffe46b', '#8fe08a', '#6cc6ff', '#9a8cff'];
      cols.forEach((col, i) => { c.strokeStyle = col; c.globalAlpha = .45; c.lineWidth = 4; c.beginPath(); c.arc(230 - d * .05 % 400, 230, 150 - i * 4, Math.PI, 2 * Math.PI); c.stroke(); });
      c.globalAlpha = 1;
    }
    tile(c, BG[1], d * .08, 18, .7);
    tile(c, BG[0], d * .15, 48, .85);
    tile(c, BG[4], d * .25, 128, 1);              // seaside town on the horizon
    tile(c, BG[2], d * .45, 92, .55);
  }
  // Wind layers: streaks move at each layer's own speed, so "which layer is fast" can be read from the sky itself.
  function wind(c, g, vt) {
    const bounds = [K.YMIN - 40, K.LAYER[0], K.LAYER[1], K.LAYER[2], K.YMAX + 6];
    for (let l = 0; l < 4; l++) {
      const v = S.layerSpeed(g, l) / 256, cy0 = bounds[l] - K.ENV_DY + 8, cy1 = bounds[l + 1] - K.ENV_DY + 8;   // streaks drawn around the envelope's height for that layer
      const n = 3 + Math.round(v * 1.5);
      c.strokeStyle = l === g.layer ? 'rgba(255,255,255,.75)' : 'rgba(255,255,255,.35)'; c.lineWidth = 1;
      for (let i = 0; i < n; i++) {
        const h = hash(l * 97 + i * 13), len = 8 + v * 9, x = W - ((vt * v * 1.6 + h * 600) % (W + 60)), y = cy0 + h * (cy1 - cy0);
        c.beginPath(); c.moveTo(x, y); c.lineTo(x + len, y); c.stroke();
      }
    }
  }
  function ground(c, g) {
    const cam = S.camX(g);
    c.fillStyle = '#7fb85c'; c.fillRect(0, K.GROUND, W, H - K.GROUND);
    c.fillStyle = '#6aa24c'; for (let x = -(cam % 12); x < W; x += 12) c.fillRect(x, K.GROUND, 6, 3);
    c.fillStyle = '#c9b48a'; c.fillRect(0, K.GROUND + 12, W, 4);
  }
  const HOUSE = [['#f2e3c6', '#d0584a'], ['#dfe9f2', '#4d6fa8'], ['#f6d7b4', '#7a5aa8'], ['#e8ecd6', '#3f8a6a']];
  function objects(c, g, vt) {
    const cam = S.camX(g), by = g.y >> 8;
    for (const o of g.objs) {
      if (!o.type) continue;
      const x = o.x - cam; if (x < -70 || x > W + 70) continue;
      if (o.type === T.HOUSE) {
        const [wall, roof] = HOUSE[(o.v >> 1) & 3], gold = o.v & 1, w = 22;
        c.fillStyle = wall; c.fillRect(x - w, o.y + 10, w * 2, K.GROUND - o.y - 10);
        c.fillStyle = roof; for (let r = 0; r < 12; r++) c.fillRect(x - w - 3 + r, o.y + r - 2, (w + 3 - r) * 2, 1);
        c.fillStyle = 'rgba(40,50,80,.55)'; c.fillRect(x - 12, o.y + 18, 7, 8); c.fillRect(x + 6, o.y + 18, 7, 8); c.fillStyle = '#8a5a3a'; c.fillRect(x - 3, K.GROUND - 12, 7, 12);
        // the mailbox on the ridge is the target
        if (o.done === 1) { c.fillStyle = '#9fe0a0'; c.fillRect(x - 5, o.y - 9, 10, 7); text(c, '✓', x, o.y - 16, 9, '#ffffff', 'center', 900); }
        else if (o.done !== 2) {
          if (gold) { c.fillStyle = `rgba(255,215,80,${.35 + .25 * Math.sin(vt * .2)})`; c.beginPath(); c.arc(x, o.y - 6, 11, 0, 7); c.fill(); }
          c.fillStyle = gold ? '#ffcf3a' : '#e8473a'; c.fillRect(x - 5, o.y - 10, 10, 8); c.fillStyle = '#2a2a3a'; c.fillRect(x - 3, o.y - 8, 6, 1);
          c.fillStyle = '#6a4a3a'; c.fillRect(x - 1, o.y - 2, 2, 3);
          if (x > BX && x < BX + 150) { c.fillStyle = 'rgba(255,255,255,.7)'; c.fillRect(x, o.y - 26 + (vt >> 3 & 1) * 2, 1, 8); c.beginPath(); c.moveTo(x - 3, o.y - 19); c.lineTo(x + 3, o.y - 19); c.lineTo(x, o.y - 15); c.fill(); }
        }
      } else if (o.type === T.TREE) {
        c.fillStyle = '#6b4a32'; c.fillRect(x - 2, o.y + 20, 4, K.GROUND - o.y - 20);
        if (o.v) { c.fillStyle = '#2f7a4f'; c.beginPath(); c.ellipse(x, o.y + 20, 7, 22, 0, 0, 7); c.fill(); c.fillStyle = '#3d9461'; c.fillRect(x - 3, o.y + 4, 3, 24); }
        else { c.fillStyle = '#3a8a52'; for (let k = 0; k < 3; k++) { const ty = o.y + k * 12, hw = 6 + k * 3; c.beginPath(); c.moveTo(x, ty); c.lineTo(x + hw, ty + 16); c.lineTo(x - hw, ty + 16); c.fill(); } }
      } else if (o.type === T.BIRD) {
        const q = o.v & 63, oy = o.y + Math.trunc(((q < 32 ? q : 64 - q) - 16) * 3 / 8);
        actor(c, 'bird', (vt >> 3) & 3, x, oy + 8);
      } else if (o.type === T.STORM) {
        const p = S.stormPhase(o), warn = p >= K.STORM_WARN && p < K.STORM_BOLT, bolt = p >= K.STORM_BOLT && p < K.STORM_END;
        if (warn || bolt) {        // where the bolt will strike: a column the player can read before it happens
          c.fillStyle = bolt ? 'rgba(255,240,140,.25)' : `rgba(255,220,90,${(p >> 3 & 1) ? .22 : .08})`; c.fillRect(x - K.BOLT_HALF, o.y + K.STORM_H, K.BOLT_HALF * 2, K.BOLT_LEN);
        }
        if (bolt) { c.strokeStyle = '#fff6a0'; c.lineWidth = 3; c.beginPath(); c.moveTo(x, o.y + 8); for (let k = 1; k <= 5; k++) c.lineTo(x + (k & 1 ? 5 : -5), o.y + K.STORM_H + k * K.BOLT_LEN / 5); c.stroke(); }
        if (warn && (p >> 2 & 1)) c.filter = 'brightness(1.6)';
        prop(c, 'sky/thundercloud', x, o.y); c.filter = 'none';
      } else if (o.type === T.TANK && !o.done) {
        const bob = Math.round(Math.sin((vt + o.x) * .08) * 2);
        c.strokeStyle = '#f5f0e0'; c.lineWidth = 1; c.beginPath(); c.arc(x, o.y - 10 + bob, 9, Math.PI, 0); c.stroke();
        c.fillStyle = '#ff9a3a'; c.beginPath(); c.arc(x, o.y - 10 + bob, 9, Math.PI, 0); c.fill();
        c.beginPath(); c.moveTo(x - 9, o.y - 10 + bob); c.lineTo(x, o.y + bob); c.lineTo(x + 9, o.y - 10 + bob); c.strokeStyle = '#f5f0e0'; c.stroke();
        c.fillStyle = '#d23a3a'; c.fillRect(x - 4, o.y - 1 + bob, 8, 10); c.fillStyle = '#fff'; c.fillRect(x - 2, o.y + 2 + bob, 4, 2);
      }
    }
    for (const L of g.letters) {
      if (!L.on) continue;
      const lx = (L.x >> 8) - cam, ly = L.y >> 8;
      c.fillStyle = '#ffffff'; c.fillRect(lx - 4, ly - 3, 8, 6); c.fillStyle = '#d0584a'; c.fillRect(lx - 1, ly - 1, 2, 2);
    }
  }

  function balloon(c, g, phase, vt, st) {
    const by = (g.y >> 8) + (phase === 'RESULT' ? Math.min(30, st.phaseT) : 0);
    if (g.invuln && (vt >> 2 & 1)) c.globalAlpha = .55;
    // shadow on the ground tells the player where a letter would land right now
    c.fillStyle = 'rgba(30,50,40,.25)'; c.beginPath(); c.ellipse(BX, K.GROUND + 2, 14 - (K.GROUND - by) / 16, 3, 0, 0, 7); c.fill();
    const ex = BX - envSmall.width / 2, ey = by - K.ENV_DY - envSmall.height / 2;
    c.drawImage(envSmall, Math.round(ex), Math.round(ey));
    c.strokeStyle = '#5a4030'; c.lineWidth = 1; c.beginPath(); c.moveTo(BX - 18, by - 32); c.lineTo(BX - 20, by - 18); c.moveTo(BX + 18, by - 32); c.lineTo(BX + 20, by - 18); c.stroke();
    if (g.heating && phase === 'PLAY') { const f = 6 + (vt & 3) * 2; c.fillStyle = '#ffb03a'; c.beginPath(); c.moveTo(BX - 4, by - 30); c.lineTo(BX, by - 30 - f); c.lineTo(BX + 4, by - 30); c.fill(); c.fillStyle = '#fff3a0'; c.fillRect(BX - 1, by - 33, 2, 3); }
    c.drawImage(basketBack, Math.round(BX - basketBack.width / 2), by - 20);
    let name = 'idle', f = (vt >> 3) % 6;
    if (phase === 'RESULT') { name = 'settlement_cheer'; f = Math.min(7, st.phaseT >> 3); }
    else if (g.invuln > K.INVULN - 24) { name = 'hit'; f = Math.min(5, (K.INVULN - g.invuln) >> 2); }
    else if (st.cheer > 0) { name = 'receive_stamp'; f = Math.min(3, (24 - st.cheer) >> 2); }
    else if (g.heating) { name = 'heat'; f = (vt >> 2) % 6; }
    else if (g.venting) { name = 'vent'; f = (vt >> 2) % 6; }
    if (name === 'settlement_cheer') actor(c, name, f, BX, by - 2); else actor(c, name, f, BX, by - 4);
    c.drawImage(basketFront, Math.round(BX - basketFront.width / 2), by - basketFront.height);
    c.globalAlpha = 1;
  }

  function hud(c, g, vt) {
    const pct = g.res / 1000, low = pct < .25;
    c.fillStyle = 'rgba(28,30,60,.62)'; c.fillRect(0, 0, W, 18);
    text(c, '燃料', 6, 9, 10, '#ffffff', 'left', 700, null);
    c.fillStyle = 'rgba(255,255,255,.2)'; c.fillRect(32, 5, 74, 8);
    c.fillStyle = low ? (vt % 20 < 10 ? '#ff5a4a' : '#ffb0a0') : pct < .5 ? '#ffc34a' : '#ffa04a'; c.fillRect(32, 5, 74 * pct, 8);
    const m = S.mult(g);
    if (g.combo >= 2) text(c, `${g.combo}连送` + (m > 1 ? ` ×${m}` : ''), 160, 9, 11, m > 1 ? '#ffd34a' : '#ffffff', 'center', 900, null);
    text(c, String(g.score), W - 6, 9, 14, '#ffffff', 'right', 900, null);
    // wind gauge on the right edge, one arrow per layer at the envelope height of that layer
    const mids = [(K.YMIN + K.LAYER[0]) / 2, (K.LAYER[0] + K.LAYER[1]) / 2, (K.LAYER[1] + K.LAYER[2]) / 2, (K.LAYER[2] + K.YMAX) / 2];
    for (let l = 0; l < 4; l++) {
      const v = S.layerSpeed(g, l), len = 6 + Math.round((v - 200) / 30), y = Math.round(mids[l] - K.ENV_DY + 10), on = l === g.layer;
      c.fillStyle = on ? 'rgba(28,30,60,.7)' : 'rgba(28,30,60,.35)'; c.fillRect(W - 34, y - 6, 32, 12);
      c.fillStyle = on ? '#ffffff' : 'rgba(255,255,255,.7)';
      c.fillRect(W - 4 - len, y - 1, len - 4, 2); c.beginPath(); c.moveTo(W - 8, y - 4); c.lineTo(W - 4, y); c.lineTo(W - 8, y + 4); c.fill();
    }
  }

  const SECTION = [null, ['小镇', '房子多，连着送'], ['候鸟', '鸟群很多'], ['雷暴', '闪电前先下降'], ['彩虹', '金邮筒变多'], ['顺风', '所有风层更快']];
  function fx(c, g) {
    const F = S.FX;
    for (const e of g.fx) {
      if (!e.kind) continue;
      c.globalAlpha = Math.max(0, 1 - e.t / 60);
      if (e.kind === F.DELIVER) text(c, '+' + e.val, e.x, e.y - e.t * .4, 12, '#ffd34a', 'center');
      else if (e.kind === F.BULL) { text(c, '正中!', e.x, e.y - 14 - e.t * .4, 11, '#ffffff', 'center'); text(c, '+' + e.val, e.x, e.y - e.t * .4, 13, '#ffd34a', 'center'); }
      else if (e.kind === F.MISS) text(c, '扔歪了', e.x, e.y - e.t * .3, 10, '#ff9a7a', 'center');
      else if (e.kind === F.SKIP) text(c, '漏了一家', Math.max(30, e.x), e.y, 10, '#ff9a7a', 'center');
      else if (e.kind === F.HIT || e.kind === F.GROUND) text(c, e.kind === F.GROUND ? '擦到地面' : '撞到了！', BX, (g.y >> 8) - 100, 12, '#ff8a6a', 'center');
      else if (e.kind === F.TANK) text(c, '+燃料', e.x, e.y - 18 - e.t * .3, 11, '#ffd0a0', 'center');
      else if (e.kind === F.NEAR) text(c, '好险', e.x, e.y - e.t * .3, 10, '#bfe6ff', 'center');
      else if (e.kind === F.SECTION && SECTION[e.val]) {
        const slide = e.t < 10 ? (10 - e.t) * 20 : 0; c.globalAlpha = Math.min(1, (70 - e.t) / 15);
        c.fillStyle = 'rgba(28,30,60,.65)'; c.fillRect(0, 150, W, 38);
        text(c, SECTION[e.val][0] + ' · 风向变了', W / 2 + slide, 162, 15, '#ffd34a', 'center', 900, null); text(c, SECTION[e.val][1], W / 2 + slide, 178, 10, '#ffffff', 'center', 700, null);
      }
      c.globalAlpha = 1;
    }
  }

  function keyRow(c, y, items) {
    items.forEach(([k, s], i) => { const x = 60 + i * 100; c.fillStyle = 'rgba(255,255,255,.16)'; c.beginPath(); c.roundRect(x - 44, y - 11, 88, 22, 8); c.fill(); text(c, `${k} ${s}`, x, y, 11, '#ffffff', 'center', 800, null); });
  }
  const UIT = { name: '风层邮差', pitch: '乘对风层，把信投进邮筒', keys: [['◀', '放气↓'], ['●', '投信'], ['▶', '加热↑']], th: [300, 1000, 2500], ink: '28,30,60', go: '起飞！', tip: '右边箭头越长，那一层风越快' };
  function title(c, vt, best) {
    const fake = S.start(3); fake.dist = vt * 420; fake.y = (150 + Math.round(Math.sin(vt * .03) * 20)) << 8; fake.heating = Math.sin(vt * .03) < 0 ? 1 : 0;
    backdrop(c, fake, vt); ground(c, fake); balloon(c, fake, 'TITLE', vt, { cheer: 0, phaseT: 0 });
    root.AdvV2UI.title(c, { ...UIT, best }, vt);
  }

  const st = { cheer: 0, lastDel: 0, shake: 0, lastHits: 0, phaseT: 0 };
  function draw(c, g, phase, vt, phaseT, best, info = {}) {
    c.imageSmoothingEnabled = false;
    if (phase === 'TITLE') return title(c, vt, best);
    if (g.delivered !== st.lastDel) { st.cheer = 24; st.lastDel = g.delivered; }
    if (g.hits !== st.lastHits) { st.shake = 10; st.lastHits = g.hits; }
    if (st.cheer > 0) st.cheer--;
    st.phaseT = phaseT;
    c.save();
    if (st.shake > 0) { st.shake--; c.translate((st.shake & 1 ? 2 : -2), (st.shake & 2 ? 1 : -1)); }
    backdrop(c, g, vt); wind(c, g, vt); ground(c, g); objects(c, g, vt); balloon(c, g, phase, vt, st);
    c.restore();
    fx(c, g); hud(c, g, vt);
    const U = root.AdvV2UI;
    if (phase === 'READY') U.ready(c, UIT, info.countdown);
    if (phase === 'PAUSE') U.pause(c, UIT);
    if (phase === 'RESULT') U.result(c, UIT, { cause: '燃料用完，平安降落', score: g.score, best: info.bestBefore ?? best, th: UIT.th,
      lines: [`送达 ${g.delivered} 封 · 正中 ${g.bulls} · 金邮筒 ${g.golds} · 最长 ${g.best} 连`, `${g.meters} 米 · 漏送 ${g.skipped} 家 · 撞到 ${g.hits} 次`] }, phaseT, vt);
  }
  root.AdvSkyV2Draw = { load, draw };
})(window);
