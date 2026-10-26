// SPACE V2「月面跳跳」rules reference: integer 60 Hz, mulberry32 + a stateless terrain hash, landscape 320x240.
// The lander hops from pad to pad across a scrolling moonscape. Taps on the middle key fire the main engine
// in pulses; left/right hold the side jets. Fuel drains all the time; landings refuel and score.
// x is Q8 world px (grows right), y is Q8 screen px of the lander's feet (grows down).
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, CAM_X: 120, CEIL: 92, FOOT: 28,
    GRAV: 6, LOW_GRAV: 3, PULSE: 200, SIDE: 5, VX_MAX: 520, VY_MAX: 900, WIND: 2,
    FUEL_MAX: 100000, FUEL_START: 70000, DRAIN: 13, PULSE_COST: 700, SIDE_COST: 30, CRASH_COST: 16000, CAN: 12000,
    SAFE_VY: 300, SAFE_VX: 170, SOFT_VY: 120, TAKEOFF_T: 70, OLD_PAD_T: 30, CRASH_T: 80,
    CHUNK: 512, CTRL: 64, ROCKS: 6, ROCK_R: 24,
    CALM: 900, EVERY: 1500, EVENT_LEN: 600,
  };
  const PAD = [null, { w: 110, mult: 1, fuel: 30000 }, { w: 84, mult: 2, fuel: 25000 }, { w: 68, mult: 3, fuel: 20000 }];
  const PH = { FLY: 0, LANDED: 1, CRASHED: 2 };
  const EV = { NONE: 0, METEOR: 1, WIND: 2, LOWGRAV: 3, DARK: 4 };
  const FX = { LAND: 1, PERFECT: 2, CRASH: 3, CAN: 4, EVENT: 5, OLD_PAD: 6, ROCK: 7 };
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n, tr = Math.trunc, px = q => q >> 8;
  // Stateless terrain: the same seed always draws the same moon; C uses the identical mix.
  function mix(seed, n) { let h = Math.imul((seed ^ Math.imul(n, 0x9E3779B1)) >>> 0, 0x85EBCA6B) >>> 0; h ^= h >>> 13; h = Math.imul(h, 0xC2B2AE35) >>> 0; return (h ^ (h >>> 16)) >>> 0; }
  const floorDiv = (a, b) => Math.floor(a / b);

  function pad(seed, chunk) {            // one pad per 512 px chunk; chunk 0 starts NABO on a wide pad
    if (chunk < 0) return null;
    if (chunk === 0) return { chunk, x: 160, y: 190, type: 1 };
    const h = mix(seed, chunk * 4 + 1), v = h % 100, type = v < 45 ? 1 : v < 78 ? 2 : 3;
    return { chunk, x: chunk * K.CHUNK + 150 + (h >>> 8) % 212, y: type === 3 ? 140 + (h >>> 16) % 30 : 160 + (h >>> 16) % 44, type };
  }
  function ctrl(seed, k) {              // control heights every 64 px; ridges reach up to y=112
    const h = mix(seed, k * 4 + 2), v = h % 100;
    return v < 26 ? 132 + (h >>> 8) % 40 : 180 + (h >>> 8) % 42;
  }
  function ground(seed, xpx) {           // screen y of the ground at world x (px)
    const c = floorDiv(xpx, K.CHUNK);
    for (const p of [pad(seed, c), pad(seed, c + 1), pad(seed, c - 1)]) if (p && Math.abs(xpx - p.x) <= (PAD[p.type].w >> 1) + 6) return p.y;
    const k = floorDiv(xpx, K.CTRL), a = ctrl(seed, k), b = ctrl(seed, k + 1), t = xpx - k * K.CTRL;
    let y = a + tr((b - a) * t / K.CTRL);
    for (const p of [pad(seed, c), pad(seed, c + 1), pad(seed, c - 1)]) if (p) {   // ramps into each pad so it is reachable
      const d = Math.abs(xpx - p.x) - (PAD[p.type].w >> 1) - 6;
      if (d >= 0 && d < 48) y = p.y + tr((y - p.y) * d / 48);
    }
    return Math.min(226, y);
  }
  function padUnder(seed, xpx) {
    const c = floorDiv(xpx, K.CHUNK);
    for (const p of [pad(seed, c), pad(seed, c + 1), pad(seed, c - 1)]) if (p && Math.abs(xpx - p.x) <= (PAD[p.type].w >> 1) - K.FOOT + 4) return p;
    return null;
  }
  function can(seed, chunk) {           // one fuel can floating between this chunk's pad and the next
    if (chunk < 0) return null;
    const a = pad(seed, chunk), b = pad(seed, chunk + 1), h = mix(seed, chunk * 4 + 3), x = tr((a.x + b.x) / 2) + (h % 80) - 40;
    return { x, y: Math.max(K.CEIL - 40, ground(seed, x) - 70 - (h >>> 8) % 60) };
  }

  function start(seed) {
    seed >>>= 0;
    return { rng: seed, tick: 0, score: 0, res: 0, over: 0, cue: 0, seed, x: 160 << 8, y: 190 << 8, vx: 0, vy: 0,
      fuel: K.FUEL_START, phase: PH.LANDED, phaseT: K.TAKEOFF_T, padChunk: 0, bestChunk: 0, streak: 0, hops: 0, perfect: 0,
      crashes: 0, cans: 0, flame: 0, sideL: 0, sideR: 0, event: 0, eventT: 0, nextRock: 0, invuln: 0, canMask: 0, canBase: 0,
      presses: 0, blocked: 0, fxHead: 0, cause: 0,
      rocks: Array.from({ length: K.ROCKS }, () => ({ x: 0, y: 0, vx: 0, vy: 0, live: 0 })),
      fx: Array.from({ length: 6 }, () => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
  }
  const streakMult = g => 1 + Math.min(4, tr(g.streak / 2));
  const camX = g => Math.max(0, px(g.x) - K.CAM_X);
  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % 6; }
  function spend(g, n) { g.fuel -= n; }

  function crash(g, cause) {
    g.phase = PH.CRASHED; g.phaseT = K.CRASH_T; g.crashes++; g.streak = 0; g.cause = cause; spend(g, K.CRASH_COST);
    g.vx = g.vy = 0; g.cue = 7; fx(g, FX.CRASH, px(g.x), px(g.y), cause);
  }
  function land(g, p) {
    g.phase = PH.LANDED; g.phaseT = p.chunk > g.bestChunk ? 0 : K.OLD_PAD_T; g.y = p.y << 8; const soft = g.vy <= K.SOFT_VY; g.vx = g.vy = 0;
    if (p.chunk > g.bestChunk) {
      g.streak++; g.hops++; g.bestChunk = p.chunk; if (soft) g.perfect++;
      const pts = (100 * PAD[p.type].mult + (soft ? 50 : 0)) * streakMult(g);
      g.score += pts; g.fuel = Math.min(K.FUEL_MAX, g.fuel + PAD[p.type].fuel); g.cue = 6;
      fx(g, soft ? FX.PERFECT : FX.LAND, p.x, p.y - 96, pts);
    } else fx(g, FX.OLD_PAD, p.x, p.y - 96, 0);
    g.padChunk = p.chunk;
  }

  function upEvent() {}
  // input: ok_held = left jet, up_held = right jet, down_down = main engine pulse.
  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 60) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);
    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVERY === 0) {
      g.event = 1 + tr((g.tick - K.CALM) / K.EVERY) % 4; g.eventT = K.EVENT_LEN; fx(g, FX.EVENT, 0, 0, g.event); g.nextRock = g.tick + 30;
    }
    if (g.eventT > 0 && --g.eventT === 0) g.event = 0;
    if (g.flame > 0) g.flame--;
    if (g.invuln > 0) g.invuln--;
    spend(g, K.DRAIN);
    g.sideL = g.sideR = 0;

    if (g.phase === PH.CRASHED) {
      if (--g.phaseT === 0) { const p = pad(g.seed, g.padChunk); g.x = p.x << 8; g.y = p.y << 8; g.phase = PH.LANDED; g.phaseT = K.OLD_PAD_T; g.invuln = 90; }
    } else {
      if (g.phase === PH.LANDED) g.phaseT++;
      const left = !!input.ok_held && !input.up_held, right = !!input.up_held && !input.ok_held;
      if (input.down_down && (g.phase === PH.FLY || g.phaseT >= K.TAKEOFF_T)) {
        g.vy = Math.max(-K.VY_MAX, g.vy - K.PULSE); g.flame = 10; spend(g, K.PULSE_COST); g.phase = PH.FLY;
      }
      if (g.phase === PH.FLY) {
        if (left) { g.vx = Math.max(-K.VX_MAX, g.vx - K.SIDE); g.sideL = 1; spend(g, K.SIDE_COST); }
        if (right) { g.vx = Math.min(K.VX_MAX, g.vx + K.SIDE); g.sideR = 1; spend(g, K.SIDE_COST); }
        if (g.event === EV.WIND) g.vx = Math.min(K.VX_MAX, g.vx + K.WIND);
        g.vy = Math.min(K.VY_MAX, g.vy + (g.event === EV.LOWGRAV ? K.LOW_GRAV : K.GRAV));
        const ox = g.x; g.x += g.vx; g.y += g.vy;
        if (g.y < K.CEIL << 8) { g.y = K.CEIL << 8; if (g.vy < 0) g.vy = 0; }
        if (g.x < 40 << 8) { g.x = 40 << 8; g.vx = 0; }
        // touchdown: either foot meets the ground
        const xp = px(g.x), feet = px(g.y), gl = ground(g.seed, xp - K.FOOT), gc = ground(g.seed, xp), gr = ground(g.seed, xp + K.FOOT);
        if (feet >= Math.min(gl, gc, gr)) {
          const p = padUnder(g.seed, xp);
          if (p && feet >= p.y - 2 && Math.min(gl, gc, gr) >= p.y && g.vy <= K.SAFE_VY && Math.abs(g.vx) <= K.SAFE_VX) land(g, p);
          else crash(g, p ? 1 : 2);
        }
        // fuel can of the current and next chunk
        const c = floorDiv(px(g.x), K.CHUNK);
        if (c > g.canBase + 8) { g.canMask >>>= c - 8 - g.canBase > 31 ? 31 : c - 8 - g.canBase; g.canBase = c - 8; }
        for (const cc of [c - 1, c, c + 1]) {
          const bit = cc - g.canBase; if (bit < 0 || bit > 30 || (g.canMask >>> bit) & 1) continue;
          const f = can(g.seed, cc); if (!f) continue;
          if (Math.abs(f.x - xp) < 30 && Math.abs(f.y - (feet - 40)) < 40) { g.canMask |= 1 << bit; g.cans++; g.fuel = Math.min(K.FUEL_MAX, g.fuel + K.CAN); g.score += 20; fx(g, FX.CAN, f.x, f.y, 20); }
        }
      }
    }

    // meteors fall from the upper right during a shower (and rarely later on)
    const rain = g.event === EV.METEOR || (g.tick > 4800 && rnd(g, 1000) < 2);
    if (rain && g.tick >= g.nextRock) {
      const r = g.rocks.find(o => !o.live);
      const x = camX(g) + 120 + rnd(g, 260), vx = -60 - rnd(g, 90), vy = 160 + rnd(g, 120);
      if (r) Object.assign(r, { x: x << 8, y: -20 << 8, vx, vy, live: 1 }); else g.blocked++;
      g.nextRock = g.tick + 70 + rnd(g, 50);
    }
    for (const r of g.rocks) {
      if (!r.live) continue;
      r.x += r.vx; r.y += r.vy;
      const dx = px(r.x) - px(g.x), dy = px(r.y) - (px(g.y) - 44);
      if (g.phase !== PH.CRASHED && !g.invuln && dx * dx + dy * dy < K.ROCK_R * K.ROCK_R) { r.live = 0; fx(g, FX.ROCK, px(r.x), px(r.y), 0); crash(g, 3); continue; }
      if (px(r.y) >= ground(g.seed, px(r.x)) || px(r.x) < camX(g) - 40) Object.assign(r, { x: 0, y: 0, vx: 0, vy: 0, live: 0 });
    }

    if (g.fuel <= 0) { g.fuel = 0; g.over = 1; g.cue = 8; }
    g.res = tr(g.fuel / 100);
    return g;
  }

  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'seed', 'x', 'y', 'vx', 'vy', 'fuel', 'phase', 'phaseT', 'padChunk', 'bestChunk',
    'streak', 'hops', 'perfect', 'crashes', 'cans', 'flame', 'sideL', 'sideR', 'event', 'eventT', 'nextRock', 'invuln', 'canMask', 'canBase',
    'presses', 'blocked', 'fxHead', 'cause'];
  function view(g) {
    const out = HEAD.map(k => k === 'canMask' ? g.canMask | 0 : g[k]);
    for (const r of g.rocks) out.push(r.x, r.y, r.vx, r.vy, r.live);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }
  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, PAD, PH, EV, FX, HEAD, start, step, status, upEvent, view, random, mix, pad, ctrl, ground, padUnder, can, camX, streakMult };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvSpaceV2 = api;
})(typeof window !== 'undefined' ? window : globalThis);
