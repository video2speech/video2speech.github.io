// Every sentence a participant or helper reads lives here, so wording can be
// reviewed and changed without touching the logic. Keep patient-facing lines short.
window.V2S = window.V2S || {};

V2S.copy = {
  loading: 'Loading…',

  setup: {
    eyebrow: 'First-time setup',
    title: 'Set up this device',
    lead: 'For the research team or a helper. You only do this once.',
    idLabel: 'Participant ID',
    idPlaceholder: 'e.g. P017',
    idHint: 'Letters, numbers and dashes.',
    idInvalid: 'Please use letters, numbers or dashes.',
    next: 'Continue',
    confirmTitle: 'Is this ID correct?',
    confirmYes: "Yes, it's correct",
    confirmChange: 'Change',
    legacyContinue: place => `Continue from ${place}`,
    legacyContinueDetail: 'This device already has progress from the earlier recording page.',
    legacyFresh: 'Start from the beginning',
    legacyFreshDetail: 'Choose this if that progress belongs to someone else.',
    folderTitle: 'Where should recordings be saved?',
    folderLead: 'Choose a folder on this computer. Every recording is saved there automatically.',
    folderChoose: 'Choose folder',
    folderZip: 'Save as ZIP files instead',
    folderFailed: 'That folder cannot be used. Please choose another one.'
  },

  welcome: {
    titleFirst: 'Welcome',
    titleBack: 'Welcome back',
    lead: 'Read each sentence aloud when it turns green.',
    start: 'Start',
    participant: id => `Participant ${id}`,
    warmup: 'Warm-up',
    warmupCount: (n, total) => `${n} of ${total}`,
    block: (b, total) => `Block ${b} of ${total}`,
    blockCount: (done, size) => `${done} of ${size} done`,
    allDone: 'All sentences are done',
    pending: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet.`,
    saveNow: 'Save now'
  },

  folder: {
    title: 'Allow saving to your folder',
    lead: name => `Recordings are saved in “${name}”. The browser needs your permission again.`,
    allow: 'Allow',
    choose: 'Choose a different folder',
    zip: 'Save as ZIP files instead',
    denied: 'Permission was not given. Press Allow, then choose Allow (or Allow on every visit).',
    failed: 'That folder cannot be used. Please choose another one.'
  },

  check: {
    title: 'Camera and microphone',
    face: 'Your face fits inside the outline',
    voice: 'Say hello. The waves should move.',
    ok: 'Looks good',
    help: 'Camera not working?',
    starting: 'Starting camera…'
  },

  record: {
    stateReady: 'Not recording',
    stateRecording: 'Recording',
    stateSaving: 'Saving…',
    stateSaved: 'Saved',
    start: 'Start',
    stop: 'Stop',
    saving: 'Saving…',
    redoLast: 'Redo last',
    startOver: 'Start over',
    finish: 'Finish for today',
    warmupOf: (n, total) => `Warm-up ${n} of ${total}`,
    sentenceOf: (n, total) => `Sentence ${n} of ${total}`,
    breakIn: n => (n === 1 ? 'Break after this one' : `Break in ${n}`),
    blockOf: (b, total) => `Block ${b} of ${total}`
  },

  saveStatus: {
    folder: name => `Saved to “${name}”`,
    folderSaving: 'Saving to folder…',
    folderProblem: 'Not saved to the folder — fix',
    device: 'Kept on this device until the break'
  },

  feedback: {
    no_speech: "We didn't hear you. Please read the sentence again.",
    no_audio: 'The microphone did not respond. Let’s try this sentence again.',
    too_loud: 'Too loud. Move the device a little farther away, then try again.',
    hold: "Please tap, don't hold. Let's start this sentence again.",
    timeout: 'Recording stopped after 1 minute. Let’s try this sentence again.',
    restarted: 'Starting this sentence again.',
    device: 'Recording stopped. Let’s try this sentence again.',
    hidden: 'Recording stopped because the page was in the background. Let’s try again.',
    speechBeforeStart: 'Not recording yet — press Start, then read.',
    redoLast: 'Recording the previous sentence again.',
    storageFull: 'This device is almost full. Please save your recordings first.'
  },

  keepDialog: {
    title: "This sentence didn't pass twice",
    body: reason => `${reason} You can try again, or keep this recording and continue.`,
    retry: 'Try again',
    keep: 'Keep it and continue'
  },

  // Shown once, on the first takes of a participant's first session.
  tutorial: {
    startFirst: 'Press Start, then read the sentence aloud.',
    stopFirst: 'Read it now. Press Stop when you finish.',
    redoLast: 'To redo the last sentence, press Redo last.',
    startOver: 'Made a mistake? Press Start over.',
    saveFolder: 'Recordings save to your folder automatically.',
    saveDevice: 'Recordings stay on this device. You save them at each break.'
  },

  warmupDone: {
    title: 'Warm-up done',
    body: 'Now the real sentences begin. Same steps as before.',
    next: 'Continue'
  },

  breakScreen: {
    title: b => `Block ${b} done`,
    lead: 'Take a short rest.',
    savedFolder: (n, name) => `${n} recording${n === 1 ? '' : 's'} saved in “${name}”.`,
    savingFolder: 'Saving to the folder…',
    folderProblem: n => `${n} recording${n === 1 ? ' is' : 's are'} not in the folder yet.`,
    allowFolder: 'Allow saving to the folder',
    zipPrompt: 'Save your recordings before you continue.',
    saveButton: 'Save recordings',
    saving: (i, n) => `Preparing file… ${i} of ${n}`,
    savedZip: 'Saved. You can continue.',
    notConfirmed: 'Not saved yet. Your recordings are still on this device.',
    savePromptTitle: 'Save your recordings',
    continue: 'Continue',
    finish: 'Finish for today',
    later: 'Save later'
  },

  saveConfirm: {
    title: 'Did the file save?',
    ios: file => `Tap the ⬇ button at the top of Safari. You should see “${file}”.`,
    android: file => `Check the download notification for “${file}”.`,
    desktop: file => `Check the browser’s downloads for “${file}”.`,
    yes: 'Yes, it saved',
    no: 'No, try again',
    unsure: 'Not sure'
  },

  done: {
    finishTitle: 'Great work today',
    finishBody: 'Your place is saved. You can close this page.',
    allTitle: 'All sentences are done',
    allBody: 'Thank you!',
    pending: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet.`,
    savedFolder: name => `All recordings are saved in “${name}”.`,
    save: 'Save recordings',
    again: 'Record more'
  },

  error: {
    deviceTitle: 'Camera or microphone stopped',
    deviceBody: 'This sometimes happens. Your progress is safe.',
    reconnect: 'Reconnect',
    permissionTitle: 'Camera and microphone are needed',
    permissionBody: 'Please allow the camera and microphone, then try again.',
    tryAgain: 'Try again',
    unsupportedTitle: 'This browser cannot record',
    unsupportedBody: 'Please open this page in Safari, Chrome or Edge.',
    loadTitle: 'Something went wrong',
    loadBody: 'Please reload this page. Your progress is safe.',
    reload: 'Reload'
  },

  help: {
    title: 'Allow camera and microphone',
    ios: 'In Safari, tap “aA” in the address bar, then Website Settings. Set Camera and Microphone to Allow. Then reload this page.',
    android: 'Tap the icon next to the web address, then Permissions. Allow Camera and Microphone. Then reload this page.',
    macSafari: 'In the Safari menu, choose Settings for This Website. Set Camera and Microphone to Allow. Then reload this page.',
    desktop: 'Click the camera icon in the address bar and choose Always allow. Then reload this page.',
    close: 'Close'
  },

  common: {
    ok: 'OK'
  }
};
