// Native NIGHT sleepwear/held-jar art; fixed camera and model-derived catch hint.
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
    const sky=c.createLinearGradient(0,32,0,290);sky.addColorStop(0,'#0b1326');sky.addColorStop(1,'#19382f');c.fillStyle=sky;c.fillRect(0,0,240,320);
    if(loaded){for(let i=0;i<4;i++)image('night/tree_shadow_0'+i,i*64-16,68);for(let i=0;i<8;i++)image('night/grass_0'+(i%4),i*32,258);}
    for(const [x,y] of [[22,54],[79,74],[191,58],[217,112],[112,116]]){c.fillStyle='#829a9d';c.fillRect(x,y,1,1);}
    if(phase==='TITLE'){
      text('萤火虫',120,44,26,'#ffe29a','center');text('N I G H T',120,82,12,'#b8cdbb','center');
      actor('seat_idle',Math.floor(visualTick/5)%8,120,174);
      text('上左挪 · 下右挪 · OK举罐',120,188,12,'#fffaf0','center');
      text('等金色光点进罐口圈再抓',120,208,12,'#ffe29a','center');
      text('萤火虫 +1  精神+60',120,232,12,'#fffaf0','center');text('飞蛾扣250 · 精神空了结束',120,252,12,'#fffaf0','center');
      text('铜15 · 银35 · 金60',120,275,12,'#b8cdbb','center');
    }else{
      c.strokeStyle='#526b65';c.lineWidth=1;
      for(let i=0;i<3;i++){c.beginPath();c.ellipse(N.POS[i],282,18,3,0,0,Math.PI*2);c.stroke();}
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
        if(e.type===N.TYPE.FIREFLY){glow(x,y,7,.6+(e.age%24)/60);c.fillStyle='#fff7b4';c.fillRect(x-1,y-1,3,3);}
        else{const clip=clips.get('night_shared/moth');if(clip)image(clip.runtime_frames[Math.floor(e.age/5)%clip.runtime_frames.length],x-8,y-7);}
      }
      if(g.good>48){const t=(60-g.good)/12;glow(Math.round(g.caughtX+(g.x+N.JAR_DX-g.caughtX)*t),Math.round(g.caughtY+(N.JAR_Y-g.caughtY)*t),6,1-t);}
      const messages=['','没碰到，等进光圈再按','抓到了 +1 · 精神+60','这是飞蛾 · 精神-250'];
      const hint=g.feedback?messages[g.message]:candidate?(candidate.type===N.TYPE.MOTH?'飞蛾别抓！':'现在点OK举罐'):'上左 · 下右 · 等光点进圈';
      text(hint,120,174,12,candidate&&candidate.type===N.TYPE.MOTH?'#ed998b':'#ffe29a','center');
      if(phase==='READY'){text(String(Math.ceil(countdown/60)),120,104,40,'#fffaf0','center');}
      if(phase==='END'){c.fillStyle='#0b1820';c.fillRect(42,114,156,44);text('精神耗尽',120,125,18,'#fffaf0','center');}
      if(phase==='PAUSE'){
        c.fillStyle='#0b1820';c.fillRect(18,80,204,138);
        text('暂停',120,99,24,'#fffaf0','center');text('OK继续',120,141,16,'#ffe29a','center');text('下键重新开始',120,173,12,'#fffaf0','center');
      }
    }
    if(phase==='RESULT'){
      c.fillStyle='#0b1820';c.fillRect(0,32,240,260);text('本局捕获',120,50,18,'#fffaf0','center');
      text(String(g.score),120,83,38,'#ffe29a','center');actor('cheer',Math.min(7,Math.floor(phaseTick/5)),120,216);
      text('最佳 '+best,120,238,16,'#fffaf0','center');text('铜15 · 银35 · 金60',120,270,12,'#b8cdbb','center');
    }
    c.fillStyle='#172c34';c.fillRect(0,0,240,32);text('精神',8,10);c.strokeStyle='#b8cdbb';c.strokeRect(40,11,128,9);
    c.fillStyle=g.res<250?'#d06b63':'#8aac86';c.fillRect(42,13,Math.trunc(g.res*124/1000),5);text(String(g.score),232,5,20,'#ffe29a','right');
    c.fillStyle='#172c34';c.fillRect(0,292,240,28);text(phase==='TITLE'?'OK开始 · 双击上回地图':phase==='RESULT'?'OK重玩 · 双击上回地图':'双击上回地图 · 长按上暂停',120,300,12,'#fffaf0','center');
  }
  let priorPhase=-1,priorSeed=-1,phaseStarted=0;
  function session(c,m,A,ms){const s=m.session;if(s.phase!==priorPhase||s.seed!==priorSeed){priorPhase=s.phase;priorSeed=s.seed;phaseStarted=ms;}const phase=Object.keys(A.PHASE).find(k=>A.PHASE[k]===s.phase);draw(c,s.game||A.Night.start(0),phase,s.t,Math.floor(ms*60/1000),Math.floor((ms-phaseStarted)*60/1000),m.best[4]);}
  root.AdvNightDraw={load,draw,session};
})(this);
