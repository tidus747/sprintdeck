import {el, append, panel} from './common.js';

export function dateKey(value) {
  return `${String(value.getFullYear()).padStart(4, '0')}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
}

export function sprintMonths(state) {
  const months = [];
  const current = new Date(`${state.sprint.start.slice(0, 7)}-01T12:00:00`);
  const last = new Date(`${state.sprint.end.slice(0, 7)}-01T12:00:00`);
  while (current <= last) {
    months.push(dateKey(current).slice(0, 7));
    current.setMonth(current.getMonth() + 1);
  }
  return months;
}

export function calendarView(state, months = sprintMonths(state)) {
  const box = panel('Sprint calendar', 'calendar-panel');
  append(box, el('p', 'muted', `${state.sprint.start} to ${state.sprint.end}`));
  const calendars = el('div', `month-calendars ${months.length > 1 ? 'multiple-months' : ''}`);
  const today = dateKey(new Date());
  for (const month of months) {
    const first = new Date(`${month}-01T12:00:00`);
    const monthEnd = new Date(first); monthEnd.setMonth(monthEnd.getMonth() + 1); monthEnd.setDate(0);
    const days = monthEnd.getDate();
    const section = el('section', 'month-calendar');
    section.append(el('h4', '', first.toLocaleDateString('en', {month: 'long', year: 'numeric'})));
    const grid = el('div', 'calendar-grid');
    for (const day of ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']) grid.append(el('span', `weekday ${day === 'Sat' || day === 'Sun' ? 'nonworking' : ''}`, day));
    for (let offset = 0; offset < (first.getDay() + 6) % 7; offset++) grid.append(el('span', 'calendar-empty'));
    for (let day = 1; day <= days; day++) {
      const current = new Date(first); current.setDate(day);
      const key = dateKey(current);
      const weekend = current.getDay() === 0 || current.getDay() === 6;
      const holidays = state.holidays.filter(item => item.date === key);
      const away = state.time_off.filter(item => item.start <= key && item.end >= key);
      const cell = el('div', `calendar-day ${key >= state.sprint.start && key <= state.sprint.end ? 'in-sprint' : ''} ${weekend || holidays.length ? 'nonworking' : ''} ${key === today ? 'today' : ''}`);
      cell.dataset.date = key;
      append(cell, el('strong', '', day), away.length ? el('small', 'away-count', `${new Set(away.map(item => item.member_id)).size} away`) : null);
      const names = [...new Set(away.map(item => state.members.find(member => member.id === item.member_id)?.name))];
      const description = [key, weekend ? 'Weekend' : '', ...holidays.map(item => item.title), names.length ? `Time off: ${names.join(', ')}` : ''].filter(Boolean).join(' | ');
      cell.setAttribute('aria-label', description); cell.title = description;
      grid.append(cell);
    }
    section.append(grid); calendars.append(section);
  }
  append(box, calendars, el('p', 'calendar-legend', 'Blue: sprint dates | Red: weekends / configured holidays | Away: planned time off'));
  const holidays = state.holidays.filter(item => months.includes(item.date.slice(0, 7)));
  if (holidays.length) box.append(el('p', 'holiday-caption', holidays.map(item => `${item.date}: ${item.title}`).join(' | ')));
  return box;
}

export function timeOffView(state, {sprintOnly = true} = {}) {
  const box = panel('Planned time off', 'time-off-panel');
  const entries = state.time_off.filter(item => !sprintOnly || (item.end >= state.sprint.start && item.start <= state.sprint.end))
    .sort((a, b) => a.start.localeCompare(b.start));
  const list = el('div', 'presentation-list');
  for (const item of entries) {
    const name = state.members.find(member => member.id === item.member_id)?.name || 'Team member';
    append(list, append(el('article', 'presentation-item'), el('strong', '', name), el('p', 'muted', `${item.start} to ${item.end}`), item.note ? el('small', 'muted', item.note) : null));
  }
  if (!entries.length) list.append(el('p', 'muted', 'No planned time off during this sprint.'));
  box.append(list); return box;
}
