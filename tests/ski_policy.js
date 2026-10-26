// SKI V2 test players: only what the screen shows (objects below NABO, the avalanche gap).
const S = require('../game-art/adventure/prototype/adv_ski.js'), K = S.K, T = S.T;
const ahead = (g, sight) => g.objs.filter(o => o.type && !o.done && o.y > (g.y >> 8) && o.y - (g.y >> 8) < sight).sort((a, b) => a.y - b.y);
function steer(g, target, dead = 4) {
  const x = g.x >> 8, brake = Math.trunc(g.vx * Math.abs(g.vx) / (2 * K.STEER * 256)), need = target - x - brake;
  return need > dead ? { up_held: 1 } : need < -dead ? { ok_held: 1 } : {};
}
function driver(kind, seed) {
  if (kind === 'expert') kind = 'skilled';
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => ({ down_down: g.tick % 25 === 0 ? 1 : 0 });
  if (kind === 'wiggle') return g => (Math.floor(g.tick / 40) % 2 ? { ok_held: 1 } : { up_held: 1 });
  const sight = kind === 'casual' ? 70 : 150;
  return g => {
    const x = g.x >> 8, list = ahead(g, sight), gate = list.find(o => o.type <= T.GATE_BLUE);
    let target = gate ? gate.x : x;
    if (kind === 'casual' && r() % 5 === 0) target += (r() % 41) - 20;
    for (const o of list) {
      const block = o.type === T.TREE || (o.type === T.PINE && kind === 'casual');
      if (block && Math.abs(o.x - target) < 24 && (!gate || o.y < gate.y)) target = o.x < target ? o.x + 30 : o.x - 30;
      if (kind === 'skilled' && o.type === T.KICKER && (!gate || o.y < gate.y - 60)) target = o.x;
    }
    const input = steer(g, Math.max(K.LEFT, Math.min(K.RIGHT, target)));
    const near = list.find(o => (o.type === T.PINE || o.type === T.MOGUL || o.type === T.DRIFT) && Math.abs(o.x - x) < 14 && o.y - (g.y >> 8) < (g.v >> 8) * 6);
    if (!g.air && near && kind !== 'casual') input.down_down = 1;
    if (kind === 'skilled' && g.air && g.kicked && g.spinT === 0 && g.air > K.SPIN + 4) input.down_down = 1;
    return input;
  };
}
module.exports = { driver };
