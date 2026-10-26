// NIGHT V2 balance probe: node tests/night_v2_sim.js [seeds]
'use strict';
const N = require('../prototype/adv_night.js'), { driver } = require('../../../tests/night_policy.js');
const seeds = +(process.argv[2] || 60);
for (const kind of ['idle', 'spam', 'mistakes', 'casual', 'skilled']) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) { const g = N.start(s * 7919), d = driver(kind, s); while (!g.over && g.tick < 60 * 600) N.step(g, d(g)); rows.push(g); }
  const avg = f => rows.reduce((a, g) => a + f(g), 0) / rows.length, sc = rows.map(g => g.score).sort((a, b) => a - b), p = q => sc[Math.floor(q * (sc.length - 1))];
  const causes = {}; for (const g of rows) causes[g.lastLoss] = (causes[g.lastLoss] || 0) + 1;
  console.log(`${kind.padEnd(8)} ${avg(g => g.tick / 60).toFixed(0)}s score p10/50/90 ${p(.1)}/${p(.5)}/${p(.9)} trips ${avg(g => g.trips).toFixed(1)} owl ${avg(g => g.owlHits).toFixed(1)}/${avg(g => g.owlNear).toFixed(1)} moth ${avg(g => g.mothHits).toFixed(1)} bursts ${avg(g => g.bursts).toFixed(1)} combo ${avg(g => g.maxCombo).toFixed(0)} blocked ${avg(g => g.blocked).toFixed(1)} causes ${JSON.stringify(causes)}`);
}
