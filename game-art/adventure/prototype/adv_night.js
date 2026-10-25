// NIGHT rules reference: integer60Hz, exact native jar hotspot and mulberry32.
(function(root){
  'use strict';
  const CAP=8,MOVE=20,CAST=30,COOLDOWN=12;
  const POS=[48,120,192],FOOT=280,JAR_DX=10,JAR_Y=227,RX=26,RY=20;
  const TYPE={FIREFLY:1,MOTH:2};
  function random(g){g.rng=(g.rng+0x6D2B79F5)>>>0;let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;}
  const range=(g,a,b)=>a+random(g)%(b-a+1);
  const speed=g=>Math.min(110,48+g.score);
  const mothPercent=g=>Math.min(32,8+Math.floor(g.score/2));
  function objectY(e){const q=(e.age+e.phase)%64,v=q<32?q:64-q;return e.baseY+Math.trunc(v*16/32)-8;}
  function start(seed){return {rng:seed>>>0,tick:0,score:0,res:1000,over:0,lane:1,x:120,fromX:120,move:0,moveDir:0,next:30,drainAcc:0,cast:0,cooldown:0,good:0,bad:0,feedback:0,message:0,cue:0,misses:0,caughtX:0,caughtY:0,spawnBlocked:0,bugs:Array.from({length:CAP},()=>({type:0,x:0,baseY:0,dir:0,phase:0,age:0}))};}
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
    const type=random(g)%100<mothPercent(g)?TYPE.MOTH:TYPE.FIREFLY;
    const dir=random(g)%2?1:-1,baseY=range(g,JAR_Y-10,JAR_Y+10),phase=random(g)%64;
    Object.assign(e,{type,x:(dir>0?-12:252)*60,baseY,dir,phase,age:0});
  }
  function step(g,input){
    input=input||{};g.tick=(g.tick+1)>>>0;g.cue=0;
    for(const name of ['cast','cooldown','good','bad','feedback'])if(g[name]>0)g[name]--;
    if(g.over)return;
    const pressed=!!input.ok_down&&!g.cooldown,hit=pressed?target(g):-1;
    const caughtX=hit<0?0:Math.trunc(g.bugs[hit].x/60),caughtY=hit<0?0:objectY(g.bugs[hit]);
    if(!!input.up_down!==!!input.down_down){
      const lane=Math.max(0,Math.min(2,g.lane+(input.up_down?-1:1)));
      if(lane!==g.lane){g.lane=lane;g.fromX=g.x;g.move=MOVE;g.moveDir=input.up_down?-1:1;g.cue=1;}
    }
    if(g.move){const elapsed=MOVE-g.move+1;g.x=g.fromX+Math.trunc((POS[g.lane]-g.fromX)*elapsed/MOVE);g.move--;if(!g.move)g.x=POS[g.lane];}
    g.drainAcc+=25;while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}
    if(--g.next<=0){spawn(g);g.next=Math.min(180,range(g,84,100)+Math.floor(g.score*3/4));}
    const velocity=speed(g);
    for(const e of g.bugs)if(e.type){e.age++;e.x+=e.dir*velocity;if(e.x< -24*60||e.x>264*60)Object.assign(e,{type:0,x:0,baseY:0,dir:0,phase:0,age:0});}
    if(pressed){
      const index=hit;g.cast=CAST;g.cooldown=COOLDOWN;g.feedback=60;
      if(index<0){g.message=1;g.misses++;g.cue=7;}
      else{
        const e=g.bugs[index];g.caughtX=caughtX;g.caughtY=caughtY;
        if(e.type===TYPE.FIREFLY){if(g.score<0xffffffff)g.score++;g.res=Math.min(1000,g.res+60);g.good=60;g.bad=0;g.message=2;g.cue=6;}
        else{g.res-=250;g.bad=60;g.good=0;g.message=3;g.cue=7;}
        Object.assign(e,{type:0,x:0,baseY:0,dir:0,phase:0,age:0});
      }
    }
    if(g.res<=0){g.res=0;g.over=1;g.cue=8;}
  }
  const FIELDS=['rng','tick','score','res','over','lane','x','fromX','move','moveDir','next','drainAcc','cast','cooldown','good','bad','feedback','message','cue','misses','caughtX','caughtY','spawnBlocked'];
  const view=g=>[...FIELDS.map(k=>g[k]),...g.bugs.flatMap(e=>[e.type,e.x,e.baseY,e.dir,e.phase,e.age]),target(g),speed(g)];
  const status=g=>({score:g.score,res:g.res,over:g.over});
  const api={CAP,MOVE,CAST,COOLDOWN,POS,FOOT,JAR_DX,JAR_Y,RX,RY,TYPE,FIELDS,start,step,status,target,objectY,speed,mothPercent,view,random};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvNight=api;
})(this);
