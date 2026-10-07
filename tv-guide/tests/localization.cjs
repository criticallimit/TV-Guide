const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../www');
const catalogs = Object.fromEntries(['da','de','en','nl','fr','it','nb','sv'].map(code => [code, JSON.parse(fs.readFileSync(path.join(root,'locales',code+'.json'),'utf8'))]));
for (const [code,catalog] of Object.entries(catalogs)) {
  assert.deepEqual(Object.keys(catalog).sort(), Object.keys(catalogs.de).sort(),code);
  for (const [key,value] of Object.entries(catalog)) {
    assert.ok(value.trim(),`${code}: ${key}`);
    assert.deepEqual((value.match(/\{\w+\}/g)||[]).sort(),(key.match(/\{\w+\}/g)||[]).sort(),`${code}: ${key}`);
  }
}
for (const match of fs.readFileSync(path.join(root,'index.html'),'utf8').matchAll(/data-i18n(?:-[\w-]+)?="([^"]+)"/g)) assert.ok(catalogs.de[match[1].replaceAll("&amp;","&")],match[1]);
const context = vm.createContext({Intl,navigator:{language:'it-CH'},document:{documentElement:{},querySelector:()=>null,querySelectorAll:()=>[]}});
context.parent=context;
for (const file of ['translations.js','i18n.js']) vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),context);
const api=context.TVGuideI18n;
assert.deepEqual(JSON.parse(JSON.stringify(context.TVGuideTranslations)),catalogs);
assert.equal(api.resolve({country:'at'}),'de');
assert.equal(api.resolve({country:'nl'}),'nl');
assert.equal(api.resolve({country:'fr'}),'fr');
assert.equal(api.resolve({country:'se'}),'sv');
assert.equal(api.resolve({country:'gb'}),'en');
assert.equal(api.resolve({country:'dk'}),'da');
assert.equal(api.resolve({country:'ch'}),'it');
assert.equal(api.resolve({home_assistant:{country:'BE',language:'fr-BE'}}),'fr');
context.hass={locale:{language:'nl-NL'}};
assert.equal(api.resolve({country:'de',home_assistant:{language:'de'}}),'nl');
assert.equal(api.resolve({language:'en',country:'nl'}),'en');
context.hass={language:'es'};
assert.equal(api.resolve({country:'de'}),'en');
context.hass={language:'nb-NO'};
assert.equal(api.resolve({country:'no'}),'nb');
context.hass={language:'no-NO'};
assert.equal(api.resolve({country:'no'}),'nb');
delete context.hass;
assert.equal(api.resolve({country:"no"}),"nb");
context.parent={document:{querySelector:()=>({hass:{language:'fr-CH'}})}};
assert.equal(api.resolve({country:'ch'}),'fr');
Object.defineProperty(context,'parent',{get(){throw Error('cross origin');},configurable:true});
assert.equal(api.resolve({home_assistant:{language:'en'}}),'en');
for (const code of ['da','de','en','nl','fr','it','nb','sv']) {
  api.configure({language:code});
  assert.equal(context.document.documentElement.lang,code);
  assert.equal(api.t('Speichern'),catalogs[code].Speichern);
  assert.ok(api.t('Erinnerung {minutes} Minuten vorher.',{minutes:15}).includes('15'));
  assert.equal(api.t('Programme title absent from translation catalogue'),'Programme title absent from translation catalogue');
}
console.log('Eight-language catalogues, placeholders, profile precedence and safe fallbacks passed');

const cardContext=vm.createContext({HTMLElement:class {},customElements:{get:()=>null,define:()=>{}}});
cardContext.window=cardContext;
vm.runInContext(fs.readFileSync(path.resolve(root,"../lovelace/tv-guide-card.js"),"utf8"),cardContext);
const cardPrototype=vm.runInContext("TVGuideCard.prototype",cardContext);
for(const code of ["da","de","en","nl","fr","it","nb","sv"]) assert.equal(cardPrototype._t.call({_hass:{language:code}},"TV Guide wird geladen …"),catalogs[code]["TV Guide wird geladen …"]);
assert.equal(cardPrototype._t.call({_hass:{language:"es"}},"TV Guide wird geladen …"),catalogs.en["TV Guide wird geladen …"]);

assert.equal(cardPrototype._t.call({_hass:{language:"no-NO"}},"TV Guide wird geladen …"),catalogs.nb["TV Guide wird geladen …"]);
