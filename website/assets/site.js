// Static documentation interactions. No application session or external service is used.
const base = document.body.dataset.base || '';
const sceneButtons = [...document.querySelectorAll('[data-scene]')];
function showScene(name) {
  sceneButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.scene === name)));
  document.querySelectorAll('[data-scene-panel]').forEach(panel => { panel.hidden = panel.dataset.scenePanel !== name; });
}
sceneButtons.forEach(button => button.addEventListener('click', () => showScene(button.dataset.scene)));
if (sceneButtons.length) showScene('welcome');

document.querySelectorAll('.copy-command').forEach(button => button.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText('python -m sprintdeck'); button.textContent = 'Copied'; }
  catch { button.textContent = 'Select text'; }
}));
const sideNavigation = document.querySelector('.docs-sidebar details');
if (sideNavigation && matchMedia('(max-width: 850px)').matches) sideNavigation.open = false;

const dialog = document.querySelector('#search-dialog');
if (dialog) {
  const input = document.querySelector('#search-input');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  let indexPromise;
  function loadIndex() {
    indexPromise = indexPromise || fetch(`${base}/assets/search-index.json`).then(response => {
      if (!response.ok) throw new Error('Search index unavailable'); return response.json();
    }).catch(error => { indexPromise = null; throw error; });
    return indexPromise;
  }
  function openSearch() { dialog.showModal(); input.focus(); loadIndex().catch(() => { status.textContent = 'Search could not load. Use the documentation navigation.'; }); }
  document.querySelector('.search-trigger').addEventListener('click', openSearch);
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !event.target.closest('input, textarea, select, [contenteditable]')) { event.preventDefault(); if (!dialog.open) openSearch(); }
  });
  input.addEventListener('input', async () => {
    const query = input.value.trim().toLowerCase();
    results.replaceChildren();
    if (!query) { status.textContent = 'Type to search.'; return; }
    status.textContent = 'Searching...';
    try {
      const index = await loadIndex();
      if (input.value.trim().toLowerCase() !== query) return;
      const words = query.split(/\s+/).filter(Boolean);
      const matches = index.map(item => ({...item, score: words.reduce((score, word) => score + (item.title.toLowerCase().includes(word) ? 5 : 0) + (item.text.toLowerCase().includes(word) ? 1 : 0), 0)}))
        .filter(item => words.every(word => `${item.title} ${item.text}`.toLowerCase().includes(word))).sort((a, b) => b.score - a.score).slice(0, 10);
      for (const item of matches) {
        const link = document.createElement('a'); link.href = item.url;
        const title = document.createElement('strong'); title.textContent = item.title;
        const excerpt = document.createElement('small');
        const position = Math.max(0, item.text.toLowerCase().indexOf(words[0]) - 65);
        excerpt.textContent = item.text.slice(position, position + 210).replace(/\s+/g, ' ') + '...';
        link.append(title, excerpt); results.append(link);
      }
      status.textContent = matches.length ? `${matches.length} matching pages` : 'No matches. Try another word or use the navigation.';
    } catch { status.textContent = 'Search could not load. Use the documentation navigation.'; }
  });
}
