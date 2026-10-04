const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {chromium,webkit}=require('playwright');
const script=fs.readFileSync(path.resolve(__dirname,'../lovelace/tv-guide-card.js'),'utf8');
async function main(){
 for(const [name,type] of [['chromium',chromium],['webkit',webkit]]){
  const browser=await type.launch(name==='chromium'&&process.env.TVGUIDE_EDGE_PATH?{executablePath:process.env.TVGUIDE_EDGE_PATH}:{});
  try{
   const page=await browser.newPage();
   await page.route('http://tv-guide.test/**',route=>route.fulfill({contentType:'text/html',body:'<hui-card-picker></hui-card-picker>'}));
   await page.goto('http://tv-guide.test/');
   await page.addScriptTag({content:script});
   for(const background of ['#111111','#ffffff']){
    const result=await page.evaluate(background=>{
     document.body.style.background=background;
     const picker=document.querySelector('hui-card-picker');
     const root=picker.shadowRoot||picker.attachShadow({mode:'open'});
     root.replaceChildren();
     let calls=0;
     const card=document.createElement('tv-guide-card');
     const config={type:'custom:tv-guide-card',...card.constructor.getStubConfig()};
     card.setConfig(config);
     card.hass={language:'en',callWS:()=>{calls++;throw Error('Picker must not call Supervisor');}};
     const wrapper=document.createElement('div');root.append(wrapper);wrapper.append(card);
     card.hass={language:'nb',callWS:()=>{calls++;}};
     const svg=card.shadowRoot.querySelector('svg');
     const rect=svg.getBoundingClientRect();
     return {calls,logo:!!svg,iframe:!!card.shadowRoot.querySelector('iframe'),width:rect.width,height:rect.height,config,preview:window.customCards[0].preview};
    },background);
    assert.equal(result.calls,0);assert.equal(result.logo,true);assert.equal(result.iframe,false);
    assert.ok(result.width>0&&result.width<=250);assert.ok(result.height>0);
    assert.equal(result.preview,true);assert.deepEqual(result.config,{type:'custom:tv-guide-card',height:1000});
   }
   const live=await page.evaluate(async()=>{
    const card=document.createElement('tv-guide-card');card.setConfig({height:750});
    card.hass={language:'en',panels:{tv_guide:{title:'TV Guide'}},callWS:async request=>request.endpoint==='/ingress/session'?{session:'test'}:{version:'1.0.8',state:'started',ingress_url:'about:blank'}};
    document.body.append(card);await new Promise(resolve=>setTimeout(resolve,30));
    const result={iframe:!!card.shadowRoot.querySelector('iframe'),height:card.shadowRoot.querySelector('iframe')?.style.height,brand:!!card.shadowRoot.querySelector('.brand')};
    card.remove();return result;
   });
   assert.deepEqual(live,{iframe:true,height:'750px',brand:false});
   console.log(`${name}: card picker logo in light/dark and live dashboard verified`);
  }finally{await browser.close();}
 }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
