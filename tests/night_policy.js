// Test-only player: observes visible state, moves one slot per completed slide,
// catches a firefly only when the same public predicate used by the HUD is true.
const N=require('../game-art/adventure/prototype/adv_night.js');
function drive(g){
  const target=N.target(g);
  if(target>=0&&g.bugs[target].type===N.TYPE.FIREFLY&&g.cooldown<=1)return {ok_down:1};
  if(g.move)return {};
  let best=null;
  for(const e of g.bugs)if(e.type===N.TYPE.FIREFLY)for(let lane=0;lane<3;lane++){
    const distance=(N.POS[lane]+N.JAR_DX)*60-e.x;
    if(distance*e.dir<0)continue;
    const ticks=Math.abs(distance)/N.speed(g),travel=Math.abs(lane-g.lane)*N.MOVE;
    if(ticks<travel-8||ticks>240)continue;
    const cost=ticks+travel*.2;
    if(!best||cost<best.cost)best={lane,cost};
  }
  return best&&best.lane!==g.lane?(best.lane<g.lane?{up_down:1}:{down_down:1}):{};
}
module.exports={drive};
