// Constants for the recorder. Thresholds and timings live here so they can be
// reviewed and tuned in one place.
window.V2S = window.V2S || {};

V2S.config = Object.freeze({
  APP_VERSION: '227',
  MATERIAL_VERSION: 'materials_v227',

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
    },
    'oct16-openVocab-350': {
      label: 'oct16-openVocab-350',
      about: '350 open-vocabulary sentences (2026-10-16)',
      file: 'newset/oct16-openVocab-350.txt',
      count: 350
    },
    'open-vocab-350-oct17': {
      label: 'open-vocab-350-oct17',
      about: '350 open-vocabulary sentences (2026-10-17 update)',
      file: 'newset/open-vocab-350-oct17.txt',
      count: 350
    },
    // v3 (owner, 2026-10-18): 10,000 sentences in 200 parts of 50. Parts 1-7 (350) are read
    // by everyone; then each participant goes on from their own part and round the rest
    // (after part 200 comes part 8). Participant n (SEMG<n+1>, enrolled n-th from 0) starts
    // at part 8 + 13n. 1-3 word sentences may appear up to 3 times.
    'open-vocab-v3': {
      label: 'open-vocab-v3',
      about: '10,000 open-vocabulary sentences (v3, 2026-10-18), read in rotation',
      file: 'newset/open-vocab-v3-10000.txt',
      count: 10000,
      shortRepeats: 3,
      rotation: Object.freeze({ sharedParts: 7, firstPart: 8, lastPart: 200, step: 13, idPattern: '^SEMG([1-9][0-9]*)$' })
    },
    // v3.1 (owner, 2026-10-18): v3 with contractions written out (I'll -> I will, it's -> it is, can't ->
    // cannot, won't -> will not; other n't, let's and possessive 's kept). Same rotation.
    'open-vocab-v3.1': {
      label: 'open-vocab-v3.1',
      about: '10,000 open-vocabulary sentences (v3.1, contractions written out), read in rotation',
      file: 'newset/open-vocab-v3.1-10000.txt',
      count: 10000,
      shortRepeats: 3,
      rotation: Object.freeze({ sharedParts: 7, firstPart: 8, lastPart: 200, step: 13, idPattern: '^SEMG([1-9][0-9]*)$' })
    },
    // v3.3 (owner, 2026-10-21): the reviewed 10,000 (material_design/open-vocab-v3.3). Same
    // rotation: parts 1-7 shared, then SEMG<n> goes on from part 8 + 13(n - 1). The default.
    // Patients never see the whole set: each day counts its parts from 1 ("Part 1 of 7"),
    // the sentences going on from where the last day stopped; after 7 parts, "All 7 parts
    // for today are done." and one more part at a time if they want (Part 8, 9, ...). No
    // Rainbow Passage with this set.
    'open-vocab-v3.3': {
      label: 'open-vocab-v3.3',
      about: 'Open-vocabulary sentences (v3.3, 2026-10-21), 7 parts a day',
      file: 'newset/open-vocab-v3.3-10000.txt',
      count: 10000,
      shortRepeats: 3,
      daily: Object.freeze({ parts: 7 }),
      rainbow: false,
      rotation: Object.freeze({ sharedParts: 7, firstPart: 8, lastPart: 200, step: 13, idPattern: '^SEMG([1-9][0-9]*)$' })
    }
  },
  // The set a device uses until one is chosen in Settings (owner, 2026-10-21: v3.3). A device
  // that chose a set keeps it; the question before each session shows which one it is.
  // (Automated tests of other things keep the earlier default through window.__V2S_TEST.)
  DEFAULT_SET: (window.__V2S_TEST && window.__V2S_TEST.defaultSet) || 'open-vocab-v3.3',
  // Before every session (Begin / Continue on Welcome), ask whether the sentence set is the
  // right one (owner, 2026-10-21).
  SET_CHECK: !(window.__V2S_TEST && window.__V2S_TEST.setCheck === false),
  // The Rainbow Passage: read once after the last sentence of every sentence set (owner,
  // 2026-10-16), one sentence at a time like any part. Its recordings go to
  // <ID>/<session>/rainbow/; its sidecars say which set it followed (rainbowAfterSet).
  // `firstSet`: before 2026-10-16 it followed only this set (a passage read then counts
  // for it).
  RAINBOW: Object.freeze({
    key: 'rainbow', file: 'newset/rainbow_passage.txt', count: 6, firstSet: '50words_350sentences',
    // Its size per screen: the largest up to `max` at which its longest sentence takes at
    // most `lines` lines of whole phrases (full lines, never one phrase a line).
    size: Object.freeze({
      phone: Object.freeze({ max: 28, lines: 5 }),
      flat: Object.freeze({ max: 26, lines: 5 }),
      tall: Object.freeze({ max: 36, lines: 4 }),
      wide: Object.freeze({ max: 40, lines: 3 })
    })
  }),
  BLOCK_SIZE: 50,              // one "part" of sentences between rests

  // Interaction (two presses: Start, then Stop).
  HOLD_MS: 1000,               // a press held this long aborts the take
  DEBOUNCE_MS: 300,            // presses closer than this are ignored (switch bounce, tremor)
  REVERSE_GUARD_MS: 1000,      // a press that would undo the one just made (Stop right after Start, cancelling a Redo just made) counts only after this: a double press acts once
  START_CUE_MAX_MS: 160,       // the start cue plays only if it is over this soon after the press (else no cue)
  START_SETTLE_MS: 80,         // green once the recorder has run this long without an error (instant failures are retried)
  START_TIMEOUT_MS: 600,       // the sentence turns green when the recorder reports it started; this is the fallback
  START_ATTEMPTS: 3,           // silent recorder restarts before the participant is told
  TAIL_MS: 700,                // keep recording this long after Stop (fixed; legacy page: 300 ms)
  MAX_TAKE_MS: (window.__V2S_TEST && window.__V2S_TEST.maxTakeMs) || 120000,         // a take this long is aborted and the sentence restarts (2 min: slow speakers, long passage sentences)
  STEP_MIN_MS: 1000,           // practice and a part's end: a step's instruction shows this long before a press counts
  SESSION_GAP_MS: 3 * 60 * 60 * 1000,   // recordings go to one session folder until a pause this long
  IDLE_SPEECH_HINT_MS: 500,    // speaking this long before Start shows a hint
  IDLE_SPEECH_HINT_COOLDOWN_MS: 6000,
  IDLE_SPEECH_GRACE_MS: 1500,  // after a take, speech in the first 1.5 s is not "reading before Start"
  ENTER_GUARD_MS: 400,         // presses this soon after the recording screen appears are ignored (a double press)
  SENTENCE_FLOOR: 18,          // the smallest sentence size when a long sentence would otherwise reach the card's kept areas
  ANSWER_ARM_MS: 1000,         // a final answer that sits where the last press was (the Rainbow Passage question) counts only after this
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
    // phones upright: 98% of sentences on at most two lines as they really wrap (a little
    // smaller, down to 28 px, before a third line); only the longest take three
    phone: Object.freeze({ min: 30, max: 36, lines: 3, twoLineShare: 0.98, twoLineMin: 28 }),
    flat: Object.freeze({ min: 26, max: 34, lines: 2 })    // phones sideways
  }),
  SENTENCE_ONE_LINE_SHARE: 0.9,
  SENTENCE_LINE_FILL: 0.9,             // a line may use at most 90% of the card width
  SENTENCE_MIN_CHARS_PER_LINE: 18,

  // Recording check (approved 2026-10-03; no_audio approved 2026-10-04). A frame counts as
  // speech when its RMS is at least max(SPEECH_MIN_RMS, SPEECH_NOISE_MULTIPLIER x noise
  // floor); the noise floor is the 20th percentile of frame RMS in the take.
  // Speech in the last END_WINDOW_MS is only recorded (speechAtEnd), never used to reject.
  // Since v220 (owner, 2026-10-15: "too strict, many patients cannot speak at a normal
  // volume"), the speech frames are only recorded; a take is too quiet, as on the page
  // before the redesign (v111), only when its RMS < QUIET_RMS and its peak < QUIET_PEAK.
  QC: Object.freeze({
    QUIET_RMS: 0.0025,
    QUIET_PEAK: 0.02,
    // The start cue plays at the press and recording starts at once, so a speaker's cue can
    // be in the first moments of a take: the quiet check leaves them out (v111 left out its
    // first 200 ms the same way).
    QUIET_SKIP_MS: 250,
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
  SETTLE_TIMEOUT_MS: 20000,     // break/done screens stop waiting for the folder after this
  TIMER_SHOW_AFTER_MS: (window.__V2S_TEST && window.__V2S_TEST.timerAfterMs) || 20000,   // the recording timer appears only on long takes
  DB_NAME: 'VideoRecorderDB',   // shared with the legacy recorder; do not bump the version
  DB_VERSION: 2,
  STATE_DB_NAME: 'V2SAppState',
  STATE_DB_VERSION: 1,
  EVENT_LOG_LIMIT: 5000
});
