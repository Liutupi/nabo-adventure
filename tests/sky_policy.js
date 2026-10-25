// SKY policies: aim for an altitude that clears what is on screen, using the real controller.
const Y=require('../game-art/adventure/prototype/adv_sky.js');
function heatTo(g,target){const a=g.alt>>4,v=g.vy;return a+Math.trunc(v*Math.abs(v)/(2*16*(v>0?Y.SINK:Y.LIFT)))/1<target?{ok_held:1}:{};}
function score(c,s0){return (c.score-s0)*3+c.res-(c.over?5000:0);}
function lookahead(g,cands,horizon){
  let best=null;
  for(const t of cands){const c=JSON.parse(JSON.stringify(g)),s0=c.score,r0=c.res;
    for(let i=0;i<horizon&&!c.over;i++)Y.step(c,heatTo(c,t));
    const v=score(c,s0)-r0;if(!best||v>best[0])best=[v,t];}
  return best[1];
}
function driver(kind,seed){
  let target=300,wait=0,rng={rng:seed^0x1234567};
  return function next(g){
    if(g.over||kind==='idle')return {};
    if(kind==='hold')return {ok_held:1};
    if(kind==='pulse')return g.tick%90<40?{ok_held:1}:{};
    if(--wait<=0){
      const a=g.alt>>4,step=kind==='expert'?40:80,cands=[];for(let t=Math.max(30,a-240);t<=Math.min(Y.CEIL-30,a+240);t+=step)cands.push(t);
      target=lookahead(g,cands,kind==='expert'?150:90)+(kind==='casual'?Y.random(rng)%41-20:0);wait=kind==='casual'?24:kind==='skilled'?12:8;}
    return heatTo(g,target);
  };
}
function play(kind,seed,limit=60*60*20){const g=Y.start(seed),next=driver(kind,seed);let n=0;while(!g.over&&n<limit){Y.step(g,next(g));n++;}return {score:g.score,steps:n,hits:g.hits,grounds:g.grounds,stamps:g.stamps,warms:g.warms};}
module.exports={driver,play};
if(require.main===module)for(const kind of ['idle','hold','pulse','casual','skilled','expert']){
  const runs=[];for(let s=1;s<=60;s++)runs.push(play(kind,s*7919));const sc=runs.map(r=>r.score).sort((a,b)=>a-b),avg=k=>Math.round(runs.reduce((a,r)=>a+r[k],0)/runs.length);
  console.log(kind.padEnd(8),'min',sc[0],'med',sc[30],'max',sc[59],'>=200',sc.filter(x=>x>=200).length,'>=500',sc.filter(x=>x>=500).length,'>=1000',sc.filter(x=>x>=1000).length,'sec',Math.round(avg('steps')/60),'hits',avg('hits'),'gnd',avg('grounds'),'stamp',avg('stamps'),'warm',avg('warms'));
}
