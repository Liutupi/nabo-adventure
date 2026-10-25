// Record SKY rules before the C port. All values are integers.
const fs=require('fs'),path=require('path'),Y=require('../../game-art/adventure/prototype/adv_sky.js');
const {driver}=require('../sky_policy.js');
function record(seed,kind,count){
  let g=Y.start(seed),r={seed,actions:[],states:[]},rng={rng:seed^0x51ba7e},next=driver(kind==='fuzz'?'casual':kind,seed);
  const step=input=>{r.actions.push([input.ok_down||0,input.ok_up||0,input.up_down||0,input.down_down||0,input.down_up||0,input.ok_held||0,input.down_held||0,input.up_held||0]);Y.step(g,input);r.states.push(Y.view(g));};
  for(let i=0;i<count;i++){
    if(kind==='fuzz'){
      if(g.over){const s=Y.random(rng);g=Y.start(s);next=driver('casual',s);r.actions.push(['reset',s]);r.states.push(Y.view(g));}
      const bits=Y.random(rng);if(bits%5<3)step(next(g));else step({ok_held:(bits>>8)&1,ok_down:bits%7===0?1:0});
    }else{step(next(g));if(g.over)break;}
  }
  return r;
}
const traces={idle:record(1,'idle',3000),hold:record(2,'hold',3000),pulse:record(3,'pulse',3000),casual:record(4,'casual',12000),skilled:record(5,'skilled',12000),expert:record(6,'expert',12000),fuzz:record(779,'fuzz',6000)};
const seen=m=>Object.values(traces).some(t=>t.states.some(s=>s[15]===m));
for(const [what,m] of Object.entries(Y.MSG))if(m&&!seen(m))throw Error('SKY traces must cover '+what);
for(const [name,trace] of Object.entries(traces)){fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(trace)+'\n');console.log(name,trace.actions.length,'steps',trace.states.at(-1)[2]);}
