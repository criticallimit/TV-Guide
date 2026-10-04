// Exercise actual translated controls and settings layout in both browser engines.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium,webkit} = require('playwright');
const root = path.resolve(__dirname,'../www');
async function main() {
 const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':'font/ttf');
  res.end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try {
  for(const [engine,type] of [['chromium',chromium],['webkit',webkit]]) {
   const browser=await type.launch(engine==='chromium'&&process.env.TVGUIDE_EDGE_PATH?{executablePath:process.env.TVGUIDE_EDGE_PATH}:{});
   try {
    for(const width of [1280,390]) {
     const page=await browser.newPage({viewport:{width,height:820},timezoneId:'Europe/Berlin'});
     page.setDefaultTimeout(12000);
     const errors=[];page.on('pageerror',error=>errors.push(error.message));
     let settings={country:'ch',language:'auto',default_view:'now',columns_desktop:5,max_channels:0,theme_mode:width===1280?'dark':'light',refresh_minutes:180,notification_service:'persistent_notification.create',home_assistant:{language:'de',country:'CH'}};
     await page.addInitScript(()=>{window.hass={locale:{language:'fr-CH'}};});
     await page.route('**/api/**',async route=>{
      const api=new URL(route.request().url()).pathname;
      let data={ok:true};
      if(api==='/api/settings') {
       if(route.request().method()==='POST') settings={...settings,...route.request().postDataJSON()};
       else data=settings;
      } else if(api==='/api/guide') {
       const now=new Date(),start=new Date(now.getTime()-600000).toISOString(),end=new Date(now.getTime()+3600000).toISOString();
       const channels=[{id:'ch_srf1',name:'SRF 1',programs:[{title:'Tagesschau',desc:'Die Nachrichten bleiben im Original.',start,end}]}];
       data={country:settings.country,channels,main_channel_ids:['ch_srf1'],custom_channel_ids:[],ui:settings,refresh_running:false};
      } else if(api==='/api/bookmarks') data={bookmarks:[]};
      else if(api==='/api/reminders') data={reminders:[]};
      else if(api==='/api/notification-services') data={services:[{service:'persistent_notification.create',type:'home_assistant',label:'Home Assistant'}]};
      await route.fulfill({json:data});
     });
     await page.goto(`http://127.0.0.1:${server.address().port}/index.html`,{waitUntil:"domcontentloaded",timeout:60000});
     await page.locator('.program-link').first().waitFor();
     assert.equal(await page.locator('html').getAttribute('lang'),'fr','Profile language must override installation language');
     for(const language of ['en','nl','fr','it','de']) {
      console.log(engine,width,language);
      await page.locator('#showAppSettings').click();
      await page.waitForFunction(()=>!document.querySelector('#saveAppSettings').disabled);
      await page.locator('.settings-disclosure summary').first().click();
      await page.locator('#settingLanguage').selectOption(language);
      await page.locator('#saveAppSettings').click();
      await page.waitForFunction(()=>!document.querySelector('#appSettingsDialog').open);
      assert.equal(await page.locator('html').getAttribute('lang'),language);
      assert.equal(settings.country,'ch','Language must not change channel country');
      assert.equal(await page.locator('.program-link strong').first().textContent(),'Tagesschau');
      await page.locator('#showAppSettings').click();
      await page.waitForFunction(()=>!document.querySelector('#saveAppSettings').disabled);
      const translated=await page.evaluate(()=>Array.from(document.querySelectorAll('#appSettingsDialog [data-i18n]')).every(node=>node.textContent===TVGuideI18n.t(node.dataset.i18n)));
      assert.equal(translated,true);
      assert.equal(await page.locator('.settings-disclosure').count(),5);
      assert.equal(await page.locator('.settings-disclosure[open]').count(),0);
      for (let section=0;section<3;section++) {
       const summary=page.locator('.settings-disclosure summary').nth(section);
       await summary.focus();
       await page.keyboard.press('Enter');
      }
      assert.equal(await page.locator('.settings-disclosure[open]').count(),3);
      const fields=await page.evaluate(()=>['settingCountry','settingLanguage','settingDefaultView','settingTheme','settingColumns','settingMaxChannels','settingNotificationService'].map(id=>{
       const box=document.getElementById(id).getBoundingClientRect();return {id,height:box.height,top:box.top,width:box.width};
      }));
      for(const field of fields) assert.equal(field.height,44,field.id+' field height');
      if(width>720) for(const [left,right] of [[0,1],[2,3],[4,5]]) {
       assert.ok(Math.abs(fields[left].top-fields[right].top)<1,'Controls in a row must align');
       assert.ok(Math.abs(fields[left].width-fields[right].width)<1,'Controls must have equal widths');
      }
      const geometry=await page.locator('#appSettingsDialog').evaluate(dialog=>({width:dialog.clientWidth,content:dialog.scrollWidth,screen:window.innerWidth}));
      assert.ok(geometry.content<=geometry.width+1,`${engine}/${width}/${language}: horizontal overflow`);
      assert.ok(geometry.width<=geometry.screen);
      if(process.env.TVGUIDE_SCREENSHOT_DIR&&((width===1280&&language==='en')||(width===390&&language==='nl'))) {
       await page.screenshot({path:path.join(process.env.TVGUIDE_SCREENSHOT_DIR,`${engine}-settings-${language}-${width}.png`)});
      }
      const advanced=page.locator('.settings-disclosure').last();
      await advanced.locator('summary').click();
      assert.equal(await advanced.evaluate(el=>el.open),true);
      await page.locator('#appSettingsDialog').evaluate(dialog=>dialog.scrollTop=dialog.scrollHeight);
      const save=await page.locator('#saveAppSettings').boundingBox();
      assert.ok(save.y>=0&&save.y+save.height<=820,'Save must remain visible while scrolling');
      await advanced.locator('summary').click();
      await page.locator('#cancelAppSettings').click();
     }
     assert.deepEqual(errors,[]);
     await page.close();
    }
    console.log(`${engine}: five UI languages, profile detection and settings desktop/mobile layout passed`);
   } finally {await browser.close();}
  }
 } finally {await new Promise(resolve=>server.close(resolve));}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
