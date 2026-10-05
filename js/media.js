// Camera/microphone stream, one MediaRecorder per take, and hardware health checks.
// - Recording settings are the legacy page's: 1080p, 30 fps, 15 Mbps, raw mono audio.
// - The audio bitrate follows the microphone's real sample rate (see config).
// - startRecorder() reports through `ready` whether the encoder really started, so the
//   sentence only turns green once something is being recorded.
// - Only real device failures (track ended, microphone muted, frozen picture) are
//   reported; silence is never treated as a failure.
window.V2S = window.V2S || {};

V2S.media = (() => {
  const cfg = V2S.config;
  const { logEvent } = V2S.util;
  const BLUETOOTH = /bluetooth|airpods|hands-?free|headset|buds|beats|bose|jabra|\bbt\b/i;

  let stream = null;
  let audioConstraintMode = 'none';
  let settings = { ...cfg.MEDIA_DEFAULTS };
  const previews = new Set();
  let failureHandler = null;
  let healthTimer = null;
  let muteTimer = null;

  // Frozen-picture detection while a take is recording.
  let monitorVideo = null;
  let monitoring = false;
  let frameCallbackId = null;
  let lastFrameAt = 0;
  let lastChangeAt = 0;
  let lastSignature = null;
  let monitorStartedAt = 0;
  let lastCurrentTime = null;
  let signatureCanvas = null;

  function setSettings(next) {
    settings = { ...cfg.MEDIA_DEFAULTS, ...(next || {}) };
    previews.forEach(applyMirror);
  }

  const getSettings = () => ({ ...settings });
  const getStream = () => stream;
  const getAudioConstraintMode = () => audioConstraintMode;
  const isBluetooth = label => BLUETOOTH.test(String(label || ''));

  function videoConstraints(useDevice = true) {
    const constraints = { frameRate: { ideal: Number(settings.fps) || 30 } };
    if (useDevice && settings.videoDeviceId) constraints.deviceId = { exact: settings.videoDeviceId };
    else constraints.facingMode = 'user';
    const size = cfg.RESOLUTIONS[settings.resolution];
    if (size) {
      constraints.width = { ideal: size.width };
      constraints.height = { ideal: size.height };
    }
    return constraints;
  }

  function rawAudioConstraints(useDevice = true) {
    const constraints = { echoCancellation: false, noiseSuppression: false, autoGainControl: false, sampleRate: 48000, channelCount: 1 };
    if (useDevice && settings.audioDeviceId) constraints.deviceId = { exact: settings.audioDeviceId };
    return constraints;
  }

  function browserAudioConstraints(useDevice = true) {
    return useDevice && settings.audioDeviceId ? { deviceId: { exact: settings.audioDeviceId } } : true;
  }

  function isSupported() {
    return Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && typeof MediaRecorder !== 'undefined');
  }

  function failure(code, error) {
    const wrapped = error instanceof Error ? error : new Error(String(error || code));
    wrapped.code = code;
    return wrapped;
  }

  const isDenied = error => Boolean(error && (error.name === 'NotAllowedError' || error.name === 'SecurityError'));
  const isMissingDevice = error => Boolean(error && (error.name === 'OverconstrainedError' || error.name === 'NotFoundError'));

  async function request(useDevice) {
    const video = videoConstraints(useDevice);
    if (settings.audioMode === 'fallback') {
      audioConstraintMode = 'fallback';
      return navigator.mediaDevices.getUserMedia({ video, audio: browserAudioConstraints(useDevice) });
    }
    try {
      const opened = await navigator.mediaDevices.getUserMedia({ video, audio: rawAudioConstraints(useDevice) });
      audioConstraintMode = 'raw';
      return opened;
    } catch (rawError) {
      if (isDenied(rawError) || isMissingDevice(rawError)) throw rawError;
      // Some devices refuse the raw-audio constraints. Keep going with the browser
      // defaults (recorded in every sidecar) instead of stopping the participant.
      logEvent('raw_audio_failed', { error: String(rawError && rawError.name || rawError) });
      audioConstraintMode = 'fallback_auto';
      return navigator.mediaDevices.getUserMedia({ video, audio: browserAudioConstraints(useDevice) });
    }
  }

  async function open() {
    close();
    if (!isSupported()) throw failure('unsupported', 'MediaRecorder or getUserMedia is not available');
    try {
      try {
        stream = await request(true);
      } catch (error) {
        // A chosen camera or microphone that is no longer connected: use the defaults.
        if (!isMissingDevice(error) || !(settings.videoDeviceId || settings.audioDeviceId)) throw error;
        logEvent('chosen_device_missing', { error: String(error.name || error) });
        stream = await request(false);
      }
    } catch (error) {
      throw failure(isDenied(error) ? 'permission' : 'device', error);
    }
    watchTracks();
    previews.forEach(attachPreview);
    logEvent('media_open', { audioConstraintMode, settings: snapshot() });
    return stream;
  }

  function close() {
    stopMonitor();
    clearTimeout(muteTimer);
    if (stream) {
      stream.getTracks().forEach(track => {
        track.onended = null;
        track.onmute = null;
        track.onunmute = null;
        track.stop();
      });
    }
    stream = null;
    audioConstraintMode = 'none';
    previews.forEach(video => { video.srcObject = null; });
  }

  // Cameras and microphones with readable names (names need camera permission first).
  async function listDevices() {
    if (!navigator.mediaDevices || typeof navigator.mediaDevices.enumerateDevices !== 'function') return { cameras: [], microphones: [] };
    const devices = await navigator.mediaDevices.enumerateDevices();
    const pick = kind => devices.filter(device => device.kind === kind && device.deviceId && device.deviceId !== 'default' && device.deviceId !== 'communications')
      .map((device, index) => ({ id: device.deviceId, label: device.label || `${kind === 'videoinput' ? 'Camera' : 'Microphone'} ${index + 1}` }));
    return { cameras: pick('videoinput'), microphones: pick('audioinput') };
  }

  // What is in use right now: { camera, microphone, cameraId, microphoneId, bluetooth }.
  function current() {
    const videoTrack = stream && stream.getVideoTracks()[0];
    const audioTrack = stream && stream.getAudioTracks()[0];
    const audioSettings = trackSettings(audioTrack);
    return {
      camera: videoTrack ? videoTrack.label : '',
      microphone: audioTrack ? audioTrack.label : '',
      cameraId: trackSettings(videoTrack).deviceId || null,
      microphoneId: audioSettings.deviceId || null,
      sampleRate: audioSettings.sampleRate || null,
      bluetooth: audioTrack ? isBluetooth(audioTrack.label) : false
    };
  }

  function onFailure(handler) {
    failureHandler = handler;
  }

  function report(code, detail = {}) {
    logEvent('device_failure', { code, ...detail });
    if (failureHandler) failureHandler(code, detail);
  }

  function watchTracks() {
    stream.getTracks().forEach(track => {
      track.onended = () => report('track_ended', { kind: track.kind });
      if (track.kind === 'audio') {
        // iOS mutes the microphone during calls or Siri; brief mutes are ignored.
        track.onmute = () => {
          clearTimeout(muteTimer);
          muteTimer = setTimeout(() => { if (track.muted) report('audio_muted'); }, 1500);
        };
        track.onunmute = () => clearTimeout(muteTimer);
      }
    });
  }

  function applyMirror(video) {
    video.classList.toggle('is-mirrored', Boolean(settings.mirror));
  }

  function attachPreview(video) {
    applyMirror(video);
    if (!stream) return;
    if (video.srcObject !== stream) video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    const playing = video.play();
    if (playing && typeof playing.catch === 'function') playing.catch(() => {});
  }

  function registerPreview(video) {
    previews.add(video);
    attachPreview(video);
  }

  function trackSettings(track) {
    try { return track && track.getSettings ? track.getSettings() : {}; } catch (error) { return {}; }
  }

  function trackConstraints(track) {
    try { return track && track.getConstraints ? track.getConstraints() : {}; } catch (error) { return {}; }
  }

  function snapshot() {
    const videoTrack = stream && stream.getVideoTracks()[0];
    const audioTrack = stream && stream.getAudioTracks()[0];
    return {
      video: { settings: trackSettings(videoTrack), constraints: trackConstraints(videoTrack), label: videoTrack ? videoTrack.label : null },
      audio: {
        settings: trackSettings(audioTrack),
        constraints: trackConstraints(audioTrack),
        label: audioTrack ? audioTrack.label : null,
        constraintMode: audioConstraintMode
      }
    };
  }

  function requestedConstraints() {
    return {
      video: videoConstraints(),
      audio: audioConstraintMode === 'raw' ? rawAudioConstraints() : browserAudioConstraints()
    };
  }

  // ---- recorder ----
  function audioBitrate() {
    const audioTrack = stream && stream.getAudioTracks()[0];
    const rate = Number(trackSettings(audioTrack).sampleRate) || 0;
    // Unknown rate: assume a full-rate microphone (the legacy page's 192 kbps).
    return rate && rate < cfg.AUDIO_FULL_RATE_HZ ? cfg.AUDIO_BITRATE_LOW_RATE : cfg.AUDIO_BITRATE;
  }

  function recorderCandidates() {
    const base = { videoBitsPerSecond: Number(settings.bitrate) || cfg.MEDIA_DEFAULTS.bitrate, audioBitsPerSecond: audioBitrate() };
    const types = [
      'video/mp4;codecs=h264,aac',
      'video/mp4;codecs=avc1.42E01E,mp4a.40.2',
      'video/mp4',
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm'
    ];
    const supported = types.filter(type => {
      try { return MediaRecorder.isTypeSupported(type); } catch (error) { return false; }
    }).map(type => ({ options: { ...base, mimeType: type }, requestedMimeType: type }));
    supported.push({ options: base, requestedMimeType: 'browser-default-with-bitrates' });
    supported.push({ options: {}, requestedMimeType: 'browser-default' });
    return supported;
  }

  function mimeInfo(recorder, chunks, requested) {
    const mimeType = recorder.mimeType
      || (chunks.find(chunk => chunk && chunk.type) || {}).type
      || (requested.startsWith('video/') ? requested : '')
      || 'video/webm';
    const lower = mimeType.toLowerCase();
    const ext = lower.includes('mp4') || lower.includes('h264') || lower.includes('avc') ? 'mp4' : 'webm';
    return { mimeType, ext };
  }

  // Starts one recording. Returns
  //   ready   — resolves { ok: true } once the recorder reports that it started and has
  //             run START_SETTLE_MS without an error, or { ok: false, error } if it failed;
  //   stop()  — resolves with { blob, mimeType, ext, recorderConfig, … };
  //   onError — set by the caller for errors after the start.
  // `skip` tries the next recording format (used after repeated start failures).
  function startRecorder({ skip = 0 } = {}) {
    if (!stream) throw failure('device', 'No camera stream');
    const attempts = [];
    let recorder = null;
    let config = null;
    let skipped = 0;
    for (const candidate of recorderCandidates()) {
      try {
        const made = new MediaRecorder(stream, candidate.options);
        if (skipped < skip) {
          skipped += 1;
          continue;
        }
        recorder = made;
        config = candidate;
        break;
      } catch (error) {
        attempts.push(`${candidate.requestedMimeType}: ${error.name || error.message}`);
      }
    }
    if (!recorder) throw failure('device', `No supported recording format (${attempts.join('; ')})`);

    const chunks = [];
    let settleStop;
    let settleReady;
    let started = false;
    const stopped = new Promise(resolve => { settleStop = resolve; });
    const ready = new Promise(resolve => { settleReady = resolve; });
    const handle = {
      startedAt: 0,
      recorderConfig: config,
      error: null,
      onError: null,
      ready,
      stop() {
        if (recorder.state !== 'inactive') {
          try {
            recorder.stop();
          } catch (error) {
            finish({ stopError: String(error) });
          }
        } else {
          finish({});
        }
        return stopped;
      }
    };
    let finished = false;
    function finish(extra) {
      if (finished) return;
      finished = true;
      const info = mimeInfo(recorder, chunks, config.requestedMimeType);
      settleStop({ blob: new Blob(chunks, { type: info.mimeType }), ...info, recorderConfig: config, stoppedAt: performance.now(), error: handle.error, ...extra });
    }
    recorder.ondataavailable = event => { if (event.data && event.data.size > 0) chunks.push(event.data); };
    recorder.onstop = () => finish({});
    recorder.onerror = event => {
      const message = String(event.error || event.name || 'unknown');
      handle.error = message;
      logEvent('recorder_error', { error: message, started, mimeType: config.requestedMimeType, audioBitsPerSecond: config.options.audioBitsPerSecond });
      if (!started) settleReady({ ok: false, error: message });
      else if (handle.onError) handle.onError(message);
    };
    try {
      recorder.start(1000);
    } catch (error) {
      handle.error = String(error);
      settleReady({ ok: false, error: handle.error });
      finish({ startError: handle.error });
      return handle;
    }
    handle.startedAt = performance.now();
    const markStarted = () => {
      if (handle.error || started) return;
      started = true;
      settleReady({ ok: true });
    };
    // Ready once the recorder reports that it started and has run START_SETTLE_MS without
    // an error (an encoder that cannot start fails at once): such a failure is retried
    // before the sentence turns green.
    recorder.onstart = () => {
      const wait = cfg.START_SETTLE_MS - (performance.now() - handle.startedAt);
      if (wait > 0) setTimeout(markStarted, wait);
      else markStarted();
    };
    // Every current browser fires "start"; if one does not, go on once no error came.
    setTimeout(markStarted, cfg.START_TIMEOUT_MS);
    return handle;
  }

  // The microphone's own input delay (ms), where the browser reports it; else 10 ms.
  function inputLatencyMs() {
    const track = stream && stream.getAudioTracks()[0];
    const latency = track && track.getSettings ? Number(track.getSettings().latency) : NaN;
    return Number.isFinite(latency) && latency > 0 ? Math.round(latency * 1000) : 10;
  }

  // ---- health ----
  function startHealth() {
    stopHealth();
    healthTimer = setInterval(checkHealth, cfg.HEALTH_INTERVAL_MS);
  }

  function stopHealth() {
    clearInterval(healthTimer);
    healthTimer = null;
  }

  function checkHealth() {
    if (!stream) return;
    const videoTrack = stream.getVideoTracks()[0];
    const audioTrack = stream.getAudioTracks()[0];
    if (!videoTrack || videoTrack.readyState !== 'live') return report('track_ended', { kind: 'video' });
    if (!audioTrack || audioTrack.readyState !== 'live') return report('track_ended', { kind: 'audio' });
    if (monitoring) {
      const issue = frozenPictureIssue();
      if (issue) report('video_frozen', issue);
    }
  }

  function setMonitorVideo(video) {
    monitorVideo = video;
  }

  function frameSignature() {
    const video = monitorVideo;
    if (!video || !video.videoWidth || !video.videoHeight) return null;
    if (!signatureCanvas) signatureCanvas = document.createElement('canvas');
    signatureCanvas.width = 12;
    signatureCanvas.height = 8;
    const context = signatureCanvas.getContext('2d', { willReadFrequently: true });
    try {
      context.drawImage(video, 0, 0, 12, 8);
      const data = context.getImageData(0, 0, 12, 8).data;
      const values = [];
      for (let i = 0; i < data.length; i += 4) values.push(data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114);
      return values;
    } catch (error) {
      return null;
    }
  }

  function updateSignature(now) {
    const signature = frameSignature();
    if (!signature) return;
    if (!lastSignature) {
      lastSignature = signature;
      lastChangeAt = now;
      return;
    }
    let diff = 0;
    for (let i = 0; i < signature.length; i++) diff += Math.abs(signature[i] - lastSignature[i]);
    if (diff / signature.length > cfg.VIDEO_SIGNATURE_DELTA) {
      lastSignature = signature;
      lastChangeAt = now;
    }
  }

  function startMonitor() {
    stopMonitor();
    const video = monitorVideo;
    const now = performance.now();
    monitoring = true;
    monitorStartedAt = now;
    lastFrameAt = now;
    lastChangeAt = now;
    lastSignature = null;
    lastCurrentTime = video && Number.isFinite(video.currentTime) ? video.currentTime : null;
    updateSignature(now);
    if (video && typeof video.requestVideoFrameCallback === 'function') {
      const onFrame = () => {
        if (!monitoring) return;
        lastFrameAt = performance.now();
        frameCallbackId = video.requestVideoFrameCallback(onFrame);
      };
      frameCallbackId = video.requestVideoFrameCallback(onFrame);
    }
  }

  function stopMonitor() {
    monitoring = false;
    if (frameCallbackId !== null && monitorVideo && typeof monitorVideo.cancelVideoFrameCallback === 'function') {
      try { monitorVideo.cancelVideoFrameCallback(frameCallbackId); } catch (error) { /* ignore */ }
    }
    frameCallbackId = null;
  }

  function frozenPictureIssue() {
    const video = monitorVideo;
    const now = performance.now();
    if (now - monitorStartedAt < cfg.VIDEO_GRACE_MS) return null;
    if (!video || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA || !video.videoWidth) return { reason: 'no_picture' };
    if (typeof video.requestVideoFrameCallback !== 'function') {
      const currentTime = Number.isFinite(video.currentTime) ? video.currentTime : null;
      if (currentTime !== null && (lastCurrentTime === null || currentTime > lastCurrentTime + 0.05)) {
        lastFrameAt = now;
        lastCurrentTime = currentTime;
      }
    }
    updateSignature(now);
    if (now - lastFrameAt > cfg.VIDEO_STUCK_MS) return { reason: 'no_new_frames' };
    if (now - lastChangeAt > cfg.VIDEO_NO_CHANGE_MS) return { reason: 'picture_unchanged' };
    return null;
  }

  return {
    isSupported,
    isBluetooth,
    setSettings,
    getSettings,
    getStream,
    getAudioConstraintMode,
    open,
    close,
    listDevices,
    current,
    onFailure,
    registerPreview,
    snapshot,
    inputLatencyMs,
    requestedConstraints,
    startRecorder,
    startHealth,
    stopHealth,
    setMonitorVideo,
    startMonitor,
    stopMonitor
  };
})();
