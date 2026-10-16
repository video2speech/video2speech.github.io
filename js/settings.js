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

  // The one action the research team looks for first (New participant): with its symbol.
  const PERSON_PLUS = '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.6"/><path d="M2.5 19.5c.7-3.5 3.3-5.4 6.5-5.4s5.8 1.9 6.5 5.4"/><path d="M19 7.5v6M16 10.5h6"/></svg>';
  function strongAction(label, onClick, icon, id) {
    const symbol = node('span', { className: 'row-icon', 'aria-hidden': 'true' });
    symbol.innerHTML = icon;
    return node('button', { type: 'button', className: 'row row-action row-strong', ...(id ? { id } : {}), on: { click: onClick } }, [
      symbol,
      node('span', { className: 'row-label', text: label })
    ]);
  }

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
  // The first page, in order of what matters (owner, 2026-10-15: "put what is important
  // where it is plain to see"): who is recording and changing that; whether every
  // recording is saved, and saving them; this participant's own settings; where they are
  // in the sentences; this device; then About and Sign out.
  async function mainPage() {
    const state = api.state();
    const unsaved = await api.pendingCount().catch(() => 0);
    const media = V2S.media.getSettings();
    const id = state.participantId;
    const folderMode = V2S.exporter.getSaveMode() === 'folder';
    return fragment([
      group([
        value(t.participantId, id),
        id ? strongAction(t.newParticipant, newParticipant, PERSON_PLUS, 'newParticipant') : null,
        id ? action(t.switchParticipant, switchParticipant) : null
      ], { foot: id ? t.participantNote : null, id: 'settingsParticipant' }),
      group([
        statusRow(unsaved ? t.notSavedLong(unsaved) : t.allSavedLong, null, unsaved ? 'warn' : 'ok'),
        unsaved ? strongAction(t.saveNow, () => saveAll(unsaved, 'main'), SAVE_ICON, 'mainSaveNow') : null,
        nav(t.savingOptions, folderMode ? t.modeFolder(V2S.exporter.folderName() || '?') : t.modeZip, 'settingsSaving')
      ], { title: t.saving, id: 'settingsSavingSummary' }),
      group([themeRow(), holdRow(), silentRow()], id ? { title: t.forParticipant(id), foot: t.forParticipantNote, id: 'settingsOwn' } : { id: 'settingsOwn' }),
      group([nav(t.participant, describePosition(state), 'settingsProgress')]),
      group([
        nav(t.devices, '', 'settingsDevices'),
        nav(t.quality, `${media.resolution || ''}`, 'settingsQuality')
      ], { title: t.device }),
      group([nav(t.about, '', 'settingsAbout')]),
      group([action(t.signOut, async () => {
        if (!(await V2S.ui.confirm({ title: t.signOut, body: t.signOutConfirm, yes: t.signOutYes, caution: true }))) return;
        await api.signOut();
      }, true)])
    ]);
  }

  // Allow recordings without voice (laryngectomy): this participant's own, off by default.
  function silentRow() {
    const box = node('input', { type: 'checkbox', id: 'setSilent', checked: V2S.qc.allowsSilent() });
    box.addEventListener('change', async () => {
      V2S.qc.setAllowSilent(box.checked);
      await V2S.storage.setSetting('allowSilent', box.checked);
      await api.saveParticipantPrefs();
      logEvent('settings_allow_silent', { allowSilent: box.checked });
    });
    return control(t.allowSilent, box);
  }

  // How long a press may be held before it counts as holding: this participant's own.
  function holdRow() {
    const hold = select('setHold', [['1000', t.hold1], ['2000', t.hold2], ['3000', t.hold3]], String(V2S.input.getHoldMs()));
    hold.addEventListener('change', async () => {
      V2S.input.setHoldMs(Number(hold.value));
      await V2S.storage.setSetting('holdMs', Number(hold.value));
      await api.saveParticipantPrefs();
      logEvent('settings_hold', { holdMs: Number(hold.value) });
    });
    return control(t.holdLabel, hold);
  }

  // What is the case, at a glance (a problem in amber): not a button.
  const CHECK_ICON = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5"/><path d="m7.8 12.3 2.9 2.9 5.5-6"/></svg>';
  const WARN_ICON = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5"/><path d="M12 7.5v5.5M12 16.4v.4"/></svg>';
  const SAVE_ICON = '<svg viewBox="0 0 24 24"><path d="M12 4.5v10M7.5 10 12 14.5l4.5-4.5M5.5 19h13"/></svg>';
  function statusRow(text, detail, tone) {
    const symbol = node('span', { className: 'row-icon', 'aria-hidden': 'true' });
    symbol.innerHTML = tone === 'warn' ? WARN_ICON : CHECK_ICON;
    return node('div', { className: `row row-status${tone === 'warn' ? ' is-warn' : ''}`, role: 'status' }, [
      symbol,
      node('span', { className: 'row-label', text }),
      detail ? node('span', { className: 'row-value', text: detail }) : null
    ]);
  }

  // Save all recordings now: a folder writes them here; ZIP files close Settings for the
  // save and its question, then come back to `returnPage`.
  async function saveAll(unsavedCount, returnPage) {
    if (V2S.exporter.getSaveMode() === 'folder') {
      if (!V2S.exporter.isFolderActive() && (await V2S.exporter.requestFolderPermission()) !== 'granted') {
        await V2S.ui.alert(t.saving, t.folderNotAllowed);
        return render();
      }
      const result = await V2S.exporter.flushPendingToFolder();
      await V2S.ui.alert(t.saving, result.written || result.failed ? t.written(result.written, result.failed) : t.nothingToSave);
      return render();
    }
    if (!unsavedCount) return V2S.ui.alert(t.saving, t.nothingToSave);
    close();
    await api.runZipSave('manual');
    await open(returnPage);
  }

  // Settings → New participant…: asks first, saying what happens to the recordings; then
  // every recording is saved (main.js) and Set up starts again.
  async function newParticipant() {
    const state = api.state();
    const unsaved = await api.pendingCount().catch(() => 0);
    const go = await V2S.ui.confirm({
      title: t.newParticipantTitle,
      body: t.newParticipantBody(state.participantId, unsaved),
      yes: unsaved ? t.newParticipantSave : t.newParticipantGo
    });
    if (!go) return;
    logEvent('settings_new_participant', { from: state.participantId, unsaved });
    close();
    await api.newParticipant();
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
    const saveNow = action(t.saveNow, () => saveAll(unsaved.length, 'settingsSaving'));
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

  // What is being recorded: the sentence set, or the Rainbow Passage while it is under way.
  function activeList(state) {
    return state.recordingRainbow && state.rainbow
      ? { material: state.rainbow.material, progress: state.rainbow.progress, passage: true }
      : { material: state.material, progress: state.progress, passage: false };
  }

  // Short: "Part 2 · 14 of 50" (the main list); long adds the sentence number in the set.
  function describePosition(state, long = false) {
    const { material, progress, passage } = activeList(state);
    if (!material || !progress) return '—';
    const index = progress.currentIndex;
    const { warmupCount, formalCount } = material;
    if (passage) return copy.record.rainbowOf(index + 1, material.all.length);
    if (progress.completed) {
      // With the Rainbow Passage still ahead (not answered, or not started): not "all done".
      const ahead = Boolean(cfg.SETS[state.setKey]) && !['declined', 'done'].includes(progress.rainbow);
      return ahead ? copy.welcome.allParts(Math.ceil(formalCount / cfg.BLOCK_SIZE)) : copy.done.allTitle;
    }
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
    // Moving around acts on what is being recorded (with the passage under way, its sentences).
    const list = activeList(state);
    if (state.participantId && list.progress && list.material) {
      const total = list.material.formalCount;
      const warmup = list.material.warmupCount;
      const index = list.progress.currentIndex;
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
      parts.push(
        group([
          action(t.previous, () => go(Math.max(0, index - 1), {}, 'settings_previous')),
          action(t.next, async () => {
            // A mis-tap must not leave a sentence unrecorded without anyone noticing.
            if (!(await V2S.ui.confirm({ title: t.next, body: t.skipConfirm }))) return;
            await go(Math.min(list.material.all.length - 1, index + 1), {}, 'settings_next');
          }),
          jumpRow
        ], { title: t.moveTitle }),
        // Practice belongs to the sentence set, not to the passage.
        list.passage ? null : group([
          index < warmup
            // During "Practise again", skipping goes back to where they were.
            ? action(t.skipPractice, () => go(Number.isInteger(state.progress.resumeIndex) ? state.progress.resumeIndex : warmup, { coachDone: true, howtoSeen: true, resumeIndex: null }, 'settings_skip_practice'))
            : action(t.practiceAgain, async () => {
              if (!(await V2S.ui.confirm({ title: t.practiceAgain, body: t.practiceConfirm }))) return;
              // After the last sentence there is nothing to come back to: practice leads
              // into the next round from its first sentence.
              await go(0, state.progress.completed ? { coachDone: false } : { coachDone: false, resumeIndex: index }, 'settings_practice_again');
            })
        ], { title: t.practiceTitle })
      );
    }
    // The Rainbow Passage question answered (No, or Yes and not finished): the research
    // team can have it asked again, for a wrong answer.
    const answer = Boolean(cfg.SETS[state.setKey]) && state.progress && state.progress.completed ? state.progress.rainbow : null;
    if (false && ['declined', 'reading'].includes(answer)) {   // (no question any more: owner, 2026-10-15)
      parts.push(group([
        action(t.rainbowAgain, async () => {
          if (!(await V2S.ui.confirm({ title: t.rainbowAgain.replace('…', ''), body: t.rainbowConfirm, yes: t.confirm }))) return;
          logEvent('settings_rainbow_again', { answer });
          close();
          await api.askRainbowAgain();
        })
      ], { title: t.rainbowTitle, foot: `${t.rainbowAnswer(answer)} ${t.rainbowNote}`, id: 'settingsRainbow' }));
    }
    // Starting this participant over (Switch participant and New participant are on the
    // first page, with the participant).
    parts.push(group([
      state.progress ? action(t.reset, async () => {
        const index = state.progress.currentIndex;
        const body = state.progress.completed ? t.resetConfirmNewRound(round + 1) : t.resetConfirm;
        if (!(await V2S.ui.confirm({ title: t.reset.replace('…', ''), body, caution: true }))) return;
        logEvent('settings_clear_progress', { from: index });
        close();
        await api.clearProgress();
      }, true) : null
    ], { foot: state.progress ? t.roundNote(round) : null }));
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
