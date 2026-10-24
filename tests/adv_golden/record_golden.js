// Records golden traces from the prototype's shell rules (game-art/adventure/prototype/adv_core.js).
// Run: node tests/adv_golden/record_golden.js   (writes tests/adv_golden/*.json)
// test_adv_model.py replays every action against the C model and compares each state.
'use strict';
const fs = require('fs');
const path = require('path');
const A = require('../../game-art/adventure/prototype/adv_core.js');

const { BTN, EV, FX } = A;
const SETTINGS = { volume: 70, brightness: 80, sleep: 300, speaker: true };

function recorder(seed, best, seen) {
  const m = A.create(seed, SETTINGS, best, seen);
  const trace = { seed, settings: [70, 80, 300, 1], best: best.slice(), seen, actions: [], states: [] };
  const push = (action, fx) => {
    trace.actions.push(action);
    trace.states.push({ view: A.view(m), fx: fx & ~FX.REDRAW, cue: m.cue });
  };
  return {
    m, trace,
    ev(btn, ev) { push(['e', btn, ev], A.event(m, btn, ev)); },
    click(btn) { this.ev(btn, EV.PRESS); this.ev(btn, EV.RELEASE); this.ev(btn, EV.CLICK); },
    long(btn) { this.ev(btn, EV.PRESS); this.ev(btn, EV.LONG); this.ev(btn, EV.RELEASE); },
    double(btn) { this.click(btn); this.ev(btn, EV.PRESS); this.ev(btn, EV.RELEASE); this.ev(btn, EV.DOUBLE); },
    steps(n) { let fx = 0; for (let i = 0; i < n; i++) fx |= A.step(m); push(['s', n], fx); },
    legacy(best) { push(['l', best], A.legacyDone(m, best)); },
    test(on) { m.test = !!on; push(['t', on ? 1 : 0], 0); },
  };
}

// Plays the placeholder game: presses OK when the marker is inside the zone (or misses on purpose).
function playDemo(r, hits, misses) {
  const s = () => r.m.session;
  while (s() && s().phase === A.PHASE.READY) r.steps(30);
  let made = 0, missed = 0, guard = 0;
  while (s() && s().phase === A.PHASE.PLAY && guard++ < 20000) {
    const g = s().game;
    const d = Math.abs(g.p + g.v - g.zc), inside = d <= g.zh - 20, outside = d > g.zh + 20;
    if (made < hits && inside) { r.ev(BTN.OK, EV.PRESS); r.steps(1); r.ev(BTN.OK, EV.RELEASE); made++; }
    else if (made >= hits && missed < misses && outside) { r.ev(BTN.OK, EV.PRESS); r.steps(1); r.ev(BTN.OK, EV.RELEASE); missed++; }
    else r.steps(1);
  }
  while (s() && s().phase === A.PHASE.END) r.steps(20);
}

function journey() {
  const r = recorder(1234, [0, 0, 0, 0, 0, 0, 0, 0, 0], 0);
  r.click(BTN.OK);                     // cover -> map
  r.click(BTN.UP);                     // jump -> post (locked: allowed to look)
  r.click(BTN.UP);                     // denied: post is locked
  r.click(BTN.OK);                     // denied
  r.click(BTN.DOWN); r.click(BTN.DOWN); r.click(BTN.DOWN);   // jump -> kiosk -> dive (locked)
  r.click(BTN.DOWN);                   // denied at the bottom
  r.click(BTN.UP); r.click(BTN.UP);    // back to jump
  r.click(BTN.OK); r.legacy(12);       // bronze for jump
  r.click(BTN.OK);                     // acknowledge the stamp
  r.click(BTN.DOWN); r.click(BTN.DOWN);
  r.click(BTN.OK); r.legacy(350);      // dive: bronze + silver
  r.click(BTN.OK); r.click(BTN.OK);
  for (let i = 0; i < 3; i++) r.click(BTN.UP);   // dive -> kiosk -> jump -> post
  r.click(BTN.OK);                     // post title
  r.double(BTN.UP);                    // back to the map
  r.click(BTN.OK); r.click(BTN.OK);    // title -> ready
  playDemo(r, 4, 3);
  r.click(BTN.OK);                     // play again from the result
  r.steps(200);
  r.long(BTN.UP);                      // pause
  r.click(BTN.OK);                     // resume
  r.steps(50);
  r.long(BTN.UP); r.click(BTN.DOWN);   // pause, restart
  playDemo(r, 7, 4);
  r.long(BTN.UP);                      // result -> map (stamps)
  r.click(BTN.OK); r.click(BTN.OK);    // post bronze and silver
  r.click(BTN.UP); r.click(BTN.OK);    // night title
  r.test(1); r.click(BTN.OK); playDemo(r, 5, 4); r.test(0);   // test mode never saves
  r.click(BTN.OK); playDemo(r, 6, 4);   // exactly the silver line
  r.double(BTN.UP); r.click(BTN.OK); r.click(BTN.OK);
  r.long(BTN.OK);                      // passport from the map
  for (let i = 0; i < 9; i++) r.click(BTN.UP);
  r.click(BTN.DOWN); r.long(BTN.UP);
  r.long(BTN.UP);                      // map -> cover
  return r.trace;
}

function kioskAndSettings() {
  const r = recorder(99, [30, 30, 700, 12, 0, 0, 0, 0, 0], 0x7ffffff);
  r.click(BTN.OK);
  r.click(BTN.DOWN); r.click(BTN.OK);  // kiosk
  r.click(BTN.UP); r.click(BTN.DOWN); r.click(BTN.DOWN); r.click(BTN.UP);   // 2, 0, 1, 0
  r.click(BTN.OK);                     // passport from the kiosk
  r.click(BTN.DOWN); r.click(BTN.OK);  // back to the kiosk
  r.click(BTN.DOWN); r.click(BTN.OK);  // settings
  r.click(BTN.OK); r.click(BTN.UP); r.click(BTN.UP); r.click(BTN.OK);   // volume +10, save
  r.click(BTN.DOWN); r.click(BTN.OK); r.click(BTN.DOWN); r.long(BTN.UP); // brightness edit cancelled
  r.click(BTN.DOWN); r.click(BTN.OK);  // speaker toggle
  r.click(BTN.DOWN); r.click(BTN.OK);
  for (let i = 0; i < 9; i++) r.click(BTN.DOWN);
  r.click(BTN.OK);
  r.click(BTN.DOWN); r.click(BTN.OK); r.click(BTN.OK);   // status page and back
  r.click(BTN.DOWN); r.click(BTN.OK);  // settings -> 返回 -> kiosk
  r.click(BTN.DOWN); r.click(BTN.OK);  // kiosk 返回地图
  for (let i = 0; i < 10; i++) r.click(BTN.UP);   // walk to the top
  r.click(BTN.OK); r.long(BTN.UP);
  return r.trace;
}

function fuzz(seed, best, seen, count) {
  const r = recorder(seed, best, seen);
  const pick = { rng: seed ^ 0x5bd1e995 };
  const events = [EV.PRESS, EV.CLICK, EV.DOUBLE, EV.LONG, EV.RELEASE];
  for (let i = 0; i < count; i++) {
    const v = A.rand(pick) % 100;
    if (v < 38) r.steps(1 + A.rand(pick) % 40);
    else if (v < 40 && r.m.page === A.PAGE.LEGACY) r.legacy(A.rand(pick) % 800);
    else if (v < 41) r.test(A.rand(pick) & 1);
    else if (v < 70) r.ev(A.rand(pick) % 3, events[A.rand(pick) % 5]);
    else r.click(A.rand(pick) % 3);
  }
  return r.trace;
}

const out = __dirname;
const traces = {
  journey: journey(),
  kiosk_settings: kioskAndSettings(),
  fuzz_fresh: fuzz(7, [0, 0, 0, 0, 0, 0, 0, 0, 0], 0, 4000),
  fuzz_open: fuzz(2024, [0, 60, 650, 11, 11, 11, 11, 11, 2], 0, 4000),
};
for (const [name, trace] of Object.entries(traces)) {
  fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(trace) + '\n');
  console.log(name, trace.actions.length, 'actions');
}
