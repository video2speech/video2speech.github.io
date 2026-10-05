// Every sentence a participant or helper reads lives here, so wording can be reviewed
// and changed without touching the logic.
// Rules: three verbs only (Start, Stop, Redo); "Practice" and "Part", never "warm-up"
// or "block"; at most two short sentences; say what happened and what to do.
// **double stars** mark words shown in bold (see ui.setRich).
window.V2S = window.V2S || {};

V2S.copy = {
  loading: 'Loading…',

  top: {
    finish: 'End for today',
    finishShort: 'End',
    help: 'How to record',
    settings: 'Settings'
  },

  setup: {
    eyebrow: 'Set up · for the research team or a helper',
    title: 'Who is recording?',
    lead: 'Enter the participant ID. You only do this once on this device.',
    idLabel: 'Participant ID',
    idPlaceholder: 'e.g. SEMG1',
    idHint: 'Letters, numbers and dashes. Saved in capitals.',
    idInvalid: 'Please use only letters, numbers or dashes.',
    next: 'Continue',
    confirmTitle: 'Is this ID correct?',
    confirmYes: "Yes, it’s correct",
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
    leadFirst: 'You will read short sentences out loud. The camera records your face and voice.',
    leadBack: 'Carry on where you left off.',
    stage1: 'Check your camera and microphone',
    stage2: 'Practise with 5 sentences',
    stage3: 'Read the sentences, with breaks',
    begin: 'Begin',
    continue: 'Continue',
    participant: id => `Participant ${id}`,
    practice: 'Practice',
    practiceCount: (done, total) => `${done} of ${total} done`,
    part: (n, total) => `Part ${n} of ${total}`,
    partCount: (done, size) => `${done} of ${size} sentences done`,
    allDone: 'All sentences are done',
    pending: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet.`,
    saveNow: 'Save now',
    partsDone: (n, total) => `${n} of ${total} parts done`,
    startsAt: 'Starts with sentence 1'
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

  // Two steps, one at a time: place the camera, then a test recording that plays back.
  check: {
    cameraStep: 'Step 1 of 2',
    // The study's camera position (from the earlier page's checklist).
    cameraTitle: 'Position the camera',
    // Name the thing to move: on a tablet or phone the camera is the device itself.
    // A computer's camera sits in the screen: tilting the screen back points it up.
    cameraText: device => (device === 'computer'
      ? 'Tilt the screen back until the camera sees your mouth, cheeks\u00a0and\u00a0throat. With a separate camera, put\u00a0it below your chin, tilted up.'
      : `Put the ${{ ipad: 'iPad', phone: 'phone', tablet: 'tablet' }[device] || 'camera'} below your chin and tilt it up, so your mouth, cheeks\u00a0and\u00a0throat are visible.`),
    next: 'Next',
    micStep: 'Step 2 of 2',
    micTitle: 'Test the microphone',
    micText: 'Press Record and say “Hello,\u00a0this\u00a0is\u00a0my\u00a0voice.” Then watch it back.',
    starting: 'Starting camera…',
    live: 'Live',
    defaultDevice: 'Default device',
    bluetooth: 'These look like Bluetooth headphones. They record lower-quality sound. Please use the built-in microphone.',
    useDevice: name => `Use ${name}`,
    micInUse: name => `Microphone: ${name}`,
    testRecord: 'Record a 5-second test',
    testSayLabel: 'Say:',
    testSay: '“Hello, this is my voice.”',
    testRecording: seconds => `Recording · ${seconds} s left`,
    testPlaying: 'Playing your test',
    testQuestion: 'Can you see your mouth, cheeks\u00a0and\u00a0throat, and hear yourself clearly?',
    testYes: 'Yes, continue',
    testAgain: 'No, try again',
    testReplay: 'Play it again',
    testHint: 'Can’t hear it? Turn the volume up and play it again.',
    testSilent: "We couldn’t hear anything. Check the microphone, then record the test again.",
    testFailed: 'The test could not be recorded. Please try again.',
    help: 'Camera or microphone not working?'
  },

  // How to record (the ? button): three steps in order, then how to fix a mistake.
  // On computers (keyboard) the keys are named; on touch screens, the buttons. k = true
  // on a computer.
  howto: {
    title: 'How to record',
    steps: k => (k
      ? ['Press **Space** once.', 'When the sentence turns\u00a0**green**, read it out loud.', 'Press **Space** again when you finish.']
      : ['Press **Start** once.', 'When the sentence turns\u00a0**green**, read it out loud.', 'Press **Stop** when you finish.']),
    fix: k => (k ? 'Read a word wrong? After you stop, press **←** (Redo) to record that sentence again.'
      : 'Read a word wrong? After **Stop**, press **Redo** to record that sentence again.'),
    close: 'Close'
  },

  record: {
    statusReady: 'Not recording',
    statusStarting: 'Starting…',
    statusRecording: 'Recording',
    statusSaving: 'Finishing…',
    statusSaved: 'Recorded',
    start: 'Start',
    stop: 'Stop',
    starting: 'Starting…',
    saving: 'Finishing…',
    redo: 'Redo',
    redoCaption: sentence => `“${sentence}”`,
    redoThis: 'Record this sentence again',
    saved: 'Recorded',
    cancelRedo: 'Cancel redo',
    toBreak: n => `Finish part ${n}`,
    toPracticeDone: 'Continue',
    toAllDone: 'Finish',
    partEndPart: n => `That was the\u00a0last\u00a0sentence of part\u00a0${n}.`,
    partEndAll: 'That was the very last sentence.',
    practiceOf: (n, total) => `Practice ${n} of ${total}`,
    partOf: (n, total) => `Part ${n} of ${total}`,
    sentenceOf: (n, total) => `Sentence ${n} of ${total}`,
    whereShort: (part, n, total) => `Part ${part} · ${n} of ${total}`,
    redoing: k => `Press ${k ? 'Space' : 'Start'}, then read this sentence again.`
  },

  // Practice coaching (first session only), just above Start. One instruction at a time:
  // `ack` says what just happened (small), `action` is the one thing to do now (large),
  // `detail` (rarely) says why. k = true on a computer (keys named instead of buttons).
  coach: {
    pressStart: k => `Press ${k ? 'Space' : 'Start'} once.`,
    noHold: 'No need to hold it.',
    readNow: k => `Read the green sentence out loud, then press ${k ? 'Space' : 'Stop'}.`,
    recordedFirst: 'Recorded. Every sentence works like this.',
    recorded: 'Recorded',
    nextSentence: k => `Next sentence: press ${k ? 'Space' : 'Start'}.`,
    tryRedo: k => (k ? 'Now press ← (Redo).' : 'Now press Redo, under Start.'),
    redoWhat: () => 'It records the sentence before this one again.',
    backToLast: 'Back to the last sentence.',
    startAgain: k => `Press ${k ? 'Space' : 'Start'} and read it again.`,
    redoDone: 'Recorded again. The old recording is replaced.',
    carryOn: k => `Now go on: press ${k ? 'Space' : 'Start'}.`,
    more: (n, k) => `${n} more to practise: press ${k ? 'Space' : 'Start'}.`,
    lastOne: k => `Last practice sentence: press ${k ? 'Space' : 'Start'}.`,
    practiceDone: 'Recorded.',
    lastPractice: 'That was the last practice\u00a0sentence.',
    pressContinue: k => (k ? 'Press Space to continue.' : 'Press Continue.')
  },

  // The same messages, short, for the practice coach (its next line says what to do).
  feedbackShort: {
    speechBeforeStart: 'Not recording yet.',
    speechBeforeRedo: 'Not recording yet.',
    afterHold: 'Press once, then let go.',
    no_speech: "We couldn’t hear you. Sit a little closer.",
    too_loud: 'Too loud. Move back a little.',
    no_audio: 'The microphone sent no sound.',
    startFailed: "The recording didn’t start.",
    stoppedEarly: 'Recording stopped unexpectedly.',
    hidden: 'Recording stopped because you left the page.',
    timeout: 'That recording was over 1 minute.',
    storeFailed: 'That recording could not be stored.',
    storageFull: 'This device is almost full.',
    holdTip: 'Recorded. Let go right after pressing.'
  },

  // Messages in the real recording (k = true on a computer: the keys are named). Two
  // short lines at most: what happened, then what to press.
  feedback: {
    speechBeforeStart: k => `Not recording yet. Press ${k ? 'Space' : 'Start'} first, then read.`,
    speechBeforeRedo: k => `Not recording yet. Press ${k ? '← (Redo)' : 'Redo'} first.`,
    afterHold: k => `Press ${k ? 'Space' : 'Start'} once, then read.`,
    holdTip: k => `Recorded. Tip: let go of the ${k ? 'key' : 'button'} right away.`,
    no_speech: k => `We couldn’t hear you. Sit closer, then press ${k ? 'Space' : 'Start'}.`,
    too_loud: k => `Too loud. Move back a little, then press ${k ? 'Space' : 'Start'}.`,
    no_audio: k => `The microphone sent no sound. Press ${k ? 'Space' : 'Start'} again.`,
    startFailed: k => `The recording didn’t start. Press ${k ? 'Space' : 'Start'} again.`,
    stoppedEarly: k => `Recording stopped unexpectedly. Press ${k ? 'Space' : 'Start'} again.`,
    hidden: k => `Recording stopped: you left the page. Press ${k ? 'Space' : 'Start'} again.`,
    timeout: k => `That recording was over a minute. Press ${k ? 'Space' : 'Start'} again.`,
    storeFailed: k => `That recording could not be stored. Press ${k ? 'Space' : 'Start'} again.`,
    storageFull: 'This device is almost full. Please save your recordings to go on.'
  },

  holdDialog: {
    title: 'Press once, then let go',
    body: k => (k ? 'Press Space once and let go. It records until you press Space again.'
      : 'Press Start once and let go. It records until you press Stop.'),
    bodyDiscarded: k => (k ? 'That recording was not kept. Press Space once and let go — it records until you press Space again.'
      : 'That recording was not kept. Press Start once and let go — it records until you press Stop.'),
    ok: 'OK'
  },

  endDialog: {
    title: 'End for today?',
    body: 'We’ll keep your place. You can carry on later.',
    keep: 'Keep going',
    end: 'End for today'
  },

  keepDialog: {
    title: "This sentence didn’t work twice",
    body: reason => `${reason} You can try again, or keep this recording and go on.`,
    reasons: {
      no_speech: "We couldn’t hear you.",
      too_loud: 'It was too loud.',
      no_audio: 'The microphone sent no sound.'
    },
    retry: 'Try again',
    keep: 'Keep it and go on'
  },

  // Saving is learnt here by doing it once (ZIP mode): the same steps as after every part.
  practiceDone: {
    title: 'Practice done',
    body: 'Now the real sentences. They work the same way.',
    saveFirst: 'Now save your practice recordings. You will do the same after each part.',
    saved: 'Your practice recordings are saved.',
    savedFolder: name => `Every recording is saved by itself in “${name}”.`,
    parts: (parts, size) => `${parts} parts of ${size} sentences. Rest\u00a0after\u00a0each\u00a0part, or stop and carry on another day.`,
    next: 'Continue to part 1'
  },

  breakScreen: {
    title: n => `Part ${n} done`,
    lead: 'Take a rest. Carry on when you are ready.',
    leadSave: 'Save your recordings, then take a rest.',
    partsDone: (n, total) => `${n} of ${total} parts done`,
    savingFolder: 'Saving…',
    stillSaving: n => `Still saving ${n} recording${n === 1 ? '' : 's'} to the folder. You can go on; saving continues.`,
    folderProblem: n => `${n} recording${n === 1 ? ' is' : 's are'} not in the folder yet.`,
    allowFolder: 'Allow saving to the folder',
    zipPrompt: 'Save your recordings before you go on.',
    saveButton: 'Save recordings',
    saving: (i, n) => `Preparing file… ${i} of ${n}`,
    savedZip: 'Your recordings are saved.',
    savedFolder: name => `Your recordings are saved in “${name}”.`,
    moreToSave: (saved, left) => `${saved} saved. Save the other ${left} too.`,
    notConfirmed: 'Not saved yet. Your recordings are still on this device.',
    savePromptTitle: 'Save your recordings',
    storageSaved: 'Your recordings are saved. You can go on.',
    // A full device: save, then (if still full) make room, then go on.
    makeRoomTitle: 'This device is full',
    roomTitle: 'Recordings saved',
    roomLead: 'You can go on.',
    continueTo: n => `Continue to part ${n}`,
    continue: 'Continue',
    finish: 'End for today',
    later: 'Continue without saving',
    makeRoom: hint => `Check that the last saved file is there: ${hint} Then make room by removing its copy from this device.`,
    makeRoomYes: 'It is saved — make room',
    saveAgain: 'Save it again'
  },

  // `name` is the start of the file name ("SEMG1_part01"); the time after it is left out.
  saveConfirm: {
    title: 'Did the file save?',
    ios: name => `If Safari asks, tap Download. Then tap ⬇ next to the web address and look for “${name}”.`,
    iosFind: name => `Tap ⬇ next to the web address and look for “${name}”.`,
    android: name => `Open the download notification and look for “${name}”.`,
    desktop: name => `Open the browser’s downloads and look for “${name}”.`,
    yes: 'Yes, I see it',
    no: 'Save it again',
    unsure: 'Not sure'
  },

  done: {
    finishTitle: 'Great work today',
    finishBody: 'We’ll keep your place on this device. You can close this page.',
    allTitle: 'All sentences done',
    allBody: 'Thank you so much!',
    pending: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet.`,
    saveFirst: 'Please save your recordings before you close this page.',
    savedFolder: name => `All recordings are saved in “${name}”.`,
    savedZip: 'All recordings are saved.',
    save: 'Save recordings',
    again: 'Record more'
  },

  error: {
    deviceTitle: 'Camera or microphone disconnected',
    deviceBody: 'Check that they are connected, then press Reconnect. We’ll keep your place.',
    reconnect: 'Reconnect',
    startTitle: 'Recording cannot start',
    startBody: 'This often happens with Bluetooth headphones. Choose the built-in microphone, then try again.',
    chooseMic: 'Choose microphone',
    permissionTitle: 'Camera and microphone are needed',
    permissionBody: 'Please allow the camera and microphone, then try again.',
    tryAgain: 'Try again',
    unsupportedTitle: 'This browser cannot record',
    unsupportedBody: 'Please open this page in Safari, Chrome or Edge.',
    loadTitle: 'Something went wrong',
    loadBody: 'Please reload this page. We’ll keep your place.',
    reload: 'Reload',
    storeTitle: 'Recordings cannot be saved on this device',
    storeBody: 'The device may be full. Free up some space, then try again. We’ll keep your place.'
  },

  // A second copy of the page (another tab or window) on the same device.
  tab: {
    title: 'Already open in another tab',
    body: 'This page is open in another tab or window. Please use only one.',
    useHere: 'Use this tab instead',
    movedTitle: 'Opened in another tab',
    movedBody: 'Recording continues in the other tab. You can close this one.'
  },

  help: {
    title: 'Allow camera and microphone',
    ios: 'In Safari, tap “aA” in the address bar, then Website Settings. Set Camera and Microphone to Allow. Then reload this page.',
    android: 'Tap the icon next to the web address, then Permissions. Allow Camera and Microphone. Then reload this page.',
    macSafari: 'In the Safari menu, choose Settings for This Website. Set Camera and Microphone to Allow. Then reload this page.',
    desktop: 'Click the camera icon in the address bar and choose Always allow. Then reload this page.',
    close: 'Close'
  },

  settings: {
    title: 'Settings',
    done: 'Done',
    back: 'Settings',
    research: 'Research team',
    allSaved: 'All saved',
    moveTitle: 'Go to a sentence',
    practiceTitle: 'Practice',
    holdTitle: 'Holding the button',
    notSaved: n => `${n} not saved`,
    devices: 'Camera and microphone',
    camera: 'Camera',
    microphone: 'Microphone',
    devicesNote: 'Changes apply right away. Record a new test afterwards.',
    testAgain: 'Record a new test',
    actual: 'In use',
    display: 'Display',
    theme: 'Appearance',
    light: 'Light',
    dark: 'Dark',
    quality: 'Recording quality',
    qualityNote: 'Same defaults as the earlier page. Changes apply when the camera restarts.',
    resolution: 'Recording resolution',
    bitrate: 'Recording quality',
    fps: 'Recording frame rate',
    audio: 'Audio mode',
    audioRaw: 'Raw - Disable Browser Processing',
    audioBrowser: 'Fallback - Browser Default',
    mirror: 'Mirror video display',
    applyQuality: 'Apply and restart camera',
    participant: 'Sentences & progress',
    participantId: 'Participant',
    set: 'Sentence set',
    previous: '← Previous sentence',
    next: 'Next sentence (skip) →',
    skipConfirm: 'Skip this sentence? It will not be recorded now. You can come back to it with Previous or Go to.',
    skipPractice: 'Skip practice (bypass warm-up)',
    holdLabel: 'Held-press limit',
    hold1: '1 second (default)',
    hold2: '2 seconds',
    hold3: '3 seconds',
    holdNote: 'A press held this long counts as holding the button. Raise it for people who let go slowly.',
    position: 'Position',
    switchParticipant: 'Switch participant…',
    switchPrompt: 'New participant ID (letters, numbers, dashes)',
    switchInvalid: 'That ID is not valid.',
    useSet: 'Use this set',
    setConfirm: 'Switch the sentence set? Progress is kept separately for each set.',
    jumpLabel: () => 'Go to sentence',
    jump: 'Go',
    jumpInvalid: total => `Enter a number from 1 to ${total}.`,
    practiceAgain: 'Practise again',
    practiceConfirm: 'Go back to practice sentence 1 and show the coaching again? Afterwards recording continues from this sentence. Recordings are not deleted.',
    reset: 'Reset progress…',
    resetConfirm: 'Go back to the very first sentence (practice 1) and coach the practice again? Recordings are not deleted. A sentence recorded again replaces its earlier recording, which moves to not_used.',
    resetConfirmNewRound: round => `Start again from the very first sentence (practice 1) and coach the practice again? Recordings are not deleted. New recordings are round ${round} ("repeat${round}" in file names).`,
    roundNote: round => `Round ${round} ("repeat${round}" in file names). Within a round, a sentence recorded again replaces its earlier recording (moved to not_used). After the last sentence, anything recorded starts the next round.`,
    saving: 'Saving',
    mode: 'Saved to',
    modeFolder: name => `Folder “${name}”`,
    modeZip: 'ZIP files',
    folderAccess: 'Folder access',
    chooseFolder: 'Choose folder…',
    useZip: 'Use ZIP files',
    saveNow: 'Save all recordings now',
    cached: 'Not saved yet',
    cachedValue: n => `${n} recording${n === 1 ? '' : 's'}`,
    backups: 'Backup copies',
    backupsValue: n => String(n),
    backupNote: 'After a ZIP file is saved, its recordings stay on this device as backup copies until space is needed.',
    saveBackups: 'Save backup copies again',
    deleteBackups: 'Delete backup copies…',
    deleteBackupsConfirm: n => `Delete ${n} backup copies from this device? They were saved in ZIP files.`,
    storage: 'Storage used',
    deleteCached: 'Clear storage…',
    deleteCachedNote: 'Clear storage deletes the recordings kept on this device. Recordings that are not saved yet cannot be deleted: save them first.',
    deleteUnsaved: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet. Save them first (Save all recordings now), then clear storage.`,
    nothingStored: 'There are no recordings on this device.',
    nothingToSave: 'All recordings are already saved.',
    deleteConfirm: (n, unsaved) => (unsaved
      ? `Permanently delete ${n} recordings from this device? ${unsaved} of them are NOT saved anywhere yet.`
      : `Permanently delete ${n} recordings from this device? They are all saved.`),
    written: (ok, failed) => `Saved: ${ok}. Not saved: ${failed}.`,
    folderNotAllowed: 'The browser did not allow access to the folder.',
    folderFailed: 'That folder could not be used.',
    noFolderSupport: 'This browser cannot save to a folder; recordings are saved as ZIP files.',
    account: 'Account',
    signOut: 'Sign out (log out)',
    signOutConfirm: 'Sign out of this device? Recordings that are not saved stay on this device.',
    about: 'About',
    version: 'Version',
    session: 'Session',
    downloadLog: 'Download event log',
    notRecording: 'Settings are available when you are not recording.',
    confirm: 'Yes, continue',
    cancel: 'Cancel'
  },

  common: {
    ok: 'OK',
    cancel: 'Cancel'
  }
};
