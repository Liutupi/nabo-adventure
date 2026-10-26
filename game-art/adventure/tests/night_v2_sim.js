// NIGHT V2 G1 balance probe: bots that only use what the screen shows.
// node tests/night_v2_sim.js [seeds]
'use strict';
const N = require('../prototype/adv_night_v2.js'), K = N.K;

function inNetSoon(g, ahead) {
  const v = K.SPEED[g.gait] * (1 + Math.min(0.5, g.x / 30000));
  let flies = 0, moths = 0;
  for (let t = K.SWING_ON; t <= K.SWING_OFF; t++) {
    const nx = g.x + v * (ahead + t) + K.NET_DX, ny = K.GROUND - K.NET_DY;
    for (const f of g.flies) { const fy = N.flyY(f, g.tick + ahead + t), fx = f.x + f.vx * (ahead + t); if ((fx - nx) ** 2 + (fy - ny) ** 2 <= (K.NET_R) ** 2) flies++; }
    for (const m of g.moths) if ((m.x - nx) ** 2 + (m.y - ny) ** 2 <= (K.NET_R - 4) ** 2) moths++;
  }
  return { flies, moths };
}

const bots = {
  idle: () => ({}),
  spam: g => ({ press: g.tick % 20 === 0 }),
  runSpam: g => ({ right: 1, press: g.tick % 20 === 0 }),
  casual: (g, mem) => {           // reacts late, never runs, swings when something is close
    const s = inNetSoon(g, 6); return { press: g.swingT === 0 && s.flies >= 1 && g.r && (g.tick + mem.jitter) % 3 === 0 };
  },
  skilled: g => {
    const s = inNetSoon(g, 0), R = N.radius(g);
    const rootAhead = g.roots.some(rt => !rt.passed && !rt.hit && rt.x > g.x && rt.x - g.x < Math.min(R, 70));
    const owl = g.owls.find(o => o.t > 0 && Math.abs(o.tx - g.x - K.SPEED[g.gait] * o.t) < 40);
    let left = 0, right = 0;
    if (owl) { if (owl.tx > g.x + 30) left = 1; else right = !rootAhead ? 1 : 0; }
    else if (!rootAhead && g.light > 250) right = 1;
    const press = (g.meter >= N.meterFull(g) && g.tick - g.lastSwingTick <= 10 && g.tick - g.lastSwingTick > 2) ||
      (g.swingT === 0 && s.flies >= 1 && s.moths === 0);
    return { left, right, press };
  },
};

const seeds = +(process.argv[2] || 60);
for (const [name, bot] of Object.entries(bots)) {
  const rows = [];
  for (let s = 1; s <= seeds; s++) {
    const g = N.start(s * 7919), mem = { jitter: s };
    while (!g.over && g.tick < 60 * 600) g.step ? 0 : N.step(g, bot(g, mem));
    rows.push(g);
  }
  const avg = f => rows.reduce((a, g) => a + f(g), 0) / rows.length;
  const sorted = rows.map(g => g.score).sort((a, b) => a - b), pct = p => sorted[Math.floor(p * (sorted.length - 1))];
  const causes = {}; for (const g of rows) causes[g.cause] = (causes[g.cause] || 0) + 1;
  console.log(`${name.padEnd(8)} time ${avg(g => g.tick / 60).toFixed(0)}s score p10/50/90 ${pct(.1)}/${pct(.5)}/${pct(.9)} ` +
    `presses/min ${avg(g => g.stats.presses / (g.tick / 3600)).toFixed(0)} trips ${avg(g => g.stats.trips).toFixed(1)} ` +
    `owl ${avg(g => g.stats.owlHits).toFixed(1)}/${avg(g => g.stats.owlNear).toFixed(1)}near moth ${avg(g => g.stats.mothHits).toFixed(1)} ` +
    `bursts ${avg(g => g.stats.bursts).toFixed(1)} combo ${avg(g => g.stats.maxCombo).toFixed(0)} causes ${JSON.stringify(causes)}`);
}
