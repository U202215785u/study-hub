import fs from 'fs';

fs.writeFileSync('debug-noconfig.log', 'step 1: start\n');
try {
  fs.appendFileSync('debug-noconfig.log', 'step 2: importing vite...\n');
  const vite = await import('vite');
  fs.appendFileSync('debug-noconfig.log', 'step 3: imported, resolving no config...\n');
  const config = await vite.resolveConfig({}, 'build');
  fs.appendFileSync('debug-noconfig.log', 'step 4: config resolved OK\n');
} catch(e) {
  fs.appendFileSync('debug-noconfig.log', 'ERROR: ' + e.message + '\n');
  fs.appendFileSync('debug-noconfig.log', e.stack + '\n');
}
fs.appendFileSync('debug-noconfig.log', 'step 5: end\n');
