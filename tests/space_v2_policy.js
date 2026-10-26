// SPACE V2 test players: they see the moon, the pads, the cans and the meteors that are on screen.
const S = require('../game-art/adventure/prototype/adv_space_v2.js'), K = S.K;
function driver(kind, seed) {
  if (kind === 'expert') kind = 'skilled';
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => ({ down_down: g.tick % 12 === 0 ? 1 : 0, up_held: 1 });
  const sloppy = kind === 'casual', margin = sloppy ? 40 : 30, land = sloppy ? 170 : 140;
  let lastPulse = 0;
  return g => {
    if (g.phase === S.PH.CRASHED) return {};
    const x = g.x >> 8, feet = g.y >> 8, target = S.pad(g.seed, g.bestChunk + 1);
    if (g.phase === S.PH.LANDED && g.phaseT < K.TAKEOFF_T + (sloppy ? 20 : 0)) return {};
    const dx = target.x - x;
    let top = 999;
    for (let t = Math.min(x, target.x) - 40; t <= Math.max(x, target.x) + 40; t += 8) top = Math.min(top, S.ground(g.seed, t));
    const cruise = Math.max(K.CEIL + 4, top - margin), near = Math.abs(dx) < (sloppy ? 14 : 8);
    const want = near ? 0 : Math.max(-420, Math.min(420, dx * (sloppy ? 3 : 4)));
    const input = {};
    let dodge = 0;                    // a meteor that will pass close to the lander soon: slide away from it
    for (const m of g.rocks) if (m.live) for (let t = 0; t < (sloppy ? 25 : 45); t += 5) {
      const mx = (m.x + m.vx * t) >> 8, my = (m.y + m.vy * t) >> 8, lx = (g.x + g.vx * t) >> 8, ly = ((g.y + g.vy * t) >> 8) - 44;
      if (Math.abs(mx - lx) < 40 && Math.abs(my - ly) < 40) { dodge = mx > lx ? -1 : 1; break; }
    }
    const goal = dodge ? dodge * 420 : want;
    if (g.vx < goal - 30) input.up_held = 1; else if (g.vx > goal + 30) input.ok_held = 1;
    let pulse;
    if (!near && Math.abs(dx) > 50) pulse = feet > cruise ? g.vy > -60 : g.vy > 150;
    else { const h = target.y - feet; pulse = h < 50 ? g.vy > land : h < 110 ? g.vy > (sloppy ? 260 : 320) : g.vy > (sloppy ? 420 : 560); }
    if (g.phase === S.PH.LANDED) pulse = true;
    if (sloppy && r() % 4 === 0) pulse = false;
    if (pulse && g.tick - lastPulse >= (sloppy ? 6 : 4)) { input.down_down = 1; lastPulse = g.tick; }
    return input;
  };
}
module.exports = { driver };
