// POST V2 test players: read signs, signals and animals on screen; drive with throttle/brake; tap at the mail door.
const S = require('../game-art/adventure/prototype/adv_post_v2.js'), K = S.K, T = S.T;
const stopDist = (v, to) => (v <= to ? 0 : Math.trunc((v * v - to * to) / (2 * K.BRAKE) / 256));   // px needed to brake from v to `to`
function driver(kind, seed) {
  if (kind === 'expert') kind = 'skilled';
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => ({ up_held: 1, down_down: g.tick % 12 === 0 ? 1 : 0 });          // full steam, mash the throw
  if (kind === 'wiggle') return g => ((g.tick / 60 | 0) % 2 ? { up_held: 1 } : { ok_held: 1 });
  const cruise = kind === 'casual' ? 560 : 820, aimJ = kind === 'casual' ? 9 : 3, look = kind === 'casual' ? 0.75 : 1.1, margin = kind === 'casual' ? 30 : 12;
  let aim = 0;
  return g => {
    const c = S.cam(g); let target = cruise;
    for (const e of g.ev) {
      if (!e.type || e.done) continue;
      const ahead = e.x - c - K.FRONT_X;
      if (ahead < -400 || ahead > 300) continue;
      if (e.type === T.LIMIT && (ahead > 0 ? ahead < stopDist(g.v, e.a) * look + margin : e.x + e.b - c > K.LOCO_X - 48)) target = Math.min(target, e.a);
      if (e.type === T.SIGNAL && ahead > 0 && e.t >= 0) {
        const left = e.a - (g.tick - e.t), eta = g.v ? ahead * 256 / g.v : 1e9;
        if (left > 0 && eta < left + 10 && ahead < stopDist(g.v, K.SLOW) * look + margin + 40) target = Math.min(target, K.SLOW - 20);
      }
      if (e.type === T.ANIMAL && ahead > 0 && e.t >= 0) {
        const left = e.a - (g.tick - e.t), eta = g.v ? ahead * 256 / g.v : 1e9;
        if (left > 0 && eta < left + 6 && ahead < stopDist(g.v, 0) * look + margin + 40) target = Math.min(target, Math.max(0, Math.trunc(ahead * 256 / (left + 12))));
      }
    }
    const input = g.v > target + 10 ? { ok_held: 1 } : g.v < target - 10 ? { up_held: 1 } : {};
    let best = null, bd = 1e9;
    for (const e of g.ev) if ((e.type === T.NET || e.type === T.CRANE) && !e.done) { const d = e.x - c - K.DOOR_X; if (Math.abs(d) < Math.abs(bd)) { bd = d; best = e; } }
    if (best && (best.type === T.CRANE || g.bags > 0)) {
      if (!aim) aim = (r() % (2 * aimJ + 1)) - aimJ || 1;
      if (Math.abs(bd - aim) <= Math.max(1, g.v >> 8)) { input.down_down = 1; aim = 0; }
    }
    return input;
  };
}
module.exports = { driver };
