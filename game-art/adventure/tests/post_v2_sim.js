// POST V2 balance probe: node game-art/adventure/tests/climb_v2_sim.js [seeds]
'use strict';
const S = require('../prototype/adv_post_v2.js'), { driver } = require('../../../tests/post_v2_policy.js');
const seeds = +(process.argv[2] || 60);
for (const kind of ['idle', 'spam', 'wiggle', 'casual', 'skilled']) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) { const g = S.start(s * 7919), d = driver(kind, s); while (!g.over && g.tick < 60 * 600) S.step(g, d(g)); rows.push(g); }
  const avg = f => (rows.reduce((a, g) => a + f(g), 0) / rows.length).toFixed(1), sc = rows.map(g => g.score).sort((a, b) => a - b), p = q => sc[Math.floor(q * (sc.length - 1))];
  console.log(`${kind.padEnd(7)} ${avg(g => g.tick / 60)}s score ${p(.1)}/${p(.5)}/${p(.9)} m ${avg(g => g.meters)} deliv ${avg(g => g.delivered)}/${avg(g => g.nets)} perfect ${avg(g => g.perfects)} crane ${avg(g => g.cranes)} waste ${avg(g => g.wasted)} skip ${avg(g => g.skipped)} red ${avg(g => g.reds)} derail ${avg(g => g.derails)} animal ${avg(g => g.animals)} near ${avg(g => g.nearMiss)} best ${avg(g => g.best)} top% ${avg(g => 100 * g.topSpeedT / g.tick)} blocked ${avg(g => g.blocked)}`);
}
