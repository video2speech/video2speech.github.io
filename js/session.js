// The recording state machine.
//   ready → recording → finishing (tail) → checking → next sentence (ready)
//                                                  ↘ same sentence (ready)
// Every failure path (held press, no speech, too loud, timeout, device problem,
// page hidden, reload) returns to the SAME sentence: progress only moves forward
// when a take is accepted or the person chooses "Keep it and continue".
// A take and the progress it causes are written in ONE IndexedDB transaction, in
// order, in the background — the screen never waits for storage, and a crash can
// never record progress without the take.
window.V2S = window.V2S || {};

V2S.session = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const { logEvent, sanitize, timestamp, uid, sinceSessionStart, sleep } = V2S.util;

  let ctx = null;            // { participantId, setKey, material, progress }
  let state = 'idle';
  let take = null;
  let feedback = null;       // { text, tone, transient, setAt }
  let lastAccepted = null;   // { index, fileName } accepted during this session
  let redo = null;           // { targetIndex, returnIndex, supersedes }
  let qcFailures = { index: null, count: 0 };
  let sentenceShownAt = 0;
  let takesThisSession = 0;
  let idleHintTimer = null;
  let savedTimer = null;
  let justSaved = false;
  let deviceFailureActive = false;
  let storageBlocked = false;
  let writeChain = Promise.resolve();
  const usedNames = new Set();
  let handlers = {};

  function configure(next) {
    handlers = { ...handlers, ...next };
  }

  const getState = () => state;
  const getContext = () => ctx;
  const index = () => ctx.progress.currentIndex;

  // ---- positions and labels ----
  function position(i) {
    const { warmupCount, formalCount } = ctx.material;
    if (i < warmupCount) return { warmup: true, pos: i + 1, total: warmupCount };
    const formal = i - warmupCount;
    const block = Math.floor(formal / cfg.BLOCK_SIZE);
    const blockStart = block * cfg.BLOCK_SIZE;
    const blockSize = Math.min(cfg.BLOCK_SIZE, formalCount - blockStart);
    return {
      warmup: false,
      pos: formal + 1,
      total: formalCount,
      block: block + 1,
      blocks: Math.ceil(formalCount / cfg.BLOCK_SIZE),
      inBlock: formal - blockStart + 1,
      blockSize
    };
  }

  function progressView(i) {
    const p = position(i);
    if (p.warmup) {
      return { progressMain: copy.record.warmupOf(p.pos, p.total), progressSub: '', progress: (p.pos - 1) / p.total };
    }
    return {
      progressMain: copy.record.sentenceOf(p.inBlock, p.blockSize),
      progressSub: copy.record.breakIn(p.blockSize - p.inBlock + 1),
      progress: (p.inBlock - 1) / p.blockSize
    };
  }

  // ---- tutorial (first session only) ----
  function tutorialStep() {
    const progress = ctx.progress;
    if (Number.isInteger(progress.tutorialStep)) return progress.tutorialStep;
    return progress.tutorialTakes >= 2 ? 3 : (progress.tutorialTakes || 0);
  }

  function tutorialTip(phase) {
    const step = tutorialStep();
    if (step === 0) {
      return phase === 'ready'
        ? { text: copy.tutorial.startFirst, tone: 'tip', highlight: 'primary' }
        : { text: copy.tutorial.stopFirst, tone: 'tip', highlight: 'primary' };
    }
    if (step === 1) {
      if (phase === 'ready') return canRedoLast() ? { text: copy.tutorial.redoLast, tone: 'tip', highlight: 'secondary' } : null;
      return { text: copy.tutorial.startOver, tone: 'tip', highlight: 'secondary' };
    }
    if (step === 2 && phase === 'ready') {
      const folder = V2S.exporter.getSaveMode() === 'folder';
      return { text: folder ? copy.tutorial.saveFolder : copy.tutorial.saveDevice, tone: 'tip', highlight: 'save' };
    }
    return null;
  }

  function canRedoLast() {
    return !redo && lastAccepted !== null && lastAccepted.index === index() - 1;
  }

  // ---- views ----
  function messageFor(phase) {
    if (feedback) return { message: { text: feedback.text, tone: feedback.tone }, highlight: null };
    const tip = tutorialTip(phase);
    return tip ? { message: { text: tip.text, tone: 'tip' }, highlight: tip.highlight } : { message: null, highlight: null };
  }

  function readyView() {
    const redoAvailable = canRedoLast();
    return {
      ...progressView(index()),
      ...messageFor('ready'),
      state: 'ready',
      justSaved,
      stateText: justSaved ? copy.record.stateSaved : copy.record.stateReady,
      sentence: ctx.material.all[index()],
      primary: { label: copy.record.start, icon: 'rec', disabled: false },
      secondary: { label: copy.record.redoLast, icon: 'undo', hidden: !redoAvailable, disabled: !redoAvailable },
      showFinish: true
    };
  }

  function recordingView() {
    return {
      ...progressView(index()),
      ...messageFor('recording'),
      state: 'recording',
      justSaved: false,
      stateText: copy.record.stateRecording,
      sentence: ctx.material.all[index()],
      primary: { label: copy.record.stop, icon: 'stop', disabled: false },
      secondary: { label: copy.record.startOver, icon: 'restart', hidden: false, disabled: false },
      showFinish: false
    };
  }

  function busyView(phase) {
    return {
      ...progressView(index()),
      state: phase,
      justSaved: false,
      stateText: copy.record.stateSaving,
      sentence: ctx.material.all[index()],
      primary: { label: copy.record.saving, icon: 'spinner', disabled: true },
      secondary: { label: copy.record.startOver, icon: 'restart', hidden: true, disabled: true },
      message: null,
      highlight: null,
      showFinish: false
    };
  }

  function render(view) {
    V2S.meter.setLive(view.state === 'recording');
    V2S.ui.renderRecord(view);
  }

  function setFeedback(text, tone = 'warn', transient = false) {
    clearTimeout(idleHintTimer);
    feedback = text ? { text, tone, transient, setAt: performance.now() } : null;
  }

  // ---- lifecycle ----
  function begin({ participantId, setKey, material, progress }) {
    ctx = { participantId, setKey, material, progress };
    if (!ctx.progress.takeCounts) ctx.progress.takeCounts = {};
    if (!Number.isInteger(ctx.progress.tutorialStep)) ctx.progress.tutorialStep = tutorialStep();
    lastAccepted = null;
    redo = null;
    feedback = null;
    justSaved = false;
    qcFailures = { index: null, count: 0 };
    deviceFailureActive = false;
    V2S.ui.fitSentences(material.all);
    logEvent('session_begin', { participantId, setKey, index: progress.currentIndex });
    enterReady();
  }

  function stop() {
    state = 'idle';
    take = null;
    V2S.meter.setIdleDetection(false);
    V2S.meter.setLive(false);
    clearTimeout(idleHintTimer);
    clearTimeout(savedTimer);
    justSaved = false;
    V2S.ui.setRecordingFrame(false);
  }

  function enterReady() {
    state = 'ready';
    take = null;
    sentenceShownAt = performance.now();
    V2S.meter.setIdleDetection(true, onIdleSpeech);
    render(readyView());
    logEvent('ready', { index: index() });
    refreshStorageGuard().catch(() => {});
  }

  function showJustSaved() {
    justSaved = true;
    clearTimeout(savedTimer);
    savedTimer = setTimeout(() => {
      justSaved = false;
      if (state === 'ready') render(readyView());
    }, cfg.SAVED_LABEL_MS);
  }

  // Speaking before Start: a gentle reminder that nothing is being recorded.
  function onIdleSpeech() {
    if (state !== 'ready') return;
    // Leave a fresh message (e.g. "Please tap, don't hold") up long enough to be read.
    if (feedback && !feedback.transient && performance.now() - feedback.setAt < 4000) return;
    setFeedback(copy.feedback.speechBeforeStart, 'info', true);
    render(readyView());
    logEvent('speech_before_start', { index: index() });
    idleHintTimer = setTimeout(() => {
      if (state === 'ready' && feedback && feedback.transient) {
        feedback = null;
        render(readyView());
      }
    }, 5000);
  }

  // ---- presses ----
  function onPrimary({ source }) {
    if (state === 'ready') startTake(source);
    else if (state === 'recording') stopTake(source);
  }

  function onSecondary() {
    if (state === 'ready') redoLast();
    else if (state === 'recording') abortTake('restarted', copy.feedback.restarted, 'info');
  }

  function onHold() {
    if (state === 'recording') {
      abortTake('aborted_hold', copy.feedback.hold);
    } else if (state === 'ready') {
      setFeedback(copy.feedback.hold, 'warn');
      render(readyView());
    }
    // While finishing, finalize() sees the hold through waitForRelease() and aborts.
  }

  // The press must turn the screen red at once, so nothing here waits on async work.
  function startTake(source) {
    if (state !== 'ready' || deviceFailureActive) return;
    if (storageBlocked) {
      logEvent('storage_blocked', {});
      setFeedback(copy.feedback.storageFull, 'warn');
      render(readyView());
      if (handlers.onStorageFull) handlers.onStorageFull();
      return;
    }
    state = 'recording';
    // The press is a user gesture: wake the audio analysis if iOS paused it.
    V2S.meter.resume();
    clearTimeout(savedTimer);
    justSaved = false;
    const i = index();
    const current = {
      id: uid(),
      index: i,
      sentence: ctx.material.all[i],
      source,
      shownAt: sentenceShownAt,
      pressAt: performance.now(),
      closed: false,
      recorder: null,
      redo: redo && redo.targetIndex === i ? { ...redo } : null
    };
    take = current;
    setFeedback(null);
    V2S.meter.setIdleDetection(false);
    render(recordingView());
    V2S.sounds.play('start');
    logEvent('take_start', { index: i, source, takeId: current.id });

    // The start sound plays first so it is not in the recording.
    current.startTimer = setTimeout(() => {
      if (current.closed) return;
      try {
        V2S.meter.beginCollect();
        current.recorder = V2S.media.startRecorder();
        V2S.media.startMonitor();
      } catch (error) {
        logEvent('recorder_start_failed', { error: String(error && error.message || error) });
        onDeviceFailure('recorder_start_failed');
      }
    }, cfg.START_CUE_LEAD_MS);

    current.maxTimer = setTimeout(() => {
      if (!current.closed && take === current && state === 'recording') {
        abortTake('aborted_timeout', copy.feedback.timeout);
      }
    }, cfg.MAX_TAKE_MS);
  }

  function stopTake(source) {
    if (state !== 'recording' || !take) return;
    const current = take;
    state = 'finishing';
    current.stopAt = performance.now();
    current.stopSource = source;
    clearTimeout(current.maxTimer);
    render(busyView('finishing'));
    logEvent('take_stop', { index: current.index, source, takeId: current.id });
    finishTail(current);
  }

  // Keep recording a moment after Stop (people often press while saying the last word).
  // A fixed delay: no speech detection, so it is the same for every take.
  async function finishTail(current) {
    await sleep(cfg.TAIL_MS);
    current.tailMs = Math.round(performance.now() - current.stopAt);
    finalize(current);
  }

  async function closeRecorder(current) {
    clearTimeout(current.startTimer);
    clearTimeout(current.maxTimer);
    V2S.media.stopMonitor();
    let recording = null;
    if (current.recorder) {
      try {
        recording = await current.recorder.stop();
      } catch (error) {
        logEvent('recorder_stop_failed', { error: String(error) });
      }
    }
    current.recorderStoppedAt = performance.now();
    const frames = V2S.meter.endCollect();
    return { recording, frames };
  }

  async function finalize(current) {
    if (current.closed || take !== current) return;
    const release = await V2S.input.waitForRelease();
    if (current.closed || take !== current) return;
    if (release === 'hold') {
      abortTake('aborted_hold', copy.feedback.hold, 'warn', current);
      return;
    }
    current.closed = true;
    state = 'checking';
    render(busyView('checking'));
    const { recording, frames } = await closeRecorder(current);
    if (!recording || !recording.blob || !recording.blob.size) {
      logEvent('take_empty', { index: current.index });
      setFeedback(copy.feedback.device, 'warn');
      enterReady();
      return;
    }
    const qc = V2S.qc.evaluate(frames);

    if (qc.pass) {
      persistTake(current, recording, qc, 'accepted', current.index + 1);
      qcFailures = { index: null, count: 0 };
      advance(current);
      return;
    }

    if (qcFailures.index !== current.index) qcFailures = { index: current.index, count: 0 };
    qcFailures.count += 1;
    const reason = copy.feedback[qc.code] || copy.feedback.no_speech;
    V2S.sounds.play('retry');
    logEvent('qc_failed', { index: current.index, code: qc.code, failures: qcFailures.count, speechMs: qc.metrics.speechMs });

    if (qcFailures.count >= cfg.QC.OVERRIDE_AFTER_FAILURES) {
      const choice = await V2S.ui.dialog({
        title: copy.keepDialog.title,
        body: copy.keepDialog.body(reason),
        actions: [
          { label: copy.keepDialog.retry, value: 'retry', variant: 'primary', default: true },
          { label: copy.keepDialog.keep, value: 'keep', variant: 'secondary' }
        ],
        dismissValue: 'retry'
      });
      logEvent('qc_choice', { index: current.index, choice });
      if (choice === 'keep') {
        persistTake(current, recording, qc, 'qc_overridden', current.index + 1);
        qcFailures = { index: null, count: 0 };
        advance(current);
        return;
      }
    }

    persistTake(current, recording, qc, 'qc_failed', current.index);
    setFeedback(reason, 'warn');
    enterReady();
  }

  // Ends the current take without accepting it. The take is still saved (marked with
  // its status) and the same sentence comes back.
  async function abortTake(status, message, tone = 'warn', current = take) {
    if (!current || current.closed) return;
    current.closed = true;
    state = 'checking';
    render(busyView('checking'));
    const { recording, frames } = await closeRecorder(current);
    if (recording && recording.blob && recording.blob.size) {
      persistTake(current, recording, V2S.qc.evaluate(frames), status, current.index);
    }
    logEvent('take_aborted', { index: current.index, status, takeId: current.id });
    if (status === 'aborted_device' && deviceFailureActive) return;
    setFeedback(message, tone);
    if (status !== 'restarted') V2S.sounds.play('retry');
    enterReady();
  }

  // Moves on right away; storage happens in the background (see persistTake).
  function advance(current) {
    V2S.sounds.play('saved');
    const p = position(current.index);
    const wasRedo = Boolean(current.redo);
    lastAccepted = { index: current.index, fileName: current.fileName };
    redo = null;
    if (tutorialStep() < 3) ctx.progress.tutorialStep = tutorialStep() + 1;
    const allDone = current.index + 1 >= ctx.material.all.length;

    if (allDone) {
      stop();
      handlers.onAllDone && handlers.onAllDone();
      return;
    }
    if (!wasRedo && p.warmup && p.pos === p.total) {
      stop();
      handlers.onWarmupDone && handlers.onWarmupDone();
      return;
    }
    if (!wasRedo && !p.warmup && p.inBlock === p.blockSize) {
      stop();
      handlers.onBlockDone && handlers.onBlockDone({ block: p.block, blocks: p.blocks });
      return;
    }
    showJustSaved();
    enterReady();
  }

  function redoLast() {
    if (state !== 'ready' || !canRedoLast()) return;
    redo = { targetIndex: lastAccepted.index, returnIndex: index(), supersedes: lastAccepted.fileName };
    ctx.progress.currentIndex = lastAccepted.index;
    saveProgress();
    logEvent('redo_last', { targetIndex: redo.targetIndex });
    setFeedback(copy.feedback.redoLast, 'info');
    enterReady();
  }

  // ---- storage (serialised, in the background) ----
  function enqueue(job) {
    writeChain = writeChain.then(job).catch(error => {
      logEvent('write_failed', { error: String(error && error.message || error) });
    });
    return writeChain;
  }

  const snapshot = progress => JSON.parse(JSON.stringify(progress));

  function saveProgress() {
    const copyOfProgress = snapshot(ctx.progress);
    return enqueue(() => V2S.storage.saveParticipantProgress(copyOfProgress));
  }

  // Resolves once every take and progress change so far is stored.
  const flush = () => writeChain;

  // Checked in the background whenever the sentence is waiting, so a press never waits.
  // Only cached takes can be freed by saving, so a nearly full device blocks recording
  // only while there is something to save (otherwise saving could not help).
  async function refreshStorageGuard() {
    const estimate = await V2S.storage.storageEstimate();
    if (!estimate || !estimate.blocked) {
      storageBlocked = false;
      return;
    }
    await flush();
    storageBlocked = (await V2S.storage.countTakes()) > 0;
    logEvent('storage_near_full', { ratio: estimate.ratio, blocked: storageBlocked });
  }

  function uniqueName(fileName) {
    if (!usedNames.has(fileName)) {
      usedNames.add(fileName);
      return fileName;
    }
    const dot = fileName.lastIndexOf('.');
    for (let n = 2; ; n++) {
      const candidate = `${fileName.slice(0, dot)}_${n}${fileName.slice(dot)}`;
      if (!usedNames.has(candidate)) {
        usedNames.add(candidate);
        return candidate;
      }
    }
  }

  function relative(ms) {
    return Number.isFinite(ms) ? Math.round(ms - (performance.now() - sinceSessionStart())) : null;
  }

  function buildMetadata(current, recording, qc, status, takeNumber, fileName) {
    const p = position(current.index);
    const settings = V2S.media.getSettings();
    const usable = status === 'accepted' || status === 'qc_overridden';
    return {
      appVersion: cfg.APP_VERSION,
      uiVersion: 'next',
      materialCacheVersion: cfg.MATERIAL_VERSION,
      createdAt: new Date().toISOString(),
      fileName,
      sidecarFileName: fileName.replace(/\.[^.]+$/, '') + '.json',
      mimeType: recording.mimeType,
      fileExt: recording.ext,
      size: recording.blob.size,
      participantId: ctx.participantId,
      sessionId: V2S.util.getSessionId(),
      takeId: current.id,
      takeIndex: takeNumber,
      status,
      usable,
      sentenceSet: ctx.setKey,
      sentenceIndex: current.index,
      phase: p.warmup ? 'warmup' : 'formal',
      position: p.pos,
      total: p.total,
      blockIndex: p.warmup ? null : p.block,
      positionInBlock: p.warmup ? null : p.inBlock,
      sentence: current.sentence,
      redo: takeNumber > 1,
      supersedes: current.redo ? current.redo.supersedes : null,
      qcOverride: status === 'qc_overridden',
      requiresRetry: !usable,
      qc: { pass: qc.pass, code: qc.code, ...qc.metrics, rules: V2S.qc.rules() },
      audioQuality: {
        rms: qc.metrics.rms ?? null,
        peak: qc.metrics.peak ?? null,
        clippingRate: qc.metrics.clippingRate ?? null,
        speechMs: qc.metrics.speechMs ?? 0
      },
      markers: {
        unit: 'ms since session start',
        sentenceShown: relative(current.shownAt),
        startPress: relative(current.pressAt),
        recorderStart: current.recorder ? relative(current.recorder.startedAt) : null,
        stopPress: relative(current.stopAt),
        recorderStop: relative(current.recorderStoppedAt)
      },
      timing: { startCueLeadMs: cfg.START_CUE_LEAD_MS, tailMs: current.tailMs ?? null, holdMs: cfg.HOLD_MS },
      inputType: current.source,
      stopInputType: current.stopSource || null,
      session: { takesInSession: takesThisSession, msSinceSessionStart: sinceSessionStart() },
      quality: { videoBitsPerSecond: Number(settings.bitrate) },
      frameRate: { requested: Number(settings.fps) },
      resolution: settings.resolution,
      audioMode: settings.audioMode,
      audioConstraintMode: V2S.media.getAudioConstraintMode(),
      requestedConstraints: V2S.media.requestedConstraints(),
      recorderConfig: recording.recorderConfig || null,
      mediaAtSave: V2S.media.snapshot(),
      browser: { userAgent: navigator.userAgent, platform: navigator.platform || '', language: navigator.language || '' },
      saveMode: V2S.exporter.getSaveMode()
    };
  }

  // Names the take now (so Redo last can refer to it) and stores it — together with
  // the progress it causes — in one background transaction.
  function persistTake(current, recording, qc, status, nextIndex) {
    takesThisSession += 1;
    const counts = ctx.progress.takeCounts;
    const takeNumber = (counts[current.index] || 0) + 1;
    counts[current.index] = takeNumber;
    const p = position(current.index);
    const repeat = (ctx.progress.repetitionCount || 0) + 1;
    const progressInfo = p.warmup ? `_warmup${p.pos}-${p.total}_repeat${repeat}` : `_${p.pos}-${p.total}_repeat${repeat}`;
    const fileName = uniqueName(`${sanitize(current.sentence)}${progressInfo}_${timestamp()}${takeNumber > 1 ? '_redo' : ''}.${recording.ext}`);
    current.fileName = fileName;
    const metadata = buildMetadata(current, recording, qc, status, takeNumber, fileName);

    if (nextIndex >= ctx.material.all.length) {
      ctx.progress.currentIndex = ctx.material.all.length - 1;
      ctx.progress.completed = true;
      ctx.progress.completedAt = new Date().toISOString();
    } else {
      ctx.progress.currentIndex = nextIndex;
    }
    const progressSnapshot = snapshot(ctx.progress);

    return enqueue(async () => {
      const record = {
        fileName,
        arrayBuffer: await recording.blob.arrayBuffer(),
        mimeType: recording.mimeType,
        sentence: current.sentence,
        sentenceSet: ctx.setKey,
        sentenceIndex: current.index,
        timestamp: new Date().toISOString(),
        size: recording.blob.size,
        metadata,
        participantId: ctx.participantId,
        status,
        takeId: current.id
      };
      try {
        const id = await V2S.storage.commitTake(record, progressSnapshot);
        logEvent('take_saved', { index: current.index, status, fileName, qc: qc.code, speechMs: qc.metrics.speechMs });
        V2S.exporter.queueFolderWrite(id, record, recording.blob);
      } catch (error) {
        // Storage failed: hand the file straight to the person rather than lose it.
        logEvent('take_store_failed', { fileName, error: String(error && error.message || error) });
        await V2S.storage.saveParticipantProgress(progressSnapshot).catch(() => {});
        V2S.exporter.rescueTake(recording.blob, fileName, metadata);
      }
    });
  }

  // ---- device problems ----
  async function onDeviceFailure(code) {
    if (deviceFailureActive || state === 'idle') return;
    deviceFailureActive = true;
    logEvent('session_device_failure', { code, state });
    if (take && !take.closed) await abortTake('aborted_device', null, 'warn', take);
    stop();
    if (handlers.onDeviceError) handlers.onDeviceError(code);
  }

  function resumeAfterReconnect() {
    deviceFailureActive = false;
    setFeedback(null);
    enterReady();
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden && take && !take.closed && (state === 'recording' || state === 'finishing')) {
      abortTake('aborted_device', copy.feedback.hidden);
    }
  });

  return {
    configure,
    begin,
    stop,
    getState,
    getContext,
    position,
    onPrimary,
    onSecondary,
    onHold,
    onDeviceFailure,
    resumeAfterReconnect,
    enterReady,
    flush,
    refreshStorage: refreshStorageGuard
  };
})();
