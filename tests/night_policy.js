// NIGHT V2 test players. They only use what the screen shows: fireflies, moths, roots inside the
// light, and the owl's ground ring. driver(kind, seed) returns g -> adv_input_t bits.
const N = require('../game-art/adventure/prototype/adv_night.js'), K = N.K;

function netHits(g, lead, gait) {          // fireflies/moths the net would sweep if swung `lead` frames from now
  const v = N.speedOf(g, gait), ny = K.GROUND - K.NET_DY;
  let flies = 0, moths = 0;
  for (let t = K.SWING_ON; t <= K.SWING_OFF; t++) {
    const nx = ((g.x + v * (lead + t)) >> 8) + K.NET_DX, tick = g.tick + lead + t + 1;
    for (const f of g.flies) if (f.type) { const dx = ((f.x + f.vx * (lead + t)) >> 8) - nx, dy = N.flyY(f, tick) - ny; if (dx * dx + dy * dy <= (K.NET_R - 3) ** 2) flies++; }
    for (const m of g.moths) if (m.rr) { const dx = (m.x >> 8) - nx, dy = (m.y >> 8) - ny; if (dx * dx + dy * dy <= (K.MOTH_R + 6) ** 2) moths++; }
  }
  return { flies, moths };
}
const visibleRoot = (g, reach) => g.roots.some(r => r.state === 1 && r.x > (g.x >> 8) && r.x - (g.x >> 8) < Math.min(N.radius(g), reach));
const owlThreat = g => g.owls.find(o => o.live && o.t > 0 && Math.abs(o.tx - g.x - N.speedOf(g, g.gait) * o.t) < (40 << 8));

function driver(kind, seed) {
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => ({ down_down: g.tick % 20 === 0 ? 1 : 0 });
  if (kind === 'casual') return g => {          // walks, swings late-ish, sometimes into moths
    const h = netHits(g, 4, g.gait);
    return { down_down: g.swing === 0 && h.flies >= 1 && r() % 3 === 0 ? 1 : 0 };
  };
  if (kind === 'mistakes') return g => {        // runs everywhere and swings at moths
    const h = netHits(g, 0, 2);
    return { up_held: 1, up_down: g.tick === 1 ? 1 : 0, down_down: g.swing === 0 && (h.moths || h.flies) ? 1 : 0 };
  };
  // skilled: runs when the lit path is clear, dodges owls by changing pace, never nets moths, bursts when full
  return g => {
    const owl = owlThreat(g), root = visibleRoot(g, 70);
    let left = 0, right = 0;
    if (owl) { if (owl.tx > g.x + (30 << 8)) left = 1; else right = root ? 0 : 1; }
    else if (!root && g.light > 250000) right = 1;
    const gait = left ? 0 : right ? 2 : 1, h = netHits(g, 0, gait);
    const burst = g.meter >= N.meterFull(g) && g.tick - g.lastSwing <= 10 && g.tick - g.lastSwing > 2;
    return { ok_held: left, up_held: right, down_down: burst || (g.swing === 0 && h.flies >= 1 && h.moths === 0) ? 1 : 0 };
  };
}
module.exports = { driver, netHits };
