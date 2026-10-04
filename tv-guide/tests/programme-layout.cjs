// Programme row layout and keyboard interaction regression checks.
// Test actual layout in Chromium and WebKit, including native button behavior.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium, webkit } = require('playwright');
const root = path.resolve(__dirname, '../www');
const titles = ['Helene, die wahre Braut', 'Tagesschau', 'Presseclub', 'Europamagazin',
  'Das Geheimnis der Tierwanderungen mit Dirk Steffens', 'Tagesschau', 'Zwei am großen See'];
const times = ['11:00', '12:00', '12:03', '12:45', '13:15', '14:00', '14:03'];
const referenceCSS = `
@font-face{font-family:"Source Sans Pro";src:url(/fonts/SourceSansPro-Regular.ttf);font-weight:400}
@font-face{font-family:"Source Sans Pro";src:url(/fonts/SourceSansPro-SemiBold.ttf);font-weight:500}
.reference{font-family:"Source Sans Pro",Arial,sans-serif;font-size:13px;line-height:1.5}
.ref-list{margin:0;padding:0;border:1px solid #d6d6d6;list-style:none}
.ref-item{border-bottom:1px dashed #d6d6d6;position:relative}
.ref-item:last-child{border-bottom:none}
.ref-link{padding:5px 6px;color:#000;display:block;text-decoration:none}
.ref-time{display:inline-block;margin-right:7px}
.ref-main{display:inline-block;width:100%;max-width:calc(100% - 38px);position:relative}
.ref-name,.ref-info{display:inline-block;font-weight:500;box-sizing:border-box;width:100%;vertical-align:top;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;word-break:break-all;word-wrap:break-word}
.ref-info{display:none;font-weight:400;margin-top:0}
.ref-item.first{background:#e8f6f3;border-bottom:none}
.ref-item.first .ref-link{display:flex;width:100%;min-height:49px}
.ref-item.first .ref-info{display:inline-block}
.ref-time-wrapper{margin-top:-2px;margin-bottom:-7px}
@media(min-width:1200px){.ref-time-wrapper{margin-top:0}}
.ref-item.second .ref-link{display:flex}
.ref-bar{height:6px;background:#e20613}
`;
const refRows = titles.map((title, i) => {
  const time = `<div class="ref-time">${times[i]}</div>`;
  const timeMarkup = i === 0 ? `<div class="ref-time-wrapper">${time}</div>` :
    i === 1 ? `<div>${time}</div>` : time;
  return `<li class="ref-item ${i === 0 ? 'first' : i === 1 ? 'second' : ''}"><a class="ref-link">${timeMarkup}<div class="ref-main"><div class="ref-name">${title}</div><div class="ref-info">Märchenfilm D 2020</div></div></a>${i === 0 ? '<div class="ref-bar"></div>' : ''}</li>`;
}).join('');
const fixture = `<!doctype html><html data-ha-theme="light"><meta charset="utf-8"><link rel="stylesheet" href="/styles.css"><style>${referenceCSS}body{padding:20px}.comparison{display:flex;gap:24px}.reference,.actual{width:224px;flex:none}</style><div class="comparison"><div class="reference"><ul class="ref-list">${refRows}</ul></div><div class="actual"><div class="programs" id="actual"></div></div></div><script src="/guide-core.js"></script></html>`;
async function main() {
  const server = http.createServer((req, res) => {
    if (req.url === '/') { res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.end(fixture); return; }
    const file = path.resolve(root, '.' + req.url);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : 'font/ttf');
    res.end(fs.readFileSync(file));
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${server.address().port}/`;
  const snapshots = {};
  try {
    for (const [engine, type] of [['chromium', chromium], ['webkit', webkit]]) {
      const browser = await type.launch(engine === 'chromium' && process.env.TVGUIDE_EDGE_PATH ?
        { executablePath: process.env.TVGUIDE_EDGE_PATH } : {});
      try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, timezoneId: 'Europe/Berlin' });
        await page.clock.install({ time: new Date('2030-01-01T11:30:00+01:00') });
        await page.goto(url);
        await page.evaluate(({ titles, times }) => {
          const programs = titles.map((title, i) => ({title, start:`2030-01-01T${times[i]}:00+01:00`,
            end: i < times.length - 1 ? `2030-01-01T${times[i+1]}:00+01:00` : '2030-01-01T15:30:00+01:00',
            category:'Märchenfilm D 2020'}));
          document.querySelector('#actual').innerHTML = TVGuideCore.renderPrograms({programs}, 'now', new Date(), null);
        }, { titles, times });
        await page.evaluate(() => document.fonts.ready);
        for (const width of [1280, 1024]) {
          await page.setViewportSize({ width, height: 720 });
          for (const theme of ['light', 'dark']) {
          await page.evaluate(theme => document.documentElement.dataset.haTheme = theme, theme);
          const data = await page.evaluate(() => {
            const measure = selector => Array.from(document.querySelectorAll(selector)).map(row => {
              const box = row.getBoundingClientRect();
              const time = row.querySelector('.program-time,.ref-time').getBoundingClientRect();
              const title = row.querySelector('strong,.ref-name').getBoundingClientRect();
              return {height:box.height,timeTop:time.top-box.top,titleTop:title.top-box.top,
                timeLeft:time.left-box.left,titleLeft:title.left-box.left,titleHeight:title.height};
            });
            return {actual:measure('.actual .program'),reference:measure('.reference .ref-item')};
          });
          assert.equal(data.actual.length, 7);
          for (let i = 0; i < 7; i++) {
            for (const key of ['height','timeTop','titleTop','timeLeft','titleLeft','titleHeight']) {
              assert.ok(Math.abs(data.actual[i][key] - data.reference[i][key]) < 1.1,
                `${engine} ${width}px row ${i} ${key}: actual ${data.actual[i][key]}, TV guide ${data.reference[i][key]}`);
            }
          }
          assert.ok(data.actual[0].height >= 55 && data.actual[1].height < 35);
          snapshots[`${engine}-${width}`] = data.actual;
          }
        }
        const button = page.locator('.program-link').first();
        await button.evaluate(el => {el.addEventListener('click', () => window.detailOpened = true);});
        await button.focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.evaluate(() => window.detailOpened), true);
        await button.evaluate(el => el.blur());
        await page.setViewportSize({width:1280,height:720});
        if (process.env.TVGUIDE_SCREENSHOT_DIR) {
          fs.mkdirSync(process.env.TVGUIDE_SCREENSHOT_DIR,{recursive:true});
          await page.screenshot({path:path.join(process.env.TVGUIDE_SCREENSHOT_DIR,`${engine}-layout-comparison.png`)});
        }
        console.log(`${engine}: TV guide row geometry and keyboard interaction passed`);
      } finally { await browser.close(); }
    }
    for (const width of [1280,1024]) for (let i=0;i<7;i++) {
      assert.ok(Math.abs(snapshots[`chromium-${width}`][i].height - snapshots[`webkit-${width}`][i].height) < 1.1);
    }
  } finally { await new Promise(resolve => server.close(resolve)); }
}
main().catch(error => {console.error(error);process.exitCode=1;});
