// Records golden traces from the prototype's shell rules (game-art/adventure/prototype/adv_core.js).
// Run: node tests/adv_golden/record_golden.js   (writes tests/adv_golden/*.json)
// test_adv_model.py replays every action against the C model and compares each state.
'use strict';
const fs = require('fs');
const path = require('path');
const A = require('../../game-art/adventure/prototype/adv_core.js');

const { BTN, EV, FX } = A;
const {drive:driveNight}=require('../night_policy.js');
const {driver:climbDriver}=require('../climb_policy.js');
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
    open(s) {push(['o',s],A.testOpen(m,s));},
    practice() {push(['p'],A.practiceOpen(m));},
  };
}

// Plays the placeholder game: presses OK when the marker is inside the zone (or misses on purpose).
function playDemo(r, hits, misses,waitResult=true) {
  if(r.m.session.station===3)return playPost(r,hits,misses,waitResult);
  if(r.m.session.station===4)return playNight(r,hits,waitResult);
  if(r.m.session.station===5)return playClimb(r,hits,waitResult);
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
  while (waitResult && s() && s().phase === A.PHASE.END) r.steps(20);
}

function playPost(r,hits,misses,waitResult=true) {
  while(r.m.session.phase===A.PHASE.READY)r.steps(30);
  let errors=0,guard=0;
  while(r.m.session.phase===A.PHASE.PLAY&&guard++<12000){
    const g=r.m.session.game;
    const station=g.events.filter(e=>e.type===2&&!e.done&&e.x>=A.Post.MAIL_X-A.Post.WINDOW).sort((a,b)=>a.x-b.x)[0];
    const fork=g.events.find(e=>e.type===1&&!e.done);
    if(fork&&station&&g.choice!==station.lane)r.ev(station.lane===0?BTN.UP:BTN.DOWN,EV.PRESS);
    if((g.score<hits&&station&&A.Post.canDeliver(g)&&Math.abs(station.x-A.Post.MAIL_X)<500)||
       (g.score>=hits&&errors<misses&&!station)){
      r.ev(BTN.OK,EV.PRESS);r.steps(1);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
      if(g.score>=hits)errors++;
    }else r.steps(3);
  }
  while(waitResult&&r.m.session.phase===A.PHASE.END)r.steps(20);
}

function playNight(r,hits,waitResult=true){
  if(r.m.session.phase===A.PHASE.TITLE||r.m.session.phase===A.PHASE.RESULT)r.click(BTN.DOWN);
  while(r.m.session.phase===A.PHASE.READY)r.steps(30);
  let guard=0;
  while(r.m.session.phase===A.PHASE.PLAY&&guard++<24000){
    const g=r.m.session.game,input=g.score<hits?driveNight(g):{};
    for(const [button,want] of [[BTN.OK,!!input.ok_held],[BTN.UP,!!input.up_held]]){
      const was=!!(r.m.held&(1<<button));if(was!==want)r.ev(button,want?EV.PRESS:EV.RELEASE);
    }
    const buttons=[];
    if(input.ok_down)buttons.push(BTN.OK);
    if(input.up_down)buttons.push(BTN.UP);
    if(input.down_down)buttons.push(BTN.DOWN);
    for(const b of buttons)r.ev(b,EV.PRESS);
    r.steps(1);
    for(const b of buttons)r.ev(b,EV.RELEASE);
  }
  if(r.m.session.phase!==A.PHASE.END)throw Error('NIGHT did not end');
  while(waitResult&&r.m.session.phase===A.PHASE.END)r.steps(20);
}

// CLIMB through real OK press/release events until `height` metres, then hang on until spent.
function playClimb(r,height,waitResult=true){
  while(r.m.session.phase===A.PHASE.READY)r.steps(30);
  const next=climbDriver('skilled',r.m.session.seed);let guard=0;
  while(r.m.session.phase===A.PHASE.PLAY&&guard++<30000){
    const g=r.m.session.game,input=g.score<height||g.press>=0?next(g):{};
    if(input.ok_down)r.ev(BTN.OK,EV.PRESS);
    r.steps(1);
    if(input.ok_up)r.ev(BTN.OK,EV.RELEASE);
  }
  if(r.m.session.phase!==A.PHASE.END)throw Error('CLIMB did not end');
  while(waitResult&&r.m.session.phase===A.PHASE.END)r.steps(20);
}

function climbRound(){
  const r=recorder(55,[0,20,300,6,16,0,0,0,0],0x3ff);
  r.click(BTN.OK);for(let i=0;i<3;i++)r.click(BTN.UP);r.click(BTN.OK);
  if(!r.m.session||r.m.session.station!==5)throw Error('CLIMB did not open');
  r.click(BTN.OK);r.steps(240);r.click(BTN.UP);r.long(BTN.UP);r.click(BTN.OK);   // single UP plays on, long UP pauses
  r.long(BTN.UP);r.click(BTN.DOWN);                                                // restart from pause
  playClimb(r,55);
  if(r.m.best[5]<50)throw Error('CLIMB round must earn bronze');
  r.double(BTN.UP);r.click(BTN.OK);
  return r.trace;
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
  playDemo(r, 13, 4);
  r.double(BTN.UP);                    // result -> map (stamps)
  r.click(BTN.OK); r.click(BTN.OK);    // post bronze and silver
  r.click(BTN.UP); r.click(BTN.OK);    // night title
  r.test(1); r.click(BTN.OK); playDemo(r, 15, 4); r.test(0);   // test mode never saves
  r.click(BTN.OK); playDemo(r, 35, 4);   // NIGHT's actual silver line
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
  r.click(BTN.OK); r.double(BTN.UP);
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

function gameReturns() {
  const r=recorder(71,[0,50,600,25,60,300,45,1000,900],0xffffff);
  r.click(BTN.OK);r.test(1);
  for(let station=3;station<9;station++)for(const phase of Object.values(A.PHASE)) {
    r.open(station);
    if(phase!==A.PHASE.TITLE)r.click(station===4?BTN.DOWN:BTN.OK);
    if(phase!==A.PHASE.TITLE&&phase!==A.PHASE.READY)r.steps(180);
    if(phase===A.PHASE.PAUSE)r.long(station===4?BTN.DOWN:BTN.UP);
    if(phase===A.PHASE.END||phase===A.PHASE.RESULT) {
      let guard=0;
      while(r.m.session.phase===A.PHASE.PLAY&&guard++<60000)r.steps(1);
      if(r.m.session.phase!==A.PHASE.END)throw Error('Expected an ended round');
      if(phase===A.PHASE.RESULT)r.steps(A.END_STEPS);
    }
    if(phase===A.PHASE.PLAY){r.click(BTN.UP);r.long(station===4?BTN.DOWN:BTN.UP);r.click(station===4?BTN.DOWN:BTN.OK);}
    else r.long(BTN.UP);
    if(r.m.page!==A.PAGE.SESSION||r.m.session.phase!==phase)throw Error('Single/long UP unexpectedly returned or changed a phase');
    r.double(BTN.UP);
    if(r.m.page!==A.PAGE.MAP||r.m.session)throw Error('Double UP did not close the game');
  }
  for(const station of [1,2]) {
    while(r.m.cursor!==station)r.click(BTN.DOWN);
    r.click(BTN.OK);r.click(BTN.UP);r.long(BTN.UP);
    if(r.m.page!==A.PAGE.LEGACY)throw Error('Legacy single/long UP escaped');
    r.double(BTN.UP);
    if(r.m.page!==A.PAGE.MAP)throw Error('Legacy double UP did not return');
  }
  return r.trace;
}

function endedReturn(test) {
  const r=recorder(82,[0,10,100,5,0,0,0,0,0],0xffffff);
  r.click(BTN.OK);r.click(BTN.UP);r.click(BTN.UP);r.click(BTN.OK);r.test(test);r.click(BTN.OK);
  playDemo(r,4,4,false);
  if(r.m.session.phase!==A.PHASE.END)throw Error('Expected finished game before result');
  r.double(BTN.UP);
  if(r.m.best[4]!== (test?0:4))throw Error('Ended return saved incorrectly');
  return r.trace;
}

// Former placeholder medals remain awarded when a formal game raises targets.
function legacyAwards(){
  const r=recorder(1234,[0,132,5888,8,12,11,13,12,15],16776831);
  r.click(BTN.OK);
  for(let station=3;station<=8;station++){
    r.click(BTN.UP);r.click(BTN.OK);
    if(!r.m.session||r.m.session.station!==station)throw new Error('Historical award lost its unlocked entry');
    r.double(BTN.UP);
  }
  return r.trace;
}
const out = __dirname;
const traces = {
  legacy_awards:legacyAwards(),
  climb_round:climbRound(),
  game_returns:gameReturns(),
  game_return_record:endedReturn(false),
  game_return_test:endedReturn(true),
  demo_thresholds:(()=>{const r=recorder(81,[0,50,600,25,60,60,0,0,0],0x1fff);r.click(BTN.OK);for(let i=0;i<4;i++)r.click(BTN.UP);r.click(BTN.OK);r.click(BTN.OK);if(r.m.session.station!==6)throw Error('demo threshold trace must use a placeholder');playDemo(r,6,4);r.double(BTN.UP);r.click(BTN.OK);r.click(BTN.OK);return r.trace;})(),
  journey: journey(),
  kiosk_settings: kioskAndSettings(),
  fuzz_fresh: fuzz(7, [0, 0, 0, 0, 0, 0, 0, 0, 0], 0, 4000),
  fuzz_open: fuzz(2024, [0, 60, 650, 11, 11, 11, 11, 11, 2], 0, 4000),
  post_test_entry:(()=>{const r=recorder(42,[0,99,0,0,0,0,0,0,0],7);r.click(BTN.OK);r.open(3);r.test(1);r.open(3);r.click(BTN.OK);playPost(r,6,4);r.double(BTN.UP);return r.trace;})(),
  threshold_edges:(()=>{const r=recorder(99,[0,10,100,5,3,3,3,3,0],0xffffff);r.click(BTN.OK);r.click(BTN.DOWN);r.click(BTN.DOWN);r.click(BTN.OK);r.legacy(100);r.click(BTN.UP);r.click(BTN.UP);for(let s=3;s<9;s++){r.click(BTN.UP);r.click(BTN.OK);r.double(BTN.UP);}return r.trace;})(),
  post_practice:(()=>{
    const r=recorder(23,[0,99,300,0,0,0,0,0,0],0xffffff);
    r.click(BTN.OK);r.click(BTN.UP);r.click(BTN.OK);r.click(BTN.DOWN);r.steps(180);r.steps(600);
    r.click(BTN.DOWN);r.click(BTN.OK);r.steps(60);r.click(BTN.UP);r.steps(240);
    r.ev(BTN.OK,EV.PRESS);r.steps(15);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
    r.long(BTN.UP);r.click(BTN.OK);
    r.ev(BTN.OK,EV.PRESS);r.steps(A.Post.HOLD+38);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
    r.ev(BTN.OK,EV.PRESS);r.steps(1);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
    if(r.m.session.phase!==A.PHASE.READY||r.m.session.game.practice)throw Error('Practice did not enter the normal countdown');
    if(r.trace.states.some(s=>s.fx&FX.SAVE_BEST)||r.m.best[3])throw Error('Practice changed a real record');
    r.steps(180);r.long(BTN.UP);r.double(BTN.UP);r.click(BTN.OK);r.click(BTN.DOWN);r.steps(180);
    r.click(BTN.UP);r.steps(60);r.long(BTN.UP);r.click(BTN.DOWN);r.steps(180);
    if(!r.m.session.game.practice||r.m.session.game.lesson)throw Error('Practice pause restart lost its mode');
    r.long(BTN.UP);r.double(BTN.UP);return r.trace;
  })(),
  post_practice_locked:(()=>{
    const r=recorder(32,[0,99,0,0,0,0,0,0,0],7);
    r.practice();r.practice();r.steps(180);r.steps(600);r.click(BTN.UP);r.steps(240);
    r.ev(BTN.OK,EV.PRESS);r.steps(15);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
    r.ev(BTN.OK,EV.PRESS);r.steps(A.Post.HOLD+38);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
    r.ev(BTN.OK,EV.PRESS);r.steps(1);r.ev(BTN.OK,EV.RELEASE);r.steps(1);
    if(r.m.page!==A.PAGE.MAP||r.m.best[3]||r.m.test||r.m.seen!==7)throw Error('Normal practice changed progress or bypassed unlock');
    if(r.trace.states.some(s=>s.fx&(FX.SAVE_BEST|FX.SAVE_PROGRESS)))throw Error('Normal practice attempted a save');
    return r.trace;
  })(),
};
for (const [name, trace] of Object.entries(traces)) {
  fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(trace) + '\n');
  console.log(name, trace.actions.length, 'actions');
}
