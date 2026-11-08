// DOM construction uses text nodes for all session content.
export function el(tag, className = '', text = '') {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== '') node.textContent = String(text);
  return node;
}

export function append(parent, ...nodes) {
  parent.append(...nodes.filter(Boolean));
  return parent;
}

export function panel(title, className = '') {
  return append(el('section', `panel ${className}`), el('h3', '', title));
}

export function badge(text, tone = '') { return el('span', `badge ${tone}`, text); }

export function checkView(items) {
  const list = el('ul', 'check-view');
  for (const item of items) append(list, append(el('li', item.checked ? 'checked' : ''), el('span', 'check-symbol', item.checked ? '✓' : '○'), el('span', '', item.label)));
  return list;
}

let syncClock = {server: 0, received: 0};
export function synchronize(state) { syncClock = {server: state.server_time, received: performance.now()}; }
export function updateTimers(state) {
  if (!state) return;
  const now = syncClock.server + (performance.now() - syncClock.received) / 1000;
  document.querySelectorAll('[data-timer-display]').forEach(node => {
    const value = state.timers[node.dataset.timerDisplay];
    const seconds = Math.ceil(Math.max(0, value.deadline === null ? value.remaining : value.deadline - now));
    node.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
    node.classList.toggle('low', seconds > 0 && seconds <= 60);
    node.classList.toggle('expired', seconds === 0);
    const status = node.parentElement.querySelector('[data-timer-status]');
    if (status) status.textContent = seconds === 0 ? 'Time complete' : value.deadline === null ? 'Paused / ready' : 'Running';
  });
}

export function timerView(name, title) {
  const box = el('div', 'timer-view');
  const digits = el('strong', 'timer-digits', '00:00');
  digits.dataset.timerDisplay = name;
  const status = el('span', 'muted'); status.dataset.timerStatus = name;
  return append(box, el('small', 'eyebrow', title), digits, status);
}

export async function request(path, options = {}) {
  const response = await fetch(path, {cache: 'no-store', ...options});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || `Request failed (${response.status})`);
  return value;
}

export function poll(onState, onError) {
  let stopped = false;
  async function tick() {
    try { const state = await request('/api/state'); synchronize(state); onState(state); }
    catch (error) { onError(error); }
    if (!stopped) setTimeout(tick, 400);
  }
  tick();
  return () => { stopped = true; };
}
