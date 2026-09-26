// 普通 HTML 链接保留为无脚本兜底；脚本只增强连续翻页体验。
let requestNumber = 0;
let controller;
const pageCache = new Map();
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function filterModules() {
  const search = document.querySelector('#search');
  const status = document.querySelector('#status');
  if (!search || !status) return;
  const query = search.value.trim().toLocaleLowerCase();
  const cards = [...document.querySelectorAll('.module-card')];
  let count = 0;
  for (const card of cards) {
    const matches = (status.value === 'all' || card.dataset.status === status.value)
      && (card.textContent + ' ' + card.dataset.search).toLocaleLowerCase().includes(query);
    card.hidden = !matches;
    count += Number(matches);
  }
  document.querySelector('#result-count').textContent = `显示 ${count} / ${cards.length} 个模块`;
  document.querySelector('#empty').hidden = count !== 0;
}

function preparePage() {
  const filters = document.querySelector('.filters');
  if (filters) {
    filters.hidden = false;
    filterModules();
  }
}

function closeDirectory() {
  document.body.classList.remove('directory-open');
  const toggle = document.querySelector('.directory-toggle');
  toggle.setAttribute('aria-expanded', 'false');
  toggle.textContent = '打开目录';
}

async function turnPage(destination, push = true, direction = 'next') {
  const request = ++requestNumber;
  controller?.abort();
  controller = new AbortController();
  document.querySelector('.reader-sheet').setAttribute('aria-busy', 'true');
  try {
    const address = new URL(destination, location.href);
    const key = address.origin + address.pathname;
    let content = pageCache.get(key);
    if (!content) {
      const response = await fetch(key, {signal: controller.signal});
      if (!response.ok) throw new Error('Page unavailable');
      content = await response.text();
      pageCache.set(key, content);
      if (pageCache.size > 12) pageCache.delete(pageCache.keys().next().value);
    }
    if (request !== requestNumber) return;
    const parsed = new DOMParser().parseFromString(content, 'text/html');
    const nextSheet = parsed.querySelector('.reader-sheet');
    const nextDirectory = parsed.querySelector('.reader-directory');
    if (!nextSheet || !nextDirectory) throw new Error('Invalid reader page');
    const oldDirectory = document.querySelector('.reader-directory');
    const scroll = oldDirectory.scrollTop;
    const opened = new Set([...oldDirectory.querySelectorAll('details[open]')]
      .map(details => details.querySelector('summary').textContent));
    for (const details of nextDirectory.querySelectorAll('details')) {
      if (opened.has(details.querySelector('summary').textContent)) details.open = true;
    }
    if (push) history.pushState(null, '', address);
    document.title = parsed.title;
    document.querySelector('.reader-sheet').replaceWith(nextSheet);
    oldDirectory.replaceWith(nextDirectory);
    nextDirectory.scrollTop = scroll;
    closeDirectory();
    preparePage();
    nextSheet.focus({preventScroll: true});
    window.scrollTo({top: 0, behavior: 'auto'});
    if (address.hash) document.getElementById(address.hash.slice(1))?.scrollIntoView();
    if (!reducedMotion.matches) {
      const sign = direction === 'previous' ? -1 : 1;
      nextSheet.animate([
        {opacity: 0.45, transform: `perspective(1600px) rotateY(${sign * 5}deg) translateX(${sign * 12}px)`},
        {opacity: 1, transform: 'perspective(1600px) rotateY(0deg) translateX(0)'},
      ], {duration: 240, easing: 'ease-out'});
    }
    document.querySelector('#reader-announcement').textContent = `已翻到：${parsed.querySelector('h1').textContent}`;
  } catch (error) {
    if (error.name !== 'AbortError' && request === requestNumber) {
      // 网络异常时回退到浏览器原生导航，不停留在半更新状态。
      location.assign(destination);
    }
  } finally {
    if (request === requestNumber) document.querySelector('.reader-sheet')?.removeAttribute('aria-busy');
  }
}

document.addEventListener('click', event => {
  if (event.target.closest('.directory-toggle')) {
    const open = !document.body.classList.contains('directory-open');
    document.body.classList.toggle('directory-open', open);
    const toggle = document.querySelector('.directory-toggle');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? '收起目录' : '打开目录';
    return;
  }
  const anchor = event.target.closest('a[href]');
  if (!anchor || event.defaultPrevented || event.button !== 0 || event.metaKey
      || event.ctrlKey || event.shiftKey || event.altKey || anchor.target || anchor.hasAttribute('download')) return;
  const address = new URL(anchor.href);
  if (address.origin !== location.origin || !address.pathname.endsWith('.html')) return;
  if (address.pathname === location.pathname && address.hash) return;
  event.preventDefault();
  turnPage(address.href, true, anchor.dataset.turn || 'next');
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') { closeDirectory(); return; }
  if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey || event.shiftKey
      || event.target.closest('input, textarea, select, button, summary, [contenteditable], .reader-directory')) return;
  const direction = event.key === 'ArrowLeft' ? 'previous' : event.key === 'ArrowRight' ? 'next' : null;
  if (!direction) return;
  const anchor = document.querySelector(`[data-turn="${direction}"]`);
  if (anchor) { event.preventDefault(); turnPage(anchor.href, true, direction); }
});

document.addEventListener('input', event => { if (event.target.id === 'search') filterModules(); });
document.addEventListener('change', event => { if (event.target.id === 'status') filterModules(); });
window.addEventListener('popstate', () => turnPage(location.href, false));
preparePage();
