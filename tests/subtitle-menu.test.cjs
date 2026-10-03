// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const source = fs.readFileSync('app/app.js', 'utf8');
const start = source.indexOf("var searchButton = add('Find subtitles'");
const code = source.slice(start, source.indexOf('focus(document.activeElement);', start));
function element(label) { return {textContent:label,children:[],setAttribute(){},appendChild(el){this.children.push(el);},removeChild(el){this.children.splice(this.children.indexOf(el),1);}}; }
function setup() {
  const calls=[], body=element(''), actions=[];
  const ctx={document:{body,createElement:()=>element('')},text:(tag,label)=>element(label),
    nav:{back(fn){this.onBack=fn;},scrollDetails(){},set(rows){this.rows=rows;}},
    back(){},focus(el){ctx.focused=el;},inDetails:true,ticket:1,detailRequest:1,item:{id:'1'},
    languages:[['en','English']],languageIndex:0,message:element(''),
    window:{VidPlexPlayer:{post(url,data,callback){calls.push({url,data,callback});}}},
    add(label,fn){const el=element(label);el.onclick=()=>fn(el);actions.push(el);return el;}};
  vm.runInNewContext(code,ctx);ctx.searchButton.onclick();return {ctx,calls,body,actions};
}
let t=setup();t.calls[0].callback(null,{items:[{id:'opaque',label:'English release'}]});
let panel=t.body.children[0].children[0];
assert(panel.children.some(x=>x.textContent==='English release'));
assert.strictEqual(t.actions.length,1,'results must not enter details actions');
assert.strictEqual(t.ctx.nav.rows.length,2);
panel.children[3].onclick();assert.strictEqual(t.body.children.length,0);
assert(t.calls[1].url.endsWith('/subtitles/download'));assert.strictEqual(t.calls[1].data.id,'opaque');
t=setup();t.ctx.nav.onBack();t.calls[0].callback(null,{items:[{id:'x',label:'Late'}]});
assert.strictEqual(t.body.children.length,0);assert.strictEqual(t.ctx.focused,t.ctx.searchButton);
t=setup();t.calls[0].callback('Search unavailable');assert.strictEqual(t.body.children[0].children[0].children[1].textContent,'Search unavailable');
t=setup();t.calls[0].callback(null,{items:[]});assert(t.body.children[0].children[0].children[1].textContent.includes('No subtitles'));
console.log('Subtitle menu: results, selection, dismissal, late responses, empty and error states passed.');
