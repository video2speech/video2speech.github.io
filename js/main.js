// Start-up and screen flow:
// setup (first time) → welcome → [folder permission] → camera check → recording
//   ⇄ block break → done.
// Rule for every click that needs the browser's permission or file dialogs: call the
// browser API FIRST in the click handler, before any other waiting, or the browser
// refuses (and a silent fallback would put recordings somewhere else).
window.V2S = window.V2S || {};

V2S.app = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const ui = V2S.ui;
  const exporter = V2S.exporter;
  const { el, logEvent, platform } = V2S.util;

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
    const text = {
      loadingText: copy.loading,
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
      welcomeLead: copy.welcome.lead,
      welcomeStart: copy.welcome.start,
      folderTitle: copy.folder.title,
      folderAllow: copy.folder.allow,
      folderChoose: copy.folder.choose,
      folderZip: copy.folder.zip,
      checkTitle: copy.check.title,
      checkFace: copy.check.face,
      checkVoice: copy.check.voice,
      checkOk: copy.check.ok,
      checkHelp: copy.check.help,
      finishButton: copy.record.finish
    };
    Object.entries(text).forEach(([id, value]) => ui.setText(id, value));
    el('setupId').placeholder = copy.setup.idPlaceholder;
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
    if (meta) meta.content = value === 'dark' ? '#0F1115' : '#F4F3EF';
    V2S.meter.refreshColors();
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

  const pendingCount = () => V2S.storage.countTakes();

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
        ? `warm-up sentence ${index + 1}`
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
    const firstVisit = (progress.tutorialStep || progress.tutorialTakes || 0) === 0 && progress.currentIndex === 0;
    ui.setText('welcomeTitle', firstVisit ? copy.welcome.titleFirst : copy.welcome.titleBack);
    ui.setText('welcomeParticipant', copy.welcome.participant(app.participantId));

    const p = positionFor(progress.currentIndex);
    if (progress.completed) {
      ui.setText('welcomeBlock', copy.welcome.allDone);
      ui.setText('welcomeCount', '');
      el('welcomeBar').style.transform = 'scaleX(1)';
    } else if (p.warmup) {
      ui.setText('welcomeBlock', copy.welcome.warmup);
      ui.setText('welcomeCount', copy.welcome.warmupCount(p.pos - 1, p.total));
      el('welcomeBar').style.transform = `scaleX(${((p.pos - 1) / p.total).toFixed(3)})`;
    } else {
      ui.setText('welcomeBlock', copy.welcome.block(p.block, p.blocks));
      ui.setText('welcomeCount', copy.welcome.blockCount(p.inBlock - 1, p.blockSize));
      el('welcomeBar').style.transform = `scaleX(${((p.inBlock - 1) / p.blockSize).toFixed(3)})`;
    }
    el('welcomeStart').hidden = Boolean(progress.completed);
    await refreshWelcomeNotice();
    ui.show('welcome');
    if (!el('welcomeStart').hidden) el('welcomeStart').focus({ preventScroll: true });
  }

  async function refreshWelcomeNotice() {
    const pending = await pendingCount();
    el('welcomeNotice').hidden = pending === 0;
    if (pending > 0) {
      ui.setText('welcomeNoticeText', copy.welcome.pending(pending));
      ui.setText('welcomeNoticeAction', copy.welcome.saveNow);
    }
  }

  async function onWelcomeSaveNow() {
    if (exporter.getSaveMode() === 'folder') {
      const permission = exporter.isFolderActive() ? 'granted' : await exporter.requestFolderPermission();
      if (permission !== 'granted') {
        const result = await askForFolder();
        ui.show('welcome');
        if (result === 'zip') await runZipSave('saved');
      }
      await flushPendingToFolder();
    } else {
      await runZipSave('saved');
    }
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
  // silently: the person decides here.
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
    renderSaveStatus(exporter.status());
    requestWakeLock();
    V2S.input.setEnabled(true);
    if (!app.sessionStarted) {
      app.sessionStarted = true;
      V2S.session.begin({ participantId: app.participantId, setKey: app.setKey, material: app.material, progress: app.progress });
    } else {
      V2S.ui.fitSentences(app.material.all);
      V2S.session.enterReady();
    }
  }

  function renderSaveStatus(status) {
    if (status.mode === 'folder') {
      if (status.problem) ui.setSaveStatus({ text: copy.saveStatus.folderProblem, tone: 'warn', actionable: true });
      else if (status.saving) ui.setSaveStatus({ text: copy.saveStatus.folderSaving });
      else ui.setSaveStatus({ text: copy.saveStatus.folder(folderLabel()), tone: 'ok' });
    } else {
      ui.setSaveStatus({ text: copy.saveStatus.device });
    }
  }

  async function onSaveStatusClick() {
    const status = exporter.status();
    if (!status.problem || V2S.session.getState() !== 'ready') return;
    V2S.session.stop();
    const permission = await exporter.requestFolderPermission(); // first: browser asks
    if (permission !== 'granted') await askForFolder();
    await flushPendingToFolder();
    await showRecord();
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

  function setSavePanel(panelId, textId, text, tone) {
    el(panelId).className = `save-panel${tone ? ` is-${tone}` : ''}`;
    ui.setText(textId, text);
  }

  function onWarmupDone() {
    V2S.input.setEnabled(false);
    ui.setText('breakTitle', copy.warmupDone.title);
    ui.setText('breakLead', copy.warmupDone.body);
    el('breakSave').hidden = true;
    setBreakButtons({ label: copy.warmupDone.next, action: () => showRecord() }, null, null);
    ui.show('break');
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
    await showBreak(copy.breakScreen.savePromptTitle, copy.feedback.storageFull);
  }

  async function showBreak(title, lead) {
    V2S.input.setEnabled(false);
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

  // Waits for every take of the session to be stored, then (folder mode) writes
  // anything still cached into the folder.
  async function settleWrites() {
    await V2S.session.flush();
    if (exporter.getSaveMode() === 'folder') {
      await exporter.flushFolderWrites();
      await flushPendingToFolder();
      await exporter.writeSessionLog(app.participantId, sessionSummary());
    }
  }

  async function refreshBreakSave() {
    const pending = await pendingCount();
    const cont = { label: copy.breakScreen.continue, action: () => showRecord() };
    const finish = { label: copy.breakScreen.finish, action: () => showDone({ allDone: false }) };
    if (exporter.getSaveMode() === 'folder') {
      if (pending === 0) {
        setSavePanel('breakSave', 'breakSaveText', copy.done.savedFolder(folderLabel()), 'ok');
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
      setSavePanel('breakSave', 'breakSaveText', copy.breakScreen.zipPrompt);
      setBreakButtons({ label: copy.breakScreen.saveButton, action: saveZipFromBreak }, null, { label: copy.breakScreen.later, action: () => showRecord() });
    }
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
    const label = breakState.mode === 'block' ? `block${String(breakState.block).padStart(2, '0')}` : 'saved';
    const result = await runZipSave(label, (done, total) => {
      el('breakSaveProgress').hidden = false;
      el('breakSaveBar').style.transform = `scaleX(${(done / total).toFixed(3)})`;
      ui.setText('breakSaveLabel', copy.breakScreen.saving(done, total));
    });
    el('breakSaveProgress').hidden = true;
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
  // a plain download is only cleared after the person confirms the file exists.
  async function runZipSave(label, onProgress) {
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const suggested = `${app.participantId || 'recordings'}_video-recordings-${stamp}_${label}.zip`;
    const target = await exporter.pickZipTarget(suggested);
    if (target === undefined) return 'cancelled';
    let result;
    try {
      result = await exporter.saveZip({ participantId: app.participantId, label, summary: sessionSummary(), target, onProgress });
    } catch (error) {
      logEvent('zip_failed', { error: String(error && error.message || error) });
      await ui.dialog({ title: copy.error.loadTitle, body: String(error && error.message || error), actions: [{ label: copy.common.ok, value: true, variant: 'primary' }], dismissValue: true });
      return 'failed';
    }
    if (!result.count) return 'nothing';
    let confirmed = result.verified;
    if (!confirmed) {
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
      if (answer === 'no') return runZipSave(label, onProgress);
      confirmed = answer === 'yes';
    }
    if (!confirmed) return 'unsure';
    await V2S.storage.deleteTakes(result.ids);
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
    ui.setText('doneTitle', allDone ? copy.done.allTitle : copy.done.finishTitle);
    ui.setText('doneBody', allDone ? copy.done.allBody : copy.done.finishBody);
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

  async function refreshDoneSave() {
    const pending = await pendingCount();
    const folder = exporter.getSaveMode() === 'folder';
    if (pending === 0) {
      setSavePanel('doneSavePanel', 'doneSaveText', folder ? copy.done.savedFolder(folderLabel()) : copy.breakScreen.savedZip, 'ok');
      el('doneSave').hidden = true;
      return;
    }
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
  function showError({ title, body, help, action, actionLabel }) {
    V2S.input.setEnabled(false);
    ui.setText('errorTitle', title);
    ui.setText('errorBody', body);
    el('errorHelp').hidden = !help;
    ui.setText('errorHelp', help || '');
    ui.setText('errorAction', actionLabel);
    el('errorAction').onclick = action;
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
        renderSaveStatus(exporter.status());
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
    el('setupFolderChoose').addEventListener('click', onSetupChooseFolder);
    el('setupFolderZip').addEventListener('click', async () => {
      await exporter.setSaveMode('zip');
      await showWelcome();
    });
    el('welcomeStart').addEventListener('click', onWelcomeStart);
    el('welcomeNoticeAction').addEventListener('click', onWelcomeSaveNow);
    el('checkOk').addEventListener('click', onCheckOk);
    el('checkHelp').addEventListener('click', () => ui.showCameraHelp());
    el('finishButton').addEventListener('click', onFinishToday);
    el('saveStatus').addEventListener('click', onSaveStatusClick);
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
    exporter.onStatus(status => { if (ui.screen() === 'record') renderSaveStatus(status); });

    V2S.media.registerPreview(el('checkPreview'));
    V2S.media.registerPreview(el('recordPreview'));
    V2S.media.setMonitorVideo(el('recordPreview'));
    V2S.meter.registerWave(el('checkWave'));
    V2S.meter.registerWave(el('recordWave'));
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
      await exporter.init();
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

  // Used by the researcher panel and tests.
  const api = {
    state: () => app,
    applyTheme,
    showWelcome,
    showSetup,
    runZipSave,
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
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    boot().catch(error => showLoadError(error));
  });

  return api;
})();
