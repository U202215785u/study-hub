import fs from 'fs';
import { resolveConfig } from 'vite';

fs.writeFileSync('debug-empty.log', 'step 1: start\n');
try {
  fs.appendFileSync('debug-empty.log', 'step 2: resolving empty config...\n');
  const config = await resolveConfig({ configFile: './vite-empty.config.js' }, 'build');
  fs.appendFileSync('debug-empty.log', 'step 3: config resolved OK\n');
} catch(e) {
  fs.appendFileSync('debug-empty.log', 'ERROR: ' + e.message + '\n');
  fs.appendFileSync('debug-empty.log', e.stack + '\n');
}
fs.appendFileSync('debug-empty.log', 'step 4: end\n');
