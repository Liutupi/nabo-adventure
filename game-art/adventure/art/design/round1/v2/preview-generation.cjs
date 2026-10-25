// Deterministic crops/resizes only. No drawing, retouching, masking or background removal.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const sharp = require('C:/Users/pc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root = __dirname;
const out = path.join(root, 'previews');
const specs = [
  {id:'01-hiker', label:'1  HIKER', file:'01-hiker-design-board.png', bbox:{left:214,top:20,width:361,height:815}, front:'first figure'},
  {id:'02-explorer', label:'2  EXPLORER', file:'02-explorer.png', bbox:{left:555,top:23,width:420,height:949}, front:'center figure'},
  {id:'03-post-traveler', label:'3  POST TRAVELER', file:'03-post-traveler.png', bbox:{left:48,top:31,width:425,height:933}, front:'first figure'},
];
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
async function caption(text, size=22) {
  return sharp({text:{text,font:`Arial ${size}`,rgba:true}}).png().toBuffer();
}
async function main() {
  fs.mkdirSync(out,{recursive:true});
  const records=[];
  const overviewLayers=[], comparisonLayers=[];
  for(let i=0;i<specs.length;i++) {
    const s=specs[i], src=path.join(root,s.file), raw=fs.readFileSync(src);
    const meta=await sharp(raw).metadata();
    const crop=await sharp(raw).extract(s.bbox).png().toBuffer();
    const cropName=`${s.id}-front-crop.png`;
    fs.writeFileSync(path.join(out,cropName),crop);
    if(process.argv.includes('--crop-only')) continue;
    const width=Math.round(s.bbox.width*48/s.bbox.height);
    const tiny=await sharp(crop).resize({width,height:48,kernel:'lanczos3',fit:'fill'}).png().toBuffer();
    const large=await sharp(tiny).resize({width:width*3,height:144,kernel:'nearest',fit:'fill'}).png().toBuffer();
    const tinyPixels=await sharp(tiny).removeAlpha().raw().toBuffer();
    const largePixels=await sharp(large).removeAlpha().raw().toBuffer();
    for(let y=0;y<144;y++) for(let x=0;x<width*3;x++) for(let c=0;c<3;c++) {
      if(largePixels[(y*width*3+x)*3+c]!==tinyPixels[(Math.floor(y/3)*width+Math.floor(x/3))*3+c])
        throw new Error(`${s.id}: nearest-neighbor pixels differ`);
    }
    const tinyName=`${s.id}-front-48px.png`, largeName=`${s.id}-front-48px-3x.png`;
    fs.writeFileSync(path.join(out,tinyName),tiny);
    fs.writeFileSync(path.join(out,largeName),large);
    const displayWidth=Math.round(s.bbox.width*600/s.bbox.height);
    const display=await sharp(crop).resize({width:displayWidth,height:600,kernel:'lanczos3',fit:'fill'}).png().toBuffer();
    const title=await caption(s.label,22), titleMeta=await sharp(title).metadata();
    const column=i*400+200;
    overviewLayers.push({input:title,left:column-Math.floor(titleMeta.width/2),top:20});
    overviewLayers.push({input:display,left:column-Math.floor(displayWidth/2),top:65});
    overviewLayers.push({input:tiny,left:column-Math.floor(width/2),top:730});
    const c=i*200+100;
    const smallTitle=await caption(s.label,14), st=await sharp(smallTitle).metadata();
    comparisonLayers.push({input:smallTitle,left:c-Math.floor(st.width/2),top:16});
    comparisonLayers.push({input:tiny,left:c-Math.floor(width/2),top:54});
    comparisonLayers.push({input:large,left:c-Math.floor(width*3/2),top:138});
    records.push({id:s.id,source:s.file,source_sha256:sha(raw),source_size:[meta.width,meta.height],selected_view:s.front,
      bbox:s.bbox,bbox_convention:'left/top inclusive; right=left+width and bottom=top+height exclusive',
      bbox_method:'Manually selected after viewing original design boards; y spans visible cap top through shoe sole, not ground shadow.',
      crop_preserves_original_pixels:true,background:'original opaque warm ivory retained; no extraction',
      target_subject_height:48,target_dimensions:[width,48],scale_y:48/s.bbox.height,scale_x:width/s.bbox.width,
      aspect_rounding:'target width rounded to nearest integer; exact 48-pixel height',downsample_kernel:'lanczos3',
      nearest_preview_dimensions:[width*3,144],nearest_scale:3,nearest_pixels_verified_exact:true,
      outputs:[{file:`previews/${cropName}`,sha256:sha(crop)},{file:`previews/${tinyName}`,sha256:sha(tiny)},{file:`previews/${largeName}`,sha256:sha(large)}]});
  }
  if(process.argv.includes('--crop-only')) return;
  const note=await caption('Front crops above · 48 px hat-to-sole below (actual output pixels)',22), noteMeta=await sharp(note).metadata();
  overviewLayers.push({input:note,left:600-Math.floor(noteMeta.width/2),top:688});
  const footer=await caption('Original ivory backgrounds retained · option 1 selected by user; options 2 and 3 unapproved',19), fm=await sharp(footer).metadata();
  overviewLayers.push({input:footer,left:600-Math.floor(fm.width/2),top:805});
  const overview=await sharp({create:{width:1200,height:850,channels:3,background:'#ffffff'}}).composite(overviewLayers).png().toBuffer();
  fs.writeFileSync(path.join(out,'outfits-overview.png'),overview);
  const actual=await caption('48 px',12), nearest=await caption('3x NEAREST',12);
  comparisonLayers.push({input:actual,left:8,top:37},{input:nearest,left:8,top:117});
  const comparison=await sharp({create:{width:600,height:296,channels:3,background:'#ffffff'}}).composite(comparisonLayers).png().toBuffer();
  fs.writeFileSync(path.join(out,'48px-comparison.png'),comparison);
  const generation={date:'2026-10-25',operation:'deterministic crop and resize only',runtime:process.version,sharp_version:sharp.versions.sharp,
    scope:'Only round1/v2 sources read; only previews/ and preview-generation.* written.',
    original_identity_reference:'../../../reference/nabo-idle-original.png',
    original_identity_reference_sha256:'eecbd9b9ad2a928d9bcf1058e1e248a006b121ca96dc814a16a924a8c091d243',
    identity_status:'The user explicitly selected V2 option 1, light hiking. This records only that human choice; options 2 and 3 are not approved. Technical animation and source-alpha validation remain separate.',
    user_selection:{option:1,id:'01-hiker',name:'light hiking',date:'2026-10-25',authority:'explicit user selection reported by root agent',other_options_approved:false},
    withdrawn_v1:'The earlier V1 automated identity pass was false and its simplified redrawn SVG designs were rejected. It is not evidence for V2 acceptance.',
    incomplete:['transparent sprites','dual-world background preview','64-color/RLE packing','animation validation'],
    unchanged:['source PNG pixels','clothing','face','hair','cap and logos'],records,
    overview:{file:'previews/outfits-overview.png',dimensions:[1200,850],sha256:sha(overview),large_subject_height:600,small_subject_height:48},
    comparison:{file:'previews/48px-comparison.png',dimensions:[600,296],sha256:sha(comparison),rows:['48px actual pixels','exact 3x nearest-neighbor enlargement']}};
  fs.writeFileSync(path.join(root,'preview-generation.json'),JSON.stringify(generation,null,2)+'\n');
  console.log(JSON.stringify({subjects:records.map(({id,bbox,target_dimensions,scale_y})=>({id,bbox,target_dimensions,scale_y})),overview:generation.overview.file,comparison:generation.comparison.file},null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
