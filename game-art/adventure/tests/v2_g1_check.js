// G1 sanity for the SKY V2 / CLIMB V2 rule files: integer-only state, deterministic replay, no slot overflow.
// node game-art/adventure/tests/v2_g1_check.js   (not a golden; goldens come with the C port after user approval)
'use strict';
const games = [
  ['sky_v2', require('../prototype/adv_sky_v2.js'), require('../../../tests/sky_v2_policy.js')],
  ['climb_v2', require('../prototype/adv_climb_v2.js'), require('../../../tests/climb_v2_policy.js')],
];
let fail = 0;
const hash = a => { let h = 2166136261; for (const v of a) { h ^= v & 0xffff; h = Math.imul(h, 16777619); h ^= v >>> 16; h = Math.imul(h, 16777619); } return h >>> 0; };
for (const [name, G, P] of games) {
  for (const kind of ['idle', 'spam', 'casual', 'skilled']) {
    for (let s = 1; s <= 12; s++) {
      const run = () => { const g = G.start(s * 104729), d = P.driver(kind, s); let h = 0, steps = 0;
        while (!g.over && g.tick < 60 * 300) { G.step(g, d(g)); const v = G.view(g); steps++;
          if (steps % 7 === 0) for (const x of v) if (!Number.isInteger(x)) { console.log(`${name} ${kind} seed ${s}: non-integer state ${x} at tick ${g.tick}`); fail++; return [0, 0, g]; }
          h = hash([h, ...v]); }
        return [h, steps, g]; };
      const [h1, n1, g1] = run(), [h2, n2] = run();
      if (h1 !== h2 || n1 !== n2) { console.log(`${name} ${kind} seed ${s}: replay differs`); fail++; }
      if (g1.blocked) { console.log(`${name} ${kind} seed ${s}: ${g1.blocked} spawns dropped (slot table full)`); fail++; }
    }
  }
  console.log(`${name}: checked`);
}
if (fail) { console.log(`FAIL ${fail}`); process.exit(1); } else console.log('PASS');
