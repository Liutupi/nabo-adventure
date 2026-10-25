// POST rules reference: integer 60 Hz, positions in 1/60 px. No rendering/clock.
(function(root) {
  'use strict';
  const TYPE={FORK:1,STATION:2,COAL:3,ANIMAL:4,DEPOT:5};
  const X=110*60, MAIL_X=156*60, WINDOW=32*60, HOLD=24, CAP=12;
  const WIDTH=320,HEIGHT=240,UPPER=132,LOWER=212;
  const DEFAULT={speed:90,drain:20,hornDrain:30,forkMin:150,forkMax:240};
  function random(g) {
    g.rng=(g.rng+0x6D2B79F5)>>>0;
    let t=g.rng;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);
    return (t^(t>>>14))>>>0;
  }
  function range(g,a,b) { return a+random(g)%(b-a+1); }
  function spawn(g,type,x,lane,color) {
    const e=g.events.find(e=>!e.type);
    if (!e) { g.spawnBlocked++;return; }
    Object.assign(e,{type,x:x*60,lane,color,done:0,horn:0});
  }
  function load(g) {
    g.remaining=g.lap ? range(g,3,5) : 3;
    g.mail=Array(5).fill(0);
    for(let i=0;i<g.remaining;i++)g.mail[i]=random(g)%(g.lap>=2?4:3);
    g.refill=0;
  }
  function start(seed,config) {
    const g={rng:seed>>>0,tick:0,score:0,res:1000,over:0,lane:1,choice:1,
      y:LOWER,transition:0,speed:90,drainAcc:0,hold:0,whistle:0,lap:0,remaining:0,
      refill:0,nextFork:100,nextCoal:300,nextAnimal:360,hit:0,miss:0,delivered:0,
      cue:0,spawnBlocked:0,distance:0,practice:0,lesson:0,tapTarget:-1,tapReason:0,missReason:0,feedback:0,presses:0,taps:0,mail:[],events:Array.from({length:CAP},()=>({type:0,x:0,lane:0,color:0,done:0,horn:0})),
      config:Object.assign({},DEFAULT,config||{})};
    g.speed=g.config.speed;load(g);return g;
  }
  function penalty(g,reason=1) {g.res-=250;g.miss=24;g.missReason=reason;g.feedback=90;g.cue=7;}
  function stationAtNose(g) {return g.events.findIndex(e=>e.type===TYPE.STATION&&!e.done&&Math.abs(e.x-MAIL_X)<=WINDOW);}
  function tapReason(g,index) {
    if(!g.remaining)return 4;
    if(index<0)return 1;
    const e=g.events[index];
    if(Math.abs(g.y-(e.lane?LOWER:UPPER))>20)return 2;
    return e.color===g.mail[0]?0:3;
  }
  function canDeliver(g) {return tapReason(g,stationAtNose(g))===0;}
  function route(g) {
    const station=g.events.filter(e=>e.type===TYPE.STATION&&!e.done&&e.x>=MAIL_X-WINDOW).sort((a,b)=>a.x-b.x)[0];
    if(!station)return {lane:-1,canChoose:0,choiceMatches:0,atLane:0};
    return {lane:station.lane,canChoose:+g.events.some(e=>e.type===TYPE.FORK&&!e.done&&e.x>X+3600&&e.x<station.x),
      choiceMatches:+(g.choice===station.lane),atLane:+(Math.abs(g.y-(station.lane?LOWER:UPPER))<=20)};
  }
  function controls(g,i,hornAllowed=true) {
    if(i.ok_down){g.hold=1;g.presses=Math.min(0xffffffff,g.presses+1);g.tapTarget=stationAtNose(g);g.tapReason=tapReason(g,g.tapTarget);}
    else if(i.ok_held&&g.hold)g.hold=Math.min(65535,g.hold+1);
    const tap=!!(i.ok_up&&g.hold>0&&g.hold<HOLD);
    g.whistle=+(!!i.ok_held&&g.hold>=HOLD&&hornAllowed);
    if(g.whistle&&(g.hold-HOLD)%24===0)g.cue=10;
    if(g.hold>=HOLD)g.tapTarget=-1;
    if(!i.ok_held){g.hold=0;if(!i.ok_up)g.tapTarget=-1;}
    return tap;
  }
  function unload(g) {
    const e=g.events[g.tapTarget];g.taps=Math.min(0xffffffff,g.taps+1);
    if(e&&!e.done&&g.tapReason===0) {
      g.score=Math.min(0xffffffff,g.score+1);g.delivered=60;g.cue=6;e.done=1;
      g.feedback=0;
      g.mail.shift();g.mail.push(0);g.remaining--;
      if(!g.remaining&&!g.refill){g.refill=1;spawn(g,TYPE.DEPOT,WIDTH+80,g.lane,0);}
    } else {penalty(g,g.tapReason||1);if(e)e.done=1;}
    g.tapTarget=-1;
  }
  function startPractice(seed) {
    const g=start(seed);g.practice=1;g.speed=60;g.remaining=1;g.refill=1;g.mail.fill(0);
    spawn(g,TYPE.FORK,210,0,0);spawn(g,TYPE.STATION,330,0,0);return g;
  }
  function practiceStep(g,i) {
    const tap=controls(g,i,g.lesson>=3&&g.lesson<=4);
    const fork=g.events[0],station=g.events[1],animal=g.events[2];
    if(g.lesson===0&&i.up_down){g.choice=0;g.lesson=1;g.cue=1;}
    if(g.lesson===1) {
      g.distance=(g.distance+g.speed)>>>0;fork.x-=g.speed;station.x-=g.speed;
      if(!fork.done&&fork.x<=X+3600){fork.done=1;g.lane=0;g.transition=120;}
      if(g.transition){g.y+=Math.trunc((UPPER-g.y)/g.transition);g.transition--;}
      if(station.x<=MAIL_X&&!g.transition){station.x=MAIL_X;g.y=UPPER;g.lesson=2;g.cue=2;}
    } else if(g.lesson===2&&tap) {
      unload(g);g.lesson=3;spawn(g,TYPE.ANIMAL,160,0,0);
    } else if(g.lesson===3) {
      if(g.whistle)animal.horn++;else animal.horn=0;
      if(animal.horn>=36){animal.done=2;g.lesson=4;g.cue=1;}
    } else if(g.lesson===4&&!i.ok_held){g.lesson=5;g.whistle=0;animal.done=1;}
    else if(g.lesson===5&&tap){g.over=1;g.whistle=0;g.cue=2;}
  }
  function step(g,input) {
    const i=input||{};g.cue=0;g.tick=(g.tick+1)>>>0;
    for(const k of ['hit','miss','delivered','feedback'])if(g[k])g[k]--;
    if(g.over)return;
    if(g.practice){practiceStep(g,i);return;}
    if(i.up_down)g.choice=0;
    if(i.down_down)g.choice=1;
    const tap=controls(g,i);
    g.drainAcc+=g.config.drain+(g.whistle?g.config.hornDrain:0);
    while(g.drainAcc>=60){g.res--;g.drainAcc-=60;}
    g.distance=(g.distance+g.speed)>>>0;
    if(--g.nextFork<=0) {
      spawn(g,TYPE.FORK,WIDTH+40,0,0);
      if(random(g)%100<60&&g.remaining)spawn(g,TYPE.STATION,WIDTH+140,random(g)%2,255);
      g.nextFork=range(g,g.config.forkMin,g.config.forkMax);
    }
    if(--g.nextCoal<=0){spawn(g,TYPE.COAL,WIDTH+40,random(g)%2,0);g.nextCoal=range(g,360,540);}
    if(g.lap>=3&&--g.nextAnimal<=0){spawn(g,TYPE.ANIMAL,Math.max(WIDTH+40,110+g.speed*2),random(g)%2,random(g)%2);g.nextAnimal=range(g,360,600);}
    for(const e of g.events)if(e.type) {
      e.x-=g.speed;
      if(e.type===TYPE.FORK&&!e.done&&e.x<=X+60*60){e.done=1;if(g.lane!==g.choice){g.lane=g.choice;g.transition=Math.ceil(7200/g.speed);}}
      if(e.type===TYPE.STATION&&e.color===255&&e.x<=WIDTH*60) {
        if(g.remaining)e.color=g.mail[0];else e.done=1;
      }
    }
    if(tap)unload(g);
    for(let at=0;at<g.events.length;at++){const e=g.events[at];if(!e.type||e.done)continue;
      if(e.type===TYPE.STATION&&e.x<MAIL_X-WINDOW&&!(g.tapTarget===at&&g.hold>0&&g.hold<HOLD)){
        e.done=1;if(g.remaining)penalty(g,5);
      }
      if(e.type===TYPE.ANIMAL) {
        const same=Math.abs(g.y-(e.lane?LOWER:UPPER))<=20;
        if(g.whistle&&same&&e.x>X&&e.x<X+g.speed*90)e.horn++;else e.horn=0;
        if(e.horn>=36){e.done=2;g.cue=1;}
        else if(e.x<=X){e.done=1;if(same){penalty(g,6);g.hit=24;}}
      }
      if(e.type===TYPE.COAL&&e.x<=X){e.done=1;if(Math.abs(g.y-(e.lane?LOWER:UPPER))<=20){g.res=Math.min(1000,g.res+300);g.cue=6;}}
      if(e.type===TYPE.DEPOT&&e.x<=X){e.done=1;g.lap++;g.speed=Math.min(200,Math.floor((g.speed*108+50)/100));load(g);g.cue=2;}
    }
    for(const e of g.events)if(e.type&&e.x<-100*60)Object.assign(e,{type:0,x:0,lane:0,color:0,done:0,horn:0});
    if(g.transition){g.y+=Math.trunc(((g.lane?LOWER:UPPER)-g.y)/g.transition);g.transition--;}
    else g.y=g.lane?LOWER:UPPER;
    if(g.res<=0){g.res=0;g.over=1;g.whistle=0;g.cue=8;}
  }
  const FIELDS=['tick','score','res','over','lane','choice','y','transition','speed','drainAcc','hold','whistle','lap',
    'remaining','refill','nextFork','nextCoal','nextAnimal','hit','miss','delivered','cue','spawnBlocked','distance','rng','practice','lesson','tapTarget','tapReason','missReason','feedback','presses','taps'];
  function view(g){const r=route(g);return [...FIELDS.map(k=>g[k]),...g.mail,...g.events.flatMap(e=>[e.type,e.x,e.lane,e.color,e.done,e.horn]),r.lane,r.canChoose,r.choiceMatches,r.atLane];}
  function status(g){return {score:g.practice?0:g.score,res:g.res,over:g.over};}
  const api={TYPE,X,MAIL_X,WINDOW,HOLD,CAP,WIDTH,HEIGHT,UPPER,LOWER,DEFAULT,FIELDS,random,start,startPractice,step,view,status,canDeliver,route};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.AdvPost=api;
})(this);
