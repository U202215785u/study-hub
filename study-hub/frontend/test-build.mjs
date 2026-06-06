import { build } from 'vite';
console.log('1. vite imported');
try {
  console.log('2. calling build...');
  await build({ configFile: './vite.config.js', logLevel: 'info' });
  console.log('3. build done');
} catch(e) {
  console.error('4. build error:', e);
  console.error('stack:', e.stack);
}
console.log('5. script end');
