// Record SPACE V2 rules (game-art/adventure/prototype/adv_space.js) for the C port. All values are integers.
// Every step stores an FNV-1a hash of the full C-order state; every 120th step and the last store it whole.
const fs = require('fs'), path = require('path'), S = require('../../game-art/adventure/prototype/adv_space.js');
const { driver } = require('../space_policy.js');
const seenFx = new Set();
function hash(v) { let h = 0x811c9dc5; for (const x of v) { const u = x >>> 0; for (let k = 0; k < 32; k += 8) { h ^= (u >>> k) & 255; h = Math.imul(h, 0x01000193) >>> 0; } } return h; }
const bits = i => [i.ok_down || 0, i.ok_up || 0, i.up_down || 0, i.down_down || 0, i.down_up || 0, i.ok_held || 0, i.down_held || 0, i.up_held || 0];
function record(seed, kind, count) {
  let g = S.start(seed), next = driver(kind === 'fuzz' ? 'casual' : kind, seed);
  const r = { seed, actions: [], hashes: [], states: {} }, rng = { rng: seed ^ 0x51ba7e };
  const keep = () => { const v = S.view(g); r.hashes.push(hash(v)); if (r.hashes.length % 120 === 0) r.states[r.hashes.length - 1] = v; };
  const step = input => { r.actions.push(bits(input)); S.step(g, input); for (const e of g.fx) if (e.kind) seenFx.add(e.kind); keep(); };
  for (let i = 0; i < count; i++) {
    if (kind === 'fuzz') {
      if (g.over) { const s = S.random(rng); g = S.start(s); next = driver('casual', s); r.actions.push(['reset', s]); keep(); }
      const b = S.random(rng);
      if (b % 5 < 3) step(next(g));
      else step({ ok_down: b % 17 === 0 ? 1 : 0, up_down: b % 19 === 0 ? 1 : 0, down_down: b % 7 === 0 ? 1 : 0, ok_held: (b >> 8) & 1, up_held: (b >> 9) & 1, down_held: (b >> 10) & 1 });
    } else { step(next(g)); if (g.over) { for (let k = 0; k < 3; k++) step({}); break; } }
  }
  r.last = S.view(g); return r;
}
const traces = {idle:record(1,'idle',12000),hover:record(2,'spam',12000),casual:record(3,'casual',18000),skilled:record(4,'skilled',18000),sloppy:record(9,'casual',18000),fuzz:record(779,'fuzz',22000)};
for(const [name,trace] of Object.entries(traces)){
 trace.states[trace.hashes.length-1]=trace.last;delete trace.last;
 fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(trace)+'\n');
 console.log(name,trace.actions.length,'steps',trace.states[trace.hashes.length-1][2]);
}
console.log('Covered effects', [...seenFx].sort((a,b)=>a-b));
