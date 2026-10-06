// Settings: the gear button in the top bar (always there, except while recording).
// Laid out like the Settings app: a short list of sections, each opening as its own page
// with a back button, so only one topic is on screen at a time. The research team's
// options keep the earlier page's names. Anything destructive is red and asks first, in
// plain words.
window.V2S = window.V2S || {};

V2S.settings = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const t = copy.settings;
  const { el, logEvent, formatBytes, downloadBlob } = V2S.util;
  let api = null;
  let page = 'main';

  // Page id → title and builder. The ids stay stable for callers (open('settingsSaving')).
  const PAGES = {
    main: { title: () => t.title, build: mainPage },
    settingsProgress: { title: () => t.participant, build: progressPage },
    settingsSaving: { title: () => t.saving, build: savingPage },
    settingsDevices: { title: () => t.devices, build: devicesPage },
    settingsQuality: { title: () => t.quality, build: qualityPage },
    settingsAbout: { title: () => t.about, build: aboutPage }
  };

  function init(appApi) {
    api = appApi;
    el('settingsButton').addEventListener('click', () => open());
    el('settingsClose').addEventListener('click', close);
    el('settingsBack').addEventListener('click', () => show('main'));
    el('settingsPanel').addEventListener('click', event => { if (event.target === el('settingsPanel')) close(); });
    el('settingsClose').textContent = t.done;
    el('settingsBackLabel').textContent = t.back;
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !event.repeat && !el('settingsPanel').hidden && !V2S.ui.isDialogOpen()) close();
    });
  }

  function canOpen() {
    return !['starting', 'recording', 'finishing', 'checking'].includes(V2S.session.getState()) && !V2S.ui.isDialogOpen();
  }

  async function open(pageId) {
    if (!canOpen()) return;
    V2S.input.setEnabled(false);
    el('settingsPanel').hidden = false;
    await show(PAGES[pageId] ? pageId : 'main');
    el('settingsClose').focus({ preventScroll: true });
    logEvent('settings_open', { section: pageId || null });
  }

  function close() {
    if (el('settingsPanel').hidden) return;
    // Space and Enter go back to Start, not to a button left focused in the sheet.
    if (el('settingsPanel').contains(document.activeElement)) document.activeElement.blur();
    el('settingsPanel').hidden = true;
    if (api) api.onSettingsClosed();
  }

  const isOpen = () => !el('settingsPanel').hidden;

  async function show(pageId) {
    page = pageId;
    await render();
    el('settingsBody').closest('.sheet').scrollTop = 0;
  }

  // The page's title and content change together, once the content is ready.
  async function render() {
    const shown = page;
    const current = PAGES[shown] || PAGES.main;
    const content = await current.build();
    if (shown !== page) return;   // another page was chosen meanwhile
    el('settingsTitle').textContent = current.title();
    el('settingsBack').hidden = shown === 'main';
    el('settingsBody').replaceChildren(content);
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

  const CHEVRON = '<svg viewBox="0 0 9 15"><path d="m1.5 1.5 6 6-6 6"/></svg>';

  // A group: an optional small title, rounded rows, an optional footnote.
  function group(rows, { title, foot, id } = {}) {
    const list = rows.filter(Boolean);
    if (!list.length) return null;
    return node('section', { className: 'group', ...(id ? { id } : {}) }, [
      title ? node('p', { className: 'group-title', text: title }) : null,
      node('div', { className: 'group-list' }, list),
      foot ? node('p', { className: 'group-foot', text: foot }) : null
    ]);
  }

  const value = (label, text) => node('div', { className: 'row' }, [
    node('span', { className: 'row-label', text: label }),
    node('span', { className: 'row-value', text: text == null || text === '' ? '—' : String(text) })
  ]);

  // A row that opens a page.
  function nav(label, text, target) {
    const chevron = node('span', { className: 'row-chevron', 'aria-hidden': 'true' });
    chevron.innerHTML = CHEVRON;
    return node('button', { type: 'button', className: 'row', on: { click: () => show(target) } }, [
      node('span', { className: 'row-label', text: label }),
      text ? node('span', { className: 'row-value', text }) : null,
      chevron
    ]);
  }

  // A row that does something: blue, or red when it removes something.
  const action = (label, onClick, danger = false) => node('button', {
    type: 'button',
    className: `row ${danger ? 'row-danger' : 'row-action'}`,
    text: label,
    on: { click: onClick }
  });

  const control = (label, element) => node('label', { className: 'row row-control', htmlFor: element.id }, [
    node('span', { className: 'row-label', text: label }),
    element
  ]);

  const warnRow = text => node('div', { className: 'row row-warn', text });

  function select(id, options, selected) {
    const element = node('select', { id });
    options.forEach(([optionValue, label]) => element.append(node('option', { value: optionValue, text: label })));
    element.value = String(selected);
    return element;
  }

  const fragment = parts => {
    const box = document.createDocumentFragment();
    parts.filter(Boolean).forEach(part => box.append(part));
    return box;
  };

  // ---- pages ----
  async function mainPage() {
    const state = api.state();
    const unsaved = await api.pendingCount().catch(() => 0);
    const media = V2S.media.getSettings();
    return fragment([
      group([
        value(t.participantId, state.participantId),
        value(t.position, describePosition(state))
      ]),
      group([
        nav(t.participant, '', 'settingsProgress'),
        nav(t.saving, unsaved ? t.notSaved(unsaved) : t.allSaved, 'settingsSaving'),
        nav(t.devices, '', 'settingsDevices'),
        nav(t.quality, `${media.resolution || ''}`, 'settingsQuality')
      ]),
      group([themeRow()]),
      group([nav(t.about, '', 'settingsAbout')]),
      group([action(t.signOut, async () => {
        if (!(await V2S.ui.confirm({ title: t.signOut, body: t.signOutConfirm, yes: t.signOutYes, caution: true }))) return;
        await api.signOut();
      }, true)])
    ]);
  }

  function themeRow() {
    const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const switcher = node('div', { className: 'segmented', role: 'group', 'aria-label': t.theme });
    [['light', t.light], ['dark', t.dark]].forEach(([theme, label]) => {
      switcher.append(node('button', {
        type: 'button',
        text: label,
        'aria-pressed': String(theme === current),
        on: { click: async () => { await api.setTheme(theme); await render(); } }
      }));
    });
    return node('div', { className: 'row' }, [node('span', { className: 'row-label', text: t.theme }), switcher]);
  }

  async function devicesPage() {
    const devices = await V2S.media.listDevices().catch(() => ({ cameras: [], microphones: [] }));
    const now = V2S.media.current();
    const media = V2S.media.getSettings();
    // Without a list (no permission yet, or the browser hides it) show what is in use.
    const cameras = devices.cameras.length ? devices.cameras.map(d => [d.id, d.label]) : [[now.cameraId || '', now.camera || copy.check.defaultDevice]];
    const microphones = devices.microphones.length ? devices.microphones.map(d => [d.id, d.label]) : [[now.microphoneId || '', now.microphone || copy.check.defaultDevice]];
    const camera = select('setCamera', cameras, now.cameraId || media.videoDeviceId || cameras[0][0]);
    const microphone = select('setMicrophone', microphones, now.microphoneId || media.audioDeviceId || microphones[0][0]);
    camera.disabled = devices.cameras.length < 2;
    microphone.disabled = devices.microphones.length < 2;
    const apply = async () => {
      const next = { ...V2S.media.getSettings(), videoDeviceId: camera.value || null, audioDeviceId: microphone.value || null };
      await V2S.storage.setSetting('mediaSettings', next);
      V2S.media.setSettings(next);
      logEvent('settings_devices', { videoDeviceId: next.videoDeviceId, audioDeviceId: next.audioDeviceId });
      await api.reopenMedia();
      await render();
    };
    camera.addEventListener('change', apply);
    microphone.addEventListener('change', apply);
    const snap = V2S.media.snapshot();
    const video = snap.video.settings || {};
    const audio = snap.audio.settings || {};
    const audioMode = { raw: t.audioRaw, fallback: t.audioBrowser, fallback_auto: t.audioBrowser }[V2S.media.getAudioConstraintMode()] || '—';
    const inUse = [
      video.width ? `${video.width}×${video.height}${Number(video.frameRate) > 0 ? ` · ${Math.round(Number(video.frameRate))} fps` : ''}` : null,
      audio.sampleRate ? `${(audio.sampleRate / 1000).toFixed(audio.sampleRate % 1000 ? 1 : 0)} kHz · ${audio.channelCount || 1} ch · ${audioMode}` : null
    ].filter(Boolean).join(' / ');
    return fragment([
      group([
        control(t.camera, camera),
        control(t.microphone, microphone),
        now.bluetooth ? warnRow(copy.check.bluetooth) : null
      ], { foot: `${t.actual}: ${inUse || '—'}. ${t.devicesNote}`, id: 'settingsDevicesList' }),
      group([action(t.testAgain, () => { close(); api.showCheck(); })])
    ]);
  }

  async function savingPage() {
    // Counts only: reading the recordings themselves would load every video.
    const [allIds, backupIds] = await Promise.all([V2S.storage.takeIds(), V2S.storage.exportedIds()]);
    const backupSet = new Set(backupIds);
    const backups = allIds.filter(id => backupSet.has(id));
    const unsaved = allIds.filter(id => !backupSet.has(id));
    const estimate = await V2S.storage.storageEstimate();
    const folderMode = V2S.exporter.getSaveMode() === 'folder';
    const folderSupported = V2S.exporter.folderSupported();
    const status = V2S.exporter.status();
    const saveNow = action(t.saveNow, async () => {
      if (folderMode) {
        if (!V2S.exporter.isFolderActive() && (await V2S.exporter.requestFolderPermission()) !== 'granted') {
          await V2S.ui.alert(t.saving, t.folderNotAllowed);
          return render();
        }
        const result = await V2S.exporter.flushPendingToFolder();
        await V2S.ui.alert(t.saving, result.written || result.failed ? t.written(result.written, result.failed) : t.nothingToSave);
      } else {
        if (!unsaved.length) {
          await V2S.ui.alert(t.saving, t.nothingToSave);
          return;
        }
        close();
        await api.runZipSave('manual');
        await open('settingsSaving');
        return;
      }
      await render();
    });
    const saveBackups = backups.length ? action(t.saveBackups, async () => {
      close();
      await api.runZipSave('backup', null, { backups: true });
      await open('settingsSaving');
    }) : null;
    const chooseFolder = folderSupported ? action(t.chooseFolder, async () => {
      try {
        const name = await V2S.exporter.chooseFolder(); // first: the browser shows its picker
        if (name) {
          logEvent('settings_folder', { name });
          await V2S.exporter.flushPendingToFolder();
        }
      } catch (error) {
        await V2S.ui.alert(t.saving, t.folderFailed);
      }
      await render();
    }) : null;
    const useZip = folderSupported && folderMode ? action(t.useZip, async () => {
      await V2S.exporter.setSaveMode('zip');
      await render();
    }) : null;
    const deleteBackups = backups.length ? action(t.deleteBackups, async () => {
      const ok = await V2S.ui.confirm({ title: t.deleteBackups.replace('…', ''), body: t.deleteBackupsConfirm(backups.length), yes: t.confirm, caution: true });
      if (!ok) return;
      await V2S.storage.deleteTakes(backups);
      logEvent('settings_delete_backups', { count: backups.length });
      await render();
    }, true) : null;
    // Recordings that are not saved anywhere yet are never deleted from here.
    const deleteAll = action(t.deleteCached, async () => {
      if (!allIds.length) return V2S.ui.alert(t.deleteCached.replace('…', ''), t.nothingStored);
      if (unsaved.length) return V2S.ui.alert(t.deleteCached.replace('…', ''), t.deleteUnsaved(unsaved.length));
      const ok = await V2S.ui.confirm({ title: t.deleteCached.replace('…', ''), body: t.deleteConfirm(allIds.length, 0), yes: t.confirm, caution: true });
      if (!ok) return;
      await V2S.storage.deleteTakes(allIds);
      logEvent('settings_delete_cached', { count: allIds.length, unsaved: unsaved.length });
      await render();
    }, true);
    const notes = [folderSupported ? null : t.noFolderSupport, folderMode ? null : t.backupNote].filter(Boolean).join(' ');
    return fragment([
      group([
        value(t.mode, folderMode ? t.modeFolder(V2S.exporter.folderName() || '?') : t.modeZip),
        folderMode ? value(t.folderAccess, t.permissionWord(status.permission)) : null,
        value(t.cached, t.cachedValue(unsaved.length)),
        backups.length ? value(t.backups, t.backupsValue(backups.length)) : null,
        value(t.storage, estimate ? `${formatBytes(estimate.usage)} of ${formatBytes(estimate.quota)}` : '—')
      ], { foot: notes, id: 'settingsSavingStatus' }),
      group([saveNow, saveBackups]),
      group([chooseFolder, useZip]),
      group([deleteBackups, deleteAll], { foot: t.deleteCachedNote })
    ]);
  }

  // Short: "Part 2 · 14 of 50" (the main list); long adds the sentence number in the set.
  function describePosition(state, long = false) {
    if (!state.material || !state.progress) return '—';
    const index = state.progress.currentIndex;
    const { warmupCount, formalCount } = state.material;
    if (state.progress.completed) return copy.done.allTitle;
    if (index < warmupCount) return copy.record.practiceOf(index + 1, warmupCount);
    const formal = index - warmupCount;
    const block = Math.floor(formal / cfg.BLOCK_SIZE) + 1;
    const size = Math.min(cfg.BLOCK_SIZE, formalCount - (block - 1) * cfg.BLOCK_SIZE);
    const short = copy.record.whereShort(block, formal % cfg.BLOCK_SIZE + 1, size);
    return long ? `${short} (${formal + 1}/${formalCount})` : short;
  }

  // Everything the earlier page offered for moving around the sentences, under its old
  // names: sentence set, Previous / Next / Skip, go to a sentence, practice (warm-up) on or
  // skipped, Clear progress, plus switching participant and the held-press limit.
  function progressPage() {
    const state = api.state();
    const setSelect = select('setSentenceSet', Object.entries(cfg.SETS).map(([key, set]) => [key, set.label]), state.setKey);
    setSelect.addEventListener('change', async () => {
      if (setSelect.value === state.setKey) return;
      if (!(await V2S.ui.confirm({ title: t.set, body: t.setConfirm }))) {
        setSelect.value = state.setKey;
        return;
      }
      await api.setSetKey(setSelect.value);
      logEvent('settings_set', { setKey: setSelect.value });
      close();
      await api.restartSession();
    });
    const round = state.progress ? V2S.storage.roundOf(state.progress) : 1;
    const parts = [
      group([
        value(t.participantId, state.participantId),
        value(t.position, describePosition(state, true)),
        control(t.set, setSelect)
      ], { foot: Object.values(cfg.SETS).map(set => `${set.label}: ${set.about}.`).join(' '), id: 'settingsProgressStatus' })
    ];
    if (state.participantId && state.progress && state.material) {
      const total = state.material.formalCount;
      const warmup = state.material.warmupCount;
      const index = state.progress.currentIndex;
      const go = async (target, extra = {}, event = 'settings_jump') => {
        logEvent(event, { from: index, to: target });
        close();
        await api.jumpTo(target, extra);
      };
      const jump = node('input', { type: 'number', min: '1', max: String(total), id: 'setJump', inputMode: 'numeric', placeholder: `1–${total}` });
      const jumpGo = node('button', { type: 'button', className: 'btn-text row-go', text: t.jump, on: { click: async () => {
        const n = Number(jump.value);
        if (!Number.isInteger(n) || n < 1 || n > total) return V2S.ui.alert(t.jump, t.jumpInvalid(total));
        await go(warmup + n - 1);
      } } });
      const jumpRow = node('div', { className: 'row' }, [node('label', { className: 'row-label', htmlFor: 'setJump', text: t.jumpLabel(total) }), jump, jumpGo]);
      const hold = select('setHold', [['1000', t.hold1], ['2000', t.hold2], ['3000', t.hold3]], String(V2S.input.getHoldMs()));
      hold.addEventListener('change', async () => {
        V2S.input.setHoldMs(Number(hold.value));
        await V2S.storage.setSetting('holdMs', Number(hold.value));
        logEvent('settings_hold', { holdMs: Number(hold.value) });
      });
      parts.push(
        group([
          action(t.previous, () => go(Math.max(0, index - 1), {}, 'settings_previous')),
          action(t.next, async () => {
            // A mis-tap must not leave a sentence unrecorded without anyone noticing.
            if (!(await V2S.ui.confirm({ title: t.next, body: t.skipConfirm }))) return;
            await go(Math.min(state.material.all.length - 1, index + 1), {}, 'settings_next');
          }),
          jumpRow
        ], { title: t.moveTitle }),
        group([
          index < warmup
            // During "Practise again", skipping goes back to where they were.
            ? action(t.skipPractice, () => go(Number.isInteger(state.progress.resumeIndex) ? state.progress.resumeIndex : warmup, { coachDone: true, howtoSeen: true, resumeIndex: null }, 'settings_skip_practice'))
            : action(t.practiceAgain, async () => {
              if (!(await V2S.ui.confirm({ title: t.practiceAgain, body: t.practiceConfirm }))) return;
              // After the last sentence there is nothing to come back to: practice leads
              // into the next round from its first sentence.
              await go(0, state.progress.completed ? { coachDone: false } : { coachDone: false, resumeIndex: index }, 'settings_practice_again');
            })
        ], { title: t.practiceTitle }),
        group([control(t.holdLabel, hold)], { title: t.holdTitle, foot: t.holdNote })
      );
    }
    parts.push(group([
      action(t.switchParticipant, switchParticipant),
      state.progress ? action(t.reset, async () => {
        const index = state.progress.currentIndex;
        const body = state.progress.completed ? t.resetConfirmNewRound(round + 1) : t.resetConfirm;
        if (!(await V2S.ui.confirm({ title: t.reset.replace('…', ''), body, caution: true }))) return;
        logEvent('settings_clear_progress', { from: index });
        close();
        await api.clearProgress();
      }, true) : null
    ], { title: t.research, foot: state.progress ? t.roundNote(round) : null }));
    return fragment(parts);
  }

  async function switchParticipant() {
    const state = api.state();
    const answer = await V2S.ui.dialog({
      title: t.switchParticipant.replace('…', ''),
      body: [],
      input: { label: t.switchPrompt, placeholder: copy.setup.idPlaceholder },
      actions: [{ label: t.confirm, value: 'ok', variant: 'go' }, { label: t.cancel, value: 'cancel', variant: 'ghost' }],
      dismissValue: 'cancel'
    });
    if (!answer || answer.action !== 'ok') return;
    const id = String(answer.value || '').trim().toUpperCase();
    if (!/^[A-Z0-9][A-Z0-9_-]{0,23}$/.test(id)) return V2S.ui.alert(t.switchParticipant.replace('…', ''), t.switchInvalid);
    const key = V2S.storage.progressKey(id, state.setKey);
    if (!(await V2S.storage.getProgress(key))) await V2S.storage.createParticipantProgress(id, state.setKey, null);
    await api.setParticipant(id);
    logEvent('settings_switch_participant', { participantId: id });
    close();
    await api.restartSession();
  }

  function qualityPage() {
    const media = V2S.media.getSettings();
    const resolution = select('setResolution', cfg.QUALITY_LABELS.resolution, media.resolution);
    const bitrate = select('setBitrate', cfg.QUALITY_LABELS.bitrate, media.bitrate);
    const fps = select('setFps', cfg.QUALITY_LABELS.fps, media.fps);
    const audioMode = select('setAudio', cfg.QUALITY_LABELS.audio, media.audioMode);
    const mirror = node('input', { type: 'checkbox', id: 'setMirror', checked: Boolean(media.mirror) });
    return fragment([
      group([
        control(t.resolution, resolution),
        control(t.bitrate, bitrate),
        control(t.fps, fps),
        control(t.audio, audioMode),
        control(t.mirror, mirror)
      ], { foot: t.qualityNote, id: 'settingsQualityList' }),
      group([action(t.applyQuality, async () => {
        const next = { ...V2S.media.getSettings(), resolution: resolution.value, bitrate: Number(bitrate.value), fps: Number(fps.value), audioMode: audioMode.value, mirror: mirror.checked };
        await V2S.storage.setSetting('mediaSettings', next);
        V2S.media.setSettings(next);
        logEvent('settings_media', next);
        await api.reopenMedia();
        await render();
      })])
    ]);
  }

  function aboutPage() {
    const state = api.state();
    return fragment([
      group([value(t.version, cfg.APP_VERSION), value(t.session, V2S.util.getSessionId())]),
      group([action(t.downloadLog, async () => {
        const events = await V2S.storage.getAllEvents();
        downloadBlob(new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), participantId: state.participantId, events }, null, 2)], { type: 'application/json' }), `v2s-events-${V2S.util.timestamp()}.json`);
      })])
    ]);
  }

  return { init, open, close, isOpen, canOpen, show };
})();
