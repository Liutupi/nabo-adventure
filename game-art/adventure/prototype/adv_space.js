// SPACE rules reference: integer 60Hz, mulberry32. Screen px with y down; position in 1/256 px,
// velocity in 1/256 px per frame. Hold OK = main engine, hold UP = drift left, hold DOWN = drift right.
// The lander art cannot rotate, so lateral control uses the side thrusters instead of tilting.
(function(root){
  'use strict';
  const GROUND=270,TOP_Y=132,LEFT=48,RIGHT=192,HOLD=6,GRAVITY=5,THRUST=12,SIDE=6,VMAX=1024;
  const MAIN_DRAIN=90,SIDE_DRAIN=40,SAFE_VY=300,SAFE_VX=160,LANDED=150,CRASH=72,CAN=300,HIT=250;
  const OBJS=3,FEET=39,BODY_TOP=80;
  const TYPE={FUEL:1,ROCK:2};
  const PHASE={FLY:0,LANDED:1,CRASH:2};
  const MSG={NONE:0,LANDED:1,HARD:2,MISSED:3,ROCK:4,FUEL:5};
  function random(g){g.rng=(g.rng+0x6D2B79F5)>>>0;let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;}
  const range=(g,a,b)=>a+random(g)%(b-a+1);
  const zone=g=>Math.max(14,40-g.round*4);
  function setupRound(g){
    g.x=range(g,70,170)*256;g.y=TOP_Y*256;g.vx=range(g,-120,120);g.vy=Math.min(240,g.round*30);
    g.pad=range(g,64,176);g.phase=PHASE.FLY;g.timer=0;g.thrust=0;g.side=0;
    for(const o of g.objs)Object.assign(o,{type:0,x:0,y:0,vx:0});
    // One fuel can most rounds; drifting rocks from the third landing on.
    if(random(g)%100<70){const o=g.objs[0],fromLeft=random(g)&1;Object.assign(o,{type:TYPE.FUEL,x:(fromLeft?-20:260)*256,y:range(g,150,230)*256,vx:fromLeft?220:-220});}
    const rocks=g.round<2?0:g.round<4?1:2;
    for(let i=0;i<rocks;i++){const o=g.objs[1+i],fromLeft=random(g)&1;Object.assign(o,{type:TYPE.ROCK,x:(fromLeft?-30:270)*256,y:range(g,140,240)*256,vx:(fromLeft?1:-1)*range(g,150,330)});}
  }
  function start(seed){
    const g={rng:seed>>>0,tick:0,score:0,res:1000,over:0,cue:0,round:0,landings:0,crashes:0,cans:0,phase:0,timer:0,
      x:0,y:0,vx:0,vy:0,pad:120,thrust:0,side:0,drainAcc:0,leftHold:0,rightHold:0,shortTaps:0,downTaps:0,message:0,feedback:0,lastBonus:0,
      objs:Array.from({length:OBJS},()=>({type:0,x:0,y:0,vx:0}))};
    setupRound(g);return g;
  }
  function upEvent(g,pressed){if(pressed)g.leftHold=0;else{g.shortTaps=g.leftHold<HOLD?Math.min(2,g.shortTaps+1):0;g.leftHold=0;}}
  function downEvent(g,pressed){if(pressed)g.rightHold=0;else{g.downTaps=g.rightHold<HOLD?Math.min(2,g.downTaps+1):0;g.rightHold=0;}}
  function feedback(g,msg,cue){g.message=msg;g.feedback=90;g.cue=cue;}
  function crash(g,msg){g.res-=HIT;g.crashes++;g.phase=PHASE.CRASH;g.timer=CRASH;g.vx=g.vy=0;g.thrust=g.side=0;feedback(g,msg,7);}
  function touchdown(g){
    const dx=Math.abs(Math.trunc(g.x/256)-g.pad),soft=g.vy<=SAFE_VY&&Math.abs(g.vx)<=SAFE_VX;
    g.y=GROUND*256;
    if(dx<=zone(g)&&soft){
      const bonus=100+Math.trunc((SAFE_VY-Math.max(0,g.vy))*50/SAFE_VY)+Math.min(50,Math.trunc(g.res/20));
      g.score+=bonus;g.lastBonus=bonus;g.landings++;g.phase=PHASE.LANDED;g.timer=LANDED;g.vx=g.vy=0;g.thrust=g.side=0;feedback(g,MSG.LANDED,6);
    }else crash(g,soft?MSG.MISSED:MSG.HARD);
  }
  function step(g,input){
    input=input||{};g.tick=(g.tick+1)>>>0;g.cue=0;
    if(g.feedback>0)g.feedback--;
    if(g.over)return;
    g.leftHold=input.up_held?Math.min(HOLD,g.leftHold+1):0;g.rightHold=input.down_held?Math.min(HOLD,g.rightHold+1):0;
    if(g.phase!==PHASE.FLY){
      if(--g.timer<=0){if(g.phase===PHASE.LANDED)g.round++;setupRound(g);}
    }else{
      g.thrust=input.ok_held?1:0;g.side=(g.rightHold>=HOLD?1:0)-(g.leftHold>=HOLD?1:0);
      g.drainAcc+=(g.thrust?MAIN_DRAIN:0)+(g.side?SIDE_DRAIN:0);while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}
      g.vy=Math.max(-VMAX,Math.min(VMAX,g.vy+GRAVITY-(g.thrust?THRUST:0)));
      g.vx=Math.max(-VMAX,Math.min(VMAX,g.vx+g.side*SIDE));
      g.x+=g.vx;g.y+=g.vy;
      if(g.x<LEFT*256){g.x=LEFT*256;g.vx=0;}if(g.x>RIGHT*256){g.x=RIGHT*256;g.vx=0;}
      if(g.y<(TOP_Y-60)*256){g.y=(TOP_Y-60)*256;if(g.vy<0)g.vy=0;}
      const lx=Math.trunc(g.x/256),ly=Math.trunc(g.y/256);
      for(const o of g.objs){
        if(!o.type)continue;
        o.x+=o.vx;const ox=Math.trunc(o.x/256),oy=Math.trunc(o.y/256);
        if(ox<-40||ox>280){o.type=0;continue;}
        if(Math.abs(ox-lx)<=FEET+8&&oy>=ly-BODY_TOP-8&&oy<=ly+4){
          o.type===TYPE.FUEL?(g.res=Math.min(1000,g.res+CAN),g.cans++,feedback(g,MSG.FUEL,6)):crash(g,MSG.ROCK);
          o.type=0;if(g.phase!==PHASE.FLY)break;
        }
      }
      if(g.phase===PHASE.FLY&&g.y>=GROUND*256)touchdown(g);
    }
    if(g.res<=0){g.res=0;g.over=1;g.cue=8;}
  }
  const FIELDS=['rng','tick','score','res','over','cue','round','landings','crashes','cans','phase','timer','x','y','vx','vy','pad','thrust','side','drainAcc',
    'leftHold','rightHold','shortTaps','downTaps','message','feedback','lastBonus'];
  const view=g=>[...FIELDS.map(k=>g[k]),...g.objs.flatMap(o=>[o.type,o.x,o.y,o.vx]),zone(g)];
  const status=g=>({score:g.score,res:g.res,over:g.over});
  const api={GROUND,TOP_Y,LEFT,RIGHT,HOLD,GRAVITY,THRUST,SIDE,VMAX,MAIN_DRAIN,SIDE_DRAIN,SAFE_VY,SAFE_VX,LANDED,CRASH,CAN,HIT,OBJS,FEET,BODY_TOP,
    TYPE,PHASE,MSG,FIELDS,start,step,status,view,random,upEvent,downEvent,zone};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvSpace=api;
})(this);
