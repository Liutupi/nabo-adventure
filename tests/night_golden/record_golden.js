// Record NIGHT V2 rules (game-art/adventure/prototype/adv_night.js) for the C port. All values are integers.
const fs = require('fs'), path = require('path'), N = require('../../game-art/adventure/prototype/adv_night.js');
const { driver } = require('../night_policy.js');
const seenFx = new Set();
function hash(v) { let h = 0x811c9dc5; for (const x of v) { const u = x >>> 0; for (let k = 0; k < 32; k += 8) { h ^= (u >>> k) & 255; h = Math.imul(h, 0x01000193) >>> 0; } } return h; }
const bits = i => [i.ok_down || 0, i.ok_up || 0, i.up_down || 0, i.down_down || 0, i.down_up || 0, i.ok_held || 0, i.down_held || 0, i.up_held || 0];
function record(seed, kind, count) {
  let g = N.start(seed), next = driver(kind === 'fuzz' ? 'casual' : kind, seed);
  // Every step stores an FNV-1a hash of the full C-order state; every 120th step and the last store it whole.
  const r = { seed, actions: [], hashes: [], states: {} }, rng = { rng: seed ^ 0x51ba7e };
  const keep = () => { const v = N.view(g); r.hashes.push(hash(v)); if (r.hashes.length % 120 === 0) r.states[r.hashes.length - 1] = v; };
  const step = input => { r.actions.push(bits(input)); N.step(g, input); for (const e of g.fx) if (e.kind) seenFx.add(e.kind); keep(); };
  for (let i = 0; i < count; i++) {
    if (kind === 'fuzz') {
      if (g.over) { const s = N.random(rng); g = N.start(s); next = driver('casual', s); r.actions.push(['reset', s]); keep(); }
      const b = N.random(rng);
      if (b % 5 < 3) step(next(g));
      else step({ ok_down: b % 17 === 0 ? 1 : 0, up_down: b % 19 === 0 ? 1 : 0, down_down: b % 7 === 0 ? 1 : 0, ok_held: (b >> 8) & 1, up_held: (b >> 9) & 1, down_held: (b >> 10) & 1 });
    } else { step(next(g)); if (g.over) { for (let k = 0; k < 3; k++) step({}); break; } }
  }
  r.last = N.view(g); return r;
}
const traces = { idle: record(1, 'idle', 3000), spam: record(2, 'spam', 6000), mistakes: record(3, 'mistakes', 12000),
  casual: record(5, 'casual', 12000), skilled: record(4, 'skilled', 12000), fuzz: record(779, 'fuzz', 9000) };
for (const [what, kind] of Object.entries(N.FX)) if (!seenFx.has(kind)) throw Error('NIGHT traces must cover fx ' + what);
for (const [name, trace] of Object.entries(traces)) {
  trace.states[trace.hashes.length - 1] = trace.last; delete trace.last; fs.writeFileSync(path.join(__dirname, name + '.json'), JSON.stringify(trace) + '\n'); console.log(name, trace.actions.length, 'steps', trace.states[trace.hashes.length - 1][2]); }
