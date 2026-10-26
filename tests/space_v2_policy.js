// SPACE V2 火箭登月 test players: they see what is on screen (objects above the rocket, gauges, the pad).
const S = require('../game-art/adventure/prototype/adv_space_v2.js'), K = S.K, T = S.T;
const GOOD = new Set([T.STAR, T.FUEL, T.REPAIR, T.RING]);
function driver(kind, seed) {
  if (kind === 'expert') kind = 'skilled';
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => ({ down_down: g.tick % 15 === 0 ? 1 : 0 });
  const sloppy = kind === 'casual', slack = sloppy ? 10 : 3;
  return g => {
    const input = {};
    if (g.mode === S.MODE.IGNITE) { if (Math.abs(S.gauge(g.modeT + 1) - 80) <= slack + (sloppy ? r() % 8 : 0)) input.down_down = 1; return input; }
    if (g.mode === S.MODE.LAND) {
      const x = g.lx >> 8, h = K.GROUND - (g.ly >> 8), dx = g.pad - x, want = Math.max(-300, Math.min(300, dx * 6));
      if (g.lvx < want - 30) input.up_held = 1; else if (g.lvx > want + 30) input.ok_held = 1;
      const limit = h > 120 ? 420 : h > 50 ? 240 : sloppy ? 200 : 110;
      if (g.lvy > limit && g.tick % 3 === 0) input.down_down = 1;
      return input;
    }
    if (g.mode !== S.MODE.FLY) return input;
    if (g.sep === 1) { if (Math.abs(Math.trunc((g.sepT + 1) * 100 / K.SEP_T) - 78) <= (sloppy ? 9 : 2)) input.down_down = 1; }
    else if (g.tli === 1) { const at = K.TLI_LEAD + g.tliHit * K.TLI_BEAT; if (g.tliT + 1 === at + (sloppy ? (r() % 9) - 4 : 0)) input.down_down = 1; }
    const alt = g.alt >> 8, rx = g.x >> 8, sight = sloppy ? 110 : 190;
    let target = rx, danger = 0;
    // flee the nearest threat in sight; otherwise go for the nearest pickup
    let threat = null, prize = null, smash = 0;
    for (const o of g.objs) {
      if (!o.type || o.done) continue;
      const dy = o.y - alt; if (dy < -10 || dy > sight) continue;
      const lead = Math.max(0, Math.trunc(dy * 256 / Math.max(200, g.v))), ox = ((o.x + (o.vx === 1 || o.vx === -1 ? 0 : o.vx) * lead) >> 8);
      if (o.type === T.STORM) { if (o.state > 0 && o.state < 60) { threat = threat || { x: o.x >> 8, w: 26 }; } continue; }
      if (o.type === T.GUST || o.type === T.JET) continue;
      if (GOOD.has(o.type)) { if (!prize || dy < prize.dy) prize = { x: ox, dy }; continue; }
      if (Math.abs(ox - rx) < S.R[o.type] + 24 && S.SMALL.has(o.type) && !sloppy && dy < 70 && g.heat < 500 && g.tick - g.lastBoost >= K.BOOST_GAP) { smash = 1; continue; }
      if (Math.abs(ox - rx) < S.R[o.type] + 24 && (!threat || dy < threat.dy)) threat = { x: ox, w: S.R[o.type] + 26, dy };
    }
    if (threat) { danger = 1; target = threat.x > rx ? threat.x - threat.w : threat.x + threat.w; if (target < K.LEFT + 10) target = threat.x + threat.w; if (target > K.RIGHT - 10) target = threat.x - threat.w; }
    else if (prize) target = prize.x;
    if (sloppy && r() % 6 === 0) target = rx;
    const want = Math.max(-600, Math.min(600, (target - rx) * 10)) - (g.push * 200);
    if (g.vx < want - 40) input.up_held = 1; else if (g.vx > want + 40) input.ok_held = 1;
    if (g.sep !== 1 && g.tli !== 1 && !input.down_down && (smash || (sloppy && !danger && g.heat < 500 && g.fuel > 40000 && g.tick - g.lastBoost > 150))) input.down_down = 1;
    return input;
  };
}
module.exports = { driver };
