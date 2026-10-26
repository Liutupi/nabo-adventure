// SPACE V2 balance probe: node tests/space_v2_sim.js [seeds]
'use strict';
const S = require('../prototype/adv_space_v2.js'), { driver } = require('../../../tests/space_v2_policy.js');
const seeds = +(process.argv[2] || 60);
for (const kind of ['idle', 'spam', 'casual', 'skilled']) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) { const g = S.start(s * 7919), d = driver(kind, s); while (!g.over && g.tick < 60 * 600) S.step(g, d(g)); rows.push(g); }
  const avg = f => (rows.reduce((a, g) => a + f(g), 0) / rows.length).toFixed(1), sc = rows.map(g => g.score).sort((a, b) => a - b), p = q => sc[Math.floor(q * (sc.length - 1))];
  const causes = {}; for (const g of rows) causes[g.cause] = (causes[g.cause] || 0) + 1;
  console.log(`${kind.padEnd(7)} ${avg(g => g.tick / 60)}s score ${p(.1)}/${p(.5)}/${p(.9)} hops ${avg(g => g.hops)} perfect ${avg(g => g.perfect)} crashes ${avg(g => g.crashes)} cans ${avg(g => g.cans)} blocked ${avg(g => g.blocked)} lastcause ${JSON.stringify(causes)}`);
}
