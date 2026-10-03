// Researcher panel. Hidden from participants: open the page with ?admin=1 once per
// browser session to show the gear button (?admin=0 hides it again).
window.V2S = window.V2S || {};

V2S.admin = (() => {
  const cfg = V2S.config;
  const { el, logEvent, formatBytes, downloadBlob } = V2S.util;
  let api = null;

  function init(appApi) {
    api = appApi;
    const params = new URLSearchParams(window.location.search);
    try {
      if (params.get('admin') === '1') sessionStorage.setItem('v2s_admin', '1');
      if (params.get('admin') === '0') sessionStorage.removeItem('v2s_admin');
    } catch (error) { /* ignore */ }
    const enabled = sessionStorage.getItem('v2s_admin') === '1';
    el('adminButton').hidden = !enabled;
    el('adminButton').addEventListener('click', open);
    el('adminClose').addEventListener('click', close);
    el('adminPanel').addEventListener('click', event => { if (event.target === el('adminPanel')) close(); });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !el('adminPanel').hidden) close();
    });
  }

  function busy() {
    return ['recording', 'finishing', 'checking', 'saved'].includes(V2S.session.getState());
  }

  async function open() {
    if (busy()) return;
    await render();
    el('adminPanel').hidden = false;
    el('adminClose').focus();
  }

  function close() {
    el('adminPanel').hidden = true;
  }

  // ---- tiny DOM helpers ----
  function node(tag, props = {}, children = []) {
    const element = document.createElement(tag);
    Object.entries(props).forEach(([key, value]) => {
      if (key === 'text') element.textContent = value;
      else if (key === 'on') Object.entries(value).forEach(([event, handler]) => element.addEventListener(event, handler));
      else if (key in element) element[key] = value;
      else element.setAttribute(key, value);
    });
    children.filter(Boolean).forEach(child => element.append(child));
    return element;
  }

  const section = (title, children) => node('section', { className: 'admin-section' }, [node('h3', { text: title }), ...children]);
  const button = (label, onClick, variant = 'btn-secondary') => node('button', { type: 'button', className: `btn ${variant}`, text: label, on: { click: onClick } });
  const buttons = list => node('div', { className: 'admin-buttons' }, list);
  const note = text => node('p', { className: 'admin-note', text });

  function kv(pairs) {
    const list = node('dl', { className: 'admin-kv' });
    pairs.forEach(([key, value]) => list.append(node('dt', { text: key }), node('dd', { text: value == null || value === '' ? '—' : String(value) })));
    return list;
  }

  function select(id, options, value) {
    const element = node('select', { id });
    options.forEach(([optionValue, label]) => element.append(node('option', { value: optionValue, text: label })));
    element.value = String(value);
    return element;
  }

  function describePosition(state) {
    if (!state.material || !state.progress) return '—';
    const index = state.progress.currentIndex;
    const { warmupCount, formalCount } = state.material;
    if (state.progress.completed) return `all ${formalCount} done`;
    if (index < warmupCount) return `warm-up ${index + 1} of ${warmupCount}`;
    return `sentence ${index - warmupCount + 1} of ${formalCount}`;
  }

  async function saveProgress(state) {
    await V2S.storage.saveParticipantProgress(state.progress);
  }

  async function restart() {
    close();
    await api.restartSession();
  }

  // ---- panel ----
  async function render() {
    const state = api.state();
    const body = el('adminBody');
    body.replaceChildren();

    const validId = value => /^[A-Z0-9][A-Z0-9_-]{0,23}$/.test(value);

    body.append(section('Participant', [
      kv([['ID', state.participantId], ['Sentence set', cfg.SETS[state.setKey] ? cfg.SETS[state.setKey].label : state.setKey], ['Position', describePosition(state)]]),
      buttons([button('Switch participant…', async () => {
        const raw = window.prompt('New participant ID (letters, numbers, dashes):', '');
        if (raw === null) return;
        const id = raw.trim().toUpperCase();
        if (!validId(id)) return window.alert('That ID is not valid.');
        const key = V2S.storage.progressKey(id, state.setKey);
        if (!(await V2S.storage.getProgress(key))) await V2S.storage.createParticipantProgress(id, state.setKey, null);
        await api.setParticipant(id);
        logEvent('admin_switch_participant', { participantId: id });
        await restart();
      })])
    ]));

    const setSelect = select('adminSet', Object.entries(cfg.SETS).map(([key, set]) => [key, set.label]), state.setKey);
    body.append(section('Sentence set', [
      setSelect,
      buttons([button('Use this set', async () => {
        if (setSelect.value === state.setKey) return;
        if (!window.confirm('Switch sentence set? Progress is kept separately for each set.')) return;
        await api.setSetKey(setSelect.value);
        logEvent('admin_set', { setKey: setSelect.value });
        await restart();
      })])
    ]));

    const jumpInput = node('input', { type: 'number', min: '1', id: 'adminJump', placeholder: 'Sentence #' });
    body.append(section('Progress', [
      node('div', { className: 'admin-row' }, [jumpInput, button('Go', async () => {
        const n = Number(jumpInput.value);
        if (!state.material || !Number.isInteger(n) || n < 1 || n > state.material.formalCount) return window.alert(`Enter a number from 1 to ${state.material ? state.material.formalCount : '?'}.`);
        state.progress.currentIndex = state.material.warmupCount + n - 1;
        state.progress.completed = false;
        await saveProgress(state);
        logEvent('admin_jump', { to: state.progress.currentIndex });
        await restart();
      })]),
      buttons([
        button('Go to warm-up 1', async () => {
          state.progress.currentIndex = 0;
          state.progress.completed = false;
          await saveProgress(state);
          logEvent('admin_jump', { to: 0 });
          await restart();
        }),
        button('Reset progress', async () => {
          if (!window.confirm('Reset this participant to the first warm-up sentence and show the tutorial again? Recordings are not deleted.')) return;
          Object.assign(state.progress, { currentIndex: 0, completed: false, completedAt: null, tutorialStep: 0, tutorialTakes: 0 });
          await saveProgress(state);
          logEvent('admin_reset_progress', {});
          await restart();
        }, 'btn-danger')
      ])
    ]));

    const takes = await V2S.storage.listTakeSummaries();
    const bytes = takes.reduce((sum, take) => sum + take.size, 0);
    const estimate = await V2S.storage.storageEstimate();
    body.append(section('Recordings on this device', [
      kv([
        ['Cached takes', takes.length],
        ['Cached size', formatBytes(bytes)],
        ['Storage used', estimate ? `${(estimate.ratio * 100).toFixed(1)}% of ${formatBytes(estimate.quota)}` : 'unknown']
      ]),
      buttons([
        V2S.exporter.getSaveMode() === 'folder'
          ? button('Write them to the folder', async () => {
            if (!V2S.exporter.isFolderActive() && (await V2S.exporter.requestFolderPermission()) !== 'granted') {
              return window.alert('The browser did not allow access to the folder.');
            }
            const result = await V2S.exporter.flushPendingToFolder();
            window.alert(`Written: ${result.written}. Not written: ${result.failed}.`);
            await render();
          })
          : button('Download ZIP now', async () => {
            close();
            await api.runZipSave('manual');
            await open();
          }),
        button('Delete cached recordings…', async () => {
          if (!takes.length) return;
          if (!window.confirm(`Permanently delete ${takes.length} cached recordings from this browser? Only do this after they are saved.`)) return;
          if (!window.confirm('Are you sure? This cannot be undone.')) return;
          await V2S.storage.deleteTakes(takes.map(take => take.id));
          logEvent('admin_delete_cached', { count: takes.length });
          await render();
        }, 'btn-danger')
      ])
    ]));

    const folderSupported = V2S.exporter.folderSupported();
    body.append(section('Saving', [
      kv([['Mode', V2S.exporter.getSaveMode() === 'folder' ? `Folder “${V2S.exporter.folderName() || '?'}”` : 'ZIP download'], ['Folder access', V2S.exporter.status().permission]]),
      folderSupported ? buttons([
        button('Choose folder…', async () => {
          try {
            const name = await V2S.exporter.chooseFolder(); // first: browser shows its picker
            if (name) {
              logEvent('admin_folder', { name });
              await V2S.exporter.flushPendingToFolder();
            }
          } catch (error) {
            window.alert('That folder could not be used.');
          }
          await render();
        }),
        button('Use ZIP files', async () => {
          await V2S.exporter.setSaveMode('zip');
          await render();
        })
      ]) : note('This browser cannot save to a folder; recordings are saved as ZIP files.')
    ]));

    const media = V2S.media.getSettings();
    const resolution = select('adminResolution', [['1080p', '1080p (1920×1080)'], ['720p', '720p (1280×720)'], ['480p', '480p'], ['360p', '360p'], ['auto', 'Camera default']], media.resolution);
    const bitrate = select('adminBitrate', [['8000000', '8 Mbps'], ['12000000', '12 Mbps'], ['15000000', '15 Mbps'], ['25000000', '25 Mbps'], ['40000000', '40 Mbps']], media.bitrate);
    const fps = select('adminFps', [['30', '30 fps'], ['60', '60 fps']], media.fps);
    const audioMode = select('adminAudio', [['raw', 'Raw (no browser processing)'], ['fallback', 'Browser default processing']], media.audioMode);
    const mirror = node('input', { type: 'checkbox', id: 'adminMirror', checked: Boolean(media.mirror) });
    body.append(section('Camera and microphone', [
      node('div', { className: 'admin-row' }, [node('label', { htmlFor: 'adminResolution', text: 'Resolution' }), resolution]),
      node('div', { className: 'admin-row' }, [node('label', { htmlFor: 'adminBitrate', text: 'Video bitrate' }), bitrate]),
      node('div', { className: 'admin-row' }, [node('label', { htmlFor: 'adminFps', text: 'Frame rate' }), fps]),
      node('div', { className: 'admin-row' }, [node('label', { htmlFor: 'adminAudio', text: 'Audio' }), audioMode]),
      node('div', { className: 'admin-row' }, [node('label', { htmlFor: 'adminMirror', text: 'Mirror the preview' }), mirror]),
      buttons([button('Save and restart camera', async () => {
        const next = { resolution: resolution.value, bitrate: Number(bitrate.value), fps: Number(fps.value), audioMode: audioMode.value, mirror: mirror.checked };
        await V2S.storage.setSetting('mediaSettings', next);
        V2S.media.setSettings(next);
        logEvent('admin_media_settings', next);
        await restart();
      })]),
      note('Changes take effect when the camera restarts, never in the middle of a recording.')
    ]));

    const theme = select('adminTheme', [['light', 'Light'], ['dark', 'Dark']], document.documentElement.getAttribute('data-theme') || 'light');
    theme.addEventListener('change', async () => {
      api.applyTheme(theme.value);
      await V2S.storage.setSetting('theme', theme.value);
      logEvent('admin_theme', { theme: theme.value });
    });
    body.append(section('Display', [node('div', { className: 'admin-row' }, [node('label', { htmlFor: 'adminTheme', text: 'Theme' }), theme])]));

    const snapshot = V2S.media.snapshot();
    const video = snapshot.video.settings || {};
    const audio = snapshot.audio.settings || {};
    body.append(section('Diagnostics', [
      kv([
        ['App version', cfg.APP_VERSION],
        ['Camera', video.width ? `${video.width}×${video.height} @ ${Number(video.frameRate || 0).toFixed(1)} fps` : 'off'],
        ['Microphone', audio.sampleRate ? `${audio.sampleRate} Hz, ${audio.channelCount || '?'} ch` : 'off'],
        ['Audio processing', V2S.media.getAudioConstraintMode()],
        ['Session', V2S.util.getSessionId()]
      ]),
      buttons([button('Download event log', async () => {
        const events = await V2S.storage.getAllEvents();
        downloadBlob(new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), participantId: state.participantId, events }, null, 2)], { type: 'application/json' }), `v2s-events-${V2S.util.timestamp()}.json`);
      })])
    ]));
  }

  return { init, open, close };
})();
