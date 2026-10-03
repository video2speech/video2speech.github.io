# Speech recorder (v200)

The new patient recorder lives at `app_next.html` while it is being tested on real
devices. The current page, `app.html` (v113, hotfixed), keeps running for participants
until the switch described at the end.

## What a participant sees

1. **First-time setup** (research team or helper, once per device): participant ID;
   on Chrome/Edge computers, the folder where recordings are saved.
2. **Welcome**: where they are (block and sentence), unsaved-recordings reminder.
3. **Camera and microphone check** (every session): large preview with a face outline
   and a live sound bar. One button: *Looks good*.
4. **Recording**: one sentence at a time.
   - *Not recording*: grey card, dimmed sentence, **Start**.
   - *Recording — read now*: thick red frame, dark sentence, **Stop**.
   - After Stop the page records 1 more second, checks the take, then shows the
     next sentence or explains why the same sentence comes back.
5. **Block break** every 50 sentences: rest, and save (ZIP) if needed.
6. **Done**: progress is saved; reminder if anything is still unsaved.

Tutorial tips appear only on the first two takes of a participant's first session.
Warm-up (5 sentences) happens only at the start of the sentence list.

## Interaction rules

- Two presses per sentence: Start, then Stop. Both act on press, not on release.
- Keys: Space, Enter, → and PageDown are the main button (presentation clickers and
  accessibility switches usually send these); ← is the small button
  (*Redo last* while waiting, *Start over* while recording).
- Keyboard auto-repeat is ignored. A key or touch **held for 1 s** throws the take away
  and restarts the same sentence ("Please tap, don't hold").
- Presses less than 300 ms apart are ignored (tremor double taps, switch bounce).
- Every failure — held press, no speech, too loud, 60-second limit, camera or
  microphone lost, page hidden, reload — returns to the **same** sentence.
  Progress only moves on an accepted take.

## Recording check (approved 2026-10-03)

- A frame counts as speech when its RMS is at least `max(0.004, 3 × noise floor)`,
  where the noise floor is the take's 20th-percentile frame RMS.
- **no_speech**: under 300 ms of speech frames. **too_loud**: 1% or more of samples clip.
- After two failures in a row on one sentence the participant may choose
  *Keep it and continue* (`status: qc_overridden`).
- Recorded but not used to decide: RMS, peak, clipping rate, noise floor, speech ms,
  silence before speech, and `speechAtEnd` (speech in the last 150 ms of the take,
  i.e. possibly cut off).

Thresholds live in `js/config.js` (`QC`).

## Files

File names are unchanged from the legacy page:
`<sentence>_<pos>-<total>_repeat<n>_<YYYYMMDD_HHMMSS>[_redo].<ext>`
(`_warmup<pos>-5_` for warm-up sentences). Every video has a JSON sidecar.

| Where | What |
|---|---|
| top level | takes to use: `status` `accepted` or `qc_overridden` |
| `not_used/` | everything else: `qc_failed`, `aborted_hold`, `aborted_timeout`, `aborted_device`, `restarted` |
| `manifest.json` (ZIP) or `session-*.json` (folder) | all records plus the session event log |

Sidecar additions: `participantId`, `sessionId`, `takeId`, `takeIndex`, `status`,
`usable`, `qc{…}`, `markers{…}` (sentence shown, start press, recorder start, stop press,
recorder stop — ms since session start), `supersedes` (for *Redo last*), `inputType`.

- **Folder mode** (Chrome/Edge on a computer): every take is written to
  `<folder>/<participant>/` as soon as it is checked; it leaves browser storage only
  after the write succeeded.
- **ZIP mode** (iPad, phones, Safari, Firefox): at each block break the participant
  downloads `<participant>_video-recordings-<time>_blockNN.zip` and answers
  *Did the file save?*. Cached takes are deleted only after **Yes, it saved**.

## Researcher panel

Open the page once with `?admin=1` (e.g. `app_next.html?admin=1`) to show the gear
button for that browser session (`?admin=0` hides it). It can switch participant or
sentence set, jump to a sentence, reset progress, download or delete cached
recordings, choose the save folder, change camera settings (applied when the camera
restarts), switch light/dark theme and download the event log.

## Compatibility with the legacy page

- Same IndexedDB (`VideoRecorderDB`, version 2) and record shape, so either page can
  export what the other recorded.
- Progress is stored per participant and mirrored to the legacy key, so the legacy page
  continues from the same sentence on that device.
- The first participant set up on a device that already has legacy progress is asked
  whether to continue from it.

## Testing

```bash
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py      # new recorder, 12 scenarios
~/.venvs/v2s-e2e/bin/python tools/e2e/test_legacy_hotfix.py  # app.html v113
~/.venvs/v2s-e2e/bin/python tools/e2e/screenshots.py         # every screen, 6 sizes, 2 themes
```

## Releasing

- Bump the version in one step: `python3 tools/bump_version.py 201`.
- **Switch** (after device testing): the `switch-to-v200` branch makes the new recorder
  `app.html`, keeps the v113 page as `app_legacy.html` (update prompt removed) and
  sets `version.json` to `{"appVersion": "200"}`.
- Backups: git tags `legacy-v111` (before any change) and `legacy-v113` (hotfix).
