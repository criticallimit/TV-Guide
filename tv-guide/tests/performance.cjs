const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium,webkit}=require('playwright');
const root=path.resolve(__dirname,'../www');
async function main(){
 let requests=0,guideRequests=0;
 const server=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://local');
  if(url.pathname.startsWith('/api/')){
   requests++;
   if(url.pathname==='/api/guide') guideRequests++;
   res.setHeader('Content-Type','application/json');
   res.end(JSON.stringify(url.pathname==='/api/guide'?{country:'de',channels:[{id:'test',name:'Test',programs:[{title:'Programme',start:'2030-01-01T20:00:00+01:00',end:'2030-01-01T22:00:00+01:00'}]}],main_channel_ids:['test'],custom_channel_ids:[],ui:{default_view:'2015'},refresh_running:false}:{bookmarks:[],reminders:[]}));return;
  }
  const file=path.resolve(root,'.'+(url.pathname==='/'?'/index.html':url.pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.html')?'text/html':'application/octet-stream');res.end(fs.readFileSync(file));
 });await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  for(const [engine,type] of [['chromium',chromium],['webkit',webkit]]){
   const browser=await type.launch(engine==='chromium'&&process.env.TVGUIDE_EDGE_PATH?{executablePath:process.env.TVGUIDE_EDGE_PATH}:{});
   try{
    const page=await browser.newPage({timezoneId:'Europe/Berlin'});const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.clock.install({time:new Date('2030-01-01T20:15:00+01:00')});
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await page.waitForSelector('[data-program-start]');
    const retained=await page.evaluate(()=>{
     const node=grid.firstElementChild;render();render();return grid.firstElementChild===node;
    });assert.equal(retained,true);
    await page.locator('[data-program-start]').first().click();
    assert.equal(await page.locator('#detail').evaluate(node=>node.open),true);
    const dates=await page.evaluate(()=>{
     const original=guide.channels;
     guide.channels=[{programs:Array.from({length:180000},()=>({end:'2030-01-04T23:00:00+01:00'}))}];
     initCustomDate();const max=customDate.max;
     guide.channels=[{programs:[]}];initCustomDate();const empty=customDate.max;
     guide.channels=original;return {max,empty};
    });assert.deepEqual(dates,{max:'2030-01-04',empty:''});
    // A quick tab switch should keep the current guide DOM/data and avoid a full guide reload.
    const quickGuideBefore=guideRequests;
    await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
    await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});
    await page.waitForLoadState('networkidle');
    assert.equal(guideRequests,quickGuideBefore,'A quick tab return must not reload the full guide');

    // Background timers stay paused. After the guide has become stale, returning may refresh it once.
    await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
    const before=requests;await page.clock.fastForward(6*60*1000);assert.equal(requests,before);
    const staleGuideBefore=guideRequests;
    await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(100);
    assert.ok(requests>before);
    assert.equal(guideRequests,staleGuideBefore+1,'A stale guide should refresh once after returning');
    assert.deepEqual(errors,[]);console.log(`${engine}: stable DOM, delegated programme click, 180000 dates and background pause passed`);
   }finally{await browser.close();}
  }
 }finally{await new Promise(resolve=>server.close(resolve));}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
