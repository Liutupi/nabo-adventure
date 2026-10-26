// SPACE V2「火箭登月」rules reference: integer 60 Hz, mulberry32, landscape 320x240 (G1 prototype).
// One journey: ignition -> ascent -> stage separation -> upper atmosphere -> space -> trans-lunar burn -> lunar landing.
// The rocket climbs (world altitude grows up, in px) while the player steers left/right and taps the middle key
// for boosts and the timing events. Fuel drains all the time; the hull takes three hits.
// Keys (landscape, left to right): OK = hold left, DOWN = tap (boost / timing / retro), UP = hold right.
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, RY: 176, ROCKET_H: 40, LEFT: 20, RIGHT: 300, OBJS: 24, AHEAD: 250, BEHIND: 120,
    Z1: 4000, Z2: 8000, Z3: 14000, Z4: 19000,
    STEER: 28, VX_MAX: 700, BOOST: 260, BOOST_COST: 2500, BOOST_HEAT: 170, BOOST_GAP: 20,
    FUEL_MAX: 100000, DRAIN_ATM: 14, DRAIN_SPACE: 10, HULL: 3, INVULN: 70, HEAT_MAX: 1000,
    IGN_T: 300, SEP_T: 96, WARN: 45, TLI_LEAD: 50, TLI_BEAT: 32,
    LAND_G: 5, RETRO: 170, RETRO_COST: 1500, LAND_SIDE: 5, LAND_SIDE_COST: 30, GROUND: 206, PAD_HALF: 34, SAFE_VY: 260, SOFT_VY: 120,
  };
  const T = { BIRDS: 1, PLANE: 2, BALLOON: 3, STORM: 4, GUST: 5, STAR: 6, FUEL: 7, RING: 8, JET: 9, SAT: 10, JUNK: 11, ROCK: 12, METEOR: 13, COMET: 14, REPAIR: 15 };
  const R = [0, 14, 16, 10, 0, 0, 9, 10, 0, 0, 18, 6, 12, 8, 10, 10];   // collision radius per type
  const MODE = { IGNITE: 0, FLY: 1, LAND: 2, ENDING: 3, LOST: 4 };
  const FX = { HIT: 1, STAR: 2, FUEL: 3, NEAR: 4, RING: 5, TIMING: 6, ZONE: 7, OVERHEAT: 8, LANDED: 9, CRASH: 10, REPAIR: 11, SEP: 12, SMASH: 13 };
  const SMALL = new Set([1, 3, 11]);   // birds, balloon, junk: a boosting rocket's shield smashes them
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n, tr = Math.trunc, px = q => q >> 8;
  const zone = alt => alt < K.Z1 ? 1 : alt < K.Z2 ? 2 : alt < K.Z3 ? 3 : 4;

  function start(seed) {
    return { rng: seed >>> 0, tick: 0, score: 0, res: 1000, over: 0, cue: 0, mode: MODE.IGNITE, modeT: 0, win: 0,
      alt: 0, v: 0, vTarget: 0, x: 160 << 8, vx: 0, fuel: K.FUEL_MAX, hull: K.HULL, heat: 0, boostT: 0, lastBoost: -100, invuln: 0,
      ign: 0, ignScore: 0, sep: 0, sepT: 0, sepQ: 0, tli: 0, tliT: 0, tliHit: 0, tliQ: 0, zoneSeen: 1,
      combo: 0, best: 0, stars: 0, near: 0, hits: 0, perfects: 0, rings: 0, cans: 0, bonus: 0, nextObj: 220, push: 0,
      lx: 0, ly: 0, lvx: 0, lvy: 0, pad: 0, landings: 0, presses: 0, blocked: 0, fxHead: 0,
      objs: Array.from({ length: K.OBJS }, () => ({ type: 0, x: 0, y: 0, vx: 0, state: 0, done: 0 })),
      fx: Array.from({ length: 6 }, () => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
  }
  const mult = g => 1 + Math.min(4, tr(g.combo / 5));
  const gauge = t => { const p = t % 60; return p < 30 ? tr(p * 100 / 30) : tr((60 - p) * 100 / 30); };   // ignition needle 0..100..0
  const quality = (v, target, perfect, good) => Math.abs(v - target) <= perfect ? 2 : Math.abs(v - target) <= good ? 1 : 0;
  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % 6; }
  function spend(g, n) { g.fuel -= n; }
  function slot(g) { const o = g.objs.find(e => !e.type); if (!o) g.blocked++; return o; }
  function hurt(g, why) {
    if (g.invuln) return;
    g.hull--; g.hits++; g.combo = 0; g.invuln = K.INVULN; g.cue = 7; fx(g, FX.HIT, px(g.x), K.RY - 20, why);
    if (g.hull <= 0) { g.mode = MODE.LOST; g.modeT = 90; }
  }

  // ---------------------------------------------------------------- spawning by zone
  function spawn(g) {
    const z = zone(px(g.alt) + K.AHEAD), y = px(g.alt) + K.AHEAD + rnd(g, 40), v = rnd(g, 100), x = K.LEFT + rnd(g, K.RIGHT - K.LEFT);
    const side = rnd(g, 2), o = slot(g);
    let type, vx = 0, state = 0;
    if (z === 1) {
      if (v < 26) { type = T.BIRDS; vx = side ? 150 : -150; }
      else if (v < 38) { type = T.PLANE; vx = side ? 380 : -380; }
      else if (v < 50) type = T.BALLOON;
      else if (v < 62) { type = T.STORM; state = 0; }
      else if (v < 72) { type = T.GUST; vx = side ? 1 : -1; }
      else if (v < 90) type = T.STAR;
      else type = T.FUEL;
    } else if (z === 2) {
      if (v < 24) { type = T.JET; vx = side ? 1 : -1; }
      else if (v < 44) type = T.RING;
      else if (v < 58) { type = T.BALLOON; }
      else if (v < 72) { type = T.METEOR; vx = side ? 260 : -260; }
      else if (v < 90) type = T.STAR;
      else type = rnd(g, 3) ? T.FUEL : T.REPAIR;
    } else if (z === 3) {
      if (v < 26) { type = T.SAT; vx = side ? 90 : -90; }
      else if (v < 50) { type = T.JUNK; vx = side ? 330 : -330; }
      else if (v < 68) { type = T.ROCK; vx = side ? 40 : -40; }
      else if (v < 88) type = T.STAR;
      else type = rnd(g, 4) ? T.FUEL : T.REPAIR;
    } else {
      if (v < 34) { type = T.METEOR; vx = side ? 300 : -300; }
      else if (v < 54) { type = T.ROCK; vx = side ? 60 : -60; }
      else if (v < 64) { type = T.COMET; vx = side ? 200 : -200; }
      else if (v < 86) type = T.STAR;
      else type = T.FUEL;
    }
    let ox = x;
    if (type === T.PLANE || type === T.JUNK || type === T.METEOR || type === T.COMET) { ox = vx > 0 ? -20 : K.W + 20; state = K.WARN; }   // edge warning first
    if (type === T.GUST || type === T.JET) ox = 160;
    if (o) Object.assign(o, { type, x: ox << 8, y, vx, state, done: 0 });
    const gap = z === 1 ? 70 : z === 2 ? 62 : z === 3 ? 56 : 50;
    g.nextObj = y + gap + rnd(g, 50);
  }

  // ---------------------------------------------------------------- per-mode steps
  function stepIgnite(g, input) {
    g.modeT++;
    if (input.down_down && g.ign < 3) {
      const q = quality(gauge(g.modeT), 80, 8, 20); g.ign++; g.ignScore += q; if (q === 2) g.perfects++;
      g.bonus += q * 50; fx(g, FX.TIMING, 160, 120, q); g.cue = q ? 6 : 7;
    }
    if (g.ign >= 3 || g.modeT >= K.IGN_T) {
      g.mode = MODE.FLY; g.modeT = 0; g.vTarget = 520 + g.ignScore * 20; fx(g, FX.ZONE, 0, 0, 1);
    }
  }

  function stepFly(g, input) {
    const z = zone(px(g.alt));
    if (z !== g.zoneSeen) { g.zoneSeen = z; fx(g, FX.ZONE, 0, 0, z); g.vTarget += z === 2 ? 220 : z === 3 ? 180 : 0; }
    // timing events
    if (!g.sep && px(g.alt) >= K.Z1) { g.sep = 1; g.sepT = 0; }
    if (g.sep === 1) {
      g.sepT++;
      const needle = tr(g.sepT * 100 / K.SEP_T);
      if (input.down_down || needle >= 100) {
        const q = input.down_down ? quality(needle, 78, 7, 18) : 0; g.sep = 2; g.sepQ = q;
        g.fuel = Math.min(K.FUEL_MAX, g.fuel + [6000, 18000, 30000][q]); g.vTarget += [-80, 60, 140][q]; if (q === 2) g.perfects++;
        g.bonus += q * 100; fx(g, FX.SEP, px(g.x), K.RY, q); g.cue = q ? 6 : 7;
      }
    }
    if (!g.tli && px(g.alt) >= K.Z3) { g.tli = 1; g.tliT = 0; }
    if (g.tli === 1) {
      g.tliT++;
      if (input.down_down) {
        const beat = g.tliHit, at = K.TLI_LEAD + beat * K.TLI_BEAT, q = quality(g.tliT, at, 5, 11);
        g.tliHit++; g.tliQ += q; if (q === 2) g.perfects++; g.vTarget += q * 40; g.bonus += q * 60; fx(g, FX.TIMING, 160, 100, q); g.cue = q ? 6 : 7;
      }
      if (g.tliHit >= 3 || g.tliT > K.TLI_LEAD + 3 * K.TLI_BEAT + 20) g.tli = 2;
    }
    const timing = g.sep === 1 || g.tli === 1;

    // steering, boost, speed
    const left = !!input.ok_held && !input.up_held, right = !!input.up_held && !input.ok_held;
    if (left) g.vx = Math.max(-K.VX_MAX, g.vx - K.STEER); else if (right) g.vx = Math.min(K.VX_MAX, g.vx + K.STEER); else g.vx -= tr(g.vx / 6);
    if (input.down_down && !timing && g.tick - g.lastBoost >= K.BOOST_GAP) {
      g.lastBoost = g.tick; g.boostT = 40; g.v += K.BOOST; spend(g, K.BOOST_COST); if (z <= 2) g.heat += K.BOOST_HEAT; g.cue = 6;
    }
    if (g.boostT > 0) g.boostT--;
    const target = g.sep === 1 ? tr(g.vTarget * 3 / 4) : g.vTarget;
    g.v = g.v < target ? Math.min(target, g.v + 4) : Math.max(target, g.v - 6);
    g.push = 0;
    g.x = Math.max(K.LEFT << 8, Math.min(K.RIGHT << 8, g.x + g.vx));
    const prev = px(g.alt); g.alt += g.v;
    const alt = px(g.alt);
    spend(g, z <= 2 ? K.DRAIN_ATM : K.DRAIN_SPACE);
    if (z <= 2) g.heat = Math.max(0, g.heat + Math.max(0, tr((g.v - target) / 24)) - 4);   // only boosting above cruise heats the hull
    else g.heat = Math.max(0, g.heat - 8);
    if (g.heat >= K.HEAT_MAX) { g.heat = 500; fx(g, FX.OVERHEAT, px(g.x), K.RY - 30, 0); hurt(g, 3); }
    if (g.invuln > 0) g.invuln--;

    // world objects
    while (g.nextObj < alt + K.AHEAD) spawn(g);
    const rx = px(g.x);
    for (const o of g.objs) {
      if (!o.type) continue;
      if (o.state > 0 && o.type !== T.STORM) { o.state--; continue; }   // waiting at the edge behind its warning arrow
      o.x += o.vx === 1 || o.vx === -1 ? 0 : o.vx;
      if (o.type === T.BALLOON) o.y += (g.tick & 3) === 0 ? 1 : 0;
      if (o.type === T.METEOR) o.y -= 3;
      const ox = px(o.x), r = R[o.type];
      if (o.type === T.GUST || o.type === T.JET) {
        if (alt + 20 >= o.y && alt + 20 <= o.y + 56) { const p = o.type === T.JET ? 22 : 14; g.vx = Math.max(-K.VX_MAX, Math.min(K.VX_MAX, g.vx + o.vx * p)); g.push = o.vx; }
      } else if (o.type === T.STORM) {   // lightning: warn 50 frames, strike 12, while the cloud is on screen
        const sy = K.RY - (o.y - alt);
        if (o.state === 0 && sy > 20 && sy < 150) { o.state = 62; o.vx = 0; o.x = (Math.max(K.LEFT, Math.min(K.RIGHT, rx + rnd(g, 61) - 30))) << 8; }
        if (o.state > 0) { o.state--; if (o.state < 12 && o.state > 0 && Math.abs(rx - px(o.x)) < 14) hurt(g, 2); if (o.state === 0) o.state = -1; }
      } else if (!o.done) {
        const top = alt + K.ROCKET_H, inY = o.y + r >= alt && o.y - r <= top, dx = Math.abs(ox - rx);
        if (inY && dx < r + 7) {
          o.done = 1;
          if (o.type === T.STAR) { g.stars++; g.combo++; g.best = Math.max(g.best, g.combo); const p = 20 * mult(g); g.bonus += p; fx(g, FX.STAR, ox, K.RY - (o.y - alt), p); g.cue = 6; o.type = 0; }
          else if (o.type === T.FUEL) { g.cans++; g.fuel = Math.min(K.FUEL_MAX, g.fuel + 14000); fx(g, FX.FUEL, ox, K.RY - (o.y - alt), 0); g.cue = 6; o.type = 0; }
          else if (o.type === T.REPAIR) { g.hull = Math.min(K.HULL, g.hull + 1); fx(g, FX.REPAIR, ox, K.RY - (o.y - alt), 0); g.cue = 6; o.type = 0; }
          else if (o.type === T.RING) { g.rings++; g.combo++; g.best = Math.max(g.best, g.combo); g.heat = Math.max(0, g.heat - 300); const p = 40 * mult(g); g.bonus += p; fx(g, FX.RING, ox, K.RY - (o.y - alt), p); g.cue = 6; }
          else if (g.boostT > 0 && SMALL.has(o.type)) { g.combo++; g.best = Math.max(g.best, g.combo); const p = 25 * mult(g); g.bonus += p; fx(g, FX.SMASH, ox, K.RY - (o.y - alt), p); g.cue = 6; o.type = 0; }
          else { hurt(g, 1); }
        } else if (o.type !== T.STAR && o.type !== T.FUEL && o.type !== T.REPAIR && o.type !== T.RING && prev + 20 < o.y && alt + 20 >= o.y && dx < r + 18) {
          o.done = 1; g.near++; g.combo++; g.best = Math.max(g.best, g.combo); const p = 15 * mult(g); g.bonus += p; fx(g, FX.NEAR, rx, K.RY - 30, p);
        }
      }
      if (o.y < alt - K.BEHIND || ox < -60 || ox > K.W + 60) Object.assign(o, { type: 0, x: 0, y: 0, vx: 0, state: 0, done: 0 });
    }
    if (alt >= K.Z4) {
      g.mode = MODE.LAND; g.modeT = 0; for (const o of g.objs) Object.assign(o, { type: 0, x: 0, y: 0, vx: 0, state: 0, done: 0 });
      g.lx = px(g.x) << 8; g.ly = 24 << 8; g.lvx = 0; g.lvy = 120; g.pad = 60 + rnd(g, 201); fx(g, FX.ZONE, 0, 0, 5);
    }
  }

  function stepLand(g, input) {
    g.modeT++;
    const left = !!input.ok_held && !input.up_held, right = !!input.up_held && !input.ok_held;
    if (left) { g.lvx -= K.LAND_SIDE; spend(g, K.LAND_SIDE_COST); }
    if (right) { g.lvx += K.LAND_SIDE; spend(g, K.LAND_SIDE_COST); }
    if (input.down_down) { g.lvy -= K.RETRO; spend(g, K.RETRO_COST); g.boostT = 10; g.cue = 6; }
    if (g.boostT > 0) g.boostT--;
    g.lvy = Math.min(900, g.lvy + K.LAND_G); g.lvx = Math.max(-500, Math.min(500, g.lvx));
    g.lx = Math.max(40 << 8, Math.min(280 << 8, g.lx + g.lvx)); g.ly = Math.max(10 << 8, g.ly + g.lvy);
    spend(g, 8);
    if (g.invuln > 0) g.invuln--;
    if (px(g.ly) >= K.GROUND) {
      const dx = Math.abs(px(g.lx) - g.pad);
      if (dx <= K.PAD_HALF - 12 && g.lvy <= K.SAFE_VY && Math.abs(g.lvx) <= 200) {
        const soft = g.lvy <= K.SOFT_VY; g.landings++; if (soft) g.perfects++;
        g.bonus += 1000 + (soft ? 500 : 0) + g.hull * 300 + tr(Math.max(0, g.fuel) / 100);
        g.ly = K.GROUND << 8; g.lvx = g.lvy = 0; g.mode = MODE.ENDING; g.modeT = 0; g.win = 1; g.cue = 6; fx(g, FX.LANDED, g.pad, K.GROUND - 110, soft ? 2 : 1);
      } else {
        fx(g, FX.CRASH, px(g.lx), K.GROUND - 100, 0); g.hull--; g.hits++; g.cue = 7;
        if (g.hull <= 0) { g.mode = MODE.LOST; g.modeT = 90; }
        else { g.ly = 24 << 8; g.lvy = 120; g.lvx = 0; spend(g, 5000); g.invuln = 40; }
      }
    }
  }

  function upEvent() {}
  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 70) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);
    if (g.mode === MODE.IGNITE) stepIgnite(g, input);
    else if (g.mode === MODE.FLY) stepFly(g, input);
    else if (g.mode === MODE.LAND) stepLand(g, input);
    else if (g.mode === MODE.ENDING) { if (++g.modeT >= 150) { g.over = 1; g.cue = 8; } }
    else if (g.mode === MODE.LOST) { if (--g.modeT <= 0) { g.over = 1; g.cue = 8; } }
    if (g.fuel <= 0 && g.mode !== MODE.ENDING && g.mode !== MODE.LOST) { g.fuel = 0; g.mode = MODE.LOST; g.modeT = 90; }
    g.res = Math.max(0, tr(g.fuel / 100));
    g.score = Math.min(tr(px(g.alt) / 10), tr(K.Z4 / 10)) + g.bonus;
    return g;
  }

  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'mode', 'modeT', 'win', 'alt', 'v', 'vTarget', 'x', 'vx', 'fuel', 'hull', 'heat',
    'boostT', 'lastBoost', 'invuln', 'ign', 'ignScore', 'sep', 'sepT', 'sepQ', 'tli', 'tliT', 'tliHit', 'tliQ', 'zoneSeen', 'combo', 'best',
    'stars', 'near', 'hits', 'perfects', 'rings', 'cans', 'bonus', 'nextObj', 'push', 'lx', 'ly', 'lvx', 'lvy', 'pad', 'landings', 'presses',
    'blocked', 'fxHead'];
  function view(g) {
    const out = HEAD.map(k => g[k]);
    for (const o of g.objs) out.push(o.type, o.x, o.y, o.vx, o.state, o.done);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }
  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, T, R, MODE, FX, SMALL, HEAD, start, step, status, upEvent, view, random, mult, gauge, zone };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvSpace = root.AdvSpaceV2 = api;
})(typeof window !== 'undefined' ? window : globalThis);
