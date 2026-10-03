// Every sentence a participant or helper reads lives here, so wording can be
// reviewed and changed without touching the logic. Keep patient-facing lines short.
window.V2S = window.V2S || {};

V2S.copy = {
  appName: 'Speech Recording',

  loading: 'Loading…',

  setup: {
    title: 'Set up this device',
    lead: 'For the research team or a helper. You only do this once.',
    idLabel: 'Participant ID',
    idPlaceholder: 'e.g. P017',
    idHint: 'Letters, numbers and dashes only.',
    idInvalid: 'Please enter an ID using letters, numbers or dashes.',
    next: 'Continue',
    confirmTitle: 'Is this ID correct?',
    confirmYes: "Yes, it's correct",
    confirmChange: 'Change',
    folderTitle: 'Where should recordings be saved?',
    folderLead: 'Choose a folder on this computer. Each recording is saved there automatically.',
    folderChoose: 'Choose folder',
    folderZip: 'Save as ZIP files instead',
    folderChosen: name => `Saving to “${name}”.`,
    folderFailed: 'That folder could not be used. Recordings will be saved as ZIP files.'
  },

  welcome: {
    titleFirst: 'Welcome',
    titleBack: 'Welcome back',
    lead: 'You will read short sentences aloud. We record your voice and face.',
    start: 'Start',
    participant: id => `Participant ${id}`,
    warmup: (n, total) => `Warm-up · sentence ${n} of ${total}`,
    block: (b, total) => `Block ${b} of ${total}`,
    blockProgress: (done, size) => `${done} of ${size} sentences done`,
    allDone: 'All sentences are done.',
    unsaved: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved to a file yet.`,
    saveNow: 'Save now',
    later: 'Later'
  },

  check: {
    title: 'Check camera and microphone',
    face: 'Place the camera so your face fits the outline.',
    voice: 'Say hello. The bar should move.',
    ok: 'Looks good',
    help: 'Camera not working?',
    starting: 'Starting camera…'
  },

  record: {
    statusReady: 'Not recording',
    statusRecording: 'Recording — read now',
    statusSaving: 'Saving…',
    statusSaved: 'Saved',
    start: 'Start',
    stop: 'Stop',
    saving: 'Saving…',
    redoLast: 'Redo last',
    startOver: 'Start over',
    finish: 'Finish for today',
    sentenceOf: (n, total) => `Sentence ${n} of ${total}`,
    warmupOf: (n, total) => `Warm-up ${n} of ${total}`,
    blockOf: (b, total) => `Block ${b} of ${total}`,
    untilBreak: n => (n === 1 ? '1 more until your break' : `${n} more until your break`),
    lastInBlock: 'Last sentence before your break',
    warmupLead: 'Warm-up sentences help you get comfortable.'
  },

  feedback: {
    no_speech: "We didn't hear you. Please read the sentence again.",
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

  tutorial: {
    readyFirst: 'Press Start, then read the sentence aloud.',
    recordingFirst: 'Read it now. Press Stop when you finish.',
    readySecond: 'Great. That’s all there is to it.',
    recordingSecond: 'Made a mistake? Press Start over.'
  },

  warmupDone: {
    title: 'Warm-up done',
    body: 'Next come the real sentences. Same steps as before.',
    next: 'Continue'
  },

  breakScreen: {
    title: b => `Block ${b} done`,
    lead: 'Take a short rest. Have some water if you like.',
    savedFolder: 'All recordings are saved in your folder.',
    savePrompt: 'Save your recordings before you continue.',
    saveButton: 'Save recordings',
    saving: (i, n) => `Preparing file… ${i} of ${n}`,
    savedZip: 'Saved. You can continue.',
    notConfirmed: 'Not saved yet. Your recordings are still on this device.',
    folderProblem: n => `${n} recording${n === 1 ? '' : 's'} could not be written to the folder. Save them as a ZIP file instead.`,
    continue: 'Continue',
    finish: 'Finish for today',
    later: 'Save later'
  },

  saveConfirm: {
    title: 'Did the file save?',
    ios: file => `Tap the ⬇ button at the top of Safari. You should see “${file}”.`,
    android: file => `Check the download notification for “${file}”.`,
    desktop: file => `Check your Downloads folder for “${file}”.`,
    yes: 'Yes, it saved',
    no: 'No, try again',
    unsure: 'Not sure'
  },

  done: {
    finishTitle: 'Great work today',
    finishBody: 'Your place is saved. You can close this page.',
    allTitle: 'All sentences are done',
    allBody: 'Thank you! Please make sure your recordings are saved.',
    unsaved: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved to a file yet.`,
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
    ok: 'OK',
    cancel: 'Cancel',
    close: 'Close'
  }
};
