// Records golden traces from the prototype's shell rules (game-art/adventure/prototype/adv_core.js).
// Run: node tests/adv_golden/record_golden.js   (writes tests/adv_golden/*.json)
// test_adv_model.py replays every action against the C model and compares each state.
'use strict';
const fs = require('fs');
const path = require('path');
const A = require('../../game-art/adventure/prototype/adv_core.js');

const { BTN, EV, FX } = A;
const {driver:nightDriver}=require('../night_policy.js');
const {driver:climbDriver}=require('../climb_v2_policy.js');
const LATE={6:require('../ski_policy.js').driver,7:require('../sky_v2_policy.js').driver,8:require('../space_policy.js').driver};
// The pause gesture of each shell game (NIGHT long DOWN, SKI long OK, SPACE two short DOWN taps, others long UP).
function pause(r,station){r.long(BTN.DOWN);}
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

// Real button edges drive the reference shell, rather than injecting game state.
const V2PLAYERS={3:require('../post_v2_policy.js').driver,4:nightDriver,5:climbDriver,...LATE};
function playGame(r,target,waitResult=true){
 const station=r.m.session.station,next=V2PLAYERS[station]('skilled',r.m.session.seed||1);
 if(r.m.session.phase===A.PHASE.TITLE||r.m.session.phase===A.PHASE.RESULT)r.click(BTN.DOWN);
 while(r.m.session.phase===A.PHASE.READY)r.steps(30);
 let guard=0;
 while(r.m.session.phase===A.PHASE.PLAY&&guard++<40000){
  const input=r.m.session.game.score<target?next(r.m.session.game):{};
  const taps=[];
  for(const [button,prefix] of [[BTN.OK,'ok'],[BTN.UP,'up'],[BTN.DOWN,'down']]){
   const held=!!input[prefix+'_held'],pulse=!!input[prefix+'_down'];
   let was=!!(r.m.held&(1<<button));
   if(pulse&&was){r.ev(button,EV.RELEASE);was=false;}
   if((held||pulse)!==was)r.ev(button,held||pulse?EV.PRESS:EV.RELEASE);
   if(pulse&&!held)taps.push(button);
  }
  r.steps(1);for(const button of taps)r.ev(button,EV.RELEASE);
 }
 for(const button of [BTN.OK,BTN.UP,BTN.DOWN])if(r.m.held&(1<<button))r.ev(button,EV.RELEASE);
 if(r.m.session.phase!==A.PHASE.END)throw Error('game did not end: '+station);
 while(waitResult&&r.m.session.phase===A.PHASE.END)r.steps(20);
}
function playDemo(r,hits,misses,waitResult=true){return r.m.session.station===4?playNight(r,hits,waitResult):playGame(r,hits,waitResult);}
function playPost(r,hits,misses,waitResult=true){return playGame(r,hits,waitResult);}

let driveNight=null;
function playNight(r,hits,waitResult=true){
  driveNight=nightDriver('skilled',r.m.session.seed||1);
  if(r.m.session.phase===A.PHASE.TITLE||r.m.session.phase===A.PHASE.RESULT)r.click(BTN.DOWN);
  while(r.m.session.phase===A.PHASE.READY)r.steps(30);
  let guard=0;
  while(r.m.session.phase===A.PHASE.PLAY&&guard++<24000){
    const g=r.m.session.game,input=g.score<hits?driveNight(g):{};
    if(input.down_down&&r.m.held&(1<<BTN.DOWN))r.ev(BTN.DOWN,EV.RELEASE);
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

function playClimb(r,target,waitResult=true){return playGame(r,target,waitResult);}
function playLate(r,target,waitResult=true){return playGame(r,target,waitResult);}
function lateGames(){
 const r=recorder(64,[0,30,400,150,100,80,0,0,0],0xffffff);r.click(BTN.OK);r.test(1);
 for(const station of [6,7,8]){r.open(station);r.click(BTN.DOWN);r.steps(200);r.double(BTN.UP);
  if(r.m.session.phase!==A.PHASE.PLAY)throw Error('V2 returned while playing');
  pause(r,station);r.click(BTN.DOWN);playGame(r,A.threshold(station,0));r.double(BTN.UP);}
 return r.trace;
}
function climbRound(){
 const r=recorder(55,[0,20,300,150,100,0,0,0,0],0xffffff);r.click(BTN.OK);r.test(1);r.open(5);
 r.click(BTN.DOWN);r.steps(240);r.click(BTN.UP);r.long(BTN.UP);pause(r,5);r.click(BTN.DOWN);
 pause(r,5);r.click(BTN.OK);playGame(r,80);r.double(BTN.UP);return r.trace;
}
function journey(){
 const r=recorder(1234,[0,0,0,0,0,0,0,0,0],0);
 r.click(BTN.OK);r.click(BTN.UP);r.click(BTN.UP);r.click(BTN.OK);r.click(BTN.DOWN);
 r.click(BTN.OK);r.legacy(12);r.click(BTN.OK);
 r.click(BTN.DOWN);r.click(BTN.DOWN);r.click(BTN.OK);r.legacy(350);r.click(BTN.OK);r.click(BTN.OK);
 for(let i=0;i<3;i++)r.click(BTN.UP);r.click(BTN.OK);r.double(BTN.UP);r.click(BTN.OK);
 r.click(BTN.DOWN);r.steps(200);pause(r,3);r.click(BTN.DOWN);r.steps(50);pause(r,3);r.click(BTN.OK);
 playGame(r,500);r.double(BTN.UP);while(r.m.page===A.PAGE.STAMP)r.click(BTN.OK);
 r.long(BTN.OK);for(let i=0;i<9;i++)r.click(BTN.UP);r.click(BTN.DOWN);r.long(BTN.UP);r.long(BTN.UP);
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
    if(phase!==A.PHASE.TITLE)r.click(station>=3&&station<=8?BTN.DOWN:BTN.OK);
    if(phase!==A.PHASE.TITLE&&phase!==A.PHASE.READY)r.steps(180);
    if(phase===A.PHASE.PAUSE)pause(r,station);
    if(phase===A.PHASE.END||phase===A.PHASE.RESULT) {
      let guard=0;
      while(r.m.session.phase===A.PHASE.PLAY&&guard++<60000)r.steps(30);
      if(r.m.session.phase!==A.PHASE.END)throw Error('Expected an ended round');
      if(phase===A.PHASE.RESULT)r.steps(A.END_STEPS);
    }
    if(phase===A.PHASE.PLAY){r.click(BTN.UP);pause(r,station);r.click(station>=3&&station<=8?BTN.DOWN:BTN.OK);}
    else r.long(BTN.UP);
    if(r.m.page!==A.PAGE.SESSION||r.m.session.phase!==phase)throw Error('Single/long UP unexpectedly returned or changed a phase');
    r.double(BTN.UP);
    if((station>=3&&station<=8)&&phase===A.PHASE.PLAY){
      // NIGHT/SKI V2 (user decision 2026-10-26): UP is a move key, so the map is reached from the pause page.
      if(r.m.page!==A.PAGE.SESSION||r.m.session.phase!==A.PHASE.PLAY)throw Error('V2 game left while playing');
      pause(r,station);r.double(BTN.UP);
    }
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
  late_games:lateGames(),
  journey: journey(),
  kiosk_settings: kioskAndSettings(),
  fuzz_fresh: fuzz(7, [0, 0, 0, 0, 0, 0, 0, 0, 0], 0, 4000),
  fuzz_open: fuzz(2024, [0, 60, 650, 11, 11, 11, 11, 11, 2], 0, 4000),
  post_test_entry:(()=>{const r=recorder(42,[0,99,0,0,0,0,0,0,0],7);r.click(BTN.OK);r.open(3);r.test(1);r.open(3);r.click(BTN.OK);playPost(r,6,4);r.double(BTN.UP);return r.trace;})(),
  threshold_edges:(()=>{const r=recorder(99,[0,10,100,5,3,3,3,3,0],0xffffff);r.click(BTN.OK);r.click(BTN.DOWN);r.click(BTN.DOWN);r.click(BTN.OK);r.legacy(100);r.click(BTN.UP);r.click(BTN.UP);for(let s=3;s<9;s++){r.click(BTN.UP);r.click(BTN.OK);r.double(BTN.UP);}return r.trace;})(),
  post_practice:(()=>{const r=recorder(23,[0,99,300,0,0,0,0,0,0],0xffffff);r.click(BTN.OK);r.practice();return r.trace;})(),
  post_practice_locked:(()=>{const r=recorder(32,[0,99,0,0,0,0,0,0,0],7);r.practice();r.click(BTN.OK);r.practice();return r.trace;})(),
};
for (const [name, trace] of Object.entries(traces)) {
  fs.writeFileSync(path.join(out, name + '.json'), JSON.stringify(trace) + '\n');
  console.log(name, trace.actions.length, 'actions');
}
