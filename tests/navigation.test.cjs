// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
// Optional developer test. Node is not needed to run the application.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
let handler, focused, clicks = 0, backs = 0;
function button() {
  return {className: '', focus() { focused = this; }, click() { clicks++; },
    getBoundingClientRect() { return {top: 100, bottom: 200}; }, scrollIntoView() {}};
}
const context = {window: {innerHeight: 1080}, location: {search: ''}, document: {
  querySelector() { return focused; }, getElementById() { return null; },
  addEventListener(name, fn) { handler = fn; }
}};
vm.runInNewContext(fs.readFileSync('app/navigation.js', 'utf8'), context);
const nav = context.window.TVNavigation;
const rows = [[button(), button()], Array.from({length: 5}, button), Array.from({length: 3}, button)];
function key(code) { let prevented = false; handler({keyCode: code, preventDefault() { prevented = true; }}); assert.ok(prevented); }
nav.set(rows); key(37); assert.equal(focused, rows[0][0]);
key(40); key(39); key(39); key(39); key(39); assert.equal(focused, rows[1][4]);
key(40); assert.equal(focused, rows[2][2]);
key(40); assert.equal(focused, rows[2][2]);
key(13); assert.equal(clicks, 1);
const saved = nav.position(); nav.set([[button()]]); nav.set(rows, saved[0], saved[1]);
assert.equal(focused, rows[2][2]);
nav.back(() => backs++); [8, 27, 461, 10009].forEach(key); assert.equal(backs, 4);
nav.set([]); key(13);
console.log('Navigation: boundaries, partial rows, OK, Back aliases and restored focus passed.');
const shelf = {className: 'shelf', scrollLeft: 0, clientWidth: 500};
const distant = button(); distant.parentNode = shelf; distant.offsetLeft = 900; distant.offsetWidth = 100;
nav.set([[distant]]); assert.equal(shelf.scrollLeft, 508);
let scroll = 0; context.window.scrollBy = (x, y) => { scroll += y; };
nav.scrollDetails(true); key(40); assert.equal(scroll, 120); key(38); assert.equal(scroll, 0);
nav.scrollDetails(false);
console.log('Horizontal shelf visibility and detail scrolling passed.');
