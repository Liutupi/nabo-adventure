// SPACE V2 火箭登月 balance probe: node tests/space_v2_sim.js [seeds]
'use strict';
const S = require('../prototype/adv_space_v2.js'), { driver } = require('../../../tests/space_v2_policy.js');
const seeds = +(process.argv[2] || 60);
for (const kind of ['idle', 'spam', 'casual', 'skilled']) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) { const g = S.start(s * 7919), d = driver(kind, s); while (!g.over && g.tick < 60 * 600) S.step(g, d(g)); rows.push(g); }
  const avg = f => (rows.reduce((a, g) => a + f(g), 0) / rows.length).toFixed(1), sc = rows.map(g => g.score).sort((a, b) => a - b), p = q => sc[Math.floor(q * (sc.length - 1))];
  const reach = z => (rows.filter(g => S.zone(g.alt >> 8) >= z || g.landings || g.mode === 2 || g.mode === 3).length * 100 / rows.length).toFixed(0);
  console.log(`${kind.padEnd(7)} ${avg(g => g.tick / 60)}s score ${p(.1)}/${p(.5)}/${p(.9)} win ${avg(g => g.win * 100)}% reach z2 ${reach(2)}% z3 ${reach(3)}% z4 ${reach(4)}% hits ${avg(g => g.hits)} near ${avg(g => g.near)} stars ${avg(g => g.stars)} cans ${avg(g => g.cans)} perf ${avg(g => g.perfects)} fuelEnd ${avg(g => g.fuel)} blocked ${avg(g => g.blocked)}`);
}
