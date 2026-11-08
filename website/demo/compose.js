// Documentation-only composition: real overlays above an explicitly fictional board.
const scene = location.pathname.split('/').pop();
const frame = document.querySelector('#overlay');
frame.src = `/overlays/${scene}`;
const source = document.querySelector('#sample-capture');
function node(tag, text, className = '') { const result = document.createElement(tag); result.textContent = text; result.className = className; return result; }
const header = node('header', '', 'sample-header');
const intro = node('div', '');
intro.append(node('span', 'FICTIONAL EXTERNAL CAPTURE', 'sample-label'), node('h1', scene === 'roadmap' ? 'Delivery roadmap' : 'Sprint 02 / Planning board'), node('p', 'Illustrative board for documentation. No project management integration.'));
header.append(intro, node('span', 'Demo workspace', 'sample-tag')); source.append(header);
if (scene === 'roadmap') {
  const timeline = node('div', '', 'timeline');
  const head = node('div', '', 'timeline-head');
  ['Milestone', 'Week 1', 'Week 2', 'Week 3', 'Week 4'].forEach(text => head.append(node('span', text))); timeline.append(head);
  [['Platform integration', 'Technical validation', 'bar-purple', '2 / 4'], ['Automated testing', 'Testing coverage', 'bar-green', '3 / 5'], ['Documentation improvements', 'Review and update', '', '2 / 5'], ['Release readiness', 'Final validation', 'bar-orange', '4 / 6']].forEach(([name, text, color, column]) => {
    const row = node('div', '', 'timeline-row'); row.append(node('strong', name));
    const bar = node('div', text, `timeline-bar ${color}`); bar.style.gridColumn = column; row.append(bar); timeline.append(row);
  }); source.append(timeline);
} else {
  const columns = node('div', '', 'sample-columns');
  [['To plan', [['EX-101', 'Documentation improvements', 'Engineer A', 'Agree the review scope.'], ['EX-102', 'Release readiness', 'Engineer C', 'Confirm the remaining validation.']]], ['In review', [['EX-103', 'Automated testing', 'Engineer B', 'Review the proposed test coverage.'], ['EX-104', 'Platform integration', 'Engineer D', 'Identify dependencies together.']]], ['Agreed', [['EX-105', 'Technical validation', 'Engineer E', 'Review sequence confirmed.']]]].forEach(([title, cards]) => {
    const column = node('section', '', 'sample-column'); const heading = node('h2', title); heading.append(node('span', String(cards.length))); column.append(heading);
    cards.forEach(([key, title, owner, description]) => { const card = node('article', '', 'sample-card'); const footer = node('footer', ''); footer.append(node('span', owner), node('span', 'Demo item', 'sample-chip')); card.append(node('span', key, 'sample-key'), node('h3', title), node('p', description), footer); column.append(card); }); columns.append(column);
  }); source.append(columns);
}
const bottom = node('footer', '', 'sample-bottom'); bottom.append(node('span', 'Fictional planning content'), node('span', '1920 x 1080 source / scaled uniformly')); source.append(bottom);
function align() {
  const aperture = frame.contentDocument?.querySelector('.capture-region');
  if (aperture) {
    // This fictional capture is inserted only by the documentation fixture, never the app.
    // Keeping it in the aperture's coordinate system avoids cross-frame zoom differences.
    if (!frame.contentDocument.querySelector('[data-demo-style]')) {
      const style = frame.contentDocument.createElement('link'); style.rel = 'stylesheet'; style.href = '/demo/board.css'; style.dataset.demoStyle = 'true'; frame.contentDocument.head.append(style);
    }
    if (source.parentElement !== aperture) aperture.append(source);
    source.style.left = '0'; source.style.top = '0';
    source.style.transform = `scale(${aperture.clientWidth / 1920})`; source.style.visibility = 'visible';
    const rect = aperture.getBoundingClientRect();
    const actual = source.getBoundingClientRect();
    document.body.dataset.alignment = Math.abs(actual.width - rect.width) < 1 && Math.abs(actual.height - rect.height) < 1 && Math.abs(actual.x - rect.x) < 1 && Math.abs(actual.y - rect.y) < 1 ? 'verified' : 'failed';
  }
}
setInterval(align, 100); frame.addEventListener('load', align); addEventListener('resize', align);
