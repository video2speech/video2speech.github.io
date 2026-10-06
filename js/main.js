// Start-up and screen flow:
//   setup (first time on a device) → welcome → [folder permission] → camera & microphone
//   check (1 place the camera, 2 test recording + playback) → recording (the first time:
//   practice, coached one step at a time) ⇄ breaks → done.
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
      setupIdLabel: copy.setup.idLabel,
      setupHint: copy.setup.idHint,
      setupNext: copy.setup.next,
      setupConfirmTitle: copy.setup.confirmTitle,
      setupConfirmYes: copy.setup.confirmYes,
      setupConfirmChange: copy.setup.confirmChange,
      setupFolderTitle: copy.setup.folderTitle,
      setupFolderChoose: copy.setup.folderChoose,
      setupFolderZip: copy.setup.folderZip,
      welcomeStage1: copy.welcome.stage1,
      welcomeStage2: copy.welcome.stage2,
      welcomeStage3: copy.welcome.stage3,
      folderTitle: copy.folder.title,
      folderAllow: copy.folder.allow,
      folderChoose: copy.folder.choose,
      folderZip: copy.folder.zip,
      checkCameraStep: copy.check.cameraStep,
      checkCameraTitle: copy.check.cameraTitle,
      checkNext: copy.check.next,
      checkMicStep: copy.check.micStep,
      checkMicTitle: copy.check.micTitle,
      testRecordLabel: copy.check.testRecord,
      testSayLabel: copy.check.testSayLabel,
      testSay: copy.check.testSay,
      testQuestion: copy.check.testQuestion,
      testYes: copy.check.testYes,
      testAgain: copy.check.testAgain,
      testReplay: copy.check.testReplay,
      testHint: copy.check.testHint,
      checkHelp: copy.check.help
    };
    Object.entries(text).forEach(([id, value]) => ui.setText(id, value));
    // Two sentences each: the second one starts its own line.
    ui.setSentences('setupLead', copy.setup.lead);
    ui.setSentences('setupFolderLead', copy.setup.folderLead);
    ui.setSentences('checkCameraText', copy.check.cameraText);
    ui.setSentences('checkMicText', copy.check.micText);
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
    if (meta) meta.content = value === 'dark' ? '#000000' : '#FFFFFF';
    V2S.meter.refreshColors();
  }

  async function setTheme(theme) {
    applyTheme(theme);
    await V2S.storage.setSetting('theme', theme === 'dark' ? 'dark' : 'light');
    logEvent('theme', { theme });
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
  let setupStep = null;
  function showSetupStep(step) {
    if (step !== setupStep) ui.pauseClicks();
    setupStep = step;
    el('setupStepId').hidden = step !== 'id';
    el('setupStepConfirm').hidden = step !== 'confirm';
    el('setupStepFolder').hidden = step !== 'folder';
    el('setupStepLegacy').hidden = step !== 'legacy';
    // A question (not the ID form): on touch screens its buttons sit at the bottom.
    el('screen-setup').classList.toggle('is-question', step !== 'id');
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
      el('setupHint').hidden = true;
      return;
    }
    el('setupError').hidden = true;
    el('setupHint').hidden = false;
    const existing = await V2S.storage.getProgress(V2S.storage.progressKey(value, app.setKey));
    const legacy = existing ? null : await V2S.storage.findUnclaimedLegacyProgress(app.setKey);
    pendingSetup = { participantId: value, legacy };
    ui.setText('setupConfirmId', value);
    el('setupLegacy').hidden = true;
    if (legacy) {
      await loadMaterial();
      const index = Math.min(Number(legacy.currentIndex) || 0, app.material.all.length - 1);
      const place = index < app.material.warmupCount
        ? `practice sentence ${index + 1}`
        : `sentence ${index - app.material.warmupCount + 1} of ${app.material.formalCount}`;
      pendingSetup.place = place;
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

  // Earlier progress on this device (before IDs): its own question, one at a time.
  function askLegacy() {
    ui.setText('setupLegacyTitle', copy.setup.legacyTitle);
    ui.setSentences('setupLegacyLead', copy.setup.legacyLead);
    ui.setText('setupLegacyContinue', copy.setup.legacyContinue(pendingSetup.place));
    ui.setText('setupLegacyFresh', copy.setup.legacyFresh);
    showSetupStep('legacy');
    el('setupLegacyContinue').focus();
  }

  async function onSetupConfirm() {
    if (!pendingSetup) return;
    if (pendingSetup.legacy && pendingSetup.useLegacy === undefined) return askLegacy();
    const useLegacy = Boolean(pendingSetup.legacy && pendingSetup.useLegacy);
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
    ui.setText('welcomeTitle', progress.completed ? copy.welcome.doneTitle : firstVisit ? copy.welcome.titleFirst : copy.welcome.titleBack);
    ui.setSentences('welcomeLead', firstVisit ? copy.welcome.leadFirst : copy.welcome.leadBack);
    el('welcomeStages').hidden = !firstVisit;
    el('welcomeJourney').hidden = firstVisit || Boolean(progress.completed);
    app.welcomeRule = !(firstVisit || needsPractice() || Boolean(progress.completed));
    el('welcomeRule').hidden = !app.welcomeRule;
    ui.setRich('welcomeRule', copy.rule(usesKeys()));

    // Where they are, as the parts (or practice sentences) done, one segment each.
    const p = positionFor(progress.currentIndex);
    const segments = (total, done, current) => {
      el('welcomeParts').replaceChildren(...Array.from({ length: total }, (_, i) => {
        const segment = document.createElement('span');
        if (i < done) segment.className = 'is-done';
        else if (i === current) segment.className = 'is-current';
        return segment;
      }));
    };
    if (progress.completed) {
      ui.setText('welcomePart', copy.welcome.allDone);
      ui.setText('welcomeCount', '');
      segments(partCount(), partCount(), -1);
    } else if (p.warmup) {
      ui.setText('welcomePart', copy.welcome.practice);
      ui.setText('welcomeCount', copy.welcome.practiceCount(p.pos - 1, p.total));
      segments(p.total, p.pos - 1, p.pos - 1);
    } else {
      ui.setText('welcomePart', copy.welcome.part(p.block, p.blocks));
      ui.setText('welcomeCount', p.inBlock > 1 ? copy.welcome.sentenceOf(p.inBlock, p.blockSize) : '');
      segments(p.blocks, p.block - 1, p.block - 1);
    }
    ui.setText('welcomeStart', firstVisit ? copy.welcome.begin : copy.welcome.continue);
    el('welcomeStart').hidden = Boolean(progress.completed);
    await refreshWelcomeNotice();
    if (progress.completed) ui.setSentences('welcomeLead', el('welcomeNotice').hidden ? copy.welcome.doneLead : copy.welcome.doneLeadUnsaved);
    ui.show('welcome');
    if (!el('welcomeStart').hidden) el('welcomeStart').focus({ preventScroll: true });
  }

  async function refreshWelcomeNotice() {
    const pending = await pendingCount();
    // In folder mode cached recordings are written automatically after Begin.
    // Mid-practice the practice recordings are saved at its end, as taught there.
    const show = pending > 0 && exporter.getSaveMode() !== 'folder' && !needsPractice();
    el('welcomeNotice').hidden = !show;
    // One step at a time: with unsaved recordings the main button saves them first (the
    // one thing to remember waits until then).
    app.welcomeSaveFirst = show;
    el('welcomeRule').hidden = !app.welcomeRule || show;
    // The notice says what to do first; "Carry on where you left off." waits (a finished
    // set keeps its lead, which says to save).
    el('welcomeLead').hidden = show && !(app.progress && app.progress.completed);
    // A way on if saving cannot be done now (the recordings stay on the device).
    el('welcomeLater').hidden = !show || Boolean(app.progress && app.progress.completed);
    ui.setText('welcomeLater', copy.breakScreen.laterGo);
    if (show) {
      ui.setText('welcomeNoticeText', copy.welcome.pending(pending));
      ui.setText('welcomeStart', copy.welcome.saveFirst);
      el('welcomeStart').hidden = false;
    } else if (app.progress && !app.progress.completed) {
      const firstVisit = !app.progress.howtoSeen && !app.progress.coachDone && app.progress.currentIndex === 0;
      ui.setText('welcomeStart', firstVisit ? copy.welcome.begin : copy.welcome.continue);
    } else {
      el('welcomeStart').hidden = true;
    }
  }

  // Guards against double taps starting the camera twice.
  let starting = false;

  async function onWelcomeStart(event, { skipSave = false } = {}) {
    if (zipSaving) return;   // a save is under way: its question comes first
    if (app.welcomeSaveFirst && !skipSave) {
      await saveFromButton('welcomeStart', copy.welcome.saveFirst, ['welcomeLater']);
      await refreshWelcomeNotice();
      if (app.progress.completed) ui.setSentences('welcomeLead', el('welcomeNotice').hidden ? copy.welcome.doneLead : copy.welcome.doneLeadUnsaved);
      if (!el('welcomeStart').hidden) el('welcomeStart').focus({ preventScroll: true });
      return;
    }
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
      ui.setSentences('folderLead', copy.folder.lead(exporter.folderName() || ''));
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
  // One step at a time: 1 place the camera (Next), 2 record a test and watch it back.
  function showCheckStep(step) {
    if (step !== app.checkStep) ui.pauseClicks();
    el('checkStepCamera').hidden = step !== 'camera';
    el('checkStepMic').hidden = step !== 'mic';
    document.querySelector('#screen-check .check').classList.toggle('is-camera-step', step === 'camera');
    app.checkStep = step;
    const focus = step === 'camera' ? el('checkNext') : (el('micChoice').hidden ? el('testRecord') : el('micSwitch'));
    if (focus && !focus.hidden) focus.focus({ preventScroll: true });
  }

  function onCheckNext() {
    if (ui.screen() !== 'check') return;
    logEvent('check_camera_ok', {});
    showCheckStep('mic');
  }

  async function showCheck({ returnTo = null } = {}) {
    app.checkReturn = returnTo || (app.sessionStarted ? 'record' : null);
    if (['ready', 'partEnd'].includes(V2S.session.getState())) V2S.session.stop();
    V2S.input.setEnabled(false);
    ui.show('check');
    resetTest();
    showCheckStep('camera');
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
    showCheckStep(app.checkStep || 'camera');
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

  // A badge on the picture only while something happens to it: the test recording (red,
  // it records) or its playback. The live picture needs no label.
  function setBadge(kind, extra) {
    const badge = el('checkBadge');
    badge.replaceChildren();
    if (!kind || kind === 'live') return;
    if (kind === 'recording') {
      const dot = document.createElement('span');
      dot.className = 'rec-dot';
      badge.append(dot);
    }
    // Short, so it never covers the face on a narrow picture (the bar under the phrase
    // shows the time left).
    const label = { live: copy.check.live, recording: copy.check.testRecording, playing: copy.check.testPlaying }[kind] || '';
    badge.append(document.createTextNode(label));
  }

  // The microphone in use, quietly, and a warning for Bluetooth headphones; devices are
  // changed in Settings → Camera and microphone.
  // The camera already works: help about devices (not about permission).
  async function onCheckHelp() {
    if (!V2S.media.getStream()) return ui.showCameraHelp();
    const choose = await ui.dialog({
      title: copy.liveHelp.title,
      body: copy.liveHelp.body,
      actions: [
        { label: copy.liveHelp.close, value: false, variant: 'go', default: true },
        { label: copy.liveHelp.choose, value: true, variant: 'text' }
      ],
      dismissValue: false
    });
    if (choose) V2S.settings.open('settingsDevices');
  }

  // 4. A Bluetooth microphone: switching to the device's own microphone is the step's
  // one main button (Record comes after); keeping the headphones is a quiet link.
  async function renderDevices() {
    const now = V2S.media.current();
    const warn = now.bluetooth && !app.keepBluetooth;
    el('micWarning').hidden = !warn;
    el('micChoice').hidden = true;
    if (!app.test.running && el('testAsk').hidden) el('testRecord').hidden = false;
    markMicProblem();
    if (!warn) return;
    ui.setText('micWarningText', copy.check.bluetooth);
    // Offer the device's own microphone if there is one.
    const { microphones } = await V2S.media.listDevices().catch(() => ({ microphones: [] }));
    const builtIn = microphones.find(mic => !V2S.media.isBluetooth(mic.label));
    if (!builtIn) return;
    ui.setText('micSwitch', copy.check.useDevice(builtIn.label));
    ui.setText('micKeep', copy.check.keepHeadphones);
    el('micChoice').hidden = false;
    el('testRecord').hidden = true;
    markMicProblem();
    if (app.checkStep === 'mic') {
      ui.pauseClicks();
      el('micSwitch').focus({ preventScroll: true });
    }
    el('micSwitch').onclick = async () => {
      const next = { ...V2S.media.getSettings(), audioDeviceId: builtIn.id };
      await V2S.storage.setSetting('mediaSettings', next);
      V2S.media.setSettings(next);
      logEvent('mic_switched', { to: builtIn.label });
      await reopenMedia();
      // Record now sits where this button was: a second tap must not start the test.
      ui.pauseClicks();
      if (!el('testRecord').hidden) el('testRecord').focus({ preventScroll: true });
    };
  }

  // A problem on the microphone step (Bluetooth headphones to replace, a test that heard
  // nothing): the step shows only the problem and its fix, without the instructions and
  // the help link (one thing at a time; it also fits a small phone).
  function markMicProblem() {
    el('screen-check').classList.toggle('has-problem', !el('micChoice').hidden || !el('testError').hidden);
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
    el('checkMicText').hidden = false;
    el('testRecord').setAttribute('aria-disabled', 'false');
    el('testLive').hidden = true;
    el('testStatus').hidden = true;
    el('testAsk').hidden = true;
    el('testHint').hidden = true;
    el('testError').hidden = true;
    el('testChooseMic').hidden = true;
    el('checkHelp').hidden = false;
    el('screen-check').classList.remove('is-asking');
    markMicProblem();
  }

  function showTestError(text) {
    resetTest();
    ui.setSentences('testErrorText', text);
    ui.setText('testChooseMic', copy.check.chooseMic);
    el('testError').hidden = false;
    el('testChooseMic').hidden = false;
    markMicProblem();
    setBadge('live');
    el('testRecord').focus({ preventScroll: true });
  }

  // Records TEST_RECORD_MS with the real recording settings, then plays it back.
  async function onTestRecord() {
    if (app.test.running || ui.screen() !== 'check') return;
    resetTest();
    app.test.running = true;
    V2S.meter.resume();
    el('testRecord').hidden = true;
    el('checkMicText').hidden = true;
    el('checkHelp').hidden = true;
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
      el('screen-check').classList.add('is-asking');
      el('checkHelp').hidden = true;
      el('testYes').scrollIntoView({ block: 'nearest' });
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
    // How to record is taught inside the practice, one step at a time; before it, the one
    // thing to remember.
    if (!app.progress.howtoSeen) {
      app.progress.howtoSeen = true;
      await V2S.storage.saveParticipantProgress(app.progress);
    }
    return needsPractice() ? showIntro() : showRecord();
  }

  const usesKeys = () => document.documentElement.classList.contains('has-keyboard');

  // Before the practice: the one thing to remember, and that the next sentences are
  // only for practice.
  function showIntro() {
    V2S.input.setEnabled(false);
    ui.setText('introEyebrow', copy.intro.eyebrow);
    ui.setText('introTitle', copy.intro.title);
    ui.setRich('introRule', copy.rule(usesKeys()));
    ui.setText('introLead', copy.intro.lead(Math.max(1, app.material.warmupCount - app.progress.currentIndex)));
    ui.setText('introStart', copy.intro.start);
    ui.show('intro');
    if (usesKeys()) el('introStart').focus({ preventScroll: true });
  }

  // ---------- how to record (the ? button) ----------
  // On a computer the keys are named as the controls (Space, ←); on touch, the buttons.
  async function onHelp() {
    const onRecord = ui.screen() === 'record' && ['ready', 'partEnd'].includes(V2S.session.getState());
    const onCheck = ui.screen() === 'check' && !app.test.running;
    if (!onRecord && !onCheck) return;
    if (onRecord) V2S.session.stop();
    logEvent('help_opened', { screen: ui.screen() });
    await ui.showHowto(document.documentElement.classList.contains('has-keyboard'));
    if (onRecord && ui.screen() === 'record') V2S.session.resume();
  }

  // ---------- recording ----------
  async function showRecord() {
    ui.show('record');
    requestWakeLock();
    V2S.input.setEnabled(true, { guard: true });
    if (!app.sessionStarted) {
      app.sessionStarted = true;
      V2S.session.begin({ participantId: app.participantId, setKey: app.setKey, material: app.material, progress: app.progress });
    } else {
      ui.fitSentences(app.material.all);
      V2S.session.resume();
    }
  }

  // Ending always asks first, from every screen: a stray or slightly missed tap must not
  // end the session.
  async function confirmEnd() {
    const end = await ui.dialog({
      title: copy.endDialog.title,
      body: copy.endDialog.body,
      actions: [
        { label: copy.endDialog.keep, value: false, variant: 'go', default: true },
        { label: copy.endDialog.end, value: true, variant: 'ghost' }
      ],
      dismissValue: false
    });
    logEvent('end_for_today', { confirmed: end, screen: ui.screen() });
    return end;
  }

  async function onFinishToday() {
    if (ui.screen() === 'break') return endFromBreak();
    if (ui.screen() !== 'record' || !['ready', 'partEnd'].includes(V2S.session.getState())) return;
    if (!await confirmEnd()) return;
    V2S.session.stop();
    await showDone({ allDone: false });
  }

  // Going on without saving asks first (Save now is the main answer), wherever it is offered.
  // Its "Continue without saving" lands where the link that opened it was: it counts only
  // after a second (a double tap must not skip the save). Esc answers nothing.
  function askContinueWithoutSaving() {
    return ui.dialog({
      title: copy.breakScreen.laterAsk,
      body: copy.breakScreen.laterAskBody,
      actions: [
        { label: copy.breakScreen.laterSave, value: false, variant: 'go', default: true },
        { label: copy.breakScreen.laterGo, value: true, variant: 'ghost' }
      ],
      dismissValue: null,
      armMs: 1000
    });
  }

  async function continueWithoutSaving() {
    const go = await askContinueWithoutSaving();
    if (go === null) return;
    if (go) return showRecord();
    return saveZipFromBreak();
  }

  async function endFromBreak() {
    if (zipSaving || ui.isDialogOpen()) return;   // a save is under way: its own question comes first
    if (await confirmEnd()) await showDone({ allDone: false });
  }

  function onSettingsClosed() {
    if (ui.screen() === 'record') {
      V2S.input.setEnabled(true, { guard: true });
      if (['ready', 'partEnd'].includes(V2S.session.getState())) V2S.session.resume();
    }
  }

  // ---------- practice done, breaks and saving ----------
  const breakState = { mode: 'block', block: 0 };

  function setBreakButtons(primary, secondary, tertiary, { focus = true } = {}) {
    const set = (id, config) => {
      const button = el(id);
      button.hidden = !config;
      if (config) {
        button.textContent = config.label;
        // The main button: blue moves on; a step that removes something is neutral.
        if (id === 'breakPrimary') {
          button.classList.toggle('btn-go', config.variant !== 'plain');
          button.classList.toggle('btn-ghost', config.variant === 'plain');
        }
        button.setAttribute('aria-disabled', 'false');
        button.onclick = () => { if (button.getAttribute('aria-disabled') !== 'true') config.action(); };
      }
    };
    set('breakPrimary', primary);
    set('breakSecondary', secondary);
    set('breakTertiary', tertiary);
    // On a computer Space / Enter / a clicker press the main button: keep it focused.
    // Never a confirmation that removes something ("It is saved — make room").
    if (primary && focus && document.documentElement.classList.contains('has-keyboard') && ui.screen() === 'break' && !ui.isDialogOpen()) {
      el('breakPrimary').focus({ preventScroll: true });
    }
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
    await showBreak(copy.practiceDone.title, copy.practiceDone.body, { parts: copy.practiceDone.parts(partCount(), cfg.BLOCK_SIZE) });
  }

  async function onBlockDone({ block, blocks }) {
    breakState.mode = 'block';
    breakState.block = block;
    breakState.next = block < blocks ? block + 1 : null;
    await showBreak(copy.breakScreen.title(block), copy.breakScreen.lead, { done: block, total: blocks });
  }

  async function onStorageFull() {
    breakState.mode = 'storage';
    breakState.next = null;
    V2S.session.stop();
    await showBreak(copy.breakScreen.savePromptTitle, copy.feedbackShort.storageFull);
  }

  // Parts done, as one row of segments (breaks), or one line about the parts (practice).
  function setParts({ done, total, parts } = {}) {
    const box = el('breakParts');
    const bar = el('breakPartsBar');
    bar.replaceChildren();
    box.hidden = !total && !parts;
    if (total) {
      for (let i = 0; i < total; i++) {
        const segment = document.createElement('span');
        if (i < done) segment.className = 'is-done';
        bar.appendChild(segment);
      }
      ui.setText('breakPartsLabel', copy.breakScreen.partsDone(done, total));
    } else {
      ui.setText('breakPartsLabel', parts || '');
    }
    bar.hidden = !total;
  }

  const SYMBOLS = {
    done: ['symbol-done', '<svg viewBox="0 0 24 24"><path d="m6.5 12.5 3.6 3.6 7.4-8"/></svg>'],
    warn: ['symbol-warn', '<svg viewBox="0 0 24 24"><path d="M12 8v5M12 16.4v.2"/><path d="M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>']
  };

  function setBreakSymbol(kind) {
    const [symbolClass, symbolIcon] = SYMBOLS[kind];
    el('breakSymbol').className = `symbol ${symbolClass}`;
    el('breakSymbol').innerHTML = symbolIcon;
  }

  async function showBreak(title, lead, parts) {
    V2S.input.setEnabled(false);
    breakState.savedNow = 0;
    breakState.lead = lead;
    const folder = exporter.getSaveMode() === 'folder';
    setBreakSymbol(breakState.mode === 'storage' ? 'warn' : 'done');
    ui.setText('breakTitle', title);
    // ZIP mode, and the practice: what to do (save first, or go on) appears once the
    // recordings are counted.
    ui.setSentences('breakLead', folder && breakState.mode !== 'practice' ? lead : '');
    el('breakRule').hidden = true;
    setParts(parts);
    // ZIP mode, practice: the parts are introduced after the practice recordings are saved.
    if (!folder && breakState.mode === 'practice') el('breakParts').hidden = true;
    el('breakSave').hidden = !folder;
    el('breakSaveProgress').hidden = true;
    setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.savingFolder);
    setBreakButtons(null, null, null);
    ui.show('break');
    await settleWrites();
    await refreshBreakSave();
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
      const hint = saveHint(release.fileName || '', { find: true });
      const [before, after] = copy.breakScreen.makeRoom('\u0001').split('\u0001');
      // The title says what is wrong; the panel what to check and what will be removed.
      ui.setText('breakTitle', copy.breakScreen.makeRoomTitle);
      setBreakSymbol('warn');
      ui.setSentences('breakLead', '');
      el('breakSave').hidden = false;
      setSavePanel('breakSave', 'breakSaveText', '', 'warn');
      el('breakSaveText').replaceChildren(before, ...(typeof hint === 'string' ? [hint] : [...hint.childNodes]), after || '');
      setBreakButtons(
        { label: copy.breakScreen.makeRoomYes, action: makeRoom, variant: 'plain' },
        null,
        { label: copy.breakScreen.saveAgain, action: saveBackupsAgain },
        { focus: false }
      );
      return;
    }
    const contLabel = practice ? breakState.continueLabel : (breakState.next ? copy.breakScreen.continueTo(breakState.next) : copy.breakScreen.continue);
    const cont = { label: contLabel, action: () => showRecord() };
    // Practice done. ZIP mode: saving is learnt here by doing it once (the same steps as
    // after every part), and only then the real sentences are introduced. Folder mode: the
    // screen says where every recording goes.
    el('breakRule').hidden = true;
    if (practice) {
      const folder = exporter.getSaveMode() === 'folder';
      if (!folder && pending > 0) {
        ui.setSentences('breakLead', copy.practiceDone.saveFirst);
        el('breakParts').hidden = true;
        el('breakSave').hidden = !breakState.savedNow;
        if (breakState.savedNow) setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.moreToSave(breakState.savedNow, pending));
        setBreakButtons({ label: copy.breakScreen.saveButton, action: saveZipFromBreak }, null, null);
        return;
      }
      ui.setSentences('breakLead', copy.practiceDone.body);
      ui.setRich('breakRule', copy.rule(usesKeys()));
      el('breakRule').hidden = false;
      el('breakParts').hidden = false;
      // ZIP: "Yes, I see it" has just said it is saved. Folder: saving is taught here, so
      // the screen says where every recording goes.
      el('breakSave').hidden = !folder;
      if (folder) setSavePanel('breakSave', 'breakSaveText', copy.practiceDone.savedFolder(folderLabel()), 'ok');
      setBreakButtons(cont, null, null);
      return;
    }
    if (exporter.getSaveMode() === 'folder') {
      const storage = breakState.mode === 'storage';
      if (storage) ui.setSentences('breakLead', pending === 0 ? copy.breakScreen.storageSaved : copy.feedbackShort.storageFull);
      if (pending > 0 && exporter.status().saving) {
        // Still writing (a slow folder): carrying on is safe, the writes continue — except
        // on a full device, where Continue would only come back here.
        setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.stillSaving(pending));
        setBreakButtons(storage ? null : cont, null, null);
        setTimeout(() => { if (ui.screen() === 'break') refreshBreakSave(); }, 1500);
      } else if (pending === 0) {
        // Everything is in the folder: nothing to say (a problem would be said).
        el('breakSave').hidden = true;
        setBreakButtons(cont, null, null);
      } else {
        setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.folderProblem(pending), 'warn');
        setBreakButtons({ label: copy.breakScreen.allowFolder, action: fixFolderFromBreak }, storage ? null : cont, null);
      }
      return;
    }
    if (breakState.mode === 'storage' && pending === 0 && !V2S.session.needsRoom()) {
      // Saved and room again: back to the sentence (no "saved" step in between).
      return showRecord();
    }
    if (breakState.mode === 'storage') {
      // Saved and room again: say so (no more "Save your recordings" above "saved").
      ui.setText('breakTitle', pending === 0 ? copy.breakScreen.roomTitle : copy.breakScreen.savePromptTitle);
      setBreakSymbol(pending === 0 ? 'done' : 'warn');
      ui.setSentences('breakLead', pending === 0 ? copy.breakScreen.roomLead : copy.feedback.storageFull);
      el('breakSave').hidden = !(pending > 0 && breakState.savedNow);
      if (pending > 0 && breakState.savedNow) setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.moreToSave(breakState.savedNow, pending));
      setBreakButtons(pending === 0 ? { label: copy.breakScreen.continue, action: () => showRecord() } : { label: copy.breakScreen.saveButton, action: saveZipFromBreak }, null, null);
    } else if (pending === 0) {
      // Saved: "Yes, I see it" has just said so; now only the rest and Continue.
      ui.setSentences('breakLead', breakState.lead);
      el('breakSave').hidden = true;
      setBreakButtons(cont, null, null);
    } else {
      // One instruction: save, then rest.
      ui.setSentences('breakLead', copy.breakScreen.leadSave);
      el('breakSave').hidden = !breakState.savedNow;
      if (breakState.savedNow) setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.moreToSave(breakState.savedNow, pending));
      setBreakButtons({ label: copy.breakScreen.saveButton, action: saveZipFromBreak }, null, null);
    }
  }

  // "Save it again" on the make-room step: nothing can be removed while it runs.
  async function saveBackupsAgain() {
    if (zipSaving) return;
    setBreakBusy(true);
    try {
      await runZipSave('backup', null, { backups: true });
    } finally {
      setBreakBusy(false);
    }
    await refreshBreakSave();
  }

  async function makeRoom() {
    if (zipSaving) return;
    const sure = await ui.dialog({
      title: copy.breakScreen.makeRoomAsk,
      body: copy.breakScreen.makeRoomAskBody,
      actions: [
        { label: copy.common.cancel, value: false, variant: 'go', default: true },
        { label: copy.breakScreen.makeRoomRemove, value: true, variant: 'ghost' }
      ],
      dismissValue: false
    });
    if (!sure) return;
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

  // While a save runs, the break's buttons and End for today rest (greyed out).
  function setBreakBusy(busy) {
    ['breakPrimary', 'breakSecondary', 'breakTertiary', 'finishButton'].forEach(id => el(id).setAttribute('aria-disabled', busy ? 'true' : 'false'));
  }

  async function saveZipFromBreak() {
    if (zipSaving) return;
    const label = breakState.mode === 'block' ? `part${String(breakState.block).padStart(2, '0')}` : breakState.mode === 'practice' ? 'practice' : 'saved';
    setBreakBusy(true);
    const result = await runZipSave(label, (done, total) => {
      if (done === null) {
        el('breakSaveProgress').hidden = true;
        el('breakSave').hidden = true;
        return;
      }
      el('breakSave').hidden = false;
      el('breakSaveProgress').hidden = false;
      el('breakSaveBar').style.transform = `scaleX(${(done / total).toFixed(3)})`;
      ui.setText('breakSaveLabel', copy.breakScreen.saving(done, total));
    }).finally(() => setBreakBusy(false));
    el('breakSaveProgress').hidden = true;
    if (result === 'saved') breakState.savedNow = (breakState.savedNow || 0) + app.lastSavedCount;
    if (result === 'saved' || result === 'nothing') {
      await refreshBreakSave();
    } else if (result !== 'cancelled') {
      el('breakSave').hidden = false;
      setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.notConfirmed, 'warn');
      setBreakButtons({ label: copy.breakScreen.saveButton, action: saveZipFromBreak },
        breakState.mode === 'storage' ? null : { label: copy.breakScreen.later, action: continueWithoutSaving },
        null);
    }
  }

  // The file to look for, without its time: "SEMG1_part01".
  // `find`: only where to look (the file is already downloaded).
  function saveHint(fileName, { find = false } = {}) {
    const name = String(fileName || '').replace(/_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.zip$/, '').replace(/\.zip$/, '');
    if (platform.ios) {
      const [before, after] = (find ? copy.saveConfirm.iosFind(name) : copy.saveConfirm.ios(name)).split('⬇');
      const text = document.createElement('p');
      const icon = document.createElement('span');
      icon.className = 'inline-icon';
      icon.setAttribute('role', 'img');
      icon.setAttribute('aria-label', 'downloads');
      icon.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.25"/><path d="M12 7.5v8M8.5 12.5 12 16l3.5-3.5"/></svg>';
      text.append(before, icon, after || '');
      return text;
    }
    if (platform.android) return copy.saveConfirm.android(name);
    return copy.saveConfirm.desktop(name);
  }

  // ZIP save. The save dialog (Chrome/Edge) opens FIRST, while the click still counts;
  // a plain download is only cleared after the participant confirms the file exists.
  // One save at a time: a second press while the ZIP is built or the question is open
  // does nothing (it would download the same file twice).
  let zipSaving = false;
  // A save started from Welcome or Done shows its progress on the button and takes no
  // second press until it is over (as on a break).
  async function saveFromButton(buttonId, idleLabel, alsoBusy = []) {
    if (zipSaving) return 'busy';
    el(buttonId).setAttribute('aria-busy', 'true');
    alsoBusy.forEach(id => el(id).setAttribute('aria-disabled', 'true'));
    try {
      return await runZipSave('saved', (done, total) => {
        ui.setText(buttonId, done === null || done === undefined ? idleLabel : copy.breakScreen.saving(done, total));
      });
    } finally {
      el(buttonId).removeAttribute('aria-busy');
      alsoBusy.forEach(id => el(id).setAttribute('aria-disabled', 'false'));
      ui.setText(buttonId, idleLabel);
    }
  }

  async function runZipSave(label, onProgress, options = {}) {
    if (zipSaving) return 'busy';
    zipSaving = true;
    try {
      return await saveZipOnce(label, onProgress, options);
    } finally {
      zipSaving = false;
    }
  }

  async function saveZipOnce(label, onProgress, { backups = false } = {}) {
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const suggested = `${app.participantId || 'recordings'}_${label}_${stamp}.zip`;
    const target = await exporter.pickZipTarget(suggested);
    if (target === undefined) return 'cancelled';
    let result;
    try {
      // Every take recorded so far is in storage before the ZIP is built.
      await V2S.session.flush();
      await app.flushEvents();
      result = await exporter.saveZip({ participantId: app.participantId, label, summary: sessionSummary(), target, onProgress, backups });
      if (onProgress) onProgress(null, null);   // the file is with the browser: no more "Preparing…"
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
          { label: copy.saveConfirm.yes, value: 'yes', variant: 'go', default: true },
          { label: copy.saveConfirm.no, value: 'no', variant: 'plain' },
          { label: copy.saveConfirm.unsure, value: 'unsure', variant: 'text' }
        ],
        dismissValue: 'unsure',
        focus: false,
        armMs: 1000
      });
      logEvent('zip_confirm', { answer, fileName: result.fileName, count: result.count });
      if (answer === 'no') return saveZipOnce(label, onProgress, { backups });
      confirmed = answer === 'yes';
    }
    if (!confirmed) return 'unsure';
    app.lastSavedCount = result.count;
    if (!backups) {
      // Kept as backup copies (left out of later ZIPs) until space is needed: a mistaken
      // "Yes" must not lose a part.
      await V2S.storage.markExported(result.ids, result.fileName);
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
    setSavePanel('doneSavePanel', 'doneSaveText', copy.breakScreen.savingFolder);
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
    ok: ['symbol-done', '<svg viewBox="0 0 24 24"><path d="m6.5 12.5 3.6 3.6 7.4-8"/></svg>'],
    wait: ['symbol-neutral', '<svg viewBox="0 0 24 24"><path d="M12 4.5v10M7.5 10 12 14.5l4.5-4.5M5.5 19h13"/></svg>']
  };

  function setDoneBadge(kind) {
    const [className, icon] = BADGES[kind];
    el('doneBadge').className = `symbol ${className}`;
    el('doneBadge').innerHTML = icon;
  }

  async function refreshDoneSave() {
    const pending = await pendingCount();
    const folder = exporter.getSaveMode() === 'folder';
    if (pending === 0) {
      setDoneBadge('ok');
      ui.setSentences('doneBody', app.doneAll ? copy.done.allBody : copy.done.finishBody);
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
    if (usesKeys()) el('doneSave').focus({ preventScroll: true });
  }

  async function onDoneSave() {
    if (zipSaving) return;
    if (exporter.getSaveMode() === 'folder') {
      const permission = await exporter.requestFolderPermission(); // first: browser asks
      if (permission !== 'granted') {
        const result = await askForFolder();
        ui.show('done');
        if (result === 'zip') return refreshDoneSave();
      }
      await flushPendingToFolder();
    } else {
      await saveFromButton('doneSave', copy.done.save, ['doneAgain']);
    }
    await refreshDoneSave();
  }

  // ---------- errors ----------
  function showError({ title, body, help, action, actionLabel, secondary, neutral = false }) {
    V2S.input.setEnabled(false);
    el('errorSymbol').className = `symbol ${neutral ? 'symbol-neutral' : 'symbol-warn'}`;
    el('errorSymbol').innerHTML = neutral ? SYMBOLS.done[1] : SYMBOLS.warn[1];
    ui.setText('errorTitle', title);
    ui.setSentences('errorBody', body);
    el('errorHelp').hidden = !help;
    ui.setText('errorHelp', help || '');
    el('errorAction').hidden = !actionLabel;
    ui.setText('errorAction', actionLabel || '');
    el('errorAction').onclick = action || null;
    el('errorSecondary').hidden = !secondary;
    if (secondary) {
      ui.setText('errorSecondary', secondary.label);
      el('errorSecondary').onclick = secondary.action;
    }
    ui.show('error');
    if (actionLabel && usesKeys()) el('errorAction').focus({ preventScroll: true });
  }

  function showMediaError(error) {
    logEvent('media_error', { code: error && error.code, error: String(error && (error.name || error.message) || error) });
    V2S.media.close();
    if (error && error.code === 'unsupported') {
      return showError({
        title: copy.error.unsupportedTitle,
        body: copy.error.unsupportedBody,
        actionLabel: copy.error.copyLink,
        action: async () => {
          const link = window.location.origin + '/index.html';
          // "Link copied" only when it was: otherwise the link is shown to copy by hand.
          let copied = false;
          try { await navigator.clipboard.writeText(link); copied = true; } catch (copyError) { window.prompt('', link); }
          if (copied) ui.setText('errorAction', copy.error.linkCopied);
        }
      });
    }
    if (error && error.code === 'permission') {
      return showError({ title: copy.error.permissionTitle, body: copy.error.permissionBody, help: ui.helpText(), actionLabel: copy.error.reload, action: () => window.location.reload() });
    }
    return showError({ title: copy.error.deviceTitle, body: copy.error.deviceBody, help: ui.helpText(), actionLabel: copy.error.tryAgain, action: () => showCheck() });
  }

  async function reconnectAndResume() {
    if (el('errorAction').getAttribute('aria-disabled') === 'true') return;   // already reconnecting
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
    V2S.input.setEnabled(true, { guard: true });
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
      body: copy.error.loadBody,
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

  // Already open elsewhere: taking over is the action. Taken over: nothing is wrong here
  // (recording goes on in the other tab), so a neutral screen with a quiet link.
  function showOtherTab(title, body, { moved = false } = {}) {
    const takeOver = async () => {
      logEvent('tab_take_over', {});
      await holdTabLock(true);
      window.location.reload();
    };
    if (moved) {
      showError({ title, body, neutral: true, secondary: { label: copy.tab.useHere, action: takeOver } });
    } else {
      showError({ title, body, actionLabel: copy.tab.useHere, action: takeOver });
    }
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
    showOtherTab(copy.tab.movedTitle, copy.tab.movedBody, { moved: true });
  }

  // ---------- boot ----------
  function wire() {
    el('setupForm').addEventListener('submit', onSetupSubmit);
    el('setupConfirmYes').addEventListener('click', onSetupConfirm);
    el('setupConfirmChange').addEventListener('click', () => showSetup(pendingSetup ? pendingSetup.participantId : ''));
    el('setupLegacyContinue').addEventListener('click', () => { pendingSetup.useLegacy = true; onSetupConfirm(); });
    el('setupLegacyFresh').addEventListener('click', () => { pendingSetup.useLegacy = false; onSetupConfirm(); });
    el('setupFolderChoose').addEventListener('click', onSetupChooseFolder);
    el('setupFolderZip').addEventListener('click', async () => {
      await exporter.setSaveMode('zip');
      await showWelcome();
    });
    el('welcomeStart').addEventListener('click', onWelcomeStart);
    el('welcomeLater').addEventListener('click', async event => {
      if (zipSaving) return;
      const go = await askContinueWithoutSaving();
      if (go === null) return;
      return onWelcomeStart(event, { skipSave: go });
    });
    el('checkNext').addEventListener('click', onCheckNext);
    el('testRecord').addEventListener('click', onTestRecord);
    el('testYes').addEventListener('click', onTestYes);
    el('introStart').addEventListener('click', () => showRecord());
    el('testAgain').addEventListener('click', () => { resetTest(); showCheckStep('camera'); });
    el('testReplay').addEventListener('click', () => {
      const playback = el('checkPlayback');
      if (!app.test.url || playback.hidden) return;
      playback.currentTime = 0;
      setBadge('playing');
      playback.play().catch(() => {});
      el('testHint').hidden = false;   // played again: the hint for not hearing it
      logEvent('mic_test_replay', {});
    });
    el('checkHelp').addEventListener('click', onCheckHelp);
    el('testChooseMic').addEventListener('click', () => V2S.settings.open('settingsDevices'));
    el('micKeep').addEventListener('click', async () => {
      app.keepBluetooth = true;
      logEvent('bluetooth_kept', {});
      await renderDevices();
      ui.pauseClicks();
      if (!el('testRecord').hidden) el('testRecord').focus({ preventScroll: true });
    });
    el('finishButton').addEventListener('click', onFinishToday);
    el('helpButton').addEventListener('click', onHelp);
    el('doneSave').addEventListener('click', onDoneSave);
    el('doneAgain').addEventListener('click', () => { if (!zipSaving) showWelcome(); });

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
    ui.labelTopbar();
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
    // Settings → Clear progress: back to the very start (Welcome, the check, practice),
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
