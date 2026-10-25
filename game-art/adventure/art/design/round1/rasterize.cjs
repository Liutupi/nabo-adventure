// Deterministic local SVG rasterization through the bundled sharp / librsvg.
const fs = require('fs');
const path = require('path');
const sharp = require(process.env.NABO_SHARP || 'C:/Users/pc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async () => {
  for (const file of process.argv.slice(2)) {
    await sharp(fs.readFileSync(file), { density: 288 }).resize(1024, 1024).png()
      .toFile(path.join(path.dirname(file), path.basename(file, '.svg') + '-4x.png'));
  }
})().catch(error => { console.error(error); process.exit(1); });
