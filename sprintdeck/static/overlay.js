import {el, append, panel, badge, checkView, timerView, updateTimers, poll} from './common.js';
import {calendarView, timeOffView} from './calendar.js';

const root = document.querySelector('#scene');
const connection = document.querySelector('#connection');
const scene = location.pathname.split('/').pop();
root.classList.toggle('discussion-canvas', scene === 'discussion' || scene === 'roadmap');
root.classList.toggle('welcome-canvas', scene === 'welcome');
let state;

function fit() {
  const scale = Math.min(innerWidth / 1920, innerHeight / 1080);
  root.style.transform = `scale(${scale})`;
  root.style.left = `${Math.max(0, (innerWidth - 1920 * scale) / 2)}px`;
  fitCaptures();
}
addEventListener('resize', fit); fit();

function fitCaptures() {
  root.querySelectorAll('.capture-slot').forEach(slot => {
    const region = slot.querySelector('.capture-region');
    // Whole 16 x 9 units give an exact 16:9 aperture for an uncropped 1080p source.
    const unit = Math.max(0, Math.floor(Math.min((slot.clientWidth - 4) / 16, (slot.clientHeight - 4) / 9)));
    region.style.width = `${unit * 16}px`;
    region.style.height = `${unit * 9}px`;
  });
}

const localClock = new Intl.DateTimeFormat('en-GB', {
  year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  hour12: false, timeZoneName: 'short'
});
function updateLocalTime() {
  const now = new Date();
  root.querySelectorAll('[data-local-clock]').forEach(node => {
    node.dateTime = now.toISOString(); node.textContent = localClock.format(now);
  });
}

function note(title, value, className = '') {
  const box = panel(title, className);
  const text = el('p', `note-text ${value ? '' : 'muted'}`, value || 'Not entered');
  text.title = value || 'Not entered'; box.append(text); return box;
}

function capture(label = 'Planning application capture') {
  const region = el('section', 'capture-region');
  region.setAttribute('aria-label', label);
  region.dataset.sourceSize = '1920x1080';
  return append(el('div', 'capture-slot'), region);
}

function header() {
  const title = {individual: 'Individual Planning', overview: 'Overview', wrapup: 'Commitment & Wrap-up', discussion: 'Board Discussion', welcome: 'Welcome', roadmap: 'Roadmap Review'}[scene];
  const head = el('header', 'scene-header');
  const branding = append(el('div', 'brand'), brandLogo(), el('span', '', 'SprintDeck'));
  const context = append(el('div', 'scene-context'), el('p', 'eyebrow', 'SPRINT PLANNING'), el('h1', '', title));
  const sprints = append(el('div', 'sprint-identifiers'), el('small', 'muted', `CURRENT  ${state.sprint.current}`), el('strong', '', state.sprint.next), badge(state.sprint.status, 'blue'));
  append(head, branding, context, sprints, timerView('meeting', 'Meeting remaining'));
  return head;
}

function brandLogo(className = 'brand-mark') {
  const logo = el('img', className);
  logo.src = '/static/logo.svg?v=brand-1'; logo.alt = ''; logo.width = 60; logo.height = 60;
  return logo;
}

function teamList() {
  const list = el('div', 'team-list');
  for (const [index, member] of state.members.entries()) {
    append(list, append(el('div', 'team-status'), el('span', 'avatar', String(index + 1).padStart(2, '0')), el('strong', '', member.name), badge(member.status, member.status === 'Confirmed' ? 'green' : member.status === 'Reviewed' ? 'purple' : ''), el('small', 'muted', `${member.completion}%`)));
  }
  if (!state.members.length) list.append(el('p', 'muted', 'No members configured'));
  return list;
}

function collection(name, title) {
  const box = panel(title, `collection-panel ${name}`);
  const list = el('div', 'presentation-list');
  for (const item of state[name]) {
    const row = el('article', 'presentation-item');
    if (name === 'roadmap') { row.classList.add('milestone', `milestone-${item.color}`); row.dataset.milestoneColor = item.color; }
    const heading = el('div', 'item-heading');
    append(heading, el('strong', '', item.title || item.text), name === 'scope' ? badge(item.confirmed ? 'Confirmed' : 'Pending', item.confirmed ? 'green' : '') : badge(item.status, item.status === 'Resolved' || item.status === 'Confirmed' ? 'green' : name === 'risks' ? 'orange' : ''));
    const metadata = [item.date, item.owner, item.due ? `Due ${item.due}` : '', item.next_action].filter(Boolean).join(' | ');
    append(row, heading, metadata ? el('small', 'muted', metadata) : null, item.description ? el('p', 'muted', item.description) : null);
    list.append(row);
  }
  if (!state[name].length) list.append(el('p', 'muted', 'No items recorded'));
  box.append(list); return box;
}

function renderIndividual() {
  const content = el('div', 'individual-layout');
  content.append(capture());
  const sidebar = el('aside', 'individual-sidebar');
  const member = state.members.find(value => value.id === state.active_member);
  if (!member) { sidebar.append(note('Individual review', 'Add a member in the controller to begin.')); content.append(sidebar); return content; }
  const identity = panel('ACTIVE REVIEW', 'identity-panel');
  append(identity, el('h2', '', member.name), el('p', 'muted', `${member.role || 'Team member'} | ${state.members.indexOf(member) + 1} of ${state.members.length}`), badge(member.status, member.status === 'Confirmed' ? 'green' : 'blue'));
  const review = panel(`Review checklist | ${member.completion}%`, 'review-panel');
  review.append(checkView(member.checks));
  if (member.review_override) review.append(el('small', 'muted', 'Review completion overridden by facilitator'));
  const timebox = append(panel('Timebox', 'individual-timebox'), timerView('individual', 'Individual remaining'));
  const notes = el('div', 'individual-notes');
  for (const [key, title] of [['objective', 'Shared sprint objective'], ['deliverables', 'Deliverables'], ['dependencies', 'Dependencies'], ['risks', 'Risks'], ['notes', 'Shared review notes'], ['pending_decisions', 'Pending decisions']]) notes.append(note(title, state.planning[key]));
  append(sidebar, identity, review, timebox, notes); content.append(sidebar); return content;
}

function renderOverview() {
  const content = el('div', 'overview-layout');
  const top = el('div', 'overview-top');
  const context = el('div', 'overview-context');
  const current = note(`Current sprint | ${state.sprint.current}`, state.sprint.summary, 'current-sprint');
  append(current, badge(state.sprint.current_status, 'blue'), el('p', 'clamp-two muted', `Carry-over: ${state.sprint.carryover || 'None recorded'}`));
  append(context, note('Upcoming sprint goal', state.sprint.goal, 'goal-panel'), current);
  append(top, context, calendarView(state), append(panel(`Team reviews | ${state.progress}%`), teamList()));
  const bottom = el('div', 'overview-bottom');
  append(bottom, capture(), append(el('div', 'overview-summary'), timeOffView(state), collection('roadmap', 'Roadmap milestones')));
  append(content, top, bottom); return content;
}

function renderWrapup() {
  const content = el('div', 'wrapup-layout');
  const commitment = note('Sprint commitment', state.sprint.commitment, 'goal-panel');
  append(commitment, el('h3', '', 'Agreed sprint objective'), el('p', 'clamp-two', state.sprint.goal || 'No goal entered'), el('p', 'muted', `${state.sprint.start} to ${state.sprint.end}`));
  const first = el('div', 'wrapup-column');
  append(first, commitment, collection('scope', 'Committed scope'), timeOffView(state));
  const second = el('div', 'wrapup-column');
  append(second, append(panel('Team commitments'), teamList()), collection('risks', 'Risks and attention points'));
  const third = el('div', 'wrapup-column');
  const final = panel('Final ceremony review', 'final-panel');
  append(final, badge(state.ready ? 'Ready for commitment' : 'Review still required', state.ready ? 'green' : 'orange'), checkView(state.final_checks));
  append(third, collection('decisions', 'Decisions'), collection('actions', 'Next steps'), final);
  append(content, first, second, third); return content;
}

function renderWelcome() {
  const content = el('section', 'welcome-content');
  const intro = el('div', 'welcome-intro');
  append(intro, append(el('div', 'welcome-branding'), brandLogo('welcome-logo'), badge('Planning starts shortly', 'blue')), el('p', 'eyebrow', state.session.title),
    el('h2', 'welcome-sprint', state.sprint.next),
    el('p', 'welcome-goal', state.sprint.goal || 'We will align the sprint goal together.'),
    el('p', 'welcome-message', 'Settle in. We will begin shortly.'));
  const facts = el('div', 'welcome-facts');
  for (const [label, value] of [['Sprint dates', `${state.sprint.start} to ${state.sprint.end}`], ['Team', `${state.members.length} team members`], ['Planning status', state.sprint.status]]) {
    append(facts, append(el('div', 'welcome-fact'), el('p', 'eyebrow', label), el('strong', '', value)));
  }
  return append(content, intro, facts);
}

function footer() {
  const time = el('time', 'local-clock'); time.dataset.localClock = 'true'; time.setAttribute('aria-label', 'Local date and time');
  return append(el('footer', 'scene-footer'), el('span', '', 'SprintDeck / Shared planning workspace'),
    el('span', 'footer-context', 'Local presentation | Changes managed by facilitator'), time);
}

function render() {
  root.replaceChildren();
  const content = scene === 'welcome' ? renderWelcome() : scene === 'individual' ? renderIndividual() : scene === 'overview' ? renderOverview()
    : scene === 'discussion' || scene === 'roadmap' ? append(el('div', 'discussion-layout'), capture(scene === 'roadmap' ? 'Roadmap application capture' : 'Planning application capture')) : renderWrapup();
  append(root, header(), content, footer());
  fitCaptures(); updateLocalTime();
}

poll(next => {
  const changed = !state || state.revision !== next.revision;
  state = next;
  connection.hidden = true;
  if (changed) render();
  updateTimers(state);
}, () => { connection.hidden = false; connection.textContent = 'Connection lost. Showing last received state. Reconnecting...'; });
setInterval(() => updateTimers(state), 200);
setInterval(updateLocalTime, 1000);
