// SKI V2 balance probe: node tests/ski_sim.js [seeds]
'use strict';
const S = require('../prototype/adv_ski.js'), { driver } = require('../../../tests/ski_policy.js');
const seeds = +(process.argv[2] || 60);
for (const kind of ['idle', 'spam', 'wiggle', 'casual', 'skilled']) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) { const g = S.start(s * 7919), d = driver(kind, s); while (!g.over && g.tick < 60 * 600) S.step(g, d(g)); rows.push(g); }
  const avg = f => (rows.reduce((a, g) => a + f(g), 0) / rows.length).toFixed(1), sc = rows.map(g => g.score).sort((a, b) => a - b), p = q => sc[Math.floor(q * (sc.length - 1))];
  console.log(`${kind.padEnd(7)} ${avg(g => g.tick / 60)}s score ${p(.1)}/${p(.5)}/${p(.9)} m ${avg(g => g.meters)} gates ${avg(g => g.combo >= 0 ? g.gates : 0)} miss ${avg(g => g.misses)} crash ${avg(g => g.crashes)} stumble ${avg(g => g.stumbles)} tricks ${avg(g => g.tricks)} best ${avg(g => g.best)} blocked ${avg(g => g.blocked)}`);
}
