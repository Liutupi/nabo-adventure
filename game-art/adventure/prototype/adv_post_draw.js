// Native art assembly for POST's playable reference. No CSS/image runtime scaling.
(function(root){
  'use strict';
  const images=new Map(),animations=new Map(),colors=['#c95d50','#407d9e','#d7ac49','#54865b'];
  async function load(){
    const m=await(await fetch('../art/post-manifest.json')).json();
    const paths=new Set(m.assets.map(a=>a.path));
    for(const a of m.animations){animations.set(a.skin+'/'+a.name,a);for(const p of a.runtime_frames)paths.add(p);}
    await Promise.all([...paths].map(async p=>{const im=new Image();im.src='../art/'+p;await im.decode();images.set(p,im);}));
    for(const a of m.assets)images.set(a.id,images.get(a.path));
  }
  function draw(c,g){
    c.imageSmoothingEnabled=false;
    const im=(id,x,y)=>{const a=images.get(id);if(a)c.drawImage(a,Math.round(x),Math.round(y));};
    const anim=(id,frame,x,y)=>{const a=animations.get(id);if(a)im(a.runtime_frames[Math.min(frame,a.runtime_frames.length-1)],x-a.runtime_anchor[0],y-a.runtime_anchor[1]);};
    c.fillStyle='#b2d4d1';c.fillRect(0,0,240,110);c.fillStyle='#94ca6a';c.fillRect(0,110,240,210);
    for(let x=0;x<240;x+=96)im('post/tiles/far-mountains',x,84);
    const scroll=Math.floor(g.distance/60)%32;
    for(const y of [184,264])for(let tile=-1;tile<=8;tile++)im('post/tiles/track-straight',tile*32-scroll,y-32);
    for(const e of g.events)if(e.type){
      const x=Math.floor(e.x/60),y=e.lane?264:184;
      if(e.type===1){
        c.fillStyle='#203849';for(let j=0;j<6;j++)for(let d=0;d<2;d++)c.fillRect(x-60+j*20,(d?254:174)+(d?-1:1)*j*14,23,5);
        im('post/tiles/track-fork',x-32,208);
      }
      if(e.type===2&&e.color<4){
        c.fillStyle=colors[e.color];c.fillRect(x-26,y-63,52,28);c.fillRect(x-30,y-16,60,6);
        c.strokeStyle='#203849';c.lineWidth=2;c.strokeRect(x-26,y-63,52,28);
        im('post/props/envelope-'+['red','blue','yellow','green'][e.color],x-16,y-61);
      }
      if(e.type===3&&!e.done)im('post/props/coal-pile',x-16,y-23);
      if(e.type===4&&e.done!==1)im('post/props/'+(e.color?'cow':'sheep'),x-(e.color?24:20),y-(e.color?34:28)-(e.done===2?30:0));
      if(e.type===5){c.fillStyle='#203849';c.fillRect(x-34,y-72,68,63);c.fillStyle='#fffaf0';c.font='bold 12px sans-serif';c.fillText('车库',x-14,y-53);}
    }
    for(let k=0;k<g.remaining;k++){
      const x=110-80-k*64;im('post/props/carriage',x-32,g.y-44);
      im('post/props/envelope-'+['red','blue','yellow','green'][g.mail[k]],x-16,g.y-65);
    }
    const left=62,top=g.y-81;
    anim('post_props/wheel-cycle',Math.floor(g.tick/5)%4,110,g.y);
    im('post/props/locomotive-body',left,top);
    let action='idle',frame=Math.floor(g.tick/5)%6;
    if(g.hit||g.miss){action='hit';frame=Math.min(5,Math.floor((24-Math.max(g.hit,g.miss))/5));}
    else if(g.whistle){action='whistle';frame=Math.floor((g.hold-12)/5)%6;}
    else if(g.delivered){action=g.delivered>30?'throw':'delivered';frame=Math.min(5,Math.floor(((g.delivered>30?60:30)-g.delivered)/5));}
    anim('post_props/whistle-cord',action==='whistle'?frame:0,110,g.y);
    anim('post_a/'+action,frame,left+25,top+49);
    im('post/props/cab-foreground',left,top);
    c.fillStyle='#203849';c.fillRect(0,0,240,34);c.fillRect(0,290,240,30);
    c.fillStyle='#fffaf0';c.font='bold 12px sans-serif';c.textBaseline='middle';c.fillText('蒸汽',8,17);
    c.strokeStyle='#fffaf0';c.strokeRect(40,12,124,10);c.fillStyle=g.res<250?'#c95d50':'#66948c';c.fillRect(42,14,Math.floor(g.res*120/1000),6);
    c.fillStyle='#fffaf0';c.font='bold 20px sans-serif';c.textAlign='right';c.fillText(g.score,232,18);c.textAlign='left';
    c.font='bold 12px sans-serif';c.fillStyle='#203849';c.fillText(g.remaining?'待送':'回库补信',8,52);
    g.mail.slice(0,g.remaining).forEach((color,k)=>im('post/props/envelope-'+['red','blue','yellow','green'][color],64+k*34,40));
    c.fillText('第'+(g.lap+1)+'趟',8,78);
    const warning=g.events.find(e=>e.type===4&&!e.done&&e.lane===g.lane&&e.x>110*60&&e.x<110*60+g.speed*90);
    const fork=g.events.find(e=>e.type===1&&!e.done&&e.x>110*60&&e.x<110*60+g.speed*90+60*60);
    const station=g.events.filter(e=>e.type===2&&!e.done&&e.x>=110*60-24*60).sort((a,b)=>a.x-b.x)[0];
    if(warning){c.fillStyle='#c95d50';c.fillText('前方牲畜 · 按住OK鸣笛',68,78);}
    else if(station)c.fillText('站台'+(station.lane?'下轨':'上轨')+' · 已选'+(g.choice?'下轨':'上轨'),68,78);
    else if(fork)c.fillText('即将岔口 · '+(g.choice?'下轨 ↓':'上轨 ↑'),68,78);
    c.fillStyle='#fffaf0';c.font='bold 12px sans-serif';c.textAlign='center';c.fillText(g.whistle?'鸣笛中':'上/下选轨 · 点OK送信 · 按住鸣笛',120,305);c.textAlign='left';
  }
  root.AdvPostDraw={load,draw};
})(this);
