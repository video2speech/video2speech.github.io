// Constants for the recorder. Thresholds and timings live here so they can be
// reviewed and tuned in one place.
window.V2S = window.V2S || {};

V2S.config = Object.freeze({
  APP_VERSION: '204',
  MATERIAL_VERSION: 'materials_v204',

  WARMUP_FILE: 'newset/aac_extra_5_sentences.txt',
  WARMUP_COUNT: 5,
  SETS: {
    '50words_350sentences': {
      label: '50words_350sentences',
      about: '350 sentences built from a 50-word vocabulary',
      file: 'newset/350_nonrepeating_sentences.txt',
      count: 350,
      legacyProgressKey: '350_with_warmup_sentences'
    },
    'Open_300sentences': {
      label: 'Open_300sentences',
      about: '300 open sentences',
      file: 'newset/sentence_set_style.txt',
      count: 300
    }
  },
  DEFAULT_SET: '50words_350sentences',
  BLOCK_SIZE: 50,              // one "part" of sentences between rests

  // Interaction (two presses: Start, then Stop).
  HOLD_MS: 1000,               // a press held this long aborts the take
  DEBOUNCE_MS: 300,            // presses closer than this are ignored (switch bounce)
  START_CUE_LEAD_MS: 150,      // start sound plays first so it is not recorded
  START_GUARD_MS: 200,         // the recorder must run this long without an error before the sentence turns green
  START_ATTEMPTS: 3,           // silent recorder restarts before the participant is told
  TAIL_MS: 700,                // keep recording this long after Stop (fixed; legacy page: 300 ms)
  MAX_TAKE_MS: 60000,          // a take this long is aborted and the sentence restarts
  SAVED_LABEL_MS: 1400,        // "Saved" shows on the next sentence without making anyone wait
  IDLE_SPEECH_HINT_MS: 500,    // speaking this long before Start shows a hint
  IDLE_SPEECH_HINT_COOLDOWN_MS: 6000,
  // The camera and microphone test (automated browser tests shorten it via window.__V2S_TEST).
  TEST_RECORD_MS: (window.__V2S_TEST && window.__V2S_TEST.testRecordMs) || 5000,

  // The sentence must read as one continuous sentence (not a few large words per line).
  // ui.fitSentences picks one size per screen and sentence set: the largest size within
  // the device's bounds at which 90% of the set fits on ONE line, with at least
  // SENTENCE_MIN_CHARS_PER_LINE characters per line; the longest sentence may wrap to
  // `lines` lines, and the card keeps that much room so nothing moves.
  SENTENCE_SIZE: Object.freeze({
    wide: Object.freeze({ min: 40, max: 56, lines: 2 }),   // computers, tablets sideways
    tall: Object.freeze({ min: 36, max: 52, lines: 2 }),   // tablets upright
    phone: Object.freeze({ min: 28, max: 36, lines: 2 }),  // phones upright
    flat: Object.freeze({ min: 26, max: 34, lines: 2 })    // phones sideways
  }),
  SENTENCE_ONE_LINE_SHARE: 0.9,
  SENTENCE_LINE_FILL: 0.9,             // a line may use at most 90% of the card width
  SENTENCE_MIN_CHARS_PER_LINE: 18,

  // Recording check (approved 2026-10-03; no_audio approved 2026-10-04). A frame counts as
  // speech when its RMS is at least max(SPEECH_MIN_RMS, SPEECH_NOISE_MULTIPLIER x noise
  // floor); the noise floor is the 20th percentile of frame RMS in the take.
  // Speech in the last END_WINDOW_MS is only recorded (speechAtEnd), never used to reject.
  QC: Object.freeze({
    SPEECH_MIN_RMS: 0.004,
    SPEECH_NOISE_MULTIPLIER: 3,
    NOISE_FLOOR_PERCENTILE: 0.2,
    SPEECH_MIN_MS: 300,
    CLIPPING_SAMPLE: 0.995,
    CLIPPING_RATE: 0.01,
    OVERRIDE_AFTER_FAILURES: 2,
    END_WINDOW_MS: 150
  }),

  // Same defaults as the legacy page. Device IDs are chosen in Settings (null = default).
  MEDIA_DEFAULTS: Object.freeze({
    resolution: '1080p',
    bitrate: 15000000,
    fps: 30,
    audioMode: 'raw',
    mirror: true,
    videoDeviceId: null,
    audioDeviceId: null
  }),
  // Option labels exactly as on the earlier page (also written into each sidecar).
  QUALITY_LABELS: Object.freeze({
    resolution: [['720p', '720p (1280×720) - Standard'], ['1080p', '1080p (1920×1080) - Recommended'], ['480p', '480p (854×480) - Standard'], ['360p', '360p (640×360) - Low Quality'], ['auto', 'Auto - Camera Default']],
    bitrate: [['8000000', '8 Mbps - Compatibility'], ['12000000', '12 Mbps - High Quality'], ['15000000', '15 Mbps - Research Quality'], ['25000000', '25 Mbps - Fast Motion'], ['40000000', '40 Mbps - Maximum Quality']],
    fps: [['30', '30 fps - Standard'], ['60', '60 fps - Fast Motion']],
    audio: [['raw', 'Raw - Disable Browser Processing'], ['fallback', 'Fallback - Browser Default']]
  }),
  RESOLUTIONS: Object.freeze({
    '360p': { width: 640, height: 360 },
    '480p': { width: 854, height: 480 },
    '720p': { width: 1280, height: 720 },
    '1080p': { width: 1920, height: 1080 }
  }),
  // AAC cannot take 192 kbps from a low-rate (e.g. 16 kHz Bluetooth) microphone; Chrome
  // then fails to start the encoder about 1 time in 4. Low-rate microphones get 64 kbps.
  AUDIO_BITRATE: 192000,
  AUDIO_BITRATE_LOW_RATE: 64000,
  AUDIO_FULL_RATE_HZ: 44100,

  // Hardware health (only real device failures end a take).
  HEALTH_INTERVAL_MS: 3000,
  VIDEO_GRACE_MS: 3000,
  VIDEO_STUCK_MS: 9000,
  VIDEO_NO_CHANGE_MS: 12000,
  VIDEO_SIGNATURE_DELTA: 0.03,

  STORAGE_BLOCK_RATIO: 0.78,
  ZIP_MAX_TAKES: 60,            // per ZIP file (about one part), so phones and tablets cope
  BACKUP_MAX_TAKES: 100,        // ZIP mode: recordings kept after a confirmed save (about two parts)
  SETTLE_TIMEOUT_MS: 20000,     // break/done screens stop waiting for the folder after this
  TIMER_SHOW_AFTER_MS: 20000,   // the recording timer appears only on long takes
  DB_NAME: 'VideoRecorderDB',   // shared with the legacy recorder; do not bump the version
  DB_VERSION: 2,
  STATE_DB_NAME: 'V2SAppState',
  STATE_DB_VERSION: 1,
  EVENT_LOG_LIMIT: 5000
});
