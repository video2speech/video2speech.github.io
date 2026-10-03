// Live microphone analysis: one AudioContext, an analyser sampled ~60 times a second.
// Feeds the level bars, collects frames for the recording check, and notices speech
// while nothing is being recorded ("Not recording yet").
window.V2S = window.V2S || {};

V2S.meter = (() => {
  const cfg = V2S.config;
  const Q = cfg.QC;

  let audioContext = null;
  let analyser = null;
  let source = null;
  let sink = null;
  let buffer = null;
  let rafId = null;
  let lastSampleAt = 0;
  let level = 0;
  const levelBars = new Set();

  let collector = null;
  let idleEnabled = false;
  let idleListener = null;
  let lastIdleHintAt = -Infinity;
  const idleWindow = [];

  function context() {
    if (!audioContext || audioContext.state === 'closed') {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioContext = AudioContextClass ? new AudioContextClass() : null;
    }
    return audioContext;
  }

  // Must be called from a user gesture on iOS so audio analysis and cues can run.
  function resume() {
    const ctx = context();
    if (ctx && ctx.state === 'suspended') ctx.resume().catch(() => {});
    return ctx;
  }

  function attach(stream) {
    detach();
    const ctx = context();
    if (!ctx || !stream || !stream.getAudioTracks().length) return;
    source = ctx.createMediaStreamSource(stream);
    analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0;
    buffer = new Float32Array(analyser.fftSize);
    sink = ctx.createGain();
    sink.gain.value = 0; // keeps the graph running without playing the microphone back
    source.connect(analyser);
    analyser.connect(sink);
    sink.connect(ctx.destination);
    idleWindow.length = 0;
    if (!rafId) rafId = requestAnimationFrame(tick);
  }

  function detach() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
    [source, analyser, sink].forEach(node => {
      if (node) {
        try { node.disconnect(); } catch (error) { /* already disconnected */ }
      }
    });
    source = null;
    analyser = null;
    sink = null;
    level = 0;
    renderLevel(0, 0);
  }

  function registerLevelBar(element) {
    levelBars.add(element);
  }

  function renderLevel(value, peak) {
    levelBars.forEach(bar => {
      bar.style.transform = `scaleX(${value.toFixed(3)})`;
      bar.parentElement.classList.toggle('is-hot', peak >= 0.98);
    });
  }

  function tick(time) {
    rafId = requestAnimationFrame(tick);
    if (!analyser || time - lastSampleAt < 14) return;
    lastSampleAt = time;
    analyser.getFloatTimeDomainData(buffer);
    let sumSquares = 0;
    let peak = 0;
    let clipped = 0;
    for (let i = 0; i < buffer.length; i++) {
      const value = buffer[i];
      const magnitude = Math.abs(value);
      sumSquares += value * value;
      if (magnitude > peak) peak = magnitude;
      if (magnitude >= Q.CLIPPING_SAMPLE) clipped++;
    }
    const frame = { t: time, rms: Math.sqrt(sumSquares / buffer.length), peak, clipped, samples: buffer.length };
    if (collector) collector.push(frame);

    // Level bar: -60 dBFS..-6 dBFS mapped to 0..1, fast attack, slow release.
    const db = 20 * Math.log10(Math.max(frame.rms, 1e-6));
    const target = Math.min(1, Math.max(0, (db + 60) / 54));
    level += (target - level) * (target > level ? 0.6 : 0.12);
    renderLevel(level, peak);

    checkIdleSpeech(frame);
  }

  // Speech while nothing records: same frame rule as the recording check, with the
  // noise floor taken from the last five seconds.
  function checkIdleSpeech(frame) {
    idleWindow.push(frame);
    while (idleWindow.length && frame.t - idleWindow[0].t > 5000) idleWindow.shift();
    if (!idleEnabled || !idleListener) return;
    if (idleWindow.length < 2 || frame.t - idleWindow[0].t < 1500) return;
    if (frame.t - lastIdleHintAt < cfg.IDLE_SPEECH_HINT_COOLDOWN_MS) return;
    const floor = V2S.util.percentile(idleWindow.map(f => f.rms), Q.NOISE_FLOOR_PERCENTILE);
    const threshold = Math.max(Q.SPEECH_MIN_RMS, Q.SPEECH_NOISE_MULTIPLIER * floor);
    const recent = idleWindow.filter(f => frame.t - f.t <= 1000);
    if (recent.length < 2) return;
    const interval = (recent[recent.length - 1].t - recent[0].t) / (recent.length - 1);
    const speechMs = recent.filter(f => f.rms >= threshold).length * interval;
    if (speechMs >= cfg.IDLE_SPEECH_HINT_MS) {
      lastIdleHintAt = frame.t;
      idleListener();
    }
  }

  function setIdleDetection(enabled, listener) {
    idleEnabled = enabled;
    if (listener) idleListener = listener;
  }

  function beginCollect() {
    collector = [];
  }

  function endCollect() {
    const frames = collector || [];
    collector = null;
    return frames;
  }

  const isRunning = () => Boolean(analyser) && Boolean(audioContext) && audioContext.state === 'running';

  return {
    context,
    resume,
    attach,
    detach,
    registerLevelBar,
    setIdleDetection,
    beginCollect,
    endCollect,
    isRunning
  };
})();

// Short cue sounds through the shared AudioContext.
V2S.sounds = (() => {
  const patterns = {
    start: [[660, 0, 0.07], [880, 0.075, 0.07]],
    saved: [[988, 0, 0.09]],
    retry: [[440, 0, 0.1], [370, 0.13, 0.13]]
  };

  function play(kind) {
    const ctx = V2S.meter.context();
    if (!ctx || ctx.state !== 'running' || !patterns[kind]) return;
    const now = ctx.currentTime + 0.01;
    patterns[kind].forEach(([frequency, offset, duration]) => {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0, now + offset);
      gain.gain.linearRampToValueAtTime(0.22, now + offset + 0.012);
      gain.gain.exponentialRampToValueAtTime(0.001, now + offset + duration);
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      oscillator.start(now + offset);
      oscillator.stop(now + offset + duration + 0.02);
    });
  }

  return { play };
})();
