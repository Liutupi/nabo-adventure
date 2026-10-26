// The existing screen-information player drives real serial buttons; no fabricated state.
const readline=require('readline'),{driver}=require('../tests/space_policy.js');
const next=driver('skilled',1);
readline.createInterface({input:process.stdin}).on('line',line=>{
 try{
  const g=JSON.parse(line);g.objs=g.objs.map(o=>({type:o[0],x:o[1],y:o[2],vx:o[3],state:o[4],done:o[5]}));
  process.stdout.write(JSON.stringify(next(g))+'\n');
 }catch(error){process.stderr.write(String(error)+'\n');process.exit(1);}
});
