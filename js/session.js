// The recording state machine.
//   ready → recording → finishing (fixed tail) → checking → next sentence (ready)
//                                                        ↘ same sentence (ready)
// Every failure path (held press, no speech, too loud, timeout, device problem,
// page hidden, reload) returns to the SAME sentence: progress only moves forward
// when a take is accepted or the person chooses "Keep it and continue".
window.V2S = window.V2S || {};

V2S.session = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const { logEvent, sanitize, timestamp, uid, sinceSessionStart, sleep } = V2S.util;

  let ctx = null;            // { participantId, setKey, material, progress }
  let state = 'idle';
  let take = null;
  let feedback = null;       // { text, tone, transient }
  let lastAccepted = null;   // { index, fileName } accepted during this session
  let redo = null;           // { targetIndex, returnIndex, supersedes }
  let qcFailures = { index: null, count: 0 };
  let sentenceShownAt = 0;
  let takesThisSession = 0;
  let idleHintTimer = null;
  let deviceFailureActive = false;
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

  function progressText(p) {
    if (p.warmup) {
      return { main: copy.record.warmupOf(p.pos, p.total), sub: copy.record.warmupLead, fraction: (p.pos - 1) / p.total };
    }
    const remaining = p.blockSize - p.inBlock + 1;
    const untilBreak = remaining === 1 ? copy.record.lastInBlock : copy.record.untilBreak(remaining);
    return {
      main: copy.record.sentenceOf(p.inBlock, p.blockSize),
      sub: `${copy.record.blockOf(p.block, p.blocks)} · ${untilBreak}`,
      fraction: (p.inBlock - 1) / p.blockSize
    };
  }

  function coachText(phase) {
    const done = ctx.progress.tutorialTakes || 0;
    if (done >= cfg.TUTORIAL_TAKES) return null;
    if (phase === 'ready') return done === 0 ? copy.tutorial.readyFirst : copy.tutorial.readySecond;
    if (phase === 'recording') return done === 0 ? copy.tutorial.recordingFirst : copy.tutorial.recordingSecond;
    return null;
  }

  function canRedoLast() {
    return state === 'ready' && !redo && lastAccepted !== null && lastAccepted.index === index() - 1;
  }

  function baseView() {
    const i = index();
    const text = progressText(position(i));
    return { sentence: ctx.material.all[i], progressMain: text.main, progressSub: text.sub, progress: text.fraction };
  }

  function readyView() {
    return {
      ...baseView(),
      state: 'ready',
      status: copy.record.statusReady,
      primary: { label: copy.record.start, icon: 'rec', disabled: false },
      secondary: { label: copy.record.redoLast, icon: 'undo', hidden: !canRedoLast(), disabled: !canRedoLast() },
      coach: coachText('ready'),
      feedback,
      showFinish: true
    };
  }

  function recordingView() {
    return {
      ...baseView(),
      state: 'recording',
      status: copy.record.statusRecording,
      primary: { label: copy.record.stop, icon: 'stop', disabled: false },
      secondary: { label: copy.record.startOver, icon: 'restart', hidden: false, disabled: false },
      coach: coachText('recording'),
      feedback: null,
      showFinish: false
    };
  }

  function busyView(phase) {
    return {
      ...baseView(),
      state: phase,
      status: copy.record.statusSaving,
      primary: { label: copy.record.saving, icon: 'spinner', disabled: true },
      secondary: { label: copy.record.startOver, icon: 'restart', hidden: true, disabled: true },
      coach: null,
      feedback: null,
      showFinish: false
    };
  }

  function savedView() {
    return { ...busyView('saved'), status: copy.record.statusSaved };
  }

  function setFeedback(text, tone = 'warn', transient = false) {
    clearTimeout(idleHintTimer);
    feedback = text ? { text, tone, transient, setAt: performance.now() } : null;
  }

  // ---- lifecycle ----
  async function begin({ participantId, setKey, material, progress }) {
    ctx = { participantId, setKey, material, progress };
    if (!ctx.progress.takeCounts) ctx.progress.takeCounts = {};
    lastAccepted = null;
    redo = null;
    feedback = null;
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
    clearTimeout(idleHintTimer);
  }

  function enterReady() {
    state = 'ready';
    take = null;
    sentenceShownAt = performance.now();
    V2S.meter.setIdleDetection(true, onIdleSpeech);
    V2S.ui.renderRecord(readyView());
    logEvent('ready', { index: index() });
    refreshStorageGuard().catch(() => {});
  }

  // Speaking before Start: a gentle reminder that nothing is being recorded.
  function onIdleSpeech() {
    if (state !== 'ready') return;
    // Leave a fresh message (e.g. "Please tap, don't hold") up long enough to be read.
    if (feedback && !feedback.transient && performance.now() - feedback.setAt < 4000) return;
    setFeedback(copy.feedback.speechBeforeStart, 'info', true);
    V2S.ui.renderRecord({ feedback });
    logEvent('speech_before_start', { index: index() });
    idleHintTimer = setTimeout(() => {
      if (state === 'ready' && feedback && feedback.transient) {
        feedback = null;
        V2S.ui.renderRecord({ feedback: null });
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
      V2S.ui.renderRecord({ feedback });
    }
    // While finishing, finalize() sees the hold through waitForRelease() and aborts.
  }

  // The press must turn the card red at once, so nothing here waits on async work;
  // the storage check runs ahead of time (see refreshStorageGuard).
  function startTake(source) {
    if (state !== 'ready' || deviceFailureActive) return;
    if (storageBlocked) {
      logEvent('storage_blocked', {});
      setFeedback(copy.feedback.storageFull, 'warn');
      V2S.ui.renderRecord({ feedback });
      if (handlers.onStorageFull) handlers.onStorageFull();
      return;
    }
    state = 'recording';
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
    V2S.ui.renderRecord(recordingView());
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
    V2S.ui.renderRecord(busyView('finishing'));
    logEvent('take_stop', { index: current.index, source, takeId: current.id });
    setTimeout(() => finalize(current), cfg.TAIL_MS);
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
    V2S.ui.renderRecord(busyView('checking'));
    const { recording, frames } = await closeRecorder(current);
    if (!recording || !recording.blob || !recording.blob.size) {
      logEvent('take_empty', { index: current.index });
      setFeedback(copy.feedback.device, 'warn');
      enterReady();
      return;
    }
    const qc = V2S.qc.evaluate(frames);

    if (qc.pass) {
      await persistTake(current, recording, qc, 'accepted');
      qcFailures = { index: null, count: 0 };
      await acceptAndAdvance(current);
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
        await persistTake(current, recording, qc, 'qc_overridden');
        qcFailures = { index: null, count: 0 };
        await acceptAndAdvance(current);
        return;
      }
    }

    await persistTake(current, recording, qc, 'qc_failed');
    setFeedback(reason, 'warn');
    enterReady();
  }

  // Ends the current take without accepting it. The take is still saved (marked with
  // its status) and the same sentence comes back.
  async function abortTake(status, message, tone = 'warn', current = take) {
    if (!current || current.closed) return;
    current.closed = true;
    state = 'checking';
    V2S.ui.renderRecord(busyView('checking'));
    const { recording, frames } = await closeRecorder(current);
    if (recording && recording.blob && recording.blob.size) {
      await persistTake(current, recording, V2S.qc.evaluate(frames), status);
    }
    logEvent('take_aborted', { index: current.index, status, takeId: current.id });
    if (status === 'aborted_device' && deviceFailureActive) return;
    setFeedback(message, tone);
    if (status !== 'restarted') V2S.sounds.play('retry');
    enterReady();
  }

  async function acceptAndAdvance(current) {
    V2S.sounds.play('saved');
    const p = position(current.index);
    const wasRedo = Boolean(current.redo);
    lastAccepted = { index: current.index, fileName: current.fileName };
    redo = null;
    if ((ctx.progress.tutorialTakes || 0) < cfg.TUTORIAL_TAKES) ctx.progress.tutorialTakes = (ctx.progress.tutorialTakes || 0) + 1;

    state = 'saved';
    V2S.ui.renderRecord(savedView());

    const next = current.index + 1;
    const allDone = next >= ctx.material.all.length;
    if (allDone) {
      ctx.progress.currentIndex = ctx.material.all.length - 1;
      ctx.progress.completed = true;
      ctx.progress.completedAt = new Date().toISOString();
    } else {
      ctx.progress.currentIndex = next;
    }
    await saveProgress();
    await sleep(cfg.SAVED_FLASH_MS);

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
    enterReady();
  }

  async function redoLast() {
    if (!canRedoLast()) return;
    redo = { targetIndex: lastAccepted.index, returnIndex: index(), supersedes: lastAccepted.fileName };
    ctx.progress.currentIndex = lastAccepted.index;
    await saveProgress();
    logEvent('redo_last', { targetIndex: redo.targetIndex });
    setFeedback(copy.feedback.redoLast, 'info');
    enterReady();
  }

  // ---- storage ----
  async function saveProgress() {
    try {
      await V2S.storage.saveParticipantProgress(ctx.progress);
    } catch (error) {
      logEvent('progress_save_failed', { error: String(error) });
    }
  }

  // Checked in the background whenever the sentence is waiting, so a press never waits.
  // Only cached takes can be freed by saving, so a nearly full device blocks recording
  // only while there is something to save (otherwise saving could not help).
  let storageBlocked = false;
  async function refreshStorageGuard() {
    const estimate = await V2S.storage.storageEstimate();
    if (!estimate || !estimate.blocked) {
      storageBlocked = false;
      return;
    }
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
      timing: { startCueLeadMs: cfg.START_CUE_LEAD_MS, tailMs: cfg.TAIL_MS, holdMs: cfg.HOLD_MS },
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

  async function persistTake(current, recording, qc, status) {
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
      const id = await V2S.storage.addTake(record);
      await saveProgress();
      V2S.exporter.queueFolderWrite(id, record, recording.blob);
      logEvent('take_saved', { index: current.index, status, fileName, qc: qc.code, speechMs: qc.metrics.speechMs });
    } catch (error) {
      // Storage failed: hand the file straight to the person rather than lose it.
      logEvent('take_store_failed', { fileName, error: String(error && error.message || error) });
      V2S.util.downloadBlob(recording.blob, fileName);
      V2S.util.downloadBlob(new Blob([JSON.stringify(metadata, null, 2)], { type: 'application/json' }), metadata.sidecarFileName);
    }
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
    refreshStorage: refreshStorageGuard
  };
})();
