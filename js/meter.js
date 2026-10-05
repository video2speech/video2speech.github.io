// Live microphone analysis: one AudioContext, an analyser sampled about 60 times a
// second. Draws the rolling sound levels (the check screen's always moves; the recording
// screen's small one only while recording, in neutral grey), collects frames for the
// recording check, and notices speech while nothing is being recorded ("Not recording yet").
window.V2S = window.V2S || {};

V2S.meter = (() => {
  const cfg = V2S.config;
  const Q = cfg.QC;
  const WAVE_WINDOW_MS = 4000;

  let audioContext = null;
  let analyser = null;
  let source = null;
  let sink = null;
  let buffer = null;
  let rafId = null;
  let lastSampleAt = 0;
  let lastDrawAt = 0;

  let collector = null;
  let idleEnabled = false;
  let idleSince = 0;          // only sound after this moment counts as "speaking before Start"
  let idleListener = null;
  let lastIdleHintAt = -Infinity;
  const recent = [];          // frames of the last 5 s (noise floor for the idle hint)
  const history = [];         // { t, v } for the waveform, v in 0..1
  const waves = new Map();      // canvas → { idleFlat }
  let live = false;
  let colors = null;

  function context() {
    if (!audioContext || audioContext.state === 'closed') {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioContext = AudioContextClass ? new AudioContextClass() : null;
    }
    return audioContext;
  }

  // Call from a user gesture: iOS only runs audio after one, and can pause it later.
  function resume() {
    const ctx = context();
    if (ctx && ctx.state !== 'running' && ctx.state !== 'closed') ctx.resume().catch(() => {});
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
    recent.length = 0;
    history.length = 0;
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
    history.length = 0;
    drawWaves(performance.now());
  }

  // ---- waveform ----
  // idleFlat: the recording screen's waveform only moves while recording, so a moving
  // waveform never suggests "it is recording" when it is not. The check screen's always moves.
  function registerWave(canvas, { idleFlat = false, windowMs = WAVE_WINDOW_MS } = {}) {
    waves.set(canvas, { idleFlat, windowMs });
  }

  function setLive(value) {
    live = Boolean(value);
    colors = null;
  }

  function refreshColors() {
    colors = null;
  }

  function resolveColors() {
    const style = getComputedStyle(document.documentElement);
    colors = {
      idle: style.getPropertyValue('--wave-wait').trim() || '#C9CCD1',
      live: style.getPropertyValue('--wave-live').trim() || '#35A562'
    };
    return colors;
  }

  // Loudness in 0..1 on a decibel scale, so quiet speech still shows.
  function level(rms) {
    const db = 20 * Math.log10(Math.max(rms, 1e-6));
    const v = Math.min(1, Math.max(0, (db + 58) / 46));
    return Math.sqrt(v);
  }

  function drawWaves(now) {
    const palette = colors || resolveColors();
    const color = live ? palette.live : palette.idle;
    waves.forEach((options, canvas) => {
      if (!canvas.isConnected || canvas.offsetParent === null) return;
      const flat = options.idleFlat && !live;
      const dpr = window.devicePixelRatio || 1;
      const width = Math.round(canvas.clientWidth * dpr);
      const height = Math.round(canvas.clientHeight * dpr);
      if (!width || !height) return;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = color;
      const barWidth = Math.max(2, Math.round(3 * dpr));
      const gap = Math.max(2, Math.round(2.5 * dpr));
      const bars = Math.floor(width / (barWidth + gap));
      const slice = options.windowMs / bars;
      const minHeight = Math.max(2, Math.round(3 * dpr));
      let index = history.length - 1;
      for (let b = 0; b < bars; b++) {
        const end = now - b * slice;
        const start = end - slice;
        let value = 0;
        while (index >= 0 && history[index].t > end) index--;
        let j = index;
        while (j >= 0 && history[j].t > start) {
          if (history[j].v > value) value = history[j].v;
          j--;
        }
        const barHeight = flat ? minHeight : Math.max(minHeight, value * (height - 2 * dpr));
        const x = width - (b + 1) * (barWidth + gap) + gap;
        const y = (height - barHeight) / 2;
        if (typeof ctx.roundRect === 'function') {
          ctx.beginPath();
          ctx.roundRect(x, y, barWidth, barHeight, barWidth / 2);
          ctx.fill();
        } else {
          ctx.fillRect(x, y, barWidth, barHeight);
        }
      }
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

    history.push({ t: time, v: level(frame.rms) });
    while (history.length && time - history[0].t > WAVE_WINDOW_MS + 200) history.shift();
    if (time - lastDrawAt >= 30) {
      lastDrawAt = time;
      drawWaves(time);
    }
    checkIdleSpeech(frame);
  }

  // Speech while nothing records: same frame rule as the recording check, with the
  // noise floor taken from the last five seconds.
  function checkIdleSpeech(frame) {
    recent.push(frame);
    while (recent.length && frame.t - recent[0].t > 5000) recent.shift();
    if (!idleEnabled || !idleListener) return;
    if (recent.length < 2 || frame.t - recent[0].t < 1500) return;
    if (frame.t - lastIdleHintAt < cfg.IDLE_SPEECH_HINT_COOLDOWN_MS) return;
    const floor = V2S.util.percentile(recent.map(f => f.rms), Q.NOISE_FLOOR_PERCENTILE);
    const threshold = Math.max(Q.SPEECH_MIN_RMS, Q.SPEECH_NOISE_MULTIPLIER * floor);
    // Only sound since the waiting began counts (not the end of the take just recorded).
    const lastSecond = recent.filter(f => frame.t - f.t <= 1000 && f.t >= idleSince);
    if (lastSecond.length < 2) return;
    const interval = (lastSecond[lastSecond.length - 1].t - lastSecond[0].t) / (lastSecond.length - 1);
    const speechMs = lastSecond.filter(f => f.rms >= threshold).length * interval;
    if (speechMs >= cfg.IDLE_SPEECH_HINT_MS) {
      lastIdleHintAt = frame.t;
      idleListener();
    }
  }

  function setIdleDetection(enabled, listener, graceMs = 0) {
    if (enabled && !idleEnabled) idleSince = performance.now() + graceMs;
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
    registerWave,
    setLive,
    refreshColors,
    setIdleDetection,
    beginCollect,
    endCollect,
    isRunning
  };
})();

// Short cue sounds through the shared AudioContext.
V2S.sounds = (() => {
  const patterns = {
    start: [[880, 0, 0.04]],
    saved: [[988, 0, 0.09]],
    retry: [[440, 0, 0.1], [370, 0.13, 0.13]]
  };

  function play(kind, level = 0.22) {
    const ctx = V2S.meter.context();
    if (!ctx || ctx.state !== 'running' || !patterns[kind]) return;
    const now = ctx.currentTime + 0.01;
    patterns[kind].forEach(([frequency, offset, duration]) => {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0, now + offset);
      gain.gain.linearRampToValueAtTime(level, now + offset + 0.008);
      gain.gain.exponentialRampToValueAtTime(0.001, now + offset + duration);
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      oscillator.start(now + offset);
      oscillator.stop(now + offset + duration + 0.02);
    });
  }

  // The start cue at the press: a short, soft tick. It must be over before recording
  // starts (so it is not in the recording), and recording must start almost at once (so
  // no word is missed). The wait counts the device's sound output delay (40 ms where the
  // browser does not report it), the microphone's input delay and 30 ms for the room;
  // if that is longer than START_CUE_MAX_MS there is no cue and recording starts at the
  // press. Returns the wait before recording starts.
  function startCue() {
    const ctx = V2S.meter.context();
    if (!ctx || ctx.state !== 'running') return 0;
    // Without a reported output delay (Safari before 18.4), or with Bluetooth headphones
    // or speakers (a long delay, not always reported), the cue could be recorded: none.
    if (!('outputLatency' in ctx) || V2S.media.current().bluetooth || V2S.media.outputIsBluetooth()) return 0;
    const outputMs = (Number(ctx.outputLatency) || 0.04) * 1000 + (Number(ctx.baseLatency) || 0) * 1000;
    const inputMs = V2S.media.inputLatencyMs();
    const [[, , seconds]] = patterns.start;
    const lead = Math.ceil(10 + seconds * 1000 + outputMs + inputMs + 30);
    if (lead > V2S.config.START_CUE_MAX_MS) return 0;
    play('start', 0.16);
    return lead;
  }

  return { play, startCue };
})();
