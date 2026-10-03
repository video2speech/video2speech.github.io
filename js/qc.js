// Recording check (rules approved 2026-10-03, thresholds in config.QC):
// too_loud when >= 1% of samples clip; no_speech when under 300 ms of frames reach
// max(0.004, 3 x the take's 20th-percentile frame RMS). Everything else is only recorded.
window.V2S = window.V2S || {};

V2S.qc = (() => {
  const Q = V2S.config.QC;

  function evaluate(frames) {
    if (!frames.length) {
      return { pass: false, code: 'no_speech', metrics: { frames: 0, speechMs: 0 } };
    }
    let sumSquares = 0;
    let samples = 0;
    let peak = 0;
    let clipped = 0;
    frames.forEach(frame => {
      sumSquares += frame.rms * frame.rms * frame.samples;
      samples += frame.samples;
      clipped += frame.clipped;
      if (frame.peak > peak) peak = frame.peak;
    });
    const noiseFloor = V2S.util.percentile(frames.map(frame => frame.rms), Q.NOISE_FLOOR_PERCENTILE);
    const threshold = Math.max(Q.SPEECH_MIN_RMS, Q.SPEECH_NOISE_MULTIPLIER * noiseFloor);
    const first = frames[0].t;
    const last = frames[frames.length - 1].t;
    const interval = frames.length > 1 && last > first ? (last - first) / (frames.length - 1) : 1000 / 60;
    const speechTimes = frames.filter(frame => frame.rms >= threshold).map(frame => frame.t);
    const clippingRate = samples ? clipped / samples : 0;
    const metrics = {
      frames: frames.length,
      durationMs: Math.round(last - first),
      rms: Number(Math.sqrt(sumSquares / samples).toFixed(6)),
      peak: Number(peak.toFixed(6)),
      clippingRate: Number(clippingRate.toFixed(6)),
      noiseFloor: Number(noiseFloor.toFixed(6)),
      speechThreshold: Number(threshold.toFixed(6)),
      speechFrames: speechTimes.length,
      frameIntervalMs: Number(interval.toFixed(2)),
      speechMs: Math.round(speechTimes.length * interval),
      leadSilenceMs: speechTimes.length ? Math.round(speechTimes[0] - first) : null,
      speechAtEnd: speechTimes.some(time => last - time <= Q.END_WINDOW_MS)
    };
    if (clippingRate >= Q.CLIPPING_RATE) return { pass: false, code: 'too_loud', metrics };
    if (metrics.speechMs < Q.SPEECH_MIN_MS) return { pass: false, code: 'no_speech', metrics };
    return { pass: true, code: null, metrics };
  }

  return { evaluate, rules: () => ({ ...Q }) };
})();
