// Freeze every 60Hz reference state, delta-encoded to keep traces reviewable.
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const source=path.resolve(__dirname,'../../game-art/adventure/prototype/adv_post.js'),P=require(source);
const KEYS=['ok_down','ok_up','up_down','down_down','down_up','ok_held','down_held'];
function record(name,seed,frames,policy){
 const g=P.start(seed),initial=P.view(g),rows=[];let previous=initial.slice();
 const pick={rng:seed^0x127643fe};let release=false;
 for(let k=0;k<frames;k++){
  const input={};
  if(policy==='fuzz') {const r=P.random(pick);for(let b=0;b<7;b++)input[KEYS[b]]=+(!!(r&(1<<b)));}
  if(policy==='drive'){
   const target=g.events.filter(e=>e.type===2&&!e.done&&e.x>=P.X-P.WINDOW).sort((a,b)=>a.x-b.x)[0];
   if(g.events.some(e=>e.type===1&&!e.done)&&target&&g.choice!==target.lane)input[target.lane?'down_down':'up_down']=1;
   const animal=g.events.find(e=>e.type===4&&!e.done&&e.lane===g.lane&&e.x>P.X&&e.x<P.X+g.speed*90);
   if(release){input.ok_up=1;release=false;}
   else if(animal){input.ok_held=1;if(!g.hold)input.ok_down=1;}
   else if(g.hold)input.ok_up=1;
   else if(target&&target.lane===g.lane&&Math.abs(target.x-P.X)<500){input.ok_down=1;input.ok_held=1;release=true;}
  }
  P.step(g,input);const state=P.view(g),delta=[];
  for(let i=0;i<state.length;i++)if(state[i]!==previous[i])delta.push(i,state[i]);
  rows.push([KEYS.reduce((n,key,b)=>n|(input[key]?1<<b:0),0),delta]);previous=state;
 }
 const out={schema:'post-every-step-v1',prototype_sha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),seed,initial,keys:KEYS,rows,final:{score:g.score,lap:g.lap,resource:g.res,over:g.over,spawnBlocked:g.spawnBlocked}};
 fs.writeFileSync(path.join(__dirname,name+'.json'),JSON.stringify(out)+'\n');
 console.log(name,frames,'steps',JSON.stringify(out.final));
}
record('idle',1,6000,'idle');record('drive',9090,18000,'drive');record('fuzz',0x80000032,6000,'fuzz');
