// CLIMB input policies for balancing and golden traces. They press real OK edges
// with human-like hold lengths; nothing reads hidden state the screen does not show.
const C=require('../game-art/adventure/prototype/adv_climb.js');
const HOLD_FOR={1:4,2:20,3:46};
// Rows of rock travel before it reaches NABO, judged from the visible rock.
function rockDanger(g,side,frames){
  const hand=C.handY(g);
  return g.rocks.some(r=>r.on&&r.side===side&&r.y-C.ROCK_V*frames<=hand+C.BODY_HI+C.ROW&&r.y+C.ROCK_H>=hand-C.BODY_LO);
}
function choose(g,opts){
  const r=g.row,s=g.side,list=[];
  const moves=[[1,r+1,1-s,C.SWITCH],[2,r+2,s,C.JUMP],[3,r+3,s,C.JUMP]];
  for(const [intent,row,side,len] of moves){
    const t=C.hold(g,row,side);if(!t)continue;
    let cost=-(row-r)*10;
    if(t===C.HOLD.FRAGILE)cost+=opts.fragile;
    if(t===C.HOLD.ICE)cost+=opts.ice;
    if(intent===3)cost+=opts.charge3;
    if(C.canteen(g,row,side))cost-=opts.canteen;
    if(rockDanger(g,side,len+HOLD_FOR[intent]+opts.react))cost+=100;
    list.push([cost,intent]);
  }
  list.sort((a,b)=>a[0]-b[0]);
  return list.length?list[0][1]:0;
}
// A stateful driver; call next(g) once per step to get that step's input.
function driver(kind,seed){
  let pressing=0,left=0,wait=0,rng={rng:seed^0x9e3779b9};
  const opts={skilled:{fragile:12,ice:6,charge3:8,canteen:25,react:0,delay:[6,14]},casual:{fragile:4,ice:2,charge3:14,canteen:8,react:6,delay:[14,34]},
    icy:{fragile:12,ice:-40,charge3:8,canteen:25,react:0,delay:[6,14]},  // icy hangs on frozen holds
    lazy:{fragile:-40,ice:2,charge3:14,canteen:8,react:6,delay:[14,34]}}[kind];  // lazy seeks crumbling rock
  return function next(g){
    if(pressing){if(--left<=0){pressing=0;return {ok_up:1};}return {ok_held:1};}
    if(g.over)return {};
    if(kind==='idle')return {};
    if(kind==='tapper'){if(g.act===C.ACT.IDLE&&!g.queue){pressing=1;left=HOLD_FOR[1];return {ok_down:1,ok_held:1};}return {};}
    if(kind==='jumper'){if(g.act===C.ACT.IDLE&&!g.queue){pressing=1;left=HOLD_FOR[2];return {ok_down:1,ok_held:1};}return {};}
    if(g.act!==C.ACT.IDLE||g.queue||g.press>=0)return {};
    // A visible rock in this column: cross over now if a hold is there, else hang on.
    if(rockDanger(g,g.side,C.SWITCH+opts.react+8)){
      if(C.hold(g,g.row+1,1-g.side)&&!rockDanger(g,1-g.side,C.SWITCH+8)){wait=0;pressing=1;left=HOLD_FOR[1];return {ok_down:1,ok_held:1};}
      return {};
    }
    if(wait>0){wait--;return {};}
    const intent=choose(g,opts);
    if(!intent)return {};
    wait=opts.delay[0]+C.random(rng)%(opts.delay[1]-opts.delay[0]+1);
    pressing=1;left=HOLD_FOR[intent];return {ok_down:1,ok_held:1};
  };
}
function play(kind,seed,limit=60*60*20){
  const g=C.start(seed),next=driver(kind,seed);let steps=0;
  while(!g.over&&steps<limit){C.step(g,next(g));steps++;}
  return {score:g.score,steps,hits:g.hits,misses:g.misses,crumbles:g.crumbles,canteens:g.canteens};
}
module.exports={driver,play,choose,rockDanger};
if(require.main===module){
  for(const kind of ['idle','tapper','jumper','casual','skilled']){
    const runs=[];for(let s=1;s<=40;s++)runs.push(play(kind,s*7919));
    const sc=runs.map(r=>r.score).sort((a,b)=>a-b),avg=k=>Math.round(runs.reduce((a,r)=>a+r[k],0)/runs.length);
    console.log(kind.padEnd(8),'min',sc[0],'med',sc[20],'max',sc[39],'sec',Math.round(avg('steps')/60),'hits',avg('hits'),'miss',avg('misses'),'crumble',avg('crumbles'),'canteen',avg('canteens'));
  }
}
