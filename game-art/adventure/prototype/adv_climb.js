// CLIMB rules reference: integer 60Hz, mulberry32, world y grows upward in px.
// Rows are 1 m apart. NABO hangs on the left (0) or right (1) wall at one row.
(function(root){
  'use strict';
  const ROW=40,RING=32,AHEAD=12,FLOOR=28,ROCKS=4;
  const TAP=12,CHARGE3=40,SWITCH=24,JUMP=30,SLIDE=30,FRAGILE=60,INVULN=60,CHEER=48;
  const DRAIN=30,ICE_DRAIN=60,GAIN=20,CANTEEN=250,HIT=250,MISS=100;
  const ROCK_V=3,ROCK_START=8,ROCK_SPAWN=9,BODY_LO=41,BODY_HI=21,ROCK_H=24;
  const HOLD={NONE:0,NORMAL:1,FRAGILE:2,ICE:3};
  const ACT={IDLE:0,SWITCH:1,JUMP:2,SLIDE:3};
  const MSG={NONE:0,MISS:1,HIT:2,CRUMBLE:3,CANTEEN:4,MILESTONE:5};
  function random(g){g.rng=(g.rng+0x6D2B79F5)>>>0;let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return (t^(t>>>14))>>>0;}
  const range=(g,a,b)=>a+random(g)%(b-a+1);
  // Row byte: bits0-1 left hold, bits2-3 right hold, bit4 canteen left, bit5 canteen right.
  const cell=(g,r)=>g.grid[r%RING];
  function hold(g,r,s){if(r<0||r>g.genTop||r<g.genTop-RING+1)return 0;return (cell(g,r)>>(s*2))&3;}
  function setHold(g,r,s,t){const i=r%RING;g.grid[i]=(g.grid[i]&~(3<<(s*2)))|(t<<(s*2));}
  const solid=(g,r,s)=>{const t=hold(g,r,s);return t===HOLD.NORMAL||t===HOLD.ICE;};
  const canteen=(g,r,s)=>r>=0&&r<=g.genTop&&r>g.genTop-RING&&((cell(g,r)>>(4+s))&1);
  const fragilePercent=h=>h<12?0:Math.min(22,4+Math.trunc(h/12));
  const icePercent=h=>h<80?0:Math.min(25,5+Math.trunc((h-80)/10));
  const bothPercent=h=>Math.max(25,50-Math.trunc(h/6));
  function rockInterval(g){return Math.max(120,300-Math.trunc(g.score*3/5));}
  function kind(g,h){const v=random(g)%100,f=fragilePercent(h),i=icePercent(h);return v<f?HOLD.FRAGILE:v<f+i?HOLD.ICE:HOLD.NORMAL;}
  function generate(g){
    const k=++g.genTop;g.grid[k%RING]=0;
    // The first metres are a ladder on both walls so a new player can learn tap and jump safely.
    if(k<=4)g.grid[k%RING]=HOLD.NORMAL|(HOLD.NORMAL<<2);
    else if(random(g)%100<bothPercent(k)){setHold(g,k,0,kind(g,k));setHold(g,k,1,kind(g,k));}
    else setHold(g,k,random(g)&1,kind(g,k));
    // Every hold three rows down must offer a move onto a hold that cannot crumble.
    const j=k-3;
    if(j>=0)for(let s=0;s<2;s++)if(hold(g,j,s)&&!solid(g,j+1,1-s)&&!solid(g,j+2,s)&&!solid(g,k,s))setHold(g,k,s,HOLD.NORMAL);
    // A canteen waits for the next row with a hold that cannot crumble.
    if(g.canteenNext>0)g.canteenNext--;
    const a=solid(g,k,0),b=solid(g,k,1);
    if(g.canteenNext<=0&&k>=20&&(a||b)){
      const s=a&&b?random(g)&1:a?0:1;
      g.grid[k%RING]|=1<<(4+s);g.canteenNext=range(g,24,36);
    }
  }
  function start(seed){
    const g={rng:seed>>>0,tick:0,score:0,res:1000,over:0,cue:0,row:0,side:0,act:0,actT:0,actLen:0,fromRow:0,fromSide:0,toRow:0,toSide:0,
      press:-1,queue:0,fragileT:0,drainAcc:0,genTop:0,canteenNext:30,rockNext:240,invuln:0,cheer:0,message:0,feedback:0,hits:0,misses:0,crumbles:0,canteens:0,
      grid:new Array(RING).fill(0),rocks:Array.from({length:ROCKS},()=>({on:0,side:0,y:0}))};
    g.grid[0]=HOLD.NORMAL|(HOLD.NORMAL<<2);
    while(g.genTop<AHEAD)generate(g);
    return g;
  }
  // Hand height in px of the logical position during actions (draw and rock checks share it).
  function handY(g){
    if(g.act===ACT.IDLE)return g.row*ROW;
    const done=g.actLen-g.actT;return g.fromRow*ROW+Math.trunc((g.toRow-g.fromRow)*ROW*done/g.actLen);
  }
  function bodySide(g){return g.act===ACT.SWITCH&&g.actT*2>g.actLen?g.fromSide:g.act===ACT.IDLE?g.side:g.toSide;}
  function slideTarget(g,r,s){
    const floor=Math.max(0,g.genTop-FLOOR);
    for(let t=r-1;t>=floor&&t>=r-3;t--){if(hold(g,t,s))return [t,s];if(hold(g,t,1-s))return [t,1-s];}
    return [r,s];
  }
  function begin(g,act,len,toRow,toSide){g.act=act;g.actT=g.actLen=len;g.fromRow=g.row;g.fromSide=g.side;g.toRow=toRow;g.toSide=toSide;g.fragileT=0;}
  function slide(g){const t=slideTarget(g,g.row,g.side);begin(g,ACT.SLIDE,SLIDE,t[0],t[1]);}
  function act(g,intent){
    const n=intent===1?1:intent===2?2:3,toSide=intent===1?1-g.side:g.side,toRow=g.row+n;
    if(hold(g,toRow,toSide))begin(g,intent===1?ACT.SWITCH:ACT.JUMP,intent===1?SWITCH:JUMP,toRow,toSide);
    else{g.misses++;g.res-=MISS;g.message=MSG.MISS;g.feedback=60;g.cue=7;slide(g);}
  }
  function land(g){
    g.row=g.toRow;g.side=g.toSide;const wasSlide=g.act===ACT.SLIDE;g.act=ACT.IDLE;g.actT=g.actLen=0;
    if(wasSlide)return;
    if(g.row>g.score){
      const gained=g.row-g.score,before=Math.trunc(g.score/50);g.score=g.row;g.res=Math.min(1000,g.res+GAIN*gained);g.cue=1;
      if(Math.trunc(g.score/50)>before){g.cheer=CHEER;g.message=MSG.MILESTONE;g.feedback=90;g.cue=6;}
    }
    if(canteen(g,g.row,g.side)){g.grid[g.row%RING]&=~(1<<(4+g.side));g.res=Math.min(1000,g.res+CANTEEN);g.canteens++;g.message=MSG.CANTEEN;g.feedback=60;g.cue=6;}
    if(hold(g,g.row,g.side)===HOLD.FRAGILE)g.fragileT=FRAGILE;
  }
  function step(g,input){
    input=input||{};g.tick=(g.tick+1)>>>0;g.cue=0;
    for(const k of ['invuln','cheer','feedback'])if(g[k]>0)g[k]--;
    if(g.over)return;
    let intent=0;
    if(input.ok_down)g.press=0;
    else if(g.press>=0&&g.press<255)g.press++;
    if(input.ok_up&&g.press>=0){intent=g.press<TAP?1:g.press>=CHARGE3?3:2;g.press=-1;}
    if(intent)g.queue=intent;
    if(g.act!==ACT.IDLE&&--g.actT<=0)land(g);
    if(g.act===ACT.IDLE&&g.queue){const q=g.queue;g.queue=0;g.cheer=0;act(g,q);}
    if(g.act===ACT.IDLE&&g.fragileT>0&&--g.fragileT===0){setHold(g,g.row,g.side,HOLD.NONE);g.crumbles++;g.message=MSG.CRUMBLE;g.feedback=60;g.cue=7;slide(g);}
    while(g.genTop<Math.max(g.row,g.toRow)+AHEAD)generate(g);
    const icy=g.act===ACT.IDLE&&hold(g,g.row,g.side)===HOLD.ICE;
    g.drainAcc+=icy?ICE_DRAIN:DRAIN;while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}
    if(g.score>=ROCK_START&&--g.rockNext<=0){
      const r=g.rocks.find(e=>!e.on);
      if(r){r.on=1;r.side=random(g)%100<60?g.side:1-g.side;r.y=(g.row+ROCK_SPAWN)*ROW;}
      g.rockNext=rockInterval(g)+range(g,0,60);
    }
    const hand=handY(g),side=bodySide(g);
    for(const r of g.rocks){
      if(!r.on)continue;r.y-=ROCK_V;
      if(r.y<(g.row-6)*ROW){r.on=0;continue;}
      if(!g.invuln&&r.side===side&&r.y<=hand+BODY_HI&&r.y+ROCK_H>=hand-BODY_LO){
        r.on=0;g.res-=HIT;g.hits++;g.invuln=INVULN;g.message=MSG.HIT;g.feedback=60;g.cue=7;g.queue=0;
        if(g.act!==ACT.SLIDE){if(g.act!==ACT.IDLE){const first=g.actT*2>g.actLen;g.row=first?g.fromRow:g.toRow;g.side=first?g.fromSide:g.toSide;}slide(g);}
      }
    }
    if(g.res<=0){g.res=0;g.over=1;g.cue=8;}
  }
  const FIELDS=['rng','tick','score','res','over','cue','row','side','act','actT','actLen','fromRow','fromSide','toRow','toSide','press','queue','fragileT','drainAcc','genTop','canteenNext','rockNext','invuln','cheer','message','feedback','hits','misses','crumbles','canteens'];
  const view=g=>[...FIELDS.map(k=>g[k]),...g.grid,...g.rocks.flatMap(r=>[r.on,r.side,r.y]),handY(g),bodySide(g)];
  const status=g=>({score:g.score,res:g.res,over:g.over});
  const api={ROW,RING,AHEAD,FLOOR,ROCKS,TAP,CHARGE3,SWITCH,JUMP,SLIDE,FRAGILE,INVULN,CHEER,DRAIN,ICE_DRAIN,GAIN,CANTEEN,HIT,MISS,ROCK_V,ROCK_START,ROCK_SPAWN,BODY_LO,BODY_HI,ROCK_H,
    HOLD,ACT,MSG,FIELDS,start,step,status,view,random,hold,solid,canteen,handY,bodySide,slideTarget,rockInterval,fragilePercent,icePercent,bothPercent};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvClimb=api;
})(this);
