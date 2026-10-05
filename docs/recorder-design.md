# Recorder design (v6)

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

0. **Apple-level quality comes first.** Appearance, interaction, aesthetics, completeness,
   naturalness and clarity at the level of Apple's own apps come before any single
   requirement (owner, 2026-10-05). A requirement is never met with an unbalanced,
   crowded or "strange" screen: find the design that meets it elegantly, or meet it
   partly. Native idioms are used where they exist: the system font, white screens,
   capsule buttons, a grouped Settings list with pages, a small self-view in the corner.
1. **One purpose and one main action per screen.** At every moment the person can tell
   where to look and what to press. Information comes one step at a time, when it is
   needed: How to record is taught inside the practice, not as a page of rules. Nothing
   is drawn that looks like a control but is not one.
2. **The sentence is the one thing to look at** while recording. Nothing near it moves,
   lights up, appears or disappears while someone reads.
3. **"Recording" is shown on the sentence itself.** It turns vivid green on a soft
   highlight, as on the earlier page. Around it only conventional, quiet signs change: a
   red ● Recording under it (steady, not blinking), and Start becoming a soft red Stop.
4. **Every colour has one meaning.**
   - Blue: continue / move on (the main button of every screen except recording).
   - Green: start recording (Start), and the sentence being recorded ("read now").
   - Red: recording (the dot, Stop).
   - Amber: a problem to fix.
   - Everything else is neutral grey.
5. **Off looks off, on looks on.** The camera picture and the sound level sit small in
   the corner: grey and still while not recording, live while recording.
6. **One instruction at a time, with its purpose.** First what just happened (small),
   then the single next action (large), rarely why (small). The control it names pulses,
   except while someone reads. Never two instructions that disagree; never a summary
   and the next step in one sentence.
7. **Teach the way it will be used.** Computers: Space and ← (the keys are shown on the
   buttons). Touch screens: the buttons.
8. **Formal recording is quiet.** After the practice, nothing explains anything while
   recording; a message appears only when something needs fixing.
9. **Guides are easy to follow.** The camera guide is one head oval in the middle (fixed
   by the owner; do not change it).
10. **Simple and predictable.** Three verbs (Start, Stop, Redo). The same steps every
    session. Every failure returns to the same sentence. Nothing moves when a message
    or the coach appears: their space is kept.
11. **Never miss a word.** Recording starts at most 0.16 s after the press (after a short,
    soft 0.04 s cue that is over before recording starts; no cue where the sound output
    is slow), and continues a fixed 0.7 s after Stop. Presses in the first 0.4 s after the
    recording screen appears are ignored (a double press on Continue must not start a
    recording).

## Flow

```
Sign in ─▶ [first time on this device: Set up — participant ID, save folder]
        ─▶ Welcome ─▶ Check: 1 camera position ─▶ 2 test recording (watch it back)
        ─▶ [first time: Practice 1–5, coached ─▶ Practice done]
        ─▶ Part n: 50 sentences ─▶ Break ─▶ … ─▶ All sentences done
```

The "?" button shows How to record at any time (a short dialog over the screen).
Settings (gear) is on every screen except while recording. The page can be open in only
one tab at a time: a second copy asks first and can take over.

## Screens, moment by moment

For each moment: what the person should look at (the focus), what is on screen, and
what changes. Sizes are per device class (`css/app.css`): wide (computers, tablets
sideways), tall (tablets upright), phone, flat (phones sideways).

### Layout of every screen
- White screen (black in dark mode), the system font, generous space.
- Top bar: small and quiet. Recording screen: **End for today** (blue text, left),
  where you are (centre: "Practice 2 of 5", "Part 2 of 7 · Sentence 14 of 50", with a
  thin bar), **?** and the gear (right). Other screens: the gear only. While recording,
  only "where you are" stays.
- Every screen is one centred group a little above the middle: content, then its main
  button right under it (never a button stranded at the bottom with a void in between).
  Flow screens (welcome, practice done, breaks, done, problems): a symbol, a title, one
  or two short lines, the main button (a filled blue capsule) and at most one or two
  quiet text buttons under it.
- One button shape: capsules. One meaning per colour (Principles 4); ticks (✓) are
  neutral grey, never green.

### Sign in
App name, "Sign in", Username, Password (Show password), the blue Sign in button, the
privacy note. The light/dark switch in the corner.

### Set up (research team or helper, once per device)
One question per step: Participant ID (example "SEMG1"; saved in capitals) → "Is this ID
correct?" in large type (and, if the device has progress from the earlier page,
continue from it or start fresh) → Chrome/Edge on a computer only: the folder for the
recordings, or ZIP files.

### Welcome
| | First visit | Returning |
|---|---|---|
| Focus | Begin | Continue |
| Shows | "Participant SEMG1", **Welcome**, "You will read short sentences out loud. The camera records your face and voice.", three plain rows (icon + text, not buttons): check camera and microphone · practise with 5 sentences · read the sentences, with breaks | **Welcome back**, "We’ll keep your place.", **Part 2 of 7**, seven segments (done parts filled, the current one outlined), "14 of 50 sentences done" (or "Starts with sentence 1") |
| Button | **Begin** (blue) | **Continue** (blue) |

ZIP mode with unsaved recordings: a quiet amber notice with **Save now**.

### Camera & microphone check (every session, two steps)
The picture stays in the same place through both steps; the panel beside it (below it
on upright screens) shows one step at a time.

| Moment | Focus | Panel |
|---|---|---|
| 1 Camera | the picture and the oval | "Step 1 of 2" · **Position the camera** · "Put it below your chin and tilt it up, so your mouth, cheeks and throat are visible." · **Next** (blue). No sound level yet. |
| 2 Microphone | Record a 5-second test | "Step 2 of 2" · **Test the microphone** · "Record 5 seconds, then watch and listen." · a quiet line "Microphone: …" (for a helper) · **● Record a 5-second test** (green, like Start). Bluetooth headphones: an amber note with a button for the built-in microphone. |
| Test recording | what to say | "Say:" in grey, then “Hello, this is my voice.” green on the highlight, like a sentence being recorded, and a grey 5-second bar; the picture says "● Recording · 4 s left" (the only red dot on this screen). |
| Playback | the playback | the recording plays with sound and picture ("Playing your test"). |
| Question | the answer | Can you see your mouth, cheeks and throat, and hear yourself clearly? (19 px, not a second title) · **Yes, continue** (blue) · Play it again · Record again (text). The help link goes once the test has played. |
| Nothing heard | the fix | "We couldn’t hear anything. Check the microphone, then record the test again." |

The live picture has no badge (red means recording). The picture never moves between
the steps, and on wide screens the panel starts level with it, so its title never moves
either. The test recording is never saved (only its result is in the event log).
Devices are chosen in Settings → Camera and microphone.

### Recording screen (practice and real sentences)
The sentence, its state under it, the guide (the practice coach, or a message),
**Start/Stop** and **Redo** form one group a little above the middle of the screen, on
every device (phones sideways: the sentence on the left, the guide and buttons on the
right). The camera picture is small in the top corner, its edge level with the gear. The
guide keeps one height all through the practice (104 px) and a smaller one all through
the real sentences (80 px; messages are two short lines at most, never wider than
Start), and Redo keeps its place when hidden, so nothing moves within the practice or
within a part. Start and Redo are at least 16 px apart. Lines break between phrases,
never right after "the", "a", "to"…

| State | Focus | Sentence | Under it | Camera, level | Main button | Redo | Guide |
|---|---|---|---|---|---|---|---|
| Waiting | the sentence, then Start | grey | ○ Not recording | grey, still | **● Start** (soft green) | "↶ Redo “last sentence”" (after the first take) | practice only, or a problem |
| Starting (~0.1 s) | — | grey | Starting… | grey | Starting… (inactive) | hidden | unchanged |
| Recording | the sentence | dark green on a clear green highlight, with room around the letters (more contrast than the grey) | **● Recording** (red, steady) | live | **■ Stop** (soft red; after 20 s it pulses and shows the time, "Stop · 0:21" — nothing changes near the sentence) | hidden | practice: "Read the green sentence out loud, then press Stop."; real sentences: nothing |
| After Stop (0.7 s + check) | — | grey | Finishing… | grey | Finishing… (inactive) | hidden | unchanged |
| Next sentence | the new sentence | grey | ○ Not recording | grey | Start | "↶ Redo “the sentence just recorded”" (a faint capsule) | "✓ Recorded" in quiet grey for 2.5 s |
| A part's last sentence | Finish part 2 | grey (stays) | ✓ Recorded | grey | **→ Finish part 2** (blue) | Redo — Record this sentence again | "That was the last sentence of part 2." |

"Recorded" is used for a take; "save" only for the file or folder step, so a participant
never reads "saved" on screen and then "save your recordings" at the break.

### Practice (the 5 warm-up sentences, first time only)
The coach says one thing at a time, just above Start. On a computer it names the keys,
elsewhere the buttons.

| Moment | What happened (small) | The one next action (large) | Why (small) | Pulses |
|---|---|---|---|---|
| Practice 1, waiting | — | Press Start once. | No need to hold it. | Start |
| Any practice, recording | — | Read the green sentence out loud, then press Stop. | — | nothing |
| Practice 2, waiting | ✓ Recorded. Every sentence works like this. | Next sentence: press Start. | — | Start |
| Practice 3, waiting (Redo lesson) | ✓ Recorded. | Now press Redo, under Start. (computer: Now press ← (Redo).) | It records the last sentence again. | Redo: the only filled button (dark), as large as Start, its sentence on a second line; Start an outline (still works) |
| After pressing Redo | Back to the last sentence. | Press Start and read it again. | — | Start |
| After that recording | ✓ Recorded again. The old recording is replaced. | Now go on: press Start. | — | Start |
| Practice 4 / 5, waiting | ✓ Recorded. | 2 more to practise / Last practice sentence: press Start. | — | Start |
| After practice 5 | That was the last practice sentence. (the pill already says ✓ Recorded) | Press Continue. | — | Continue (blue) |
| A problem | ⚠ the reason ("We couldn’t hear you. Sit a little closer.") | Press Start and read it again. | — | Start |
| Speaking before Start | ⚠ Not recording yet. | (unchanged) | — | — |

If Start is pressed instead of Redo at practice 3, practice 4 offers the lesson once
more.

### Practice done → the real sentences
Saving is learnt here by doing it once (ZIP mode), with the same steps as after every
part; only then are the real sentences introduced. One instruction at a time:

| Moment | Focus | Shows | Buttons |
|---|---|---|---|
| ZIP mode, before saving | Save recordings | blue ✓ · **Practice done** · "Now save your practice recordings. You will do the same after each part." | **Save recordings** (blue) · End for today (text) |
| ZIP mode, the question | the answer | "Did the file save?" (see Break) | |
| ZIP mode, saved | Continue to part 1 | "✓ Your practice recordings are saved." (right under the title: what happened first) · "Now the real sentences. They work the same way." · "7 parts of 50 sentences, with a rest after each part." | **Continue to part 1** (blue) · End for today (text) |
| Folder mode | Continue to part 1 | the same, with "✓ Every recording is saved by itself in “…”." | **Continue to part 1** · End for today |

"Continue", not "Start": on this page blue moves on; green "Start" belongs to recording.

### Break (after each part of 50)
The part's last sentence first stays on the recording screen (Recorded, Redo possible,
**Finish part 2**). Then (the top of the screen stays put while it changes; the symbol is
neutral grey, so the blue button is the only blue):

| Moment | Focus | Shows | Buttons |
|---|---|---|---|
| Folder mode | Continue | blue ✓ · **Part 2 done** · "Take a rest. Carry on when you are ready." · seven segments, two filled: "2 of 7 parts done" · "✓ Your recordings are saved in “…”." | **Continue to part 3** (blue) · End for today (text) |
| ZIP mode, before saving | Save recordings | blue ✓ · **Part 2 done** · "Save your recordings, then take a rest." (one instruction) · the segments | **Save recordings** (blue) · End for today (text) |
| ZIP mode, the question | the answer | **Did the file save?** iPhone/iPad: "If Safari asks, tap Download. Then tap ⬇ next to the web address and look for “SEMG1_part02”." (Android: the download notification; computers: the browser's downloads) | **Yes, I see it** (blue) · Save it again · Not sure (text). Nothing is pre-chosen, not even on a computer: the answer is given after looking. |
| ZIP mode, saved | Continue | "Take a rest. Carry on when you are ready." · "✓ Your recordings are saved." | **Continue to part 3** · End for today |
| ZIP mode, not saved | Save recordings | "Not saved yet. Your recordings are still on this device." (amber) | **Save recordings** · Continue without saving · End for today |

The ZIP files are named after the participant and the part, then the time
(`SEMG1_part02_2026-10-05T14-03-11.zip`); the question names only the first part.
A device that is almost full shows its own version of this screen: a warning symbol,
"This device is almost full. Please save your recordings to go on.", Save recordings,
then "Your recordings are saved. You can go on." and Continue.

### Done
| | End for today | All sentences done |
|---|---|---|
| Shows | ✓ · **Great work today** · "We’ll keep your place. You can close this page." · "✓ All recordings are saved." | ✓ · **All sentences done** · "Thank you so much!" · save status |
| Buttons | Record more (text) | — |

Anything still unsaved: a download symbol, "Please save your recordings before you close
this page.", the amber count, and **Save recordings** (blue). The page never says "you
can close this page" while something is unsaved.

### How to record (the ? button, on the recording screen)
A dialog over the screen: **How to record** · 1 Press Start once. · 2 When the sentence
turns green, read it out loud. · 3 Press Stop when you finish. · "Read a word wrong?
After Stop, press Redo to record that sentence again." · **Close** (blue). Computers
name Space and ←. Nothing records while it is open.

### Settings (gear)
Laid out like the Settings app: a short list; each topic opens as its own page with a
back button; **Done** closes. The earlier page's option names are kept.

- First page: Participant and Position (values) · **Sentences & progress** › ·
  **Saving** › (e.g. "3 not saved") · **Camera and microphone** › · **Recording
  quality** › · Appearance (Light | Dark) · About › · **Sign out (log out)** (red).
- Sentences & progress: Participant, Position, Sentence set (with a note on each set) ·
  *Go to a sentence*: ← Previous sentence · Next sentence (skip) → (asks first) · Go to
  sentence [ ] Go · *Practice*: Practise again or Skip practice (bypass warm-up) ·
  *Holding the button*: Held-press limit (note) · *Research team*: Switch participant… ·
  Reset progress… (red, asks first) · a note on rounds (`repeat<n>`).
- Saving: Saved to, Folder access, Not saved yet, Backup copies, Storage used (note) ·
  Save all recordings now · Save backup copies again · Choose folder… · Use ZIP files ·
  Delete backup copies… and Clear storage… (red, ask first). Recordings that are not
  saved anywhere yet can never be deleted here: Clear storage asks to save them first.
- In dark mode the sheet is dark grey with an edge, so it stands out from the dimmed
  page.
- Camera and microphone: Camera, Microphone (Bluetooth warning; what is in use) ·
  Record a new test.
- Recording quality: Recording resolution, Recording quality, Recording frame rate,
  Audio mode, Mirror video display (same defaults as the earlier page) · Apply and
  restart camera.
- About: Version, Session · Download event log.

## Errors and messages

Each message says what happened and what to do, in at most two short sentences. The
same sentence comes back every time. On a computer every message names the keys
("press Space", "← (Redo)") instead of the buttons. Messages are never wider than the
buttons under them.

| Situation | Message |
|---|---|
| Speaking before Start (not in the first 2 s after a take: people often say a word after Stop) | Not recording yet. Press Start first, then read. |
| Start held ≥ 1 s (push-to-talk habit) | Dialog "Press once, then let go": Press Start once and let go. It records until you press Stop. (take not used) |
| Stop held ≥ 1 s | Take kept; next sentence says: Recorded. Tip: let go of the button right after pressing it. |
| No speech | We couldn’t hear you. Sit a little closer, press Start and read it again. |
| Too loud | Too loud. Move back a little, press Start and read it again. |
| No audio at all | The microphone sent no sound. Press Start and read it again. |
| Recorder failed to start (after silent retries) | The recording didn’t start. Please press Start again. Twice in a row: a screen suggests the built-in microphone. |
| Recorder error while recording | Recording stopped unexpectedly. Press Start and read it again. |
| Page left while recording | Recording stopped because you left the page. Press Start and read it again. |
| Over 1 minute | That recording was over 1 minute. Press Start and read it again. |
| Take could not be stored | That recording could not be stored. Press Start and read it again. Twice in a row: "Recordings cannot be saved on this device". |
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
- **No missed words at Start** (owner, 2026-10-05: never miss speech; keep the cue only
  if the delay stays very short). A soft 0.04 s cue plays at the press and recording
  starts as soon as it is over, counting the sound output delay (40 ms where the browser
  does not report it), the microphone's input delay and 30 ms for the room: about
  0.13–0.16 s after the press, before anyone can start speaking. If that would be longer
  than 0.16 s, if the browser cannot report its output delay (Safari before 18.4), or if
  the microphone is Bluetooth, there is no cue and recording starts at the press. The sentence turns green once the recorder reports that it runs and has run
  0.08 s without an error (about 0.22 s after the press), so green always means "being
  recorded". An encoder that cannot start fails at once: it is rebuilt and restarted
  silently, up to twice, before anything turns green; the participant only sees a
  message if all tries fail. The sidecar records the wait (`timing.startCueLeadMs`).
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
  stay on the device as backup copies and can be saved again from Settings. They are
  never removed by count — only when the device is nearly full (the copies of the most
  recent ZIP only after the participant confirms that file again) — so a mistaken "Yes"
  does not lose a part.

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
