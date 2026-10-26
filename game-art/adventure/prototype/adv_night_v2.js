// NIGHT V2「萤火虫之夜」— G1 browser prototype rules (not yet the firmware reference).
// Landscape 320x240, 60 Hz fixed steps, seeded mulberry32. Floats are fine at G1;
// the firmware port (G4) will convert to integer fixed point after the rules are approved.
(function (root) {
  'use strict';
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  const K = {
    W: 320, H: 240, GROUND: 200,
    SPEED: [0.55, 1.15, 2.2],          // brake / walk / run, world px per frame
    SCREEN_X: [78, 112, 156],          // where the camera keeps NABO for each gait
    LIGHT_MAX: 1000, LIGHT_START: 720,
    DECAY: 0.42, RUN_COST: 0.22,       // light per frame
    FLY_LIGHT: 36, GOLD_LIGHT: 150, MOTH_LOSS: 120, TRIP_LOSS: 130, OWL_LOSS: 200,
    SWING_FRAMES: 18, SWING_ON: 3, SWING_OFF: 12, NET_R: 28, NET_DX: 20, NET_DY: 42,
    METER_FULL: 30, METER_STEP: 12, BURST_FRAMES: 150, BURST_LIGHT: 160, WHIFF_LOSS: 16, DOUBLE_TAP: 16,
    TRIP_STUN: 54, OWL_STUN: 30, OWL_WARN: 96, OWL_HIT: 18, OWL_NEAR: 44,
    CALM: 900, EVENT_EVERY: 1500, EVENT_LEN: 480,
  };
  const EVENTS = ['swarm', 'owls', 'wind'];

  function start(seed) {
    const g = {
      seed, r: rng(seed), tick: 0, x: 0, gait: 1, screenX: K.SCREEN_X[1], camX: -K.SCREEN_X[1],
      light: K.LIGHT_START, score: 0, caught: 0, combo: 0, meter: 0,
      swingT: 0, swingCaught: 0, lastSwingTick: -999, stunT: 0, stunKind: '', burstT: 0,
      flies: [], moths: [], roots: [], owls: [], fx: [],
      nextGroup: 120, nextRoot: 520, nextOwl: 0, event: '', eventT: 0,
      over: false, cause: '', lastLoss: 'decay',
      stats: { presses: 0, swings: 0, whiffs: 0, multi: 0, maxCombo: 0, trips: 0, owlHits: 0, owlNear: 0, mothHits: 0,
        bursts: 0, golds: 0, missed: 0, rootsPassed: 0, loss: { decay: 0, run: 0, trip: 0, owl: 0, moth: 0, whiff: 0 } },
    };
    return g;
  }

  const speedScale = g => 1 + Math.min(0.5, g.x / 30000);
  const decayScale = g => 1 + g.tick / 9000;            // x2 at 2.5 min, x3 at 5 min
  const flyLight = g => K.FLY_LIGHT * Math.max(0.5, 1 - g.tick / 36000);
  const meterFull = g => K.METER_FULL + K.METER_STEP * g.stats.bursts;
  const radius = g => g.burstT > 0 ? 220 : 34 + g.light * 0.15;
  const mult = g => 1 + Math.min(4, Math.floor(g.combo / 6));
  const flyY = (f, t) => f.baseY + f.amp * Math.sin(f.ph + t * f.freq);

  function lose(g, amount, kind) {
    const real = Math.min(g.light, amount); g.light -= amount; g.stats.loss[kind] += real; g.lastLoss = kind;
  }
  function breakCombo(g) { g.combo = 0; }

  function spawnGroup(g) {
    const r = g.r, swarm = g.event === 'swarm';
    const n = (swarm ? 5 : 3) + Math.floor(r() * (swarm ? 5 : 4));
    const high = r() < 0.28;                       // drifts above reach, dips down now and then
    const baseY = high ? 104 + r() * 10 : 128 + r() * 40;
    const amp = high ? 26 + r() * 10 : 10 + r() * 26;
    const freq = 0.025 + r() * 0.035, vx = -0.7 + r() * 1.0, ph = r() * 6.28;
    const x0 = g.camX + K.W + 20;
    const goldAt = g.tick > 600 && r() < 0.22 ? Math.floor(r() * n) : -1;
    for (let i = 0; i < n; i++) {
      const f = { x: x0 + i * (10 + r() * 10), baseY: baseY + (r() - 0.5) * 16, amp, ph: ph + i * 0.55, freq, vx, gold: i === goldAt, tw: r() * 6.28 };
      g.flies.push(f);
      if (f.gold) { g.stats.golds++; for (let m = 0; m < 2; m++) g.moths.push({ host: f, a: r() * 6.28, rr: 15 + r() * 8, va: (r() < 0.5 ? -1 : 1) * (0.06 + r() * 0.04), x: f.x, y: f.baseY }); }
    }
    g.nextGroup = g.x + (swarm ? 70 : 150) + r() * (swarm ? 70 : 120);
  }

  function spawnOwl(g) {
    const v = K.SPEED[g.gait] * speedScale(g);
    g.owls.push({ tx: g.x + v * K.OWL_WARN, t: K.OWL_WARN, done: 0 });
  }

  function catchAt(g, f, burst) {
    g.combo++; g.caught++; g.stats.maxCombo = Math.max(g.stats.maxCombo, g.combo);
    const m = mult(g);
    if (f.gold) { g.score += 5 * m; g.light += K.GOLD_LIGHT; g.meter += 5; }
    else { g.score += m; g.light += flyLight(g); g.meter += 1; }
    g.light = Math.min(K.LIGHT_MAX, g.light); g.meter = Math.min(meterFull(g), g.meter);
    g.fx.push({ kind: f.gold ? 'gold' : 'fly', x: f.x, y: f.cy, t: 0, m, burst: !!burst });
    g.moths = g.moths.filter(mo => mo.host !== f || (mo.host = null, true));
  }

  // input: { left, right } held; { press } = middle key pressed this frame.
  function step(g, input = {}) {
    if (g.over) return g;
    const r = g.r; g.tick++;
    if (input.press) g.stats.presses++;
    if (input.leftEdge || input.rightEdge) g.stats.presses++;

    // --- event director -------------------------------------------------
    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVENT_EVERY === 0) {
      g.event = EVENTS[Math.floor((g.tick - K.CALM) / K.EVENT_EVERY) % EVENTS.length]; g.eventT = K.EVENT_LEN;
      g.fx.push({ kind: 'event', name: g.event, t: 0 });
      if (g.event === 'owls') g.nextOwl = g.tick + 40;
    }
    if (g.eventT > 0 && --g.eventT === 0) g.event = '';

    // --- gait & movement -------------------------------------------------
    g.gait = input.left && !input.right ? 0 : input.right && !input.left ? 2 : 1;
    if (g.stunT > 0) { g.stunT--; }
    const moving = g.stunT === 0;
    const v = moving ? K.SPEED[g.gait] * speedScale(g) : 0;
    const prevX = g.x; g.x += v;
    g.screenX += (K.SCREEN_X[moving ? g.gait : 1] - g.screenX) * 0.06;
    g.camX = g.x - g.screenX;

    // --- light ------------------------------------------------------------
    lose(g, K.DECAY * decayScale(g), 'decay');
    if (moving && g.gait === 2) lose(g, K.RUN_COST, 'run');
    if (g.burstT > 0) g.burstT--;

    // --- swing & burst ----------------------------------------------------
    if (input.press && moving) {
      if (g.meter >= meterFull(g) && g.tick - g.lastSwingTick <= K.DOUBLE_TAP) {
        g.burstT = K.BURST_FRAMES; g.meter = 0; g.stats.bursts++; g.light = Math.min(K.LIGHT_MAX, g.light + K.BURST_LIGHT);
        g.fx.push({ kind: 'burst', t: 0 });
        for (const f of g.flies) if (!f.dead && f.x > g.camX && f.x < g.camX + K.W) { f.cy = flyY(f, g.tick); f.dead = true; catchAt(g, f, true); }
        g.moths = [];
      } else if (g.swingT === 0) {
        g.swingT = K.SWING_FRAMES; g.swingCaught = 0; g.stats.swings++;
      }
      g.lastSwingTick = g.tick;
    }
    if (g.swingT > 0) {
      const age = K.SWING_FRAMES - g.swingT;
      if (age >= K.SWING_ON && age <= K.SWING_OFF) {
        const nx = g.x + K.NET_DX, ny = K.GROUND - K.NET_DY;
        for (const f of g.flies) {
          if (f.dead) continue; const fy = flyY(f, g.tick);
          if ((f.x - nx) ** 2 + (fy - ny) ** 2 <= (K.NET_R + 3) ** 2) { f.dead = true; f.cy = fy; catchAt(g, f); g.swingCaught++; }
        }
        for (const m of g.moths) {
          if (m.dead) continue;
          if ((m.x - nx) ** 2 + (m.y - ny) ** 2 <= (K.NET_R - 4) ** 2) { m.dead = true; lose(g, K.MOTH_LOSS, 'moth'); breakCombo(g); g.meter = Math.max(0, g.meter - 5); g.stats.mothHits++; g.fx.push({ kind: 'moth', x: m.x, y: m.y, t: 0 }); }
        }
      }
      if (--g.swingT === 0) {
        if (g.swingCaught === 0) { g.stats.whiffs++; breakCombo(g); lose(g, K.WHIFF_LOSS, 'whiff'); }
        if (g.swingCaught >= 3) { g.stats.multi++; g.light = Math.min(K.LIGHT_MAX, g.light + 60); g.fx.push({ kind: 'multi', n: g.swingCaught, x: g.x + K.NET_DX, y: K.GROUND - 80, t: 0 }); }
      }
    }

    // --- flies & moths ----------------------------------------------------
    const wind = g.event === 'wind';
    for (const f of g.flies) { f.x += f.vx + (wind ? -1.1 : 0); if (wind) f.ph += 0.02; }
    for (const f of g.flies) if (!f.dead && f.x < g.camX - 24) { f.dead = true; g.stats.missed++; }
    g.flies = g.flies.filter(f => !f.dead);
    for (const m of g.moths) {
      if (m.host && !g.flies.includes(m.host)) m.host = null;
      m.a += m.va;
      if (m.host) { m.x = m.host.x + Math.cos(m.a) * m.rr; m.y = flyY(m.host, g.tick) + Math.sin(m.a) * m.rr * 0.8; }
      else { m.x += -0.4 + Math.cos(m.a) * 0.8; m.y += Math.sin(m.a * 1.3) * 0.7; }
    }
    g.moths = g.moths.filter(m => !m.dead && m.x > g.camX - 30);
    if (g.x >= g.nextGroup) spawnGroup(g);

    // --- roots (only dangerous at a run) -----------------------------------
    if (g.x >= g.nextRoot) {
      g.roots.push({ x: g.camX + K.W + 30, w: 10 + Math.floor(r() * 8), hit: false });
      g.nextRoot = g.x + 230 + r() * Math.max(140, 380 - g.x / 120);
    }
    const foot = g.x + 4, prevFoot = prevX + 4;
    for (const rt of g.roots) {
      if (rt.hit || rt.passed) continue;
      if (prevFoot < rt.x && foot >= rt.x) {
        if (g.gait === 2 && moving) {
          rt.hit = true; g.stunT = K.TRIP_STUN; g.stunKind = 'trip'; g.stats.trips++; lose(g, K.TRIP_LOSS, 'trip'); breakCombo(g);
          g.fx.push({ kind: 'trip', x: g.x, t: 0 });
        } else { rt.passed = true; g.stats.rootsPassed++; }
      }
    }
    g.roots = g.roots.filter(rt => rt.x > g.camX - 40);

    // --- owls ---------------------------------------------------------------
    const owlsActive = g.event === 'owls' || (g.tick > 3600 && r() < 0.0012);
    if (g.event === 'owls' && g.tick >= g.nextOwl) { spawnOwl(g); g.nextOwl = g.tick + 110 + Math.floor(r() * 40); }
    else if (g.event !== 'owls' && owlsActive && g.owls.length === 0) spawnOwl(g);
    for (const o of g.owls) {
      o.t--;
      if (o.t === 0) {
        const d = Math.abs(g.x - o.tx);
        if (d < K.OWL_HIT && g.burstT === 0) { lose(g, K.OWL_LOSS, 'owl'); g.stunT = Math.max(g.stunT, K.OWL_STUN); g.stunKind = 'owl'; g.stats.owlHits++; breakCombo(g); g.fx.push({ kind: 'owlhit', x: g.x, t: 0 }); }
        else if (d < K.OWL_NEAR) { g.stats.owlNear++; g.fx.push({ kind: 'near', x: g.x, t: 0 }); }
      }
      if (o.t < -40) o.done = 1;
    }
    g.owls = g.owls.filter(o => !o.done);

    for (const e of g.fx) e.t++;
    g.fx = g.fx.filter(e => e.t < 70);

    if (g.light <= 0) { g.light = 0; g.over = true; g.cause = g.lastLoss; }
    return g;
  }

  const api = { K, start, step, radius, mult, flyY, meterFull };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvNightV2 = api;
})(typeof window !== 'undefined' ? window : globalThis);
