# Recorder design (v4)

What every screen shows, why, and how the recorder keeps the data clean. It is the
reference for building and reviewing the patient recorder (`app_next.html`).

## Who uses it

- People with speech and movement difficulties after stroke, or with cerebral palsy,
  Parkinson's or ALS. Many are older. Some have tremor, weak hands, low vision, or tire
  quickly. Some record alone, others with a family member.
- Devices: iPad (touch, sometimes a keyboard), phones, laptops (Chrome, Edge, Safari),
  presentation clickers and accessibility switches.
- Researchers set up a device once, then collect the files. They should not need to
  train anyone, sit beside anyone, or clean the data by hand.

## Goals

1. A first-time participant can complete the whole flow without help.
2. The sentence to read is always the center of attention. Nothing else competes with it.
3. Every recording covers the whole sentence, read once.
4. Mistakes are easy to fix. The participant knows a fix exists and how to use it (**Redo**).
5. Errors explain what happened and what to do, in plain words. They always return
   to the same sentence; no sentence is ever skipped.
6. The participant's folder holds exactly one usable recording per sentence (and round).
   Everything else goes into `not_used/` with its reason, so researchers don't have to
   clean anything.

## Principles

- **One task per screen, one main button.** Secondary actions are smaller and quieter.
- **Three verbs only:** Start, Stop, Redo. No "tap", "hold", "take", "block", "QC".
- **One colour per meaning.**
  - Green: go / recording now. It marks the Start button, and the sentence card while
    recording.
  - Amber: something needs attention.
  - Everything else is neutral grey.
  - No red, no blue.
- **Hide what is not needed now.** While recording, only the sentence and the Stop
  button are shown.
- **Teach by doing**, one idea at a time, in the same words every time.
- **Same steps every session.** It is predictable, and predictable is learnable.

## Flow

```
Sign in ─▶ [first time on this device: Set up — participant ID, save folder]
        ─▶ Welcome ─▶ Camera & microphone check (test recording + playback)
        ─▶ [first time: How to record ─▶ Practice 1–5 ─▶ Practice done]
        ─▶ Part n: 50 sentences ─▶ Break ─▶ … ─▶ Done
```

The help button ("?") shows *How to record* again at any time. Settings (gear) and the
light/dark switch are on every screen except while recording. The page can be open in
only one tab at a time: a second copy asks first and can take over.

## Screens

### Sign in
Card centred on the page background. It shows:
- the app name;
- "Sign in";
- the Username and Password fields, with Show password;
- the Sign in button;
- the privacy note.

The light/dark switch sits in the corner. The page uses the same font, colours and
buttons as the recorder.

### Set up (research team or helper, once per device)
1. Participant ID (example "SEMG1"), saved in capitals.
2. Confirm the ID in large type. If the device holds progress from the earlier page,
   choose to continue from it or start fresh.
3. Chrome/Edge on a computer only: choose the folder where every recording is saved,
   or choose ZIP files instead.

### Welcome
- First time:
  - "Welcome".
  - One sentence on what happens: "You will read short sentences out loud. The camera
    records your face and voice."
  - The three stages: check camera & microphone, learn and practise, then read the
    sentences with rests between parts.
  - The **Begin** button.
- Returning:
  - "Welcome back".
  - The participant ID and where they are, e.g. "Part 2 of 7 — 14 of 50 done".
  - The **Continue** button.
- ZIP mode with unsaved recordings: a quiet notice with **Save now**.

### Camera & microphone check (every session)
- Large live preview with a dashed head-and-neck outline, and the study's camera
  position (from the earlier page's How to Record checklist): "Place the camera below
  your chin and tilt it up, so your mouth, cheeks and throat are visible." A face-only
  oval would invite a camera at eye level, which hides the throat.
- The camera and microphone in use, each with a **Change** link (opens Settings).
- A Bluetooth or headset microphone gets an amber note: lower sound quality; use the
  built-in microphone. One button switches to it.
- Microphone test, like Zoom: **Record a 5-second test**. The participant says
  something; the clip plays back with sound and picture, then asks "Can you see your
  mouth, cheeks and throat, and hear yourself clearly?" with **Yes, continue** and
  **Record again**.
- If the test heard nothing, it says so and offers to record again.
- **Continue** appears only after "Yes".

### How to record (first time, and from "?")
Three numbered steps, each with a small picture of the real control:
1. Press **Start** once — no need to hold it.
2. When the sentence turns **green**, read it out loud.
3. Press **Stop** when you finish.

Then one fix: "Read a word wrong? Press **Stop**, then **Redo** to record that sentence again."

With a keyboard, one more line: Space = Start/Stop, ← = Redo.

Button: **Practice now**.

### Recording screen (practice and real sentences)
Top to bottom:

1. **Top bar**, small and grey.
   - Left: where you are ("Practice 2 of 5", or "Part 2 of 7 · Sentence 14 of 50"), with
     "37 to go before the break" under it and a thin progress bar.
   - Right: End for today (asks first), ?, light/dark, settings.
   - While recording, only the progress stays.
2. **Coach** (practice only): one short instruction for the current moment, with a
   3-step strip (Start → Read → Stop) showing the current step.
3. **Sentence card**, which fills the free space.
   - Status pill at the top: "Not recording" (grey) or "Recording" (solid green). A clock
     appears in the pill only on takes longer than 20 s (a forgotten Stop, or the
     1-minute limit coming); a clock from 0:00 would hurry slow speakers.
   - The sentence: one size per screen and set, chosen so it reads as one continuous
     sentence (see `config.SENTENCE_SIZE`). The card keeps room for the longest sentence,
     so nothing jumps.
   - A slim waveform at the bottom moves only while recording.
   - While recording, the card turns light green with a green ring, the sentence turns
     green, and a green frame is drawn round the whole screen.
4. **Message line**, always in the same place: one amber line for a problem (what
   happened, what to do), a quiet line while recording ("Read it out loud, then press
   Stop.").
5. **Controls**:
   - The big **Start** (soft green) or **Stop** (neutral) button in the centre, always
     in the same place.
   - **Redo** to its left, with the sentence it would record again written under it. The
     "✓ Saved" chip appears on it for 1.4 s after a take, so "Saved" sits next to the
     sentence that was saved. While a Redo is under way the button reads **Cancel redo**.
     Shown only while waiting.
   - A small camera thumbnail on the right, also only while waiting.

States:

| State | Card | Pill | Button | Others |
|---|---|---|---|---|
| Waiting | neutral, sentence grey | Not recording | Start | Redo (+ Saved chip), camera, top-bar actions |
| Starting (≈0.35 s) | neutral | Starting… | Starting… (inactive) | hidden |
| Recording | green tint and ring, green sentence, screen frame | Recording (clock after 20 s) | Stop | hidden |
| Finishing (0.7 s) and checking | neutral | Saving… | Saving… (inactive) | hidden |
| Last sentence of a part | that sentence, neutral | Saved (grey) | Take a break / Continue / Finish | Redo ("Record this sentence again") |

The sentence turns green only after the recorder has really started. Green always
means "this is being recorded now"; "Saved" is grey.

### Practice (the 5 warm-up sentences, first time only)
1. "Press Start once — no need to hold it." Steps 1 → 2 → 3 light up in turn; the button
   for the current step pulses gently.
2. "Well done! That is all there is to it." then the same steps.
3. Redo lesson: "Now try Redo: press Redo to read "…" again." The Redo button pulses.
   After the Redo: "That is how Redo works. Read a word wrong? Press Stop, then Redo."
   Start is never blocked: a person with a single switch can simply go on.
4. Reminder: "Read a word wrong? Press Stop, then Redo."
5. "Press Start, read the sentence, then press Stop."

After practice 5 the sentence stays on screen ("Practice done. Press Continue.") so it
can still be redone. Then **Practice done**: "The real sentences work the same way.
There are 7 parts of 50 sentences, and you can rest between parts." Button: **Start part
1** (or **Continue to part n** after Settings → Practise again, which returns to the same
sentence).

### Break (after each part of 50)
- The part's last sentence first stays on screen (Saved, Redo still possible, **Take a
  break**).
- "Part 2 done — Well done. Take a rest."
- Save status: in folder mode "All recordings are saved in …" (or "still saving … you
  can go on" on a slow folder); in ZIP mode **Save recordings** first (at most 60 per
  ZIP file; "40 saved. Save the other 20 too." when more are waiting).
- **Continue to part 3**, or **Finish for today**.

### Done
"Great work today". Progress is saved. If anything is still unsaved, a reminder with the
save action.

### Settings (gear)
Sections, in this order (names the research team knows from the earlier page):
- **Sentences and progress** (research team):
  - participant, position, and which round new recordings get (`repeat<n>`);
  - Sentence set;
  - ← Previous sentence, Next sentence (skip) →, Go to sentence N;
  - Skip practice (bypass warm-up) or Practise again;
  - Clear progress…;
  - Held-press limit (1, 2 or 3 s);
  - Switch participant….
- **Saving**:
  - where recordings go (folder or ZIP files), folder access;
  - not saved yet, backup copies (ZIP mode), storage used;
  - Save all recordings now, Save backup copies again;
  - Choose folder…, Use ZIP files;
  - Delete backup copies…, Clear storage (delete recordings on this device)….
- **Camera and microphone**: the pickers, a Bluetooth warning when needed, the stream in
  use, Record a new test.
- **Recording quality** (research team): Recording resolution, Recording quality,
  Recording frame rate, Audio mode, Mirror video display (defaults as the earlier page).
- **Display**: Light / Dark.
- **Account**: Sign out (log out).
- **About**: version, session ID, Download event log.

Anything destructive asks for confirmation in plain words.

## Errors and messages

Each message says what happened and what to do, in at most two short sentences. The
same sentence comes back every time.

| Situation | Message |
|---|---|
| Speaking before Start | Not recording yet. Press Start first, then read. |
| Start held ≥ 1 s (push-to-talk habit) | Dialog "Press once, then let go": Press Start once and let go. It records until you press Stop. (take not used) |
| Stop held ≥ 1 s | Take kept; next sentence says: Saved. Tip: let go of the button right after pressing it. |
| No speech | We couldn't hear you. Sit a little closer, press Start and read it again. |
| Too loud | Too loud. Move back a little, press Start and read it again. |
| No audio at all | The microphone sent no sound. Press Start and read it again. |
| Recorder failed to start (after silent retries) | The recording didn't start. Please press Start again. Twice in a row: a screen suggests the built-in microphone. |
| Recorder error while recording | Recording stopped unexpectedly. Press Start and read it again. |
| Page left while recording | Recording stopped because you left the page. Press Start and read it again. |
| Over 1 minute | That recording was over 1 minute. Press Start and read it again. |
| Take could not be stored | That recording could not be saved. Press Start and read it again. Twice in a row: "Recordings cannot be saved on this device". |
| Device nearly full | The save screen: This device is almost full. Please save your recordings to go on. |
| Same sentence failed twice | Dialog: **Try again** (default) or **Keep it and go on** |
| Camera/microphone lost | Screen: what happened, "your progress is saved", **Reconnect** |
| Page already open in another tab | Screen: **Use this tab instead** (the other copy stops) |

## Recording reliability

- **Settings** are the same as the legacy page:
  - video: 1920×1080, 30 fps, 15 Mbps, H.264 MP4 where supported, WebM elsewhere;
  - audio: raw (no echo cancellation, noise suppression or gain control), 48 kHz
    requested, mono, AAC/Opus.
- **Audio bitrate** follows the microphone's real sample rate: 192 kbps at 44.1/48 kHz,
  64 kbps below that. Chrome's encoder fails to start about 1 time in 4 when a 16 kHz
  Bluetooth microphone is given 192 kbps; that was the cause of "Recording stopped".
- **The recorder must prove it started.** The sentence turns green only after a short
  check (0.2 s) that it started. If it reports an error at start, it is rebuilt and
  restarted silently, up to twice. The participant only sees a message if all tries fail.
- **Start sound first:** it plays 150 ms before recording, so it is not in the file.
- **Tail:** after Stop, recording continues a fixed 0.7 s for the last word.
- **Recorded in every sidecar, not used to reject:**
  - speech in the final 150 ms (`speechAtEnd`), a possible cut-off;
  - the silence before speech;
  - the time from press to green.

## Data and folders

```
<folder>/<ID>/                  one usable recording per sentence and round (+ JSON sidecar)
<folder>/<ID>/not_used/         failed checks, aborted takes, and recordings replaced by a newer one
<folder>/<ID>/logs/             session-*.json (event log of each session), superseded.json
<folder>/previous-page-recordings/   unsaved recordings the earlier page left on this device
```

A ZIP file has the same layout, plus `manifest.json` at the top.

- File names are unchanged:
  `<sentence>_<pos>-<total>_repeat<n>_<YYYYMMDD_HHMMSS>[_redo].<ext>`.
- **Rounds:** `repeat<n>` is the pass through the sentence set. After the last sentence,
  anything recorded (Clear progress, Go to, Practise again) starts the next round. The
  last sentence can still be redone before that, within the same round.
- **One usable recording per sentence and round.** When a usable recording replaces an
  earlier one of the same sentence (Redo, Previous, Go to, Practise again), the earlier
  one becomes `superseded` (with `supersededBy`; the new one has `supersedes`):
  - still on the device: marked in the same storage transaction, so it is written
    straight into `not_used/`;
  - already in the folder: moved into `not_used/` (copied, checked, then removed);
  - already in an earlier ZIP: listed in `logs/superseded.json`, which every later ZIP
    and the folder carry in full.
- **Progress** moves only together with a stored take (one transaction). If a take cannot
  be stored, the participant goes back to that sentence.
- **Folder writes** are verified by reading back the size. The cached copy is deleted
  only after that check.
- **ZIP:** at most 60 recordings per file. Saved where the participant chooses
  (Chrome/Edge) or downloaded and confirmed ("Did the file save?"). Confirmed recordings
  stay on the device as backup copies (at most 100, removed first when space is needed)
  and can be saved again from Settings.

## Validation

- `docs/recorder-checklist.md`: every feature of the earlier page, every requirement and
  every review finding, each with where it lives and how it is verified.
- Browser scenario tests (47) in Chrome, WebKit (iPad/iPhone engine) and Firefox:
  - first-run flow end to end, including the test recording, practice and the Redo
    lesson;
  - every error path, Redo (also after a reload, and of a part's last sentence),
    rounds, recorder start failures with silent retry, the bitrate cap on a 16 kHz
    microphone, storage failures, a 22-second take, two open tabs;
  - folder and ZIP saving (backups), every Settings option, theme, sign-in.
- Screenshots of every screen on:
  - phone, upright and sideways;
  - iPad mini upright, iPad upright and sideways;
  - laptop;
  - in light and dark.
- Independent reviews of the screenshots and flows:
  - a first-time participant's view;
  - a product designer's view;
  - a research data manager's view.
