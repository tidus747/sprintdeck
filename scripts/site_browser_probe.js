const result = document.querySelector('#result');
const home = document.querySelector('#home');
const docs = document.querySelector('#docs');
const mobile = document.querySelector('#mobile');
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
function assert(condition, message) { if (!condition) throw new Error(message); }
async function until(predicate, message) { for (let attempt = 0; attempt < 70; attempt++) { if (predicate()) return; await wait(100); } throw new Error(message); }
try {
  await until(() => home.contentDocument?.querySelector('.hero-preview img')?.naturalWidth === 1920, 'Hero screenshot did not load');
  const homeDocument = home.contentDocument;
  homeDocument.querySelector('[data-scene="roadmap"]').click();
  const roadmap = homeDocument.querySelector('[data-scene-panel="roadmap"]');
  roadmap.scrollIntoView();
  await until(() => !roadmap.hidden && roadmap.querySelector('img').naturalWidth === 1920, 'Scene gallery did not switch');
  assert(homeDocument.querySelector('[data-scene-panel="welcome"]').hidden, 'Inactive scene was not hidden');
  await until(() => docs.contentDocument?.querySelector('.search-trigger'), 'Documentation did not render');
  const docsDocument = docs.contentDocument;
  docsDocument.querySelector('.search-trigger').click();
  assert(docsDocument.querySelector('#search-dialog').open, 'Search dialog did not open');
  const input = docsDocument.querySelector('#search-input');
  input.value = 'timer'; input.dispatchEvent(new Event('input', {bubbles: true}));
  await until(() => docsDocument.querySelector('#search-results a'), 'Local search returned no results');
  assert([...docsDocument.querySelectorAll('#search-results a')].every(link => link.pathname.startsWith('/sprintdeck/docs/')), 'Search lost the GitHub Pages base path');
  docsDocument.querySelector('.close-search').click();
  assert(!docsDocument.querySelector('#search-dialog').open, 'Search dialog did not close');
  await until(() => mobile.contentDocument?.querySelector('.hero'), 'Mobile page did not render');
  assert(mobile.contentDocument.documentElement.scrollWidth <= mobile.contentWindow.innerWidth + 1, 'Mobile page has horizontal overflow');
  assert(homeDocument.documentElement.scrollWidth <= home.contentWindow.innerWidth + 1, 'Desktop page has horizontal overflow');
  result.textContent = 'SITE_BROWSER_PASSED';
} catch (error) { result.textContent = `SITE_BROWSER_FAILED: ${error.message}`; }
