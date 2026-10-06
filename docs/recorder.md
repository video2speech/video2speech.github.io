# Speech recorder (v210)

The new patient recorder lives at `app_next.html` while it is being tested on real
devices. The current page, `app.html` (v114, hotfixed), keeps running for participants
until the switch described at the end.

Why every screen looks and behaves the way it does (sizes, colours, wording, flow):
[recorder-design.md](recorder-design.md). What was checked before hand-over, item by
item: [recorder-checklist.md](recorder-checklist.md).

## What a participant sees

Every screen has one purpose and one main button; information comes one step at a time
(the moment-by-moment design is in recorder-design.md). The look follows Apple's
conventions: the system font, white (or black) screens, a filled blue button to move on.

1. **Sign in** (`index.html`), in the same style, with a light/dark switch.
2. **First-time setup** (research team or helper, once per device), one question per
   step: the participant ID (example "SEMG1", saved in capitals), confirmed in large
   type; on Chrome/Edge computers, the folder where recordings are saved. If the device
   holds progress from the earlier page, the setup asks whether to continue from it.
3. **Welcome**:
   - First time: what will happen, as three plain rows, and **Begin**.
   - Later visits: where they are ("Part 2 of 7", "14 of 50 sentences done") and
     **Continue**.
   - In folder mode the browser must be allowed to write to the folder again in each
     new browser session; **Begin** / **Continue** asks for it. If permission is not
     given, a screen offers **Allow**, **Choose a different folder** or **Save as ZIP
     files instead**. Nothing is ever saved anywhere else without asking.
4. **Camera and microphone check** (every session), two steps beside the same live
   picture:
   1. **Position the camera**: one head oval in the middle; "Put your face inside the
      oval." **Next**.
   2. **Test the microphone**: "Press Record and say “Hello, this is my voice.” Then
      watch it back." **Record a 5-second test**; the clip plays back (picture and
      sound), then "Can you see your face and hear yourself clearly?" **Yes, continue** / Play it again / No, try again (back to step 1). A
      Bluetooth microphone gets a warning and a one-tap switch to the built-in one. The
      test is never saved.
5. **Practice** (the 5 warm-up sentences, first time only). How to record is taught
   here, one step at a time, just above Start: first what just happened ("✓
   Recorded."), then the one next action ("Next sentence: press Start."). The control it
   names pulses. Practice 3 teaches Redo by doing it.
6. **Recording**, one sentence at a time. The sentence is the one thing on the screen:
   - *Not recording*: the sentence in grey, "○ Not recording" under it, a soft green
     **Start**, and **Redo** with the previous sentence. The camera picture and sound
     level, small in the corner, are grey and still.
   - *Starting…* (about 0.2 s): a short, soft start cue (0.04 s), then recording starts
     (at most 0.16 s after the press); the sentence turns green once the recorder has run
     0.08 s without an error.
     Where the device's sound output is too slow for that, there is no cue and recording
     starts at the press.
   - *Recording*: the sentence turns vivid green on a soft highlight. Around it only
     quiet signs change: a red "● Recording" under it, the camera picture and sound
     level come alive, and Start becomes a soft red **Stop**. No text appears. After
     20 s Stop pulses and shows the time ("Stop · 0:21").
   - After Stop, recording continues a fixed 0.7 s (the legacy page: 0.3 s). The next
     sentence then appears; "✓ Recorded" shows quietly above Start for 2.5 s, and Redo
     names the sentence just recorded. Checking and storing happen in the background. ("Save" is only ever
     used for the file or folder step.)
   - The last sentence of a part stays on screen ("Recorded", Redo still possible) until
     **Finish part 2** (blue).
7. **Practice done**: in ZIP mode the practice recordings are saved once, with the same
   steps as after every part (saving is learnt by doing it); then "Now the real
   sentences. They work the same way." and **Continue to part 1**. In folder mode the
   screen names the folder.
8. **Break** after every 50 sentences ("Part 2 done", seven segments for the parts); in
   ZIP mode "Save your recordings, then take a rest." and **Save recordings** first
   (the file is `SEMG1_part02_<time>.zip`; "Did the file save?" → **Yes, I see it**, nothing
   pre-chosen). Then
   **Continue to part 3** or End for today.
9. **Done**: "You can close this page" only when everything is saved; otherwise "Please
   save your recordings before you close this page." with **Save recordings**.

The top bar shows where you are ("Part 2 of 7 · Sentence 14 of 50", a thin bar), **End
for today** (asks first), **?** (How to record, as a short dialog) and **Settings**. Its
buttons are hidden while recording. Light/dark is in Settings.

The page runs in one tab at a time. A second copy shows "Already open in another tab"
with **Use this tab instead**; the first copy then stops and says so.

## Interaction rules

- Two presses per sentence: Start, then Stop. Both act on press, not on release.
- Keys: Space, Enter, → and PageDown are the main button (presentation clickers and
  accessibility switches send these); ← and PageUp are **Redo**.
- Keyboard auto-repeat is ignored. Presses less than 0.3 s apart are ignored (switch
  bounce, tremor). A press that would undo the one just made counts only after 1 s:
  a double press on Start never stops the take, and a double ← never cancels the Redo
  it has just made. Start right after a take, or right after Redo, counts at once.
- On every screen, a press acts once: clicks in the 0.4 s after a screen (or a step on
  it) appears are ignored, and a key or finger still down from the press that brought a
  screen does nothing there (holding Space or Enter never runs on through screens).
  Closing a dialog counts as a screen change (a double tap on its answer never presses
  the button behind it). Save recordings and Reconnect do nothing while they are
  already running.
- **Start held for 1 s** (the push-to-talk habit) throws the take away. A dialog then
  explains: "Press Start once and let go. It records until you press Stop." The same
  sentence comes back.
- **Stop held** is not push-to-talk (people let go slowly): the take is kept and the next
  sentence shows a gentle tip. The limit is 1 s, or 2 or 3 s in Settings. A second press
  less than 1 s after Start is not a Stop (a double press); held, it is the push-to-talk
  habit (a tap, then a hold) and is treated like a held Start.
- **Redo** records the previous sentence again, within the same part only (also the
  part's last sentence, before the break), and then returns. While it is under way the
  button reads **Cancel redo**. A Redo survives a reload or End for today. The
  recording it replaces goes to `not_used/` as `superseded`.
- Every failure returns to the **same** sentence: held Start, no speech, too loud, no
  audio, recorder failed to start, 60-second limit, camera or microphone lost, page
  hidden, reload, a take that could not be stored. Progress only moves together with a
  stored take.

## Recording reliability

- **Recording settings** are the legacy page's (see Settings → Recording quality):
  - video: 1080p, 30 fps, 15 Mbps; H.264 MP4 where supported, otherwise WebM;
  - audio: raw (no echo cancellation, noise suppression or gain control), 48 kHz
    requested, mono.
- **Audio bitrate**: 192 kbps for a microphone at 44.1/48 kHz, 64 kbps below that.
  Chrome's MP4 encoder fails to start about 1 time in 4 with a 16 kHz (Bluetooth)
  microphone at 192 kbps.
- **Start failures**: an error while starting is retried silently with a new recorder
  (up to 3 tries; the last uses the next recording format). If all tries fail the
  participant is told. A second failure in a row shows a screen suggesting the
  built-in microphone. Each sidecar records `timing.startAttempts` and `startErrors`.

## Recording check (approved 2026-10-03; no_audio approved 2026-10-04)

- A frame counts as speech when its RMS is at least `max(0.004, 3 × noise floor)`,
  where the noise floor is the take's 20th-percentile frame RMS.
- **no_speech**: under 300 ms of speech frames.
- **too_loud**: 1% or more of samples clip.
- **no_audio**: the audio analysis delivered nothing (e.g. iOS paused it).
- After two failures in a row on one sentence the participant may choose
  *Keep it and go on* (`status: qc_overridden`).
- Recorded but not used to decide:
  - RMS, peak, clipping rate, noise floor and speech ms;
  - silence before speech;
  - `speechAtEnd` (speech in the last 150 ms: a possible cut-off);
  - `timing.tailMs`.

## Files

File names are unchanged from the legacy page:
`<sentence>_<pos>-<total>_repeat<n>_<YYYYMMDD_HHMMSS>[_redo].<ext>`
(`_warmup<pos>-5_` for practice sentences). Every video has a JSON sidecar.

The folder and the ZIP use the same layout:

| Where | What |
|---|---|
| `<participant>/` | exactly one usable recording per sentence and round: `status` `accepted` or `qc_overridden` |
| `<participant>/not_used/` | everything else: `qc_failed`, `aborted_hold`, `aborted_timeout`, `aborted_device`, `aborted_hidden`, and `superseded` (replaced by a newer recording of the same sentence, with `supersededBy`) |
| `<participant>/logs/` | `session-*.json` (folder: the event log of each session), `superseded.json` (every replaced recording so far) |
| `previous-page-recordings/` | recordings the earlier page left unsaved on this device (no participant ID) |
| `manifest.json` (ZIP) | all records in the ZIP, the replaced list, and the event log |

- **Rounds** (`repeat<n>`): the pass through the sentence set, as on the legacy page
  (`repetitionCount` counts completed passes). After the last sentence, anything
  recorded starts the next round; until then the last sentence can still be redone in
  the same round. Settings shows the current round.
- **One usable recording per sentence and round**: a newer usable recording of a
  sentence (Redo, Previous, Go to, Practise again) supersedes the earlier one. Still on
  the device: marked in the same storage transaction. Already in the folder: moved to
  `not_used/`. Already in an earlier ZIP: listed in `logs/superseded.json`, which every
  later ZIP carries in full.
- **Nothing is deleted or overwritten** (owner's rule, 2026-10-05): a misread recording
  stays a complete recording with its sidecar. Every attempt is its own file (time in the
  name, `_redo` for later attempts); the replaced one only moves to `not_used/` with
  `status: superseded` and `supersededBy`, and the new one says what it `supersedes`.
  Takes leave the browser's storage only after they are in the folder or in a ZIP file
  that was confirmed saved.
- **Sidecar additions**:
  - identity and status: `participantId`, `sessionId`, `takeId`, `takeIndex`,
    `status`, `usable`, `round`;
  - `qc{…}`;
  - `markers{…}`: sentence shown, start press, recorder start, read now (green), stop
    press, recorder stop;
  - `timing{…}`;
  - replacement links: `supersedes` / `supersededBy`;
  - `inputType`.
- **Folder mode** (Chrome/Edge on a computer): every take is written to the chosen
  folder as soon as it is checked, then read back to verify its size. It leaves browser
  storage only after that. Folder mode never downloads files.
- **ZIP mode** (iPad, phones, Safari, Firefox, or when chosen at setup): one ZIP per
  part, at most 60 recordings per file, named `<participant>_<what>_<time>.zip`, where
  `<what>` is `part01` … `part07`, `practice`, `saved` (the end or a full device),
  `manual` (Settings → Save all recordings now) or `backup` (Settings → Save backup
  copies again).
  - Where the browser has a save dialog (Chrome/Edge), it opens first.
  - Elsewhere the ZIP is a normal download followed by *Did the file save?*
    (**Yes, I see it** / **Save it again** / **Not sure**).
  - After **Yes, I see it** the recordings stay on the device as backup copies: left
    out of later ZIPs and removed only when the device needs space (oldest first).
    Settings → **Save backup copies again** recovers from a mistaken "Yes".
- If a take cannot be stored (for example a full device), the participant goes back to
  that sentence; a nearly full device leads to the save screen. When the only thing left
  to remove is the copy of the most recent ZIP, the save screen first asks the
  participant to check that file is saved ("It is saved — make room").
- **Merging** files from several places (two folders, or ZIP files from different days):
  unzip the oldest first, then run `python3 tools/apply_superseded.py <folder>/<participant>
  --apply`; it moves every recording listed in `logs/superseded.json` into `not_used/`
  (nothing is deleted).
- **Falling back to the legacy page** on a device: save everything with the new page
  first. The legacy page's Save All puts every cached take (including not-used ones and
  backup copies) flat into its ZIP.

## Settings (gear button)

Available on every screen except while recording. Every option of the legacy page is
here, under its old name (checked by the `settings_parity` test):
- **Sentences and progress** (research team): participant, position and round;
  Sentence set; ← Previous sentence; Next sentence (skip) →; Go to sentence N; Skip
  practice (bypass warm-up) or Practise again (returns to the same sentence afterwards);
  Clear progress…; Held-press limit; Switch participant….
- **Saving**: where recordings go; not saved yet, backup copies, storage used; Save all
  recordings now; Save backup copies again; Choose folder… / Use ZIP files; Delete
  backup copies…; Clear storage (delete recordings on this device)….
- **Camera and microphone**: device pickers, a Bluetooth warning, the stream in use, and
  Record a new test.
- **Recording quality** (research team): Recording resolution, Recording quality
  (bitrate), Recording frame rate, Audio mode, Mirror video display.
- **Display**: Light / Dark.
- **Account**: Sign out (log out); signing in again returns to this page.
- **About**: version, session ID, and Download event log.

Destructive actions ask for confirmation first.

## Device recommendations (tell participants)

The study's camera position (the earlier page's How to Record checklist): the camera
**below chin level, tilted up**, so the **mouth, cheeks and throat** are visible. Front
cameras sit at the top edge of the screen, so:
- **Tablet**: low in front of the participant (on the table, or a low stand), screen
  tilted back, so its top edge is below the chin. Sideways if the camera is on the long
  edge (iPad 10th generation and newer, recent iPad Air and Pro), so the camera is in the
  middle; upright if it is on the short edge (older iPads).
- **Phone**: upright on a low stand, tilted back. Held sideways, the camera ends up to
  one side and films the face from the side. Upright phones record portrait video
  (1080×1920); computers and tablets record 1920×1080.
- **Computer**: the built-in camera usually sits above eye level, which is too high. Use
  a webcam placed below the chin, pointing up, and choose it in Settings → Camera.
  Prefer the built-in microphone over Bluetooth headphones.

The camera check shows one head oval in the middle and asks participants only to put
their face inside it (owner, 2026-10-05); the test playback asks whether they can see
their face and hear themselves. The position above is a setup tip for the research
team, not an instruction on screen.

The layout is checked on all five shapes: phone upright and sideways, tablet upright
and sideways, computer.

## Compatibility with the legacy page

- Same IndexedDB (`VideoRecorderDB`, version 2) and record shape, so either page can
  export what the other recorded.
- Progress is stored per participant and mirrored to the legacy key, so the legacy page
  continues from the same sentence on that device.
- The first participant set up on a device that already has legacy progress is asked
  whether to continue from it. Such participants go straight on after the check; there
  is no practice (the ? button shows How to record).

## Code

Classic scripts sharing `window.V2S`, loaded in order:

| Script | Role |
|---|---|
| `config.js` | thresholds and timings, including sentence-size rules |
| `copy.js` | every visible sentence |
| `util.js` | shared helpers |
| `storage.js` | IndexedDB access |
| `sentences.js` | the sentence lists |
| `media.js` | camera, microphone, recorder |
| `meter.js` | waveform and cue sounds |
| `qc.js` | the recording check |
| `input.js` | presses, holds, debounce |
| `ui.js` | rendering and sentence sizing |
| `export.js` | folder, ZIP (chunks, backups), superseded handling |
| `session.js` | the state machine, practice coaching, Redo, rounds |
| `settings.js` | the settings panel |
| `main.js` | screens and flow |

Styles: `css/base.css` (shared with the sign-in page) and `css/app.css`.

## Testing

See `tools/e2e/README.md` for setup. Every test run is silent: browsers are muted.

```bash
python tools/e2e/test_next_app.py                   # 51 scenarios (Chrome)
python tools/e2e/test_next_app.py --engine webkit   # 40 scenarios in Safari's engine
python tools/e2e/test_next_app.py --engine firefox
python tools/e2e/test_legacy_hotfix.py              # app.html v114
python tools/e2e/screenshots.py --engine webkit OUT_DIR --only phone ipad
```

What the tests can and cannot show:
- **Folder permission rules** (picker and permission only during a click, `prompt` in
  a new browser session, refusal) are emulated on the browser's private file system
  with Chrome's rules.
  - That the real folder picker opens from the click is checked in Chrome through
    DevTools.
  - Writing to a real folder on disk was only checked by hand.
- **iPad/iPhone** are approximated by WebKit with a synthetic camera and voice; keep the
  real-device checks.

## Releasing

- Bump the version in one step: `python3 tools/bump_version.py <new version>`.
- **Switch** (after device testing): the `switch-to-v200` branch makes the new recorder
  `app.html`, keeps the legacy page as `app_legacy.html` (update prompt removed) and
  moves the recorder's version to the `appVersion` key of `version.json`.
- Backups: git tags `legacy-v111` (before any change), `legacy-v113` (first hotfix)
  and `legacy-v114` (save dialog first).
