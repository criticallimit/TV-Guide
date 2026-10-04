// Exercise the real picker and application in both engines, including mobile layouts.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium, webkit} = require('playwright');
const www = path.resolve(__dirname, '../www');
const channels = [
  {id:'ch:ch_srf1',source_channel_id:'ch_srf1',name:'SRF 1',source_country:'ch',country_name:'Schweiz'},
  {id:'de:ard',source_channel_id:'ard',name:'Das Erste',source_country:'de',country_name:'Deutschland'},
  {id:'de:rtl',source_channel_id:'rtl',name:'RTL Deutschland',source_country:'de',country_name:'Deutschland'},
  {id:'ch:ch_rtl',source_channel_id:'ch_rtl',name:'RTL Schweiz',source_country:'ch',country_name:'Schweiz'},
  {id:'at:at_orf1',source_channel_id:'at_orf1',name:'ORF 1',source_country:'at',country_name:'Österreich'},
  {id:'no:no_nrk1',source_channel_id:'no_nrk1',name:'NRK 1',source_country:'no',country_name:'Norwegen'},
  {id:'nl:nl_npo1',source_channel_id:'nl_npo1',name:'NPO 1',source_country:'nl',country_name:'Niederlande'},
  {id:'be:be_vrt1',source_channel_id:'be_vrt1',name:'VRT 1',source_country:'be',country_name:'Belgien'},
];
const supported_countries=[['ch','Schweiz'],['de','Deutschland'],['at','Österreich'],['no','Norwegen'],['nl','Niederlande'],['be','Belgien']].map(([code,name])=>({code,name}));
async function main() {
 const server=http.createServer((req,res)=>{
  const file=path.resolve(www,'.'+new URL(req.url,'http://localhost').pathname);
  if(!file.startsWith(www+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':'font/ttf');
  res.end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try {
  for(const [engine,type] of [['chromium',chromium],['webkit',webkit]]) {
   const browser=await type.launch(engine==='chromium'&&process.env.TVGUIDE_EDGE_PATH?{executablePath:process.env.TVGUIDE_EDGE_PATH}:{});
   try {
    for(const width of [1100,360,320]) {
     const page=await browser.newPage({viewport:{width,height:900},timezoneId:'Europe/Berlin',hasTouch:width===320});
     page.setDefaultTimeout(12000);
     let prefs={order:['ch:ch_srf1','de:ard','at:at_orf1'],countries:['ch','de','at']};
     let country='ch';
     const errors=[];page.on('pageerror',error=>errors.push(error.message));
     const now=new Date(),start=new Date(now.getTime()-600000).toISOString(),end=new Date(now.getTime()+3600000).toISOString();
     const programme={title:'Current programme',start,end};
     const ui={language:'de',default_view:'now',theme_mode:width===1100?'dark':'light',columns_desktop:5,max_channels:0};
     await page.route('**/api/**',async route=>{
      const request=route.request(),api=new URL(request.url()).pathname;
      let data={ok:true};
      if(api==='/api/personal-channels') {
       if(request.method()==='POST') {
        const wanted=request.postDataJSON();
        prefs=wanted.reset?{order:['ch:ch_srf1'],countries:['ch']}:wanted;
        data={ok:true,...prefs};
       } else data={...prefs,channels,country,supported_countries};
      } else if(api==='/api/guide') data={country,channels:[{id:'ch_srf1',name:'SRF 1',programs:[programme]},...channels.filter(c=>prefs.order.includes(c.id)).map(c=>({...c,programs:[programme]}))],main_channel_ids:['ch_srf1'],custom_channel_ids:prefs.order,ui,refresh_running:false};
      else if(api==='/api/bookmarks') data={bookmarks:[]};
      else if(api==='/api/reminders') data={reminders:[]};
      await route.fulfill({json:data});
     });
     await page.goto(`http://127.0.0.1:${server.address().port}/index.html`,{waitUntil:'domcontentloaded',timeout:60000});
     await page.locator('.program-link').first().waitFor();
     await page.locator('#showChannelSettings').click();
     const personal=page.locator('#channelSettingsList .channel-settings-row');
     const personalIds=()=>personal.evaluateAll(rows=>rows.map(row=>row.dataset.channelId));
     await personal.first().waitFor();
     assert.deepEqual(await personalIds(),prefs.order);
     await page.locator('#channelCountryFilters input[value=de]').uncheck();
     assert.equal(await page.locator('#availableChannelsList [data-channel-id="de:ard"]').count(),0);
     assert.deepEqual(await personalIds(),prefs.order,'Country filter removed a selected channel');
     await page.locator('#channelCountryFilters input[value=no]').check();
     await page.locator('#channelSearch').fill('NRK');
     await page.locator('#availableChannelsList [data-channel-id="no:no_nrk1"] input').check();
     await page.getByRole('button',{name:'NRK 1: Nach oben',exact:true}).click();
     assert.deepEqual(await personalIds(),['ch:ch_srf1','de:ard','no:no_nrk1','at:at_orf1']);
     await page.locator('#channelSearch').fill('');
     await page.locator('#channelCountryFilters input[value=de]').check();
     assert.equal(await page.locator('#availableChannelsList input:checked').count(),4);
     assert.equal(await page.locator('#availableChannelsList [data-channel-id="de:rtl"]').count(),1);
     assert.equal(await page.locator('#availableChannelsList [data-channel-id="ch:ch_rtl"]').count(),1);
     const bounds=await page.locator('#channelSettingsDialog').evaluate(dialog=>({dialog:dialog.getBoundingClientRect().toJSON(),overflow:dialog.scrollWidth>dialog.clientWidth,rows:[...dialog.querySelectorAll('.channel-settings-row')].map(row=>({width:row.clientWidth,scroll:row.scrollWidth}))}));
     assert.ok(!bounds.overflow,`${engine} ${width}: dialog overflow`);
     assert.ok(bounds.rows.every(row=>row.scroll<=row.width),`${engine} ${width}: row overflow`);
     assert.ok(bounds.dialog.x>=0&&bounds.dialog.right<=width,`${engine} ${width}: dialog outside viewport`);
     const legacyBookmark = await page.evaluate(() => bookmarkId({id:'de:ard',source_channel_id:'ard'}, {start:'same',title:'same'}));
     assert.equal(legacyBookmark,'ard|same|same','Existing bookmarks lost their identity');
     await page.locator('#saveChannelSettings').click();
     await page.locator('#channelSettingsDialog').waitFor({state:'hidden'});
     await page.waitForFunction(()=>document.querySelectorAll('.channel-card').length===4);
     assert.deepEqual(prefs.order,['ch:ch_srf1','de:ard','no:no_nrk1','at:at_orf1']);
     assert.equal(await page.locator('.channel-card').count(),4);
     await page.reload({waitUntil:'domcontentloaded'});
     await page.locator('#showChannelSettings').click();
     await personal.first().waitFor();
     assert.deepEqual(await personalIds(),prefs.order,'Reload lost the saved order');
     while(await page.locator('#channelCountryFilters input:checked').count()) await page.locator('#channelCountryFilters input:checked').first().uncheck();
     assert.deepEqual(await personalIds(),prefs.order);
     await page.locator('#saveChannelSettings').click();
     await page.locator('#channelSettingsDialog').waitFor({state:'hidden'});
     assert.deepEqual(prefs.countries,[]);
     country='at';
     await page.reload({waitUntil:'domcontentloaded'});
     await page.locator('#showChannelSettings').click();
     await personal.first().waitFor();
     assert.deepEqual(await personalIds(),prefs.order,'Country change lost favourites');
     assert.equal(await page.locator('#channelCountryFilters input:checked').count(),0);
     await page.getByRole('button',{name:'Das Erste: Entfernen',exact:true}).click();
     assert.ok(!(await personalIds()).includes('de:ard'));
     await page.locator('#cancelChannelSettings').click();
     await page.locator('#showChannelSettings').click();
     await personal.first().waitFor();
     assert.ok((await personalIds()).includes('de:ard'),'Cancel saved the draft');
     await page.locator('#resetChannelSettings').click();
     await page.waitForFunction(()=>document.querySelectorAll('#channelSettingsList .channel-settings-row').length===1);
     assert.deepEqual(await personalIds(),['ch:ch_srf1']);
     assert.deepEqual(errors,[]);
     await page.close();
     console.log(`${engine} ${width}: mixed selection, filter independence, order, save/reload, country change, cancel/reset and layout passed`);
    }
   } finally {await browser.close();}
  }
 } finally {await new Promise(resolve=>server.close(resolve));}
}
main().catch(error=>{console.error(error);process.exit(1);});
