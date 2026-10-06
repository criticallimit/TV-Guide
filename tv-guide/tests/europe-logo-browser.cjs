// Exercise the actual logo endpoint and rasterize its SVG response as an <img>.
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium, webkit} = require('playwright');

async function main() {
  const server = spawn(process.env.TVGUIDE_PYTHON || 'python', ['-u', '-c', `
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from tvguide import services as app
channels = []
for country in app.COUNTRIES:
    assets = [a for a in app.EUROPE_LOGO_LIBRARY['assets'].values() if country in a['countries']]
    for asset in assets[:2]:
        channels.append({'id': str(len(channels)), 'name': asset['brand_key'], 'source_country': country})
app.STORE = SimpleNamespace(channels=channels)
server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
print(str(server.server_port) + ' ' + str(len(channels)), flush=True)
server.serve_forever()
`], {cwd: path.resolve(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe']});
  let diagnostics = '';
  server.stderr.on('data', data => { diagnostics += data; });
  try {
    const [port, count] = await new Promise((resolve, reject) => {
      let output = '';
      const timer = setTimeout(() => reject(new Error('Logo server did not start: ' + diagnostics)), 15000);
      server.on('error', error => { clearTimeout(timer); reject(error); });
      server.on('exit', code => { clearTimeout(timer); reject(new Error('Logo server exited: ' + code + diagnostics)); });
      server.stdout.on('data', data => {
        output += data;
        const match = output.match(/^(\d+) (\d+)\r?$/m);
        if (match) { clearTimeout(timer); resolve([Number(match[1]), Number(match[2])]); }
      });
    });
    assert.ok(count >= 16, 'Expected logo coverage across supported countries');
    for (const [engine, type] of [['chromium', chromium], ['webkit', webkit]]) {
      const browser = await type.launch();
      try {
        const page = await browser.newPage();
        await page.goto(`http://127.0.0.1:${port}/api/channel-logo/0/light.svg`);
        const results = await page.evaluate(async count => {
          const results = [];
          for (let id = 0; id < count; id++) for (const theme of ['light', 'dark']) {
            const url = `/api/channel-logo/${id}/${theme}.svg`;
            const svg = await (await fetch(url)).text();
            const image = new Image(); image.src = url; await image.decode();
            const canvas = document.createElementNS('http://www.w3.org/1999/xhtml', 'canvas'); canvas.width = 260; canvas.height = 64;
            const context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
            const pixels = context.getImageData(0, 0, 260, 64).data;
            let ink = 0;
            for (let i = 3; i < pixels.length; i += 4) if (pixels[i] > 80) ink++;
            results.push({url, ink, embedded: svg.includes('href="data:image/'), external: svg.includes('../assets/')});
          }
          return results;
        }, count);
        for (const result of results) {
          assert.ok(result.embedded && !result.external, JSON.stringify(result));
          assert.ok(result.ink >= 30, JSON.stringify(result));
        }
        console.log(`${engine}: ${results.length} Europe logo API responses render visible artwork`);
      } finally { await browser.close(); }
    }
  } finally { server.kill(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
