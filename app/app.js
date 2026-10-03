// Copyright (c) 2026 Vidafix contributors. Licensed under MIT; see LICENSE.
(function () {
  'use strict';
  var nav = window.TVNavigation, menu = [], sections = [], selected = 'home', savedElement = null;
  var libraries = [], librarySorts = {}, viewCache = [], viewStarted = 0;
  var detailTrail = [], currentDetail = null, homeDirty = false, autoplay = true;
  var inDetails = false, generation = 0, detailRequest = 0;
  var status = document.getElementById('status'), retry = document.getElementById('retry');
  var contentRoot = document.getElementById('posters');
  function text(tag, value, className) {
    var el = document.createElement(tag); el.textContent = value;
    if (className) { el.className = className; } return el;
  }
  function request(url, done) {
    var xhr = new XMLHttpRequest(); xhr.open('GET', url, true);
    xhr.timeout = url === '/api/watchlist' ? 60000 : 30000;
    xhr.onload = function () {
      var data;
      try { data = JSON.parse(xhr.responseText); } catch (ignore) { done('The helper returned an invalid response.'); return; }
      if (xhr.status !== 200) { done(data.error || 'The request failed. Please try again.'); return; }
      done(null, data);
    };
    xhr.onerror = function () { done('Cannot reach the helper. Check your network.'); };
    xhr.ontimeout = function () { done('The request timed out. Please try again.'); };
    xhr.send();
  }
  function focusRows(r, c, keep) {
    var rows = [], i, j;
    var menuTop = null;
    for (i = 0; i < menu.length; i += 1) {
      var top = menu[i].getBoundingClientRect().top;
      if (menuTop === null || Math.abs(top - menuTop) > 2) { rows.push([]); menuTop = top; }
      rows[rows.length - 1].push(menu[i]);
    }
    if (retry.className !== 'hidden') { rows.push([retry]); }
    for (i = 0; i < sections.length; i += 1) {
      if (sections[i].sortButtons.length) { rows.push(sections[i].sortButtons); }
      if (sections[i].horizontal && sections[i].buttons.length) { rows.push(sections[i].buttons); }
      else {
        for (j = 0; j < sections[i].buttons.length; j += 6) { rows.push(sections[i].buttons.slice(j, j + 6)); }
      }
      if (sections[i].pageButtons.length) { rows.push(sections[i].pageButtons); }
    }
    if (keep) {
      for (i = 0; i < rows.length; i += 1) {
        for (j = 0; j < rows[i].length; j += 1) { if (rows[i][j] === keep) { r = i; c = j; } }
      }
    }
    nav.set(rows, r, c); queueArtwork();
  }
  function rebuildFocus() { if (!inDetails) { focusRows(0, 0, document.activeElement); } }
  var artTimer = null;
  function loadVisibleArtwork() {
    artTimer = null;
    var images = document.querySelectorAll('img[data-art-src]');
    for (var i = 0; i < images.length; i += 1) {
      var img = images[i], rect = img.parentNode.getBoundingClientRect();
      if (rect.width > 0 && rect.bottom > -200 && rect.top < window.innerHeight + 200 &&
          rect.right > -200 && rect.left < window.innerWidth + 200) {
        img.src = img.getAttribute('data-art-src'); img.removeAttribute('data-art-src');
      }
    }
  }
  function queueArtwork() {
    if (artTimer === null) { artTimer = window.setTimeout(loadVisibleArtwork, 40); }
  }
  window.addEventListener('scroll', queueArtwork, true);
  window.addEventListener('resize', queueArtwork);
  document.addEventListener('keydown', queueArtwork);
  function artwork(url, title, defer) {
    var frame = text('div', 'No artwork', 'artwork');
    if (url) {
      var img = document.createElement('img'); img.alt = title;
      if (defer) { img.setAttribute('data-art-src', url); queueArtwork(); }
      else { img.src = url; }
      img.onerror = function () { if (img.parentNode) { img.parentNode.removeChild(img); } };
      frame.appendChild(img);
    }
    return frame;
  }
  function episodeLabel(item) {
    return item.type === 'episode' ? 'S' + (item.season || 0) + ' E' + (item.episode || 0) + ' · ' + item.episodeTitle : '';
  }
  function card(item) {
    var button = document.createElement('button'); button.type = 'button'; button.className = 'poster';
    button.appendChild(artwork(item.poster, item.title, true)); button.appendChild(text('span', item.title, 'poster-title'));
    if (item.type === 'episode') { button.appendChild(text('span', episodeLabel(item), 'poster-subtitle')); }
    if (item.viewOffset > 0 && item.duration > 0) {
      var percent = Math.min(100, Math.round(100 * item.viewOffset / item.duration));
      var progress = document.createElement('progress'); progress.max = 100; progress.value = percent;
      progress.setAttribute('aria-label', percent + '% watched'); button.appendChild(progress);
      button.appendChild(text('span', Math.max(0, Math.ceil((item.duration - item.viewOffset) / 60000)) + ' min remaining', 'poster-subtitle'));
    }
    button.onclick = function () { nav.adopt(button); openDetails(item.id); };
    return button;
  }
  function loadSection(section, ticket, offset) {
    if (section.loading) { return; }
    section.loading = true;
    var pageOffset = typeof offset === 'number' ? offset : (section.offset || 0);
    section.message.textContent = 'Loading…';
    var url = section.url + (section.paged ? '?offset=' + pageOffset + '&sort=' + section.sort : '');
    request(url, function (error, data) {
      if (sections.indexOf(section) === -1) { return; }
      section.loading = false;
      if (error) {
        section.message.textContent = error;
        section.pageButtons = []; section.pager.innerHTML = '';
        var again = text('button', 'Retry ' + section.title); again.type = 'button';
        again.onclick = function () { loadSection(section, ticket, pageOffset); };
        section.pageButtons.push(again); section.pager.appendChild(again);
      } else {
        var paging = section.paged && section.loaded;
        section.offset = pageOffset; section.loaded = true;
        section.buttons = []; section.grid.innerHTML = '';
        section.pageButtons = []; section.pager.innerHTML = '';
        section.message.textContent = data.items.length ? (data.message || data.items.length + ' titles') : section.empty;
        if (section.paged) {
          section.message.textContent = data.items.length ? 'Titles ' + (pageOffset + 1) + '–' + (pageOffset + data.items.length) + (data.total !== null ? ' of ' + data.total : '') : 'No titles on this page.';
          addPageButton(section, 'Previous page', data.previous, ticket);
          addPageButton(section, 'Next page', data.next, ticket);
        }
        if (data.truncated) { section.message.textContent += ' Showing a limited selection; some Watchlist entries have not been checked.'; }
        for (var i = 0; i < data.items.length; i += 1) {
          var button = card(data.items[i]); section.buttons.push(button); section.grid.appendChild(button);
        }
        if (paging && !inDetails) {
          focusRows(0, 0, section.buttons[0] || section.pageButtons[0]); return;
        }
      }
      rebuildFocus();
    });
  }
  function addPageButton(section, label, offset, ticket) {
    if (typeof offset !== 'number') { return; }
    var button = text('button', label); button.type = 'button';
    button.onclick = function () { nav.adopt(button); loadSection(section, ticket, offset); };
    section.pageButtons.push(button); section.pager.appendChild(button);
  }
  function section(title, url, empty, horizontal) {
    var el = document.createElement('section'); el.className = 'media-section';
    el.appendChild(text('h2', title));
    var sortButtons = [], sort = librarySorts[selected] || 'title';
    if (url.indexOf('/api/library/') === 0 && !horizontal) {
      var controls = document.createElement('div'); controls.className = 'sort-controls';
      controls.appendChild(text('span', 'Sort by: '));
      function sortButton(label, value, index) {
        var button = text('button', label); button.type = 'button';
        button.setAttribute('aria-pressed', sort === value ? 'true' : 'false');
        button.onclick = function () {
          librarySorts[selected] = value; loadView(selected, true); focusRows(0, 0, sections[0].sortButtons[index]);
        };
        controls.appendChild(button); sortButtons.push(button);
      }
      sortButton('Title A–Z', 'title', 0); sortButton('Recently added', 'recent', 1);
      el.appendChild(controls);
    }
    var message = text('p', 'Loading…', 'row-status'); message.setAttribute('role', 'status'); el.appendChild(message);
    var grid = document.createElement('div'); grid.className = horizontal ? 'shelf' : 'poster-grid'; el.appendChild(grid);
    var pager = document.createElement('div'); pager.className = 'pager'; el.appendChild(pager);
    contentRoot.appendChild(el);
    var entry = {title: title, url: url, empty: empty, horizontal: horizontal, message: message, grid: grid, buttons: [],
      sort: sort, sortButtons: sortButtons, pager: pager, pageButtons: [], paged: url.indexOf('/api/library/') === 0 && !horizontal, offset: 0, loading: false, loaded: false};
    sections.push(entry); loadSection(entry, generation);
  }
  function loadView(id, refresh) {
    var now = new Date().getTime(), previous = selected, cached = null, i;
    if (!refresh && id === selected && sections.length) { return; }
    /* Keep at most two inactive screens plus the active screen for TV memory. */
    if (!refresh && sections.length && sections.every(function (entry) { return entry.loaded && !entry.loading; })) {
      var saved = {id: previous, sections: sections, nodes: [], time: viewStarted,
        scrolls: sections.map(function (entry) { return entry.grid.scrollLeft; })};
      while (contentRoot.firstChild) { saved.nodes.push(contentRoot.removeChild(contentRoot.firstChild)); }
      viewCache.push(saved);
    }
    for (i = viewCache.length - 1; i >= 0; i -= 1) {
      if (now - viewCache[i].time > 300000 || (refresh && viewCache[i].id === id)) { viewCache.splice(i, 1); }
      else if (viewCache[i].id === id) { cached = viewCache.splice(i, 1)[0]; }
    }
    while (viewCache.length > 2) { viewCache.shift(); }
    selected = id; generation += 1; sections = []; contentRoot.innerHTML = ''; retry.className = 'hidden';
    for (var i = 0; i < menu.length; i += 1) { menu[i].setAttribute('aria-pressed', menu[i].viewId === id ? 'true' : 'false'); }
    status.textContent = id === 'home' ? 'Your local library · Up to 100 titles per row' : 'Select a poster for details';
    if (cached) {
      sections = cached.sections; viewStarted = cached.time;
      for (i = 0; i < cached.nodes.length; i += 1) { contentRoot.appendChild(cached.nodes[i]); }
      for (i = 0; i < sections.length; i += 1) { sections[i].grid.scrollLeft = cached.scrolls[i]; }
      focusRows(0, nav.position()[1]); return;
    }
    viewStarted = now;
    focusRows(0, nav.position()[1]);
    if (id === 'home') {
      section('Continue Watching', '/api/feed/continue', 'Nothing in progress for this Plex account.', true);
      section('On Deck', '/api/feed/ondeck', 'No next episodes are queued by Plex.', true);
      for (i = 0; i < libraries.length; i += 1) {
        section('Recently Added · ' + libraries[i].title, '/api/library/' + libraries[i].id + '/recent',
          'No recently added titles in this library.', true);
      }
    } else if (id === 'watchlist') {
      section('Watchlist', '/api/watchlist', 'No Watchlist titles matched your local libraries.', false);
    } else {
      var title = 'Library';
      for (i = 0; i < menu.length; i += 1) { if (menu[i].viewId === id) { title = menu[i].textContent; } }
      section(title, '/api/library/' + id, 'This library has no movie or TV titles.', false);
    }
  }
  function back() {
    if (window.VidPlexPlayer.stop()) { return; }
    if (!inDetails) { focusRows(0, 0); return; }
    if (detailTrail.length) { openDetails(detailTrail.pop()); return; }
    inDetails = false; detailRequest += 1; nav.scrollDetails(false);
    document.getElementById('details-view').className = 'hidden';
    document.getElementById('library-view').className = '';
    if (homeDirty && selected === 'home') { homeDirty = false; loadView('home', true); }
    else { focusRows(0, 0, savedElement); }
  }
  function openDetails(id, child, autoStart) {
    if (!inDetails) { detailTrail = []; }
    if (child && currentDetail) { detailTrail.push(currentDetail); }
    currentDetail = id;
    document.getElementById('back').textContent = detailTrail.length ? '← Back' : '← Back to library';
    if (!inDetails) { savedElement = document.activeElement; } inDetails = true; nav.scrollDetails(true); var ticket = ++detailRequest;
    document.getElementById('library-view').className = 'hidden';
    document.getElementById('details-view').className = '';
    var content = document.getElementById('detail-content'); content.innerHTML = '';
    content.appendChild(text('p', 'Loading details…')); nav.set([[document.getElementById('back')]]);
    request('/api/item/' + id, function (error, item) {
      if (!inDetails || ticket !== detailRequest) { return; }
      content.innerHTML = '';
      if (error) { content.appendChild(text('p', error + ' Go back and select the poster to retry.')); return; }
      if (item.background) {
        var bg = document.createElement('img'); bg.className = 'backdrop'; bg.alt = ''; bg.src = item.background;
        bg.onerror = function () { bg.className = 'hidden'; }; content.appendChild(bg);
      }
      var cover = artwork(item.poster, item.title); cover.className += ' detail-poster'; content.appendChild(cover);
      var info = document.createElement('div'); info.className = 'detail-info';
      info.appendChild(text('p', item.type === 'movie' ? 'MOVIE' : 'TV', 'eyebrow'));
      info.appendChild(text('h1', item.title));
      if (item.type === 'episode') { info.appendChild(text('p', episodeLabel(item))); }
      var bits = []; if (item.year) { bits.push(item.year); }
      if (item.duration) { bits.push(Math.round(item.duration / 60000) + ' min'); }

      info.appendChild(text('p', bits.join(' · '), 'metadata'));
      var ratings = item.ratings || [], ratingRow = document.createElement('div');
      ratingRow.className = 'ratings';
      for (var ri = 0; ri < ratings.length; ri += 1) {
        ratingRow.appendChild(text('span', ratings[ri].label + ' ' + ratings[ri].score, 'rating-badge'));
      }
      if (ratings.length) { info.appendChild(ratingRow); }
      info.appendChild(text('p', item.summary, 'summary'));
      if (item.cast.length) { info.appendChild(text('p', 'Cast: ' + item.cast.join(', '), 'cast')); }
      content.appendChild(info); playbackActions(item, info, ticket, autoStart);
    });
  }
  function playbackActions(item, info, ticket, autoStart) {
    var actions = document.createElement('div'); actions.className = 'detail-actions'; info.insertBefore(actions, info.querySelector('.summary'));
    var message = text('p', 'Loading playback options…', 'phase-note'); actions.appendChild(message);
    var buttons = [], backButton = document.getElementById('back');
    function focus(keep) {
      var rows = [[backButton]], top = null, r = 0, c = 0;
      for (var i = 0; i < buttons.length; i += 1) {
        var buttonTop = buttons[i].getBoundingClientRect().top;
        if (top === null || Math.abs(buttonTop - top) > 2) {
          rows.push([]); top = buttonTop;
        }
        rows[rows.length - 1].push(buttons[i]);
        if (buttons[i] === keep) { r = rows.length - 1; c = rows[r].length - 1; }
      }
      nav.scrollDetails(false); nav.set(rows, r, c);
    }
    function add(label, click) {
      var button = text('button', label); button.type = 'button';
      button.onclick = function () { nav.adopt(button); click(button); };
      buttons.push(button); actions.appendChild(button); return button;
    }
    if (item.type === 'show' || item.type === 'season') {
      var seasons = item.type === 'show';
      actions.className += seasons ? ' season-list' : ' episode-list';
      function episodes(offset) {
        message.textContent = seasons ? 'Loading seasons…' : 'Loading episodes…';
        request((seasons ? '/api/show/' + item.id + '/seasons' : '/api/season/' + item.id + '/episodes') + '?offset=' + offset, function (error, data) {
          if (!inDetails || ticket !== detailRequest) { return; }
          while (actions.lastChild !== message) { actions.removeChild(actions.lastChild); } buttons = [];
          if (error) { message.textContent = error; add(seasons ? 'Retry seasons' : 'Retry episodes', function () { episodes(offset); }); }
          else {
            message.textContent = data.items.length ? (seasons ? 'Choose a season' : 'Choose an episode') : 'No items available.';
            for (var i = 0; i < data.items.length; i += 1) {
              (function (entry) {
                var button = add(seasons ? entry.title : episodeLabel(entry), function () { openDetails(entry.id, true); });
                if (seasons) {
                  button.textContent = ''; button.className = 'poster';
                  button.appendChild(artwork(entry.poster, entry.title));
                  button.appendChild(text('span', entry.title, 'poster-title'));
                }
              }(data.items[i]));
            }
            if (data.previous !== null) { add(seasons ? 'Previous seasons' : 'Previous episodes', function () { episodes(data.previous); }); }
            if (data.next !== null) { add(seasons ? 'Next seasons' : 'Next episodes', function () { episodes(data.next); }); }
          }
          focus(offset ? buttons[0] : backButton);
        });
      }
      episodes(0); return;
    }
    request('/api/playback/' + item.id + '/options', function (error, options) {
      if (!inDetails || ticket !== detailRequest) { return; }
      if (error) { message.textContent = error; return; }
      var audio = options.audio, subs = [{id: '0', label: 'Off'}].concat(options.subtitles), ai = 0, si = 0;
      for (var i = 0; i < audio.length; i += 1) { if (audio[i].selected) { ai = i; } }
      for (var sj = 1; sj < subs.length; sj += 1) { if (subs[sj].selected) { si = sj; } }
      message.textContent = 'Choose tracks, then Play. Subtitles are rendered by Plex.';
      function begin(button, offset) {
        window.VidPlexPlayer.start(item.id, {offset: offset, audio: audio.length ? audio[ai].id : '', subtitle: subs[si].id}, function (error, stoppedAt, ended) {
          if (!inDetails || ticket !== detailRequest) { return; }
          homeDirty = true; viewCache = [];
          if (selected === 'home') {
            for (var refreshIndex = 0; refreshIndex < sections.length; refreshIndex += 1) {
              if (sections[refreshIndex].url === '/api/feed/continue' || sections[refreshIndex].url === '/api/feed/ondeck') {
                loadSection(sections[refreshIndex], generation);
              }
            }
          }
          if (!error && ended && item.type === 'episode' && autoplay) {
            message.textContent = 'Finding next episode…'; focus(backButton);
            request('/api/playback/' + item.id + '/next', function (nextError, data) {
              if (!inDetails || ticket !== detailRequest) { return; }
              if (nextError) { message.textContent = nextError; return; }
              if (data.item) { detailTrail = []; openDetails(data.item.id, false, true); }
              else { openDetails(item.id); }
            }); return;
          }
          if (!error && typeof stoppedAt === 'number') { openDetails(item.id); return; }
          nav.scrollDetails(true); focus(button);
          message.textContent = error || 'Playback stopped. Select Play or return to your library.';
        });
      }
      if (options.resume > 0 && options.resume < options.duration) { add('Resume', function (button) { begin(button, options.resume); }); }
      add('Play from beginning', function (button) { begin(button, 0); });
      if (audio.length) { add('Audio: ' + audio[ai].label, function (button) { ai = (ai + 1) % audio.length; button.textContent = 'Audio: ' + audio[ai].label; focus(button); }); }
      add('Subtitles: ' + subs[si].label, function (button) { si = (si + 1) % subs.length; button.textContent = 'Subtitles: ' + subs[si].label; focus(button); });
      if (item.type === 'episode') {
        add('Autoplay next: ' + (autoplay ? 'On' : 'Off'), function (button) {
          autoplay = !autoplay; button.textContent = 'Autoplay next: ' + (autoplay ? 'On' : 'Off'); focus(button);
        });
      }
      var languages = [['en', 'English'], ['es', 'Spanish'], ['fr', 'French'], ['de', 'German'], ['it', 'Italian'], ['pt', 'Portuguese'], ['ja', 'Japanese'], ['zh', 'Chinese'], ['ko', 'Korean'], ['nl', 'Dutch']], languageIndex = 0;
      add('Subtitle search: English', function (button) {
        languageIndex = (languageIndex + 1) % languages.length;
        button.textContent = 'Subtitle search: ' + languages[languageIndex][1]; focus(button);
      });
      var searchButton = add('Find subtitles', function () {
        if (searchButton.disabled) { return; }
        var overlay = document.createElement('div'); overlay.className = 'subtitle-menu';
          overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-modal', 'true');
          overlay.setAttribute('aria-label', 'Find subtitles');
          var panel = document.createElement('div'); panel.className = 'subtitle-menu-panel'; overlay.appendChild(panel);
          panel.appendChild(text('h2', 'Find subtitles'));
          var menuMessage = text('p', 'Searching Plex for subtitles…'); panel.appendChild(menuMessage);
          var closeButton = text('button', 'Cancel'), menuRows = [[closeButton]], closed = false;
          closeButton.type = 'button'; panel.appendChild(closeButton);
          function closeMenu() {
            if (closed) { return; } closed = true;
            document.body.removeChild(overlay); nav.back(back); focus(searchButton);
          }
          closeButton.onclick = closeMenu; document.body.appendChild(overlay);
          nav.back(closeMenu); nav.scrollDetails(false); nav.set(menuRows);
        window.VidPlexPlayer.post('/api/playback/' + item.id + '/subtitles/search', {language: languages[languageIndex][0]}, function (error, data) {
          if (closed || !inDetails || ticket !== detailRequest) { return; }
            menuMessage.textContent = error || (data.items.length ? 'Choose a subtitle to download through Plex.' : 'No subtitles found. Close and try another language.');
            if (!error) {
            for (var n = 0; n < data.items.length; n += 1) {
              (function (result) {
                var resultButton = text('button', result.label); resultButton.type = 'button';
                  panel.appendChild(resultButton); menuRows.push([resultButton]);
                  resultButton.onclick = function () {
                    closeMenu();
                    var button = searchButton;
                    button.disabled = true; message.textContent = 'Requesting subtitle download…';
                    window.VidPlexPlayer.post('/api/playback/' + item.id + '/subtitles/download', {id: result.id}, function (downloadError) {
                    if (!inDetails || ticket !== detailRequest) { return; }
                    button.disabled = false;
                    if (downloadError) { message.textContent = downloadError; focus(button); return; }
                    var attempts = 0;
                    function pollTracks() {
                      if (!inDetails || ticket !== detailRequest) { return; }
                      request('/api/playback/' + item.id + '/options', function (pollError, updated) {
                        if (!inDetails || ticket !== detailRequest) { return; }
                        if (!pollError && updated.subtitles.some(function (track) { return !options.subtitles.some(function (old) { return old.id === track.id; }); })) {
                          openDetails(item.id); return;
                        }
                        attempts += 1;
                        if (attempts < 10 && !pollError) { window.setTimeout(pollTracks, 1000); }
                        else { message.textContent = pollError || 'Plex accepted the download. Reopen details to refresh tracks if it is still processing.'; focus(button); }
                      });
                    }
                    message.textContent = 'Waiting for Plex to add the subtitle…'; pollTracks();
                  });
                };
              }(data.items[n]));
            }
          }
          nav.set(menuRows, menuRows.length > 1 ? 1 : 0, 0);
        });
      });

      focus(document.activeElement);
      if (autoStart) { begin(buttons[0], 0); }
    });
  }
  function addMenu(title, id) {
    var button = text('button', title); button.type = 'button'; button.viewId = id;
    button.onclick = function () { nav.adopt(button); loadView(id === 'refresh' ? selected : id, id === 'refresh'); };
    menu.push(button); document.getElementById('libraries').appendChild(button);
  }
  function start() {
    if (window.location.protocol === 'file:') {
      status.textContent = 'Start the Python helper, then open http://localhost:8765/ on that computer.';
      retry.className = 'hidden'; nav.set([]); return;
    }
    status.textContent = 'Connecting to your local Plex server…'; retry.className = 'hidden'; nav.set([]);
    request('/api/libraries', function (error, data) {
      if (error) { status.textContent = error; retry.className = ''; focusRows(); return; }
      document.getElementById('libraries').innerHTML = ''; menu = [];
      libraries = data.libraries;
      addMenu('Home', 'home');
      for (var i = 0; i < data.libraries.length; i += 1) { addMenu(data.libraries[i].title, data.libraries[i].id); }
      addMenu('Watchlist', 'watchlist'); addMenu('Refresh', 'refresh'); loadView('home');
    });
  }
  retry.onclick = start; document.getElementById('back').onclick = back; nav.back(back); start();
}());
