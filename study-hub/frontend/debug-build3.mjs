import fs from 'fs';

fs.writeFileSync('debug-build3.log', 'step 1: start\n');

try {
  fs.appendFileSync('debug-build3.log', 'step 2: importing vite...\n');
  const vite = await import('vite');
  fs.appendFileSync('debug-build3.log', 'step 3: vite imported\n');
  
  fs.appendFileSync('debug-build3.log', 'step 4: creating logger...\n');
  const logger = vite.createLogger('info');
  fs.appendFileSync('debug-build3.log', 'step 5: logger created\n');
  
  fs.appendFileSync('debug-build3.log', 'step 6: resolving config...\n');
  const config = await vite.resolveConfig({}, 'build');
  fs.appendFileSync('debug-build3.log', 'step 7: config resolved\n');
  
  fs.appendFileSync('debug-build3.log', 'step 8: calling build...\n');
  await vite.build({ configFile: './vite.config.js', logLevel: 'info' });
  fs.appendFileSync('debug-build3.log', 'step 9: build done\n');
} catch(e) {
  fs.appendFileSync('debug-build3.log', 'ERROR: ' + e.message + '\n');
  fs.appendFileSync('debug-build3.log', e.stack + '\n');
}

fs.appendFileSync('debug-build3.log', 'step 10: end\n');
