// SKY rules reference: integer 60Hz, mulberry32. The balloon's basket point B is fixed on screen;
// altitude (px*16, up positive) and distance (px*16) move the world. Hold OK to heat and climb.
(function(root){
  'use strict';
  const CAP=10,CEIL=1200,LIFT=3,SINK=2,VMAX=40,HEAT_DRAIN=60,SPEED0=24,SPEED_MAX=56,SPAWN_X=260,GONE_X=-90,INVULN=60;
  const ENV_Y=141,ENV_RX=44,ENV_RY=46,BASKET_X=32,BASKET_LO=-22,BASKET_HI=8,WARM_W=36,WARM_H=18;
  const HIT=250,GROUND=250,WARM=200,STAMP=10;
  const TYPE={BIRD:1,STORM:2,STAMP:3,WARM:4};
  const RADIUS=[0,8,18,8,0];
  const MSG={NONE:0,BIRD:1,STORM:2,STAMP:3,WARM:4,GROUND:5};
  function random(g){g.rng=(g.rng+0x6D2B79F5)>>>0;let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;}
  const range=(g,a,b)=>a+random(g)%(b-a+1);
  const clear=o=>Object.assign(o,{type:0,x:0,alt:0,phase:0,done:0});
  const meters=g=>Math.trunc(g.dist/160)+g.bonus;
  function spawn(g){
    const o=g.objs.find(e=>!e.type);if(!o){g.blocked++;return;}
    const v=random(g)%100,type=v<30?TYPE.STORM:v<70?TYPE.BIRD:v<85?TYPE.STAMP:TYPE.WARM;
    const alt=Math.max(40,Math.min(CEIL-40,(g.alt>>4)+range(g,-180,180)));
    Object.assign(o,{type,x:(g.dist>>4)+SPAWN_X,alt,phase:random(g)%64,done:0});
  }
  function start(seed){
    return {rng:seed>>>0,tick:0,score:0,res:1000,over:0,cue:0,alt:300*16,vy:0,dist:0,speed:SPEED0,heating:0,invuln:0,drainAcc:0,
      nextSpawn:220,bonus:0,message:0,feedback:0,hits:0,grounds:0,stamps:0,warms:0,blocked:0,
      objs:Array.from({length:CAP},()=>({type:0,x:0,alt:0,phase:0,done:0}))};
  }
  function feedback(g,msg,cue){g.message=msg;g.feedback=60;g.cue=cue;}
  // Object centre relative to B (y up) against the envelope ellipse and the basket box.
  function touches(dx,dy,r){
    if(dx>=-BASKET_X-r&&dx<=BASKET_X+r&&dy>=BASKET_LO-r&&dy<=BASKET_HI+r)return true;
    const rx=ENV_RX+r,ry=ENV_RY+r,ey=dy-ENV_Y;
    if(Math.abs(dx)>rx||Math.abs(ey)>ry)return false;
    return dx*dx*ry*ry+ey*ey*rx*rx<=rx*rx*ry*ry;
  }
  function objectAlt(o){const q=o.phase%64,v=q<32?q:64-q;return o.type===TYPE.BIRD?o.alt+Math.trunc(v*24/32)-12:o.alt;}
  function step(g,input){
    input=input||{};g.tick=(g.tick+1)>>>0;g.cue=0;
    for(const k of ['feedback','invuln'])if(g[k]>0)g[k]--;
    if(g.over)return;
    g.heating=input.ok_held?1:0;
    g.vy=Math.max(-VMAX,Math.min(VMAX,g.vy+(g.heating?LIFT:-SINK)));
    if(g.heating){g.drainAcc+=HEAT_DRAIN;while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}}
    g.alt+=g.vy;
    if(g.alt>CEIL*16){g.alt=CEIL*16;g.vy=0;}
    if(g.alt<0){g.alt=0;
      // The treetops: every touch while not invulnerable costs and bounces the balloon up.
      if(!g.invuln){g.res-=GROUND;g.grounds++;g.invuln=INVULN;g.vy=32;feedback(g,MSG.GROUND,7);}else g.vy=0;}
    g.dist+=g.speed;g.speed=Math.min(SPEED_MAX,SPEED0+Math.trunc(g.dist/(16*400)));
    while((g.dist>>4)+SPAWN_X>=g.nextSpawn){spawn(g);g.nextSpawn+=range(g,90,160)-Math.min(50,Math.trunc(g.dist/(16*200)));}
    const d=g.dist>>4,a=g.alt>>4;
    for(const o of g.objs){
      if(!o.type)continue;
      if(o.type===TYPE.BIRD){o.x--;o.phase++;}
      const dx=o.x-d;
      if(dx<GONE_X){clear(o);continue;}
      if(o.done)continue;
      const dy=objectAlt(o)-a;
      if(o.type===TYPE.WARM){if(Math.abs(dx)<=WARM_W&&dy>=-WARM_H-BASKET_HI&&dy<=WARM_H-BASKET_LO){o.done=1;g.res=Math.min(1000,g.res+WARM);g.warms++;feedback(g,MSG.WARM,6);}continue;}
      if(!touches(dx,dy,RADIUS[o.type]))continue;
      if(o.type===TYPE.STAMP){o.done=1;g.bonus+=STAMP;g.stamps++;feedback(g,MSG.STAMP,6);}
      else if(!g.invuln){o.done=1;g.res-=HIT;g.hits++;g.invuln=INVULN;feedback(g,o.type===TYPE.BIRD?MSG.BIRD:MSG.STORM,7);}
    }
    g.score=meters(g);
    if(g.res<=0){g.res=0;g.over=1;g.cue=8;}
  }
  const FIELDS=['rng','tick','score','res','over','cue','alt','vy','dist','speed','heating','invuln','drainAcc','nextSpawn','bonus','message','feedback','hits','grounds','stamps','warms','blocked'];
  const view=g=>[...FIELDS.map(k=>g[k]),...g.objs.flatMap(o=>[o.type,o.x,o.alt,o.phase,o.done])];
  const status=g=>({score:g.score,res:g.res,over:g.over});
  const api={CAP,CEIL,LIFT,SINK,VMAX,HEAT_DRAIN,SPEED0,SPEED_MAX,SPAWN_X,GONE_X,INVULN,ENV_Y,ENV_RX,ENV_RY,BASKET_X,BASKET_LO,BASKET_HI,WARM_W,WARM_H,
    HIT,GROUND,WARM,STAMP,TYPE,RADIUS,MSG,FIELDS,start,step,status,view,random,touches,objectAlt};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvSky=api;
})(this);
