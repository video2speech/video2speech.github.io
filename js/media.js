// Camera/microphone stream, one MediaRecorder per take, and hardware health checks.
// Only real device failures (track ended, microphone muted, frozen picture) are
// reported; silence is never treated as a failure.
window.V2S = window.V2S || {};

V2S.media = (() => {
  const cfg = V2S.config;
  const { logEvent } = V2S.util;

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

  function videoConstraints() {
    const constraints = { facingMode: 'user', frameRate: { ideal: Number(settings.fps) || 30 } };
    const size = cfg.RESOLUTIONS[settings.resolution];
    if (size) {
      constraints.width = { ideal: size.width };
      constraints.height = { ideal: size.height };
    }
    return constraints;
  }

  function rawAudioConstraints() {
    return { echoCancellation: false, noiseSuppression: false, autoGainControl: false, sampleRate: 48000, channelCount: 1 };
  }

  function isSupported() {
    return Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && typeof MediaRecorder !== 'undefined');
  }

  function failure(code, error) {
    const wrapped = error instanceof Error ? error : new Error(String(error || code));
    wrapped.code = code;
    return wrapped;
  }

  async function open() {
    close();
    if (!isSupported()) throw failure('unsupported', 'MediaRecorder or getUserMedia is not available');
    const video = videoConstraints();
    try {
      if (settings.audioMode === 'fallback') {
        stream = await navigator.mediaDevices.getUserMedia({ video, audio: true });
        audioConstraintMode = 'fallback';
      } else {
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video, audio: rawAudioConstraints() });
          audioConstraintMode = 'raw';
        } catch (rawError) {
          if (rawError && (rawError.name === 'NotAllowedError' || rawError.name === 'SecurityError')) throw rawError;
          // Some devices refuse the raw-audio constraints. Keep going with the browser
          // defaults instead of asking the participant to change a setting.
          logEvent('raw_audio_failed', { error: String(rawError && rawError.name || rawError) });
          stream = await navigator.mediaDevices.getUserMedia({ video, audio: true });
          audioConstraintMode = 'fallback_auto';
        }
      }
    } catch (error) {
      const denied = error && (error.name === 'NotAllowedError' || error.name === 'SecurityError');
      throw failure(denied ? 'permission' : 'device', error);
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
      audio: audioConstraintMode === 'raw' ? rawAudioConstraints() : true
    };
  }

  // ---- recorder ----
  function recorderCandidates() {
    const base = { videoBitsPerSecond: Number(settings.bitrate) || cfg.MEDIA_DEFAULTS.bitrate, audioBitsPerSecond: cfg.AUDIO_BITRATE };
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

  // Starts recording one take. stop() resolves with the recorded blob.
  function startRecorder() {
    if (!stream) throw failure('device', 'No camera stream');
    const attempts = [];
    let recorder = null;
    let config = null;
    for (const candidate of recorderCandidates()) {
      try {
        recorder = new MediaRecorder(stream, candidate.options);
        config = candidate;
        break;
      } catch (error) {
        attempts.push(`${candidate.requestedMimeType}: ${error.name || error.message}`);
      }
    }
    if (!recorder) throw failure('device', `No supported recording format (${attempts.join('; ')})`);

    const chunks = [];
    let settle;
    const stopped = new Promise(resolve => { settle = resolve; });
    const finish = extra => {
      const info = mimeInfo(recorder, chunks, config.requestedMimeType);
      settle({ blob: new Blob(chunks, { type: info.mimeType }), ...info, recorderConfig: config, stoppedAt: performance.now(), ...extra });
    };
    recorder.ondataavailable = event => { if (event.data && event.data.size > 0) chunks.push(event.data); };
    recorder.onstop = () => finish({});
    recorder.onerror = event => logEvent('recorder_error', { error: String(event.error || event.name || 'unknown') });
    recorder.start(1000);
    const startedAt = performance.now();

    return {
      startedAt,
      recorderConfig: config,
      stop() {
        if (recorder.state !== 'inactive') {
          try {
            recorder.stop();
          } catch (error) {
            finish({ stopError: String(error) });
          }
        }
        return stopped;
      }
    };
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
    setSettings,
    getSettings,
    getStream,
    getAudioConstraintMode,
    open,
    close,
    onFailure,
    registerPreview,
    snapshot,
    requestedConstraints,
    startRecorder,
    startHealth,
    stopHealth,
    setMonitorVideo,
    startMonitor,
    stopMonitor
  };
})();
