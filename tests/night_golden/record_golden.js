// Record the rules before C implementation. All values are integers.
const fs=require('fs'),path=require('path'),N=require('../../game-art/adventure/prototype/adv_night.js');
const {drive}=require('../night_policy.js');
function record(seed,kind,count){
  let g=N.start(seed),r={seed,actions:[],states:[]},rng={rng:seed^0x51ba7e};
  const step=input=>{r.actions.push([input.ok_down||0,input.ok_up||0,input.up_down||0,input.down_down||0,input.down_up||0,input.ok_held||0,input.down_held||0]);N.step(g,input);r.states.push(N.view(g));};
  for(let i=0;i<count;i++){
    if(kind==='drive'){step(drive(g));if(g.over)break;}
    else if(kind==='fuzz'){
      if(g.over){const next=N.random(rng);g=N.start(next);r.actions.push(['reset',next]);r.states.push(N.view(g));}
      const bits=N.random(rng);step({ok_down:bits%17===0?1:0,ok_held:(bits>>6)&1,up_down:bits%43===0?1:0,down_down:bits%37===0?1:0,down_held:(bits>>9)&1});
    }else step({});
  }
  return r;
}
for(const [name,trace] of Object.entries({idle:record(1,'idle',2500),drive:record(2,'drive',24000),fuzz:record(779,'fuzz',9000)})){
  fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(trace)+'\n');console.log(name,trace.actions.length,'steps');
}
