// Start-up and screen flow:
// setup (first time) → welcome → camera check → recording ⇄ block break → done.
window.V2S = window.V2S || {};

V2S.app = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const ui = V2S.ui;
  const { el, logEvent, platform, sleep } = V2S.util;

  const app = {
    participantId: null,
    setKey: cfg.DEFAULT_SET,
    material: null,
    progress: null,
    sessionStarted: false,
    wakeLock: null
  };

  // ---------- static text ----------
  function fillStaticCopy() {
    ui.setText('loadingText', copy.loading);
    ui.setText('setupTitle', copy.setup.title);
    ui.setText('setupLead', copy.setup.lead);
    ui.setText('setupIdLabel', copy.setup.idLabel);
    el('setupId').placeholder = copy.setup.idPlaceholder;
    ui.setText('setupHint', copy.setup.idHint);
    ui.setText('setupNext', copy.setup.next);
    ui.setText('setupConfirmTitle', copy.setup.confirmTitle);
    ui.setText('setupConfirmYes', copy.setup.confirmYes);
    ui.setText('setupConfirmChange', copy.setup.confirmChange);
    ui.setText('setupFolderTitle', copy.setup.folderTitle);
    ui.setText('setupFolderLead', copy.setup.folderLead);
    ui.setText('setupFolderChoose', copy.setup.folderChoose);
    ui.setText('setupFolderZip', copy.setup.folderZip);
    ui.setText('welcomeLead', copy.welcome.lead);
    ui.setText('welcomeStart', copy.welcome.start);
    ui.setText('welcomeSaveNow', copy.welcome.saveNow);
    ui.setText('checkTitle', copy.check.title);
    ui.setText('checkFace', copy.check.face);
    ui.setText('checkVoice', copy.check.voice);
    ui.setText('checkOk', copy.check.ok);
    ui.setText('checkHelp', copy.check.help);
    ui.setText('finishButton', copy.record.finish);
  }

  // ---------- settings ----------
  async function loadSettings() {
    const media = await V2S.storage.getSetting('mediaSettings', null);
    V2S.media.setSettings(media || cfg.MEDIA_DEFAULTS);
    const setKey = await V2S.storage.getSetting('setKey', cfg.DEFAULT_SET);
    app.setKey = cfg.SETS[setKey] ? setKey : cfg.DEFAULT_SET;
    applyTheme(await V2S.storage.getSetting('theme', document.documentElement.getAttribute('data-theme') || 'light'));
  }

  function applyTheme(theme) {
    const value = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', value);
    try { localStorage.setItem('v2s_theme', value); } catch (error) { /* ignore */ }
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = value === 'dark' ? '#0B0F19' : '#F3F4F6';
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
      V2S.storage.appendEvents(batch).catch(error => console.warn('Event log write failed', error));
    };
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
    if (!document.hidden && ui.screen() === 'record') requestWakeLock();
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

  const cachedTakeCount = () => V2S.storage.countTakes();

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
        ? `warm-up sentence ${index + 1}`
        : `sentence ${index - app.material.warmupCount + 1} of ${app.material.formalCount}`;
      options.append(
        optionRow('legacyChoice', 'continue', true, `Continue from ${place}`, 'This device already has progress from the earlier recording page.'),
        optionRow('legacyChoice', 'fresh', false, 'Start from the beginning', 'Use this if the earlier progress belongs to someone else.')
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
    if (V2S.exporter.folderSupported()) {
      el('setupFolderError').hidden = true;
      showSetupStep('folder');
    } else {
      await V2S.exporter.setSaveMode('zip');
      await showWelcome();
    }
  }

  async function onChooseFolder() {
    try {
      const name = await V2S.exporter.chooseFolder();
      logEvent('folder_chosen', { name });
      await showWelcome();
    } catch (error) {
      if (error && error.name === 'AbortError') return;
      ui.setText('setupFolderError', copy.setup.folderFailed);
      el('setupFolderError').hidden = false;
      await V2S.exporter.setSaveMode('zip');
    }
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
    const firstVisit = !progress.tutorialTakes && progress.currentIndex === 0;
    ui.setText('welcomeTitle', firstVisit ? copy.welcome.titleFirst : copy.welcome.titleBack);
    ui.setText('welcomeParticipant', copy.welcome.participant(app.participantId));
    el('participantChip').textContent = app.participantId;

    const p = positionFor(progress.currentIndex);
    if (progress.completed) {
      ui.setText('welcomeBlock', copy.welcome.allDone);
      ui.setText('welcomeCount', '');
      el('welcomeBar').style.transform = 'scaleX(1)';
    } else if (p.warmup) {
      ui.setText('welcomeBlock', copy.welcome.warmup(p.pos, p.total));
      ui.setText('welcomeCount', '');
      el('welcomeBar').style.transform = `scaleX(${((p.pos - 1) / p.total).toFixed(3)})`;
    } else {
      ui.setText('welcomeBlock', copy.welcome.block(p.block, p.blocks));
      ui.setText('welcomeCount', copy.welcome.blockProgress(p.inBlock - 1, p.blockSize));
      el('welcomeBar').style.transform = `scaleX(${((p.inBlock - 1) / p.blockSize).toFixed(3)})`;
    }
    el('welcomeStart').hidden = Boolean(progress.completed);

    // Anything still cached was never saved to a file (ZIP mode), or failed to reach the
    // folder (folder mode). Either way, offer a ZIP before starting.
    const cached = await cachedTakeCount();
    el('welcomeUnsaved').hidden = cached === 0;
    if (cached > 0) ui.setText('welcomeUnsavedText', copy.welcome.unsaved(cached));
    ui.show('welcome');
    el('welcomeStart').focus({ preventScroll: true });
  }

  // Same numbering as the session, available before a session starts.
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

  // Guards against double taps starting the camera twice.
  let starting = false;

  async function onWelcomeStart() {
    if (starting) return;
    starting = true;
    try {
      await welcomeStart();
    } finally {
      starting = false;
    }
  }

  async function welcomeStart() {
    // Runs inside the click: unlocks audio on iOS and folder access on Chrome.
    V2S.meter.resume();
    if (V2S.exporter.getSaveMode() === 'folder') {
      const ok = await V2S.exporter.ensureFolderPermission(true);
      if (!ok) logEvent('folder_unavailable', {});
    }
    V2S.storage.requestPersistence();
    await showCheck();
  }

  // ---------- camera check ----------
  async function showCheck() {
    V2S.input.setEnabled(false);
    ui.show('check');
    ui.setText('checkStatus', copy.check.starting);
    el('checkOk').setAttribute('aria-disabled', 'true');
    try {
      await openMedia();
    } catch (error) {
      return showMediaError(error);
    }
    ui.setText('checkStatus', '');
    el('checkOk').setAttribute('aria-disabled', 'false');
    el('checkOk').focus({ preventScroll: true });
  }

  async function openMedia() {
    const stream = await V2S.media.open();
    V2S.meter.attach(stream);
    V2S.media.startHealth();
    return stream;
  }

  async function onCheckOk() {
    if (el('checkOk').getAttribute('aria-disabled') === 'true' || ui.screen() !== 'check') return;
    V2S.meter.resume();
    await showRecord();
  }

  // ---------- recording ----------
  async function showRecord() {
    ui.show('record');
    requestWakeLock();
    V2S.input.setEnabled(true);
    if (!app.sessionStarted) {
      app.sessionStarted = true;
      await V2S.session.begin({ participantId: app.participantId, setKey: app.setKey, material: app.material, progress: app.progress });
    } else {
      V2S.ui.fitSentences(app.material.all);
      V2S.session.enterReady();
    }
  }

  async function onFinishToday() {
    if (V2S.session.getState() !== 'ready') return;
    V2S.session.stop();
    await showDone({ allDone: false });
  }

  // ---------- breaks and saving ----------
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

  function setSaveBox(text, tone = '') {
    const box = el('breakSaveBox');
    box.className = `save-box${tone ? ` is-${tone}` : ''}`;
    ui.setText('breakSaveText', text);
  }

  async function onWarmupDone() {
    V2S.input.setEnabled(false);
    ui.show('break');
    ui.setText('breakTitle', copy.warmupDone.title);
    ui.setText('breakLead', copy.warmupDone.body);
    el('breakSaveBox').hidden = true;
    setBreakButtons({ label: copy.warmupDone.next, action: () => showRecord() });
    el('breakPrimary').focus({ preventScroll: true });
  }

  async function onBlockDone({ block }) {
    breakState.mode = 'block';
    breakState.block = block;
    await showBreak(copy.breakScreen.title(block), copy.breakScreen.lead);
  }

  async function onStorageFull() {
    breakState.mode = 'storage';
    V2S.session.stop();
    await showBreak(copy.breakScreen.savePrompt, copy.feedback.storageFull);
  }

  async function showBreak(title, lead) {
    V2S.input.setEnabled(false);
    ui.show('break');
    ui.setText('breakTitle', title);
    ui.setText('breakLead', lead);
    el('breakSaveBox').hidden = false;
    el('breakSaveProgress').hidden = true;
    setSaveBox(copy.record.statusSaving);
    setBreakButtons(null, null, null);
    const summary = sessionSummary();
    if (V2S.exporter.isFolderActive()) {
      await V2S.exporter.flushFolderWrites();
      await V2S.exporter.writeSessionLog(app.participantId, summary);
    }
    await refreshBreakSave();
    el('breakPrimary').focus({ preventScroll: true });
  }

  async function refreshBreakSave() {
    const cached = await cachedTakeCount();
    const cont = { label: copy.breakScreen.continue, action: () => showRecord() };
    const finish = { label: copy.breakScreen.finish, action: () => showDone({ allDone: false }) };
    const save = { label: copy.breakScreen.saveButton, action: () => saveFromBreak() };
    if (cached === 0) {
      setSaveBox(V2S.exporter.isFolderActive() ? copy.breakScreen.savedFolder : copy.breakScreen.savedZip, 'ok');
      setBreakButtons(cont, finish, null);
    } else if (V2S.exporter.isFolderActive()) {
      setSaveBox(copy.breakScreen.folderProblem(cached), 'warn');
      setBreakButtons(save, cont, { label: copy.breakScreen.finish, action: () => showDone({ allDone: false }) });
    } else {
      setSaveBox(copy.breakScreen.savePrompt);
      setBreakButtons(save, null, { label: copy.breakScreen.later, action: () => showRecord() });
    }
  }

  async function saveFromBreak() {
    const label = breakState.mode === 'block' ? `block${String(breakState.block).padStart(2, '0')}` : 'saved';
    const result = await runZipSave(label, (done, total) => {
      el('breakSaveProgress').hidden = false;
      el('breakSaveBar').style.transform = `scaleX(${(done / total).toFixed(3)})`;
      ui.setText('breakSaveLabel', copy.breakScreen.saving(done, total));
    });
    el('breakSaveProgress').hidden = true;
    if (result === 'saved' || result === 'nothing') {
      await refreshBreakSave();
    } else {
      setSaveBox(copy.breakScreen.notConfirmed, 'warn');
      setBreakButtons(
        { label: copy.breakScreen.saveButton, action: () => saveFromBreak() },
        null,
        { label: copy.breakScreen.later, action: () => showRecord() }
      );
    }
  }

  function saveHint(fileName) {
    if (platform.ios) return copy.saveConfirm.ios(fileName);
    if (platform.android) return copy.saveConfirm.android(fileName);
    return copy.saveConfirm.desktop(fileName);
  }

  // Downloads a ZIP and deletes the cached takes only after "Yes, it saved".
  async function runZipSave(label, onProgress) {
    let result;
    try {
      result = await V2S.exporter.downloadZip({ participantId: app.participantId, label, summary: sessionSummary(), onProgress });
    } catch (error) {
      logEvent('zip_failed', { error: String(error && error.message || error) });
      await ui.dialog({ title: copy.error.loadTitle, body: String(error && error.message || error), actions: [{ label: copy.common.ok, value: true, variant: 'primary' }], dismissValue: true });
      return 'failed';
    }
    if (!result.count) return 'nothing';
    const answer = await ui.dialog({
      title: copy.saveConfirm.title,
      body: saveHint(result.fileName),
      actions: [
        { label: copy.saveConfirm.yes, value: 'yes', variant: 'primary' },
        { label: copy.saveConfirm.no, value: 'no', variant: 'secondary' },
        { label: copy.saveConfirm.unsure, value: 'unsure', variant: 'secondary', default: true }
      ],
      dismissValue: 'unsure'
    });
    logEvent('zip_confirm', { answer, fileName: result.fileName, count: result.count });
    if (answer === 'yes') {
      await V2S.storage.deleteTakes(result.ids);
      await V2S.session.refreshStorage().catch(() => {});
      return 'saved';
    }
    if (answer === 'no') return runZipSave(label, onProgress);
    return 'unsure';
  }

  function sessionSummary() {
    return {
      participantId: app.participantId,
      sentenceSet: app.setKey,
      currentIndex: app.progress ? app.progress.currentIndex : null,
      completed: app.progress ? Boolean(app.progress.completed) : false,
      sessionId: V2S.util.getSessionId(),
      saveMode: V2S.exporter.getSaveMode(),
      media: V2S.media.snapshot(),
      settings: V2S.media.getSettings()
    };
  }

  // ---------- done ----------
  async function showDone({ allDone }) {
    V2S.input.setEnabled(false);
    V2S.session.stop();
    if (V2S.exporter.isFolderActive()) {
      await V2S.exporter.flushFolderWrites();
      await V2S.exporter.writeSessionLog(app.participantId, sessionSummary());
    }
    ui.setText('doneTitle', allDone ? copy.done.allTitle : copy.done.finishTitle);
    ui.setText('doneBody', allDone ? copy.done.allBody : copy.done.finishBody);
    ui.setText('doneAgain', copy.done.again);
    el('doneAgain').hidden = Boolean(allDone);
    await refreshDoneSave();
    ui.show('done');
    if (!el('doneSave').hidden) el('doneSave').focus({ preventScroll: true });
    releaseWakeLock();
    V2S.media.stopHealth();
    V2S.meter.detach();
    V2S.media.close();
    app.sessionStarted = false;
    logEvent('session_end', { allDone, index: app.progress && app.progress.currentIndex });
  }

  async function refreshDoneSave() {
    const cached = await cachedTakeCount();
    el('doneUnsaved').hidden = cached === 0;
    el('doneSave').hidden = cached === 0;
    if (cached > 0) {
      ui.setText('doneUnsavedText', copy.done.unsaved(cached));
      ui.setText('doneSave', copy.done.save);
    }
  }

  async function onDoneSave() {
    await runZipSave('saved');
    await refreshDoneSave();
  }

  // ---------- errors ----------
  function showError({ title, body, help, action, actionLabel }) {
    V2S.input.setEnabled(false);
    ui.show('error');
    ui.setText('errorTitle', title);
    ui.setText('errorBody', body);
    el('errorHelp').hidden = !help;
    ui.setText('errorHelp', help || '');
    ui.setText('errorAction', actionLabel);
    el('errorAction').onclick = action;
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

  function onDeviceError(code) {
    V2S.media.stopHealth();
    showError({
      title: copy.error.deviceTitle,
      body: copy.error.deviceBody,
      actionLabel: copy.error.reconnect,
      action: async () => {
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
    });
    logEvent('device_error_screen', { code });
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

  // ---------- boot ----------
  function wire() {
    el('setupForm').addEventListener('submit', onSetupSubmit);
    el('setupConfirmYes').addEventListener('click', onSetupConfirm);
    el('setupConfirmChange').addEventListener('click', () => showSetup(pendingSetup ? pendingSetup.participantId : ''));
    el('setupFolderChoose').addEventListener('click', onChooseFolder);
    el('setupFolderZip').addEventListener('click', async () => {
      await V2S.exporter.setSaveMode('zip');
      await showWelcome();
    });
    el('welcomeStart').addEventListener('click', onWelcomeStart);
    el('welcomeSaveNow').addEventListener('click', async () => {
      await runZipSave('saved');
      await showWelcome();
    });
    el('checkOk').addEventListener('click', onCheckOk);
    el('checkHelp').addEventListener('click', () => ui.showCameraHelp());
    el('finishButton').addEventListener('click', onFinishToday);
    el('doneSave').addEventListener('click', onDoneSave);
    el('doneAgain').addEventListener('click', () => showWelcome());

    V2S.input.configure({
      primary: press => V2S.session.onPrimary(press),
      secondary: press => V2S.session.onSecondary(press),
      hold: press => V2S.session.onHold(press)
    });
    V2S.input.bindButton(el('primaryButton'), 'primary');
    V2S.input.bindButton(el('secondaryButton'), 'secondary');
    V2S.media.onFailure(code => {
      if (ui.screen() === 'record') V2S.session.onDeviceFailure(code);
      else if (ui.screen() === 'check') showMediaError(Object.assign(new Error(code), { code: 'device' }));
    });
    V2S.session.configure({ onWarmupDone, onBlockDone, onAllDone: () => showDone({ allDone: true }), onDeviceError, onStorageFull });

    V2S.media.registerPreview(el('checkPreview'));
    V2S.media.registerPreview(el('recordPreview'));
    V2S.media.setMonitorVideo(el('recordPreview'));
    V2S.meter.registerLevelBar(el('checkLevel'));
    V2S.meter.registerLevelBar(el('recordLevel'));
    ui.watchPreviewShape('checkFrame', 'checkPreview');
    ui.watchPreviewShape('recordFrame', 'recordPreview');

    if (window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      document.documentElement.classList.add('has-keyboard');
    }
  }

  async function boot() {
    await window.__v2sGate;
    fillStaticCopy();
    wire();
    try {
      await V2S.storage.init();
      await V2S.exporter.init();
      await loadSettings();
    } catch (error) {
      return showLoadError(error);
    }
    persistEvents();
    V2S.util.startSession();
    V2S.storage.trimEvents().catch(() => {});
    if (V2S.admin) V2S.admin.init(api);
    app.participantId = await V2S.storage.getSetting('participantId', null);
    if (!app.participantId) showSetup();
    else await showWelcome();
  }

  // Used by the researcher panel.
  const api = {
    state: () => app,
    applyTheme,
    showWelcome,
    showSetup,
    runZipSave,
    loadMaterial,
    openMedia,
    restartSession: async () => {
      V2S.session.stop();
      V2S.input.setEnabled(false);
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
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    boot().catch(error => showLoadError(error));
  });

  return api;
})();
