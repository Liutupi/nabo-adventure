// SKI input policies from what the screen shows: upcoming gates and hazards.
const K=require('../game-art/adventure/prototype/adv_ski.js');
function plan(g,opts){
  const x=Math.trunc(g.x/16),ahead=g.objs.filter(o=>o.type&&!o.done&&o.y>g.pos&&o.y-g.pos<opts.sight).sort((a,b)=>a.y-b.y);
  const gate=ahead.find(o=>o.type<=K.TYPE.GATE_BLUE);
  let target=gate?gate.x:120;
  // Steer around trees that sit on the line to the target; jump moguls and small pines.
  for(const o of ahead){
    if(o.type===K.TYPE.TREE&&Math.abs(o.x-target)<26&&(!gate||o.y<gate.y))target=o.x<target?Math.min(208,o.x+30):Math.max(32,o.x-30);
    if(o.type===K.TYPE.CABIN&&g.res<opts.cocoa&&(!gate||o.y<gate.y-40))target=o.x;
  }
  const bump=ahead.find(o=>(o.type===K.TYPE.MOGUL||o.type===K.TYPE.PINE)&&Math.abs(o.x-x)<18&&o.y-g.pos<=Math.trunc(g.speed*opts.jumpLead/16));
  return {target,jump:!!bump};
}
// Look-ahead skier: tries a few visible targets on a copy of the run and keeps the best.
function steerTo(g,target){const x=Math.trunc(g.x/16),need=target-x,brake=Math.trunc(g.vx*Math.abs(g.vx)/(2*K.ACCEL*16));
  return need-brake>4?{down_held:1}:need-brake<-4?{up_held:1}:{};}
function bumpAhead(g,lead){const x=Math.trunc(g.x/16);return g.objs.some(o=>(o.type===K.TYPE.MOGUL||o.type===K.TYPE.PINE)&&!o.done&&o.y>g.pos&&Math.abs(o.x-x)<18&&o.y-g.pos<=Math.trunc(g.speed*lead/16));}
function lookahead(g,horizon){
  const gate=g.objs.filter(o=>o.type&&o.type<=K.TYPE.GATE_BLUE&&!o.done&&o.y>g.pos).sort((a,b)=>a.y-b.y)[0];
  const base=gate?gate.x:120,cands=[base,base-14,base+14,40,80,160,200,Math.trunc(g.x/16)];let best=null;
  for(const t of cands){
    const c=JSON.parse(JSON.stringify(g));let jumpUp=0;const s0=c.score,r0=c.res;
    for(let i=0;i<horizon&&!c.over;i++){const inp=steerTo(c,t);if(jumpUp){inp.ok_up=1;jumpUp=0;}else if(!c.air&&bumpAhead(c,20)){inp.ok_down=1;jumpUp=1;}K.step(c,inp);}
    const v=(c.score-s0)*150+(c.res-r0)+(c.over?-5000:0);if(!best||v>best[0])best=[v,t];
  }
  return best[1];
}
function driver(kind,seed){
  const opts={skilled:{sight:300,cocoa:700,jumpLead:20,wobble:0,delay:0},casual:{sight:200,cocoa:500,jumpLead:16,wobble:10,delay:12}}[kind];
  let rng={rng:seed^0x2545f491},target=120,wait=0,jumpHeld=0;
  return function next(g){
    if(g.over||kind==='idle')return {};
    if(kind==='straight')return {};
    if(kind==='wiggle'){const t=g.tick%120;return t<60?{up_held:1}:{down_held:1};}
    if(kind==='expert'){if(--wait<=0){target=lookahead(g,90);wait=6;}const inp=steerTo(g,target);
      if(jumpHeld){jumpHeld=0;inp.ok_up=1;}else if(!g.air&&bumpAhead(g,20)){jumpHeld=1;inp.ok_down=1;inp.ok_held=1;}return inp;}
    if(--wait<=0){const p=plan(g,opts);target=p.target+(opts.wobble?K.random(rng)%(2*opts.wobble+1)-opts.wobble:0);wait=opts.delay+1;
      if(p.jump&&!g.air&&!jumpHeld){jumpHeld=1;return {ok_down:1,ok_held:1};}}
    const input={};if(jumpHeld){jumpHeld=0;input.ok_up=1;}
    const x=Math.trunc(g.x/16),need=target-x,brake=Math.trunc(g.vx*Math.abs(g.vx)/(2*K.ACCEL*16));
    if(need-brake>4)input.down_held=1;else if(need-brake<-4)input.up_held=1;
    return input;
  };
}
function play(kind,seed,limit=60*60*20){const g=K.start(seed),next=driver(kind,seed);let n=0;while(!g.over&&n<limit){K.step(g,next(g));n++;}return {score:g.score,steps:n,misses:g.misses,crashes:g.crashes,bumps:g.bumps,cocoa:g.cocoa};}
module.exports={driver,play};
if(require.main===module)for(const kind of ['idle','wiggle','casual','skilled','expert']){
  const runs=[];for(let s=1;s<=100;s++)runs.push(play(kind,s*7919));const sc=runs.map(r=>r.score).sort((a,b)=>a-b),avg=k=>Math.round(runs.reduce((a,r)=>a+r[k],0)/runs.length);
  console.log(kind.padEnd(8),'min',sc[0],'med',sc[50],'max',sc[99],'>=10',sc.filter(x=>x>=10).length,'>=25',sc.filter(x=>x>=25).length,'>=45',sc.filter(x=>x>=45).length,'sec',Math.round(avg('steps')/60),'miss',avg('misses'),'crash',avg('crashes'),'bump',avg('bumps'),'cocoa',avg('cocoa'));
}
