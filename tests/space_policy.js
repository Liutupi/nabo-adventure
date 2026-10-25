// SPACE policies: an autopilot that reads the lander, pad and visible objects like a player would.
const P=require('../game-art/adventure/prototype/adv_space.js');
function pilot(g,o){
  const x=Math.trunc(g.x/256),h=P.GROUND-Math.trunc(g.y/256),input={};
  const want=Math.min(o.vmax,o.vland+h*o.slope);
  if(g.vy>want)input.ok_held=1;
  const target=Math.max(-o.hmax,Math.min(o.hmax,(g.pad-x)*o.gain));
  if(target-g.vx>o.dead)input.down_held=1;else if(target-g.vx<-o.dead)input.up_held=1;
  return input;
}
function driver(kind,seed){
  const opts={skilled:{vmax:700,vland:150,slope:4,hmax:320,gain:5,dead:24,jitter:0},casual:{vmax:900,vland:200,slope:5,hmax:420,gain:7,dead:60,jitter:4},
    sloppy:{vmax:700,vland:150,slope:4,hmax:700,gain:14,dead:260,jitter:0}}[kind];  // lands while still drifting
  let rng={rng:seed^0x77},hold=0,cur={};
  return function next(g){
    if(g.over||kind==='idle')return {};
    if(kind==='hover')return g.tick%30<16?{ok_held:1}:{};
    if(g.phase!==P.PHASE.FLY)return {};
    if(opts.jitter&&--hold>0)return cur;
    cur=pilot(g,opts);hold=opts.jitter?1+P.random(rng)%opts.jitter:0;return cur;
  };
}
function play(kind,seed,limit=60*60*20){const g=P.start(seed),next=driver(kind,seed);let n=0;while(!g.over&&n<limit){P.step(g,next(g));n++;}return {score:g.score,steps:n,landings:g.landings,crashes:g.crashes,cans:g.cans};}
module.exports={driver,play,pilot};
if(require.main===module)for(const kind of ['idle','hover','casual','skilled']){
  const runs=[];for(let s=1;s<=100;s++)runs.push(play(kind,s*7919));const sc=runs.map(r=>r.score).sort((a,b)=>a-b),avg=k=>Math.round(runs.reduce((a,r)=>a+r[k],0)/runs.length*10)/10;
  console.log(kind.padEnd(8),'min',sc[0],'med',sc[50],'max',sc[99],'>=300',sc.filter(x=>x>=300).length,'>=600',sc.filter(x=>x>=600).length,'>=900',sc.filter(x=>x>=900).length,'sec',Math.round(avg('steps')/60),'land',avg('landings'),'crash',avg('crashes'),'cans',avg('cans'));
}
