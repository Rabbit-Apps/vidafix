// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = {}, requests = [];
let hideTimeout;
for (const id of ['video', 'player-view', 'player-controls', 'player-status', 'player-time', 'player-toggle', 'player-rewind', 'player-forward', 'player-stop']) {
  elements[id] = {textContent: '', className: '', currentTime: 0};
}
const video = elements.video;
Object.assign(video, {
  canPlayType: () => 'probably', paused: true, seekable: {length: 1, start: () => 0, end: () => 120},
  play() { this.paused = false; }, pause() { this.paused = true; },
  load() {}, removeAttribute() {}
});
function XHR() { requests.push(this); }
XHR.prototype.open = function (method, url) { this.url = url; };
XHR.prototype.setRequestHeader = function () {};
XHR.prototype.send = function (body) { this.body = JSON.parse(body); };
XHR.prototype.reply = function (body, status = 200) { this.responseText = JSON.stringify(body); this.status = status; this.onload(); };
const nav = {set() {}, adopt() {}, scrollDetails() {}, media(fn) { this.handler = fn; }};
const window = {TVNavigation: nav, addEventListener() {}};
vm.runInNewContext(fs.readFileSync('app/player.js', 'utf8'), {
  window, document: {getElementById: id => elements[id]}, XMLHttpRequest: XHR,
  setInterval: () => 1, clearInterval() {}, setTimeout: fn => { hideTimeout = fn; return 2; }, clearTimeout: () => { hideTimeout = null; }, Math, JSON
});
const player = window.VidPlexPlayer;
let stopped;
player.start('1', {offset: 30000}, (err, time) => { stopped = time; });
requests.at(-1).reply({session: 'one', url: '/playback/one/master.m3u8', offset: 30000, duration: 120000});
video.onloadedmetadata();
assert.equal(video.currentTime, 30);
video.currentTime = 35;
video.onplaying();
assert.equal(requests.at(-1).body.time, 35000, 'Resume offset must not be counted twice');
requests.at(-1).reply({ok: true});
assert.equal(typeof hideTimeout, 'function');
hideTimeout();
assert.equal(elements['player-controls'].className, 'controls-hidden');
assert.equal(nav.handler(13), true, 'First OK should reveal controls without toggling playback');
assert.equal(elements['player-controls'].className, '');
assert.equal(video.paused, false);
hideTimeout();
elements['player-view'].onmousemove();
assert.equal(elements['player-controls'].className, '');
video.onwaiting();
assert.equal(hideTimeout, null, 'Buffering keeps controls visible');
video.onplaying();
assert.equal(typeof hideTimeout, 'function');
nav.handler(19);
assert.equal(video.paused, true);
video.onpause();
assert.equal(hideTimeout, null, 'Pause keeps controls visible');
nav.handler(417);
assert.equal(video.currentTime, 65);
player.stop();
assert.equal(requests.at(-1).body.time, 65000);
requests.at(-1).reply({ok: true});
assert.equal(stopped, 65000);
player.start('1', {offset: 0}, () => {});
const pendingStart = requests.at(-1);
player.stop();
pendingStart.reply({session: 'late', url: '/playback/late/master.m3u8', offset: 0, duration: 120000});
assert.equal(requests.at(-1).url, '/api/playback/late/stop', 'Late startup must release its session');
assert.deepEqual(requests.at(-1).body, {}, 'Unplayed sessions must not overwrite progress');
player.start('1', {offset: 35000, audio: '20', subtitle: '0'}, () => {});
requests.at(-1).reply({session: 'trimmed', url: '/playback/trimmed/master.m3u8', offset: 35000, timelineBase: 32000, duration: 120000});
video.currentTime = 0;
video.onloadedmetadata();
assert.equal(video.currentTime, 3);
video.currentTime = 5;
video.onplaying();
assert.equal(requests.at(-1).body.time, 37000, 'Trimmed playlist must report absolute Plex time');
requests.at(-1).reply({ok: true});
nav.handler(412);
assert.equal(requests.at(-1).url, '/api/playback/trimmed/stop');
requests.at(-1).reply({ok: true});
assert.equal(requests.at(-1).url, '/api/playback/1/start');
assert.equal(requests.at(-1).body.offset, 7000, 'Rewind before playlist origin prepares the earlier position');
const rewindStart = requests.at(-1);
player.stop();
rewindStart.reply({session: 'cancelled-rewind', offset: 7000});
assert.equal(requests.at(-1).url, '/api/playback/cancelled-rewind/stop');
video.canPlayType = () => '';
const before = requests.length;
let unsupported;
player.start('1', {offset: 0}, error => { unsupported = error; });
assert.match(unsupported, /native HLS/);
assert.equal(requests.length, before);
console.log('Player: absolute resume progress, media keys, seek, stop, cancelled startup and unsupported HLS passed.');

video.canPlayType = () => 'probably';
let endedResult;
player.start('2', {offset:0}, (error,time,ended) => { endedResult={error,time,ended}; });
requests.at(-1).reply({session:'ended',url:'/playback/ended/master.m3u8',offset:0,duration:120000});
video.onloadedmetadata(); video.currentTime=119.9; video.onended();
assert.equal(requests.at(-1).body.time,120000,'Natural end saves the full duration');
assert.equal(endedResult,undefined,'Completion waits for final progress save');
requests.at(-1).reply({ok:true}); assert.equal(endedResult.ended,true);
player.start('2',{offset:0},(error,time,ended)=>{endedResult={error,time,ended};});
requests.at(-1).reply({session:'manual',url:'/playback/manual/master.m3u8',offset:0,duration:120000});
video.onloadedmetadata(); player.stop();requests.at(-1).reply({ok:true});
assert.equal(endedResult.ended,false,'Manual Stop must not autoplay');
