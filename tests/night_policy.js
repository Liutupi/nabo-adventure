// Test-only player: observes visible state, moves one slot per completed slide,
// catches a firefly only when the same public predicate used by the HUD is true.
const N=require('../game-art/adventure/prototype/adv_night.js');
function drive(g){
  const target=N.target(g);
  if(target>=0&&g.bugs[target].type===N.TYPE.FIREFLY&&g.cooldown<=1)return {down_down:1};
  let best=null;
  for(const e of g.bugs)if(e.type===N.TYPE.FIREFLY){
    const lane=e.lane,travel=Math.ceil(Math.abs(N.POS[lane]-g.x)/N.WALK)+N.HOLD;
    if(N.LIFE-e.age<travel+2)continue;
    const cost=N.LIFE-e.age+travel*.2;
    if(!best||cost<best.cost)best={lane,cost};
  }
  return best&&Math.abs(N.POS[best.lane]-g.x)>8?(N.POS[best.lane]<g.x?{ok_held:1}:{up_held:1}):{};
}
module.exports={drive};
