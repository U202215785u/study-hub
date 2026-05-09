import { build } from 'vite';
try {
  await build();
  console.log('build done');
} catch (e) {
  console.error('build error:', e.message);
}
