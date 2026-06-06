import { build } from 'vite';
import fs from 'fs';

fs.writeFileSync('debug-build.log', 'start\n');

try {
  fs.appendFileSync('debug-build.log', 'calling build...\n');
  await build({ configFile: './vite.config.js', logLevel: 'info' });
  fs.appendFileSync('debug-build.log', 'build done\n');
} catch(e) {
  fs.appendFileSync('debug-build.log', 'ERROR: ' + e.message + '\n');
  fs.appendFileSync('debug-build.log', e.stack + '\n');
}

fs.appendFileSync('debug-build.log', 'end\n');
