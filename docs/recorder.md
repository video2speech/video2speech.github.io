# Speech recorder (v202)

The new patient recorder lives at `app_next.html` while it is being tested on real
devices. The current page, `app.html` (v114, hotfixed), keeps running for participants
until the switch described at the end.

## What a participant sees

1. **First-time setup** (research team or helper, once per device): participant ID,
   shown back in large type to confirm. On Chrome/Edge computers, the folder where
   recordings are saved. A device that has progress from the earlier page asks whether
   to continue from it.
2. **Welcome**: where they are (warm-up, or block and sentence) and, in ZIP mode, how
   many recordings are not saved yet.
   In folder mode the browser must be allowed to write to the folder again in every
   new browser session; pressing **Start** asks for it. If permission is not given,
   the *Allow saving to your folder* screen offers **Allow**, **Choose a different
   folder** or **Save as ZIP files instead**. Nothing is ever saved anywhere else
   without asking.
3. **Camera and microphone check** (every session): large preview with a face outline
   and a live waveform. One button: *Looks good*.
4. **Recording**: one sentence at a time.
   - *Not recording*: the sentence is grey but readable; **● Start**. Speaking before
     Start shows "Not recording yet — press Start, then read."
   - *Recording*: the sentence turns **green**, a red frame surrounds the whole screen,
     "● Recording"; **■ Stop**.
   - After Stop the page keeps recording for a fixed 0.7 s (the legacy page: 0.3 s),
     whether or not the person is still speaking. The next sentence then appears at once
     with "Saved"; checking and storing happen in the background.
   - Next to Start/Stop: the waveform (last 4 s, green while recording), a small
     camera view, and one line saying where recordings go
     (*Saved to “folder”* or *Kept on this device until the break*).
5. **Block break** every 50 sentences: rest; in ZIP mode, save before continuing.
6. **Done**: progress is saved; a reminder if anything is still unsaved.

Warm-up (5 sentences) happens only at the start of the sentence list.

### First-session tutorial

Shown once per participant, on the first three takes, in the message line under the
sentence. The button the tip talks about pulses.

| Take | Before Start | While recording |
|---|---|---|
| 1 | Press Start, then read the sentence aloud. | Read it now. Press Stop when you finish. |
| 2 | To redo the last sentence, press Redo last. | Made a mistake? Press Start over. |
| 3 | Recordings save to your folder automatically. *(or)* Recordings stay on this device. You save them at each break. | — |

A problem message (for example "We didn't hear you…") always replaces the tip.

## Design language

- One thing to look at: the sentence. Then the Start/Stop button, then the recording
  state (dot + red frame), then a single message line. Progress, the waveform, the
  camera view and save status are small and quiet.
- Colour has one meaning each: red = recording, green = read now / saved,
  amber = try again, blue = tip. Nothing else is coloured.
- Light and dark themes (researcher panel → Display). Font: Atkinson Hyperlegible
  Next, bundled in `vendor/fonts/`.
- On tablets held upright and on phones the controls form one column: secondary
  button, waveform + camera, Start/Stop at the bottom. The waveform row keeps the two
  buttons apart so a shaky press cannot hit the wrong one.

## Interaction rules

- Two presses per sentence: Start, then Stop. Both act on press, not on release.
- Keys: Space, Enter, → and PageDown are the main button (presentation clickers and
  accessibility switches usually send these); ← is the small button
  (*Redo last* while waiting, *Start over* while recording).
- Keyboard auto-repeat is ignored. A key or touch **held for 1 s** throws the take away
  and restarts the same sentence ("Please tap, don't hold"). The click a browser sends
  after a held mouse button is ignored too.
- Presses less than 300 ms apart are ignored (tremor double taps, switch bounce).
- Every failure — held press, no speech, too loud, 60-second limit, camera or
  microphone lost, page hidden, reload — returns to the **same** sentence.
  Progress only moves on an accepted take.

## Recording check (approved 2026-10-03; no_audio approved 2026-10-04)

- A frame counts as speech when its RMS is at least `max(0.004, 3 × noise floor)`,
  where the noise floor is the take's 20th-percentile frame RMS.
- **no_speech**: under 300 ms of speech frames. **too_loud**: 1% or more of samples clip.
  **no_audio**: the audio analysis delivered nothing (e.g. iOS paused it); the page says
  the microphone did not respond instead of blaming the speaker.
- After two failures in a row on one sentence the participant may choose
  *Keep it and continue* (`status: qc_overridden`).
- Recorded but not used to decide: RMS, peak, clipping rate, noise floor, speech ms,
  silence before speech and `speechAtEnd` (speech in the last 150 ms of the take, i.e.
  possibly cut off). `timing.tailMs` says how long recording continued after Stop.

Thresholds live in `js/config.js` (`QC`, `TAIL_MS`).

## Files

File names are unchanged from the legacy page:
`<sentence>_<pos>-<total>_repeat<n>_<YYYYMMDD_HHMMSS>[_redo].<ext>`
(`_warmup<pos>-5_` for warm-up sentences). Every video has a JSON sidecar.

The folder and the ZIP use the same layout:

| Where | What |
|---|---|
| `<participant>/` | takes to use: `status` `accepted` or `qc_overridden` |
| `<participant>/not_used/` | everything else: `qc_failed`, `aborted_hold`, `aborted_timeout`, `aborted_device`, `restarted` |
| `previous-page-recordings/` | recordings the earlier page left unsaved on this device (no participant ID) |
| `manifest.json` (ZIP) or `<participant>/session-*.json` (folder) | all records plus the session event log |

Sidecar additions: `participantId`, `sessionId`, `takeId`, `takeIndex`, `status`,
`usable`, `qc{…}`, `markers{…}` (sentence shown, start press, recorder start, stop press,
recorder stop — ms since session start), `supersedes` (for *Redo last*), `inputType`.

- **Folder mode** (Chrome/Edge on a computer): every take is written to the chosen
  folder as soon as it is checked, and read back to verify its size. It leaves browser
  storage only after that check. Folder mode never downloads files.
- **ZIP mode** (iPad, phones, Safari, Firefox, or when chosen at setup): one ZIP per
  block, `<participant>_video-recordings-<time>_blockNN.zip`. Where the browser has a
  save dialog (Chrome/Edge) it opens first and the person picks the location; cached
  takes are deleted after the file is written there. Elsewhere the ZIP is a normal
  download followed by *Did the file save?*; cached takes are deleted only after
  **Yes, it saved**.

## Researcher panel

Open the page once with `?admin=1` (e.g. `app_next.html?admin=1`) to show the gear
button for that browser session (`?admin=0` hides it). It can switch participant or
sentence set, jump to a sentence, reset progress (shows the tutorial again), write
cached recordings to the folder or download them as a ZIP, delete cached recordings,
choose the save folder, change camera settings (applied when the camera restarts),
switch light/dark theme and download the event log.

## Compatibility with the legacy page

- Same IndexedDB (`VideoRecorderDB`, version 2) and record shape, so either page can
  export what the other recorded.
- Progress is stored per participant and mirrored to the legacy key, so the legacy page
  continues from the same sentence on that device.
- The first participant set up on a device that already has legacy progress is asked
  whether to continue from it.

## Testing

See `tools/e2e/README.md` for setup.

```bash
python tools/e2e/test_next_app.py                   # new recorder, 22 scenarios (Chrome)
python tools/e2e/test_next_app.py --engine webkit   # 15 scenarios in Safari's engine
python tools/e2e/test_next_app.py --engine firefox  # 15 scenarios in Firefox
python tools/e2e/test_legacy_hotfix.py              # app.html v114
python tools/e2e/screenshots.py --engine webkit OUT_DIR --only phone ipad
```

What the tests can and cannot show:
- Folder permission rules (picker and permission only during a click, `prompt` in a new
  browser session, refusal) are emulated on the browser's private file system with
  Chrome's rules. That the real folder picker opens from the click is checked in
  Chrome through DevTools. Writing to a real folder on disk was only checked by hand.
- iPad/iPhone are approximated by WebKit with a synthetic camera and voice; keep the
  real-device checks.

## Releasing

- Bump the version in one step: `python3 tools/bump_version.py 201`.
- **Switch** (after device testing): the `switch-to-v200` branch makes the new recorder
  `app.html`, keeps the legacy page as `app_legacy.html` (update prompt removed) and
  moves the recorder's version to the `appVersion` key of `version.json`.
- Backups: git tags `legacy-v111` (before any change), `legacy-v113` (first hotfix)
  and `legacy-v114` (save dialog first).
