// NIGHT V2「萤火虫之夜」rules reference (V1 lives in git history before 2026-10-26): integer 60 Hz, mulberry32, landscape 320x240.
// firmware/main/adv_night.c follows this file step by step (tests/night_golden). World x is
// 1/256 px (Q8); light is 1/1000 of the shell resource (0..1,000,000).
// Keys (landscape, left to right): OK = hold to slow, DOWN = swing / double tap burst, UP = hold to run.
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, GROUND: 200, FLIES: 40, MOTHS: 12, ROOTS: 6, OWLS: 4, FX: 6,
    SPEED: [141, 294, 563], SCREEN: [78, 112, 156],
    LIGHT_MAX: 1000000, LIGHT_START: 720000, DECAY: 420, DECAY_RAMP: 5400, RUN_COST: 220,
    FLY_LIGHT: 36000, FLY_LIGHT_MIN: 18000, GOLD_LIGHT: 150000, MULTI_LIGHT: 60000,
    WHIFF: 16000, MOTH: 120000, TRIP: 130000, OWL: 200000, BURST_LIGHT: 160000,
    SWING: 18, SWING_ON: 3, SWING_OFF: 12, NET_DX: 20, NET_DY: 42, NET_R: 31, MOTH_R: 24,
    METER: 30, METER_STEP: 12, BURST: 150, DOUBLE: 16,
    TRIP_STUN: 54, OWL_STUN: 30, OWL_WARN: 96, OWL_HIT: 18, OWL_NEAR: 44,
    CALM: 900, EVERY: 1500, EVENT_LEN: 480,
  };
  const EV = { NONE: 0, SWARM: 1, OWLS: 2, WIND: 3 };
  const FX = { FLY: 1, GOLD: 2, MULTI: 3, MOTH: 4, TRIP: 5, OWL: 6, NEAR: 7, BURST: 8, EVENT: 9 };
  const LOSS = { DECAY: 0, RUN: 1, WHIFF: 2, MOTH: 3, TRIP: 4, OWL: 5 };
  const QSIN = [0,101,201,301,401,501,601,700,799,897,995,1092,1189,1285,1380,1474,1567,1660,1751,1842,1931,2019,2106,2191,2276,2359,2440,2520,2598,2675,2751,2824,2896,2967,3035,3102,3166,3229,3290,3349,3406,3461,3513,3564,3612,3659,3703,3745,3784,3822,3857,3889,3920,3948,3973,3996,4017,4036,4052,4065,4076,4085,4091,4095,4096];
  function isin(i) { i &= 255; return i < 64 ? QSIN[i] : i < 128 ? QSIN[128 - i] : i < 192 ? -QSIN[i - 128] : -QSIN[256 - i]; }
  const icos = i => isin(i + 64);
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n;
  const tr = Math.trunc;

  const blank = n => Array.from({ length: n }, () => null);
  function start(seed) {
    const g = { rng: seed >>> 0, tick: 0, score: 0, res: 720, over: 0, cue: 0, light: K.LIGHT_START, x: 0, screen: K.SCREEN[1] << 8,
      gait: 1, stun: 0, stunKind: 0, swing: 0, swingCaught: 0, lastSwing: -1000, burst: 0, combo: 0, caught: 0, meter: 0, bursts: 0,
      event: 0, eventT: 0, nextGroup: 120 << 8, nextRoot: 520 << 8, nextOwl: 0, lastLoss: 0, maxCombo: 0, whiffs: 0, trips: 0,
      owlHits: 0, owlNear: 0, mothHits: 0, missed: 0, golds: 0, multi: 0, swings: 0, presses: 0, rootsPassed: 0, blocked: 0, fxHead: 0,
      loss: [0, 0, 0, 0, 0, 0],
      flies: blank(K.FLIES).map(() => ({ type: 0, x: 0, baseY: 0, amp: 0, ph: 0, freq: 0, vx: 0 })),
      moths: blank(K.MOTHS).map(() => ({ host: 0, x: 0, y: 0, a: 0, rr: 0, va: 0 })),
      roots: blank(K.ROOTS).map(() => ({ x: 0, w: 0, state: 0 })),
      owls: blank(K.OWLS).map(() => ({ tx: 0, t: 0, live: 0 })),
      fx: blank(K.FX).map(() => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
    return g;
  }

  const camX = g => g.x - g.screen;
  const px = q => q >> 8;
  const speedOf = (g, gait) => tr(K.SPEED[gait] * (30000 + Math.min(15000, px(g.x))) / 30000);
  const decay = g => tr(K.DECAY * (K.DECAY_RAMP + Math.min(g.tick, 1000000)) / K.DECAY_RAMP);
  const radius = g => g.burst > 0 ? 220 : 34 + tr(g.light * 15 / 100000);
  const mult = g => 1 + Math.min(4, tr(g.combo / 6));
  const meterFull = g => K.METER + K.METER_STEP * g.bursts;
  const flyY = (f, tick) => f.baseY + tr(f.amp * isin(((f.ph + Math.imul(tick, f.freq)) >>> 8)) / 4096);

  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % K.FX; }
  function lose(g, amount, kind) { g.loss[kind] += Math.min(Math.max(g.light, 0), amount); g.light -= amount; g.lastLoss = kind; }
  function gain(g, amount) { g.light = Math.min(K.LIGHT_MAX, g.light + amount); }
  function detach(g, slot) { for (const m of g.moths) if (m.host === slot + 1) m.host = 0; }

  function spawnGroup(g) {
    const swarm = g.event === EV.SWARM;
    const n = (swarm ? 5 : 3) + rnd(g, swarm ? 5 : 4), high = rnd(g, 100) < 28;
    const baseY = high ? 104 + rnd(g, 11) : 128 + rnd(g, 41), amp = high ? 26 + rnd(g, 11) : 10 + rnd(g, 27);
    const freq = 261 + rnd(g, 363), vx = -179 + rnd(g, 257), ph = rnd(g, 65536);
    const goldAt = g.tick > 600 && rnd(g, 100) < 22 ? rnd(g, n) : -1;
    let x = camX(g) + (340 << 8);
    for (let i = 0; i < n; i++) {
      const dy = rnd(g, 17) - 8, gap = 10 + rnd(g, 11), gold = i === goldAt;
      const slot = g.flies.findIndex(f => !f.type);
      if (slot < 0) { g.blocked++; x += gap << 8; continue; }
      Object.assign(g.flies[slot], { type: gold ? 2 : 1, x, baseY: baseY + dy, amp, ph: (ph + i * 5734) & 0xffff, freq, vx });
      x += gap << 8;
      if (gold) {
        g.golds++;
        for (let k = 0; k < 2; k++) {
          const a = rnd(g, 65536), rr = 15 + rnd(g, 9), va = (rnd(g, 2) ? -1 : 1) * (626 + rnd(g, 417));
          const m = g.moths.find(o => !o.host && !o.rr);
          if (m) Object.assign(m, { host: slot + 1, x: g.flies[slot].x, y: (baseY + dy) << 8, a, rr, va });
        }
      }
    }
    g.nextGroup = g.x + (((swarm ? 70 : 150) + rnd(g, swarm ? 71 : 121)) << 8);
  }

  function spawnOwl(g) {
    const o = g.owls.find(e => !e.live); if (!o) { g.blocked++; return; }
    Object.assign(o, { tx: g.x + speedOf(g, g.gait) * K.OWL_WARN, t: K.OWL_WARN, live: 1 });
  }

  function catchFly(g, slot, burst) {
    const f = g.flies[slot], y = flyY(f, g.tick);
    g.combo++; g.caught++; if (g.combo > g.maxCombo) g.maxCombo = g.combo;
    const m = mult(g);
    if (f.type === 2) { g.score += 5 * m; gain(g, K.GOLD_LIGHT); g.meter += 5; fx(g, FX.GOLD, px(f.x), y, 5 * m); }
    else { g.score += m; gain(g, Math.max(K.FLY_LIGHT_MIN, K.FLY_LIGHT - g.tick)); g.meter += 1; if (!burst) fx(g, FX.FLY, px(f.x), y, m); }
    g.meter = Math.min(meterFull(g), g.meter);
    f.type = 0; detach(g, slot);
  }

  function upEvent() {}       // V2: UP is the run key; leaving for the map happens from the pause page

  // input: adv_input_t fields (ok_held = slow, up_held = run, down_down = swing press).
  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 60) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);

    // event director
    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVERY === 0) {
      g.event = 1 + tr((g.tick - K.CALM) / K.EVERY) % 3; g.eventT = K.EVENT_LEN; fx(g, FX.EVENT, 0, 0, g.event);
      if (g.event === EV.OWLS) g.nextOwl = g.tick + 40;
    }
    if (g.eventT > 0 && --g.eventT === 0) g.event = 0;

    // gait and movement
    const left = !!input.ok_held, right = !!input.up_held;
    g.gait = left && !right ? 0 : right && !left ? 2 : 1;
    if (g.stun > 0) g.stun--;
    const moving = g.stun === 0, prevFoot = px(g.x) + 4;
    if (moving) g.x += speedOf(g, g.gait);
    g.screen += tr(((K.SCREEN[moving ? g.gait : 1] << 8) - g.screen) * 15 / 256);

    // light
    lose(g, decay(g), LOSS.DECAY);
    if (moving && g.gait === 2) lose(g, K.RUN_COST, LOSS.RUN);
    if (g.burst > 0) g.burst--;

    // swing and burst
    if (input.down_down && moving) {
      if (g.meter >= meterFull(g) && g.tick - g.lastSwing <= K.DOUBLE) {
        g.burst = K.BURST; g.meter = 0; g.bursts++; gain(g, K.BURST_LIGHT); fx(g, FX.BURST, 0, 0, 0); g.cue = 6;
        const lo = camX(g), hi = lo + (K.W << 8);
        for (let i = 0; i < K.FLIES; i++) { const f = g.flies[i]; if (f.type && f.x > lo && f.x < hi) catchFly(g, i, true); }
        for (const m of g.moths) Object.assign(m, { host: 0, x: 0, y: 0, a: 0, rr: 0, va: 0 });
      } else if (g.swing === 0) { g.swing = K.SWING; g.swingCaught = 0; g.swings++; }
      g.lastSwing = g.tick;
    }
    if (g.swing > 0) {
      const age = K.SWING - g.swing;
      if (age >= K.SWING_ON && age <= K.SWING_OFF) {
        const nx = px(g.x) + K.NET_DX, ny = K.GROUND - K.NET_DY;
        for (let i = 0; i < K.FLIES; i++) {
          const f = g.flies[i]; if (!f.type) continue;
          const dx = px(f.x) - nx, dy = flyY(f, g.tick) - ny;
          if (dx * dx + dy * dy <= K.NET_R * K.NET_R) { catchFly(g, i, false); g.swingCaught++; g.cue = 6; }
        }
        for (const m of g.moths) {
          if (!m.rr) continue;
          const dx = px(m.x) - nx, dy = px(m.y) - ny;
          if (dx * dx + dy * dy <= K.MOTH_R * K.MOTH_R) {
            fx(g, FX.MOTH, px(m.x), px(m.y), 0); Object.assign(m, { host: 0, x: 0, y: 0, a: 0, rr: 0, va: 0 });
            lose(g, K.MOTH, LOSS.MOTH); g.combo = 0; g.meter = Math.max(0, g.meter - 5); g.mothHits++; g.cue = 7;
          }
        }
      }
      if (--g.swing === 0) {
        if (g.swingCaught === 0) { g.whiffs++; g.combo = 0; lose(g, K.WHIFF, LOSS.WHIFF); }
        if (g.swingCaught >= 3) { g.multi++; gain(g, K.MULTI_LIGHT); fx(g, FX.MULTI, px(g.x) + K.NET_DX, K.GROUND - 80, g.swingCaught); }
      }
    }

    // flies and moths
    const wind = g.event === EV.WIND, cull = camX(g) - (24 << 8);
    for (let i = 0; i < K.FLIES; i++) {
      const f = g.flies[i]; if (!f.type) continue;
      f.x += f.vx + (wind ? -282 : 0); if (wind) f.ph = (f.ph + 209) & 0xffff;
      if (f.x < cull) { f.type = 0; g.missed++; detach(g, i); }
    }
    const mcull = camX(g) - (30 << 8);
    for (const m of g.moths) {
      if (!m.rr) continue;
      m.a = (m.a + m.va) & 0xffff;
      const ai = m.a >> 8;
      if (m.host) { const h = g.flies[m.host - 1]; m.x = h.x + tr(icos(ai) * m.rr / 16); m.y = (flyY(h, g.tick) << 8) + tr(isin(ai) * m.rr / 20); }
      else { m.x += -102 + tr(icos(ai) * 205 / 4096); m.y += tr(isin(ai * 13 / 10 | 0) * 179 / 4096); }
      if (m.x < mcull) Object.assign(m, { host: 0, x: 0, y: 0, a: 0, rr: 0, va: 0 });
    }
    if (g.x >= g.nextGroup) spawnGroup(g);

    // roots: only dangerous at a run
    if (g.x >= g.nextRoot) {
      const w = 10 + rnd(g, 8), r = g.roots.find(e => !e.state);
      if (r) Object.assign(r, { x: px(camX(g)) + 350, w, state: 1 }); else g.blocked++;
      g.nextRoot = g.x + ((230 + rnd(g, Math.max(140, 380 - tr(px(g.x) / 120)))) << 8);
    }
    const foot = px(g.x) + 4;
    for (const r of g.roots) {
      if (r.state === 1 && prevFoot < r.x && foot >= r.x) {
        if (g.gait === 2 && moving) {
          r.state = 2; g.stun = K.TRIP_STUN; g.stunKind = 1; g.trips++; lose(g, K.TRIP, LOSS.TRIP); g.combo = 0; g.cue = 7;
          fx(g, FX.TRIP, px(g.x), K.GROUND - 70, 0);
        } else { r.state = 3; g.rootsPassed++; }
      }
      if (r.state && r.x < px(camX(g)) - 40) Object.assign(r, { x: 0, w: 0, state: 0 });
    }

    // owls
    if (g.event === EV.OWLS) { if (g.tick >= g.nextOwl) { spawnOwl(g); g.nextOwl = g.tick + 110 + rnd(g, 41); } }
    else if (g.tick > 3600 && !g.owls.some(o => o.live) && rnd(g, 10000) < 12) spawnOwl(g);
    for (const o of g.owls) {
      if (!o.live) continue;
      if (--o.t === 0) {
        const d = Math.abs(g.x - o.tx);
        if (d < K.OWL_HIT << 8 && g.burst === 0) {
          lose(g, K.OWL, LOSS.OWL); g.stun = Math.max(g.stun, K.OWL_STUN); g.stunKind = 2; g.owlHits++; g.combo = 0; g.cue = 7;
          fx(g, FX.OWL, px(g.x), K.GROUND - 72, 0);
        } else if (d < K.OWL_NEAR << 8) { g.owlNear++; fx(g, FX.NEAR, px(g.x), K.GROUND - 72, 0); }
      }
      if (o.t < -40) Object.assign(o, { tx: 0, t: 0, live: 0 });
    }

    if (g.light <= 0) { g.light = 0; g.over = 1; g.cue = 8; }
    g.res = tr((g.light + 999) / 1000);
    return g;
  }

  // Flat state in the C struct order (tests/night_golden, tests/test_adv_night.py).
  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'light', 'x', 'screen', 'gait', 'stun', 'stunKind', 'swing', 'swingCaught',
    'lastSwing', 'burst', 'combo', 'caught', 'meter', 'bursts', 'event', 'eventT', 'nextGroup', 'nextRoot', 'nextOwl', 'lastLoss',
    'maxCombo', 'whiffs', 'trips', 'owlHits', 'owlNear', 'mothHits', 'missed', 'golds', 'multi', 'swings', 'presses', 'rootsPassed',
    'blocked', 'fxHead'];
  function view(g) {
    const out = HEAD.map(k => g[k]);
    out.push(...g.loss);
    for (const f of g.flies) out.push(f.type, f.x, f.baseY, f.amp, f.ph, f.freq, f.vx);
    for (const m of g.moths) out.push(m.host, m.x, m.y, m.a, m.rr, m.va);
    for (const r of g.roots) out.push(r.x, r.w, r.state);
    for (const o of g.owls) out.push(o.tx, o.t, o.live);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }

  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, EV, FX, LOSS, HEAD, start, step, status, upEvent, view, random, isin, icos, radius, mult, meterFull, flyY, speedOf, camX };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvNight = api;
})(typeof window !== 'undefined' ? window : globalThis);
