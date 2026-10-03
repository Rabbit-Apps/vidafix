// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const page = fs.readFileSync(path.join(__dirname, '../sideload-addon/vidafix-install.template.html'), 'utf8');
const code = page.match(/<script>([\s\S]*?)<\/script>/)[1].replace('__VIDAFIX_SETTINGS__',
  JSON.stringify({host:'192.168.1.20',url:'http://192.168.1.20:8765/',icon:'http://192.168.1.20:8765/static/vidafix.png'}));
function fixture(hostname, api) {
  const document = {activeElement:null};
  const nodes = {};
  ['install','remove','status','icon'].forEach(id => {
    nodes[id] = {textContent:'', focus(){document.activeElement = this;}};
  });
  document.getElementById = id => nodes[id];
  const calls = [];
  const window = api ? {
    Hisense_AddInsecureDomain(host){calls.push(['host', host]);},
    Hisense_installApp(...args){calls.push(['install', ...args.slice(0,-1)]);args.at(-1)(0);},
    Hisense_uninstallApp(id, callback){calls.push(['remove',id]);callback(0);}
  } : {};
  vm.runInNewContext(code,{window,document,location:{hostname}});
  return {document,nodes,calls};
}
let f = fixture('vidaahub.com',true);
f.nodes.install.onclick();
assert.equal(f.calls[0][1], '192.168.1.20');
assert.deepEqual(f.calls[1], ['install','vidplex-local','Vidafix',
  'http://192.168.1.20:8765/static/vidafix.png','http://192.168.1.20:8765/static/vidafix.png',
  'http://192.168.1.20:8765/static/vidafix.png','http://192.168.1.20:8765/','store']);
assert.match(f.nodes.status.textContent,/Restore the previous DNS/);
f.document.onkeydown({keyCode:39,preventDefault(){}});
assert.equal(f.document.activeElement,f.nodes.remove);
f.document.onkeydown({keyCode:13,preventDefault(){}});
assert.deepEqual(f.calls[2],['remove','vidplex-local']);
f = fixture('localhost',true);f.nodes.install.onclick();assert.equal(f.calls.length,0);
f = fixture('vidaahub.com',false);f.nodes.install.onclick();assert.match(f.nodes.status.textContent,/unavailable/);
console.log('Sideload add-on: local host/API checks, installer arguments, existing tile ID and remote focus passed.');
