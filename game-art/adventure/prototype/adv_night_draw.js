// Native art,320x240 clockwise landscape. Fireflies stay in one marked grove.
(function(root){
  'use strict';
  const images=new Map(),clips=new Map();let loaded=false;
  async function load(){
    const manifest=await(await fetch('../art/night-manifest.json')).json(),paths=new Set(manifest.assets.map(a=>a.path));
    for(const clip of manifest.animations){clips.set(clip.skin+'/'+clip.name,clip);for(const p of clip.runtime_frames)paths.add(p);}
    await Promise.all([...paths].map(async p=>{const image=new Image();image.src='../art/'+p;await image.decode();images.set(p,image);}));
    for(const a of manifest.assets)images.set(a.id,images.get(a.path));loaded=true;
  }
  function draw(c,g,phase='PLAY',countdown=0,visualTick=g.tick,phaseTick=0,best=0){
    const N=root.AdvNight;c.imageSmoothingEnabled=false;c.textBaseline='top';c.textAlign='left';
    const text=(s,x,y,size=12,color='#fffaf0',align='left')=>{c.fillStyle=color;c.font='bold '+size+'px sans-serif';c.textAlign=align;c.fillText(s,x,y);c.textAlign='left';};
    const image=(id,x,y)=>{const im=images.get(id);if(im)c.drawImage(im,Math.round(x),Math.round(y));};
    const actor=(action,frame,x,y)=>{const clip=clips.get('night_a/'+action);if(clip){const i=Math.max(0,Math.min(frame,clip.runtime_frames.length-1));image(clip.runtime_frames[i],x-clip.runtime_anchor[0],y-clip.runtime_anchor[1]);}};
    const glow=(x,y,r,alpha=1)=>{const gradient=c.createRadialGradient(x,y,0,x,y,r);gradient.addColorStop(0,'rgba(255,226,106,'+alpha+')');gradient.addColorStop(1,'rgba(255,226,106,0)');c.fillStyle=gradient;c.fillRect(x-r,y-r,2*r,2*r);};
    const sky=c.createLinearGradient(0,32,0,220);sky.addColorStop(0,'#0b1326');sky.addColorStop(1,'#19382f');c.fillStyle=sky;c.fillRect(0,0,320,240);
    for(let i=0;i<4;i++){const x=8+i*100;c.fillStyle='#0d242e';c.fillRect(x-4,60,8,145);for(const [cx,cy,r,color] of [[x,75,36,'#0e2931'],[x+14,95,28,'#102f33']]){c.fillStyle=color;c.beginPath();c.arc(cx,cy,r,0,Math.PI*2);c.fill();}if(loaded)image('night/tree_shadow_0'+i,x-16,68);}
    if(loaded)for(let i=0;i<10;i++)image('night/grass_0'+(i%4),i*32,190);
    for(const [x,y] of [[22,54],[99,74],[221,58],[297,112],[152,96]]){c.fillStyle='#829a9d';c.fillRect(x,y,1,1);}
    if(phase==='TITLE'){
      c.fillStyle='#fffaf0';c.fillRect(16,36,200,80);text('萤火虫',116,46,26,'#203849','center');text('N I G H T',116,83,12,'#cb5145','center');
      actor('seat_idle',Math.floor(visualTick/5)%8,266,116);
      text('光点只在一簇草丛停留，过时飞走',160,128,12,'#ffe29a','center');
      text('按住左/右移动 · 中键举罐',160,148,12,'#fffaf0','center');
      text('抓到 +1 / 精神+60 · 飞蛾扣250',160,168,12,'#fffaf0','center');
      text('精神耗尽结束 · 铜15 / 银35 / 金60',160,190,12,'#fffaf0','center');
    }else if(phase==='RESULT'){
      text('本局捕获',160,45,18,'#fffaf0','center');text(String(g.score),160,73,36,'#ffe29a','center');
      actor('cheer',Math.min(7,Math.floor(phaseTick/5)),160,188);text('最佳 '+best,160,199,12,'#fffaf0','center');
    }else{
      const fly=g.bugs.find(e=>e.type===N.TYPE.FIREFLY);
      for(let lane=0;lane<3;lane++){
        const x=N.POS[lane]+N.JAR_DX,active=fly&&fly.lane===lane;
        c.fillStyle='#1d4137';for(let j=-1;j<=1;j++){c.beginPath();c.arc(x+j*10,203,12,0,Math.PI*2);c.fill();}
        if(active)glow(x,206,26,.35);
      }
      let action='seat_idle',frame=Math.floor(g.tick/5)%8;
      if(g.cast){action='catch';frame=Math.floor((N.CAST-g.cast)/5);}
      else if(g.good>0&&g.good<=30){action='lift_jar';frame=Math.floor((30-g.good)/5);}
      else if(g.move){action=g.moveDir<0?'move_left':'move_right';frame=Math.floor((N.MOVE-g.move)/5);}
      else if(g.res<250&&g.tick%240<30){action='yawn';frame=Math.floor((g.tick%240)/5);}
      actor(action,frame,g.x,N.FOOT);
      const target=N.target(g),candidate=target<0?null:g.bugs[target];
      c.setLineDash([2,3]);c.strokeStyle=candidate?(candidate.type===N.TYPE.MOTH?'#ed998b':'#ffe29a'):'#53675d';
      c.beginPath();c.ellipse(g.x+N.JAR_DX,N.JAR_Y,N.RX,N.RY,0,0,Math.PI*2);c.stroke();c.setLineDash([]);
      for(const e of g.bugs)if(e.type){
        const x=Math.trunc(e.x/60),y=N.objectY(e);
        if(e.type===N.TYPE.FIREFLY){glow(x,y,7,.8);c.fillStyle='#fff7b4';c.fillRect(x-1,y-1,3,3);c.fillStyle='#ffe29a';c.fillRect(N.POS[e.lane]+N.JAR_DX-18,132,Math.ceil(36*(N.LIFE-e.age)/N.LIFE),3);}
        else{const clip=clips.get('night_shared/moth');if(clip)image(clip.runtime_frames[Math.floor(e.age/5)%clip.runtime_frames.length],x-8,y-7);}
      }
      const messages=['','没抓到，去亮起的草丛','抓到了 +1 · 精神+60','这是飞蛾 · 精神-250'];
      const hint=g.feedback?messages[g.message]:candidate?(candidate.type===N.TYPE.MOTH?'飞蛾别抓！':'现在按中键举罐'):fly?'去'+['左','中','右'][fly.lane]+'草丛，过时会飞走':'留意下一簇亮起的草丛';
      text(hint,160,40,12,candidate&&candidate.type===N.TYPE.MOTH?'#ed998b':'#ffe29a','center');
      if(phase==='READY')text(String(Math.ceil(countdown/60)),160,86,36,'#fffaf0','center');
      if(phase==='END'){c.fillStyle='#0b1820';c.fillRect(82,80,156,44);text('精神耗尽',160,91,18,'#fffaf0','center');}
      if(phase==='PAUSE'){
        c.fillStyle='#0b1820';c.fillRect(56,65,208,124);text('暂停',160,80,24,'#fffaf0','center');
        text('中键继续',160,122,16,'#ffe29a','center');text('左键重新开始',160,154,12,'#fffaf0','center');
      }
    }
    c.fillStyle='#172c34';c.fillRect(0,0,320,32);text('夜林',8,9);text('精神',48,10);c.strokeStyle='#b8cdbb';c.strokeRect(80,11,152,9);
    c.fillStyle=g.res<250?'#d06b63':'#8aac86';c.fillRect(82,13,Math.trunc(g.res*148/1000),5);text(String(g.score),312,5,20,'#ffe29a','right');
    c.fillStyle='#172c34';c.fillRect(0,220,320,20);text(phase==='TITLE'?'中键开始 · 长按中暂停 · 双击上返回':phase==='RESULT'?'中键重玩 · 双击上键回地图':'按住左右移动 · 长按中暂停 · 双击上返回',160,224,12,'#fffaf0','center');
  }
  let priorPhase=-1,priorSeed=-1,phaseStarted=0;
  function session(c,m,A,ms){const s=m.session;if(s.phase!==priorPhase||s.seed!==priorSeed){priorPhase=s.phase;priorSeed=s.seed;phaseStarted=ms;}const phase=Object.keys(A.PHASE).find(k=>A.PHASE[k]===s.phase);draw(c,s.game||A.Night.start(0),phase,s.t,Math.floor(ms*60/1000),Math.floor((ms-phaseStarted)*60/1000),m.best[4]);}
  root.AdvNightDraw={load,draw,session};
})(this);
