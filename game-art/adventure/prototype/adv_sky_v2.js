// SKY V2「风层邮差」rules reference (G1): integer 60 Hz, mulberry32, landscape 320x240.
// The balloon stays at screen x = BX; the world scrolls left at the speed of the wind layer the basket is in.
// Screen y grows downward, Q8 for the balloon and letters. World x is integer px (dist is Q8).
// Keys (landscape, left to right): OK = hold to vent (sink fast), DOWN = tap to drop a letter, UP = hold to heat (climb).
// Long-press DOWN is the shell's pause, so nothing here needs DOWN held.
// Firmware does NOT follow this yet: V1 (portrait, hold OK to heat) is still adv_sky.c. Port only after the user approves G1.
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, BX: 92, YMIN: 104, YMAX: 204, GROUND: 214, Y0: 150,
    LAYER: [128, 160, 186],                 // basket y boundaries between the four wind layers (0 = highest)
    SPEEDS: [230, 340, 450, 560],           // Q8 px/frame, permuted per section; identity at start: lower = faster
    HEAT: 15, VENT: 20, SINK: 5, DAMP: 12, VMAX: 440,
    DRAIN: 9, DRAIN_HEAT: 15,               // fuel per 60 frames is (DRAIN [+ DRAIN_HEAT]) / 6 ... see step()
    LETTERS: 4, COOLDOWN: 16, GRAV: 22, LETTER_VMAX: 900,
    BOX_HALF: 10, BULL: 3, HIGH_DROP: 70,
    PTS: 10, GOLD: 3, TIP: 30, TIP_GOLD: 100, TANK: 180, DRAIN_RAMP: 1200,
    HIT_TREE: 120, HIT_BIRD: 100, HIT_STORM: 150, HIT_GROUND: 60, INVULN: 70,
    ENV_DY: 58, ENV_R: 29, BASKET_HALF: 15, BASKET_H: 16,
    OBJS: 24, AHEAD: 360, CULL: -60,
    CALM: 900, EVERY: 1500, SECTION_LEN: 900,
    STORM_CYCLE: 230, STORM_WARN: 150, STORM_BOLT: 200, STORM_END: 222, BOLT_HALF: 7, STORM_HALF: 26, BOLT_LEN: 62, STORM_H: 12, MISS_COST: 25,
  };
  const T = { HOUSE: 1, TREE: 2, BIRD: 3, STORM: 4, TANK: 5 };
  const SEC = { NONE: 0, TOWN: 1, BIRDS: 2, STORM: 3, RAINBOW: 4, GUST: 5 };
  const FX = { DELIVER: 1, BULL: 2, MISS: 3, SKIP: 4, HIT: 5, TANK: 6, SECTION: 7, NEAR: 8, GROUND: 9, WIND: 10 };
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n, tr = Math.trunc, px = q => q >> 8;

  function start(seed) {
    return { rng: seed >>> 0, tick: 0, score: 0, res: 1000, over: 0, cue: 0, y: K.Y0 << 8, vy: 0, dist: 0, spd: K.SPEEDS[2], layer: 2,
      order: [0, 1, 2, 3], heating: 0, venting: 0, drainAcc: 0, invuln: 0, cool: 0, combo: 0, best: 0, bonus: 0,
      delivered: 0, bulls: 0, golds: 0, skipped: 0, missDrops: 0, drops: 0, hits: 0, tanks: 0, nearMiss: 0, grounds: 0,
      section: 0, sectionT: 0, nextGround: 300, nextSky: 420, houses: 0, presses: 0, blocked: 0, fxHead: 0, meters: 0,
      objs: Array.from({ length: K.OBJS }, () => ({ type: 0, x: 0, y: 0, v: 0, t: 0, done: 0, n: 0 })),
      letters: Array.from({ length: K.LETTERS }, () => ({ on: 0, x: 0, y: 0, vx: 0, vy: 0, y0: 0 })),
      fx: Array.from({ length: 6 }, () => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
  }
  const mult = g => 1 + Math.min(4, tr(g.combo / 3));
  const layerOf = y => (y < K.LAYER[0] ? 0 : y < K.LAYER[1] ? 1 : y < K.LAYER[2] ? 2 : 3);
  const layerSpeed = (g, l) => tr(K.SPEEDS[g.order[l]] * (g.section === SEC.GUST ? 5 : 4) / 4);
  const camX = g => px(g.dist);                        // world x at screen x = 0
  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % 6; }
  function slot(g) { const o = g.objs.find(e => !e.type); if (!o) g.blocked++; return o; }
  function clear(o) { o.type = o.x = o.y = o.v = o.t = o.done = o.n = 0; }
  // A storm's bolt only strikes from its own bottom down, so this is the danger column for the warning, too.
  const stormPhase = o => o.t % K.STORM_CYCLE;

  function spawnGround(g, x) {
    const s = g.section, v = rnd(g, 100), o = slot(g);
    const houseOdds = s === SEC.TOWN ? 80 : s === SEC.STORM ? 45 : 58;
    if (o && v < houseOdds) {
      const gold = rnd(g, 100) < (s === SEC.RAINBOW ? 40 : 9) ? 1 : 0;
      Object.assign(o, { type: T.HOUSE, x, y: 176 + rnd(g, 18), v: gold | (rnd(g, 4) << 1), t: 0, done: 0, n: 0 }); g.houses++;
      // a tree right behind a gold house: the reward sits next to the danger
      if (gold) { const t2 = slot(g); if (t2) Object.assign(t2, { type: T.TREE, x: x + 38 + rnd(g, 10), y: 150 + rnd(g, 14), v: 1, t: 0, done: 0, n: 0 }); }
    } else if (o) Object.assign(o, { type: T.TREE, x, y: (s === SEC.TOWN ? 172 : 150) + rnd(g, 30), v: rnd(g, 3) === 0 ? 1 : 0, t: 0, done: 0, n: 0 });
    g.nextGround = x + (s === SEC.TOWN ? 62 : 78) + rnd(g, s === SEC.TOWN ? 30 : 60);
  }
  function spawnSky(g, x) {
    const s = g.section, v = rnd(g, 100), o = slot(g);
    if (o) {
      const birdOdds = s === SEC.BIRDS ? 62 : s === SEC.GUST ? 22 : 32, stormOdds = s === SEC.STORM ? 90 : s === SEC.BIRDS ? 92 : 86;
      if (v < birdOdds) Object.assign(o, { type: T.BIRD, x, y: 118 + rnd(g, 72), v: rnd(g, 64), t: 0, done: 0, n: 0 });
      else if (v < stormOdds) Object.assign(o, { type: T.STORM, x, y: (s === SEC.STORM ? 48 : 36) + rnd(g, 18), v: 0, t: rnd(g, K.STORM_WARN), done: 0, n: 0 });
      else Object.assign(o, { type: T.TANK, x, y: 110 + rnd(g, 70), v: 0, t: 0, done: 0, n: 0 });
    }
    g.nextSky = x + (s === SEC.BIRDS ? 80 : 150) + rnd(g, s === SEC.BIRDS ? 60 : 140);
  }

  function hurt(g, dmg, kind, x, y) {
    if (g.invuln) return;
    g.res -= dmg; g.invuln = K.INVULN; g.combo = 0; g.hits++; g.cue = 7; fx(g, kind, x, y, dmg);
  }
  // Envelope circle (centre BX, y - ENV_DY) and basket box against a circle.
  function touches(by, ox, oy, r) {
    const dx = ox - K.BX, ey = oy - (by - K.ENV_DY), rr = K.ENV_R + r;
    if (dx * dx + ey * ey <= rr * rr) return true;
    return Math.abs(dx) <= K.BASKET_HALF + r && oy >= by - K.BASKET_H - r && oy <= by + r;
  }

  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 60) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);
    if (g.invuln > 0) g.invuln--;
    if (g.cool > 0) g.cool--;

    // sections: every EVERY frames a new stretch; each one also reshuffles which wind layer is fast
    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVERY === 0) {
      g.section = 1 + tr((g.tick - K.CALM) / K.EVERY) % 5; g.sectionT = K.SECTION_LEN;
      for (let i = 3; i > 0; i--) { const j = rnd(g, i + 1), t = g.order[i]; g.order[i] = g.order[j]; g.order[j] = t; }
      fx(g, FX.SECTION, 160, 100, g.section);
    }
    if (g.sectionT > 0 && --g.sectionT === 0) g.section = 0;

    // vertical: UP heats, OK vents, otherwise the balloon slowly sinks
    g.heating = input.up_held && !input.ok_held ? 1 : 0; g.venting = input.ok_held && !input.up_held ? 1 : 0;
    g.vy += g.heating ? -K.HEAT : g.venting ? K.VENT : K.SINK;
    g.vy -= tr(g.vy / K.DAMP);
    g.vy = Math.max(-K.VMAX, Math.min(K.VMAX, g.vy));
    g.y += g.vy;
    if (g.y < K.YMIN << 8) { g.y = K.YMIN << 8; if (g.vy < 0) g.vy = 0; }
    if (g.y > K.YMAX << 8) {
      g.y = K.YMAX << 8; g.vy = -720;
      if (!g.invuln) { g.grounds++; hurt(g, K.HIT_GROUND, FX.GROUND, K.BX, K.YMAX); }
    }
    const by = px(g.y);

    // fuel: the pilot light always burns; heating burns more
    g.drainAcc += K.DRAIN + Math.min(12, tr(g.tick / K.DRAIN_RAMP)) + (g.heating ? K.DRAIN_HEAT : 0);
    while (g.drainAcc >= 60) { g.res--; g.drainAcc -= 60; }

    // wind layer → horizontal speed (eased so a layer change is felt, not a jump)
    const l = layerOf(by);
    if (l !== g.layer) { g.layer = l; fx(g, FX.WIND, K.BX, by, l); }
    const target = layerSpeed(g, l);
    g.spd += tr((target - g.spd) / 16) + (target > g.spd ? 1 : target < g.spd ? -1 : 0);
    g.dist += g.spd;
    const cam = camX(g), bxw = cam + K.BX;

    // drop a letter: it keeps the balloon's ground speed, so on screen it falls straight down
    if (input.down_down && !g.cool) {
      const L = g.letters.find(e => !e.on);
      if (L) { Object.assign(L, { on: 1, x: bxw << 8, y: (by - 4) << 8, vx: g.spd, vy: g.vy > 0 ? g.vy : 0, y0: by - 4 }); g.cool = K.COOLDOWN; g.drops++; }
    }

    // world objects
    for (const o of g.objs) {
      if (!o.type) continue;
      if (o.type === T.BIRD) { o.x -= 1; o.v++; }
      if (o.type === T.STORM) o.t++;
      const sx = o.x - cam;
      if (sx < K.CULL) {
        if (o.type === T.HOUSE && !o.done) { g.skipped++; if (g.combo) fx(g, FX.SKIP, 20, o.y - 20, 0); g.combo = 0; }
        clear(o); continue;
      }
      if (o.done) continue;
      if (o.type === T.HOUSE) {
        if (sx < K.BX - 40) { o.done = 2; g.skipped++; if (g.combo) fx(g, FX.SKIP, sx, o.y - 20, 0); g.combo = 0; }
      } else if (o.type === T.TREE) {
        const hw = o.v ? 6 : 11;
        if (Math.abs(sx - K.BX) <= hw + K.BASKET_HALF) {
          if (by > o.y) hurt(g, K.HIT_TREE, FX.HIT, sx, o.y);
          else if (by > o.y - 8 && !o.n && sx <= K.BX) { o.n = 1; g.nearMiss++; fx(g, FX.NEAR, sx, o.y - 16, 0); }
        }
      } else if (o.type === T.BIRD) {
        const q = o.v & 63, oy = o.y + tr(((q < 32 ? q : 64 - q) - 16) * 3 / 8);
        if (touches(by, sx, oy, 5)) { o.done = 1; hurt(g, K.HIT_BIRD, FX.HIT, sx, oy); }
        else if (!o.n && sx < K.BX && touches(by, sx, oy, 17)) { o.n = 1; g.nearMiss++; fx(g, FX.NEAR, sx, oy - 10, 0); }
      } else if (o.type === T.STORM) {
        if (Math.abs(sx - K.BX) <= K.STORM_HALF + K.ENV_R - 6 && by - K.ENV_DY - K.ENV_R <= o.y + K.STORM_H) hurt(g, K.HIT_STORM, FX.HIT, sx, o.y);
        const p = stormPhase(o);
        if (p >= K.STORM_BOLT && p < K.STORM_END && Math.abs(sx - K.BX) <= K.BOLT_HALF + K.ENV_R && by - K.ENV_DY - K.ENV_R < o.y + K.STORM_H + K.BOLT_LEN) hurt(g, K.HIT_STORM, FX.HIT, sx, by - K.ENV_DY);
      } else if (o.type === T.TANK) {
        if (touches(by, sx, o.y, 9)) { o.done = 1; g.res = Math.min(1000, g.res + K.TANK); g.tanks++; g.cue = 6; fx(g, FX.TANK, sx, o.y, K.TANK); }
      }
    }

    // letters
    for (const L of g.letters) {
      if (!L.on) continue;
      L.vy = Math.min(K.LETTER_VMAX, L.vy + K.GRAV); L.x += L.vx; L.y += L.vy;
      const lx = px(L.x), ly = px(L.y);
      let land = ly >= K.GROUND ? K.GROUND : 0, hit = null;
      for (const o of g.objs) {
        if (o.type !== T.HOUSE || ly < o.y) continue;
        const dx = lx - o.x;
        if (Math.abs(dx) <= 24) { land = o.y; if (!o.done && Math.abs(dx) <= K.BOX_HALF) hit = o; break; }
      }
      if (!land) continue;
      L.on = 0;
      if (hit) {
        hit.done = 1; g.combo++; g.delivered++; if (g.combo > g.best) g.best = g.combo;
        const bull = Math.abs(lx - hit.x) <= K.BULL, gold = hit.v & 1, high = hit.y - L.y0 >= K.HIGH_DROP;
        let pts = K.PTS * mult(g); if (bull) pts *= 2; if (gold) pts *= K.GOLD; if (high) pts += tr(pts / 2);
        g.bonus += pts; g.res = Math.min(1000, g.res + (gold ? K.TIP_GOLD : K.TIP));
        if (bull) g.bulls++; if (gold) g.golds++;
        fx(g, bull ? FX.BULL : FX.DELIVER, hit.x - camX(g), hit.y - 14, pts); g.cue = 6;
      } else { g.missDrops++; g.combo = 0; g.res -= K.MISS_COST; fx(g, FX.MISS, lx - camX(g), land - 6, 0); }
    }

    // spawning ahead
    const ahead = cam + K.W + 40;
    while (g.nextGround < ahead + K.AHEAD - 320) spawnGround(g, g.nextGround);
    while (g.nextSky < ahead + K.AHEAD - 320) spawnSky(g, g.nextSky);

    g.meters = tr(px(g.dist) / 16);
    g.score = tr(g.meters / 2) + g.bonus;
    if (g.res <= 0) { g.res = 0; g.over = 1; g.cue = 8; }
    return g;
  }

  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'y', 'vy', 'dist', 'spd', 'layer', 'heating', 'venting', 'drainAcc', 'invuln', 'cool',
    'combo', 'best', 'bonus', 'delivered', 'bulls', 'golds', 'skipped', 'missDrops', 'drops', 'hits', 'tanks', 'nearMiss', 'grounds',
    'section', 'sectionT', 'nextGround', 'nextSky', 'houses', 'presses', 'blocked', 'fxHead', 'meters'];
  function view(g) {
    const out = HEAD.map(k => g[k]).concat(g.order);
    for (const o of g.objs) out.push(o.type, o.x, o.y, o.v, o.t, o.done, o.n);
    for (const L of g.letters) out.push(L.on, L.x, L.y, L.vx, L.vy, L.y0);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }
  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, T, SEC, FX, HEAD, start, step, status, view, random, mult, layerOf, layerSpeed, camX, stormPhase, touches };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvSkyV2 = api;
})(typeof window !== 'undefined' ? window : globalThis);
