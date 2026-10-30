// SKY V2 test players: they only use what the screen shows (objects ahead, wind arrows, fuel).
const S = require('../game-art/adventure/prototype/adv_sky_v2.js'), K = S.K, T = S.T;
const fallFrames = d => { let y = 0, v = 0, n = 0; while (y < d << 8 && n < 200) { v = Math.min(K.LETTER_VMAX, v + K.GRAV); y += v; n++; } return n; };
function hold(g, target, slack) {
  const y = g.y >> 8, pred = y + Math.trunc(g.vy * 18 / 256);
  return pred > target + 2 ? { up_held: 1 } : pred < target - slack ? { ok_held: 1 } : {};
}
function driver(kind, seed) {
  if (kind === 'expert') kind = 'skilled';
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => ({ down_down: g.tick % 20 === 0 ? 1 : 0, up_held: (g.tick >> 5) & 1 });
  if (kind === 'wiggle') return g => ((g.tick / 50 | 0) % 2 ? { up_held: 1 } : { ok_held: 1 });
  const sight = kind === 'casual' ? 150 : 230, jitter = kind === 'casual' ? 9 : 2;
  let aimErr = 0;
  return g => {
    const cam = S.camX(g), y = g.y >> 8, objs = g.objs.filter(o => o.type && o.x - cam > K.BX - 30 && o.x - cam < K.BX + sight);
    // preferred cruise: the fastest layer the player can see on the wind arrows (casual just stays low-ish)
    let best = 3, bs = -1;
    for (let l = 0; l < 4; l++) { const v = S.layerSpeed(g, l); if (v > bs) { bs = v; best = l; } }
    let target = kind === 'casual' ? 172 : [112, 144, 172, 196][best];
    const house = objs.filter(o => o.type === T.HOUSE && !o.done && o.x - cam > K.BX).sort((a, b) => a.x - b.x)[0];
    if (house && kind === 'skilled' && house.x - cam - K.BX < 160) target = Math.min(target, house.y - 34);
    for (const o of objs) {
      const sx = o.x - cam, close = sx - K.BX < 110;
      if (o.type === T.TREE && close) target = Math.min(target, o.y - 12);
      if (o.type === T.BIRD && close && o.y > target - K.ENV_DY - K.ENV_R - 8 && o.y < target + 12) target = o.y > 150 ? o.y - 4 - K.ENV_DY - K.ENV_R - 10 : o.y + 16;
      if (o.type === T.STORM && Math.abs(sx - K.BX) < 70) {
        const p = S.stormPhase(o);
        if (kind === 'skilled' && p >= K.STORM_WARN - 40 && p < K.STORM_END) target = Math.max(target, o.y + K.STORM_H + K.BOLT_LEN + K.ENV_DY + K.ENV_R + 6);
        target = Math.max(target, o.y + 18 + K.ENV_DY + K.ENV_R + 6);
      }
      if (o.type === T.TANK && close && g.res < 700) target = o.y + 30;
    }
    target = Math.max(K.YMIN, Math.min(K.YMAX - 4, target));
    const input = hold(g, target, kind === 'casual' ? 14 : 8);
    if (house && !g.cool) {
      const lead = Math.trunc(g.spd * fallFrames(house.y - y + 4) / 256), dx = house.x - cam - K.BX;
      if (!aimErr) aimErr = (r() % (2 * jitter + 1)) - jitter;
      if (Math.abs(dx - lead - aimErr) <= 2) { input.down_down = 1; aimErr = 0; }
    }
    return input;
  };
}
module.exports = { driver };
