// Start-up and screen flow:
//   setup (first time on a device) → welcome → [folder permission] → camera & microphone
//   check (test recording + playback) → [How to record, first time] → recording
//   (practice with coaching the first time) ⇄ breaks → done.
// Rule for every click that needs the browser's permission or file dialogs: call the
// browser API FIRST in the click handler, before any other waiting, or the browser
// refuses (and a silent fallback would put recordings somewhere else).
window.V2S = window.V2S || {};

V2S.app = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const ui = V2S.ui;
  const exporter = V2S.exporter;
  const { el, logEvent, platform, sleep } = V2S.util;

  const app = {
    participantId: null,
    setKey: cfg.DEFAULT_SET,
    material: null,
    progress: null,
    sessionStarted: false,
    wakeLock: null,
    checkReturn: null,     // 'record' when the check was opened from Settings mid-session
    howtoReturn: null,     // screen to go back to from How to record (the ? button)
    test: { running: false, url: null },
    flushEvents: () => Promise.resolve()
  };

  // ---------- static text ----------
  function fillStaticCopy() {
    const text = {
      loadingText: copy.loading,
      finishLong: copy.top.finish,
      finishShort: copy.top.finishShort,
      setupEyebrow: copy.setup.eyebrow,
      setupTitle: copy.setup.title,
      setupLead: copy.setup.lead,
      setupIdLabel: copy.setup.idLabel,
      setupHint: copy.setup.idHint,
      setupNext: copy.setup.next,
      setupConfirmTitle: copy.setup.confirmTitle,
      setupConfirmYes: copy.setup.confirmYes,
      setupConfirmChange: copy.setup.confirmChange,
      setupFolderTitle: copy.setup.folderTitle,
      setupFolderLead: copy.setup.folderLead,
      setupFolderChoose: copy.setup.folderChoose,
      setupFolderZip: copy.setup.folderZip,
      welcomeStage1: copy.welcome.stage1,
      welcomeStage2: copy.welcome.stage2,
      welcomeStage3: copy.welcome.stage3,
      folderTitle: copy.folder.title,
      folderAllow: copy.folder.allow,
      folderChoose: copy.folder.choose,
      folderZip: copy.folder.zip,
      checkTitle: copy.check.title,
      checkCameraTitle: copy.check.cameraTitle,
      checkCameraText: copy.check.cameraText,
      checkMicTitle: copy.check.micTitle,
      checkMicText: copy.check.micText,
      changeCamera: copy.check.change,
      changeMic: copy.check.change,
      testRecordLabel: copy.check.testRecord,
      testSay: copy.check.testSay,
      testQuestion: copy.check.testQuestion,
      testYes: copy.check.testYes,
      testAgain: copy.check.testAgain,
      checkHelp: copy.check.help,
      howtoTitle: copy.howto.title,
      howtoMockStart: copy.howto.mockStart,
      howtoMockStop: copy.howto.mockStop,
      howtoMockRedo: copy.howto.mockRedo,
      howtoMockSentence: copy.howto.mockSentence,
      howtoKeys: copy.howto.keys,
      redoSavedText: copy.record.saved
    };
    Object.entries(text).forEach(([id, value]) => ui.setText(id, value));
    el('setupId').placeholder = copy.setup.idPlaceholder;
  }

  // ---------- settings and theme ----------
  async function loadSettings() {
    const media = await V2S.storage.getSetting('mediaSettings', null);
    V2S.media.setSettings(media || cfg.MEDIA_DEFAULTS);
    const setKey = await V2S.storage.getSetting('setKey', cfg.DEFAULT_SET);
    app.setKey = cfg.SETS[setKey] ? setKey : cfg.DEFAULT_SET;
    applyTheme(await V2S.storage.getSetting('theme', document.documentElement.getAttribute('data-theme') || 'light'));
    V2S.input.setHoldMs(await V2S.storage.getSetting('holdMs', cfg.HOLD_MS));
  }

  function applyTheme(theme) {
    const value = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', value);
    try { localStorage.setItem('v2s_theme', value); } catch (error) { /* ignore */ }
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = value === 'dark' ? '#111316' : '#F2F1EC';
    V2S.meter.refreshColors();
    ui.labelTopbar(value);
  }

  async function setTheme(theme) {
    applyTheme(theme);
    await V2S.storage.setSetting('theme', theme === 'dark' ? 'dark' : 'light');
    logEvent('theme', { theme });
  }

  function toggleTheme() {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    setTheme(next);
  }

  // ---------- event log persistence ----------
  function persistEvents() {
    let queue = [];
    let timer = null;
    const flush = () => {
      clearTimeout(timer);
      timer = null;
      const batch = queue;
      queue = [];
      return V2S.storage.appendEvents(batch).catch(error => console.warn('Event log write failed', error));
    };
    app.flushEvents = flush;
    V2S.util.onEvent(entry => {
      queue.push(entry);
      if (queue.length >= 25) flush();
      else if (!timer) timer = setTimeout(flush, 2000);
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) flush(); });
    window.addEventListener('pagehide', flush);
  }

  // ---------- wake lock ----------
  async function requestWakeLock() {
    try {
      if ('wakeLock' in navigator && !app.wakeLock) {
        app.wakeLock = await navigator.wakeLock.request('screen');
        app.wakeLock.addEventListener('release', () => { app.wakeLock = null; });
      }
    } catch (error) {
      logEvent('wake_lock_failed', { error: String(error && error.name || error) });
    }
  }

  function releaseWakeLock() {
    if (app.wakeLock) app.wakeLock.release().catch(() => {});
    app.wakeLock = null;
  }

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && ['record', 'check'].includes(ui.screen())) requestWakeLock();
  });

  // ---------- participant and material ----------
  async function loadMaterial() {
    app.material = await V2S.sentences.load(app.setKey);
  }

  async function loadProgress() {
    const key = V2S.storage.progressKey(app.participantId, app.setKey);
    let record = await V2S.storage.getProgress(key);
    if (!record) record = await V2S.storage.createParticipantProgress(app.participantId, app.setKey, null);
    const last = app.material.all.length - 1;
    record.currentIndex = Math.min(Math.max(0, Number(record.currentIndex) || 0), last);
    app.progress = record;
    return record;
  }

  // Recordings not saved anywhere yet (ZIP backup copies do not count).
  const pendingCount = () => V2S.storage.countUnsaved();

  function positionFor(index) {
    const { warmupCount, formalCount } = app.material;
    if (index < warmupCount) return { warmup: true, pos: index + 1, total: warmupCount };
    const formal = index - warmupCount;
    const block = Math.floor(formal / cfg.BLOCK_SIZE);
    const blockStart = block * cfg.BLOCK_SIZE;
    return {
      warmup: false,
      block: block + 1,
      blocks: Math.ceil(formalCount / cfg.BLOCK_SIZE),
      inBlock: formal - blockStart + 1,
      blockSize: Math.min(cfg.BLOCK_SIZE, formalCount - blockStart)
    };
  }

  const partCount = () => Math.ceil(app.material.formalCount / cfg.BLOCK_SIZE);
  const needsPractice = () => !app.progress.coachDone && app.progress.currentIndex < app.material.warmupCount;

  function folderLabel() {
    const name = exporter.folderName() || '';
    return app.participantId ? `${name}/${app.participantId}` : name;
  }

  // ---------- setup ----------
  function showSetupStep(step) {
    el('setupStepId').hidden = step !== 'id';
    el('setupStepConfirm').hidden = step !== 'confirm';
    el('setupStepFolder').hidden = step !== 'folder';
  }

  function showSetup(prefill = '') {
    ui.show('setup');
    showSetupStep('id');
    el('setupId').value = prefill;
    el('setupError').hidden = true;
    setTimeout(() => el('setupId').focus(), 50);
  }

  let pendingSetup = null;

  async function onSetupSubmit(event) {
    event.preventDefault();
    const value = el('setupId').value.trim().toUpperCase();
    if (!/^[A-Z0-9][A-Z0-9_-]{0,23}$/.test(value)) {
      ui.setText('setupError', copy.setup.idInvalid);
      el('setupError').hidden = false;
      return;
    }
    el('setupError').hidden = true;
    const existing = await V2S.storage.getProgress(V2S.storage.progressKey(value, app.setKey));
    const legacy = existing ? null : await V2S.storage.findUnclaimedLegacyProgress(app.setKey);
    pendingSetup = { participantId: value, legacy };
    ui.setText('setupConfirmId', value);
    const options = el('setupLegacy');
    options.replaceChildren();
    options.hidden = !legacy;
    if (legacy) {
      await loadMaterial();
      const index = Math.min(Number(legacy.currentIndex) || 0, app.material.all.length - 1);
      const place = index < app.material.warmupCount
        ? `practice sentence ${index + 1}`
        : `sentence ${index - app.material.warmupCount + 1} of ${app.material.formalCount}`;
      options.append(
        optionRow('legacyChoice', 'continue', true, copy.setup.legacyContinue(place), copy.setup.legacyContinueDetail),
        optionRow('legacyChoice', 'fresh', false, copy.setup.legacyFresh, copy.setup.legacyFreshDetail)
      );
    }
    showSetupStep('confirm');
    el('setupConfirmYes').focus();
  }

  function optionRow(name, value, checked, title, detail) {
    const label = document.createElement('label');
    label.className = 'option';
    const input = document.createElement('input');
    input.type = 'radio';
    input.name = name;
    input.value = value;
    input.checked = checked;
    const text = document.createElement('div');
    const strong = document.createElement('strong');
    strong.textContent = title;
    const span = document.createElement('span');
    span.textContent = detail;
    text.append(strong, span);
    label.append(input, text);
    return label;
  }

  async function onSetupConfirm() {
    if (!pendingSetup) return;
    const choice = document.querySelector('input[name="legacyChoice"]:checked');
    const useLegacy = pendingSetup.legacy && (!choice || choice.value === 'continue');
    app.participantId = pendingSetup.participantId;
    const key = V2S.storage.progressKey(app.participantId, app.setKey);
    if (!(await V2S.storage.getProgress(key))) {
      await V2S.storage.createParticipantProgress(app.participantId, app.setKey, useLegacy ? pendingSetup.legacy : null);
    }
    await V2S.storage.setSetting('participantId', app.participantId);
    logEvent('participant_set', { participantId: app.participantId, adoptedLegacy: Boolean(useLegacy) });
    if (exporter.folderSupported()) {
      el('setupFolderError').hidden = true;
      showSetupStep('folder');
      el('setupFolderChoose').focus();
    } else {
      await exporter.setSaveMode('zip');
      await showWelcome();
    }
  }

  async function onSetupChooseFolder() {
    let name;
    try {
      name = await exporter.chooseFolder(); // first: the browser shows its folder picker
    } catch (error) {
      ui.setText('setupFolderError', copy.setup.folderFailed);
      el('setupFolderError').hidden = false;
      return;
    }
    if (!name) return; // cancelled: stay on this step
    flushPendingToFolder();
    await showWelcome();
  }

  // Anything still cached (including recordings the earlier page left unsaved) goes into
  // the folder as soon as the folder is usable.
  function flushPendingToFolder() {
    if (!exporter.isFolderActive()) return Promise.resolve({ written: 0, failed: 0 });
    return exporter.flushPendingToFolder();
  }

  // ---------- welcome ----------
  async function showWelcome() {
    V2S.input.setEnabled(false);
    ui.show('loading');
    try {
      await loadMaterial();
      await loadProgress();
    } catch (error) {
      return showLoadError(error);
    }
    const progress = app.progress;
    const firstVisit = !progress.howtoSeen && !progress.coachDone && progress.currentIndex === 0;
    ui.setText('welcomeId', copy.welcome.participant(app.participantId));
    ui.setText('welcomeTitle', firstVisit ? copy.welcome.titleFirst : copy.welcome.titleBack);
    ui.setText('welcomeLead', firstVisit ? copy.welcome.leadFirst : copy.welcome.leadBack);
    el('welcomeStages').hidden = !firstVisit;
    el('welcomeJourney').hidden = firstVisit;

    const p = positionFor(progress.currentIndex);
    if (progress.completed) {
      ui.setText('welcomePart', copy.welcome.allDone);
      ui.setText('welcomeCount', '');
      el('welcomeBar').style.transform = 'scaleX(1)';
    } else if (p.warmup) {
      ui.setText('welcomePart', copy.welcome.practice);
      ui.setText('welcomeCount', copy.welcome.practiceCount(p.pos - 1, p.total));
      el('welcomeBar').style.transform = `scaleX(${((p.pos - 1) / p.total).toFixed(3)})`;
    } else {
      ui.setText('welcomePart', copy.welcome.part(p.block, p.blocks));
      ui.setText('welcomeCount', copy.welcome.partCount(p.inBlock - 1, p.blockSize));
      el('welcomeBar').style.transform = `scaleX(${((p.inBlock - 1) / p.blockSize).toFixed(3)})`;
    }
    ui.setText('welcomeStart', firstVisit ? copy.welcome.begin : copy.welcome.continue);
    el('welcomeStart').hidden = Boolean(progress.completed);
    await refreshWelcomeNotice();
    ui.show('welcome');
    if (!el('welcomeStart').hidden) el('welcomeStart').focus({ preventScroll: true });
  }

  async function refreshWelcomeNotice() {
    const pending = await pendingCount();
    // In folder mode cached recordings are written automatically after Begin.
    const show = pending > 0 && exporter.getSaveMode() !== 'folder';
    el('welcomeNotice').hidden = !show;
    if (show) {
      ui.setText('welcomeNoticeText', copy.welcome.pending(pending));
      ui.setText('welcomeNoticeAction', copy.welcome.saveNow);
    }
  }

  async function onWelcomeSaveNow() {
    await runZipSave('saved');
    await refreshWelcomeNotice();
  }

  // Guards against double taps starting the camera twice.
  let starting = false;

  async function onWelcomeStart() {
    if (starting) return;
    starting = true;
    try {
      V2S.meter.resume(); // a user gesture: lets audio run on iOS
      if (exporter.getSaveMode() === 'folder') {
        let permission = await exporter.checkPermission();
        if (permission !== 'granted') permission = await exporter.requestFolderPermission();
        if (permission !== 'granted') await askForFolder();
        flushPendingToFolder();
      }
      V2S.storage.requestPersistence();
      await showCheck();
    } finally {
      starting = false;
    }
  }

  // ---------- folder permission screen ----------
  // Resolves 'granted' (same or new folder) or 'zip'. Where recordings go never changes
  // silently: the participant or helper decides here.
  function askForFolder() {
    return new Promise(resolve => {
      V2S.input.setEnabled(false);
      ui.setText('folderLead', copy.folder.lead(exporter.folderName() || ''));
      el('folderError').hidden = true;
      ui.show('folder');
      el('folderAllow').focus({ preventScroll: true });
      el('folderAllow').onclick = async () => {
        const permission = await exporter.requestFolderPermission(); // first: browser asks
        if (permission === 'granted') return resolve('granted');
        ui.setText('folderError', copy.folder.denied);
        el('folderError').hidden = false;
      };
      el('folderChoose').onclick = async () => {
        let name;
        try {
          name = await exporter.chooseFolder(); // first: browser shows its picker
        } catch (error) {
          ui.setText('folderError', copy.folder.failed);
          el('folderError').hidden = false;
          return;
        }
        if (name) resolve('granted');
      };
      el('folderZip').onclick = async () => {
        await exporter.setSaveMode('zip');
        resolve('zip');
      };
    });
  }

  // ---------- camera and microphone check ----------
  async function showCheck({ returnTo = null } = {}) {
    app.checkReturn = returnTo || (app.sessionStarted ? 'record' : null);
    if (['ready', 'partEnd'].includes(V2S.session.getState())) V2S.session.stop();
    V2S.input.setEnabled(false);
    ui.show('check');
    resetTest();
    ui.setText('checkBadge', copy.check.starting);
    if (!V2S.media.getStream()) {
      try {
        await openMedia();
      } catch (error) {
        return showMediaError(error);
      }
    }
    requestWakeLock();
    renderDevices();
    setBadge('live');
    el('testRecord').focus({ preventScroll: true });
  }

  async function openMedia() {
    const stream = await V2S.media.open();
    V2S.meter.attach(stream);
    V2S.media.startHealth();
    return stream;
  }

  // Settings changed the camera, microphone or quality: open the stream again.
  async function reopenMedia() {
    V2S.media.stopHealth();
    try {
      await openMedia();
    } catch (error) {
      return showMediaError(error);
    }
    if (ui.screen() === 'check') {
      renderDevices();
      resetTest();
      setBadge('live');
    }
    return true;
  }

  function setBadge(kind, extra) {
    const badge = el('checkBadge');
    badge.replaceChildren();
    if (!kind) return;
    if (kind === 'live' || kind === 'recording') {
      const dot = document.createElement('span');
      dot.className = 'rec-dot';
      badge.append(dot);
    }
    const label = { live: copy.check.live, recording: copy.check.testRecording(extra), playing: copy.check.testPlaying }[kind] || '';
    badge.append(document.createTextNode(label));
  }

  async function renderDevices() {
    const now = V2S.media.current();
    ui.setText('cameraName', now.camera || copy.check.defaultDevice);
    ui.setText('micName', now.microphone || copy.check.defaultDevice);
    el('micWarning').hidden = !now.bluetooth;
    el('micSwitch').hidden = true;
    if (!now.bluetooth) return;
    ui.setText('micWarningText', copy.check.bluetooth);
    // Offer the device's own microphone if there is one.
    const { microphones } = await V2S.media.listDevices().catch(() => ({ microphones: [] }));
    const builtIn = microphones.find(mic => !V2S.media.isBluetooth(mic.label));
    if (!builtIn) return;
    ui.setText('micSwitch', copy.check.useDevice(builtIn.label));
    el('micSwitch').hidden = false;
    el('micSwitch').onclick = async () => {
      const next = { ...V2S.media.getSettings(), audioDeviceId: builtIn.id };
      await V2S.storage.setSetting('mediaSettings', next);
      V2S.media.setSettings(next);
      logEvent('mic_switched', { to: builtIn.label });
      await reopenMedia();
    };
  }

  function resetTest() {
    const playback = el('checkPlayback');
    playback.pause();
    playback.hidden = true;
    playback.removeAttribute('src');
    playback.controls = false;
    playback.load();
    if (app.test.url) URL.revokeObjectURL(app.test.url);
    app.test.url = null;
    app.test.running = false;
    el('checkPreview').hidden = false;
    el('checkFrame').classList.remove('is-playing');
    el('testRecord').hidden = false;
    el('testRecord').setAttribute('aria-disabled', 'false');
    el('testLive').hidden = true;
    el('testStatus').hidden = true;
    el('testAsk').hidden = true;
    el('testError').hidden = true;
  }

  function showTestError(text) {
    resetTest();
    ui.setText('testError', text);
    el('testError').hidden = false;
    setBadge('live');
  }

  // Records TEST_RECORD_MS with the real recording settings, then plays it back.
  async function onTestRecord() {
    if (app.test.running || ui.screen() !== 'check') return;
    resetTest();
    app.test.running = true;
    V2S.meter.resume();
    el('testRecord').hidden = true;
    el('testLive').hidden = false;
    el('testBar').style.transition = 'none';
    el('testBar').style.transform = 'scaleX(0)';
    let handle = null;
    let ready = { ok: false };
    for (let attempt = 0; attempt < cfg.START_ATTEMPTS && !ready.ok; attempt++) {
      if (handle) await handle.stop().catch(() => {});
      V2S.meter.beginCollect();
      try {
        handle = V2S.media.startRecorder({ skip: attempt >= cfg.START_ATTEMPTS - 1 ? 1 : 0 });
      } catch (error) {
        V2S.meter.endCollect();
        return showTestError(copy.check.testFailed);
      }
      ready = await handle.ready;
      if (!ready.ok) V2S.meter.endCollect();
    }
    if (!ready.ok) {
      logEvent('mic_test_failed', { error: ready.error });
      return showTestError(copy.check.testFailed);
    }
    const startedAt = performance.now();
    requestAnimationFrame(() => {
      el('testBar').style.transition = `transform ${cfg.TEST_RECORD_MS}ms linear`;
      el('testBar').style.transform = 'scaleX(1)';
    });
    while (performance.now() - startedAt < cfg.TEST_RECORD_MS) {
      if (ui.screen() !== 'check') {
        await handle.stop().catch(() => {});
        V2S.meter.endCollect();
        app.test.running = false;
        return;
      }
      setBadge('recording', Math.max(1, Math.ceil((cfg.TEST_RECORD_MS - (performance.now() - startedAt)) / 1000)));
      await sleep(200);
    }
    const recording = await handle.stop();
    const frames = V2S.meter.endCollect();
    const qc = V2S.qc.evaluate(frames);
    const now = V2S.media.current();
    logEvent('mic_test', { pass: qc.pass, code: qc.code, speechMs: qc.metrics.speechMs, rms: qc.metrics.rms, microphone: now.microphone, sampleRate: now.sampleRate, size: recording.blob.size });
    if (!recording.blob.size) return showTestError(copy.check.testFailed);
    if (qc.code === 'no_speech' || qc.code === 'no_audio') return showTestError(copy.check.testSilent);
    await playTest(recording.blob);
  }

  async function playTest(blob) {
    const playback = el('checkPlayback');
    app.test.url = URL.createObjectURL(blob);
    playback.src = app.test.url;
    playback.muted = false;
    playback.classList.toggle('is-mirrored', Boolean(V2S.media.getSettings().mirror));
    el('checkPreview').hidden = true;
    playback.hidden = false;
    el('checkFrame').classList.add('is-playing');
    el('testLive').hidden = true;
    setBadge('playing');
    const ask = () => {
      app.test.running = false;
      el('testAsk').hidden = false;
      el('testBox').scrollIntoView({ block: 'nearest' });
      el('testYes').focus({ preventScroll: true });
    };
    playback.onended = () => {
      setBadge(null);
      ask();
    };
    try {
      await playback.play();
    } catch (error) {
      // Autoplay with sound was blocked: let the participant press play.
      playback.controls = true;
      setBadge(null);
      ask();
    }
  }

  async function onTestYes() {
    if (ui.screen() !== 'check') return;
    resetTest();
    logEvent('mic_test_ok', V2S.media.current());
    if (app.checkReturn === 'record' && app.sessionStarted) return showRecord();
    if (!app.progress.howtoSeen || needsPractice()) return showHowto({ next: 'record' });
    return showRecord();
  }

  // ---------- how to record ----------
  function showHowto({ next }) {
    app.howtoReturn = next;
    V2S.input.setEnabled(false);
    const backToSession = next === 'back-record' || next === 'back-check';
    ui.setText('howtoGo', backToSession ? copy.howto.back : (needsPractice() ? copy.howto.practice : copy.welcome.continue));
    // On a computer the keys are taught as the controls (Space, ←); on touch, the buttons.
    const keys = document.documentElement.classList.contains('has-keyboard');
    ui.setRich('howtoStep1', copy.howto.step1(keys));
    ui.setRich('howtoStep2', copy.howto.step2(keys));
    ui.setRich('howtoStep3', copy.howto.step3(keys));
    ui.setRich('howtoRedo', copy.howto.redo(keys));
    const green = el('howtoStep2').querySelector('b'); // "green" is shown in green
    if (green) green.className = 'go-word';
    ui.show('howto');
    el('howtoGo').focus({ preventScroll: true });
  }

  async function onHowtoGo() {
    const next = app.howtoReturn;
    app.howtoReturn = null;
    if (next === 'back-check') {
      ui.show('check');
      return;
    }
    if (!app.progress.howtoSeen) {
      app.progress.howtoSeen = true;
      await V2S.storage.saveParticipantProgress(app.progress);
    }
    await showRecord();
  }

  function onHelp() {
    if (ui.screen() === 'record' && ['ready', 'partEnd'].includes(V2S.session.getState())) {
      V2S.session.stop();
      showHowto({ next: 'back-record' });
    } else if (ui.screen() === 'check' && !app.test.running) {
      showHowto({ next: 'back-check' });
    }
  }

  // ---------- recording ----------
  async function showRecord() {
    ui.show('record');
    requestWakeLock();
    V2S.input.setEnabled(true);
    if (!app.sessionStarted) {
      app.sessionStarted = true;
      V2S.session.begin({ participantId: app.participantId, setKey: app.setKey, material: app.material, progress: app.progress });
    } else {
      ui.fitSentences(app.material.all);
      V2S.session.resume();
    }
  }

  // Ending asks first: a stray tap must not end the session.
  async function onFinishToday() {
    if (ui.screen() !== 'record' || !['ready', 'partEnd'].includes(V2S.session.getState())) return;
    const end = await ui.dialog({
      title: copy.endDialog.title,
      body: copy.endDialog.body,
      actions: [
        { label: copy.endDialog.keep, value: false, variant: 'go', default: true },
        { label: copy.endDialog.end, value: true, variant: 'ghost' }
      ],
      dismissValue: false
    });
    logEvent('end_for_today', { confirmed: end });
    if (!end) return;
    V2S.session.stop();
    await showDone({ allDone: false });
  }

  function onSettingsClosed() {
    if (ui.screen() === 'record') {
      V2S.input.setEnabled(true);
      if (['ready', 'partEnd'].includes(V2S.session.getState())) V2S.session.resume();
    }
  }

  // ---------- practice done, breaks and saving ----------
  const breakState = { mode: 'block', block: 0 };

  function setBreakButtons(primary, secondary, tertiary) {
    const set = (id, config) => {
      const button = el(id);
      button.hidden = !config;
      if (config) {
        button.textContent = config.label;
        button.onclick = config.action;
      }
    };
    set('breakPrimary', primary);
    set('breakSecondary', secondary);
    set('breakTertiary', tertiary);
  }

  function setSavePanel(panelId, textId, text, tone) {
    el(panelId).className = `save-panel${tone ? ` is-${tone}` : ''}`;
    ui.setText(textId, text);
  }

  // Practice done. Saving is learnt here by doing it once: in ZIP mode the practice
  // recordings are saved with the same steps as after every part; in folder mode the
  // screen says where every recording goes.
  async function onWarmupDone() {
    breakState.mode = 'practice';
    breakState.next = null;
    const p = positionFor(app.progress.currentIndex);
    const first = p.warmup || (p.block === 1 && p.inBlock === 1);
    breakState.continueLabel = first ? copy.practiceDone.next : copy.breakScreen.continueTo(p.block);
    await showBreak(copy.practiceDone.title, copy.practiceDone.body(partCount(), cfg.BLOCK_SIZE));
  }

  async function onBlockDone({ block, blocks }) {
    breakState.mode = 'block';
    breakState.block = block;
    breakState.next = block < blocks ? block + 1 : null;
    await showBreak(copy.breakScreen.title(block), copy.breakScreen.lead);
  }

  async function onStorageFull() {
    breakState.mode = 'storage';
    breakState.next = null;
    V2S.session.stop();
    await showBreak(copy.breakScreen.savePromptTitle, copy.feedback.storageFull);
  }

  async function showBreak(title, lead) {
    V2S.input.setEnabled(false);
    breakState.savedNow = 0;
    ui.setText('breakTitle', title);
    ui.setText('breakLead', lead);
    el('breakSave').hidden = false;
    el('breakSaveProgress').hidden = true;
    setSavePanel('breakSave', 'breakSaveText', exporter.getSaveMode() === 'folder' ? copy.breakScreen.savingFolder : copy.record.saving);
    setBreakButtons(null, null, null);
    ui.show('break');
    await settleWrites();
    await refreshBreakSave();
    el('breakPrimary').focus({ preventScroll: true });
  }

  // Waits for every take of the session to be stored, then (folder mode) writes anything
  // still cached into the folder. Gives up waiting after SETTLE_TIMEOUT_MS (a slow or
  // stuck folder): the writes go on in the background and the screen says so.
  async function settleWrites() {
    const settle = async () => {
      await V2S.session.flush();
      if (exporter.getSaveMode() === 'folder') {
        await exporter.flushFolderWrites();
        await flushPendingToFolder();
        await exporter.writeSessionLog(app.participantId, sessionSummary());
      }
    };
    const settled = settle().then(() => true, error => {
      logEvent('settle_failed', { error: String(error && error.message || error) });
      return true;
    });
    const done = await Promise.race([settled, sleep(cfg.SETTLE_TIMEOUT_MS).then(() => false)]);
    if (!done) logEvent('settle_timeout', {});
  }

  async function refreshBreakSave() {
    const pending = await pendingCount();
    const practice = breakState.mode === 'practice';
    const release = pending === 0 && V2S.session.needsRoom() ? await V2S.storage.latestBackup() : null;
    if (release && release.ids.length) {
      // The device is full and only the last saved ZIP's copies could make room: they
      // are removed only after the participant has checked that file is saved.
      setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.makeRoom(saveHint(release.fileName || '')), 'warn');
      setBreakButtons(
        { label: copy.breakScreen.makeRoomYes, action: makeRoom },
        null,
        { label: copy.breakScreen.saveAgain, action: async () => { await runZipSave('backup', null, { backups: true }); await refreshBreakSave(); } }
      );
      return;
    }
    const contLabel = practice ? breakState.continueLabel : (breakState.next ? copy.breakScreen.continueTo(breakState.next) : copy.breakScreen.continue);
    const cont = { label: contLabel, action: () => showRecord() };
    const finish = { label: copy.breakScreen.finish, action: () => showDone({ allDone: false }) };
    if (exporter.getSaveMode() === 'folder') {
      if (pending > 0 && exporter.status().saving) {
        // Still writing (a slow folder): carrying on is safe, the writes continue.
        setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.stillSaving(pending));
        setBreakButtons(cont, finish, null);
        setTimeout(() => { if (ui.screen() === 'break') refreshBreakSave(); }, 1500);
      } else if (pending === 0) {
        setSavePanel('breakSave', 'breakSaveText', practice ? copy.practiceDone.savedFolder(folderLabel()) : copy.done.savedFolder(folderLabel()), 'ok');
        setBreakButtons(cont, finish, null);
      } else {
        setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.folderProblem(pending), 'warn');
        setBreakButtons({ label: copy.breakScreen.allowFolder, action: fixFolderFromBreak }, cont, null);
      }
      return;
    }
    if (pending === 0) {
      setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.savedZip, 'ok');
      setBreakButtons(cont, finish, null);
    } else {
      const prompt = practice ? copy.practiceDone.zipPrompt : copy.breakScreen.zipPrompt;
      setSavePanel('breakSave', 'breakSaveText', breakState.savedNow ? copy.breakScreen.moreToSave(breakState.savedNow, pending) : prompt);
      setBreakButtons({ label: copy.breakScreen.saveButton, action: saveZipFromBreak }, null, { label: copy.breakScreen.later, action: () => showRecord() });
    }
  }

  async function makeRoom() {
    const removed = await V2S.storage.releaseLatestBackup();
    logEvent('backups_released', { count: removed });
    await V2S.session.refreshStorage().catch(() => {});
    await refreshBreakSave();
  }

  async function fixFolderFromBreak() {
    const permission = await exporter.requestFolderPermission(); // first: browser asks
    if (permission !== 'granted') {
      const result = await askForFolder();
      ui.show('break');
      if (result === 'zip') return refreshBreakSave();
    }
    await flushPendingToFolder();
    await refreshBreakSave();
  }

  async function saveZipFromBreak() {
    const label = breakState.mode === 'block' ? `block${String(breakState.block).padStart(2, '0')}` : breakState.mode === 'practice' ? 'practice' : 'saved';
    const result = await runZipSave(label, (done, total) => {
      el('breakSaveProgress').hidden = false;
      el('breakSaveBar').style.transform = `scaleX(${(done / total).toFixed(3)})`;
      ui.setText('breakSaveLabel', copy.breakScreen.saving(done, total));
    });
    el('breakSaveProgress').hidden = true;
    if (result === 'saved') breakState.savedNow = (breakState.savedNow || 0) + app.lastSavedCount;
    if (result === 'saved' || result === 'nothing') {
      await refreshBreakSave();
    } else if (result !== 'cancelled') {
      setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.notConfirmed, 'warn');
      setBreakButtons({ label: copy.breakScreen.saveButton, action: saveZipFromBreak }, null, { label: copy.breakScreen.later, action: () => showRecord() });
    }
  }

  function saveHint(fileName) {
    if (platform.ios) return copy.saveConfirm.ios(fileName);
    if (platform.android) return copy.saveConfirm.android(fileName);
    return copy.saveConfirm.desktop(fileName);
  }

  // ZIP save. The save dialog (Chrome/Edge) opens FIRST, while the click still counts;
  // a plain download is only cleared after the participant confirms the file exists.
  async function runZipSave(label, onProgress, { backups = false } = {}) {
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const suggested = `${app.participantId || 'recordings'}_video-recordings-${stamp}_${label}.zip`;
    const target = await exporter.pickZipTarget(suggested);
    if (target === undefined) return 'cancelled';
    let result;
    try {
      // Every take recorded so far is in storage before the ZIP is built.
      await V2S.session.flush();
      await app.flushEvents();
      result = await exporter.saveZip({ participantId: app.participantId, label, summary: sessionSummary(), target, onProgress, backups });
    } catch (error) {
      logEvent('zip_failed', { error: String(error && error.message || error) });
      await ui.alert(copy.error.loadTitle, String(error && error.message || error));
      return 'failed';
    }
    if (!result.count) return 'nothing';
    let confirmed = result.verified;
    if (!confirmed) {
      const answer = await ui.dialog({
        title: copy.saveConfirm.title,
        body: saveHint(result.fileName),
        actions: [
          { label: copy.saveConfirm.yes, value: 'yes', variant: 'plain' },
          { label: copy.saveConfirm.no, value: 'no', variant: 'plain' },
          { label: copy.saveConfirm.unsure, value: 'unsure', variant: 'plain', default: true }
        ],
        dismissValue: 'unsure'
      });
      logEvent('zip_confirm', { answer, fileName: result.fileName, count: result.count });
      if (answer === 'no') return runZipSave(label, onProgress, { backups });
      confirmed = answer === 'yes';
    }
    if (!confirmed) return 'unsure';
    app.lastSavedCount = result.count;
    if (!backups) {
      // Kept as backup copies (left out of later ZIPs) until space is needed.
      await V2S.storage.markExported(result.ids, result.fileName);
      const extra = (await V2S.storage.exportedIds()).length - cfg.BACKUP_MAX_TAKES;
      if (extra > 0) logEvent('backups_pruned', { count: await V2S.storage.pruneExported(extra, { keepLatest: true }), reason: 'limit' });
    }
    await V2S.session.refreshStorage().catch(() => {});
    return 'saved';
  }

  function sessionSummary() {
    return {
      participantId: app.participantId,
      sentenceSet: app.setKey,
      currentIndex: app.progress ? app.progress.currentIndex : null,
      completed: app.progress ? Boolean(app.progress.completed) : false,
      sessionId: V2S.util.getSessionId(),
      saveMode: exporter.getSaveMode(),
      folder: exporter.folderName(),
      media: V2S.media.snapshot(),
      settings: V2S.media.getSettings()
    };
  }

  // ---------- done ----------
  async function showDone({ allDone }) {
    V2S.input.setEnabled(false);
    V2S.session.stop();
    app.doneAll = Boolean(allDone);
    ui.setText('doneTitle', allDone ? copy.done.allTitle : copy.done.finishTitle);
    ui.setText('doneBody', '');
    setDoneBadge('wait');
    ui.setText('doneAgain', copy.done.again);
    el('doneAgain').hidden = Boolean(allDone);
    setSavePanel('doneSavePanel', 'doneSaveText', exporter.getSaveMode() === 'folder' ? copy.breakScreen.savingFolder : copy.record.saving);
    el('doneSavePanel').hidden = false;
    el('doneSave').hidden = true;
    ui.show('done');
    await settleWrites();
    await refreshDoneSave();
    releaseWakeLock();
    V2S.media.stopHealth();
    V2S.meter.detach();
    V2S.media.close();
    app.sessionStarted = false;
    logEvent('session_end', { allDone, index: app.progress && app.progress.currentIndex });
  }

  const BADGES = {
    ok: ['badge-go', '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>'],
    wait: ['badge-neutral', '<svg viewBox="0 0 24 24"><path d="M12 4v10M7.5 9.5 12 14l4.5-4.5M5 19h14"/></svg>']
  };

  function setDoneBadge(kind) {
    const [className, icon] = BADGES[kind];
    el('doneBadge').className = `badge ${className}`;
    el('doneBadge').innerHTML = icon;
  }

  async function refreshDoneSave() {
    const pending = await pendingCount();
    const folder = exporter.getSaveMode() === 'folder';
    if (pending === 0) {
      setDoneBadge('ok');
      ui.setText('doneBody', app.doneAll ? copy.done.allBody : copy.done.finishBody);
      setSavePanel('doneSavePanel', 'doneSaveText', folder ? copy.done.savedFolder(folderLabel()) : copy.done.savedZip, 'ok');
      el('doneSave').hidden = true;
      return;
    }
    // Recordings still only in the browser: the page must not say "you can close this page".
    setDoneBadge('wait');
    ui.setText('doneBody', copy.done.saveFirst);
    setSavePanel('doneSavePanel', 'doneSaveText', copy.done.pending(pending), 'warn');
    ui.setText('doneSave', folder ? copy.breakScreen.allowFolder : copy.done.save);
    el('doneSave').hidden = false;
    el('doneSave').focus({ preventScroll: true });
  }

  async function onDoneSave() {
    if (exporter.getSaveMode() === 'folder') {
      const permission = await exporter.requestFolderPermission(); // first: browser asks
      if (permission !== 'granted') {
        const result = await askForFolder();
        ui.show('done');
        if (result === 'zip') return refreshDoneSave();
      }
      await flushPendingToFolder();
    } else {
      await runZipSave('saved');
    }
    await refreshDoneSave();
  }

  // ---------- errors ----------
  function showError({ title, body, help, action, actionLabel, secondary }) {
    V2S.input.setEnabled(false);
    ui.setText('errorTitle', title);
    ui.setText('errorBody', body);
    el('errorHelp').hidden = !help;
    ui.setText('errorHelp', help || '');
    ui.setText('errorAction', actionLabel);
    el('errorAction').onclick = action;
    el('errorSecondary').hidden = !secondary;
    if (secondary) {
      ui.setText('errorSecondary', secondary.label);
      el('errorSecondary').onclick = secondary.action;
    }
    ui.show('error');
    el('errorAction').focus({ preventScroll: true });
  }

  function showMediaError(error) {
    logEvent('media_error', { code: error && error.code, error: String(error && (error.name || error.message) || error) });
    V2S.media.close();
    if (error && error.code === 'unsupported') {
      return showError({ title: copy.error.unsupportedTitle, body: copy.error.unsupportedBody, actionLabel: copy.error.reload, action: () => window.location.reload() });
    }
    if (error && error.code === 'permission') {
      return showError({ title: copy.error.permissionTitle, body: copy.error.permissionBody, help: ui.helpText(), actionLabel: copy.error.tryAgain, action: () => showCheck() });
    }
    return showError({ title: copy.error.deviceTitle, body: copy.error.deviceBody, help: ui.helpText(), actionLabel: copy.error.tryAgain, action: () => showCheck() });
  }

  async function reconnectAndResume() {
    V2S.meter.resume();
    el('errorAction').setAttribute('aria-disabled', 'true');
    try {
      await openMedia();
    } catch (error) {
      el('errorAction').setAttribute('aria-disabled', 'false');
      return showMediaError(error);
    }
    el('errorAction').setAttribute('aria-disabled', 'false');
    ui.show('record');
    V2S.input.setEnabled(true);
    V2S.session.resumeAfterReconnect();
  }

  function onDeviceError(code) {
    V2S.media.stopHealth();
    showError({ title: copy.error.deviceTitle, body: copy.error.deviceBody, actionLabel: copy.error.reconnect, action: reconnectAndResume });
    logEvent('device_error_screen', { code });
  }

  // Takes could not be stored twice in a row, and saving would not help.
  function onStoreFailure() {
    V2S.session.stop();
    showError({
      title: copy.error.storeTitle,
      body: copy.error.storeBody,
      actionLabel: copy.error.tryAgain,
      action: () => showRecord(),
      secondary: { label: copy.error.reload, action: () => window.location.reload() }
    });
    logEvent('store_failure_screen', {});
  }

  // The recorder failed to start twice in a row (after silent retries each time).
  function onStartFailure() {
    V2S.session.stop();
    showError({
      title: copy.error.startTitle,
      body: copy.error.startBody,
      actionLabel: copy.error.chooseMic,
      action: () => showCheck({ returnTo: 'record' }).then(() => V2S.settings.open('settingsDevices')),
      secondary: { label: copy.error.tryAgain, action: () => showRecord() }
    });
    logEvent('start_failure_screen', {});
  }

  function showLoadError(error) {
    console.error(error);
    logEvent('load_error', { error: String(error && error.message || error) });
    showError({
      title: copy.error.loadTitle,
      body: `${copy.error.loadBody} (${String(error && error.message || error)})`,
      actionLabel: copy.error.reload,
      action: () => window.location.reload()
    });
  }

  async function signOut() {
    logEvent('sign_out', {});
    V2S.session.stop();
    await V2S.session.flush();
    if (exporter.getSaveMode() === 'folder') await exporter.flushFolderWrites();
    try {
      sessionStorage.removeItem('v2s_auth_ok');
      sessionStorage.removeItem('v2s_auth_user');
    } catch (error) { /* ignore */ }
    // Back to this page after signing in again.
    window.location.replace('/index.html?next=' + encodeURIComponent(window.location.pathname));
  }

  // ---------- one tab at a time ----------
  // Two open copies would record into the same storage and progress. The page holds a
  // lock while open; a second copy asks first and can take over (the first one stops).
  function holdTabLock(steal = false) {
    if (!navigator.locks || typeof navigator.locks.request !== 'function') return Promise.resolve(true);
    return new Promise(resolve => {
      const options = steal ? { steal: true } : { ifAvailable: true };
      navigator.locks.request('v2s-recorder', options, lock => {
        if (!lock) {
          resolve(false);
          return null;
        }
        resolve(true);
        return new Promise(() => {}); // held until the page closes
      }).catch(error => {
        // Taken over by another tab.
        if (error && error.name === 'AbortError') onTabTakenOver();
      });
    });
  }

  function showOtherTab(title, body) {
    showError({
      title,
      body,
      actionLabel: copy.tab.useHere,
      action: async () => {
        logEvent('tab_take_over', {});
        await holdTabLock(true);
        window.location.reload();
      }
    });
  }

  async function onTabTakenOver() {
    logEvent('tab_taken_over', {});
    await V2S.session.abortCurrent('aborted_hidden');
    V2S.session.stop();
    V2S.input.setEnabled(false);
    V2S.media.stopHealth();
    V2S.meter.detach();
    V2S.media.close();
    app.sessionStarted = false;
    showOtherTab(copy.tab.movedTitle, copy.tab.movedBody);
  }

  // ---------- boot ----------
  function wire() {
    el('setupForm').addEventListener('submit', onSetupSubmit);
    el('setupConfirmYes').addEventListener('click', onSetupConfirm);
    el('setupConfirmChange').addEventListener('click', () => showSetup(pendingSetup ? pendingSetup.participantId : ''));
    el('setupFolderChoose').addEventListener('click', onSetupChooseFolder);
    el('setupFolderZip').addEventListener('click', async () => {
      await exporter.setSaveMode('zip');
      await showWelcome();
    });
    el('welcomeStart').addEventListener('click', onWelcomeStart);
    el('welcomeNoticeAction').addEventListener('click', onWelcomeSaveNow);
    el('testRecord').addEventListener('click', onTestRecord);
    el('testYes').addEventListener('click', onTestYes);
    el('testAgain').addEventListener('click', onTestRecord);
    el('changeCamera').addEventListener('click', () => V2S.settings.open('settingsDevices'));
    el('changeMic').addEventListener('click', () => V2S.settings.open('settingsDevices'));
    el('checkHelp').addEventListener('click', () => ui.showCameraHelp());
    el('howtoGo').addEventListener('click', onHowtoGo);
    el('finishButton').addEventListener('click', onFinishToday);
    el('helpButton').addEventListener('click', onHelp);
    el('themeButton').addEventListener('click', toggleTheme);
    el('doneSave').addEventListener('click', onDoneSave);
    el('doneAgain').addEventListener('click', () => showWelcome());

    V2S.input.configure({
      primary: press => V2S.session.onPrimary(press),
      secondary: press => V2S.session.onSecondary(press),
      hold: press => V2S.session.onHold(press)
    });
    V2S.input.bindButton(el('mainButton'), 'primary');
    V2S.input.bindButton(el('redoButton'), 'secondary');
    V2S.media.onFailure(code => {
      if (ui.screen() === 'record') V2S.session.onDeviceFailure(code);
      else if (ui.screen() === 'check') showMediaError(Object.assign(new Error(code), { code: 'device' }));
    });
    V2S.session.configure({ onWarmupDone, onBlockDone, onAllDone: () => showDone({ allDone: true }), onDeviceError, onStorageFull, onStartFailure, onStoreFailure });

    V2S.media.registerPreview(el('checkPreview'));
    V2S.media.registerPreview(el('recordPreview'));
    V2S.media.registerPreview(el('monitorVideo'));
    V2S.media.setMonitorVideo(el('monitorVideo'));
    V2S.meter.registerWave(el('checkWave'));
    V2S.meter.registerWave(el('recordWave'), { idleFlat: true, windowMs: 2400 });
    ui.watchPreviewShape('checkFrame', 'checkPreview');
    ui.watchPreviewShape('recordFrame', 'recordPreview');

    if (window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      document.documentElement.classList.add('has-keyboard');
    }

    // Presentation clickers and switches send PageDown / →. Outside the recording screen
    // (where input.js handles them) they press the highlighted button, so a clicker alone
    // gets through every screen; each screen highlights its main button.
    document.addEventListener('keydown', event => {
      if (event.repeat || !['PageDown', 'ArrowRight'].includes(event.key)) return;
      if (ui.screen() === 'record' && !ui.isDialogOpen()) return;
      const target = document.activeElement;
      if (!target || target.tagName !== 'BUTTON' || target.disabled || target.getAttribute('aria-disabled') === 'true') return;
      event.preventDefault();
      target.click();
    });
  }

  async function boot() {
    await window.__v2sGate;
    fillStaticCopy();
    wire();
    ui.labelTopbar(document.documentElement.getAttribute('data-theme'));
    // On a reload the previous copy of this page may take a moment to let go.
    let locked = await holdTabLock();
    for (let i = 0; !locked && i < 5; i++) {
      await sleep(300);
      locked = await holdTabLock();
    }
    if (!locked) {
      logEvent('tab_already_open', {});
      return showOtherTab(copy.tab.title, copy.tab.body);
    }
    try {
      await V2S.storage.init();
      await exporter.init();
      await loadSettings();
    } catch (error) {
      return showLoadError(error);
    }
    persistEvents();
    V2S.util.startSession();
    V2S.storage.trimEvents().catch(() => {});
    V2S.settings.init(api);
    app.participantId = await V2S.storage.getSetting('participantId', null);
    if (!app.participantId) showSetup();
    else await showWelcome();
  }

  // Used by Settings and tests.
  const api = {
    state: () => app,
    applyTheme,
    setTheme,
    showWelcome,
    showSetup,
    showCheck,
    runZipSave,
    pendingCount,
    reopenMedia,
    onSettingsClosed,
    signOut,
    restartSession: async () => {
      V2S.session.stop();
      V2S.input.setEnabled(false);
      await V2S.session.flush();
      V2S.media.stopHealth();
      V2S.meter.detach();
      V2S.media.close();
      app.sessionStarted = false;
      await showWelcome();
    },
    setParticipant: async participantId => {
      app.participantId = participantId;
      await V2S.storage.setSetting('participantId', participantId);
    },
    setSetKey: async setKey => {
      app.setKey = setKey;
      await V2S.storage.setSetting('setKey', setKey);
    },
    // Settings → Clear progress: back to the very start (Welcome, How to record, practice),
    // after every pending write, so nothing older can overwrite it.
    clearProgress: async () => {
      V2S.session.stop();
      await V2S.session.flush();
      V2S.session.startNewRoundIfCompleted(app.progress);
      Object.assign(app.progress, { currentIndex: 0, completed: false, completedAt: null, coachDone: false, howtoSeen: false, resumeIndex: null });
      delete app.progress.pendingRedo;
      await V2S.storage.saveParticipantProgress(app.progress);
      await api.restartSession();
    },
    // Settings → Previous / Next / Skip / Go to: during a session the screen just moves to
    // that sentence (no camera restart); otherwise the welcome screen shows the new place.
    jumpTo: async (index, extra = {}) => {
      V2S.session.startNewRoundIfCompleted(app.progress);
      Object.assign(app.progress, extra);
      if (app.sessionStarted && V2S.session.jumpTo(index)) {
        if (ui.screen() !== 'record') await showRecord();
        return;
      }
      Object.assign(app.progress, { currentIndex: index, completed: false, completedAt: null });
      await V2S.storage.saveParticipantProgress(app.progress);
      await showWelcome();
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    boot().catch(error => showLoadError(error));
  });

  return api;
})();
