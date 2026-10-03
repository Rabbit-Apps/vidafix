// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
/* Native HLS baseline for VIDAA. No cloud media or client-side Plex token. */
(function () {
  'use strict';
  var nav = window.TVNavigation, video = document.getElementById('video');
  var view = document.getElementById('player-view'), status = document.getElementById('player-status');
  var toggle = document.getElementById('player-toggle'), sid = null, active = false;
  var controls = document.getElementById('player-controls'), hideTimer = null, controlsHidden = false, holdControls = true;
  function showControls(hold) {
    if (typeof hold === 'boolean') { holdControls = hold; }
    clearTimeout(hideTimer); controlsHidden = false; controls.className = ''; view.className = active ? '' : 'hidden';
    if (active && ready && !video.paused && !holdControls) {
      hideTimer = setTimeout(function () {
        if (active && ready && !video.paused && !holdControls) {
          controlsHidden = true; controls.className = 'controls-hidden'; view.className = 'controls-asleep';
        }
      }, 4000);
    }
  }
  view.onmousemove = function () { if (active) { showControls(); } };
  view.onclick = function () { if (active) { showControls(); } };
  var currentKey = null, currentOptions = null, timelineBase = 0;
  var duration = 0, base = 0, timer = null, done = null, serial = 0, pending = false, ready = false;
  function post(url, data, callback) {
    var xhr = new XMLHttpRequest(); xhr.open('POST', url, true); xhr.timeout = url.indexOf('/start') !== -1 ? 120000 : 45000;
    xhr.setRequestHeader('Content-Type', 'application/json'); xhr.setRequestHeader('X-VidPlex', '1');
    xhr.onload = function () {
      var body;
      try { body = JSON.parse(xhr.responseText); } catch (ignore) { callback('Invalid playback response.'); return; }
      callback(xhr.status === 200 ? null : (body.error || 'Playback request failed.'), body);
    };
    xhr.onerror = function () { callback('Cannot reach the playback helper.'); };
    xhr.ontimeout = function () { callback('Playback preparation timed out. Please try again.'); };
    xhr.send(JSON.stringify(data));
  }
  function position() { return Math.min(duration, Math.max(0, timelineBase + Math.round((video.currentTime || 0) * 1000))); }
  function format(ms) { var s = Math.floor(ms / 1000); return Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); }
  function report() {
    if (!sid || !ready || pending) { return; }
    pending = true; var session = sid;
    post('/api/playback/' + session + '/progress', {time: position(), state: video.paused ? 'paused' : 'playing'}, function (error) {
      pending = false; if (error && sid === session) { status.textContent = 'Progress could not be saved: ' + error; showControls(true); }
    });
  }
  function play() {
    var result = video.play();
    if (result && result.catch) { result.catch(function () { if (active) { status.textContent = 'Press Play to begin, or Stop to return.'; toggle.textContent = 'Play'; showControls(true); } }); }
  }
  function stop(ended) {
    if (!active) { return false; }
    var session = sid, time = ended === true ? duration : position(), callback = done, wasReady = ready;
    active = false; sid = null; serial += 1; clearInterval(timer); clearTimeout(hideTimer); video.pause();
    video.removeAttribute('src'); video.load(); view.className = 'hidden';
    if (session) { post('/api/playback/' + session + '/stop', wasReady ? {time: time} : {}, function (error) { callback(error, time, ended === true); }); }
    else { callback(null, time, ended === true); }
    return true;
  }
  function prepare(key, options, ticket) {
      post('/api/playback/' + key + '/start', options, function (error, data) {
        if (ticket !== serial) {
          if (!error) { post('/api/playback/' + data.session + '/stop', {}, function () {}); }
          return;
        }
        if (error) { active = false; view.className = 'hidden'; done(error); return; }
        sid = data.session; timelineBase = data.timelineBase || 0; base = data.offset; duration = data.duration;
        video.src = data.url; video.load(); play(); timer = setInterval(report, 10000);
      });
  }
  function restartAt(offset) {
    var oldSession = sid, oldPosition = position(), ticket = ++serial;
    sid = null; ready = false; clearInterval(timer); video.pause();
    video.removeAttribute('src'); video.load(); showControls(true); status.textContent = 'Seeking…';
    post('/api/playback/' + oldSession + '/stop', {time: oldPosition}, function (error) {
      if (ticket !== serial) { return; }
      if (error) { active = false; view.className = 'hidden'; done(error); return; }
      prepare(currentKey, {offset: offset, audio: currentOptions.audio, subtitle: currentOptions.subtitle}, ticket);
    });
  }
  function seek(delta) {
    if (!ready) { return; }
    var absoluteTarget = Math.max(0, Math.min(duration - 1, position() + delta * 1000));
    if (absoluteTarget < timelineBase) { restartAt(absoluteTarget); return; }
    var target = (absoluteTarget - timelineBase) / 1000, ranges = video.seekable;
    if (!ranges.length) { status.textContent = 'Seeking is not available yet. Wait for the stream to load.'; return; }
    target = Math.max(ranges.start(0), Math.min(target, ranges.end(ranges.length - 1) - 0.1));
    try { video.currentTime = target; status.textContent = 'Seeking…'; showControls(true); } catch (ignore) { status.textContent = 'This position is not available yet.'; }
  }
  toggle.onclick = function () { nav.adopt(toggle); if (!sid) { return; } if (video.paused) { play(); } else { video.pause(); } };
  document.getElementById('player-rewind').onclick = function () { nav.adopt(this); seek(-30); };
  document.getElementById('player-forward').onclick = function () { nav.adopt(this); seek(30); };
  document.getElementById('player-stop').onclick = stop;
  video.onloadedmetadata = function () {
    // The resume playlist begins at timelineBase, near the requested position.
    var relativeStart = Math.max(0, base - timelineBase);
    if (relativeStart > 0 && Math.abs(video.currentTime * 1000 - relativeStart) > 500) {
      try { video.currentTime = relativeStart / 1000; } catch (ignore) { status.textContent = 'Resume position is not available yet.'; }
    }
    ready = true;
  };
  video.onplaying = function () { status.textContent = 'Playing'; toggle.textContent = 'Pause'; showControls(false); report(); };
  video.onpause = function () { if (active && ready) { status.textContent = 'Paused'; toggle.textContent = 'Play'; showControls(true); report(); } };
  video.onwaiting = function () { if (active) { status.textContent = 'Buffering…'; showControls(true); } };
  video.ontimeupdate = function () { document.getElementById('player-time').textContent = format(position()) + ' / ' + format(duration); };
  video.onseeked = function () { status.textContent = video.paused ? 'Paused' : 'Playing'; showControls(video.paused); report(); };
  video.onended = function () { stop(true); };
  video.onerror = function () { if (active) { status.textContent = 'Playback failed. The TV may not support this stream, or Plex could not transcode it. Stop to return.'; showControls(true); } };
  nav.media(function (code) {
    if (!active) { return false; }
    if (code === 13 || (code >= 37 && code <= 40)) {
      var wasHidden = controlsHidden; showControls();
      if (wasHidden) { return true; }
    }
    if (code === 415) { play(); }
    else if (code === 19) { video.pause(); }
    else if (code === 179 || code === 10252) { toggle.onclick(); }
    else if (code === 413) { stop(); }
    else if (code === 412) { seek(-30); }
    else if (code === 417) { seek(30); }
    else { return false; }
    showControls(); return true;
  });
  window.addEventListener('pagehide', function () { if (active) { stop(); } });
  window.VidPlexPlayer = {
    stop: stop,
    post: post,
    start: function (key, options, callback) {
      if (active) { return; }
      if (!video.canPlayType('application/vnd.apple.mpegurl') && !video.canPlayType('application/x-mpegURL')) {
        callback('This browser does not support native HLS playback. Test playback in the VIDAA TV browser.'); return;
      }
      active = true; ready = false; pending = false; done = callback; base = options.offset; duration = 0;
      showControls(true); view.className = ''; status.textContent = 'Preparing playback…'; document.getElementById('player-time').textContent = '';
      nav.scrollDetails(false); nav.set([[toggle, document.getElementById('player-rewind'), document.getElementById('player-forward'), document.getElementById('player-stop')]]);
      var ticket = ++serial;
      currentKey = key; currentOptions = options; timelineBase = 0;
      prepare(key, options, ticket);
    }
  };
}());
