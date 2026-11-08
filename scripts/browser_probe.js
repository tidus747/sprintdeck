// Optional real-browser integration check, served only by check_browser.py.
import {calendarView, sprintMonths} from '/static/calendar.js';
const result = document.querySelector('#result');
const control = document.querySelector('#control');
const overlay = document.querySelector('#overlay');
const overview = document.querySelector('#overview');
const discussion = document.querySelector('#discussion');
const welcome = document.querySelector('#welcome');
const roadmap = document.querySelector('#roadmap');
const wrapup = document.querySelector('#wrapup');
const wait = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const assert = (condition, message) => { if (!condition) throw new Error(message); };
async function until(predicate, message) {
  for (let attempt = 0; attempt < 70; attempt++) { if (predicate()) return; await wait(100); }
  throw new Error(message);
}
const cdoc = () => control.contentDocument;
const odoc = () => overlay.contentDocument;
const findButton = label => [...cdoc().querySelectorAll('button')].find(button => button.textContent === label);
function setInput(input, value) {
  input.value = value;
  input.dispatchEvent(new Event('input', {bubbles: true}));
}
// Wait on UI effects, rather than introducing a browser automation dependency.
try {
  const calendarState = {sprint: {start: '2032-02-23', end: '2032-03-07'}, members: [], holidays: [], time_off: []};
  const leapView = calendarView(calendarState);
  assert(leapView.querySelector('[data-date="2032-02-29"]'), 'Leap day is missing from the calendar');
  assert(leapView.querySelector('[data-date="2032-03-31"]'), 'Cross-month calendar is incomplete');
  assert(sprintMonths({...calendarState, sprint: {start: '2030-12-23', end: '2031-01-05'}}).join(',') === '2030-12,2031-01', 'Calendar failed at the year boundary');
  assert(sprintMonths({...calendarState, sprint: {start: '9999-12-01', end: '9999-12-14'}}).length === 1, 'Last supported year did not terminate');
  await until(() => cdoc()?.querySelector('form[data-key="sprint-details"]') && odoc()?.querySelector('.identity-panel'), 'Pages did not render');
  const sprint = cdoc().querySelector('form[data-key="sprint-details"]');
  setInput(sprint.elements.namedItem('goal'), '<img src=x onerror=alert(1)> Technical validation');
  sprint.requestSubmit();
  await until(() => cdoc().querySelector('#feedback').textContent === 'Saved to the local session.', 'Sprint form did not save');
  const raw = await fetch('/api/export').then(response => response.json());
  assert(raw.sprint.goal.startsWith('<img'), 'Sprint goal did not persist as text');

  await until(() => welcome.contentDocument?.querySelector('.welcome-sprint'), 'Welcome scene did not render');
  assert(welcome.contentDocument.querySelector('.welcome-sprint').textContent === raw.sprint.next, 'Welcome scene has the wrong sprint');
  assert(welcome.contentDocument.body.textContent.includes('Planning starts shortly'), 'Welcome scene is missing its starting message');
  await until(() => welcome.contentDocument.body.textContent.includes('Technical validation'), 'Welcome scene did not synchronize the goal');
  assert(!welcome.contentDocument.querySelector('img'), 'Welcome goal was rendered as HTML');

  const milestone = cdoc().querySelector('form[data-key="roadmap-new"]');
  milestone.closest('details').open = true;
  setInput(milestone.elements.namedItem('title'), 'Colored validation milestone');
  const colorInput = milestone.elements.namedItem('color');
  colorInput.value = 'purple'; colorInput.dispatchEvent(new Event('change', {bubbles: true}));
  milestone.requestSubmit();
  await until(() => overview.contentDocument?.querySelector('[data-milestone-color="purple"]'), 'Milestone color did not update Overview');
  const colored = overview.contentDocument.querySelector('[data-milestone-color="purple"]');
  assert(overview.contentWindow.getComputedStyle(colored).borderLeftColor === 'rgb(105, 67, 166)', 'Milestone color is not visible');

  let sharedForm = cdoc().querySelector('form[data-key="shared-planning"]');
  setInput(sharedForm.elements.namedItem('objective'), 'Shared objective draft');
  const firstCheck = cdoc().querySelector('#individual .check-editor input'); firstCheck.click();
  await until(() => cdoc().querySelector('#individual h3')?.textContent.includes('20%'), 'Checklist did not save');
  assert(cdoc().querySelector('form[data-key="shared-planning"]').elements.namedItem('objective').value === 'Shared objective draft', 'Immediate save discarded a form draft');
  await until(() => odoc().querySelector('.review-panel h3')?.textContent.includes('20%'), 'Overlay did not poll checklist change');

  findButton('Next member').click();
  await until(() => odoc().querySelector('.identity-panel h2')?.textContent === 'Engineer B', 'Overlay did not update selected member');
  assert(!odoc().querySelector('.review-panel li').classList.contains('checked'), 'Checklists leaked between members');
  findButton('Previous member').click();
  await until(() => odoc().querySelector('.identity-panel h2')?.textContent === 'Engineer A', 'Previous navigation failed');
  assert(odoc().querySelector('.review-panel li').classList.contains('checked'), 'Checklist was lost on navigation');
  assert(cdoc().querySelector('form[data-key="shared-planning"]').elements.namedItem('objective').value === 'Shared objective draft', 'Navigation discarded a shared draft');

  let downloaded = 0;
  let downloadBlob;
  const controlWindow = control.contentWindow;
  const createURL = controlWindow.URL.createObjectURL.bind(controlWindow.URL);
  controlWindow.URL.createObjectURL = blob => { downloadBlob = blob; return createURL(blob); };
  controlWindow.HTMLAnchorElement.prototype.click = function () { downloaded++; assert(this.download === 'sprintdeck-recap.md', 'Incorrect download filename'); };
  setInput(cdoc().querySelector('form[data-key="session-notes"]').elements.namedItem('notes'), 'Private recap note: testing agreed.');
  findButton('Save session & download recap (.md)').click();
  await until(() => cdoc().querySelector('#feedback').textContent.includes('other edited sections'), 'Recap did not guard unsaved drafts');
  assert(downloaded === 0, 'Recap downloaded despite unsaved changes');
  sharedForm = cdoc().querySelector('form[data-key="shared-planning"]');
  setInput(sharedForm.elements.namedItem('notes'), '<img src=x onerror=alert(1)>');
  sharedForm.requestSubmit();
  await until(() => odoc().body.textContent.includes('Shared objective draft'), 'Shared context did not update');
  assert(!odoc().querySelector('img'), 'User text became an image element');
  assert(odoc().body.textContent.includes('<img src=x onerror=alert(1)>'), 'User text was not displayed safely');
  assert(!cdoc().querySelector('[name="available"]') && !odoc().querySelector('.capacity'), 'Capacity UI was not removed');
  findButton('Next member').click();
  await until(() => odoc().querySelector('.identity-panel h2')?.textContent === 'Engineer B', 'Member navigation failed');
  assert(odoc().body.textContent.includes('Shared objective draft'), 'Planning context changed with the selected member');

  await until(() => overview.contentDocument?.querySelector('.calendar-day'), 'Overview calendar did not render');
  const month = raw.sprint.start.slice(0, 7);
  const monthDate = new Date(`${month}-01T12:00:00`);
  const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
  assert(overview.contentDocument.querySelector(`[data-date="${month}-01"]`), 'Calendar is missing the start of the month');
  assert(overview.contentDocument.querySelector(`[data-date="${month}-${lastDay}"]`), 'Calendar is missing the end of the month');
  assert(overview.contentDocument.querySelector('.calendar-day.nonworking'), 'Weekends were not marked');
  const holiday = cdoc().querySelector('form[data-key="holidays-new"]');
  holiday.closest('details').open = true;
  setInput(holiday.elements.namedItem('title'), 'Example holiday');
  setInput(holiday.elements.namedItem('date'), raw.sprint.start);
  holiday.requestSubmit();
  await until(() => overview.contentDocument.querySelector(`[data-date="${raw.sprint.start}"].nonworking`), 'Holiday did not update the calendar');
  const timeOff = cdoc().querySelector('form[data-key="time_off-new"]');
  timeOff.closest('details').open = true;
  setInput(timeOff.elements.namedItem('start'), raw.sprint.start);
  setInput(timeOff.elements.namedItem('end'), raw.sprint.end);
  timeOff.requestSubmit();
  await until(() => overview.contentDocument.querySelector(`[data-date="${raw.sprint.start}"] .away-count`), 'Time off did not update the calendar');
  assert(overview.contentDocument.querySelector('.time-off-panel').textContent.includes('Engineer A'), 'Time off list is missing the member');

  findButton('Save session & download recap (.md)').click();
  await until(() => downloaded === 1, 'Recap download did not start');
  const markdown = await downloadBlob.text();
  assert(markdown.includes('Private recap note: testing agreed.'), 'Recap omitted saved session notes');
  assert(markdown.includes('Shared objective draft'), 'Recap omitted shared planning context');
  assert(markdown.includes('Example holiday') && markdown.includes('Planned time off'), 'Recap omitted calendar information');
  assert(!odoc().body.textContent.includes('Private recap note'), 'Private session notes leaked into the overlay');

  const timerButton = [...cdoc().querySelectorAll('#individual button')].find(button => button.textContent === 'Start / resume');
  timerButton.click();
  await until(() => odoc().querySelector('[data-timer-display="individual"]').parentElement.textContent.includes('Running'), 'Timer did not start');
  [...cdoc().querySelectorAll('#individual button')].find(button => button.textContent === 'Pause').click();
  await until(() => odoc().querySelector('[data-timer-display="individual"]').parentElement.textContent.includes('Paused'), 'Timer did not pause');
  const frameWindow = overlay.contentWindow;
  assert(frameWindow.getComputedStyle(odoc().body).backgroundColor === 'rgba(0, 0, 0, 0)', 'Overlay body is opaque');
  assert(frameWindow.getComputedStyle(odoc().querySelector('.capture-region')).backgroundColor === 'rgba(0, 0, 0, 0)', 'Capture region is opaque');
  await until(() => discussion.contentDocument?.querySelector('.capture-region'), 'Discussion scene did not render');
  const discussionRegion = discussion.contentDocument.querySelector('.capture-region');
  assert(discussion.contentWindow.getComputedStyle(discussionRegion).backgroundColor === 'rgba(0, 0, 0, 0)', 'Discussion capture is opaque');
  assert(discussionRegion.getBoundingClientRect().width > discussion.contentWindow.innerWidth * .8, 'Discussion capture is too narrow');
  assert(discussionRegion.getBoundingClientRect().height > discussion.contentWindow.innerHeight * .8, 'Discussion capture is too short');

  await until(() => roadmap.contentDocument?.querySelector('.capture-region') && wrapup.contentDocument?.querySelector('[data-local-clock]'), 'Additional scenes did not render');
  for (const frame of [overlay, overview, discussion, roadmap]) {
    const region = frame.contentDocument.querySelector('.capture-region');
    const rect = region.getBoundingClientRect();
    assert(Math.abs(rect.width / rect.height - 16 / 9) < .0001, 'Capture source would be distorted');
    assert(rect.left >= 0 && rect.top >= 0 && rect.right <= frame.contentWindow.innerWidth + 1 && rect.bottom <= frame.contentWindow.innerHeight + 1, 'Capture exceeds the scene bounds');
    assert(!region.children.length, 'Capture aperture obscures the source');
  }
  for (const frame of [overlay, overview, discussion, roadmap, welcome, wrapup]) {
    const time = frame.contentDocument.querySelector('[data-local-clock]');
    assert(time?.dateTime && time.textContent.includes(':'), 'Local date and time is missing');
    const format = new frame.contentWindow.Intl.DateTimeFormat('en-GB', {year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZoneName: 'short'});
    assert(time.textContent === format.format(new Date(time.dateTime)), 'Footer clock does not use local time');
  }
  const previousTime = welcome.contentDocument.querySelector('[data-local-clock]').dateTime;
  await wait(1200);
  assert(welcome.contentDocument.querySelector('[data-local-clock]').dateTime !== previousTime, 'Local clock did not tick');
  result.textContent = 'BROWSER_CHECK_PASSED';
} catch (error) { result.textContent = `BROWSER_CHECK_FAILED: ${error.message}`; }
