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
    legacyTitle: 'Earlier progress on this device',
    legacyLead: 'Recordings were made on this device before IDs were used. Are they this participant’s?',
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

  // The one thing to remember. Shown before the practice, after it, and when coming back.
  // Each key says what it is for, and what to do after a mistake (owner, 2026-10-15).
  rule: k => (k
    ? 'Press **Space** to start recording, then read the **green**\u00a0sentence out loud.\nPress **Space** again to stop recording.\nMade a mistake? Stop recording first, then press **←** to record that sentence again.'
    : 'Tap **Start** to start recording, then read the **green**\u00a0sentence out loud.\nTap **Stop** to stop recording.\nMade a mistake? Tap **Stop** first, then tap **Redo last sentence** to record that sentence again.'),

  // Before the practice (first time only).
  // After the last sentence of the 350-sentence set, once: the Rainbow Passage?
  rainbow: {
    eyebrow: parts => `All ${parts} parts done`,
    title: 'Do you want to read the Rainbow\u00a0Passage?',
    lead: n => `A short story in ${n} sentences, one at a time, as\u00a0before.`,
    yes: 'Yes, read it',
    no: 'No, finish'
  },

  // A returning participant, after the check: how it works, one line at a time.
  review: {
    eyebrow: 'Welcome back',
    title: 'How it works',
    lines: k => (k
      ? ['Press **Space** to start recording. The sentence turns green: read it out loud.',
        'Press **Space** again to stop recording. The next sentence appears.',
        'Made a mistake? Press **Space** to stop recording first, then press **←** to record that sentence again.']
      : ['Tap **Start** to start recording. The sentence turns green: read it out loud.',
        'Tap **Stop** to stop recording. The next sentence appears.',
        'Made a mistake? Tap **Stop** first, then tap **Redo last sentence** (top left) to record that sentence again.']),
    eyebrowPractice: 'How to record',
    count: (n, total) => `${n} of ${total}`,
    titlePractice: 'Before the real sentences',
    next: 'Got it',
    last: 'Got it — show the sentence'
  },

  // Before part 1: only to get ready.
  ready: {
    eyebrow: 'The real sentences',
    title: (n, total) => `Part ${n} of ${total}`,
    lead: n => `${n} sentences in each part. After each part you can rest, or stop for\u00a0today.`,
    start: (n, resume) => (resume ? `Continue part ${n}` : `Start part ${n}`)
  },

  intro: {
    eyebrow: 'Practice',
    title: 'One thing to remember',
    lead: n => (n === 1 ? 'Try it now with one short sentence. It is only for practice.'
      : `Try it now with ${n} short sentences. They are only for practice.`),
    start: 'Begin practice'
  },

  welcome: {
    titleFirst: 'Welcome',
    titleBack: 'Welcome back',
    leadFirst: 'You will read short sentences out loud. The camera records your face and voice.',
    leadBack: 'Carry on where you left off.',
    stage1: 'Check your camera and microphone',
    stage2: 'Practice with 5 sentences',
    stage3: 'Read the sentences, with breaks',
    begin: 'Begin',
    continue: 'Continue',
    participant: id => `Participant ${id}`,
    practice: 'Practice',
    practiceCount: (done, total) => `${done} of ${total} done`,
    part: (n, total) => `Part ${n} of ${total}`,
    partCount: (done, size) => `${done} of ${size} sentences done`,
    allDone: 'All sentences are done',
    allParts: parts => `All ${parts} parts done`,
    rainbow: 'Rainbow Passage',
    doneTitle: 'All sentences done',
    doneLead: 'Thank you! There is nothing more to record. You can close this page.',
    doneLeadUnsaved: 'Thank you! There is nothing more to record.',
    saveFirst: 'Save recordings',
    pending: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet.`,
    saveNow: 'Save now',
    partsDone: (n, total) => `${n} of ${total} parts done`,
    sentenceOf: (n, total) => `Sentence ${n} of ${total}`
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
    // Participants only need their face inside the oval (owner, 2026-10-05).
    cameraTitle: 'Position the camera',
    cameraText: 'Put your face inside the oval.',
    next: 'Next',
    micStep: 'Step 2 of 2',
    // One purpose: check that we can hear you. What to do, then the words to say.
    micTitle: 'Check that we can hear you',
    micText: 'Start the test, then say out\u00a0loud:',
    micTextTouch: 'Start the test, then say out\u00a0loud:',
    starting: 'Starting camera…',
    live: 'Live',
    defaultDevice: 'Default device',
    bluetooth: 'These look like Bluetooth headphones, which record lower-quality sound. Please use the built-in microphone.',
    useDevice: name => `Use ${name}`,
    testRecord: 'Start the 5-second test',
    testSayLabel: 'Recording — say it now',
    testSay: '“Hello, this is my voice.”',
    testRecording: 'Recording',
    testPlaying: 'Playing your test',
    askTitle: 'Did the test work?',
    testQuestion: 'Could you see your face and hear your voice clearly?',
    testYes: 'Yes, continue',
    testAgain: 'No, try again',
    testReplay: 'Play it again',
    testHint: 'Can’t hear it? Turn the volume up and play it again.',
    // Nothing heard: the title says so; three equal choices (owner, 2026-10-15: many
    // patients have a speech impairment, so name the condition, not "your voice").
    silentTitle: 'We couldn’t hear you',
    failedTitle: 'The test did not record',
    testSilent: 'The test recording had no sound. Choose what fits you:',
    retryTitle: 'Try again',
    retryText: 'Make sure nothing covers the microphone, come a little closer and speak\u00a0up.',
    chooseMicTitle: 'Use another microphone',
    chooseMicText: 'Pick a different microphone, for example the one built into this\u00a0device.',
    noVoiceChoiceTitle: 'My condition stops me making enough sound',
    noVoiceChoiceText: 'For example after a laryngectomy, or a voice too weak to\u00a0hear.',
    noVoiceTitle: 'Record without sound?',
    noVoiceBody: 'Your face is still recorded on video. The app will not ask you to speak up again. You can change this in Settings.',
    noVoiceYes: 'Yes, record without sound',
    keepHeadphones: 'Keep using these headphones',
    testFailed: 'Something went wrong while recording the test. Choose what to do:',
    help: 'Camera or microphone not working?'
  },

  // How to record (the ? button): three steps in order, then how to fix a mistake.
  // On computers (keyboard) the keys are named; on touch screens, the buttons. k = true
  // on a computer.
  howto: {
    title: 'How to record',
    steps: k => (k
      ? ['Press **Space** once to start recording.', 'Read the **green** sentence out\u00a0loud.', 'Press **Space** again to stop recording.']
      : ['Tap **Start** once to start recording.', 'Read the **green** sentence out\u00a0loud.', 'Tap **Stop** to stop recording.']),
    fix: k => (k ? 'Made a mistake? Press **Space** to stop recording first, then press **←** to\u00a0record that sentence again.'
      : 'Made a mistake? Tap **Stop** first, then tap **Redo last sentence** (at the top) to\u00a0record that sentence again.'),
    close: 'Close'
  },

  record: {
    recordingSign: 'Recording',
    start: 'Start',
    stop: 'Stop',
    starting: 'Starting…',
    saving: 'Finishing…',
    redo: 'Redo last sentence',
    redoQueued: 'After saving, this one again',
    redoCaption: sentence => `“${sentence}”`,
    redoThis: 'This sentence again',
    cancelRedo: 'Cancel redo',
    toBreak: n => `Finish part ${n}`,
    toPracticeDone: 'Continue',
    toNext: 'Continue',
    donePractice: 'Practice done.',
    donePart: n => `Part ${n} done.`,
    doneAll: n => `All ${n} parts done.`,
    doneRainbow: 'Rainbow Passage done.',
    pressEnterGo: 'Press Space to continue',
    pressBreak: k => (k ? 'Press Space to go to your break' : 'Tap Go to break'),
    toBreakShort: 'Go to break',
    readyHint: k => (k ? 'Press Space to start, then read.' : 'Tap Start to start, then read.'),
    endHint: k => (k ? 'Press Space to end recording.' : 'Tap Stop to end recording.'),
    tailBreak: 'to go to your break',
    tailGo: 'to continue',
    tapGo: label => `Tap ${label}`,
    passageNext: n => `Next: the Rainbow Passage, ${n} sentences.`,
    toAllDone: 'Finish',
    partEndPart: n => `That was the\u00a0last\u00a0sentence of part\u00a0${n}.`,
    partEndAll: 'That was the very last sentence.',
    partEndRainbow: 'That was the last sentence of the Rainbow\u00a0Passage.',
    rainbowOf: (n, total) => `Rainbow Passage · ${n} of ${total}`,
    rainbowShort: (n, total) => `Rainbow · ${n} of ${total}`,
    practiceOf: (n, total) => `Practice ${n} of ${total}`,
    partOf: (n, total) => `Part ${n} of ${total}`,
    sentenceOf: (n, total) => `Sentence ${n} of ${total}`,
    whereShort: (part, n, total) => `Part ${part} · ${n} of ${total}`,
    // The narrowest screens (a phone with larger text): only the place in the part.
    whereTiny: (n, total) => `${n} of ${total}`,
    redoing: k => `Press ${k ? 'Space' : 'Start'}, then read this sentence again.`
  },

  // Practice coaching (first session only), just above Start. One instruction at a time:
  // `ack` says what just happened (small), `action` is the one thing to do now (large),
  // `detail` (rarely) says why. k = true on a computer (keys named instead of buttons).
  coach: {
    // The floating guide's parts (session.js coachView).
    steps: {
      startLabel: 'Step 1 · Start recording',
      toStart: 'to start recording',
      startDetail: () => 'Then read the green sentence out loud.',
      endLabel: 'Read the sentence out loud',
      endVerb: k => (k ? 'When you finish, press' : 'When you finish, tap'),
      toEnd: 'to end recording',
      againLabel: 'Step 2 · Every sentence',
      againDetail: 'Every sentence works the same way.',
      redoLabel: 'Step 3 · Redo last sentence',
      redoTailKeys: 'to record the last sentence again',
      redoTailTouch: 'to record it again',
      redoDetail: k => (k ? 'After a mistake: end recording first, then press ←.' : 'After a mistake: tap Stop first, then Redo.'),
      redoingLabel: 'Redo',
      readAgain: 'and read it again',
      redoDoneLabel: 'Redo done',
      redoDoneDetail: 'You can redo any sentence like this.',
      forNext: 'for the next sentence'
    },
    pressStart: k => (k ? 'Press Space to start' : 'Tap Start to begin'),
    startWhat: k => (k ? 'Recording starts at once and the sentence appears in green. Read it out loud, then press Space again.'
      : 'Recording starts at once and the sentence appears in green. Read it out loud, then tap Stop.'),
    readNow: k => (k ? 'Read it out loud. When you finish, press Space to stop recording.' : 'Read it out loud. When you finish, tap Stop to stop recording.'),
    recordedFirst: 'That’s it. Every sentence works like this.',
    nextSentence: k => (k ? 'Press Space for the next sentence' : 'Tap Start for the next sentence'),
    // The Redo lesson: nothing went wrong; it shows how to fix a misread sentence.
    redoLesson: 'This is only practice — nothing went wrong.',
    tryRedo: k => (k ? 'Now press ← to redo the last sentence' : 'Now tap “Redo last sentence” at the top'),
    redoWhat: () => 'Redo records the sentence you just read once more. Made a mistake while reading? Stop recording first, then Redo.',
    backToLast: 'This is the sentence before.',
    startAgain: k => (k ? 'Press Space and read it again' : 'Tap Start and read it again'),
    cancelHint: k => (k ? 'Pressed ← by mistake? Press → to go back.' : 'Tapped Redo by mistake? Tap Cancel redo.'),
    redoDone: 'That’s how Redo works.',
    carryOn: k => (k ? 'Press Space for the next sentence' : 'Tap Start for the next sentence'),
    more: (n, k) => (k ? `${n} more. Press Space to start` : `${n} more. Tap Start to begin`),
    lastOne: k => (k ? 'Last one. Press Space to start' : 'Last one. Tap Start to begin'),
    lastPractice: 'That was the last practice\u00a0sentence.',
    pressContinue: k => (k ? 'Press Space to continue.' : 'Press Continue.')
  },

  // The same messages, short, for the practice coach (its next line says what to do).
  feedbackShort: {
    speechBeforeStart: 'Not recording yet.',
    afterHold: 'Press once, then let go.',
    no_speech: "We couldn’t hear you. Sit a little closer.",
    too_loud: 'Too loud. Move back a little.',
    no_audio: 'The microphone sent no sound.',
    startFailed: "The recording didn’t start.",
    stoppedEarly: 'Recording stopped unexpectedly.',
    hidden: 'Recording stopped because you left the page.',
    timeout: 'That recording was over 2 minutes.',
    storeFailed: 'That recording could not be stored.',
    storageFull: 'This device is almost full.',
    holdTip: 'Let go right after pressing.'
  },

  // Messages in the real recording (k = true on a computer: the keys are named). Two
  // short lines at most: what happened, then what to press.
  feedback: {
    speechBeforeStart: k => `Not recording yet. Press ${k ? 'Space' : 'Start'} first, then read.`,
    afterHold: k => `Press ${k ? 'Space' : 'Start'} once, then read.`,
    holdTip: k => `Tip: let go of the ${k ? 'key' : 'button'} right away.`,
    no_speech: k => `We couldn’t hear that. Sit closer, then ${k ? 'press Space' : 'tap Start'} and read it again.`,
    too_loud: k => `Too loud. Move back a little, then press ${k ? 'Space' : 'Start'}.`,
    no_audio: k => `The microphone sent no sound. Press ${k ? 'Space' : 'Start'} again.`,
    startFailed: k => `The recording didn’t start. Press ${k ? 'Space' : 'Start'} again.`,
    stoppedEarly: k => `Recording stopped unexpectedly. Press ${k ? 'Space' : 'Start'} again.`,
    hidden: k => `Recording stopped: you left the page. Press ${k ? 'Space' : 'Start'} again.`,
    timeout: k => `That recording was over 2 minutes. Press ${k ? 'Space' : 'Start'} again.`,
    storeFailed: k => `That recording could not be stored. Press ${k ? 'Space' : 'Start'} again.`,
    storageFull: 'This device is almost full. Please save your recordings to go on.'
  },

  holdDialog: {
    title: 'Press once, then let go',
    body: k => (k ? 'Press Space once and let go. It records until you press Space again.'
      : 'Tap Start once and let go. It records until you tap Stop.'),
    bodyDiscarded: k => (k ? 'That recording was not kept. Press Space once and let go — it records until you press Space again.'
      : 'That recording was not kept. Tap Start once and let go — it records until you tap Stop.'),
    ok: 'OK',
    longer: 'I need longer to let go'
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
    body: 'Next, the real sentences: start recording, then read.',
    saveFirst: 'Save your practice recordings now. You will do this after every part, so nothing is\u00a0lost.',
    saved: 'Your practice recordings are saved.',
    savedFolder: name => `Every recording is saved by itself in “${name}”.`,
    parts: (parts, size) => `${parts} parts of ${size} sentences. You can stop after any\u00a0part.`,
    next: 'Continue to part 1',
    continue: 'Continue'
  },

  breakScreen: {
    title: n => `Part ${n} done`,
    lead: 'Take a rest. Carry on when you are ready.',
    leadSave: 'First, save the recordings from this\u00a0part.',
    partsDone: (n, total) => `${n} of ${total} parts done`,
    savingFolder: 'Checking the last recording is saved…',
    stillSaving: n => `Still saving ${n} recording${n === 1 ? '' : 's'} to the folder. You can go on; saving continues.`,
    folderProblem: n => `${n} recording${n === 1 ? ' is' : 's are'} not in the folder yet.`,
    allowFolder: 'Allow saving to the folder',
    zipPrompt: 'Save your recordings before you go on.',
    saveButton: 'Save recordings',
    saving: (i, n) => `Preparing file… ${i} of ${n}`,
    savedZip: 'Your recordings are saved.',
    savedFolder: name => `Your recordings are saved in “${name}”.`,
    moreToSave: (saved, left) => `${saved} saved. Save the other ${left} too.`,
    notConfirmed: 'Let’s save them again to be sure. Your recordings are still on this device.',
    savePromptTitle: 'Save your recordings',
    storageSaved: 'Your recordings are saved. You can go on.',
    // A full device: save, then (if still full) make room, then go on.
    makeRoomTitle: 'Make room on this device',
    roomTitle: 'Recordings saved',
    roomLead: 'You can go on.',
    continueTo: n => `Continue to part ${n}`,
    continue: 'Continue',
    finish: 'End for today',
    later: 'Continue without saving',
    makeRoom: hint => `Check that the last saved file is there: ${hint} Then make room by removing its copy from this device.`,
    makeRoomYes: 'It is saved — make room',
    makeRoomAsk: 'Remove the copy from this device?',
    makeRoomAskBody: 'Only if you found the saved file. The file itself is not changed.',
    makeRoomRemove: 'Remove the copy',
    laterAsk: 'Continue without saving?',
    laterAskBody: 'Your recordings stay on this device. You can save them at the next break.',
    laterSave: 'Save now',
    laterGo: 'Continue without saving',
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
    allBody: 'Thank you so much! You can close this page.',
    pending: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet.`,
    saveFirst: 'Please save your recordings before you close this page.',
    savedFolder: name => `All recordings are saved in “${name}”.`,
    savedZip: 'All recordings are saved.',
    save: 'Save recordings',
    again: 'Record more'
  },

  error: {
    deviceTitle: 'Camera or microphone disconnected',
    deviceBody: 'Close other apps that use the camera or microphone, then press Reconnect. We’ll keep your place.',
    reconnect: 'Reconnect',
    startTitle: 'Recording cannot start',
    startBody: 'This often happens with Bluetooth headphones. Choose the built-in\u00a0microphone, then try again.',
    chooseMic: 'Choose microphone',
    permissionTitle: 'Camera and microphone are needed',
    permissionBody: 'Please allow the camera and microphone, then reload this page.',
    tryAgain: 'Try again',
    unsupportedTitle: 'This browser cannot record',
    unsupportedBody: 'Please open this page in Safari, Chrome or Edge: copy the link, then paste it there.',
    copyLink: 'Copy link',
    linkCopied: 'Link copied',
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

  // The check's help when the picture already works: what else to check.
  liveHelp: {
    title: 'Camera or microphone not working?',
    body: 'Check that nothing covers the camera or the microphone and that the sound is not muted. To use another camera or microphone, choose it below.',
    choose: 'Choose camera or microphone',
    close: 'Close'
  },

  help: {
    title: 'Allow camera and microphone',
    ios: 'In Safari, tap “aA” in the address bar, then Website Settings. Set Camera and Microphone to Allow.',
    android: 'Tap the icon next to the web address, then Permissions. Allow Camera and Microphone.',
    macSafari: 'In the Safari menu, choose Settings for This Website. Set Camera and Microphone to Allow.',
    desktop: 'Click the camera icon in the address bar and choose Always allow.',
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
    practiceAgain: 'Practice again',
    practiceConfirm: 'Go back to practice sentence 1 and show the coaching again? Afterwards recording continues from this sentence. Recordings are not deleted.',
    participantNote: 'Each participant’s recordings, progress and settings stay on this device.',
    allSavedLong: 'All recordings are saved',
    notSavedLong: n => `${n} recording${n === 1 ? ' is' : 's are'} not saved yet`,
    savingOptions: 'Saving options',
    forParticipant: id => `For ${id}`,
    allowSilent: 'Allow recordings without voice',
    forParticipantNote: 'A press held this long counts as holding the button. Without voice (e.g. after a laryngectomy): a take with no sound is kept, not asked again. These settings stay with this participant.',
    device: 'This device',
    newParticipant: 'New participant…',
    newParticipantNote: id => `Back to Set up for the next participant. ${id}’s recordings and progress stay on this device: enter ${id} again to go on where they left off.`,
    newParticipantTitle: 'New participant?',
    newParticipantBody: (id, unsaved) => (unsaved
      ? `First, the ${unsaved} recording${unsaved === 1 ? '' : 's'} not saved yet ${unsaved === 1 ? 'is' : 'are'} saved. Then Set up starts again for the next participant; ${id}’s progress stays on this device.`
      : `Set up starts again for the next participant. ${id}’s recordings and progress stay on this device.`),
    newParticipantSave: 'Save and continue',
    newParticipantGo: 'New participant',
    newParticipantNotSaved: 'Not saved yet',
    newParticipantNotSavedBody: 'Some recordings could not be saved, so nothing has changed. Try again, or look under Saving.',
    rainbowTitle: 'Rainbow Passage',
    rainbowAgain: 'Ask the question again…',
    rainbowAnswer: answer => (answer === 'declined' ? 'The participant answered No.' : 'The participant answered Yes; it is not finished.'),
    rainbowNote: 'For a wrong answer: the next start asks "Do you want to read the Rainbow Passage?" again. Recordings are kept.',
    rainbowConfirm: 'Ask "Do you want to read the Rainbow Passage?" again at the next start? Recordings are kept.',
    reset: 'Reset progress…',
    resetConfirm: 'Go back to the very first sentence (practice 1) and coach the practice again? Recordings are not deleted. A sentence recorded again replaces its earlier recording, which moves to not_used.',
    resetConfirmNewRound: round => `Start again from the very first sentence (practice 1) and coach the practice again? Recordings are not deleted. New recordings are round ${round} ("repeat${round}" in file names).`,
    roundNote: round => `Round ${round} ("repeat${round}" in file names). Within a round, a sentence recorded again replaces its earlier recording (moved to not_used). After the last sentence, anything recorded starts the next round.`,
    saving: 'Saving',
    mode: 'Saved to',
    modeFolder: name => `Folder “${name}”`,
    modeZip: 'ZIP files',
    folderAccess: 'Folder access',
    permissionWord: state => ({ granted: 'Allowed', prompt: 'Ask again', denied: 'Not allowed' }[state] || 'Unknown'),
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
    signOutYes: 'Sign out',
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
