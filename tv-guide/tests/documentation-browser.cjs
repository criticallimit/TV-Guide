// Exercise published guide navigation in both engines, on desktop and mobile.
const assert=require('node:assert/strict');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {chromium,webkit}=require('playwright');
const root=path.resolve(__dirname,'../../docs');
async function main(){
 const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+new URL(req.url,'http://local').pathname);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(file));
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{
  for(const [engine,type] of [['chromium',chromium],['webkit',webkit]]){
   const browser=await type.launch(engine==='chromium'&&process.env.TVGUIDE_EDGE_PATH?{executablePath:process.env.TVGUIDE_EDGE_PATH}:{});
   try{
    for(const width of [390,1280]){
     const page=await browser.newPage({viewport:{width,height:800}});
     for(const theme of ['light','dark']){
      await page.emulateMedia({colorScheme:theme});
      await page.goto(`http://127.0.0.1:${server.address().port}/manuals/en.html`);
      for(const language of ['de','nl','fr','it','nb','en']){
       await page.locator(`nav a[lang="${language}"]`).click();
       assert.equal(await page.locator('html').getAttribute('lang'),language);
       assert.equal(await page.locator('nav a[aria-current="page"]').getAttribute('lang'),language);
       assert.ok((await page.locator('h1').textContent()).includes('TV Guide'));
       assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
      }
     }
     await page.close();
    }
    console.log(`${engine}: all six user guides and language links work on desktop/mobile in both themes`);
   }finally{await browser.close();}
  }
 }finally{await new Promise(r=>server.close(r));}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
