const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium, webkit} = require('playwright');
const root = path.resolve(__dirname, '../www');
const script = fs.readFileSync(path.resolve(__dirname, '../lovelace/tv-guide-card.js'), 'utf8');

async function main() {
  for (const [engine, type] of [['chromium', chromium], ['webkit', webkit]]) {
    const browser = await type.launch(engine === 'chromium' && process.env.TVGUIDE_EDGE_PATH ? {executablePath:process.env.TVGUIDE_EDGE_PATH} : {});
    try {
      const page = await browser.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.addInitScript(() => {
        window.themeMessages = [];
        window.addEventListener('message', event => {
          if (event.data?.type === 'tv-guide-theme') window.themeMessages.push(event.data);
        });
      });
      await page.route('http://tv-guide.test/**', async route => {
        const pathname = new URL(route.request().url()).pathname;
        if (pathname === '/') return route.fulfill({contentType:'text/html', body:'<!doctype html><body></body>'});
        if (pathname.includes('/api/')) return route.fulfill({json:pathname.endsWith('/guide')
          ? {country:'de', channels:[], main_channel_ids:[], custom_channel_ids:[], ui:{theme_mode:'auto'}, refresh_running:false}
          : {bookmarks:[], reminders:[]}});
        const file = path.resolve(root, '.' + pathname.replace(/^\/guide/, '').replace(/\/$/, '/index.html'));
        if (!file.startsWith(root + path.sep) || !fs.existsSync(file)) return route.fulfill({status:404, body:''});
        return route.fulfill({body:fs.readFileSync(file), contentType:file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : file.endsWith('.html') ? 'text/html' : 'application/octet-stream'});
      });
      await page.goto('http://tv-guide.test/');
      await page.addScriptTag({content:script});
      await page.evaluate(() => {
        window.activeTimers = new Set();
        window.timerCallbacks = new Map();
        const start = window.setInterval.bind(window), stop = window.clearInterval.bind(window);
        window.setInterval = (...args) => { const id = start(...args); activeTimers.add(id); timerCallbacks.set(id, args[0]); return id; };
        window.clearInterval = id => { activeTimers.delete(id); timerCallbacks.delete(id); stop(id); };
        window.host = document.createElement('div');
        host.style.setProperty('--primary-background-color', '#ffffff');
        document.body.append(host);
        window.mount = host.attachShadow({mode:'open'});
        window.info = {version:'1', state:'started', ingress_url:'/guide/'};
        window.hass = {themes:{theme:'default', darkMode:false, themes:{}}, panels:{tv_guide:{}},
          callWS:async request => request.endpoint === '/ingress/session' ? {session:'valid'} : info};
        window.card = document.createElement('tv-guide-card');
        card.setConfig({height:700}); card.hass = hass; mount.append(card);
      });
      await page.waitForFunction(() => card._iframe?.style.opacity === '1');
      const frame = page.frames().find(frame => frame.url().includes('/guide/'));
      assert.equal(await frame.locator('html').getAttribute('data-ha-theme'), 'light');
      await page.evaluate(() => host.style.setProperty('--primary-background-color', '#111111'));
      await frame.waitForFunction(() => document.documentElement.dataset.haTheme === 'dark');
      await page.evaluate(() => host.style.setProperty('--lovelace-background', 'rgb(200, 0, 0)'));
      await frame.waitForFunction(() => getComputedStyle(document.body).backgroundColor === 'rgb(200, 0, 0)');
      await page.evaluate(() => host.style.removeProperty('--lovelace-background'));
      await frame.waitForFunction(() => document.documentElement.style.getPropertyValue('--lovelace-background') === '');
      assert.equal(await frame.locator('body').evaluate(node => getComputedStyle(node).backgroundColor), 'rgb(17, 19, 24)');
      const before = await frame.evaluate(() => themeMessages.length);
      await page.evaluate(async () => {
        for (let i = 0; i < 20; i++) card.hass = {...hass};
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      });
      assert.equal(await frame.evaluate(() => themeMessages.length), before, 'Identical hass updates must not resend the theme');
      await page.evaluate(() => {
        card.hass = {...hass, themes:{...hass.themes, themes:{Bright:{'primary-background-color':'#ffffff'}}}};
        card.setConfig({theme:'Bright'});
      });
      await frame.waitForFunction(() => document.documentElement.dataset.haTheme === 'light');
      await page.evaluate(() => card.setConfig({}));
      await frame.waitForFunction(() => document.documentElement.dataset.haTheme === 'dark');
      for (const mode of ['light', 'dark', 'auto']) {
        await frame.evaluate(mode => { guide.ui.theme_mode = mode; syncHomeAssistantTheme(); }, mode);
        assert.equal(await frame.locator('html').getAttribute('data-ha-theme'), mode === 'auto' ? 'dark' : mode);
        assert.equal(await frame.evaluate(() => sessionStorage.getItem('tv-guide-dashboard-display-mode')), mode);
      }
      await page.evaluate(() => card.remove());
      assert.deepEqual(await page.evaluate(() => ({timers:activeTimers.size, observer:card._themeObserver, frame:card._themeSyncFrame, retry:card._themeRetryTimer, listening:card._themeReadyListening})),
        {timers:0, observer:null, frame:null, retry:null, listening:false});

      // Removing before either Supervisor response arrives must not resurrect the card or its cookie.
      await page.evaluate(() => {
        window.pending = [];
        window.stale = document.createElement('tv-guide-card'); stale.setConfig({});
        stale.hass = {...hass, callWS:request => new Promise(resolve => pending.push({request, resolve}))};
        mount.append(stale);
      });
      await page.waitForFunction(() => pending.length === 2);
      const cookiesBeforeDisconnect = await page.context().cookies();
      const detached = await page.evaluate(async () => {
        stale.remove();
        for (const task of pending) task.resolve(task.request.endpoint === '/ingress/session' ? {session:'stale'} : info);
        await new Promise(resolve => setTimeout(resolve, 0));
        return {iframe:stale._iframe, timers:activeTimers.size, session:stale._session};
      });
      assert.deepEqual(detached, {iframe:null, timers:0, session:''});
      assert.deepEqual(await page.context().cookies(), cookiesBeforeDisconnect, 'Detached start must not overwrite the ingress cookie');

      // Both a late success and a late failure from the previous connection must be ignored.
      for (const fail of [false, true]) {
        await page.evaluate(() => {
          window.oldResponse = null;
          window.racing = document.createElement('tv-guide-card'); racing.setConfig({});
          racing.hass = {...hass, callWS:request => request.endpoint === '/ingress/session'
            ? Promise.resolve({session:'old'}) : new Promise((resolve, reject) => { oldResponse = {resolve, reject}; })};
          mount.append(racing);
        });
        await page.waitForFunction(() => !!oldResponse);
        await page.evaluate(() => { racing.remove(); racing.hass = hass; mount.append(racing); });
        await page.waitForFunction(() => racing._iframe?.style.opacity === '1');
        const result = await page.evaluate(async fail => {
          const iframe = racing._iframe;
          if (fail) oldResponse.reject(new Error('late failure')); else oldResponse.resolve(info);
          await new Promise(resolve => setTimeout(resolve, 0));
          const result = {sameFrame:racing._iframe === iframe, timers:activeTimers.size};
          racing.remove(); return result;
        }, fail);
        assert.deepEqual(result, {sameFrame:true, timers:1});
      }
      // A failed add-on-info request must invalidate its still-pending session.
      const cookiesBeforeFailure = await page.context().cookies();
      await page.evaluate(() => {
        window.pendingSession = null;
        window.rejectInfo = null;
        window.failed = document.createElement('tv-guide-card'); failed.setConfig({});
        failed.hass = {...hass, callWS:request => request.endpoint === '/ingress/session'
          ? new Promise(resolve => { pendingSession = resolve; })
          : new Promise((resolve, reject) => { rejectInfo = reject; })};
        mount.append(failed);
      });
      await page.waitForFunction(() => !!pendingSession && !!rejectInfo);
      await page.evaluate(() => rejectInfo(new Error('Add-on info unavailable')));
      await page.waitForFunction(() => failed._started === false);
      const failedState = await page.evaluate(async () => {
        pendingSession({session:'failed-start-session'});
        await new Promise(resolve => setTimeout(resolve, 0));
        return {iframe:failed._iframe, timers:activeTimers.size, session:failed._session};
      });
      assert.deepEqual(failedState, {iframe:null, timers:0, session:''});
      assert.deepEqual(await page.context().cookies(), cookiesBeforeFailure, 'Late session must not overwrite the ingress cookie');
      await page.evaluate(() => { failed.hass = hass; });
      await page.waitForFunction(() => failed._iframe?.style.opacity === '1');
      assert.equal(await page.evaluate(() => activeTimers.size), 1, 'Failed start must remain retryable');
      await page.evaluate(() => failed.remove());

      // Slow validation and renewal must not overlap subsequent interval ticks.
      await page.evaluate(() => {
        window.renewing = document.createElement('tv-guide-card'); renewing.setConfig({});
        renewing.hass = hass; mount.append(renewing);
      });
      await page.waitForFunction(() => renewing._iframe?.style.opacity === '1');
      await page.evaluate(async () => {
        window.renewalRequests = [];
        renewing.hass = {...hass, callWS:request => new Promise((resolve, reject) => renewalRequests.push({request, resolve, reject}))};
        window.keepAliveTick = timerCallbacks.get(renewing._sessionTimer);
        window.firstValidation = keepAliveTick();
        window.secondValidation = keepAliveTick();
      });
      assert.equal(await page.evaluate(() => renewalRequests.length), 1, 'Pending validation must prevent overlapping ticks');
      await page.evaluate(() => renewalRequests[0].reject(new Error('Session expired')));
      await page.waitForFunction(() => renewalRequests.length === 2);
      assert.equal(await page.evaluate(() => renewalRequests[1].request.endpoint), '/ingress/session');
      await page.evaluate(() => keepAliveTick());
      assert.equal(await page.evaluate(() => renewalRequests.length), 2, 'Pending renewal must prevent another validation');
      await page.evaluate(async () => { renewalRequests[1].resolve({session:'renewed'}); await firstValidation; });
      await page.evaluate(() => { window.nextValidation = keepAliveTick(); });
      assert.equal(await page.evaluate(() => renewalRequests[2].request.data.session), 'renewed', 'Next validation must use the renewed session');
      await page.evaluate(async () => { renewalRequests[2].resolve({}); await nextValidation; });
      await page.evaluate(() => { window.failedRenewal = keepAliveTick(); renewalRequests[3].reject(new Error('Expired again')); });
      await page.waitForFunction(() => renewalRequests.length === 5);
      await page.evaluate(async () => { renewalRequests[4].reject(new Error('Supervisor unavailable')); await failedRenewal; });
      await page.evaluate(() => { window.lastValidation = keepAliveTick(); });
      assert.equal(await page.evaluate(() => renewalRequests.length), 6, 'Failed renewal must release the pending guard');
      await page.evaluate(() => renewalRequests[5].reject(new Error('Expired before disconnect')));
      await page.waitForFunction(() => renewalRequests.length === 7);
      await page.evaluate(() => { renewing.remove(); renewing.hass = hass; mount.append(renewing); });
      await page.waitForFunction(() => renewing._iframe?.style.opacity === '1');
      const cookiesBeforeLateRenewal = await page.context().cookies();
      await page.evaluate(async () => { renewalRequests[6].resolve({session:'obsolete-renewal'}); await lastValidation; });
      assert.deepEqual(await page.context().cookies(), cookiesBeforeLateRenewal, 'Renewal from a previous connection must not overwrite its replacement');
      assert.equal(await page.evaluate(() => activeTimers.size), 1);
      await page.evaluate(() => renewing.remove());
      assert.equal(await page.evaluate(() => activeTimers.size), 0);
      assert.deepEqual(errors, []);
      console.log(`${engine}: real iframe handshake, inherited themes, removed variables, deduplication and pending-start cleanup passed`);
    } finally { await browser.close(); }
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
