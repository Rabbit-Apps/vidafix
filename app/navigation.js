// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
/* ES5 deliberately: no modules, promises, arrow functions or spatial-nav APIs. */
(function (root) {
  'use strict';
  var rows = [], row = 0, col = 0, onBack = function () {}, detailScroll = false, onMedia = function () { return false; };
  function focus() {
    var old = document.querySelector('.focused');
    if (old) { old.className = old.className.replace(/\s*focused/g, ''); }
    if (!rows[row] || !rows[row][col]) { return; }
    var el = rows[row][col];
    el.className += ' focused';
    el.focus();
    if (el.parentNode && el.parentNode.className === 'shelf') {
      var shelf = el.parentNode;
      if (el.offsetLeft < shelf.scrollLeft) { shelf.scrollLeft = el.offsetLeft; }
      if (el.offsetLeft + el.offsetWidth > shelf.scrollLeft + shelf.clientWidth) {
        shelf.scrollLeft = el.offsetLeft + el.offsetWidth - shelf.clientWidth + 8;
      }
    }
    var rect = el.getBoundingClientRect();
    if (rect.bottom > window.innerHeight - 80) { window.scrollBy(0, rect.bottom - window.innerHeight + 80); }
    else if (rect.top < 20) { window.scrollBy(0, rect.top - 20); }
  }
  function set(next, r, c) {
    rows = next;
    row = Math.max(0, Math.min(r || 0, rows.length - 1));
    col = Math.max(0, Math.min(c || 0, rows[row] ? rows[row].length - 1 : 0));
    focus();
  }
  function adopt(el) {
    for (var r = 0; r < rows.length; r += 1) {
      for (var c = 0; c < rows[r].length; c += 1) {
        if (rows[r][c] === el) { row = r; col = c; focus(); return; }
      }
    }
  }
  document.addEventListener('keydown', function (event) {
    var code = event.keyCode || event.which;
    var debug = document.getElementById('key-debug');
    if (location.search.indexOf('debug=1') !== -1 && debug) { debug.textContent = ' · Key: ' + code; }
    if (onMedia(code)) { event.preventDefault(); return; }
    if (code === 8 || code === 27 || code === 461 || code === 10009 || event.key === 'GoBack' || event.key === 'BrowserBack') {
      event.preventDefault(); onBack(); return;
    }
    if (code === 13) {
      event.preventDefault();
      if (!event.repeat && rows[row] && rows[row][col]) { rows[row][col].click(); }
      return;
    }
    if (code < 37 || code > 40 || !rows.length) { return; }
    event.preventDefault();
    if (detailScroll && (code === 38 || code === 40)) { window.scrollBy(0, code === 38 ? -120 : 120); return; }
    if (code === 37) { col = Math.max(0, col - 1); }
    if (code === 39) { col = Math.min(rows[row].length - 1, col + 1); }
    if (code === 38) { row = Math.max(0, row - 1); }
    if (code === 40) { row = Math.min(rows.length - 1, row + 1); }
    col = Math.min(col, rows[row].length - 1);
    focus();
  });
  root.TVNavigation = {media: function (callback) { onMedia = callback; }, set: set, adopt: adopt, position: function () { return [row, col]; },
    back: function (callback) { onBack = callback; }, scrollDetails: function (value) { detailScroll = value; }};
}(window));
