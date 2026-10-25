// SKI rules reference: integer 60Hz, mulberry32. NABO skis up the screen (rear view);
// world y grows ahead of him in px, x is 1/16 px. Hold UP = left, hold DOWN = right, OK = jump.
(function(root){
  'use strict';
  const CAP=16,LEFT=24,RIGHT=216,AHEAD=340,BEHIND=80,HOLD=6,AIR=34,FALL=48,BUMP_T=24,INVULN=40;
  const ACCEL=5,VMAX=40,SPEED0=40,SPEED_STEP=2,SPEED_MAX=96,DRAIN=15,GATE_HALF=24;
  const MISS=100,TREE=250,BUMP=100,COCOA=300;
  const TYPE={GATE_RED:1,GATE_BLUE:2,TREE:3,PINE:4,MOGUL:5,CABIN:6};
  const MSG={NONE:0,PASS:1,MISS:2,TREE:3,BUMP:4,COCOA:5};
  function random(g){g.rng=(g.rng+0x6D2B79F5)>>>0;let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;}
  const range=(g,a,b)=>a+random(g)%(b-a+1);
  const clear=o=>Object.assign(o,{type:0,x:0,y:0,done:0});
  function slot(g){const o=g.objs.find(e=>!e.type);if(!o)g.blocked++;return o;}
  function nearGate(g,y){return g.objs.find(o=>o.type&&o.type<=TYPE.GATE_BLUE&&Math.abs(o.y-y)<56);}
  function spawnGate(g){
    const o=slot(g);if(!o)return;
    const lo=Math.max(64,g.lastGateX-90),hi=Math.min(176,g.lastGateX+90),x=range(g,lo,hi);
    Object.assign(o,{type:g.gates&1?TYPE.GATE_BLUE:TYPE.GATE_RED,x,y:g.nextGate,done:0});g.lastGateX=x;g.gates++;
  }
  function spawnHazard(g){
    const v=random(g)%100,y=g.nextHazard;let type=v<45?TYPE.TREE:v<65?TYPE.PINE:v<90?TYPE.MOGUL:TYPE.CABIN;
    if(type===TYPE.CABIN&&g.cabinWait>0)type=TYPE.TREE;
    let x=type===TYPE.CABIN?(random(g)&1?200:40):range(g,32,208);
    const gate=nearGate(g,y);
    // Never block a gate corridor: move the hazard to the wider side of the gate.
    if(gate&&Math.abs(x-gate.x)<48)x=gate.x<120?Math.min(208,gate.x+56):Math.max(32,gate.x-56);
    const o=slot(g);if(!o)return;
    Object.assign(o,{type,x,y,done:0});if(type===TYPE.CABIN)g.cabinWait=8;
  }
  function start(seed){
    const g={rng:seed>>>0,tick:0,score:0,res:1000,over:0,cue:0,x:120*16,vx:0,pos:0,speed:SPEED0,air:0,fall:0,invuln:0,
      drainAcc:0,leftHold:0,rightHold:0,shortTaps:0,nextGate:300,nextHazard:200,lastGateX:120,gates:0,cabinWait:3,
      message:0,feedback:0,misses:0,crashes:0,bumps:0,cocoa:0,blocked:0,sub:0,
      objs:Array.from({length:CAP},()=>({type:0,x:0,y:0,done:0}))};
    return g;
  }
  function upEvent(g,pressed){if(pressed)g.leftHold=0;else{g.shortTaps=g.leftHold<HOLD?Math.min(2,g.shortTaps+1):0;g.leftHold=0;}}
  function feedback(g,msg,cue){g.message=msg;g.feedback=60;g.cue=cue;}
  function cross(g,o){
    o.done=1;const dx=Math.abs(Math.trunc(g.x/16)-o.x);
    if(o.type<=TYPE.GATE_BLUE){
      if(dx<=GATE_HALF){if(g.score<0xffffffff)g.score++;g.speed=Math.min(SPEED_MAX,g.speed+SPEED_STEP);feedback(g,MSG.PASS,6);}
      else{g.res-=MISS;g.misses++;feedback(g,MSG.MISS,7);}
    }else if(o.type===TYPE.CABIN){
      if(dx<34){g.res=Math.min(1000,g.res+COCOA);g.cocoa++;feedback(g,MSG.COCOA,6);}
    }else if(!g.invuln&&!g.fall){
      if(o.type===TYPE.TREE&&dx<20){g.res-=TREE;g.crashes++;g.fall=FALL;g.vx=0;g.air=0;feedback(g,MSG.TREE,7);}
      else if(o.type!==TYPE.TREE&&!g.air&&dx<(o.type===TYPE.MOGUL?16:14)){g.res-=BUMP;g.bumps++;g.fall=BUMP_T;g.vx=0;feedback(g,MSG.BUMP,7);}
    }
  }
  function step(g,input){
    input=input||{};g.tick=(g.tick+1)>>>0;g.cue=0;
    for(const k of ['feedback','invuln'])if(g[k]>0)g[k]--;
    if(g.over)return;
    g.leftHold=input.up_held?Math.min(HOLD,g.leftHold+1):0;g.rightHold=input.down_held?Math.min(HOLD,g.rightHold+1):0;
    if(input.ok_down&&!g.air&&!g.fall){g.air=AIR;g.cue=1;}
    if(g.fall){if(--g.fall===0)g.invuln=INVULN;}
    else{
      const dir=(g.rightHold>=HOLD?1:0)-(g.leftHold>=HOLD?1:0);
      if(dir)g.vx=Math.max(-VMAX,Math.min(VMAX,g.vx+dir*ACCEL));else{g.vx-=Math.trunc(g.vx/6);if(Math.abs(g.vx)<4)g.vx=0;}
      g.x+=g.vx;if(g.x<LEFT*16){g.x=LEFT*16;g.vx=0;}if(g.x>RIGHT*16){g.x=RIGHT*16;g.vx=0;}
      if(g.air)g.air--;
      g.sub+=g.speed;const moved=g.sub>>4;g.sub&=15;g.pos+=moved;
    }
    // Gates are placed 60 px earlier than hazards so a hazard can always see the gate it must avoid.
    while(g.pos+AHEAD+60>=g.nextGate){spawnGate(g);g.nextGate+=range(g,190,250);}
    while(g.pos+AHEAD>=g.nextHazard){spawnHazard(g);if(g.cabinWait>0)g.cabinWait--;g.nextHazard+=range(g,70,130)-Math.min(40,g.score);}
    for(const o of g.objs){
      if(!o.type)continue;
      if(!o.done&&o.y<=g.pos)cross(g,o);
      if(o.y<g.pos-BEHIND)clear(o);
    }
    g.drainAcc+=DRAIN;while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}
    if(g.res<=0){g.res=0;g.over=1;g.cue=8;}
  }
  const FIELDS=['rng','tick','score','res','over','cue','x','vx','pos','speed','air','fall','invuln','drainAcc','leftHold','rightHold','shortTaps',
    'nextGate','nextHazard','lastGateX','gates','cabinWait','message','feedback','misses','crashes','bumps','cocoa','blocked','sub'];
  const view=g=>[...FIELDS.map(k=>g[k]),...g.objs.flatMap(o=>[o.type,o.x,o.y,o.done])];
  const status=g=>({score:g.score,res:g.res,over:g.over});
  const api={CAP,LEFT,RIGHT,AHEAD,BEHIND,HOLD,AIR,FALL,BUMP_T,INVULN,ACCEL,VMAX,SPEED0,SPEED_STEP,SPEED_MAX,DRAIN,GATE_HALF,MISS,TREE,BUMP,COCOA,
    TYPE,MSG,FIELDS,start,step,status,view,random,upEvent};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvSki=api;
})(this);
