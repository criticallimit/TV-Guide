const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path');
const {chromium, webkit} = require('playwright');
const root = path.resolve(__dirname, '../www');

async function main() {
  for (const [engine, type] of [['chromium', chromium], ['webkit', webkit]]) {
    const browser = await type.launch();
    try {
      const page = await browser.newPage();
      const errors = []; page.on('pageerror', error => errors.push(error.message));
      await page.route('http://tv-guide.test/**', async route => {
        const pathname = new URL(route.request().url()).pathname;
        if (pathname.startsWith('/api/')) return route.fulfill({json:pathname.endsWith('/guide')
          ? {country:'de', channels:[], main_channel_ids:[], custom_channel_ids:[], ui:{language:'en'}, refresh_running:false}
          : {bookmarks:[], reminders:[], ok:true}});
        const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
        if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) return route.fulfill({status:404, body:''});
        await route.fulfill({body:fs.readFileSync(file), contentType:file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : 'text/html'});
      });
      await page.goto('http://tv-guide.test/');
      await page.waitForFunction(() => !!guide);
      await page.evaluate(() => {
        window.pending = [];
        const originalFetch = window.fetch;
        window.fetch = (url, options) => {
          const pathname = new URL(url, location.href).pathname;
          if (['/api/settings', '/api/notification-services', '/api/personal-channels'].includes(pathname)) {
            return new Promise(resolve => pending.push({pathname, resolve:(payload, status = 200) =>
              resolve(new Response(JSON.stringify(payload), {status, headers:{'Content-Type':'application/json'}}))}));
          }
          return originalFetch(url, options);
        };
        window.latestSettings = {country:'se', language:'en', columns_desktop:4, notification_service:'notify.latest'};
        window.oldSettings = {country:'dk', language:'fr', columns_desktop:5, notification_service:'notify.old'};
      });

      // An earlier settings response or failure must not alter a reopened dialog.
      for (const status of [200, 500]) {
        await page.evaluate(() => { pending = []; window.oldOpen = openAppSettings(); });
        await page.waitForFunction(() => pending.length === 1);
        await page.evaluate(() => { appSettingsDialog.close(); window.newOpen = openAppSettings(); });
        await page.waitForFunction(() => pending.length === 2);
        await page.evaluate(() => pending[1].resolve(latestSettings));
        await page.waitForFunction(() => pending.length === 3);
        await page.evaluate(() => pending[2].resolve({services:[]}));
        await page.waitForFunction(() => !saveAppSettings.disabled);
        await page.evaluate(status => { settingColumns.value = '6'; pending[0].resolve(oldSettings, status); }, status);
        await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
        assert.deepEqual(await page.evaluate(() => ({columns:settingColumns.value, country:settingCountry.value,
          language:document.documentElement.lang, status:appSettingsStatus.textContent})),
          {columns:'6', country:'se', language:'en', status:''}, 'Old settings request overwrote a newer dialog');
        await page.evaluate(() => appSettingsDialog.close());
      }

      // A late receiver list must not change the new dialog's selected recipient.
      for (const status of [200, 500]) {
        await page.evaluate(() => { pending = []; openAppSettings(); });
        await page.waitForFunction(() => pending.length === 1);
        await page.evaluate(() => pending[0].resolve(oldSettings));
        await page.waitForFunction(() => pending.length === 2);
        await page.evaluate(() => { appSettingsDialog.close(); openAppSettings(); });
        await page.waitForFunction(() => pending.length === 3);
        await page.evaluate(() => pending[2].resolve(latestSettings));
        await page.waitForFunction(() => pending.length === 4);
        await page.evaluate(() => pending[3].resolve({services:[{service:'notify.chosen', label:'Chosen'}]}));
        await page.waitForFunction(() => !saveAppSettings.disabled);
        await page.evaluate(status => { settingNotificationService.value = 'notify.chosen'; pending[1].resolve({services:[]}, status); }, status);
        await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
        assert.equal(await page.evaluate(() => settingNotificationService.value), 'notify.chosen');
        await page.evaluate(() => appSettingsDialog.close());
      }
      // Completion of an old save must not close or re-enable a reopened dialog.
      for (const status of [200, 500]) {
        await page.evaluate(() => { pending = []; openAppSettings(); });
        await page.waitForFunction(() => pending.length === 1);
        await page.evaluate(() => pending[0].resolve(latestSettings));
        await page.waitForFunction(() => pending.length === 2);
        await page.evaluate(() => pending[1].resolve({services:[]}));
        await page.waitForFunction(() => !saveAppSettings.disabled);
        await page.evaluate(() => { window.saveAttempt = persistAppSettings(); appSettingsDialog.close(); openAppSettings(); });
        await page.waitForFunction(() => pending.length === 4);
        await page.evaluate(() => pending[3].resolve(latestSettings));
        await page.waitForFunction(() => pending.length === 5);
        await page.evaluate(() => pending[4].resolve({services:[]}));
        await page.waitForFunction(() => !saveAppSettings.disabled);
        await page.evaluate(status => { settingColumns.value = '6'; pending[2].resolve({ok:status === 200, error:'Old save failed'}, status); }, status);
        await page.evaluate(() => saveAttempt);
        await page.waitForTimeout(550);
        assert.deepEqual(await page.evaluate(() => ({open:appSettingsDialog.open, columns:settingColumns.value,
          disabled:saveAppSettings.disabled, status:appSettingsStatus.textContent})),
          {open:true, columns:'6', disabled:false, status:''});
        await page.evaluate(() => appSettingsDialog.close());
      }

      // Even a close timer scheduled before reopening belongs to the old dialog.
      await page.evaluate(() => { pending = []; openAppSettings(); });
      await page.waitForFunction(() => pending.length === 1);
      await page.evaluate(() => pending[0].resolve(latestSettings));
      await page.waitForFunction(() => pending.length === 2);
      await page.evaluate(() => pending[1].resolve({services:[]}));
      await page.waitForFunction(() => !saveAppSettings.disabled);
      await page.evaluate(async () => {
        const save = persistAppSettings(); pending[2].resolve({ok:true}); await save;
        appSettingsDialog.close(); openAppSettings();
      });
      await page.waitForTimeout(550);
      assert.equal(await page.evaluate(() => appSettingsDialog.open), true, 'A previously scheduled close must not close a new dialog');
      assert.equal(await page.evaluate(() => saveAppSettings.disabled), true, 'Old save must not enable a new dialog that is still loading');
      await page.evaluate(() => { appSettingsDialog.close(); pending[3].resolve(latestSettings); });

      // The channel picker already guards successful responses; guard errors too.
      await page.evaluate(() => { pending = []; openChannelSettings(); });
      await page.waitForFunction(() => pending.length === 1);
      await page.evaluate(() => { channelSettingsDialog.close(); openChannelSettings(); });
      await page.waitForFunction(() => pending.length === 2);
      await page.evaluate(() => pending[1].resolve({channels:[], order:[], countries:['se'], supported_countries:[{code:'se', name:'Schweden'}]}));
      await page.waitForFunction(() => !saveChannelSettings.disabled);
      await page.evaluate(() => pending[0].resolve({}, 500));
      await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
      assert.equal(await page.evaluate(() => channelSettingsStatus.textContent), '');
      await page.evaluate(() => channelSettingsDialog.close());
      assert.deepEqual(errors, []);
      console.log(`${engine}: stale settings and receiver responses cannot overwrite reopened dialogs`);
    } finally { await browser.close(); }
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
