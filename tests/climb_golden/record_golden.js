// Record CLIMB rules before the C port. All values are integers.
const fs=require('fs'),path=require('path'),C=require('../../game-art/adventure/prototype/adv_climb.js');
const {driver}=require('../climb_policy.js');
const MSG=C.MSG;
function record(seed,kind,count){
  let g=C.start(seed),r={seed,actions:[],states:[]},rng={rng:seed^0x51ba7e},next=driver(kind==='fuzz'?'casual':kind,seed);
  const step=input=>{r.actions.push([input.ok_down||0,input.ok_up||0,input.up_down||0,input.down_down||0,input.down_up||0,input.ok_held||0,input.down_held||0,input.up_held||0]);C.step(g,input);r.states.push(C.view(g));};
  for(let i=0;i<count;i++){
    if(kind==='fuzz'){
      if(g.over){const s=C.random(rng);g=C.start(s);next=driver('casual',s);r.actions.push(['reset',s]);r.states.push(C.view(g));}
      const bits=C.random(rng);
      // Mix a sensible climber with random taps, releases and long holds.
      if(bits%5<3)step(next(g));
      else step({ok_down:bits%7===0?1:0,ok_up:bits%11===0?1:0,ok_held:(bits>>8)&1,up_down:bits%43===0?1:0,down_down:bits%37===0?1:0});
    }else if(kind==='lazy'&&g.act===C.ACT.IDLE&&g.fragileT>0&&g.press<0)step({});  // stays on crumbling rock
    else{step(next(g));if(g.over)break;}
  }
  return r;
}
const traces={idle:record(1,'idle',2400),skilled:record(2,'skilled',30000),casual:record(3,'casual',20000),tapper:record(4,'tapper',4000),lazy:record(5,'lazy',12000),fuzz:record(779,'fuzz',10000)};
const seen=(name,i)=>traces[name].states.some(s=>s[24]===i);
const all=Object.keys(traces);
for(const [what,ok] of [['milestone',all.some(n=>seen(n,MSG.MILESTONE))],['canteen',all.some(n=>seen(n,MSG.CANTEEN))],['rock hit',all.some(n=>seen(n,MSG.HIT))],
  ['miss',all.some(n=>seen(n,MSG.MISS))],['crumble',all.some(n=>seen(n,MSG.CRUMBLE))],['ice',traces.skilled.states.some(s=>s[2]>=90)],['reset',traces.fuzz.actions.some(a=>a[0]==='reset')]])
  if(!ok)throw Error('CLIMB golden traces must cover '+what);
for(const [name,trace] of Object.entries(traces)){fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(trace)+'\n');console.log(name,trace.actions.length,'steps');}
