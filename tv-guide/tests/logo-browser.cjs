// Decode every bundled theme asset in both browser engines, without external requests.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium,webkit}=require('playwright');
const root=path.resolve(__dirname,'../www');
const library=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../data/logo_library.json'),'utf8'));
async function main(){
 const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+new URL(req.url,'http://local').pathname);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',file.endsWith('.svg')?'image/svg+xml':'text/html');res.end(fs.readFileSync(file));
 });await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{
  const assets=[...new Set(Object.values(library.channels).flatMap(c=>[c.light,c.dark]))];
  for(const [engine,type] of [['chromium',chromium],['webkit',webkit]]){
   const browser=await type.launch(engine==='chromium'&&process.env.TVGUIDE_EDGE_PATH?{executablePath:process.env.TVGUIDE_EDGE_PATH}:{});
   try{
    const page=await browser.newPage();await page.goto(`http://127.0.0.1:${server.address().port}/index.html`);
    await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
    const results=await page.evaluate(async assets=>{
     const results=[];
     for(let offset=0;offset<assets.length;offset+=16){
      await Promise.all(assets.slice(offset,offset+16).map(async file=>{
       try{
        const image=new Image();image.src='/'+file;await image.decode();
        const canvas=document.createElement('canvas');canvas.width=260;canvas.height=64;
        const context=canvas.getContext('2d');context.drawImage(image,0,0,260,64);
        const data=context.getImageData(0,0,260,64).data;let ink=0;
        for(let i=3;i<data.length;i+=4)if(data[i]>80)ink++;
        results.push({file,ink,width:image.naturalWidth,height:image.naturalHeight});
       }catch(error){results.push({file,error:String(error)});}
      }));
     }return results;
    },assets);
    for(const result of results){assert.ok(!result.error,JSON.stringify(result));assert.ok(result.ink>=30,JSON.stringify(result));assert.equal(result.width,260,result.file);assert.equal(result.height,64,result.file);}
    console.log(`${engine}: ${results.length} local light/dark logos render successfully`);
   }finally{await browser.close();}
  }
 }finally{await new Promise(r=>server.close(r));}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
