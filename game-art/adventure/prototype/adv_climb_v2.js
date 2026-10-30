// CLIMB V2「双线攀岩」rules reference (G1): integer 60 Hz, mulberry32, landscape 320x240.
// The wall has two climbing lanes. Each lane is a ladder of rows; a row's hold sits on the left or right of the lane,
// alternating, so climbing is a left-right rhythm. Holds can be blank (lane broken), fragile (crumbles), or icy (hold the key).
// Keys (landscape, left to right): OK = left hand, DOWN = tap to traverse to the other lane, UP = right hand.
// Long-press DOWN is the shell's pause; traverse fires on the press edge, so nothing needs DOWN held.
// Approved 2026-10-30: firmware/main/adv_climb_v2.c mirrors these rules; V1 stays available for rollback.
(function (root) {
  'use strict';
  const K = {
    W: 320, H: 240, NY: 150, STEP: 26, LANE_X: [104, 216], HOLD_DX: 23, ROWS: 32, AHEAD: 14,
    TWEEN: 6, RHYTHM: 24, COMBO_IDLE: 70, STUN: 18, TRAVERSE: 14, ICE_HOLD: 15, CRUMBLE: 42,
    DRAIN: 28, DRAIN_ROWS: 8, DRAIN_MAX: 40, GAIN: 22, GAIN_RHYTHM: 26, SLIP: 90, ROCK_HIT: 170, TRAV_COST: 10, GAIN_MIN: 8, GAIN_FADE: 16,
    CANTEEN: 260, FLAG: 30, INVULN: 50,
    ROCKS: 3, ROCK_WARN: 75, ROCK_V: 5, ROCK_TOP: -16,
    CALM: 900, EVERY: 1500, SECTION_LEN: 900,
  };
  const H = { BLANK: 0, NORMAL: 1, FRAGILE: 2, ICE: 3 };
  const ITEM = { NONE: 0, CANTEEN: 1, FLAG: 2 };
  const SEC = { NONE: 0, ROCKS: 1, ICE: 2, CRUMBLE: 3, NIGHT: 4, SPRINT: 5 };
  const FX = { GRAB: 1, SLIP: 2, ROCK: 3, CANTEEN: 4, FLAG: 5, SECTION: 6, NEAR: 7, NOHOLD: 8, CRUMBLE: 9, TRAVERSE: 10, RHYTHM: 11 };
  function random(g) { g.rng = (g.rng + 0x6D2B79F5) >>> 0; let t = g.rng; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) >>> 0; }
  const rnd = (g, n) => random(g) % n, tr = Math.trunc;

  function start(seed) {
    const g = { rng: seed >>> 0, tick: 0, score: 0, res: 1000, over: 0, cue: 0, row: 0, lane: 0, tween: 0, stun: 0, trav: 0, ice: 0, iceSide: 0,
      crumble: 0, invuln: 0, lastGrab: -99, combo: 0, best: 0, bonus: 0, drainAcc: 0, genRow: 0, blankRun: [0, 0],
      grabs: 0, rhythmGrabs: 0, slips: 0, rockHits: 0, nearMiss: 0, canteens: 0, flags: 0, traverses: 0, crumbles: 0, iceSlips: 0,
      section: 0, sectionT: 0, nextRock: 420, presses: 0, fxHead: 0, meters: 0,
      rows: Array.from({ length: K.ROWS }, () => ({ h0: 0, h1: 0, i0: 0, i1: 0 })),
      rocks: Array.from({ length: K.ROCKS }, () => ({ on: 0, lane: 0, t: 0, y: 0, n: 0 })),
      fx: Array.from({ length: 6 }, () => ({ kind: 0, x: 0, y: 0, val: 0, t: 0 })) };
    for (let r = 0; r <= K.AHEAD; r++) gen(g);
    return g;
  }
  const rowAt = (g, r) => g.rows[r % K.ROWS];
  const holdAt = (g, r, lane) => (lane ? rowAt(g, r).h1 : rowAt(g, r).h0);
  // A row's hold side alternates up each lane; the two lanes are out of phase so a traverse can change the next hand.
  const sideOf = (r, lane) => (r + lane) & 1;       // 0 = left, 1 = right
  const holdX = (r, lane) => K.LANE_X[lane] + (sideOf(r, lane) ? K.HOLD_DX : -K.HOLD_DX);
  const mult = g => 1 + Math.min(4, tr(g.combo / 6));
  function fx(g, kind, x, y, val) { Object.assign(g.fx[g.fxHead], { kind, x, y, val, t: 0 }); g.fxHead = (g.fxHead + 1) % 6; }

  function gen(g) {
    const r = g.genRow++, o = rowAt(g, r), s = g.section;
    if (r < 3) { Object.assign(o, { h0: H.NORMAL, h1: H.NORMAL, i0: 0, i1: 0 }); return; }
    const pick = () => { const v = rnd(g, 100), ice = s === SEC.ICE ? 45 : 10, fr = s === SEC.CRUMBLE ? 45 : 10; return v < ice ? H.ICE : v < ice + fr ? H.FRAGILE : H.NORMAL; };
    let h = [pick(), pick()];
    // breaks: one lane goes blank for 2..4 rows, never both, never right after the other lane's break
    for (let l = 0; l < 2; l++) {
      if (g.blankRun[l] > 0) { h[l] = H.BLANK; g.blankRun[l]--; }
      else if (!g.blankRun[1 - l] && r > 6 && rnd(g, 100) < 9) { g.blankRun[l] = 1 + rnd(g, 3); h[l] = H.BLANK; }
    }
    if (h[0] === H.BLANK && h[1] === H.BLANK) h[rnd(g, 2)] = H.NORMAL;
    const items = [0, 0];
    if (rnd(g, 100) < 7) { const l = rnd(g, 2); if (h[l]) items[l] = rnd(g, 100) < 45 ? ITEM.CANTEEN : ITEM.FLAG; }
    Object.assign(o, { h0: h[0], h1: h[1], i0: items[0], i1: items[1] });
  }

  function slip(g, kind) {
    if (g.row > 0) g.row--;
    while (g.row > 0 && !holdAt(g, g.row, g.lane)) g.row--;   // slide down to the nearest hold in this lane
    g.stun = K.STUN; g.res -= K.SLIP; g.combo = 0; g.ice = 0; g.crumble = 0; g.slips++; g.cue = 7; g.tween = K.TWEEN;
    fx(g, kind, K.LANE_X[g.lane], K.NY - 30, 0);
  }
  function arrive(g) {
    const h = holdAt(g, g.row, g.lane), o = rowAt(g, g.row), it = g.lane ? o.i1 : o.i0;
    const rhythm = g.tick - g.lastGrab <= K.RHYTHM || g.section === SEC.SPRINT && g.tick - g.lastGrab <= K.RHYTHM + 10;
    g.lastGrab = g.tick; g.grabs++;
    if (rhythm) { g.combo++; g.rhythmGrabs++; if (g.combo > g.best) g.best = g.combo; } else g.combo = Math.max(0, g.combo - 2);
    g.res = Math.min(1000, g.res + Math.max(K.GAIN_MIN, (rhythm ? K.GAIN_RHYTHM : K.GAIN) - tr(g.row / K.GAIN_FADE)));
    g.bonus += mult(g) * (g.section === SEC.SPRINT ? 2 : 1);
    g.crumble = h === H.FRAGILE ? K.CRUMBLE : 0;
    if (it) {
      if (g.lane) o.i1 = 0; else o.i0 = 0;
      if (it === ITEM.CANTEEN) { g.res = Math.min(1000, g.res + K.CANTEEN); g.canteens++; fx(g, FX.CANTEEN, holdX(g.row, g.lane), K.NY - 20, K.CANTEEN); }
      else { const p = K.FLAG * mult(g); g.bonus += p; g.flags++; fx(g, FX.FLAG, holdX(g.row, g.lane), K.NY - 20, p); }
      g.cue = 6;
    }
    if (g.combo && g.combo % 10 === 0) fx(g, FX.RHYTHM, 160, 60, g.combo);
    g.tween = K.TWEEN;
  }

  function step(g, input = {}) {
    g.cue = 0;
    for (const e of g.fx) if (e.kind && ++e.t >= 60) e.kind = 0;
    if (g.over) return g;
    g.tick++;
    g.presses += (input.ok_down ? 1 : 0) + (input.up_down ? 1 : 0) + (input.down_down ? 1 : 0);
    if (g.invuln > 0) g.invuln--;
    if (g.tween > 0) g.tween--;

    if (g.tick >= K.CALM && (g.tick - K.CALM) % K.EVERY === 0) { g.section = 1 + tr((g.tick - K.CALM) / K.EVERY) % 5; g.sectionT = K.SECTION_LEN; fx(g, FX.SECTION, 160, 100, g.section); }
    if (g.sectionT > 0 && --g.sectionT === 0) g.section = 0;
    if (g.tick - g.lastGrab > K.COMBO_IDLE && g.combo) g.combo = 0;

    // hands
    if (g.stun > 0) g.stun--;
    else if (g.trav > 0) { if (--g.trav === 0) { g.lane ^= 1; while (g.row > 0 && !holdAt(g, g.row, g.lane)) { g.row--; } g.crumble = holdAt(g, g.row, g.lane) === H.FRAGILE ? K.CRUMBLE : 0; g.tween = K.TWEEN; } }
    else if (g.ice) {
      const held = g.iceSide ? input.up_held : input.ok_held;
      if (!held) { g.iceSlips++; slip(g, FX.SLIP); }
      else if (--g.ice === 0) arrive(g);
    } else if (input.down_down) {
      g.trav = K.TRAVERSE; g.res -= K.TRAV_COST; g.traverses++; g.crumble = 0; fx(g, FX.TRAVERSE, K.LANE_X[g.lane], K.NY, 0);
    } else if ((input.ok_down || input.up_down) && g.tween <= 2) {
      const side = input.ok_down && !input.up_down ? 0 : input.up_down && !input.ok_down ? 1 : -1, next = g.row + 1, h = holdAt(g, next, g.lane);
      if (side < 0) slip(g, FX.SLIP);
      else if (!h) { g.stun = 8; g.combo = 0; fx(g, FX.NOHOLD, K.LANE_X[g.lane], K.NY - 50, 0); }
      else if (side !== sideOf(next, g.lane)) slip(g, FX.SLIP);
      else { g.row = next; if (h === H.ICE) { g.ice = K.ICE_HOLD; g.iceSide = side; g.tween = K.TWEEN; } else arrive(g); }
    }
    if (g.crumble > 0 && !g.trav && --g.crumble === 0) { g.crumbles++; const o = rowAt(g, g.row); if (g.lane) o.h1 = H.BLANK; else o.h0 = H.BLANK; slip(g, FX.CRUMBLE); }

    // grip drains while hanging, faster the higher you are
    g.drainAcc += K.DRAIN + Math.min(K.DRAIN_MAX, tr(g.row / K.DRAIN_ROWS));
    while (g.drainAcc >= 60) { g.res--; g.drainAcc -= 60; }

    // falling rocks: a warning at the top of one lane, then the rock drops past NABO's height
    if (g.tick >= g.nextRock) {
      const k = g.rocks.find(e => !e.on);
      if (k) Object.assign(k, { on: 1, lane: rnd(g, 2), t: K.ROCK_WARN, y: K.ROCK_TOP, n: 0 });
      g.nextRock = g.tick + (g.section === SEC.ROCKS ? 80 : 200) + rnd(g, g.section === SEC.ROCKS ? 60 : 180);
    }
    for (const k of g.rocks) {
      if (!k.on) continue;
      if (k.t > 0) { k.t--; continue; }
      k.y += K.ROCK_V;
      if (!k.n && k.y >= K.NY - 56 && k.y <= K.NY + 4) {
        const inLane = g.trav ? g.trav > K.TRAVERSE / 2 ? g.lane === k.lane : g.lane !== k.lane : g.lane === k.lane;
        if (inLane && !g.invuln) { k.n = 1; g.rockHits++; g.res -= K.ROCK_HIT - K.SLIP; g.invuln = K.INVULN; slip(g, FX.ROCK); }
        else if (!inLane && k.y >= K.NY - 4) { k.n = 1; g.nearMiss++; fx(g, FX.NEAR, K.LANE_X[g.lane], K.NY - 40, 0); }
      }
      if (k.y > K.H + 20) k.on = 0;
    }

    while (g.genRow <= g.row + K.AHEAD) gen(g);
    g.meters = tr(g.row / 2);
    g.score = g.meters + g.bonus;
    if (g.res <= 0) { g.res = 0; g.over = 1; g.cue = 8; }
    return g;
  }

  const HEAD = ['rng', 'tick', 'score', 'res', 'over', 'cue', 'row', 'lane', 'tween', 'stun', 'trav', 'ice', 'iceSide', 'crumble', 'invuln', 'lastGrab',
    'combo', 'best', 'bonus', 'drainAcc', 'genRow', 'grabs', 'rhythmGrabs', 'slips', 'rockHits', 'nearMiss', 'canteens', 'flags', 'traverses',
    'crumbles', 'iceSlips', 'section', 'sectionT', 'nextRock', 'presses', 'fxHead', 'meters'];
  function view(g) {
    const out = HEAD.map(k => g[k]).concat(g.blankRun);
    for (const o of g.rows) out.push(o.h0, o.h1, o.i0, o.i1);
    for (const k of g.rocks) out.push(k.on, k.lane, k.t, k.y, k.n);
    for (const e of g.fx) out.push(e.kind, e.x, e.y, e.val, e.t);
    return out;
  }
  const status = g => ({ score: g.score, res: g.res, over: g.over });
  const api = { K, H, ITEM, SEC, FX, HEAD, start, step, status, view, random, mult, rowAt, holdAt, sideOf, holdX };
  if (typeof module !== 'undefined') module.exports = api; else root.AdvClimbV2 = api;
})(typeof window !== 'undefined' ? window : globalThis);
