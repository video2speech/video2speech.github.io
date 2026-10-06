// The recording state machine.
//   ready → starting (start sound, recorder proves it runs) → recording (sentence green)
//         → finishing (fixed tail) → checking → next sentence (ready)
//                                              ↘ same sentence (ready)
// Every failure path (held press, no speech, too loud, recorder failure, timeout, device
// problem, page hidden, reload) returns to the SAME sentence: progress only moves forward
// when a take is accepted or the participant chooses "Keep it and go on".
// A take and the progress it causes are written in ONE IndexedDB transaction, in order,
// in the background — the screen never waits for storage.
window.V2S = window.V2S || {};

V2S.session = (() => {
  const cfg = V2S.config;
  const copy = V2S.copy;
  const { logEvent, sanitize, timestamp, uid, sinceSessionStart, sleep } = V2S.util;

  let ctx = null;            // { participantId, setKey, material, progress }
  let state = 'idle';
  let take = null;
  let feedback = null;       // { text, tone, transient, setAt }
  let lastAccepted = null;   // { index, fileName, sentence } — the sentence Redo would record again
  let redo = null;           // { targetIndex, returnIndex, partEnd } — also kept in progress.pendingRedo
  let redoLesson = 'pending';  // practice: 'pending' → 'redoing' → 'done'
  let justRecorded = false;    // practice: the last thing that happened was a recorded take
  let lessonJustDone = false;  // practice: the Redo lesson was just completed (said once)
  let partEnd = null;          // { kind: 'practice' | 'part' | 'all', block, blocks } after a part's last sentence
  let holdTipNext = false;     // a held Stop press: say so (gently) on the next sentence
  let storeFailedAt = null;    // a take that could not be stored: go back to that sentence
  let storeFailures = 0;       // in a row
  let quotaHit = false;        // the last write failed because the device was full
  let roomFromLatest = false;  // full, and only the most recent ZIP's copies could make room
  let qcFailures = { index: null, count: 0 };
  let consecutiveStartFailures = 0;
  let sentenceShownAt = 0;
  let takesThisSession = 0;
  let idleHintTimer = null;
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
    if (i < warmupCount) return { warmup: true, pos: i + 1, total: warmupCount, part: 0 };
    const formal = i - warmupCount;
    const block = Math.floor(formal / cfg.BLOCK_SIZE);
    const blockStart = block * cfg.BLOCK_SIZE;
    const blockSize = Math.min(cfg.BLOCK_SIZE, formalCount - blockStart);
    return {
      warmup: false,
      pos: formal + 1,
      total: formalCount,
      part: block + 1,
      block: block + 1,
      blocks: Math.ceil(formalCount / cfg.BLOCK_SIZE),
      inBlock: formal - blockStart + 1,
      blockSize
    };
  }

  function whereView(i) {
    const p = position(i);
    if (p.warmup) return { main: copy.record.practiceOf(p.pos, p.total), progress: (p.pos - 1) / p.total };
    return {
      main: `${copy.record.partOf(p.block, p.blocks)} · ${copy.record.sentenceOf(p.inBlock, p.blockSize)}`,
      short: copy.record.whereShort(p.block, p.inBlock, p.blockSize),
      progress: (p.inBlock - 1) / p.blockSize
    };
  }

  // ---- practice coaching (first session only) ----
  const coaching = () => Boolean(ctx) && !ctx.progress.coachDone
    && (index() < ctx.material.warmupCount || (state === 'partEnd' && partEnd && partEnd.kind === 'practice'));

  // Redo reaches only the sentence just recorded, within the same part (at a part's end,
  // before the break, its last sentence can still be redone).
  function canRedo() {
    if (redo || !lastAccepted) return false;
    if (state === 'partEnd') return true;
    if (state !== 'ready' || lastAccepted.index !== index() - 1) return false;
    return position(lastAccepted.index).part === position(index()).part;
  }

  const redoPending = () => Boolean(redo && redo.targetIndex === index());

  // On a computer the instructions name the keys (Space, ←); on touch, the buttons.
  const usesKeys = () => document.documentElement.classList.contains('has-keyboard');

  const MORE = { 2: 'Two', 3: 'Three', 4: 'Four' };

  // The practice coach for this moment (docs/recorder-design.md, principle 5): `ack` says
  // what just happened, `action` is the ONE thing to do now (target = the control it
  // names, which pulses), `detail` rarely says why. A problem replaces the ack; the action
  // then says what to do about it. Never two instructions that disagree.
  function coachView(phase) {
    if (!coaching()) return null;
    const k = usesKeys();
    const c = copy.coach;
    if (phase === 'partEnd') return { ack: { text: c.lastPractice, tone: 'plain' }, action: c.pressContinue(k), target: 'main' };
    // Starting, recording, finishing: the same line all through, so nothing flickers; no
    // control pulses while someone reads.
    if (phase !== 'ready') return { ack: null, action: c.readNow(k), target: null };
    const p = index();
    let view;
    if (redoPending()) {
      view = { ack: { text: c.backToLast, tone: 'info' }, action: c.startAgain(k), target: 'main' };
    } else if (lessonJustDone) {
      view = { ack: { text: c.redoDone, tone: 'ok' }, action: c.carryOn(k), target: 'main' };
    } else if ((p === 2 || p === 3) && redoLesson !== 'done' && canRedo()) {
      // The Redo lesson says first that it is a lesson (nothing went wrong), then what
      // to press, then what Redo is for.
      view = { ack: { text: c.redoLesson, tone: 'plain' }, action: c.tryRedo(k), detail: c.redoWhat(), target: 'redo', quietMain: true };
    } else if (p === 0) {
      view = { ack: null, action: c.pressStart(k), detail: c.noHold, target: 'main' };
    } else if (p === 1) {
      view = { ack: justRecorded ? { text: c.recordedFirst, tone: 'ok' } : null, action: c.nextSentence(k), target: 'main' };
    } else {
      const left = ctx.material.warmupCount - p;
      view = { ack: null, action: left === 1 ? c.lastOne(k) : c.more(MORE[left] || String(left), k), target: 'main' };
    }
    if (feedback) {
      const text = copy.feedbackShort[feedback.key] || feedback.text;
      view.ack = { text, tone: feedback.tone === 'warn' ? 'warn' : 'info' };
      // After a failed take the same sentence comes back: say so (unless it is a hint
      // about speaking before Start, where the action already says what to press).
      const hint = feedback.key === 'speechBeforeStart';
      if (feedback.tone === 'warn' && !hint && view.target === 'main' && !redoPending()) view.action = c.startAgain(k);
    }
    return view;
  }

  // ---- views ----
  // Formal recording is quiet: the message line is only for something that needs fixing
  // (in practice the coach says it instead). A take that went fine shows nothing: the
  // next sentence appearing is the confirmation.
  function messageView() {
    if (coaching()) return null;
    if (feedback) return { text: feedback.text, tone: feedback.tone };
    return null;
  }

  function pulseFor(coach, redoVisible) {
    if (!coach || !coach.target) return null;
    if (coach.target === 'redo') return redoVisible ? 'redo' : null;
    return 'main';
  }

  // Waiting: the grey sentence in its card and the green Start; Redo (top left) names the
  // sentence it would record again. No status text: nothing needs doing but Start.
  function readyView() {
    const coach = coachView('ready');
    let redoView = { visible: false };
    if (redoPending()) {
      redoView = { visible: true, cancel: true, label: copy.record.cancelRedo, caption: '' };
    } else if (canRedo()) {
      redoView = { visible: true, label: copy.record.redo, caption: copy.record.redoCaption(lastAccepted.sentence) };
    }
    return {
      state: 'ready',
      saved: false,
      status: '',
      sentence: ctx.material.all[index()],
      where: whereView(index()),
      main: { label: copy.record.start, icon: 'go', disabled: false, quiet: Boolean(coach && coach.quietMain) },
      redo: redoView,
      message: messageView(),
      coach,
      pulse: pulseFor(coach, redoView.visible)
    };
  }

  // After a part's last sentence: that sentence stays on screen ("Saved"), Redo is still
  // possible, and one button goes on to the break (or practice done / the end).
  function partEndView() {
    const coach = coachView('partEnd');
    const kind = partEnd.kind;
    return {
      state: 'ready',
      saved: false,
      status: '',
      sentence: lastAccepted.sentence,
      where: { ...whereView(lastAccepted.index), progress: 1 },
      main: { label: kind === 'practice' ? copy.record.toPracticeDone : kind === 'all' ? copy.record.toAllDone : copy.record.toBreak(partEnd.block), icon: 'next', disabled: false },
      redo: { visible: true, label: copy.record.redo, caption: copy.record.redoThis },
      message: coach ? null : { text: kind === 'part' ? copy.record.partEndPart(partEnd.block) : copy.record.partEndAll, tone: 'note' },
      coach,
      pulse: pulseFor(coach, true)
    };
  }

  function startingView() {
    return {
      state: 'starting',
      saved: false,
      status: '',
      sentence: ctx.material.all[index()],
      where: whereView(index()),
      main: { label: copy.record.starting, icon: 'busy', disabled: true },
      redo: { visible: false },
      message: null,
      coach: coachView('starting'),
      pulse: null
    };
  }

  // Recording: the sentence turns green (CSS), Stop is offered. Nothing else appears; on a
  // long take (a forgotten Stop) the clock shows and Stop pulses, away from the sentence.
  function recordingView() {
    const coach = coachView('recording');
    return {
      state: 'recording',
      saved: false,
      status: copy.record.recordingSign,
      sentence: ctx.material.all[index()],
      where: whereView(index()),
      main: { label: copy.record.stop, icon: 'stop', disabled: false },
      redo: { visible: false },
      message: null,
      coach,
      // Nothing moves while someone reads (the coach line already says "then press
      // Stop"); only a long take (a forgotten Stop) makes Stop pulse.
      pulse: take && take.longTake ? 'main' : null,
      liveSince: take && take.readNowAt ? take.readNowAt : performance.now()
    };
  }

  function busyView(phase) {
    return {
      state: phase,
      saved: false,
      status: '',
      sentence: ctx.material.all[index()],
      where: whereView(index()),
      main: { label: copy.record.saving, icon: 'busy', disabled: true },
      redo: { visible: false },
      message: null,
      coach: coachView('busy'),
      pulse: null
    };
  }

  function render(view) {
    V2S.meter.setLive(view.state === 'recording');
    V2S.ui.renderRecord(view);
  }

  // key: a message in copy.feedback (or copy.record); null clears.
  // A message's words; on a computer they name the keys (Space, ←) instead of the buttons.
  function feedbackText(key) {
    const entry = key ? copy.feedback[key] || copy.record[key] || '' : '';
    return typeof entry === 'function' ? entry(usesKeys()) : entry;
  }

  function setFeedback(key, tone = 'warn', transient = false) {
    clearTimeout(idleHintTimer);
    const text = feedbackText(key);
    feedback = key ? { key, text, tone, transient, setAt: performance.now() } : null;
  }

  // ---- lifecycle ----
  function begin({ participantId, setKey, material, progress }) {
    ctx = { participantId, setKey, material, progress };
    if (!ctx.progress.takeCounts) ctx.progress.takeCounts = {};
    lastAccepted = null;
    redo = null;
    redoLesson = 'pending';
    justRecorded = false;
    lessonJustDone = false;
    partEnd = null;
    holdTipNext = false;
    storeFailedAt = null;
    storeFailures = 0;
    quotaHit = false;
    feedback = null;
    if (!ctx.progress.usable) ctx.progress.usable = {};
    ctx.progress.round = V2S.storage.roundOf(ctx.progress);
    // A Redo that was under way (reload, End for today) carries on.
    const pending = ctx.progress.pendingRedo;
    if (pending && pending.targetIndex === ctx.progress.currentIndex) {
      redo = { targetIndex: pending.targetIndex, returnIndex: pending.returnIndex, partEnd: pending.partEnd || null };
      lastAccepted = { index: pending.targetIndex, fileName: (ctx.progress.usable[pending.targetIndex] || {}).fileName || null, sentence: material.all[pending.targetIndex] };
      if (!coaching()) setFeedback('redoing', 'info');
    } else if (pending) {
      delete ctx.progress.pendingRedo;
    }
    qcFailures = { index: null, count: 0 };
    consecutiveStartFailures = 0;
    deviceFailureActive = false;
    V2S.ui.fitSentences(material.all);
    logEvent('session_begin', { participantId, setKey, index: progress.currentIndex, coaching: coaching() });
    enterReady();
  }

  function stop() {
    state = 'idle';
    if (take) {
      clearTimeout(take.startTimer);
      clearTimeout(take.maxTimer);
      clearTimeout(take.longTimer);
    }
    take = null;
    V2S.meter.setIdleDetection(false);
    V2S.meter.setLive(false);
    clearTimeout(idleHintTimer);
    V2S.ui.setRecording(false);
  }

  function enterPartEnd(info) {
    state = 'partEnd';
    partEnd = info;
    take = null;
    V2S.input.guard();   // Start has just become Continue: not the second press of Stop
    V2S.meter.setIdleDetection(false);
    render(partEndView());
    logEvent('part_end', { kind: info.kind, index: lastAccepted && lastAccepted.index });
  }

  function leavePartEnd() {
    const info = partEnd;
    partEnd = null;
    lastAccepted = null;  // Redo never reaches back into a finished part
    stop();
    if (info.kind === 'practice') {
      ctx.progress.coachDone = true;
      if (Number.isInteger(ctx.progress.resumeIndex)) {
        ctx.progress.currentIndex = ctx.progress.resumeIndex;
        delete ctx.progress.resumeIndex;
      }
      saveProgress();
      if (handlers.onWarmupDone) handlers.onWarmupDone();
    } else if (info.kind === 'all') {
      if (handlers.onAllDone) handlers.onAllDone();
    } else if (handlers.onBlockDone) {
      handlers.onBlockDone({ block: info.block, blocks: info.blocks });
    }
  }

  function enterReady() {
    if (storeFailedAt !== null) return backToUnstored();
    state = 'ready';
    take = null;
    sentenceShownAt = performance.now();
    // People often say a word after Stop ("oops", or the end of the sentence): only speech
    // that starts a moment later counts as reading before Start.
    V2S.meter.setIdleDetection(true, onIdleSpeech, cfg.IDLE_SPEECH_GRACE_MS);
    render(readyView());
    logEvent('ready', { index: index() });
    refreshStorageGuard().catch(() => {});
  }

  // Speaking before Start: a gentle reminder that nothing is being recorded.
  function onIdleSpeech() {
    if (state !== 'ready' || V2S.ui.isOverlayOpen()) return;
    // Leave a fresh message (e.g. the hold message) up long enough to be read.
    if (feedback && !feedback.transient && performance.now() - feedback.setAt < 4000) return;
    // The Redo lesson keeps its three lines: reading the new sentence aloud there is not
    // a mistake to point out (the lesson asks for Redo; nothing went wrong).
    const lesson = coachView('ready');
    if (lesson && lesson.target === 'redo') return;
    setFeedback('speechBeforeStart', 'warn', true);
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
  // A double press acts once: the press that would undo the one just made (Stop right
  // after Start, cancelling a Redo just made) counts only after REVERSE_GUARD_MS. Other
  // presses (Start after Stop, Start after Redo) count at once.
  const tooSoon = since => Number.isFinite(since) && performance.now() - since < cfg.REVERSE_GUARD_MS;

  function onPrimary({ source }) {
    if (state === 'ready') startTake(source);
    else if (state === 'recording') {
      if (take && tooSoon(take.pressAt)) {
        logEvent('press_ignored', { reason: 'stop_too_soon', index: take.index });
        return;
      }
      stopTake(source);
    }
    else if (state === 'partEnd') leavePartEnd();
    // starting / finishing / checking: the press is ignored (the button shows it is busy).
  }

  function onSecondary() {
    if (state === 'ready' && redoPending()) {
      if (tooSoon(redo.pressedAt)) {
        logEvent('press_ignored', { reason: 'cancel_too_soon' });
        return;
      }
      cancelRedo();
    }
    else if (state === 'ready' || state === 'partEnd') redoLast();
  }

  // A held button is the push-to-talk habit: the take is thrown away and a short dialog
  // explains "press once, then let go". The same sentence comes back.
  // Only the press that STARTS a take is treated this way: a slow release of Stop is not
  // push-to-talk, so that recording is kept (finalize) and a gentle tip follows.
  async function onHold(press = {}) {
    if (press.kind === 'secondary') return;
    if (state === 'starting' || state === 'recording') {
      await abortTake('aborted_hold', null);
      explainHold(copy.holdDialog.bodyDiscarded(usesKeys()));
    } else if (state === 'ready') {
      explainHold(copy.holdDialog.body(usesKeys()));
    }
  }

  async function explainHold(body) {
    logEvent('hold_explained', { index: ctx ? index() : null });
    await V2S.ui.dialog({
      title: copy.holdDialog.title,
      body,
      actions: [{ label: copy.holdDialog.ok, value: true, variant: 'go', default: true }],
      dismissValue: true
    });
    if (state === 'ready') {
      setFeedback('afterHold', 'info');
      render(readyView());
    }
  }

  // The press must answer at once, so nothing here waits on async work.
  function startTake(source) {
    if (state !== 'ready' || deviceFailureActive) return;
    if (storageBlocked) {
      logEvent('storage_blocked', {});
      setFeedback('storageFull', 'warn');
      render(readyView());
      if (handlers.onStorageFull) handlers.onStorageFull();
      return;
    }
    state = 'starting';
    justRecorded = false;
    lessonJustDone = false;
    // The press is a user gesture: wake the audio analysis if iOS paused it.
    V2S.meter.resume();
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
      attempts: 0,
      startErrors: [],
      redo: redo && redo.targetIndex === i ? { ...redo } : null
    };
    take = current;
    setFeedback(null);
    V2S.meter.setIdleDetection(false);
    render(startingView());
    // A short cue, then recording at once (about 0.1 s after the press, before anyone can
    // start speaking); no cue where the device's sound output is too slow for that. The
    // sentence turns green as soon as the recorder runs.
    current.cueLeadMs = V2S.sounds.startCue();
    logEvent('take_start', { index: i, source, takeId: current.id, cueLeadMs: current.cueLeadMs });
    if (current.cueLeadMs) current.startTimer = setTimeout(() => launchRecorder(current), current.cueLeadMs);
    else launchRecorder(current);
  }

  // Starts the recorder and waits until it has proven it runs. Start failures are retried
  // silently with a new recorder; only if every try fails is the participant told.
  async function launchRecorder(current) {
    if (current.closed || take !== current) return;
    current.attempts += 1;
    let handle;
    try {
      V2S.meter.beginCollect();
      handle = V2S.media.startRecorder({ skip: current.attempts >= cfg.START_ATTEMPTS ? 1 : 0 });
    } catch (error) {
      logEvent('recorder_start_failed', { error: String(error && error.message || error) });
      onDeviceFailure('recorder_start_failed');
      return;
    }
    current.recorder = handle;
    const result = await handle.ready;
    if (current.closed || take !== current) {
      if (!result.ok) handle.stop().catch(() => {});
      return;
    }
    if (!result.ok) {
      current.startErrors.push(result.error);
      logEvent('recorder_restart', { index: current.index, attempt: current.attempts, error: result.error });
      current.recorder = null;
      handle.stop().catch(() => {});
      V2S.meter.endCollect();
      if (current.attempts < cfg.START_ATTEMPTS) {
        current.startTimer = setTimeout(() => launchRecorder(current), 150);
        return;
      }
      current.closed = true;
      take = null;
      consecutiveStartFailures += 1;
      logEvent('recorder_gave_up', { index: current.index, errors: current.startErrors, consecutive: consecutiveStartFailures });
      setFeedback('startFailed', 'warn');
      V2S.sounds.play('retry');
      enterReady();
      if (consecutiveStartFailures >= 2 && handlers.onStartFailure) handlers.onStartFailure();
      return;
    }
    consecutiveStartFailures = 0;
    handle.onError = () => {
      if (!current.closed && take === current) abortTake('aborted_device', 'stoppedEarly', 'warn', current);
    };
    state = 'recording';
    current.readNowAt = performance.now();
    current.mediaAtStart = V2S.media.snapshot();
    render(recordingView());
    V2S.media.startMonitor();
    current.longTimer = setTimeout(() => {
      if (!current.closed && take === current && state === 'recording') {
        current.longTake = true;
        render(recordingView());
        logEvent('long_take_reminder', { index: current.index });
      }
    }, cfg.TIMER_SHOW_AFTER_MS);
    current.maxTimer = setTimeout(() => {
      if (!current.closed && take === current && state === 'recording') {
        abortTake('aborted_timeout', 'timeout');
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
    clearTimeout(current.longTimer);
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
    clearTimeout(current.longTimer);
    V2S.media.stopMonitor();
    let recording = null;
    if (current.recorder) {
      try {
        recording = await Promise.race([current.recorder.stop(), sleep(3000).then(() => null)]);
        if (!recording) logEvent('recorder_stop_timeout', { index: current.index });
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
    current.heldStop = release === 'hold';
    current.closed = true;
    state = 'checking';
    render(busyView('checking'));
    const { recording, frames } = await closeRecorder(current);
    if (!recording || !recording.blob || !recording.blob.size) {
      logEvent('take_empty', { index: current.index, error: recording && recording.error });
      setFeedback('stoppedEarly', 'warn');
      V2S.sounds.play('retry');
      enterReady();
      return;
    }
    const qc = V2S.qc.evaluate(frames);

    if (qc.pass) {
      persistTake(current, recording, qc, 'accepted', current.index + 1);
      qcFailures = { index: null, count: 0 };
      if (current.heldStop) holdTipNext = true;
      advance(current);
      return;
    }

    if (qcFailures.index !== current.index) qcFailures = { index: current.index, count: 0 };
    qcFailures.count += 1;
    V2S.sounds.play('retry');
    logEvent('qc_failed', { index: current.index, code: qc.code, failures: qcFailures.count, speechMs: qc.metrics.speechMs });

    if (qcFailures.count >= cfg.QC.OVERRIDE_AFTER_FAILURES) {
      const choice = await V2S.ui.dialog({
        title: copy.keepDialog.title,
        body: copy.keepDialog.body(copy.keepDialog.reasons[qc.code] || copy.keepDialog.reasons.no_speech),
        actions: [
          { label: copy.keepDialog.retry, value: 'retry', variant: 'go', default: true },
          { label: copy.keepDialog.keep, value: 'keep', variant: 'ghost' }
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
    setFeedback(copy.feedback[qc.code] ? qc.code : 'no_speech', 'warn');
    enterReady();
  }

  // Ends the current take without accepting it. Whatever was recorded is still saved
  // (marked with its status, into not_used/) and the same sentence comes back.
  async function abortTake(status, messageKey, tone = 'warn', current = take) {
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
    setFeedback(messageKey, tone);
    V2S.sounds.play('retry');
    enterReady();
  }

  // Moves on right away; storage happens in the background (see persistTake). The last
  // sentence of a part (also after a Redo of it) pauses on the part-end view.
  function advance(current) {
    V2S.sounds.play('saved');
    const p = position(current.index);
    const wasRedo = Boolean(current.redo);
    lastAccepted = { index: current.index, fileName: current.fileName, sentence: current.sentence };
    justRecorded = true;
    if (wasRedo && redoLesson === 'redoing') {
      redoLesson = 'done';
      lessonJustDone = true;
    }
    redo = null;
    if (wasRedo) {
      delete ctx.progress.pendingRedo;
      saveProgress();
    }
    const last = current.index + 1 >= ctx.material.all.length;
    const tip = holdTipNext;
    holdTipNext = false;
    if (last) return enterPartEnd({ kind: 'all' });
    if (p.warmup && p.pos === p.total) return enterPartEnd({ kind: 'practice' });
    if (!p.warmup && p.inBlock === p.blockSize) return enterPartEnd({ kind: 'part', block: p.block, blocks: p.blocks });
    if (tip) setFeedback('holdTip', 'info', true);
    enterReady();
  }

  function redoLast() {
    if (!canRedo()) return;
    const fromPartEnd = state === 'partEnd';
    redo = { targetIndex: lastAccepted.index, returnIndex: index(), partEnd: fromPartEnd ? partEnd : null, pressedAt: performance.now() };
    // After the very last sentence: not "all done" while its Redo is pending, so a reload
    // or End for today comes back to it.
    if (fromPartEnd && partEnd.kind === 'all') Object.assign(ctx.progress, { completed: false, completedAt: null });
    partEnd = null;
    if (coaching() && redoLesson === 'pending') redoLesson = 'redoing';
    justRecorded = false;
    lessonJustDone = false;
    ctx.progress.pendingRedo = { targetIndex: redo.targetIndex, returnIndex: redo.returnIndex, partEnd: redo.partEnd };
    ctx.progress.currentIndex = lastAccepted.index;
    saveProgress();
    logEvent('redo_last', { targetIndex: redo.targetIndex, fromPartEnd });
    setFeedback(coaching() ? null : 'redoing', 'info');
    enterReady();
  }

  // Pressed Redo by mistake: go back to where they were.
  function cancelRedo() {
    const pending = redo;
    redo = null;
    justRecorded = false;
    if (redoLesson === 'redoing') redoLesson = 'pending';
    delete ctx.progress.pendingRedo;
    ctx.progress.currentIndex = pending.returnIndex;
    if (pending.partEnd && pending.partEnd.kind === 'all') Object.assign(ctx.progress, { completed: true, completedAt: new Date().toISOString() });
    saveProgress();
    logEvent('redo_cancelled', { targetIndex: pending.targetIndex });
    setFeedback(null);
    if (pending.partEnd) enterPartEnd(pending.partEnd);
    else enterReady();
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
    if (!quotaHit && !(estimate && estimate.blocked)) {
      storageBlocked = false;
      roomFromLatest = false;
      return;
    }
    await flush();
    // Copies of earlier ZIP files make room first. Those of the most recent ZIP stay until
    // the participant confirms that file is saved (the save screen asks).
    const pruned = await V2S.storage.pruneExported(Infinity, { keepLatest: true });
    if (pruned) {
      logEvent('backups_pruned', { count: pruned, reason: 'storage' });
      quotaHit = false;
      const after = await V2S.storage.storageEstimate();
      if (!(after && after.blocked)) {
        storageBlocked = false;
        roomFromLatest = false;
        return;
      }
    }
    // Saving helps if something is waiting to be saved; otherwise only the last ZIP's
    // copies are left to remove.
    const unsaved = await V2S.storage.countUnsaved();
    roomFromLatest = unsaved === 0 && (await V2S.storage.latestBackup()).ids.length > 0;
    storageBlocked = unsaved > 0 || roomFromLatest;
    logEvent('storage_near_full', { ratio: estimate ? estimate.ratio : null, quotaHit, unsaved, roomFromLatest, blocked: storageBlocked });
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

  // The earlier page's option text for a setting (its sidecars carry these labels).
  function optionLabel(kind, value) {
    const option = cfg.QUALITY_LABELS[kind].find(([key]) => String(key) === String(value));
    return option ? option[1] : String(value);
  }

  // Every key the earlier page wrote, in the same shape, so old and new sidecars can be
  // read by the same scripts; the new keys come on top.
  function buildMetadata(current, recording, qc, status, takeNumber, fileName, replaced, round) {
    const p = position(current.index);
    const settings = V2S.media.getSettings();
    const usable = status === 'accepted' || status === 'qc_overridden';
    const requested = V2S.media.requestedConstraints() || {};
    const failuresInARow = qc.pass ? 0 : (qcFailures.index === current.index ? qcFailures.count : 1);
    return {
      appVersion: cfg.APP_VERSION,
      uiVersion: 'next',
      materialCacheVersion: cfg.MATERIAL_VERSION,
      createdAt: new Date().toISOString(),
      startedAt: current.recorder && Number.isFinite(current.recorder.startedAt) ? new Date(performance.timeOrigin + current.recorder.startedAt).toISOString() : null,
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
      supersedes: replaced ? replaced.fileName : null,
      round,
      qcOverride: status === 'qc_overridden',
      requiresRetry: !usable,
      qcIssue: qc.pass ? null : qc.code,
      qcFailuresInARow: failuresInARow,
      audioQualityWarning: qc.pass ? null : feedbackText(qc.code) || null,
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
        readNow: relative(current.readNowAt),
        stopPress: relative(current.stopAt),
        recorderStop: relative(current.recorderStoppedAt)
      },
      timing: {
        startCueLeadMs: current.cueLeadMs || 0,
        startGuardMs: 0,
        startAttempts: current.attempts,
        startErrors: current.startErrors,
        tailMs: current.tailMs ?? null,
        holdMs: V2S.input.getHoldMs()
      },
      stopDelayMs: cfg.TAIL_MS,
      inputType: current.source,
      stopInputType: current.stopSource || null,
      session: { takesInSession: takesThisSession, msSinceSessionStart: sinceSessionStart() },
      quality: { label: optionLabel('bitrate', settings.bitrate), videoBitsPerSecond: Number(settings.bitrate) },
      frameRate: { label: optionLabel('fps', settings.fps), fps: Number(settings.fps) },
      resolution: settings.resolution,
      audioMode: { mode: settings.audioMode === 'fallback' ? 'fallback' : 'raw', label: optionLabel('audio', settings.audioMode === 'fallback' ? 'fallback' : 'raw') },
      audioConstraintMode: V2S.media.getAudioConstraintMode(),
      requestedVideoConstraints: requested.video || null,
      requestedAudioConstraints: requested.audio || null,
      recorderConfig: recording.recorderConfig || null,
      recorderError: recording.error || null,
      mediaAtStart: current.mediaAtStart || null,
      mediaAtSave: V2S.media.snapshot(),
      browser: { userAgent: navigator.userAgent, platform: navigator.platform || '', language: navigator.language || '' },
      saveMode: V2S.exporter.getSaveMode(),
      downloadClearPolicy: V2S.exporter.getSaveMode() === 'folder' ? 'deleted_after_verified_folder_write' : 'kept_as_backup_after_confirmed_save'
    };
  }

  // Names the take now and stores it — together with the progress it causes — in one
  // background transaction. A usable take replaces any earlier usable take of the same
  // sentence in this round (Redo, going back, practising again): storage marks the old one
  // superseded in the same transaction, or lists it if it has already left the device.
  function persistTake(current, recording, qc, status, nextIndex) {
    takesThisSession += 1;
    const counts = ctx.progress.takeCounts;
    const takeNumber = (counts[current.index] || 0) + 1;
    counts[current.index] = takeNumber;
    const p = position(current.index);
    const round = ctx.progress.round;
    const progressInfo = p.warmup ? `_warmup${p.pos}-${p.total}_repeat${round}` : `_${p.pos}-${p.total}_repeat${round}`;
    const fileName = uniqueName(`${sanitize(current.sentence)}${progressInfo}_${timestamp()}${takeNumber > 1 ? '_redo' : ''}.${recording.ext}`);
    current.fileName = fileName;
    const usable = status === 'accepted' || status === 'qc_overridden';
    const replaced = usable ? ctx.progress.usable[current.index] || null : null;
    if (usable) ctx.progress.usable[current.index] = { fileName, takeId: current.id };
    const metadata = buildMetadata(current, recording, qc, status, takeNumber, fileName, replaced, round);

    // The last practice sentence after "Practise again": the place to come back to is
    // stored with this take (End for today on the pause must not lose it).
    if (p.warmup && p.pos === p.total && nextIndex === current.index + 1 && Number.isInteger(ctx.progress.resumeIndex)) {
      nextIndex = ctx.progress.resumeIndex;
    }
    if (nextIndex >= ctx.material.all.length) {
      ctx.progress.currentIndex = ctx.material.all.length - 1;
      ctx.progress.completed = true;
      ctx.progress.completedAt = new Date().toISOString();
      ctx.progress.repetitionCount = Math.max(Number(ctx.progress.repetitionCount) || 0, round);
    } else {
      ctx.progress.currentIndex = nextIndex;
    }
    const progressSnapshot = snapshot(ctx.progress);

    enqueue(async () => {
      let record = null;
      try {
        record = {
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
        const id = await V2S.storage.commitTake(record, progressSnapshot, replaced);
        storeFailures = 0;
        quotaHit = false;
        logEvent('take_saved', { index: current.index, status, fileName, qc: qc.code, speechMs: qc.metrics.speechMs, replaces: replaced && replaced.fileName });
        V2S.exporter.queueFolderWrite(id, record, recording.blob);
        if (replaced) V2S.exporter.applySuperseded(ctx.participantId, ctx.setKey);
      } catch (error) {
        const quota = Boolean(error && error.name === 'QuotaExceededError');
        logEvent('take_store_failed', { fileName, quota, error: String(error && error.message || error) });
        // Folder mode: write it straight to the folder instead. Otherwise the participant
        // records that sentence again — the take is never silently lost or skipped.
        const rescued = await V2S.exporter.rescueTake(recording.blob, {
          fileName, metadata, mimeType: recording.mimeType, participantId: ctx.participantId, status,
          sentence: current.sentence, sentenceSet: ctx.setKey, sentenceIndex: current.index, size: recording.blob.size,
          timestamp: new Date().toISOString(), takeId: current.id
        }, replaced);
        if (rescued) {
          await V2S.storage.saveParticipantProgress(progressSnapshot).catch(() => {});
        } else {
          storeFailed(current, usable, replaced, quota);
        }
      }
    });
    return writeChain;
  }

  // A take could not be stored, so its sentence must be recorded again. Progress goes back
  // to it at once (saved after every write already queued), also when no session is on
  // screen; while another take is being recorded, the screen follows when it is done.
  function storeFailed(current, usable, replaced, quota) {
    if (usable) {
      const entry = ctx.progress.usable[current.index];
      // Undo only this take's own entry: a newer take of the sentence may have replaced it.
      if (entry && entry.takeId === current.id) {
        if (replaced) ctx.progress.usable[current.index] = replaced;
        else delete ctx.progress.usable[current.index];
      }
    }
    storeFailures += 1;
    if (quota) quotaHit = true;
    storeFailedAt = storeFailedAt === null ? current.index : Math.min(storeFailedAt, current.index);
    if (state === 'ready' || state === 'partEnd') backToUnstored();
    else if (state === 'idle') rewindTo(storeFailedAt);
  }

  function rewindTo(i) {
    if (!ctx.progress.completed && ctx.progress.currentIndex <= i) return;
    Object.assign(ctx.progress, { currentIndex: i, completed: false, completedAt: null });
    ctx.progress.repetitionCount = Math.min(Number(ctx.progress.repetitionCount) || 0, V2S.storage.roundOf(ctx.progress) - 1);
    delete ctx.progress.pendingRedo;
    saveProgress();
    logEvent('rewound', { index: i });
  }

  // Back to the first sentence whose take could not be stored. A full device leads to the
  // save screen; a device that keeps failing for another reason gets the error screen.
  async function backToUnstored() {
    const i = storeFailedAt;
    storeFailedAt = null;
    redo = null;
    partEnd = null;
    lastAccepted = null;
    rewindTo(i);
    setFeedback('storeFailed', 'warn');
    logEvent('back_to_unstored', { index: i, failures: storeFailures });
    enterReady();
    if (quotaHit || storeFailures >= 2) {
      await refreshStorageGuard().catch(() => {});
      if (state !== 'ready') return;
      if (storageBlocked && handlers.onStorageFull) handlers.onStorageFull();
      else if (storeFailures >= 2 && handlers.onStoreFailure) handlers.onStoreFailure();
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
    consecutiveStartFailures = 0;
    setFeedback(null);
    resume();
  }

  // After the last sentence, recording again (Settings: Go to, Previous, Clear progress, …)
  // starts the next pass: new file names say repeat<n+1>, and no sentence has a usable
  // take in it yet. Before that, a sentence recorded again replaces its earlier take.
  function startNewRoundIfCompleted(progress) {
    if (!progress.completed) return false;
    const round = V2S.storage.roundOf(progress) + 1;
    Object.assign(progress, { completed: false, completedAt: null, round, usable: {}, takeCounts: {} });
    delete progress.pendingRedo;
    logEvent('new_round', { round });
    return true;
  }

  // Settings: go to another sentence without recording (Previous / Next / Skip / Go to).
  // Redo is cleared: it must never reach across a jump.
  function jumpTo(target) {
    if (!ctx || !['ready', 'partEnd', 'idle'].includes(state)) return false;
    const i = Math.max(0, Math.min(target, ctx.material.all.length - 1));
    startNewRoundIfCompleted(ctx.progress);
    Object.assign(ctx.progress, { currentIndex: i, completed: false, completedAt: null });
    delete ctx.progress.pendingRedo;
    redo = null;
    lastAccepted = null;
    partEnd = null;
    justRecorded = false;
    lessonJustDone = false;
    if (i < ctx.material.warmupCount && !ctx.progress.coachDone) redoLesson = 'pending';
    qcFailures = { index: null, count: 0 };
    setFeedback(null);
    saveProgress();
    logEvent('jump', { to: i });
    if (state !== 'idle') enterReady();
    return true;
  }

  // Back on the recording screen (from How to record, Settings, a new check): carry on
  // exactly where it was, including the pause after a part's last sentence.
  function resume() {
    if (partEnd && lastAccepted) enterPartEnd(partEnd);
    else enterReady();
  }

  // The page is being left (another tab took over): keep what was recorded, as not used.
  async function abortCurrent(status) {
    if (take && !take.closed) await abortTake(status, null, 'warn', take);
    await flush();
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden && take && !take.closed && ['starting', 'recording', 'finishing'].includes(state)) {
      abortTake('aborted_hidden', 'hidden');
    }
  });

  return {
    configure,
    begin,
    stop,
    getState,
    getContext,
    position,
    coaching,
    onPrimary,
    onSecondary,
    onHold,
    onDeviceFailure,
    resumeAfterReconnect,
    resume,
    jumpTo,
    startNewRoundIfCompleted,
    abortCurrent,
    needsRoom: () => storageBlocked && roomFromLatest,
    enterReady,
    flush,
    refreshStorage: refreshStorageGuard
  };
})();
