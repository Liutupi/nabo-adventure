// Approved V2 reference traces: every-step FNV, full checkpoints every 120 steps.
// Run: node tests/record_v2_golden.js [sky|climb|post]
'use strict';
const fs=require('fs'),path=require('path');
function hash(words){let h=0x811c9dc5;for(const w of words)for(let s=0;s<32;s+=8){h^=(w>>>s)&255;h=Math.imul(h,0x01000193);}return h>>>0;}
for(const name of process.argv[2]?[process.argv[2]]:['sky','climb','post']){
 const G=require('../game-art/adventure/prototype/adv_'+name+'_v2.js'),P=require('./'+name+'_v2_policy.js');
 const out=path.join(__dirname,'v2_golden',name);fs.mkdirSync(out,{recursive:true});
 for(const [n,kind] of ['idle','spam','wiggle','casual','skilled','fuzz'].entries()){
  const seed=104729*(n+1);let g=G.start(seed),driver=P.driver(kind==='fuzz'?'skilled':kind,seed),prng=seed;
  const trace={seed,fields:G.HEAD,initial:G.view(g),actions:[],hashes:[],states:{}};
  function keep(action){const i=trace.actions.length,v=G.view(g);trace.actions.push(action);trace.hashes.push(hash(v));if(i%120===0||g.over)trace.states[i]=v;}
  for(let i=0;i<(kind==='fuzz'?10000:18000);i++){
   if(g.over){if(kind!=='fuzz')break;prng=(Math.imul(prng,1664525)+1013904223)>>>0;g=G.start(prng);driver=P.driver('skilled',prng);keep(['reset',prng]);}
   let input=driver(g);
   if(kind==='fuzz'){prng=(Math.imul(prng,1664525)+1013904223)>>>0;if(prng%5===0)input={ok_down:(prng>>>3)&1,up_down:(prng>>>4)&1,down_down:(prng>>>5)&1,ok_held:(prng>>>6)&1,up_held:(prng>>>7)&1};}
   G.step(g,input);keep(['ok_down','ok_up','up_down','down_down','down_up','ok_held','down_held','up_held'].map(k=>input[k]||0));
  }
  trace.states[trace.actions.length-1]=G.view(g);
  fs.writeFileSync(path.join(out,kind+'.json'),JSON.stringify(trace)+'\n');console.log(name,kind,trace.actions.length,g.score);
 }
}
