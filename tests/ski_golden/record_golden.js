// Record SKI rules before the C port. All values are integers.
const fs=require('fs'),path=require('path'),K=require('../../game-art/adventure/prototype/adv_ski.js');
const {driver}=require('../ski_policy.js');
function record(seed,kind,count){
  let g=K.start(seed),r={seed,actions:[],states:[]},rng={rng:seed^0x51ba7e},next=driver(kind==='fuzz'?'casual':kind,seed);
  const step=input=>{r.actions.push([input.ok_down||0,input.ok_up||0,input.up_down||0,input.down_down||0,input.down_up||0,input.ok_held||0,input.down_held||0,input.up_held||0]);K.step(g,input);r.states.push(K.view(g));};
  for(let i=0;i<count;i++){
    if(kind==='fuzz'){
      if(g.over){const s=K.random(rng);g=K.start(s);next=driver('casual',s);r.actions.push(['reset',s]);r.states.push(K.view(g));}
      const bits=K.random(rng);
      if(bits%13===0){const pressed=(bits>>5)&1;K.upEvent(g,!!pressed);r.actions.push(['up',pressed]);r.states.push(K.view(g));continue;}
      if(bits%5<3)step(next(g));
      else step({ok_down:bits%7===0?1:0,ok_held:(bits>>8)&1,up_held:(bits>>9)&1,down_held:(bits>>10)&1});
    }else{step(next(g));if(g.over)break;}
  }
  return r;
}
const traces={idle:record(1,'idle',3000),wiggle:record(2,'wiggle',3000),casual:record(3,'casual',20000),skilled:record(5,'skilled',20000),expert:record(4,'expert',20000),fuzz:record(779,'fuzz',6000)};
const seen=(m)=>Object.values(traces).some(t=>t.states.some(s=>s[22]===m));
for(const [what,m] of Object.entries(K.MSG))if(m&&!seen(m))throw Error('SKI traces must cover '+what);
if(traces.expert.states.at(-1)[2]<45)throw Error('expert trace should reach gold');
for(const [name,trace] of Object.entries(traces)){fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(trace)+'\n');console.log(name,trace.actions.length,'steps',trace.states.at(-1)[2]);}
