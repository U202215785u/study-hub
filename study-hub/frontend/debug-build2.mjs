import fs from 'fs';

fs.writeFileSync('debug-build2.log', 'step 1: start\n');

try {
  fs.appendFileSync('debug-build2.log', 'step 2: importing vite...\n');
  const vite = await import('vite');
  fs.appendFileSync('debug-build2.log', 'step 3: vite imported, calling build...\n');
  await vite.build({ configFile: './vite.config.js', logLevel: 'info' });
  fs.appendFileSync('debug-build2.log', 'step 4: build done\n');
} catch(e) {
  fs.appendFileSync('debug-build2.log', 'ERROR: ' + e.message + '\n');
  fs.appendFileSync('debug-build2.log', e.stack + '\n');
}

fs.appendFileSync('debug-build2.log', 'step 5: end\n');
