const test = require('node:test');
const assert = require('node:assert/strict');

let douyinFavorites = {};
try {
  douyinFavorites = require('./douyin-favorites.js');
} catch {
  // RED phase: the production module does not exist yet.
}

function requireFunction(name) {
  assert.equal(
    typeof douyinFavorites[name],
    'function',
    `douyin-favorites.js should export ${name}`,
  );
  return douyinFavorites[name];
}

function createPageRuntime(rounds, pageUrl = 'https://www.douyin.com/user/self?showTab=favorite_collection') {
  let round = 0;
  const scrollCalls = [];

  const runtime = {
    document: {
      body: { scrollHeight: 5000 },
      querySelectorAll() {
        return (rounds[Math.min(round, rounds.length - 1)] || []).map(href => ({
          getAttribute(name) {
            return name === 'href' ? href : null;
          },
        }));
      },
    },
    window: {
      location: { href: pageUrl },
      scrollY: 320,
      scrollTo(x, y) {
        scrollCalls.push([x, y]);
        if (y === 5000 && round < rounds.length - 1) round += 1;
      },
    },
    sleep: async () => {},
  };

  return { runtime, scrollCalls };
}

test('collect keeps only canonical Douyin video links and removes duplicates', async () => {
  const collect = requireFunction('collectDouyinFavorites');
  const { runtime } = createPageRuntime([[
    '/video/123456?previous_page=web_code_link',
    'https://www.douyin.com/video/123456#comment',
    'https://m.douyin.com/video/789012/',
    'https://evil.example/video/999999',
    'https://www.douyin.com/note/888888',
    'https://www.douyin.com/video/not-a-number',
  ]]);

  const result = await collect(0, 2, 0, runtime);

  assert.deepEqual(result.links, [
    'https://www.douyin.com/video/123456',
    'https://www.douyin.com/video/789012',
  ]);
  assert.equal(result.total, 2);
});

test('collect accumulates virtualized links and stops after consecutive empty rounds', async () => {
  const collect = requireFunction('collectDouyinFavorites');
  const { runtime, scrollCalls } = createPageRuntime([
    ['/video/100001'],
    ['/video/100001', '/video/100002'],
    ['/video/100002', '/video/100003'],
    ['/video/100003'],
    ['/video/100003'],
    ['/video/100004'],
  ]);

  const result = await collect(30, 2, 0, runtime);

  assert.deepEqual(result.links, [
    'https://www.douyin.com/video/100001',
    'https://www.douyin.com/video/100002',
    'https://www.douyin.com/video/100003',
  ]);
  assert.equal(result.scrolls, 4);
  assert.equal(result.stoppedBy, 'no-new-links');
  assert.deepEqual(scrollCalls.at(-1), [0, 320]);
});

test('collect never exceeds the configured scroll limit', async () => {
  const collect = requireFunction('collectDouyinFavorites');
  const { runtime } = createPageRuntime([
    ['/video/200001'],
    ['/video/200002'],
    ['/video/200003'],
    ['/video/200004'],
  ]);

  const result = await collect(2, 5, 0, runtime);

  assert.equal(result.scrolls, 2);
  assert.equal(result.stoppedBy, 'max-scrolls');
  assert.deepEqual(result.links, [
    'https://www.douyin.com/video/200001',
    'https://www.douyin.com/video/200002',
    'https://www.douyin.com/video/200003',
  ]);
});

test('favorite-page detection rejects ordinary Douyin and non-Douyin pages', () => {
  const isDouyinFavoritesUrl = requireFunction('isDouyinFavoritesUrl');

  assert.equal(isDouyinFavoritesUrl('https://www.douyin.com/user/self?showTab=favorite_collection'), true);
  assert.equal(isDouyinFavoritesUrl('https://www.douyin.com/user/abc?showTab=collection'), true);
  assert.equal(isDouyinFavoritesUrl('https://www.douyin.com/video/123456'), false);
  assert.equal(isDouyinFavoritesUrl('https://example.com/user/self?showTab=favorite_collection'), false);
});

test('favorite-page detection rejects the Douyin likes tab', () => {
  const isDouyinFavoritesUrl = requireFunction('isDouyinFavoritesUrl');

  assert.equal(isDouyinFavoritesUrl('https://www.douyin.com/user/self?showTab=like'), false);
});

test('collect rejects video-like paths that are not canonical video pages', async () => {
  const collect = requireFunction('collectDouyinFavorites');
  const { runtime } = createPageRuntime([[
    'https://www.douyin.com/foo/video/345678/bar',
  ]]);

  const result = await collect(0, 2, 0, runtime);

  assert.deepEqual(result.links, []);
});

test('queue message matches the existing backend contract', () => {
  const buildDouyinQueueMessage = requireFunction('buildDouyinQueueMessage');
  const links = [
    'https://www.douyin.com/video/300001',
    'https://www.douyin.com/video/300002',
  ];

  assert.deepEqual(buildDouyinQueueMessage(links), {
    type: 'API_REQUEST',
    path: '/automation/queue',
    method: 'POST',
    body: {
      module_id: 'douyin-summary',
      inputs: links,
    },
  });
});
