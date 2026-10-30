// CLIMB V2 balance probe: node game-art/adventure/tests/climb_v2_sim.js [seeds]
'use strict';
const S = require('../prototype/adv_climb_v2.js'), { driver } = require('../../../tests/climb_v2_policy.js');
const seeds = +(process.argv[2] || 60);
for (const kind of ['idle', 'spam', 'wiggle', 'casual', 'skilled']) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) { const g = S.start(s * 7919), d = driver(kind, s); while (!g.over && g.tick < 60 * 600) S.step(g, d(g)); rows.push(g); }
  const avg = f => (rows.reduce((a, g) => a + f(g), 0) / rows.length).toFixed(1), sc = rows.map(g => g.score).sort((a, b) => a - b), p = q => sc[Math.floor(q * (sc.length - 1))];
  console.log(`${kind.padEnd(7)} ${avg(g => g.tick / 60)}s score ${p(.1)}/${p(.5)}/${p(.9)} m ${avg(g => g.meters)} grabs ${avg(g => g.grabs)} rhythm ${avg(g => g.rhythmGrabs)} slips ${avg(g => g.slips)} rock ${avg(g => g.rockHits)} near ${avg(g => g.nearMiss)} trav ${avg(g => g.traverses)} crumble ${avg(g => g.crumbles)} ice ${avg(g => g.iceSlips)} canteen ${avg(g => g.canteens)} flag ${avg(g => g.flags)} best ${avg(g => g.best)} ppm ${avg(g => g.presses / (g.tick / 3600))}`);
}
