// CLIMB browser drawing, 240x320 portrait with native runtime art. Layout matches adv_ui_climb.c.
(function(root){
  'use strict';
  const images=new Map(),clips=new Map();let loaded=false;
  const HAND_Y=230,WALL=32,HOLD_X=[33,207],ROOT_X=[56,184];
  const SWITCH_HAND=[[7,5,38,50,52,51],[51,52,50,38,5,7]];
  async function load(){
    const manifest=await(await fetch('../art/climb-manifest.json')).json(),paths=new Set(manifest.assets.map(a=>a.path));
    for(const clip of manifest.animations){clips.set(clip.skin+'/'+clip.name,clip);for(const p of clip.runtime_frames)paths.add(p);}
    await Promise.all([...paths].map(async p=>{const image=new Image();image.src='../art/'+p;await image.decode();images.set(p,image);}));
    for(const a of manifest.assets)images.set(a.id,images.get(a.path));loaded=true;
  }
  const zone=row=>row<100?0:row<200?1:2;
  function draw(c,g,phase='PLAY',countdown=0,visualTick=g.tick,phaseTick=0,best=0){
    const C=root.AdvClimb;c.imageSmoothingEnabled=false;c.textBaseline='top';
    const text=(s,x,y,size=12,color='#fffaf0',align='left')=>{c.fillStyle=color;c.font='bold '+size+'px sans-serif';c.textAlign=align;c.fillText(s,x,y);c.textAlign='left';};
    const image=(id,x,y)=>{const im=images.get(id);if(im)c.drawImage(im,Math.round(x),Math.round(y));};
    const actor=(name,frame,x,y)=>{const clip=clips.get('climb_a/'+name);if(!clip)return;const i=Math.max(0,Math.min(frame,clip.runtime_frames.length-1));image(clip.runtime_frames[i],x-clip.runtime_anchor[0],y-clip.runtime_anchor[1]);};
    const hand=C.handY(g),sy=wy=>HAND_Y-(wy-hand),z=zone(Math.trunc(hand/C.ROW));
    c.fillStyle=['#8b9aa7','#a3b4c4','#d6dde6'][z];c.fillRect(0,0,240,320);
    const top=hand+HAND_Y,firstTile=Math.floor((top)/32);
    for(let t=firstTile;t>firstTile-12;t--){const y=sy(t*32+32),kind=['grey','cold','snow'][zone(Math.trunc(t*32/C.ROW))];
      for(const [side,x] of [[0,0],[1,208]])image('climb/tiles/'+kind+'-'+((t*7+side)&1),x,y);}
    const lo=Math.trunc((hand-90)/C.ROW)-1,hi=Math.trunc((hand+HAND_Y)/C.ROW)+1;
    for(let r=Math.max(0,lo);r<=hi;r++)for(const s of [0,1]){
      const t=C.hold(g,r,s);if(!t)continue;image('climb/props/'+['','hold-normal','hold-fragile','hold-ice'][t],HOLD_X[s]-12,sy(r*C.ROW)-9);
      if(C.canteen(g,r,s))image('climb/props/canteen',(s?222:18)-8,sy(r*C.ROW)+4-24);
    }
    // NABO
    const done=g.actLen-g.actT,side=g.act===C.ACT.IDLE?g.side:g.fromSide;let name='grip_idle_'+(side?'right':'left'),frame=Math.floor(visualTick/5)%6,rx=ROOT_X[side];
    if(phase==='RESULT'){actor('settlement_cheer',Math.min(7,Math.floor(phaseTick/5)),120,250);}
    else{
      if(g.act===C.ACT.SWITCH){frame=Math.min(5,Math.floor(done*6/g.actLen));name='switch_grab_'+(side?'right':'left');const hx=HOLD_X[g.fromSide]+Math.trunc((HOLD_X[g.toSide]-HOLD_X[g.fromSide])*frame/5);rx=hx-SWITCH_HAND[g.fromSide][frame]+30;}
      else if(g.act===C.ACT.JUMP){frame=Math.min(5,Math.floor(done*6/g.actLen));name='jump_'+(side?'right':'left');}
      else if(g.act===C.ACT.SLIDE){frame=Math.min(5,Math.floor(done*6/g.actLen));name='slide_'+(side?'right':'left');}
      else if(g.press>=C.TAP){frame=Math.min(3,Math.trunc((g.press-C.TAP)*4/(C.CHARGE3-C.TAP)));name='charge_'+(side?'right':'left');}
      else if(g.cheer>0){frame=Math.min(7,Math.trunc((C.CHEER-g.cheer)/6));name='summit_cheer_'+(side?'right':'left');}
      actor(name,frame,rx,HAND_Y+41);
    }
    for(const r of g.rocks){if(!r.on)continue;const y=sy(r.y);if(y<34){c.fillStyle='#cb5145';c.fillRect(ROOT_X[r.side]-6,36,12,12);text('!',ROOT_X[r.side],36,12,'#fffaf0','center');}else image('climb/props/falling-rock',ROOT_X[r.side]-12,y-24);}
    // HUD
    c.fillStyle='#203849';c.fillRect(0,0,240,32);text('雪山',6,9);text('体力',38,9);c.strokeStyle='#5b6f7d';c.strokeRect(70.5,11.5,108,9);
    c.fillStyle=g.res<250?'#cb5145':'#8aac86';c.fillRect(72,13,Math.trunc(g.res*104/1000),6);text(g.score+'m',234,7,16,'#f4c64e','right');
    c.fillStyle='#203849';c.fillRect(0,300,240,20);
    const msgs=['','那边没有岩点 · 体力-100','被落石砸中 · 体力-250','岩点碎了！','水壶 +250','海拔 '+Math.trunc(g.score/50)*50+' m！'];
    let hint=g.feedback&&g.message?msgs[g.message]:g.press>=C.TAP?(g.press>=C.CHARGE3?'松开：同侧跳3米':'继续按住跳3米 · 松开跳2米'):
      g.act===C.ACT.IDLE&&C.hold(g,g.row,g.side)===C.HOLD.FRAGILE?'碎石要塌，快离开':g.act===C.ACT.IDLE&&C.hold(g,g.row,g.side)===C.HOLD.ICE?'结冰：体力消耗翻倍':'点OK换边 · 按住蓄力跳';
    text(hint,120,304,12,g.feedback&&(g.message===2||g.message===1||g.message===3)?'#f08c7e':'#f4c64e','center');
    if(phase==='READY'){text(String(Math.ceil(countdown/60)),120,120,40,'#f4c64e','center');}
    if(phase==='PAUSE'){c.fillStyle='#203849';c.fillRect(30,110,180,90);text('暂停',120,122,18,'#fffaf0','center');text('OK继续 · 下键重来',120,160,12,'#f4c64e','center');}
    if(phase==='TITLE'){c.fillStyle='rgba(32,56,73,.9)';c.fillRect(10,40,220,250);text('登山 CLIMB',120,50,20,'#f4c64e','center');
      ['点OK：换到对面岩点，上1米','按住OK蓄力，松开同侧跳2/3米','碎石1秒就塌 · 结冰更耗体力','躲开落石 · 水壶补体力','体力耗尽结束','铜50 / 银150 / 金300 米','最佳 '+best+' m'].forEach((s,i)=>text(s,120,90+i*24,12,'#fffaf0','center'));}
    if(phase==='RESULT'){text('本次海拔',120,60,18,'#203849','center');text(g.score+' m',120,90,36,'#203849','center');text('最佳 '+best+' m',120,140,12,'#203849','center');}
  }
  root.AdvClimbDraw={load,draw,HAND_Y,HOLD_X,ROOT_X,SWITCH_HAND};
})(this);
