// Settings: the gear button in the top bar (always there, except while recording).
// Research-team sections (sentences and progress, saving, recording quality) carry the
// earlier page's names; camera, microphone and light/dark are for everyone. Anything
// destructive asks first, in plain words.
window.V2S = window.V2S || {};

V2S.settings = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const t = copy.settings;
  const { el, logEvent, formatBytes, downloadBlob } = V2S.util;
  let api = null;

  function init(appApi) {
    api = appApi;
    el('settingsButton').addEventListener('click', () => open());
    el('settingsClose').addEventListener('click', close);
    el('settingsPanel').addEventListener('click', event => { if (event.target === el('settingsPanel')) close(); });
    el('settingsClose').setAttribute('aria-label', copy.help.close);
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !el('settingsPanel').hidden && !V2S.ui.isDialogOpen()) close();
    });
  }

  function canOpen() {
    return !['starting', 'recording', 'finishing', 'checking'].includes(V2S.session.getState()) && !V2S.ui.isDialogOpen();
  }

  async function open(sectionId) {
    if (!canOpen()) return;
    V2S.input.setEnabled(false);
    await render();
    el('settingsPanel').hidden = false;
    const target = sectionId && el(sectionId);
    if (target) target.scrollIntoView({ block: 'start' });
    el('settingsClose').focus({ preventScroll: true });
    logEvent('settings_open', { section: sectionId || null });
  }

  function close() {
    if (el('settingsPanel').hidden) return;
    el('settingsPanel').hidden = true;
    if (api) api.onSettingsClosed();
  }

  const isOpen = () => !el('settingsPanel').hidden;

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

  function section(id, title, children, research = false) {
    const heading = node('h3', { text: title }, [research ? node('span', { className: 'set-tag', text: t.research }) : null]);
    return node('section', { className: 'set-section', id }, [heading, ...children]);
  }

  const button = (label, onClick, variant = 'ghost') => node('button', { type: 'button', className: `btn btn-${variant}`, text: label, on: { click: onClick } });
  const buttons = list => node('div', { className: 'set-buttons' }, list);
  const note = text => node('p', { className: 'set-note', text });
  const warn = text => node('p', { className: 'set-warn', text });
  const row = (label, control) => node('div', { className: 'set-row' }, [node('label', { htmlFor: control.id, text: label }), control]);

  function kv(pairs) {
    const list = node('dl', { className: 'set-kv' });
    pairs.forEach(([key, value]) => list.append(node('dt', { text: key }), node('dd', { text: value == null || value === '' ? '—' : String(value) })));
    return list;
  }

  function select(id, options, value) {
    const element = node('select', { id });
    options.forEach(([optionValue, label]) => element.append(node('option', { value: optionValue, text: label })));
    element.value = String(value);
    return element;
  }

  // ---- panel ----
  async function render() {
    const body = el('settingsBody');
    el('settingsTitle').textContent = t.title;
    body.replaceChildren();
    body.append(progressSection(), await savingSection(), await devicesSection(), qualitySection(), displaySection(), accountSection(), aboutSection());
  }

  async function devicesSection() {
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
    return section('settingsDevices', t.devices, [
      row(t.camera, camera),
      row(t.microphone, microphone),
      now.bluetooth ? warn(copy.check.bluetooth) : null,
      kv([[t.actual, [
        video.width ? `${video.width}×${video.height}${Number(video.frameRate) > 0 ? ` · ${Math.round(Number(video.frameRate))} fps` : ''}` : null,
        audio.sampleRate ? `${(audio.sampleRate / 1000).toFixed(audio.sampleRate % 1000 ? 1 : 0)} kHz · ${audio.channelCount || 1} ch · ${audioMode}` : null
      ].filter(Boolean).join(' / ')]]),
      note(t.devicesNote),
      buttons([button(t.testAgain, () => { close(); api.showCheck(); }, 'go')])
    ]);
  }

  function displaySection() {
    const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const group = node('div', { className: 'segmented', role: 'group', 'aria-label': t.theme });
    [['light', t.light], ['dark', t.dark]].forEach(([value, label]) => {
      group.append(node('button', {
        type: 'button',
        text: label,
        'aria-pressed': String(value === current),
        on: { click: async () => { await api.setTheme(value); await render(); } }
      }));
    });
    return section('settingsDisplay', t.display, [node('div', { className: 'set-row' }, [node('label', { text: t.theme }), group])]);
  }

  async function savingSection() {
    // Counts only: reading the recordings themselves would load every video.
    const [allIds, backupIds] = await Promise.all([V2S.storage.takeIds(), V2S.storage.exportedIds()]);
    const backupSet = new Set(backupIds);
    const backups = allIds.filter(id => backupSet.has(id));
    const unsaved = allIds.filter(id => !backupSet.has(id));
    const estimate = await V2S.storage.storageEstimate();
    const folderMode = V2S.exporter.getSaveMode() === 'folder';
    const folderSupported = V2S.exporter.folderSupported();
    const status = V2S.exporter.status();
    const actions = [
      button(t.saveNow, async () => {
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
      }, 'go')
    ];
    if (backups.length) {
      actions.push(button(t.saveBackups, async () => {
        close();
        await api.runZipSave('backup', null, { backups: true });
        await open('settingsSaving');
      }));
    }
    if (folderSupported) {
      actions.push(button(t.chooseFolder, async () => {
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
      }));
      if (folderMode) {
        actions.push(button(t.useZip, async () => {
          await V2S.exporter.setSaveMode('zip');
          await render();
        }));
      }
    }
    if (backups.length) {
      actions.push(button(t.deleteBackups, async () => {
        const ok = await V2S.ui.confirm({ title: t.deleteBackups.replace('…', ''), body: t.deleteBackupsConfirm(backups.length), yes: t.confirm, caution: true });
        if (!ok) return;
        await V2S.storage.deleteTakes(backups);
        logEvent('settings_delete_backups', { count: backups.length });
        await render();
      }, 'caution'));
    }
    actions.push(button(t.deleteCached, async () => {
      if (!allIds.length) return V2S.ui.alert(t.deleteCached.replace('…', ''), t.nothingStored);
      const ok = await V2S.ui.confirm({ title: t.deleteCached.replace('…', ''), body: t.deleteConfirm(allIds.length, unsaved.length), yes: t.confirm, caution: true });
      if (!ok) return;
      await V2S.storage.deleteTakes(allIds);
      logEvent('settings_delete_cached', { count: allIds.length, unsaved: unsaved.length });
      await render();
    }, 'caution'));
    return section('settingsSaving', t.saving, [
      kv([
        [t.mode, folderMode ? t.modeFolder(V2S.exporter.folderName() || '?') : t.modeZip],
        folderMode ? [t.folderAccess, status.permission] : null,
        [t.cached, t.cachedValue(unsaved.length)],
        backups.length ? [t.backups, t.backupsValue(backups.length)] : null,
        [t.storage, estimate ? `${(estimate.ratio * 100).toFixed(1)}% of ${formatBytes(estimate.quota)}` : '—']
      ].filter(Boolean)),
      folderSupported ? null : note(t.noFolderSupport),
      folderMode ? null : note(t.backupNote),
      buttons(actions)
    ]);
  }

  function describePosition(state) {
    if (!state.material || !state.progress) return '—';
    const index = state.progress.currentIndex;
    const { warmupCount, formalCount } = state.material;
    if (state.progress.completed) return copy.done.allTitle;
    if (index < warmupCount) return copy.record.practiceOf(index + 1, warmupCount);
    const formal = index - warmupCount;
    const block = Math.floor(formal / cfg.BLOCK_SIZE) + 1;
    const blocks = Math.ceil(formalCount / cfg.BLOCK_SIZE);
    return `${copy.record.partOf(block, blocks)} · ${copy.record.sentenceOf(formal % cfg.BLOCK_SIZE + 1, Math.min(cfg.BLOCK_SIZE, formalCount - (block - 1) * cfg.BLOCK_SIZE))} (${formal + 1}/${formalCount})`;
  }

  // Everything the earlier page offered for moving around the sentences, under its old
  // names: sentence set, Previous / Next / Skip, go to a sentence, practice (warm-up) on or
  // skipped, Clear progress, plus switching participant and the held-press limit.
  function progressSection() {
    const state = api.state();
    const setSelect = select('setSentenceSet', Object.entries(cfg.SETS).map(([key, set]) => [key, set.label]), state.setKey);
    const setAbout = note(Object.values(cfg.SETS).map(set => `${set.label}: ${set.about}.`).join(' '));
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
    const children = [
      kv([[t.participantId, state.participantId], [t.position, describePosition(state)]]),
      state.progress ? note(t.roundNote(round)) : null,
      row(t.set, setSelect),
      setAbout
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
      const hold = select('setHold', [['1000', t.hold1], ['2000', t.hold2], ['3000', t.hold3]], String(V2S.input.getHoldMs()));
      hold.addEventListener('change', async () => {
        V2S.input.setHoldMs(Number(hold.value));
        await V2S.storage.setSetting('holdMs', Number(hold.value));
        logEvent('settings_hold', { holdMs: Number(hold.value) });
      });
      children.push(
        buttons([
          button(t.previous, () => go(Math.max(0, index - 1), {}, 'settings_previous')),
          button(t.next, async () => {
            // A mis-tap must not leave a sentence unrecorded without anyone noticing.
            if (!(await V2S.ui.confirm({ title: t.next, body: t.skipConfirm }))) return;
            await go(Math.min(state.material.all.length - 1, index + 1), {}, 'settings_next');
          })
        ]),
        node('div', { className: 'set-row' }, [node('label', { htmlFor: 'setJump', text: t.jumpLabel(total) }), node('div', { className: 'set-buttons' }, [jump, button(t.jump, async () => {
          const n = Number(jump.value);
          if (!Number.isInteger(n) || n < 1 || n > total) return V2S.ui.alert(t.jump, t.jumpInvalid(total));
          await go(warmup + n - 1);
        })])]),
        buttons([
          index < warmup
            // During "Practise again", skipping goes back to where they were.
            ? button(t.skipPractice, () => go(Number.isInteger(state.progress.resumeIndex) ? state.progress.resumeIndex : warmup, { coachDone: true, howtoSeen: true, resumeIndex: null }, 'settings_skip_practice'))
            : button(t.practiceAgain, async () => {
              if (!(await V2S.ui.confirm({ title: t.practiceAgain, body: t.practiceConfirm }))) return;
              // After the last sentence there is nothing to come back to: practice leads
              // into the next round from its first sentence.
              await go(0, state.progress.completed ? { coachDone: false } : { coachDone: false, resumeIndex: index }, 'settings_practice_again');
            }),
          button(t.reset, async () => {
            const body = state.progress.completed ? t.resetConfirmNewRound(round + 1) : t.resetConfirm;
            if (!(await V2S.ui.confirm({ title: t.reset.replace('…', ''), body, caution: true }))) return;
            logEvent('settings_clear_progress', { from: index });
            close();
            await api.clearProgress();
          }, 'caution')
        ]),
        row(t.holdLabel, hold),
        note(t.holdNote)
      );
    }
    children.push(buttons([button(t.switchParticipant, switchParticipant)]));
    return section('settingsProgress', t.participant, children, true);
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

  function qualitySection() {
    const media = V2S.media.getSettings();
    const resolution = select('setResolution', cfg.QUALITY_LABELS.resolution, media.resolution);
    const bitrate = select('setBitrate', cfg.QUALITY_LABELS.bitrate, media.bitrate);
    const fps = select('setFps', cfg.QUALITY_LABELS.fps, media.fps);
    const audioMode = select('setAudio', cfg.QUALITY_LABELS.audio, media.audioMode);
    const mirror = node('input', { type: 'checkbox', id: 'setMirror', checked: Boolean(media.mirror) });
    return section('settingsQuality', t.quality, [
      note(t.qualityNote),
      row(t.resolution, resolution),
      row(t.bitrate, bitrate),
      row(t.fps, fps),
      row(t.audio, audioMode),
      row(t.mirror, mirror),
      buttons([button(t.applyQuality, async () => {
        const next = { ...V2S.media.getSettings(), resolution: resolution.value, bitrate: Number(bitrate.value), fps: Number(fps.value), audioMode: audioMode.value, mirror: mirror.checked };
        await V2S.storage.setSetting('mediaSettings', next);
        V2S.media.setSettings(next);
        logEvent('settings_media', next);
        await api.reopenMedia();
        await render();
      })])
    ], true);
  }

  function accountSection() {
    return section('settingsAccount', t.account, [
      buttons([button(t.signOut, async () => {
        if (!(await V2S.ui.confirm({ title: t.signOut, body: t.signOutConfirm }))) return;
        await api.signOut();
      })])
    ]);
  }

  function aboutSection() {
    const state = api.state();
    return section('settingsAbout', t.about, [
      kv([[t.version, cfg.APP_VERSION], [t.session, V2S.util.getSessionId()]]),
      buttons([button(t.downloadLog, async () => {
        const events = await V2S.storage.getAllEvents();
        downloadBlob(new Blob([JSON.stringify({ exportedAt: new Date().toISOString(), participantId: state.participantId, events }, null, 2)], { type: 'application/json' }), `v2s-events-${V2S.util.timestamp()}.json`);
      })])
    ]);
  }

  return { init, open, close, isOpen, canOpen };
})();
