(function initDouyinFavorites(globalScope) {
  function isDouyinFavoritesUrl(rawUrl) {
    try {
      const url = new URL(rawUrl);
      const hostname = url.hostname.toLowerCase();
      if (hostname !== 'douyin.com' && !hostname.endsWith('.douyin.com')) return false;
      if (!url.pathname.startsWith('/user/')) return false;

      const tab = (url.searchParams.get('showTab') || '').toLowerCase();
      return ['favorite_collection', 'favorite', 'collection', 'like'].includes(tab);
    } catch {
      return false;
    }
  }

  // This function is serialized by chrome.scripting.executeScript, so it must be self-contained.
  async function collectDouyinFavorites(maxScrolls, maxNoNew, delayMs, runtime) {
    const pageDocument = runtime && runtime.document ? runtime.document : document;
    const pageWindow = runtime && runtime.window ? runtime.window : window;
    const sleep = runtime && runtime.sleep
      ? runtime.sleep
      : milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

    const scrollLimit = Math.max(0, Math.min(50, Number(maxScrolls) || 0));
    const noNewLimit = Math.max(1, Math.min(10, Number(maxNoNew) || 1));
    const waitMilliseconds = Math.max(0, Math.min(5000, Number(delayMs) || 0));
    const collected = new Set();

    function normalizeVideoUrl(rawHref) {
      if (!rawHref || typeof rawHref !== 'string') return null;
      try {
        const url = new URL(rawHref, 'https://www.douyin.com');
        const hostname = url.hostname.toLowerCase();
        const isDouyin = hostname === 'douyin.com' || hostname.endsWith('.douyin.com');
        if (url.protocol !== 'https:' || !isDouyin) return null;

        const match = url.pathname.match(/\/video\/(\d+)(?:\/|$)/);
        if (!match) return null;
        return `https://www.douyin.com/video/${match[1]}`;
      } catch {
        return null;
      }
    }

    function collectVisibleLinks() {
      let added = 0;
      pageDocument.querySelectorAll('a[href]').forEach(anchor => {
        const normalized = normalizeVideoUrl(anchor.getAttribute('href'));
        if (normalized && !collected.has(normalized)) {
          collected.add(normalized);
          added += 1;
        }
      });
      return added;
    }

    collectVisibleLinks();

    const startingScrollY = Number(pageWindow.scrollY) || 0;
    let scrolls = 0;
    let noNewRounds = 0;
    let stoppedBy = 'max-scrolls';

    try {
      for (let round = 0; round < scrollLimit; round += 1) {
        const scrollHeight = Math.max(
          Number(pageDocument.body && pageDocument.body.scrollHeight) || 0,
          Number(pageDocument.documentElement && pageDocument.documentElement.scrollHeight) || 0,
        );
        pageWindow.scrollTo(0, scrollHeight);
        await sleep(waitMilliseconds);
        scrolls += 1;

        if (collectVisibleLinks() === 0) {
          noNewRounds += 1;
          if (noNewRounds >= noNewLimit) {
            stoppedBy = 'no-new-links';
            break;
          }
        } else {
          noNewRounds = 0;
        }
      }
    } finally {
      pageWindow.scrollTo(0, startingScrollY);
    }

    const links = Array.from(collected);
    return { links, total: links.length, scrolls, stoppedBy };
  }

  function buildDouyinQueueMessage(links) {
    return {
      type: 'API_REQUEST',
      path: '/automation/queue',
      method: 'POST',
      body: {
        module_id: 'douyin-summary',
        inputs: Array.from(links),
      },
    };
  }

  const api = {
    isDouyinFavoritesUrl,
    collectDouyinFavorites,
    buildDouyinQueueMessage,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  globalScope.DouyinFavorites = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
