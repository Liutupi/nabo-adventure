// NIGHT rules reference: integer60Hz, exact native jar hotspot and mulberry32.
(function(root){
  'use strict';
  const CAP=8,MOVE=20,CAST=30,COOLDOWN=12,LIFE=108,HOLD=6,WALK=5;
  const POS=[54,160,266],FOOT=216,JAR_DX=10,JAR_Y=163,RX=26,RY=20;
  const TYPE={FIREFLY:1,MOTH:2};
  function random(g){g.rng=(g.rng+0x6D2B79F5)>>>0;let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;}
  const range=(g,a,b)=>a+random(g)%(b-a+1);
  const interval=g=>120+Math.min(84,Math.floor(g.score*3/2));
  const mothPercent=g=>Math.min(20,8+Math.floor(g.score/5));
  function objectY(e){const q=(e.age+e.phase)%64,v=q<32?q:64-q;return e.baseY+Math.trunc(v*16/32)-8;}
  function objectX(e){const q=(e.age+e.phase)%48,v=q<24?q:48-q;return (POS[e.lane]+JAR_DX+Math.trunc(v*20/24)-10)*60;}
  function start(seed){return {rng:seed>>>0,tick:0,score:0,res:1000,over:0,lane:1,x:160,fromX:160,move:0,moveDir:0,next:45,drainAcc:0,cast:0,cooldown:0,good:0,bad:0,feedback:0,message:0,cue:0,misses:0,caughtX:0,caughtY:0,spawnBlocked:0,bag:0,bagLeft:0,lastLane:-1,escaped:0,leftHold:0,rightHold:0,shortTaps:0,bugs:Array.from({length:CAP},()=>({type:0,x:0,baseY:0,lane:0,phase:0,age:0}))};}
  function upEvent(g,pressed){if(pressed)g.rightHold=0;else{g.shortTaps=g.rightHold<HOLD?Math.min(2,g.shortTaps+1):0;g.rightHold=0;}}
  function target(g){
    let found=-1,best=2147483647;
    for(let i=0;i<CAP;i++){
      const e=g.bugs[i];if(!e.type)continue;
      const dx=e.x-(g.x+JAR_DX)*60,dy=(objectY(e)-JAR_Y)*60;
      if(Math.abs(dx)>RX*60||Math.abs(dy)>RY*60)continue;
      const d=dx*dx*RY*RY+dy*dy*RX*RX;
      if(d<=RX*RX*RY*RY*3600&&d<best){found=i;best=d;}
    }
    return found;
  }
  function spawn(g){
    const e=g.bugs.find(e=>!e.type);
    if(!e){g.spawnBlocked++;return;}
    // Every three appearances visit all groves. Never repeat at a bag boundary.
    if(!g.bagLeft){g.bag=[36,24,33,9,18,6][random(g)%6];if((g.bag&3)===g.lastLane)g.bag=(g.bag&48)|((g.bag&3)<<2)|((g.bag>>2)&3);g.bagLeft=3;}
    const lane=g.bag&3;g.bag>>=2;g.bagLeft--;g.lastLane=lane;
    Object.assign(e,{type:TYPE.FIREFLY,x:0,baseY:range(g,JAR_Y-8,JAR_Y+8),lane,phase:random(g)%64,age:0});e.x=objectX(e);
    // A decoy never replaces the real opportunity: gold remains skill-based.
    if(random(g)%100<mothPercent(g)){
      const moth=g.bugs.find(b=>!b.type);
      if(moth){Object.assign(moth,{type:TYPE.MOTH,x:0,baseY:range(g,JAR_Y-8,JAR_Y+8),lane:(lane+1+random(g)%2)%3,phase:random(g)%64,age:0});moth.x=objectX(moth);}
    }
  }
  function step(g,input){
    input=input||{};g.tick=(g.tick+1)>>>0;g.cue=0;
    for(const name of ['cast','cooldown','good','bad','feedback'])if(g[name]>0)g[name]--;
    if(g.over)return;
    // Clockwise landscape: physical left=OK, middle=DOWN, right=UP.
    const pressed=!!input.down_down&&!g.cooldown,hit=pressed?target(g):-1;
    const caughtX=hit<0?0:Math.trunc(g.bugs[hit].x/60),caughtY=hit<0?0:objectY(g.bugs[hit]);
    g.leftHold=input.ok_held?Math.min(HOLD,g.leftHold+1):0;g.rightHold=input.up_held?Math.min(HOLD,g.rightHold+1):0;
    const direction=(g.rightHold>=HOLD?1:0)-(g.leftHold>=HOLD?1:0),oldX=g.x;
    g.fromX=g.x;g.x=Math.max(POS[0],Math.min(POS[2],g.x+direction*WALK));
    g.move=g.x!==oldX?MOVE-g.tick%MOVE:0;if(g.move)g.moveDir=direction;
    g.lane=Math.max(0,Math.min(2,Math.floor((g.x-POS[0]+53)/106)));
    g.drainAcc+=25;while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}
    if(--g.next<=0){spawn(g);g.next=interval(g)+range(g,0,12);}
    for(const e of g.bugs)if(e.type){e.age++;e.x=objectX(e);if(e.age>=LIFE){if(e.type===TYPE.FIREFLY)g.escaped++;Object.assign(e,{type:0,x:0,baseY:0,lane:0,phase:0,age:0});}}
    if(pressed){
      const index=hit;g.cast=CAST;g.cooldown=COOLDOWN;g.feedback=60;
      if(index<0){g.message=1;g.misses++;g.cue=7;}
      else{
        const e=g.bugs[index];g.caughtX=caughtX;g.caughtY=caughtY;
        if(e.type===TYPE.FIREFLY){if(g.score<0xffffffff)g.score++;g.res=Math.min(1000,g.res+60);g.good=60;g.bad=0;g.message=2;g.cue=6;}
        else{g.res-=250;g.bad=60;g.good=0;g.message=3;g.cue=7;}
        Object.assign(e,{type:0,x:0,baseY:0,lane:0,phase:0,age:0});
      }
    }
    if(g.res<=0){g.res=0;g.over=1;g.cue=8;}
  }
  const FIELDS=['rng','tick','score','res','over','lane','x','fromX','move','moveDir','next','drainAcc','cast','cooldown','good','bad','feedback','message','cue','misses','caughtX','caughtY','spawnBlocked','bag','bagLeft','lastLane','escaped','leftHold','rightHold','shortTaps'];
  const view=g=>[...FIELDS.map(k=>g[k]),...g.bugs.flatMap(e=>[e.type,e.x,e.baseY,e.lane,e.phase,e.age]),target(g),interval(g)];
  const status=g=>({score:g.score,res:g.res,over:g.over});
  const api={CAP,MOVE,CAST,COOLDOWN,LIFE,HOLD,WALK,POS,FOOT,JAR_DX,JAR_Y,RX,RY,TYPE,FIELDS,start,step,status,target,objectX,objectY,interval,mothPercent,view,random,upEvent};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvNight=api;
})(this);
