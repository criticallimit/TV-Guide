const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const {chromium, webkit} = require('playwright');
const root = path.resolve(__dirname, '../www');
async function main() {
  let guideRequests = 0, refreshRunning = false;
  const programs = [
    {title:'Before midnight', start:'2030-01-01T23:00:00+01:00', end:'2030-01-01T23:59:00+01:00'},
    {title:'Across midnight', start:'2030-01-01T23:59:00+01:00', end:'2030-01-02T00:05:00+01:00'},
    {title:'After midnight', start:'2030-01-02T00:05:00+01:00', end:'2030-01-02T01:00:00+01:00'}
  ];
  const channels = Array.from({length:120}, (_, index) => ({id:String(index), name:`Channel ${index}`, programs}));
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://local');
    if (url.pathname.startsWith('/api/')) {
      if (url.pathname === '/api/guide') guideRequests++;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(url.pathname === '/api/guide'
        ? {country:'de', channels, main_channel_ids:channels.map(item => item.id), custom_channel_ids:[], ui:{default_view:'now'}, refresh_running:refreshRunning}
        : {bookmarks:[], reminders:[]})); return;
    }
    const file = path.resolve(root, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : file.endsWith('.html') ? 'text/html' : 'application/octet-stream');
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    for (const [engine, type] of [['chromium', chromium], ['webkit', webkit]]) {
      const browser = await type.launch(engine === 'chromium' && process.env.TVGUIDE_EDGE_PATH ? {executablePath:process.env.TVGUIDE_EDGE_PATH} : {});
      try {
        const page = await browser.newPage({timezoneId:'Europe/Berlin'});
        const errors = []; page.on('pageerror', error => errors.push(error.message));
        await page.clock.install({time:new Date('2030-01-01T23:50:00+01:00')});
        await page.goto(`http://127.0.0.1:${server.address().port}/`);
        await page.waitForSelector('.progress-fill');
        await page.evaluate(() => {
          window.cardsBefore = [...grid.children];
          window.focusedBefore = grid.querySelector('[data-program-start]'); focusedBefore.focus();
          window.progressBefore = grid.querySelector('.progress-fill').style.width;
        });
        await page.clock.fastForward(60000);
        assert.deepEqual(await page.evaluate(() => ({retained:cardsBefore.every((card, index) => grid.children[index] === card),
          focus:document.activeElement === focusedBefore, progress:grid.querySelector('.progress-fill').style.width !== progressBefore})),
          {retained:true, focus:true, progress:true});
        assert.equal(await page.evaluate(() => {
          guide.channels[0].programs[0].title = 'Changed'; render();
          return grid.children[0] !== cardsBefore[0] && cardsBefore.slice(1).every((card, index) => grid.children[index + 1] === card);
        }), true, 'One changed channel must not rebuild the others');
        await page.clock.fastForward(20 * 60 * 1000);
        assert.equal(await page.locator('.program.current').count(), 120);
        assert.equal(await page.locator('.program.current strong').first().textContent(), 'After midnight');
        assert.equal(await page.evaluate(() => dateKey(TVGuideCore.targetForMode('now', new Date('2030-01-01T00:00:00+01:00'), null))), '2030-01-02');
        assert.equal(await page.evaluate(() => dateKey(TVGuideCore.targetForMode('2015', new Date('2030-01-01T00:00:00+01:00'), null))), '2030-01-01');

        refreshRunning = true;
        await page.evaluate(() => loadGuide());
        await page.evaluate(() => { Object.defineProperty(document, 'hidden', {configurable:true, value:true}); document.dispatchEvent(new Event('visibilitychange')); });
        const before = guideRequests;
        refreshRunning = false;
        await page.evaluate(() => { Object.defineProperty(document, 'hidden', {configurable:true, value:false}); document.dispatchEvent(new Event('visibilitychange')); });
        await page.waitForFunction(() => guide.refresh_running === false);
        assert.equal(guideRequests, before + 1, 'A quick return must resume an interrupted refresh');
        assert.deepEqual(errors, []);
        console.log(`${engine}: 120-channel focus/DOM retention, isolated updates, midnight rollover and interrupted refresh passed`);
      } finally { await browser.close(); }
    }
  } finally { await new Promise(resolve => server.close(resolve)); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
