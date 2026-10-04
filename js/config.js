// Constants for the recorder. Thresholds and timings live here so they can be
// reviewed and tuned in one place.
window.V2S = window.V2S || {};

V2S.config = Object.freeze({
  APP_VERSION: '202',
  MATERIAL_VERSION: 'materials_v202',

  WARMUP_FILE: 'newset/aac_extra_5_sentences.txt',
  WARMUP_COUNT: 5,
  SETS: {
    '50words_350sentences': {
      label: '350 sentences (50-word vocabulary)',
      file: 'newset/350_nonrepeating_sentences.txt',
      count: 350,
      legacyProgressKey: '350_with_warmup_sentences'
    },
    'Open_300sentences': {
      label: '300 open sentences',
      file: 'newset/sentence_set_style.txt',
      count: 300
    }
  },
  DEFAULT_SET: '50words_350sentences',
  BLOCK_SIZE: 50,

  // Interaction (two presses: Start, then Stop).
  HOLD_MS: 1000,           // a press held this long aborts the take
  DEBOUNCE_MS: 300,        // presses closer than this are ignored (switch bounce)
  START_CUE_LEAD_MS: 150,  // start sound plays first so it is not recorded
  TAIL_MS: 700,            // keep recording this long after Stop (fixed; legacy page: 300 ms)
  MAX_TAKE_MS: 60000,      // a take this long is aborted and the sentence restarts
  SAVED_LABEL_MS: 1400,    // "Saved" shows on the next sentence without making anyone wait
  IDLE_SPEECH_HINT_MS: 500,     // speaking this long before Start shows a hint
  IDLE_SPEECH_HINT_COOLDOWN_MS: 6000,

  // Recording check (approved 2026-10-03). A frame counts as speech when its RMS is
  // at least max(SPEECH_MIN_RMS, SPEECH_NOISE_MULTIPLIER x noise floor); the noise
  // floor is the 20th percentile of frame RMS in the take.
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

  MEDIA_DEFAULTS: Object.freeze({
    resolution: '1080p',
    bitrate: 15000000,
    fps: 30,
    audioMode: 'raw',
    mirror: true
  }),
  RESOLUTIONS: Object.freeze({
    '360p': { width: 640, height: 360 },
    '480p': { width: 854, height: 480 },
    '720p': { width: 1280, height: 720 },
    '1080p': { width: 1920, height: 1080 }
  }),
  AUDIO_BITRATE: 192000,

  // Hardware health (only real device failures end a take).
  HEALTH_INTERVAL_MS: 3000,
  VIDEO_GRACE_MS: 3000,
  VIDEO_STUCK_MS: 9000,
  VIDEO_NO_CHANGE_MS: 12000,
  VIDEO_SIGNATURE_DELTA: 0.03,

  STORAGE_BLOCK_RATIO: 0.78,
  DB_NAME: 'VideoRecorderDB',   // shared with the legacy recorder; do not bump the version
  DB_VERSION: 2,
  STATE_DB_NAME: 'V2SAppState',
  STATE_DB_VERSION: 1,
  EVENT_LOG_LIMIT: 5000
});
