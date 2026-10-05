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
    toDark: 'Switch to dark mode',
    toLight: 'Switch to light mode',
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
    leadFirst: 'You will read short sentences out loud. The camera records your face and voice.',
    leadBack: 'Your place is saved. Carry on whenever you are ready.',
    stage1: 'Check your camera and microphone',
    stage2: 'Learn how it works and practise',
    stage3: 'Read the sentences, with rests between parts',
    begin: 'Begin',
    continue: 'Continue',
    participant: id => `Participant ${id}`,
    practice: 'Practice',
    practiceCount: (done, total) => `${done} of ${total} done`,
    part: (n, total) => `Part ${n} of ${total}`,
    partCount: (done, size) => `${done} of ${size} done`,
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
    title: 'Check your camera and microphone',
    cameraTitle: 'Camera',
    // The study's camera position (from the earlier page's checklist).
    cameraText: 'Place the camera below your chin and tilt it up, so your mouth, cheeks and throat are visible.',
    micTitle: 'Microphone',
    micText: 'Record a short test, then watch and listen to it.',
    change: 'Change',
    starting: 'Starting camera…',
    live: 'Live',
    defaultDevice: 'Default device',
    bluetooth: 'These look like Bluetooth headphones. They record lower-quality sound. Please use the built-in microphone.',
    useDevice: name => `Use ${name}`,
    testRecord: 'Record a 5-second test',
    testSay: 'Say: “Hello, this is my voice.”',
    testRecording: seconds => `Recording… ${seconds}`,
    testPlaying: 'Playing your test',
    testQuestion: 'Can you see your mouth, cheeks and throat, and hear yourself clearly?',
    testYes: 'Yes, continue',
    testAgain: 'Record again',
    testSilent: "We couldn't hear anything. Check the microphone, then record the test again.",
    testFailed: 'The test could not be recorded. Please try again.',
    help: 'Camera or microphone not working?'
  },

  howto: {
    title: 'How to record',
    step1: 'Press **Start** once — no need to hold it.',
    step2: 'When the sentence turns **green**, read it out loud.',
    step3: 'Press **Stop** when you finish.',
    redo: 'Read a word wrong? Press **Stop**, then **Redo** to record that sentence again.',
    keys: 'Keyboard: Space = Start and Stop · ← = Redo',
    mockStart: 'Start',
    mockStop: 'Stop',
    mockRedo: 'Redo',
    mockSentence: 'Read me out loud.',
    practice: 'Practice now',
    back: 'Back to recording',
    close: 'Close'
  },

  record: {
    statusReady: 'Not recording',
    statusStarting: 'Starting…',
    statusRecording: 'Recording',
    recordingHint: 'Read it out loud, then press Stop.',
    stillRecording: 'Still recording. Press Stop when you have finished.',
    statusSaving: 'Saving…',
    statusSaved: 'Saved',
    start: 'Start',
    stop: 'Stop',
    starting: 'Starting…',
    saving: 'Saving…',
    redo: 'Redo',
    redoCaption: sentence => `“${sentence}”`,
    redoThis: 'Record this sentence again',
    saved: 'Saved',
    cancelRedo: 'Cancel redo',
    toBreak: 'Take a break',
    toPracticeDone: 'Continue',
    toAllDone: 'Finish',
    partEndPart: n => `That was the last sentence of part ${n}.`,
    partEndAll: 'That was the very last sentence.',
    practiceOf: (n, total) => `Practice ${n} of ${total}`,
    partOf: (n, total) => `Part ${n} of ${total}`,
    sentenceOf: (n, total) => `Sentence ${n} of ${total}`,
    restIn: n => (n === 1 ? 'Break after this one' : `${n} to go before the break`),
    whereShort: (part, n, total) => `Part ${part} · ${n} of ${total}`,
    redoing: 'Press Start, then read this sentence again.'
  },

  // Practice coaching (first session only), shown above the sentence.
  coach: {
    step1: 'Start',
    step2: 'Read',
    step3: 'Stop',
    pressStart: 'Press Start once — no need to hold it.',
    readNow: 'Read the green sentence out loud. Then press Stop.',
    wellDone: 'Well done! That is all there is to it. Press Start for the next one.',
    again: 'Press Start, read the sentence, then press Stop.',
    tryRedo: sentence => `Now try Redo: press Redo to read “${sentence}” again.`,
    redoReady: 'Press Start, then read this sentence again.',
    redoRecording: 'Read it out loud. Then press Stop.',
    redoDone: 'That is how Redo works. Read a word wrong? Press Stop, then Redo. Now press Start.',
    reminder: 'Read a word wrong? Press Stop, then Redo.',
    practiceEnd: 'Practice done. Press Continue.'
  },

  feedback: {
    speechBeforeStart: 'Not recording yet. Press Start first, then read.',
    speechBeforeRedo: 'Not recording yet. Press Redo first.',
    afterHold: 'Press Start once, then read.',
    holdTip: 'Saved. Tip: let go of the button right after pressing it.',
    no_speech: "We couldn't hear you. Sit a little closer, press Start and read it again.",
    too_loud: 'Too loud. Move back a little, press Start and read it again.',
    no_audio: 'The microphone sent no sound. Press Start and read it again.',
    startFailed: "The recording didn't start. Please press Start again.",
    stoppedEarly: 'Recording stopped unexpectedly. Press Start and read it again.',
    hidden: 'Recording stopped because you left the page. Press Start and read it again.',
    timeout: 'That recording was over 1 minute. Press Start and read it again.',
    storeFailed: 'That recording could not be saved. Press Start and read it again.',
    storageFull: 'This device is almost full. Please save your recordings to go on.'
  },

  holdDialog: {
    title: 'Press once, then let go',
    body: 'Press Start once and let go. It records until you press Stop.',
    bodyDiscarded: 'That recording was not kept. Press Start once and let go — it records until you press Stop.',
    ok: 'OK'
  },

  endDialog: {
    title: 'End for today?',
    body: 'Your place is saved. You can carry on later.',
    keep: 'Keep going',
    end: 'End for today'
  },

  keepDialog: {
    title: "This sentence didn't work twice",
    body: reason => `${reason} You can try again, or keep this recording and go on.`,
    reasons: {
      no_speech: "We couldn't hear you.",
      too_loud: 'It was too loud.',
      no_audio: 'The microphone sent no sound.'
    },
    retry: 'Try again',
    keep: 'Keep it and go on'
  },

  practiceDone: {
    title: 'Practice done',
    body: (parts, size) => `The real sentences work the same way. There are ${parts} parts of ${size} sentences, and you can rest between parts.`,
    zipPrompt: 'After each part you save your recordings. Try it now with your practice recordings.',
    savedFolder: name => `Every recording is saved by itself in “${name}”. Nothing to do.`,
    next: 'Start part 1'
  },

  breakScreen: {
    title: n => `Part ${n} done`,
    lead: 'Well done. Take a rest.',
    savingFolder: 'Saving to the folder…',
    stillSaving: n => `Still saving ${n} recording${n === 1 ? '' : 's'} to the folder. You can go on; saving continues.`,
    folderProblem: n => `${n} recording${n === 1 ? ' is' : 's are'} not in the folder yet.`,
    allowFolder: 'Allow saving to the folder',
    zipPrompt: 'Save your recordings before you go on.',
    saveButton: 'Save recordings',
    saving: (i, n) => `Preparing file… ${i} of ${n}`,
    savedZip: 'Saved. You can go on.',
    moreToSave: (saved, left) => `${saved} saved. Save the other ${left} too.`,
    notConfirmed: 'Not saved yet. Your recordings are still on this device.',
    savePromptTitle: 'Save your recordings',
    continueTo: n => `Continue to part ${n}`,
    continue: 'Continue',
    finish: 'Finish for today',
    later: 'Save later and continue',
    makeRoom: hint => `This device is full. Check that the last saved file is there: ${hint} Then make room by removing its copy from this device.`,
    makeRoomYes: 'It is saved — make room',
    saveAgain: 'Save it again'
  },

  saveConfirm: {
    title: 'Did the file save?',
    ios: file => `In Safari, tap the ⬇ (downloads) button next to the web address. You should see “${file}”.`,
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
    deviceBody: 'Check that they are connected, then press Reconnect. Your progress is saved.',
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
    loadBody: 'Please reload this page. Your progress is saved.',
    reload: 'Reload',
    storeTitle: 'Recordings cannot be saved on this device',
    storeBody: 'The device may be full. Free up some space, then try again. Your progress is saved.'
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
    research: 'Research team',
    devices: 'Camera and microphone',
    camera: 'Camera',
    microphone: 'Microphone',
    devicesNote: 'Changes apply right away. Record a new test afterwards.',
    testAgain: 'Record a new test',
    actual: 'In use',
    display: 'Display',
    theme: 'Theme',
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
    participant: 'Sentences and progress',
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
    jumpLabel: total => `Go to sentence (1–${total})`,
    jump: 'Go',
    jumpInvalid: total => `Enter a number from 1 to ${total}.`,
    practiceAgain: 'Practise again',
    practiceConfirm: 'Go back to practice sentence 1 and show the coaching again? Afterwards recording continues from this sentence. Recordings are not deleted.',
    reset: 'Reset progress…',
    resetConfirm: 'Go back to the very first sentence (practice 1) and show How to record again? Recordings are not deleted. A sentence recorded again replaces its earlier recording, which moves to not_used.',
    resetConfirmNewRound: round => `Start again from the very first sentence (practice 1) and show How to record again? Recordings are not deleted. New recordings are round ${round} ("repeat${round}" in file names).`,
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
    backupsValue: n => `${n} recording${n === 1 ? '' : 's'} already saved in ZIP files`,
    backupNote: 'After a ZIP file is saved, its recordings stay on this device as backup copies (at most 100, removed first when space is needed).',
    saveBackups: 'Save backup copies again',
    deleteBackups: 'Delete backup copies…',
    deleteBackupsConfirm: n => `Delete ${n} backup copies from this device? They were saved in ZIP files.`,
    storage: 'Storage used',
    deleteCached: 'Clear storage (delete recordings on this device)…',
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
