// POST V2「邮政快车」rules reference (G1): integer 60 Hz, mulberry32, landscape 320x240.
// Side view, the train runs right on one line. Speed is the game: faster = higher multiplier and more stations
// reached before the timetable runs out, but speed limits, red signals and animals punish a driver who cannot brake.
// Mail moves without stopping, like the old railway mail cranes: tap to throw a bag into a station net,
// or to snatch a hanging bag from a crane.
// Keys (landscape, left to right): OK = hold to brake, DOWN = tap to throw/catch, UP = hold for steam (accelerate).
// Long-press DOWN is the shell's pause; the action fires on the press edge, so nothing needs DOWN held.
// Firmware does NOT follow this yet: V1 (two tracks, mail colours, OK tap/hold) is still adv_post.c.
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, RAIL: 196, LOCO_X: 150, DOOR_X: 120, FRONT_X: 196,
    VMAX: 1024, ACC: 7, BRAKE: 18, DRAG: 1, V0: 300,
    WINDOW: 14, PERFECT: 4, COOL: 10,
    BAGS0: 3, BAGS_MAX: 5,
    TIME_NET: 85, TIME_PERFECT: 30, TIME_CRANE: 25, TIME_SKIP: 40, TIME_RED: 160, TIME_DERAIL: 180, TIME_ANIMAL: 130, TIME_WASTE: 20,
    DRAIN: 28, DRAIN_RAMP: 1800, DRAIN_MAX: 14,
    PTS: 10, CRANE_PTS: 15, SLOW: 260, OVER_GRACE: 24, STUN: 50,
    EVENTS: 16, AHEAD: 380, CULL: -80,
    CALM: 900, EVERY: 1500, SECTION_LEN: 900,
  };
  const T = { NET: 1, CRANE: 2, LIMIT: 3, SIGNAL: 4, ANIMAL: 5 };
  const SEC = { NONE: 0, TOWN: 1, HILLS: 2, FARM: 3, NIGHT: 4, DOWNHILL: 5 };
  const FX = { NET: 1, PERFECT: 2, CRANE: 3, WASTE: 4, SKIP: 5, RED: 6, DERAIL: 7, ANIMAL: 8, SECTION: 9, OVER: 10, NEAR: 11, TIER: 12 };
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n, tr = Math.trunc, px = q => q >> 8;

  function start(seed) {
    return { rng: seed >>> 0, tick: 0, score: 0, res: 1000, over: 0, cue: 0, v: K.V0, dist: 0, bags: K.BAGS0, cool: 0, stun: 0,
      braking: 0, steaming: 0, combo: 0, best: 0, bonus: 0, drainAcc: 0, over_t: 0, zone: 0, tier: 1,
      delivered: 0, perfects: 0, cranes: 0, wasted: 0, skipped: 0, reds: 0, derails: 0, animals: 0, nearMiss: 0, nets: 0,
      section: 0, sectionT: 0, nextEvent: 360, presses: 0, blocked: 0, fxHead: 0, meters: 0, topSpeedT: 0,
      ev: Array.from({ length: K.EVENTS }, () => ({ type: 0, x: 0, a: 0, b: 0, t: 0, done: 0 })),
      fx: Array.from({ length: 6 }, () => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
  }
  const cam = g => px(g.dist);                       // world x at screen x = 0
  const tierOf = v => (v >= 720 ? 3 : v >= 420 ? 2 : 1);
  const mult = g => tierOf(g.v) + Math.min(3, tr(g.combo / 4));
  const kmh = v => tr(v * 120 / K.VMAX);              // what the speedometer shows (0..120)
  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % 6; }
  function slot(g) { const e = g.ev.find(e => !e.type); if (!e) g.blocked++; return e; }
  function clear(e) { e.type = e.x = e.a = e.b = e.t = e.done = 0; }

  // One event per spawn, spaced along the line. A limit zone reserves its own stretch so nothing else starts inside it
  // except nets and cranes (a slow zone with a station is a breather, not a trap).
  function spawn(g, x) {
    const s = g.section, v = rnd(g, 100), e = slot(g);
    let type;
    const w = s === SEC.TOWN ? [44, 26, 8, 14, 8] : s === SEC.HILLS ? [26, 20, 36, 9, 9] : s === SEC.FARM ? [26, 20, 9, 9, 36]
      : s === SEC.NIGHT ? [30, 22, 12, 26, 10] : [34, 24, 18, 12, 12];
    let acc = 0; type = 1; for (let i = 0; i < 5; i++) { acc += w[i]; if (v < acc) { type = i + 1; break; } }
    if (g.tick < 600 && (type === T.SIGNAL || type === T.ANIMAL)) type = T.NET;      // first ten seconds: just learn the throw
    if (e) {
      if (type === T.LIMIT) Object.assign(e, { type, x, a: 360 + rnd(g, 5) * 60, b: 160 + rnd(g, 120), t: 0, done: 0 });       // a = limit (Q8), b = zone length px
      else if (type === T.SIGNAL) Object.assign(e, { type, x, a: 50 + rnd(g, 130), b: 0, t: -1, done: 0 });                   // a = frames red after it comes on screen; t = tick it appeared
      else if (type === T.ANIMAL) Object.assign(e, { type, x, a: 80 + rnd(g, 120), b: rnd(g, 2), t: -1, done: 0 });           // a = frames on the track after it appears; b = sheep/cow
      else { Object.assign(e, { type, x, a: type === T.NET ? rnd(g, 4) : 0, b: 0, t: 0, done: 0 }); if (type === T.NET) g.nets++; }
    }
    const gap = (s === SEC.TOWN ? 110 : 140) + rnd(g, 120) + (type === T.LIMIT && e ? e.b : 0);
    g.nextEvent = x + gap;
  }

  function lose(g, kind, time, x) {
    g.res -= time; g.combo = 0; g.cue = 7; fx(g, kind, x, K.RAIL - 60, time);
  }

  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 60) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);
    if (g.cool > 0) g.cool--;

    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVERY === 0) { g.section = 1 + tr((g.tick - K.CALM) / K.EVERY) % 5; g.sectionT = K.SECTION_LEN; fx(g, FX.SECTION, 160, 100, g.section); }
    if (g.sectionT > 0 && --g.sectionT === 0) g.section = 0;

    // throttle and brake
    g.braking = input.ok_held && !input.up_held ? 1 : 0; g.steaming = input.up_held && !input.ok_held ? 1 : 0;
    if (g.stun > 0) { g.stun--; g.v = Math.max(0, g.v - K.BRAKE); }
    else if (g.braking) g.v = Math.max(0, g.v - K.BRAKE);
    else if (g.steaming) g.v = Math.min(K.VMAX, g.v + K.ACC);
    else g.v = Math.max(0, g.v - K.DRAG + (g.section === SEC.DOWNHILL ? 3 : 0));
    g.v = Math.min(K.VMAX, g.v);
    const t1 = tierOf(g.v); if (t1 > g.tier) fx(g, FX.TIER, K.LOCO_X, K.RAIL - 96, t1); g.tier = t1;
    if (g.v >= 720) g.topSpeedT++;
    g.dist += g.v;
    const c = cam(g);

    // timetable: always ticking, faster later
    g.drainAcc += K.DRAIN + Math.min(K.DRAIN_MAX, tr(g.tick / K.DRAIN_RAMP));
    while (g.drainAcc >= 60) { g.res--; g.drainAcc -= 60; }

    // throw / catch on the press edge: the nearest net or crane to the mail door decides
    if (input.down_down && !g.cool && !g.stun) {
      g.cool = K.COOL;
      let best = null, bd = 1e9;
      for (const e of g.ev) if ((e.type === T.NET || e.type === T.CRANE) && !e.done) { const d = Math.abs(e.x - c - K.DOOR_X); if (d < bd) { bd = d; best = e; } }
      if (best && bd <= K.WINDOW) {
        best.done = 1;
        if (best.type === T.NET) {
          if (g.bags > 0) {
            g.bags--; g.delivered++; g.combo++; if (g.combo > g.best) g.best = g.combo;
            const perfect = bd <= K.PERFECT, pts = K.PTS * mult(g) * (perfect ? 2 : 1);
            g.bonus += pts; g.res = Math.min(1000, g.res + K.TIME_NET + (perfect ? K.TIME_PERFECT : 0)); if (perfect) g.perfects++;
            fx(g, perfect ? FX.PERFECT : FX.NET, best.x - c, K.RAIL - 54, pts); g.cue = 6;
          } else { best.done = 0; }        // no bag: the net stays open; nothing thrown
        } else {
          g.bags = Math.min(K.BAGS_MAX, g.bags + 1); g.cranes++; const pts = K.CRANE_PTS * tierOf(g.v);
          g.bonus += pts; g.res = Math.min(1000, g.res + K.TIME_CRANE); fx(g, FX.CRANE, best.x - c, K.RAIL - 70, pts); g.cue = 6;
        }
      } else if (best && bd <= K.WINDOW * 4 && g.bags > 0 && best.type === T.NET) {
        g.bags--; g.wasted++; lose(g, FX.WASTE, K.TIME_WASTE, K.DOOR_X);   // threw too early/late: the bag lands in the grass
      }
    }

    // world events
    g.zone = 0;
    for (const e of g.ev) {
      if (!e.type) continue;
      const sx = e.x - c;
      if (e.type === T.LIMIT && e.x + e.b - c < K.CULL || e.type !== T.LIMIT && sx < K.CULL) { clear(e); continue; }
      if ((e.type === T.SIGNAL || e.type === T.ANIMAL) && e.t < 0 && sx < K.W + 10) e.t = g.tick;
      if (e.type === T.NET) {
        if (!e.done && sx < K.DOOR_X - K.WINDOW) { e.done = 2; if (g.bags > 0) { g.skipped++; lose(g, FX.SKIP, K.TIME_SKIP, K.DOOR_X - 30); } }
      } else if (e.type === T.CRANE) {
        if (!e.done && sx < K.DOOR_X - K.WINDOW) e.done = 2;
      } else if (e.type === T.LIMIT) {
        if (sx <= K.FRONT_X && e.x + e.b - c >= K.LOCO_X - 48) {
          g.zone = e.a;
          if (g.v > e.a + 24) {
            if (++g.over_t === 1) fx(g, FX.OVER, K.LOCO_X, K.RAIL - 96, kmh(e.a));
            if (g.over_t >= K.OVER_GRACE && !e.done) { e.done = 1; g.derails++; g.stun = K.STUN; lose(g, FX.DERAIL, K.TIME_DERAIL, K.LOCO_X); g.over_t = 0; }
          } else g.over_t = 0;
        }
      } else if (e.type === T.SIGNAL) {
        const red = e.t >= 0 && g.tick - e.t < e.a;
        if (!e.done && sx <= K.FRONT_X) {
          e.done = 1;
          if (red && g.v > K.SLOW) { g.reds++; lose(g, FX.RED, K.TIME_RED, K.FRONT_X); g.v = tr(g.v / 2); }
          else if (red) { g.nearMiss++; fx(g, FX.NEAR, K.FRONT_X, K.RAIL - 80, 0); }
        }
      } else if (e.type === T.ANIMAL) {
        const on = e.t >= 0 && g.tick - e.t < e.a;
        if (!e.done && sx <= K.FRONT_X + 4 && sx >= K.FRONT_X - 40) {
          if (on) { e.done = 1; g.animals++; g.v = tr(g.v / 3); lose(g, FX.ANIMAL, K.TIME_ANIMAL, K.FRONT_X); }
          else { e.done = 1; if (g.tick - e.t - e.a < 40) { g.nearMiss++; fx(g, FX.NEAR, K.FRONT_X, K.RAIL - 80, 0); } }
        }
      }
    }
    if (!g.zone) g.over_t = 0;

    while (g.nextEvent < c + K.W + K.AHEAD - 320 + 160) spawn(g, g.nextEvent);
    g.meters = tr(px(g.dist) / 4);
    g.score = tr(g.meters / 40) + g.bonus;
    if (g.res <= 0) { g.res = 0; g.over = 1; g.cue = 8; }
    return g;
  }

  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'v', 'dist', 'bags', 'cool', 'stun', 'braking', 'steaming', 'combo', 'best', 'bonus',
    'drainAcc', 'over_t', 'zone', 'tier', 'delivered', 'perfects', 'cranes', 'wasted', 'skipped', 'reds', 'derails', 'animals', 'nearMiss', 'nets',
    'section', 'sectionT', 'nextEvent', 'presses', 'blocked', 'fxHead', 'meters', 'topSpeedT'];
  function view(g) {
    const out = HEAD.map(k => g[k]);
    for (const e of g.ev) out.push(e.type, e.x, e.a, e.b, e.t, e.done);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }
  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, T, SEC, FX, HEAD, start, step, status, view, random, mult, tierOf, kmh, cam };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvPostV2 = api;
})(typeof window !== 'undefined' ? window : globalThis);
