// Record SPACE rules before the C port. All values are integers.
const fs=require('fs'),path=require('path'),P=require('../../game-art/adventure/prototype/adv_space.js');
const {driver}=require('../space_policy.js');
function record(seed,kind,count){
  let g=P.start(seed),r={seed,actions:[],states:[]},rng={rng:seed^0x51ba7e},next=driver(kind==='fuzz'?'casual':kind,seed);
  const step=input=>{r.actions.push([input.ok_down||0,input.ok_up||0,input.up_down||0,input.down_down||0,input.down_up||0,input.ok_held||0,input.down_held||0,input.up_held||0]);P.step(g,input);r.states.push(P.view(g));};
  for(let i=0;i<count;i++){
    if(kind==='fuzz'){
      if(g.over){const s=P.random(rng);g=P.start(s);next=driver('casual',s);r.actions.push(['reset',s]);r.states.push(P.view(g));}
      const bits=P.random(rng);
      if(bits%17===0){const which=(bits>>4)&1?'up':'down',pressed=(bits>>5)&1;(which==='up'?P.upEvent:P.downEvent)(g,!!pressed);r.actions.push([which,pressed]);r.states.push(P.view(g));continue;}
      if(bits%5<3)step(next(g));else step({ok_held:(bits>>8)&1,up_held:(bits>>9)&1,down_held:(bits>>10)&1});
    }else{step(next(g));if(g.over)break;}
  }
  return r;
}
const traces={idle:record(1,'idle',3000),hover:record(2,'hover',3000),casual:record(3,'casual',12000),skilled:record(8,'skilled',12000),sloppy:record(9,'sloppy',4000),fuzz:record(779,'fuzz',6000)};
const seen=m=>Object.values(traces).some(t=>t.states.some(s=>s[24]===m));
for(const [what,m] of Object.entries(P.MSG))if(m&&!seen(m))throw Error('SPACE traces must cover '+what);
for(const [name,trace] of Object.entries(traces)){fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(trace)+'\n');console.log(name,trace.actions.length,'steps',trace.states.at(-1)[2]);}
