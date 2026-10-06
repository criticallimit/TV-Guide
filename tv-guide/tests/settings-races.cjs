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
          if (['/api/settings', '/api/notification-services', '/api/personal-channels', '/api/bookmarks', '/api/reminders'].includes(pathname)) {
            return new Promise(resolve => pending.push({pathname, resolve:(payload, status = 200) =>
              resolve(new Response(JSON.stringify(payload), {status, headers:{'Content-Type':'application/json'}}))}));
          }
          return originalFetch(url, options);
        };
        window.latestSettings = {country:'se', language:'en', columns_desktop:4, notification_service:'notify.latest'};
        window.oldSettings = {country:'dk', language:'fr', columns_desktop:5, notification_service:'notify.old'};
        localStorage.setItem('tvguide-bookmarks-migrated', '1');
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
      // Saves and resets also belong to the dialog instance that initiated them.
      for (const reset of [false, true]) {
        for (const status of [200, 500]) {
          await page.evaluate(() => { pending = []; openChannelSettings(); });
          await page.waitForFunction(() => pending.length === 1);
          await page.evaluate(() => pending[0].resolve({channels:[], order:[], countries:['de'], supported_countries:[]}));
          await page.waitForFunction(() => !saveChannelSettings.disabled);
          await page.evaluate(reset => {
            window.channelSave = persistChannelSettings(reset);
            channelSettingsDialog.close(); openChannelSettings();
          }, reset);
          await page.waitForFunction(() => pending.length === 3);
          await page.evaluate(status => pending[1].resolve({ok:status === 200, error:'Old channel save failed'}, status), status);
          await page.evaluate(() => channelSave);
          assert.deepEqual(await page.evaluate(() => ({open:channelSettingsDialog.open,
            save:saveChannelSettings.disabled, reset:resetChannelSettings.disabled, status:channelSettingsStatus.textContent})),
            {open:true, save:true, reset:true, status:'Loading channel list …'}, 'Old channel save affected a new loading dialog');
          await page.evaluate(() => { channelSettingsDialog.close(); pending[2].resolve({channels:[], order:[], countries:[], supported_countries:[]}); });
        }
      }
      // A reset's follow-up GET may arrive after the picker has been reopened.
      for (const status of [200, 500]) {
        await page.evaluate(() => { pending = []; openChannelSettings(); });
        await page.waitForFunction(() => pending.length === 1);
        await page.evaluate(() => pending[0].resolve({channels:[], order:[], countries:['de'], supported_countries:[]}));
        await page.waitForFunction(() => !saveChannelSettings.disabled);
        await page.evaluate(() => { window.channelReset = persistChannelSettings(true); pending[1].resolve({ok:true}); });
        await page.waitForFunction(() => pending.length === 3);
        await page.evaluate(() => { channelSettingsDialog.close(); openChannelSettings(); });
        await page.waitForFunction(() => pending.length === 4);
        await page.evaluate(() => pending[3].resolve({channels:[], order:[], countries:['se'], supported_countries:[{code:'se', name:'Sweden'}]}));
        await page.waitForFunction(() => !saveChannelSettings.disabled);
        const selection = await page.evaluate(() => channelPicker.value());
        await page.evaluate(status => pending[2].resolve({channels:[], order:[], countries:['de'], supported_countries:[]}, status), status);
        await page.evaluate(() => channelReset);
        assert.deepEqual(await page.evaluate(() => channelPicker.value()), selection, 'Old reset overwrote the reopened picker');
        assert.equal(await page.evaluate(() => channelSettingsStatus.textContent), '');
        await page.evaluate(() => channelSettingsDialog.close());
      }
      // Background reads must not undo a newer successful write or read.
      for (const kind of ['bookmarks', 'reminders']) {
        for (const duringSave of [false, true]) {
          await page.evaluate(({kind, duringSave}) => {
            pending = [];
            activeDetail = {channel:{id:'test', name:'Test'}, program:{title:'Programme', start:'2030-01-01T20:00:00+01:00', end:'2030-01-01T21:00:00+01:00'}};
            const read = () => kind === 'bookmarks' ? loadBookmarksRemote() : loadReminders();
            const save = () => kind === 'bookmarks' ? syncBookmark('remove', {id:'obsolete'}) : saveReminderForActiveDetail(false, 10);
            if (duringSave) { window.listSave = save(); window.listRead = read(); }
            else { window.listRead = read(); window.listSave = save(); }
          }, {kind, duringSave});
          const saveIndex = duringSave ? 0 : 1, readIndex = duringSave ? 1 : 0;
          await page.evaluate(({kind, saveIndex}) => pending[saveIndex].resolve({ok:true, [kind]:[]}), {kind, saveIndex});
          await page.evaluate(() => listSave);
          await page.evaluate(({kind, readIndex}) => pending[readIndex].resolve({[kind]:[{id:'obsolete'}]}), {kind, readIndex});
          await page.evaluate(() => listRead);
          assert.deepEqual(await page.evaluate(kind => kind === 'bookmarks' ? bookmarks : reminders, kind), [], `${kind}: old GET undid a successful deletion`);
        }
        await page.evaluate(kind => {
          pending = [];
          const read = () => kind === 'bookmarks' ? loadBookmarksRemote() : loadReminders();
          window.firstRead = read(); window.secondRead = read();
        }, kind);
        await page.evaluate(kind => pending[1].resolve({[kind]:[{id:'latest'}]}), kind);
        await page.evaluate(() => secondRead);
        await page.evaluate(kind => pending[0].resolve({[kind]:[{id:'old'}]}), kind);
        await page.evaluate(() => firstRead);
        assert.equal(await page.evaluate(kind => (kind === 'bookmarks' ? bookmarks : reminders)[0].id, kind), 'latest');
        await page.evaluate(kind => {
          pending = [];
          window.failedRead = kind === 'bookmarks' ? loadBookmarksRemote() : loadReminders();
          pending[0].resolve({}, 500);
        }, kind);
        await page.evaluate(() => failedRead);
        assert.equal(await page.evaluate(kind => (kind === 'bookmarks' ? bookmarks : reminders)[0]?.id, kind), 'latest', 'A failed refresh must retain known saved entries');
      }
      // Removing a bookmark also removes its reminder and invalidates older reminder reads.
      await page.evaluate(() => {
        pending = [];
        const id = bookmarkId(activeDetail.channel, activeDetail.program);
        bookmarks = [{id, ...activeDetail.program}]; reminders = [{id, minutes:10}];
        window.reminderRead = loadReminders(); window.bookmarkRemoval = toggleBookmark();
        pending[1].resolve({ok:true, bookmarks:[]});
      });
      await page.evaluate(() => bookmarkRemoval);
      await page.evaluate(() => pending[0].resolve({reminders:[{id:bookmarkId(activeDetail.channel, activeDetail.program), minutes:10}]}));
      await page.evaluate(() => reminderRead);
      assert.deepEqual(await page.evaluate(() => reminders), []);
      assert.equal(await page.evaluate(() => reminderEnabled.checked), false);

      // Importing browser-only bookmarks must still preserve them if a write fails.
      for (const status of [200, 500]) {
        await page.evaluate(() => {
          pending = [];
          window.legacy = {id:'legacy', title:'Legacy', start:'2030-01-01T20:00:00+01:00', end:'2030-01-01T21:00:00+01:00'};
          bookmarks = [legacy]; saveBookmarksLocal();
          localStorage.removeItem('tvguide-bookmarks-migrated');
          window.importRead = loadBookmarksRemote(); pending[0].resolve({bookmarks:[]});
        });
        await page.waitForFunction(() => pending.length === 2);
        await page.evaluate(status => pending[1].resolve({ok:status === 200, bookmarks:[legacy], error:'Import failed'}, status), status);
        await page.evaluate(() => importRead);
        assert.equal(await page.evaluate(() => bookmarks[0]?.id), 'legacy');
        assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('tvguide-bookmarks'))[0]?.id), 'legacy');
        assert.equal(await page.evaluate(() => localStorage.getItem('tvguide-bookmarks-migrated')), status === 200 ? '1' : null);
      }
      assert.deepEqual(errors, []);
      console.log(`${engine}: stale dialog and saved-list responses, failed refreshes and bookmark migration passed`);
    } finally { await browser.close(); }
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
