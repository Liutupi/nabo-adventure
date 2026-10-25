// Native POST art in a true 320x240 playfield. No sprite scaling or mirroring.
(function(root){
  'use strict';
  const images=new Map(),animations=new Map(),colors=['#c95d50','#407d9e','#d7ac49','#54865b'];
  async function load(){
    const m=await(await fetch('../art/post-manifest.json')).json(),paths=new Set(m.assets.map(a=>a.path));
    for(const a of m.animations){animations.set(a.skin+'/'+a.name,a);for(const p of a.runtime_frames)paths.add(p);}
    await Promise.all([...paths].map(async p=>{const im=new Image();im.src='../art/'+p;await im.decode();images.set(p,im);}));
    for(const a of m.assets)images.set(a.id,images.get(a.path));
  }
  function draw(c,g){
    const P=root.AdvPost;c.imageSmoothingEnabled=false;c.textBaseline='top';c.textAlign='left';
    const im=(id,x,y)=>{const a=images.get(id);if(a)c.drawImage(a,Math.round(x),Math.round(y));};
    const anim=(id,frame,x,y)=>{const a=animations.get(id);if(a)im(a.runtime_frames[Math.max(0,Math.min(frame,a.runtime_frames.length-1))],x-a.runtime_anchor[0],y-a.runtime_anchor[1]);};
    const text=(s,x,y,size=12,color='#fffaf0',align='left')=>{c.fillStyle=color;c.font='bold '+size+'px sans-serif';c.textAlign=align;c.fillText(s,x,y);c.textAlign='left';};
    c.fillStyle='#b2d4d1';c.fillRect(0,0,320,64);c.fillStyle='#94ca6a';c.fillRect(0,64,320,176);
    for(let x=0;x<320;x+=96)im('post/tiles/far-mountains',x,40);
    const scroll=Math.floor(g.distance/60)%32;
    for(const y of [P.UPPER,P.LOWER])for(let tile=-1;tile<=10;tile++)im('post/tiles/track-straight',tile*32-scroll,y-32);
    for(const e of g.events)if(e.type){
      const x=Math.floor(e.x/60),y=e.lane?P.LOWER:P.UPPER;
      if(e.type===1){
        c.fillStyle='#203849';for(let j=0;j<6;j++)for(let d=0;d<2;d++)c.fillRect(x-60+j*20,(d?P.LOWER-10:P.UPPER-10)+(d?-1:1)*j*14,23,5);
        im('post/tiles/track-fork',x-32,156);
      }
      if(e.type===2&&e.color<4){
        c.fillStyle=colors[e.color];c.fillRect(x-26,y-63,52,28);c.fillRect(x-30,y-16,60,6);
        c.strokeStyle='#203849';c.lineWidth=2;c.strokeRect(x-26,y-63,52,28);
        im('post/props/envelope-'+['red','blue','yellow','green'][e.color],x-16,y-61);
      }
      if(e.type===3&&!e.done)im('post/props/coal-pile',x-16,y-23);
      if(e.type===4&&e.done!==1)im('post/props/'+(e.color?'cow':'sheep'),x-(e.color?24:20),y-(e.color?34:28)-(e.done===2?30:0));
      if(e.type===5){c.fillStyle='#203849';c.fillRect(x-34,y-72,68,63);text('车库',x,y-60,16,'#fffaf0','center');}
    }
    for(let k=0;k<g.remaining;k++){const x=30-k*64;im('post/props/carriage',x-32,g.y-44);im('post/props/envelope-'+['red','blue','yellow','green'][g.mail[k]],x-16,g.y-65);}
    const left=62,top=g.y-81;let action='idle',frame=Math.floor(g.tick/5)%6;
    if(g.hit||g.miss){action='hit';frame=Math.floor((24-Math.max(g.hit,g.miss))/5);}
    else if(g.whistle){action='whistle';frame=Math.floor((g.hold-P.HOLD)/5)%6;}
    else if(g.delivered){action=g.delivered>30?'throw':'delivered';frame=Math.floor(((g.delivered>30?60:30)-g.delivered)/5);}
    anim('post_props/wheel-cycle',Math.floor(g.tick/5)%4,110,g.y);im('post/props/locomotive-body',left,top);
    anim('post_props/whistle-cord',action==='whistle'?frame:0,110,g.y);anim('post_a/'+action,frame,left+25,top+49);im('post/props/cab-foreground',left,top);
    if(P.canDeliver(g)){c.strokeStyle='#fffaf0';c.lineWidth=2;c.strokeRect(128,g.y-68,56,34);}
    c.fillStyle='#203849';c.fillRect(0,0,320,32);c.fillRect(0,220,320,20);
    text(g.practice?'练习':'蒸汽',8,9);c.strokeStyle='#fffaf0';c.lineWidth=1;c.strokeRect(36,10,66,10);
    c.fillStyle=g.res<250?'#c95d50':'#66948c';c.fillRect(38,12,Math.floor(g.res*62/1000),6);text(g.remaining?'先送':g.practice?'已送':'补给',106,9);
    g.mail.slice(0,g.remaining).forEach((color,k)=>im('post/props/envelope-'+['red','blue','yellow','green'][color],134+k*34,4));
    if(g.remaining){c.strokeStyle='#d7ac49';c.lineWidth=2;c.strokeRect(132,2,36,28);}
    c.fillStyle='#203849';c.fillRect(0,32,78,58);
    text(g.transition?'正在换轨':'当前 '+(g.lane?'下轨':'上轨'),8,36);
    text('预选 '+(g.choice?'下轨':'上轨'),8,54);
    text(g.practice?(g.lesson<2?'练习 1/3':g.lesson<3?'练习 2/3':'练习 3/3'):'送达 '+(g.score>9999?'9999+':g.score+'封'),8,74);
    c.fillStyle='#203849';c.fillRect(176,34,140,54);
    const r=P.route(g);let title,actionHint;
    if(g.practice){
      [title,actionHint]=[['第一步 选上轨','按上键选择上轨'],['正在切换到上轨','等到红站再送信'],['第二步 送红信','现在轻点一下OK'],['第三步 鸣笛','按住OK让羊离开'],['鸣笛成功','先松开OK'],['你学会了','点OK继续']][g.lesson];
    }else if(r.lane<0){title=g.remaining?'前方暂无车站':'信已送完';actionHint=g.remaining?'看到站牌再选轨':'自动回库补信';}
    else{title='下一站 '+(r.lane?'下轨 ↓':'上轨 ↑');actionHint=r.canChoose?(r.choiceMatches?'已选好，保持轨道':r.lane?'按下键选下轨':'按上键选上轨'):r.atLane?'保持轨道，等送信':g.lane===r.lane?'正在切换轨道':'已过岔口，来不及了';}
    text(title,246,38,16,'#fffaf0','center');text(actionHint,246,63,12,!g.practice&&r.canChoose&&!r.choiceMatches?'#f3c15a':'#fffaf0','center');
    const reasons=['','未到送信位置','这站在另一轨','信封颜色不同','没有待送的信','错过站台 蒸汽-250','撞到牲畜 蒸汽-250'];
    const animal=g.events.some(e=>e.type===4&&!e.done&&e.lane===g.lane&&e.x>P.X&&e.x<P.X+g.speed*90);
    const pending=g.hold>0&&g.hold<P.HOLD&&g.tapTarget>=0&&!g.tapReason;
    const hint=g.practice?'练习不耗汽 · 长按上暂停':g.feedback?reasons[g.missReason]:g.delivered?'送达 +1':pending?'松开OK，送出这封信':P.canDeliver(g)?'现在点OK，送出同色信':g.whistle?'鸣笛中，松开停止':animal?'前方牲畜，按住OK鸣笛':'OK送信/鸣笛 · 下键下轨 · 上键上轨';
    text(hint,160,224,12,'#fffaf0','center');
  }
  function session(c,m,A){
    const s=m.session;c.textAlign='center';c.textBaseline='top';
    const text=(v,x,y,size=16,color='#203849')=>{c.fillStyle=color;c.font='bold '+size+'px sans-serif';c.textAlign='center';c.fillText(v,x,y);};
    if(s.phase===A.PHASE.TITLE){
      c.fillStyle='#fffaf0';c.fillRect(0,0,320,240);c.fillStyle='#203849';c.fillRect(0,0,320,30);c.fillRect(0,220,320,20);
      text('铁路平原 · 顺时针横拿，按键朝下',160,8,12,'#fffaf0');text('小火车送信',160,40,26);text('POST',160,76,16,'#c95d50');
      text('先看第一封信的颜色',88,108,12);text('同色站前点OK送信',88,127,12);text('蒸汽空了结束，煤补汽',88,146,12);
      c.fillStyle='#203849';c.fillRect(184,108,120,42);text('下键 分步练习',244,120,16,'#fffaf0');
      text('上下键选轨',244,158,12);text('按住OK鸣笛',244,176,12);text('门槛 5 / 12 / 25',90,201,12);text('最佳 '+m.best[3],252,201,16);
      text('OK直接开始 · 下键练习 · 长按上返回',160,224,12,'#fffaf0');return;
    }
    draw(c,s.game);
    if(s.phase===A.PHASE.READY)text(String(Math.ceil(s.t/60)),160,106,36);
    if(s.phase===A.PHASE.END){c.fillStyle='#203849';c.fillRect(80,99,160,44);text('蒸汽耗尽',160,110,18,'#fffaf0');}
    if(s.phase===A.PHASE.PAUSE||s.phase===A.PHASE.RESULT){
      c.fillStyle='rgba(32,56,73,.6)';c.fillRect(0,0,320,240);c.fillStyle='#fffaf0';c.fillRect(48,36,224,172);
      if(s.phase===A.PHASE.PAUSE){text('暂停',160,60,18);text('OK继续',160,99);text('下键重新开始',160,132);text('长按上回地图',160,165);}
      else{text('本局送达',160,47);text(s.game.score,160,82,36);text('最佳 '+m.best[3],160,147);text('OK重玩 · 下键练习 · 长按上返回',160,183,12);}
    }
  }
  root.AdvPostDraw={load,draw,session};
})(this);
