// SKI V2「雪崩速降」rules reference: integer 60 Hz, mulberry32, landscape 320x240. firmware/main/adv_ski.c
// follows it step by step (tests/ski_golden). V1 (portrait rear view) lives in git history before 2026-10-26 14:27.
// NABO skis down the screen (three-quarter front art), an avalanche chases from above.
// World y grows downhill in Q8 px; x is Q8 screen px (no horizontal scroll).
// Keys (landscape, left to right): OK = hold to carve left, DOWN = jump / spin in the air, UP = hold to carve right.
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, NABO_Y: 92, LEFT: 18, RIGHT: 302, OBJS: 28, AHEAD: 200, CULL: 110,
    STEER: 26, VX_MAX: 600, V0: 470, FLOW_MAX: 520, FLOW_GATE: 85, FLOW_SPIN: 70, ACCEL: 8, DRAG_DIV: 40,
    GATE_HALF: 21, GATE_BOOST: 110, GATE_PUSH: 26, MISS_PULL: 20,
    TREE_R: 11, PINE_R: 9, MOGUL_R: 11, KICK_HALF: 18, DRIFT_HALF: 14, ICE_HALF: 34, ICE_LEN: 60,
    HOP: 26, KICK_AIR: 72, SPIN: 22, SPIN_PTS: 50, SPIN_PUSH: 18,
    CRASH: 36, STUMBLE: 20, INVULN: 50,
    AVAL0: 340, AVAL_RAMP: 460, AVAL_DIV: 12, AVAL_CAP: 300, AVAL_START: 200,
    CALM: 900, EVERY: 1500, SECTION_LEN: 600,
  };
  const T = { GATE_RED: 1, GATE_BLUE: 2, TREE: 3, PINE: 4, MOGUL: 5, KICKER: 6, ICE: 7, DRIFT: 8 };
  const SEC = { NONE: 0, SLALOM: 1, FOREST: 2, PARK: 3, ICE: 4, FOG: 5 };
  const FX = { GATE: 1, MISS: 2, CRASH: 3, STUMBLE: 4, SPIN: 5, LAND: 6, WIPE: 7, SECTION: 8, KICK: 9, NEAR: 10 };
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n, tr = Math.trunc, px = q => q >> 8;

  function start(seed) {
    return { rng: seed >>> 0, tick: 0, score: 0, res: 0, over: 0, cue: 0, x: 160 << 8, vx: 0, y: 0, v: K.V0, air: 0, airMax: 0,
      kicked: 0, spinT: 0, spins: 0, crash: 0, invuln: 0, aval: -(K.AVAL_START << 8), combo: 0, best: 0, gates: 0, passed: 0, misses: 0,
      tricks: 0, flow: 0, crashes: 0, stumbles: 0, nearMiss: 0, nextGate: 260, nextRow: 140, lastGateX: 160, section: 0, sectionT: 0,
      onIce: 0, meters: 0, bonus: 0, presses: 0, blocked: 0, fxHead: 0,
      objs: Array.from({ length: K.OBJS }, () => ({ type: 0, x: 0, y: 0, done: 0 })),
      fx: Array.from({ length: 6 }, () => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
  }
  const mult = g => 1 + Math.min(4, tr(g.combo / 4));
  const gap = g => g.y - g.aval;
  const avalSpeed = g => K.AVAL0 + Math.min(K.AVAL_RAMP, tr(g.tick / K.AVAL_DIV));
  const vTarget = g => K.V0 + g.flow;
  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % 6; }
  function slot(g) { const o = g.objs.find(e => !e.type); if (!o) g.blocked++; return o; }
  function nearGate(g, y, x) { return g.objs.some(o => o.type && o.type <= 2 && Math.abs(o.y - y) < 44 && Math.abs(o.x - x) < 46); }

  function spawnGate(g, y) {
    const slalom = g.section === SEC.SLALOM, swing = slalom ? 110 : 80;
    const lo = Math.max(48, g.lastGateX - swing), hi = Math.min(272, g.lastGateX + swing), x = lo + rnd(g, hi - lo + 1);
    const o = slot(g); if (o) Object.assign(o, { type: g.gates & 1 ? T.GATE_BLUE : T.GATE_RED, x, y, done: 0 });
    g.lastGateX = x; g.gates++;
    g.nextGate = y + (slalom ? 110 : 170) + rnd(g, slalom ? 50 : 90);
  }
  function spawnRow(g, y) {
    const s = g.section, n = 1 + rnd(g, s === SEC.FOREST ? 4 : 3);
    for (let i = 0; i < n; i++) {
      const v = rnd(g, 100), x = K.LEFT + rnd(g, K.RIGHT - K.LEFT), dy = rnd(g, 30);
      let type;
      if (s === SEC.PARK) type = v < 35 ? T.KICKER : v < 60 ? T.MOGUL : v < 80 ? T.PINE : T.TREE;
      else if (s === SEC.FOREST) type = v < 60 ? T.TREE : v < 85 ? T.PINE : T.MOGUL;
      else if (s === SEC.ICE) type = v < 40 ? T.ICE : v < 70 ? T.TREE : T.DRIFT;
      else type = v < 40 ? T.TREE : v < 58 ? T.PINE : v < 74 ? T.MOGUL : v < 86 ? T.DRIFT : v < 94 ? T.KICKER : T.ICE;
      if (nearGate(g, y + dy, x)) continue;
      const o = slot(g); if (o) Object.assign(o, { type, x, y: y + dy, done: 0 });
    }
    g.nextRow = y + (s === SEC.FOREST ? 34 : 46) + rnd(g, 40);
  }

  function crash(g, kind) {
    g.crash = kind === FX.CRASH ? K.CRASH : K.STUMBLE; g.v = kind === FX.CRASH ? 0 : tr(g.v / 2); g.vx = 0; g.combo = 0; g.spinT = 0; g.air = 0; g.flow = tr(g.flow / 2);
    g.invuln = K.INVULN; if (kind === FX.CRASH) g.crashes++; else g.stumbles++; g.cue = 7; fx(g, kind, px(g.x), K.NABO_Y, 0);
  }

  function upEvent() {}
  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 60) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);

    // sections
    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVERY === 0) { g.section = 1 + tr((g.tick - K.CALM) / K.EVERY) % 5; g.sectionT = K.SECTION_LEN; fx(g, FX.SECTION, 160, 100, g.section); }
    if (g.sectionT > 0 && --g.sectionT === 0) g.section = 0;

    // steering (not while crashed or airborne)
    const left = !!input.ok_held, right = !!input.up_held;
    if (g.crash > 0) g.crash--;
    else if (!g.air) {
      const acc = g.onIce ? tr(K.STEER / 4) : K.STEER, want = left && !right ? -1 : right && !left ? 1 : 0;
      if (want) g.vx = Math.max(-K.VX_MAX, Math.min(K.VX_MAX, g.vx + want * acc));
      else if (!g.onIce) g.vx -= tr(g.vx / 6);
      // carving bleeds speed; pointing downhill gains it
      const target = vTarget(g) - tr(Math.abs(g.vx) / 3);
      if (g.v < target) g.v = Math.min(target, g.v + K.ACCEL); else g.v = Math.max(target, g.v - tr(Math.abs(g.vx) / K.DRAG_DIV) - 1);
    }
    if (g.invuln > 0) g.invuln--;
    if (g.flow > 0 && (g.tick & 1)) g.flow--;

    // jump / spin
    if (input.down_down && !g.crash) {
      if (!g.air) { g.air = g.airMax = K.HOP; g.kicked = 0; }
      else if (g.kicked && g.spinT === 0) { g.spinT = K.SPIN; }
    }
    const prevY = g.y;
    g.x = Math.max(K.LEFT << 8, Math.min(K.RIGHT << 8, g.x + g.vx));
    g.y += g.v;
    if (g.spinT > 0 && --g.spinT === 0) { g.spins++; g.tricks++; }
    if (g.air > 0 && --g.air === 0) {
      if (g.spinT > 0) { crash(g, FX.CRASH); fx(g, FX.WIPE, px(g.x), K.NABO_Y, 0); g.spins = 0; }
      else if (g.spins) {
        const pts = g.spins * K.SPIN_PTS * mult(g); g.bonus += pts; g.aval -= g.spins * K.SPIN_PUSH << 8; g.combo += g.spins; g.flow = Math.min(K.FLOW_MAX, g.flow + g.spins * K.FLOW_SPIN);
        fx(g, FX.LAND, px(g.x), K.NABO_Y, pts); g.cue = 6; g.spins = 0;
      }
      g.kicked = 0;
    }

    // objects crossed this frame (feet at NABO_Y; object y is the base line)
    g.onIce = 0;
    const nx = px(g.x), y0 = px(prevY), y1 = px(g.y);
    for (const o of g.objs) {
      if (!o.type) continue;
      const dx = Math.abs(nx - o.x);
      if (o.type === T.ICE) { if (dx <= K.ICE_HALF && y1 >= o.y && y1 <= o.y + K.ICE_LEN && !g.air) g.onIce = 1; continue; }
      if (o.done || !(y0 < o.y && y1 >= o.y)) continue;
      o.done = 1;
      if (o.type <= T.GATE_BLUE) {
        if (dx <= K.GATE_HALF) {
          g.combo++; g.passed++; if (g.combo > g.best) g.best = g.combo; g.v += K.GATE_BOOST; g.flow = Math.min(K.FLOW_MAX, g.flow + K.FLOW_GATE); g.aval -= K.GATE_PUSH << 8;
          const pts = 10 * mult(g); g.bonus += pts; fx(g, FX.GATE, o.x, K.NABO_Y - 30, pts); g.cue = 6;
        } else { g.combo = 0; g.misses++; g.aval += K.MISS_PULL << 8; fx(g, FX.MISS, o.x, K.NABO_Y - 30, 0); g.cue = 7; }
      } else if (o.type === T.KICKER) {
        if (dx <= K.KICK_HALF && !g.crash) { g.air = g.airMax = K.KICK_AIR; g.kicked = 1; g.spinT = 0; fx(g, FX.KICK, nx, K.NABO_Y, 0); }
      } else if (g.air || g.invuln || g.crash) continue;
      else if (o.type === T.TREE) { if (dx <= K.TREE_R) crash(g, FX.CRASH); else if (dx <= K.TREE_R + 10) { g.nearMiss++; fx(g, FX.NEAR, nx, K.NABO_Y, 0); } }
      else if (o.type === T.PINE) { if (dx <= K.PINE_R) crash(g, FX.STUMBLE); }
      else if (o.type === T.MOGUL) { if (dx <= K.MOGUL_R) { g.v = tr(g.v * 2 / 3); g.air = g.airMax = 10; g.kicked = 0; } }
      else if (o.type === T.DRIFT) { if (dx <= K.DRIFT_HALF) g.v = tr(g.v / 2); }
    }

    // spawning ahead, culling behind
    const ahead = y1 + K.AHEAD;
    while (g.nextGate < ahead) spawnGate(g, g.nextGate);
    while (g.nextRow < ahead) spawnRow(g, g.nextRow);
    for (const o of g.objs) if (o.type && o.y < y1 - K.CULL) Object.assign(o, { type: 0, x: 0, y: 0, done: 0 });

    // avalanche
    g.aval += avalSpeed(g);
    if (gap(g) > K.AVAL_CAP << 8) g.aval = g.y - (K.AVAL_CAP << 8);
    g.res = Math.max(0, tr(gap(g) * 1000 / (K.AVAL_CAP << 8)));
    g.meters = tr(px(g.y) / 8);
    g.score = tr(g.meters / 4) + g.bonus;
    if (gap(g) <= 0) { g.over = 1; g.res = 0; g.cue = 8; }
    return g;
  }

  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'x', 'vx', 'y', 'v', 'air', 'airMax', 'kicked', 'spinT', 'spins', 'crash',
    'invuln', 'aval', 'combo', 'best', 'gates', 'passed', 'misses', 'tricks', 'flow', 'crashes', 'stumbles', 'nearMiss', 'nextGate', 'nextRow', 'lastGateX',
    'section', 'sectionT', 'onIce', 'meters', 'bonus', 'presses', 'blocked', 'fxHead'];
  function view(g) {
    const out = HEAD.map(k => g[k]);
    for (const o of g.objs) out.push(o.type, o.x, o.y, o.done);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }
  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, T, SEC, FX, HEAD, start, step, status, upEvent, view, random, mult, gap, avalSpeed };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvSki = api;
})(typeof window !== 'undefined' ? window : globalThis);
