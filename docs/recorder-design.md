# Recorder design (v5)

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

These come from the owner's reviews of real use. Every screen and every element is
checked against all of them before it is shown.

1. **The sentence is the one thing to look at.** While someone reads, nothing near the
   sentence moves, lights up, appears or disappears. Everything else sits at the edges
   and stays quiet.
2. **"Recording" is shown on the sentence itself.** It turns a vivid green with a soft
   highlight, as on the earlier page, which participants found clear. Around it only
   conventional, quiet signs change:
   - a small red ● Recording in the corner (the universal record sign);
   - the green Start button becomes a soft red Stop.

   There are no green frames, tinted panels or glowing borders.
3. **One meaning per colour.**
   - Green: read now (the live sentence) and go (Start).
   - Red: recording (the dot, the Stop button).
   - Amber: a problem to fix.
   - Everything else is neutral.
4. **Off looks off, on looks on, the same way everywhere.** The camera picture and the
   sound level are always in the same small place in the card's corner:
   - while not recording, grey and still;
   - while recording, in colour and moving;
   - never brighter or larger than needed.
5. **One instruction at a time, with its purpose.**
   - First say what just happened ("✓ Recorded."), then give the single next action in
     large, plain words, and highlight the control it names.
   - Never show two instructions that disagree.
   - Never put a summary and the next step in one sentence.
6. **Teach the way it will be used.** On a computer the keyboard needs no aiming, so the
   instructions name **Space** and **←**, and the keys are shown on the buttons. On touch
   screens the instructions name the buttons.
7. **Formal recording is quiet.** After the practice, nothing explains anything while
   recording. Messages appear only when something needs fixing.
8. **Guides must be easy and comfortable to follow.** The camera guide marks only what
   is required (the head), with a faint hint of the neck. Never shoulders: fitting them
   makes people bend their head.
9. **Simple and predictable.**
   - One task and one main button per screen.
   - Three verbs only: Start, Stop, Redo.
   - Same steps every session.
   - Hide what is not needed now.
   - Teach by doing.
   - Every failure returns to the same sentence.

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
Three numbered steps, each with a picture of the control to use. On a computer the
pictures are keys and the steps name them; on touch screens they are the buttons.
1. Press **Space** (touch: **Start**) once — no need to hold it.
2. When the sentence turns **green**, read it out loud.
3. Press **Space** again (touch: **Stop**) when you finish.

Then one fix: "Read a word wrong? Press **Space** to stop, then **←** to record that
sentence again." (touch: **Stop**, then **Redo**). On a computer, one quiet line adds
"You can also click the buttons on the screen."


Button: **Practice now**.

### Recording screen (practice and real sentences)
Top to bottom:

1. **Top bar**, small and grey.
   - Left: where you are ("Practice 2 of 5", or "Part 2 of 7 · Sentence 14 of 50"), with
     "37 to go before the break" and a thin progress bar.
   - Right: End for today (asks first), ?, light/dark, settings.
   - While recording, only the progress stays.
2. **Coach** (practice only): a quiet panel above the card. It keeps one size, so the card
   never moves.
   - First, small: what just happened ("✓ Recorded.") or a problem ("⚠ We couldn't hear
     you.").
   - Then, large: the one thing to do now ("Next sentence: press Start.").
   - Rarely, below: why ("Redo records the last sentence again.").
   - The control it names pulses, except while someone reads: nothing moves then.
   - In practice the message line below the card takes no room (the coach says it all),
     which keeps short screens (phones held sideways) from running out of space.
3. **Sentence card**:
   - Its top row holds the state on the left and the monitor on the right.
     - State: "○ Not recording" (grey), or "● Recording" with a red dot.
     - Monitor: a small sound level and camera picture. Grey and still while not
       recording; live while recording.
   - Below the top row is the sentence: one size per screen and set (see
     `config.SENTENCE_SIZE`), with room kept for the longest sentence.
   - While not recording the sentence is grey. While recording it turns vivid green on
     a soft highlight; nothing else in the card changes colour.
4. **Message line**, the same place every time, used only when something needs fixing
   (amber), or after Redo ("Press Start, then read this sentence again."). Formal
   recording never shows text here while reading.
5. **Controls**:
   - The big **Start** (soft green) in the centre. While recording it becomes a soft red
     **Stop**. On a computer each button shows its key (Space, ←).
   - **Redo** to its left, with the sentence it would record again; "✓ Saved" sits on it
     for 1.4 s after a take. While a Redo is under way it reads **Cancel redo**. Shown
     only while waiting.

States:

| State | Sentence | Pill | Monitor | Button | Others |
|---|---|---|---|---|---|
| Waiting | grey | ○ Not recording | grey, still | Start (green) | Redo, top-bar actions |
| Starting (≈0.35 s) | grey | Starting… | grey | Starting… (inactive) | hidden |
| Recording | vivid green on a highlight | ● Recording (red dot; clock after 20 s) | live | Stop (soft red; pulses after 20 s) | hidden |
| Finishing (0.7 s) and checking | grey | Saving… | grey | Saving… (inactive) | hidden |
| Last sentence of a part | grey | ✓ Saved | grey | Take a break / Continue / Finish | Redo ("Record this sentence again") |

The sentence turns green only after the recorder has really started. Green on the
sentence always means "this is being recorded now".

### Practice (the 5 warm-up sentences, first time only)
The coach says one thing at a time. On a computer it names the keys ("press Space",
"press ← (Redo)"), elsewhere the buttons.

| Moment | What happened (small) | The one next action (large) |
|---|---|---|
| Practice 1, waiting | — | Press Start once — no need to hold it. |
| Any practice, recording | — | Read the green sentence out loud. Then press Stop. |
| Practice 2, waiting | ✓ Recorded. That is how every sentence works. | Next sentence: press Start. |
| Practice 3, waiting (the Redo lesson) | ✓ Recorded. | Now practise fixing a mistake: press Redo. (*Redo records the last sentence again.*) Redo pulses; Start stays plain but works. |
| After pressing Redo | Redo: back to the last sentence. | Press Start and read it again. |
| After that recording | ✓ Recorded again. The new recording replaces the old one: that is how you fix a mistake. | Now carry on with this sentence: press Start. |
| Practice 4 / 5, waiting | ✓ Recorded. | Two more to practise / Last practice sentence: press Start. |
| After practice 5 | ✓ Practice done. | Press Continue. |
| A problem | ⚠ the reason ("We couldn't hear you. Sit a little closer.") | Press Start and read it again. |
| Speaking before Start | ⚠ Not recording yet. | (unchanged: Start, or Redo during the lesson) |

If Start is pressed instead of Redo at practice 3, practice 4 offers the lesson once
more. Then **Practice done**: "The real sentences work the same way. There are 7 parts
of 50 sentences, and you can rest between parts." In ZIP mode the practice recordings
are saved once here, with the same steps as after every part.

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
