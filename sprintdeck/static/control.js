import {el, append, panel, badge, timerView, updateTimers, synchronize, request, poll} from './common.js';
import {calendarView, dateKey} from './calendar.js';

let state;
let busy = false;
let submittedKey = null;
const drafts = new Map();
let viewedMonth = null;
const root = document.querySelector('#workspace');
const feedback = document.querySelector('#feedback');
const connection = document.querySelector('#connection');

function notify(message, error = false) {
  feedback.textContent = message;
  feedback.className = error ? 'feedback-error' : 'feedback-success';
}

async function act(action, form = null) {
  if (busy) return;
  busy = true;
  root.setAttribute('aria-busy', 'true');
  try {
    const next = await request('/api/actions', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...action, revision: state.revision})});
    submittedKey = form?.dataset.key;
    if (action.type === 'reset_session' || action.type === 'import_session') {
      drafts.clear();
      root.querySelectorAll('form').forEach(edit => { delete edit.dataset.dirty; });
    }
    state = next; synchronize(state); render();
    notify('Saved to the local session.');
    return true;
  } catch (error) {
    notify(error.message, true);
    try { state = await request('/api/state'); synchronize(state); render(); } catch { /* Polling retries connection failures. */ }
    return false;
  }
  finally { busy = false; root.removeAttribute('aria-busy'); submittedKey = null; }
}

function button(label, handler, className = 'secondary') {
  const node = el('button', className, label); node.type = 'button';
  node.addEventListener('click', handler); return node;
}

function field(form, label, name, value = '', type = 'text') {
  const wrap = el('label', 'field');
  const input = el(type === 'textarea' ? 'textarea' : 'input');
  input.name = name;
  if (type !== 'textarea') input.type = type;
  if (type === 'checkbox') input.checked = Boolean(value);
  else input.value = value;
  if (type === 'number') { input.min = '0'; input.max = '366'; input.step = '0.5'; }
  if (type === 'text' || type === 'textarea') input.maxLength = 2000;
  append(wrap, el('span', '', label), input); form.append(wrap);
  input.addEventListener('input', () => { form.dataset.dirty = 'true'; });
  return input;
}

function selectField(form, label, name, value, options) {
  const wrap = el('label', 'field'); const input = el('select'); input.name = name;
  for (const option of options) { const node = el('option', '', option.label ?? option); node.value = option.value ?? option; input.append(node); }
  input.value = value; input.addEventListener('change', () => { form.dataset.dirty = 'true'; });
  append(wrap, el('span', '', label), input); form.append(wrap); return input;
}

function form(key, handler) {
  const node = el('form', 'edit-form'); node.dataset.key = key;
  node.addEventListener('submit', event => { event.preventDefault(); handler(values(node), node); });
  return node;
}

function values(node) {
  return Object.fromEntries([...node.elements].filter(input => input.name).map(input => [input.name, input.type === 'checkbox' ? input.checked : input.type === 'number' ? Number(input.value) : input.value]));
}

function save(form, label = 'Save changes') {
  const node = el('button', 'primary', label); node.type = 'submit'; form.append(node);
}

function section(id, title, description) {
  const node = el('section', 'dashboard-section'); node.id = id;
  append(node, el('p', 'eyebrow', `PLANNING / ${title.toUpperCase()}`), el('h2', '', title), el('p', 'section-description', description));
  root.append(node); return node;
}

function timerControl(name, title) {
  const box = panel(title);
  box.append(timerView(name, title));
  const controls = el('div', 'button-row');
  const running = state.timers[name].deadline !== null;
  append(controls, button(running ? 'Pause' : 'Start / resume', () => act({type: 'timer', timer: name, operation: running ? 'pause' : 'start'}), 'primary'),
    button('Reset', () => { if (confirm(`Reset the ${title.toLowerCase()}?`)) act({type: 'timer', timer: name, operation: 'reset'}); }));
  box.append(controls);
  const edit = form(`timer-${name}`, (v, f) => {
    if (confirm(`Set the duration and reset the ${title.toLowerCase()}?`)) act({type: 'timer', timer: name, operation: 'reset', duration: v.minutes * 60}, f);
  });
  const duration = field(edit, 'Duration (minutes, saves and resets timer)', 'minutes', state.timers[name].duration / 60, 'number');
  duration.min = '0.1'; duration.max = '1440'; duration.step = '0.1'; duration.required = true;
  save(edit, 'Set duration'); box.append(edit); return box;
}

function sprintForm(key, fields) {
  const edit = form(key, (v, f) => act({type: 'update_sprint', values: v}, f));
  for (const [name, label, type = 'text'] of fields) field(edit, label, name, state.sprint[name], type);
  save(edit); return edit;
}

const collectionFields = {
  roadmap: [['title', 'Milestone'], ['date', 'Planned date', 'date'], ['description', 'Description', 'textarea'], ['status', 'Status', 'select'], ['color', 'Milestone color', 'color']],
  scope: [['title', 'Deliverable'], ['confirmed', 'Confirmed', 'checkbox']],
  risks: [['text', 'Risk or blocker', 'textarea'], ['owner', 'Owner'], ['next_action', 'Next action'], ['status', 'Status', 'select']],
  decisions: [['text', 'Decision', 'textarea'], ['owner', 'Responsible person'], ['status', 'Status', 'select']],
  actions: [['text', 'Follow-up action', 'textarea'], ['owner', 'Owner'], ['due', 'Due date', 'date'], ['status', 'Status', 'select']],
  holidays: [['title', 'Holiday name'], ['date', 'Date', 'date']],
  time_off: [['member_id', 'Team member', 'member'], ['start', 'First day away', 'date'], ['end', 'Last day away (inclusive)', 'date'], ['note', 'Note (optional)']]
};

function collectionEditor(name, title) {
  const box = panel(title);
  const list = el('div', 'collection-editor');
  function itemForm(item = null) {
    const edit = form(`${name}-${item?.id || 'new'}`, (v, f) => act({type: 'save_item', collection: name, id: item?.id ?? null, values: v}, f));
    for (const [key, label, type = 'text'] of collectionFields[name]) {
      if (type === 'select') selectField(edit, label, key, item?.[key] || (name === 'roadmap' ? 'Planned' : 'Open'), ['Planned', 'Open', 'In progress', 'Confirmed', 'Resolved']);
      else if (type === 'color') selectField(edit, label, key, item?.[key] || 'blue', ['blue', 'green', 'purple', 'orange', 'red', 'teal'].map(color => ({value: color, label: color[0].toUpperCase() + color.slice(1)})));
      else if (type === 'member') selectField(edit, label, key, item?.[key] || state.members[0]?.id, state.members.map(member => ({value: member.id, label: member.name}))).required = true;
      else { const input = field(edit, label, key, item?.[key] ?? (type === 'checkbox' ? false : ''), type); if (key === 'text' || key === 'title' || (type === 'date' && ['holidays', 'time_off'].includes(name))) input.required = true; if (type === 'text' || type === 'textarea') input.maxLength = 400; }
    }
    save(edit, item ? 'Save item' : 'Add item');
    if (item) edit.append(button('Remove item', () => { if (confirm('Remove this item?')) act({type: 'remove_item', collection: name, id: item.id, confirm: true}); }, 'danger'));
    return edit;
  }
  for (const item of state[name]) {
    const details = el('details'); details.dataset.item = item.id;
    const heading = name === 'time_off' ? `${state.members.find(member => member.id === item.member_id)?.name}: ${item.start} to ${item.end}` : name === 'holidays' ? `${item.title} | ${item.date}` : item.title || item.text;
    const summary = el('summary', '', heading);
    if (name === 'roadmap') { summary.classList.add('milestone-summary', `milestone-${item.color}`); summary.append(el('span', 'milestone-color-label', item.color)); }
    append(details, summary, itemForm(item)); list.append(details);
  }
  box.append(list);
  if (name === 'time_off' && !state.members.length) box.append(el('p', 'muted', 'Add a team member before recording time off.'));
  else if (state[name].length < (['holidays', 'time_off'].includes(name) ? 60 : 12)) { const details = el('details'); details.dataset.item = `new-${name}`; append(details, el('summary', '', `Add ${title.toLowerCase()} item`), itemForm()); box.append(details); }
  return box;
}

async function saveRecap(edit) {
  const otherDrafts = new Set(drafts.keys());
  root.querySelectorAll('form[data-dirty="true"]').forEach(form => otherDrafts.add(form.dataset.key));
  otherDrafts.delete('session-notes');
  if (otherDrafts.size) { notify('Save changes in other edited sections before generating the recap. Your drafts are still available.', true); return; }
  if (!await act({type: 'update_session', values: values(edit)}, edit)) return;
  try {
    const response = await fetch('/api/recap', {cache: 'no-store'});
    if (!response.ok) throw new Error('The recap could not be generated. Your notes are saved; try downloading again.');
    const url = URL.createObjectURL(await response.blob());
    const link = el('a'); link.href = url; link.download = 'sprintdeck-recap.md'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    notify('Session saved and Markdown recap downloaded. Review the file before sharing.');
  } catch (error) { notify(error.message, true); }
}

function checksEditor(items, memberId = null) {
  const list = el('div', 'check-editor');
  for (const item of items) {
    const label = el('label', 'check-row'); const input = el('input'); input.type = 'checkbox'; input.checked = item.checked;
    input.addEventListener('change', () => act(memberId ? {type: 'set_check', member_id: memberId, id: item.id, checked: input.checked} : {type: 'set_final_check', id: item.id, checked: input.checked}));
    append(label, input, el('span', '', item.label)); list.append(label);
  }
  return list;
}

function render() {
  // Keep unsaved form values, focus, and open editors when polling or saving another panel.
  if (submittedKey) drafts.delete(submittedKey);
  for (const edit of root.querySelectorAll('form[data-dirty="true"]')) {
    if (edit.dataset.key !== submittedKey) drafts.set(edit.dataset.key, values(edit));
  }
  const opened = new Set([...root.querySelectorAll('details[open]')].map(node => node.dataset.item));
  const focused = document.activeElement;
  const focusKey = focused?.closest('form')?.dataset.key;
  const focusName = focused?.name;
  const selection = typeof focused?.selectionStart === 'number' ? focused.selectionStart : null;
  root.replaceChildren();

  const ceremony = section('ceremony', 'Ceremony', 'One shared session for your controller and every presentation scene.');
  const progress = panel('Session pulse');
  const progressMeter = el('progress'); progressMeter.max = 100; progressMeter.value = state.progress; progressMeter.setAttribute('aria-label', 'Team checklist completion');
  append(progress, badge(state.ready ? 'Ready for commitment' : 'Review in progress', state.ready ? 'green' : 'purple'), el('p', '', `${state.progress}% of individual checks complete`), progressMeter);
  const links = el('div', 'button-row');
  for (const [route, label] of [['welcome', 'Welcome preview'], ['overview', 'Overview preview'], ['individual', 'Individual preview'], ['wrapup', 'Wrap-up preview'], ['discussion', 'Board discussion preview'], ['roadmap', 'Roadmap preview']]) {
    const link = el('a', 'button-link', label); link.href = `/overlays/${route}`; link.target = '_blank'; link.rel = 'noopener'; links.append(link);
  }
  append(ceremony, links, append(el('div', 'grid two'), progress, timerControl('meeting', 'Meeting timer')));

  const overview = section('overview', 'Overview', 'Set the shared context before reviewing individual commitments.');
  append(overview, append(el('div', 'grid two'), append(panel('Sprint details'), sprintForm('sprint-details', [['current', 'Current sprint'], ['next', 'Upcoming sprint'], ['start', 'Start date', 'date'], ['end', 'End date', 'date'], ['status', 'Planning status'], ['goal', 'Sprint goal', 'textarea']])),
    append(panel('Current sprint summary'), sprintForm('current-summary', [['current_status', 'Current sprint status'], ['summary', 'Summary', 'textarea'], ['carryover', 'Carry-over work', 'textarea']]))), collectionEditor('roadmap', 'Roadmap'));

  const shared = form('shared-planning', (v, f) => act({type: 'update_planning', values: v}, f));
  for (const [key, label] of [['objective', 'Shared sprint objective'], ['deliverables', 'Expected deliverables'], ['dependencies', 'Dependencies'], ['risks', 'Shared risks'], ['notes', 'Shared review notes'], ['pending_decisions', 'Pending decisions']]) field(shared, label, key, state.planning[key], 'textarea').maxLength = 28000;
  save(shared, 'Save shared planning context');
  append(overview, append(panel('Shared planning context, common to every team member'), el('p', 'section-description', 'These fields stay the same when switching members and are visible in the Individual Planning overlay.'), shared));

  const calendar = section('calendar', 'Calendar & time off', 'Configure holidays and planned absences manually. SprintDeck does not calculate capacity.');
  viewedMonth = viewedMonth || state.sprint.start.slice(0, 7);
  const calendarNavigation = el('div', 'button-row');
  function moveMonth(direction) {
    const current = new Date(`${viewedMonth}-01T12:00:00`); current.setMonth(current.getMonth() + direction);
    viewedMonth = dateKey(current).slice(0, 7); render();
  }
  append(calendarNavigation, button('Previous month', () => moveMonth(-1)), button('Sprint month', () => { viewedMonth = state.sprint.start.slice(0, 7); render(); }), button('Next month', () => moveMonth(1)));
  append(calendar, calendarNavigation, calendarView(state, [viewedMonth]), append(el('div', 'grid two'), collectionEditor('holidays', 'Holidays'), collectionEditor('time_off', 'Time off')));

  const team = section('team', 'Team', 'Arrange the review sequence. Selection never confirms a commitment.');
  const roster = el('div', 'roster');
  state.members.forEach((member, index) => {
    const row = el('div', `member-row ${member.id === state.active_member ? 'active' : ''}`);
    const choose = button(`${String(index + 1).padStart(2, '0')}  ${member.name}`, () => act({type: 'select_member', member_id: member.id}));
    choose.setAttribute('aria-pressed', String(member.id === state.active_member));
    const up = button('Move up', () => act({type: 'move_member', member_id: member.id, direction: -1})); up.disabled = index === 0;
    const down = button('Move down', () => act({type: 'move_member', member_id: member.id, direction: 1})); down.disabled = index === state.members.length - 1;
    append(row, choose, badge(member.status), el('span', 'muted', `${member.completion}%`), up, down,
      button('Remove', () => { if (confirm(`Remove ${member.name}, their review, and planned time off?`)) act({type: 'remove_member', member_id: member.id, confirm: true}); }, 'danger'));
    roster.append(row);
  });
  const add = form('add-member', (v, f) => act({type: 'add_member', name: v.name}, f)); field(add, 'New member name', 'name').required = true; save(add, 'Add member');
  append(team, roster, add);

  const individual = section('individual', 'Individual review', 'Review each commitment against the shared sprint context. Use your captured board for capacity.');
  const navigation = el('div', 'button-row');
  const previous = button('Previous member', () => act({type: 'navigate_member', direction: -1}));
  const next = button('Next member', () => act({type: 'navigate_member', direction: 1}));
  previous.disabled = next.disabled = state.members.length === 0;
  append(navigation, previous, next); individual.append(navigation);
  const member = state.members.find(value => value.id === state.active_member);
  if (member) {
    const review = panel(`${member.name} | ${member.completion}% complete`);
    append(review, badge(member.status), checksEditor(member.checks, member.id));
    const confirmation = form(`confirmation-${member.id}`, (v, f) => act({type: 'update_member', member_id: member.id, values: v}, f));
    field(confirmation, 'Facilitator override: mark review complete without all checks', 'review_override', member.review_override, 'checkbox');
    field(confirmation, 'Member explicitly confirmed their commitment', 'confirmed', member.confirmed, 'checkbox'); save(confirmation, 'Save review status');
    append(review, confirmation, el('small', 'muted', 'Confirmed status requires a complete review (or the labeled override) and explicit commitment confirmation.'));
    append(individual, append(el('div', 'grid two'), review, timerControl('individual', 'Individual timer')));
    const details = form(`member-${member.id}`, (v, f) => act({type: 'update_member', member_id: member.id, values: v}, f));
    field(details, 'Name', 'name', member.name).maxLength = 100;
    field(details, 'Role (optional)', 'role', member.role).maxLength = 100;
    save(details, 'Save member details');
    append(individual, append(panel('Member details'), details));
  } else individual.append(el('p', 'empty', 'Add a team member to begin the review.'));

  const commitment = section('commitment', 'Commitment', 'Close with an explicit scope, recorded decisions, and assigned next steps.');
  append(commitment, append(panel('Sprint commitment'), sprintForm('commitment', [['commitment', 'Agreed commitment summary', 'textarea']])),
    append(el('div', 'grid two'), collectionEditor('scope', 'Committed scope'), append(panel('Final ceremony checklist'), checksEditor(state.final_checks))),
    append(el('div', 'grid two'), collectionEditor('risks', 'Risks and attention points'), collectionEditor('decisions', 'Decisions')), collectionEditor('actions', 'Next steps'));

  const notes = section('notes', 'Session notes & recap', 'Keep private meeting notes and download a Markdown recap of the agreements, decisions, risks, and next steps. Notes are not shown on presentation overlays.');
  const noteForm = form('session-notes', (v, f) => act({type: 'update_session', values: v}, f));
  field(noteForm, 'Session title', 'title', state.session.title).maxLength = 100;
  field(noteForm, 'Session notes', 'notes', state.session.notes, 'textarea').maxLength = 16000;
  save(noteForm, 'Save notes');
  noteForm.append(button('Save session & download recap (.md)', () => saveRecap(noteForm), 'primary'));
  append(notes, append(panel('Meeting minutes'), noteForm, el('p', 'muted', 'Save edited sections before generating the recap. The report uses saved data, preserves pending items, and includes the complete notes without projection truncation.')));

  const settings = section('settings', 'Settings', 'Export a backup before replacing or clearing this session.');
  const data = panel('Session data');
  const exportButton = button('Export session JSON', async () => {
    try {
      const value = await request('/api/export'); const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type: 'application/json'}));
      const link = el('a'); link.href = url; link.download = 'sprintdeck.session.json'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); notify('Session exported. Keep this file private.');
    } catch (error) { notify(error.message, true); }
  });
  const importForm = el('div', 'import-control'); const importLabel = el('label', 'field'); const file = el('input'); file.type = 'file'; file.accept = '.json,application/json';
  append(importLabel, el('span', '', 'Import session JSON (replaces the current session)'), file); importForm.append(importLabel);
  file.addEventListener('change', async () => {
    const selected = file.files[0]; if (!selected) return;
    if (selected.size > 250000) { notify('Import file is too large (maximum 250,000 bytes).', true); file.value = ''; return; }
    try { const imported = JSON.parse(await selected.text()); if (confirm('Replace this session with the imported data? Export a backup first.')) await act({type: 'import_session', state: imported, confirm: true}); }
    catch { notify('The file is not valid JSON.', true); }
    file.value = '';
  });
  append(data, exportButton, importForm, button('Load fictional demo', async () => {
    if (!confirm('Replace this session with the fictional demo? Export a backup first.')) return;
    try { const demo = await request('/static/demo-session.json'); await act({type: 'import_session', state: demo, confirm: true}); }
    catch (error) { notify(error.message, true); }
  }), button('Reset entire session', () => { if (confirm('Clear all session data and restore a blank five-member team? This cannot be undone.')) act({type: 'reset_session', confirm: true}); }, 'danger'));
  const config = form('checklist-config', (v, f) => { if (confirm('Replace and clear every individual checklist and commitment confirmation?')) act({type: 'configure_checks', labels: v.labels.split('\n').map(s => s.trim()).filter(Boolean), confirm: true}, f); });
  field(config, 'Individual checklist template (one item per line, 1 to 12 items)', 'labels', (state.members[0]?.checks || []).map(c => c.label).join('\n'), 'textarea'); save(config, 'Replace all individual checklists');
  append(settings, data, append(panel('Review checklist configuration'), config), el('p', 'muted', 'Limits: 20 members, 60 holidays and time-off entries, 12 items in other lists. Long overlay text is truncated; complete content stays in the controller, JSON export, and Markdown recap.'));

  for (const edit of root.querySelectorAll('form')) {
    const draft = drafts.get(edit.dataset.key);
    if (draft) { for (const input of edit.elements) { if (!(input.name in draft)) continue; if (input.type === 'checkbox') input.checked = draft[input.name]; else input.value = draft[input.name]; } edit.dataset.dirty = 'true'; }
    if (edit.dataset.key === focusKey && focusName) {
      const input = edit.elements.namedItem(focusName); input?.focus({preventScroll: true});
      if (selection !== null && input?.type !== 'number') { try { input.setSelectionRange(selection, selection); } catch { /* Some input types have no selection range. */ } }
    }
  }
  root.querySelectorAll('details').forEach(node => { if (opened.has(node.dataset.item)) node.open = true; });
  const validDrafts = new Set([...root.querySelectorAll('form')].map(edit => edit.dataset.key));
  state.members.forEach(member => { validDrafts.add(`member-${member.id}`); validDrafts.add(`confirmation-${member.id}`); });
  for (const key of drafts.keys()) { if (!validDrafts.has(key)) drafts.delete(key); }
  updateTimers(state);
}

poll(next => {
  const recovered = connection.textContent === 'Disconnected';
  connection.textContent = 'Connected locally'; connection.className = 'badge green';
  if (busy) return;
  const changed = !state || state.revision !== next.revision;
  state = next;
  if (changed) render();
  updateTimers(state);
  if (feedback.textContent === 'Loading session...') notify('Session ready. Changes save on this device.');
  else if (recovered) notify('Connection restored. The local session is available.');
}, error => { connection.textContent = 'Disconnected'; connection.className = 'badge orange'; notify(`Connection lost. ${error.message}. Reconnecting automatically.`, true); });
setInterval(() => updateTimers(state), 200);
