// CLIMB V2 test players: they read the holds and rock warnings on screen and press with a human-ish tempo.
const S = require('../game-art/adventure/prototype/adv_climb_v2.js'), K = S.K, H = S.H;
function driver(kind, seed) {
  if (kind === 'expert') kind = 'skilled';
  let s = seed >>> 0; const r = () => (s = (Math.imul(s, 1103515245) + 12345) >>> 0) >>> 16;
  if (kind === 'idle') return () => ({});
  if (kind === 'spam') return g => (g.tick % 10 === 0 ? ((g.tick / 10) & 1 ? { up_down: 1 } : { ok_down: 1 }) : {});
  if (kind === 'wiggle') return g => (g.tick % 30 === 0 ? ((g.tick / 30) & 1 ? { up_down: 1 } : { ok_down: 1 }) : {});
  const tempo = kind === 'casual' ? 26 : 15, err = kind === 'casual' ? 6 : 2, react = kind === 'casual' ? 30 : 12;
  let wait = 0, holdSide = -1, holdFor = 0;
  return g => {
    if (holdFor > 0) { holdFor--; return holdSide ? { up_held: 1 } : { ok_held: 1 }; }
    if (g.stun || g.trav || g.ice) return {};
    if (wait > 0) { wait--; return {}; }
    const lane = g.lane, other = lane ^ 1, next = g.row + 1;
    // danger: a rock coming down my lane that I can see
    const rock = g.rocks.find(k => k.on && k.lane === lane && !k.n && (k.t > 0 ? k.t < K.ROCK_WARN - react : k.y < K.NY - 40));
    const rockOther = g.rocks.find(k => k.on && k.lane === other && !k.n && k.y < K.NY + 4);
    const blankAhead = !S.holdAt(g, next, lane) || (kind === 'skilled' && !S.holdAt(g, next + 1, lane) && S.holdAt(g, next, other));
    const lowAndCanteen = kind === 'skilled' && g.res < 600 && [1, 2, 3].some(d => (other ? S.rowAt(g, g.row + d).i1 : S.rowAt(g, g.row + d).i0) === S.ITEM.CANTEEN);
    if (!rockOther && (rock || (blankAhead && S.holdAt(g, g.row, other)) || lowAndCanteen)) { wait = 4; return { down_down: 1 }; }
    wait = tempo - 4 + (r() % 9);
    let side = S.sideOf(next, lane);
    if (r() % 100 < err) side ^= 1;
    if (S.holdAt(g, next, lane) === H.ICE) { holdSide = side; holdFor = K.ICE_HOLD + 2; }
    return side ? { up_down: 1, up_held: 1 } : { ok_down: 1, ok_held: 1 };
  };
}
module.exports = { driver };
