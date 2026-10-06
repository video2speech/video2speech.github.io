# Recorder design (v6)

What every screen shows, why, and how the recorder keeps the data clean. It is the
reference for building and reviewing the patient recorder (`app.html`).

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
2. **The sentence is the one thing to look at.** It sits in a card with a clear edge
   (white on a grey page; grey on black), the only large surface on the screen, which
   draws the eye to it. Everything else is small and quiet around the card. Nothing near
   the sentence moves, lights up, appears or disappears while someone reads.
3. **"Recording" is shown on the sentence itself.** It turns vivid green on a soft
   highlight, as on the earlier page. Around it only conventional, quiet signs change: a
   red ● Recording on the card's top edge (steady, not blinking), and Start becoming a
   soft red Stop.
4. **Every colour has one meaning.**
   - Blue: continue / move on (the main button of every screen except recording).
   - Green: start recording (Start), and the sentence being recorded ("read now").
   - Red: recording (the dot, Stop).
   - Amber: a problem to fix.
   - Everything else is neutral grey.
5. **Off looks off, on looks on.** The camera picture and the sound level sit small in
   the corner: grey and still while not recording, live while recording.
6. **One instruction at a time, with its purpose.** First what just happened (small),
   then the single next action (large), rarely why (small). The control it names pulses
   three times, then stays still (never while someone reads). Never two instructions that disagree; never a summary
   and the next step in one sentence.
7. **Teach the way it will be used.** Computers: Space and ← (the keys are shown on the
   buttons). Touch screens: the buttons.
8. **Information only when something needs handling.** No routine confirmations: no
   "✓ Recorded" after each take, no "Not recording" while waiting (the next sentence
   appearing is the confirmation; the grey sentence and the green Start say "not
   recording"). After the practice, nothing explains anything while recording; a
   message appears only when something needs fixing, or when the next action differs
   from the usual one ("That was the last sentence of part 2.").
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
12. **A press acts once.** On every screen, clicks in the first 0.4 s after it (or a step
    on it) appears are ignored, so the second tap of a double tap never presses the button
    that has just appeared under the finger. A key or finger still held from the press
    that brought a screen does nothing there: auto-repeat never presses a button, and its
    release is ignored, so holding Space or Enter never runs on through screens. A press
    that would undo the one just made counts only after 1 s (a double press on Start
    never stops the take; a double ← never cancels the Redo). Opening and closing a
    dialog count as screen changes: a finger or key still down from before does nothing
    in it, and its answers count only after 0.35 s ("Did the file save?", answered after
    looking, after 1 s: on touch screens its main answer lands where the finger was). A
    button that removes something is never pre-selected for the keyboard, and a save or
    a reconnection that is running ignores further presses; a save started from Welcome
    or Done shows its progress on the button, as on a break. Nothing can be removed while
    a save runs.

13. **No accidental presses on touch screens.** On phones and tablets every screen's
    main button sits where Start sits: at the bottom, where a thumb, or a hand resting on
    the table, reaches it. A second action goes above it, never under it, so a slip
    downwards presses nothing. Start and these buttons sit 44 px above the bottom edge
    (32 px on short screens inside a browser's bars, 20 px on phones held sideways).
    On the recording screen Redo is far from Start, at the top
    left, where a Back button goes. Dialogs rise from the bottom: their main answer lands
    where Start sits, the other answers above it, 24 px apart (on computers they stay in
    the middle, the main answer first). Nothing that removes something is pre-selected,
    and removing asks first.
14. **Teaching says it is teaching; the one action is repeated.** The Redo lesson
    says "This is only practice — nothing went wrong." The one action to remember
    ("Press Start, read the green sentence out loud, then press Stop.") is shown before
    the practice, after it, and when coming back.

## Flow

```
Sign in ─▶ [first time on this device: Set up — participant ID, save folder]
        ─▶ Welcome ─▶ Check: 1 camera position ─▶ 2 test recording (watch it back)
        ─▶ [first time: One thing to remember ─▶ Practice 1–5, coached ─▶ Practice done]
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
- Top bar: small and quiet, its edges in line with the card's. Recording screen:
  **End for today** (grey text, left; the full name on every device, since "End" alone
  could mean "end this sentence"), where you are (centre: "Practice 2 of 5", "Part 2 of
  7 · Sentence 14 of 50", with a thin bar), **?** and the gear (right). Break: End for
  today and the gear. Other screens: the gear only. While recording, only "where you
  are" stays. During the Redo lesson End for today is hidden (one thing to press). End
  for today keeps its room while hidden, so nothing moves when a take starts; on the
  narrowest screens (a phone with larger text, 320 px) where you are shortens to "14 of
  50" rather than End for today to "End".
- Flow screens (welcome, practice done, breaks, done, problems) on computers are one
  centred group a little above the middle: a symbol, a title, one or two short lines,
  the main button (a filled blue capsule) and at most one or two quiet text buttons,
  24 px under it. On phones and tablets (touch screens, and any upright screen narrower
  than 1000 px) the text stays in the middle and the main button sits at the bottom,
  where Start sits on the recording screen; a text button goes above it, never under it.
  Break and Done keep their text at the top, so it stays put while the save steps change
  it; so does Welcome. The screen is the height of the window: if its words do not fit (a
  small phone held sideways), they scroll, their edges fade rather than cut a line in
  half, and the buttons stay in view. Set up is the exception: its form scrolls as one
  page, Continue under the field (the keyboard is up anyway). A long dialog scrolls its
  words, never its answers. The ID form in Set up keeps its button under the field (the keyboard is up); its
  questions follow the rule.
- Every problem on a flow screen looks the same: an amber notice. On the check it sits
  right above the button that fixes it; on a break it reports what just happened, under
  the title, and the usual line under the title steps aside (the notice and the buttons
  say what to do).
- The recording screen is a grey page with the sentence card: Redo and the camera
  picture above the card, the guide and Start/Stop at the bottom (see below).
- One button shape: capsules. One meaning per colour (Principles 4); ticks (✓) are
  neutral grey, never green.

### Sign in
App name, "Sign in", Username, Password (Show password), the blue Sign in button, the
privacy note. The light/dark switch in the corner.

### Set up (research team or helper, once per device)
One question per step: Participant ID (example "SEMG1"; saved in capitals) → "Is this ID
correct?" in large type → only if the device has progress from the earlier page, its
own question: **Earlier progress on this device** · "Recordings were made on this
device before IDs were used. Are they this participant’s?" · **Continue from sentence
120 of 350** (blue) · Start from the beginning (text) → Chrome/Edge on a computer only:
the folder for the recordings, or ZIP files. A wrong ID replaces the hint under the field
with what to fix.

### Welcome
| | First visit | Returning |
|---|---|---|
| Focus | Begin | Continue |
| Shows | "Participant SEMG1", **Welcome**, "You will read short sentences out loud. The camera records your face and voice.", three plain rows (icon + text, not buttons): check camera and microphone · practice with 5 sentences · read the sentences, with breaks | **Welcome back**, "Carry on where you left off.", **Part 2 of 7**, seven segments (done parts filled, the current one outlined), "Sentence 14 of 50" (nothing at a part's first sentence), then the one action to remember: "Press **Start**, read the **green** sentence out loud, then press **Stop**." |
| Button | **Begin** (blue) | **Continue** (blue) |

ZIP mode with unsaved recordings (not mid-practice: those are saved at its end), one
step at a time: the amber notice "3 recordings are not saved yet." under the words (what
happened, then the action, as on a break; it replaces "Carry on where you left off."), the main button becomes **Save recordings** (then the
usual "Did the file save?"; while it saves the button shows its progress), and a quiet
"Continue without saving" (it asks first, as on a break; the recordings stay on the
device). The one thing to remember waits until the recordings are saved. Once saved, the button is
**Continue** again.

Everything recorded: **All sentences done** · "Thank you! There is nothing more to
record. You can close this page." (with anything unsaved: "Please save your recordings
first." and **Save recordings**). No Continue.

### Camera & microphone check (every session, two steps)
The picture stays in the same place through both steps; the panel beside it (below it
on upright screens) shows one step at a time.

| Moment | Focus | Panel |
|---|---|---|
| 1 Camera | the picture and the oval | "Step 1 of 2" · **Position the camera** · "Put your face inside the oval." (owner: the face in the frame is enough) · **Next** (blue). No sound level yet. |
| 2 Microphone | Record a 5-second test | "Step 2 of 2" · **Test the microphone** · "Press Record and say “Hello, this is my voice.” Then watch it back." (the phrase is known before the 5 seconds start) · (the microphone's name is not shown: nothing to do about it) · **● Record a 5-second test** (green, like Start). Bluetooth headphones: an amber note; the step's main button becomes **Use “MacBook Air Microphone”** (blue) with "Keep using these headphones" (text); Record comes after the choice. |
| Test recording | what to say | under the title, where the instructions were: "Say:" in grey, then “Hello, this is my voice.” on one line, green on the highlight like a sentence being recorded, and a grey 5-second bar (the time left); the picture says "● Recording" (the only red dot on this screen; short, so it never covers the face). |
| Playback | the playback | the recording plays with sound and picture ("Playing your test"). |
| Question | the answer | Can you see your face and hear yourself clearly? (19 px, not a second title) · **Yes, continue** (blue) · Play it again · No, try again (text; back to step 1, where the usual fix is). After Play it again: "Can’t hear it? Turn the volume up and play it again." The help link goes once the test has played. |
| Nothing heard | the fix | the problem and its fix only (no instructions, no help link): an amber notice "We couldn’t hear anything. Check that the microphone is not muted or covered, and speak up." · Choose another microphone (a text link, as "Keep using these headphones"; opens Settings → Camera and microphone) · **● Record a 5-second test** |
| Camera or microphone not working? (link) | the fix | Before the picture works: how to allow the camera and microphone on this device. Once it works: what else to check (nothing covering them, the sound not muted) · **Close** · Choose camera or microphone |

On phones and tablets the check is one column: the picture, the step's words, and the
step's buttons at the bottom, where Start sits; the help link and any amber notice sit
right above them ("Play it again · No, try again" too, above **Yes, continue**). What to
read ("Say: …") and the question stay under the title, near the camera: reading at the
bottom would look down. Phones and tablets held sideways: the picture on the left, the
step on the right with its buttons at the bottom of that column. The picture is as large
as the screen allows (a third of the height on a short phone inside the browser's
bars); only a problem takes some of its room.

The live picture has no badge (red means recording). The picture never moves between
the steps, and on wide screens the panel starts level with it, so its title never moves
either. The test recording is never saved (only its result is in the event log).
Devices are chosen in Settings → Camera and microphone.

### Before the practice: one thing to remember (first time only)
"Practice" · **One thing to remember** · "Press **Start**, read the **green** sentence out
loud, then press **Stop**." (larger and darker than a lead; computers: Space) · "Try it
now with 5 short sentences. They are only for practice." · **Begin practice** (blue;
"Start" belongs to recording). After a reload mid-practice it counts what is left.

### Recording screen (practice and real sentences)
A grey page with one white card (dark mode: a grey card on black): the sentence card,
the only large surface, so the eye goes there. Above the card: **Redo** at the top left
(where a Back button goes, far from Start) and the camera picture with the sound level
at the top right. Below the card, in the practice only: the coach (one instruction at a
time). Then **Start/Stop** at the bottom of the screen, where a thumb or a resting hand
reaches it. A problem, or a next action that differs from the usual one, shows as a
small pill on the card's bottom edge, mirroring the red ● Recording on its top edge;
otherwise nothing is there, and the card keeps its size.
The card fills the space between Redo and Start (at most 960 px wide; the top bar lines
up with it). Phones sideways: the card on the left; Redo and the camera at the top
right, the coach and Start at the bottom right. The card, the coach and Start keep
their places and sizes all through the practice and all through a part; only the
sentence, its state and the labels change. Redo has two lines, "↶ Redo" over the
sentence it would record again (a long one shrinks to fit, then ends in "…"). Lines
break between phrases, never right after "the", "a", "to"… The size is one per screen and
sentence set: on computers and tablets nearly every sentence on one line; on phones 98%
on at most two lines as they really wrap, a little smaller (down to 28 px) rather than a
third line, which reads as keywords one by one.

| State | Focus | Sentence (in the card) | Card's top edge | Camera, level | Main button (bottom) | Redo (top left) | Guide |
|---|---|---|---|---|---|---|---|
| Waiting | the sentence, then Start | grey | — | grey, still | **● Start** (soft green) | "↶ Redo" over “the last sentence” (after the first take) | practice: the coach; real sentences: nothing (a problem: the pill on the card's bottom edge) |
| Starting (~0.1 s) | — | grey | — | grey | Starting… (inactive) | hidden | unchanged |
| Recording | the sentence | dark green on a clear green highlight | **● Recording** (red, steady) | live | **■ Stop** (soft red; after 20 s it pulses and shows the time, "Stop · 0:21") | hidden | practice: "Read the green sentence out loud, then press Stop."; real sentences: nothing |
| After Stop (0.7 s + check) | — | grey | — | grey | Finishing… (inactive) | hidden | unchanged |
| Next sentence | the new sentence | grey | — | grey | Start | "↶ Redo" over “the sentence just recorded” | nothing (the new sentence is the confirmation) |
| A part's last sentence | Finish part 2 | grey (stays) | — | grey | **→ Finish part 2** (blue) | "↶ Redo" over "Record this sentence again" | "That was the last sentence of part 2." (the pill on the card's bottom edge) |

### Practice (the 5 warm-up sentences, first time only)
The coach says one thing at a time, between the card and Start. On a computer it names the keys,
elsewhere the buttons.

| Moment | What happened (small) | The one next action (large) | Why (small) | Pulses |
|---|---|---|---|---|
| Practice 1, waiting | — | Press Start once. | No need to hold it. | Start |
| Any practice, recording | — | Read the green sentence out loud, then press Stop. | — | nothing |
| Practice 2, waiting | That’s it. Every sentence works like this. | Next sentence: press Start. | — | Start |
| Practice 3, waiting (Redo lesson) | This is only practice — nothing went wrong. | Now try Redo, at the top. (computer: Now try Redo: press ←.) | If you ever misread a sentence, Redo lets you read it again. | Redo (top left): a darker grey capsule with a ring, pulsing three times; Start an outline (still works); End for today hidden |
| After pressing Redo | This is the sentence before. | Press Start and read it again. | — | Start |
| After that recording | That’s how Redo works. | Now go on: press Start. | — | Start |
| Practice 4 / 5, waiting | — | 2 more to practice / Last practice sentence: press Start. | — | Start |
| After practice 5 | That was the last practice sentence. | Press Continue. | — | Continue (blue) |
| A problem | ⚠ the reason ("We couldn’t hear you. Sit a little closer.") | Press Start and read it again. | — | Start |
| Speaking before Start | ⚠ Not recording yet. | (unchanged) | — | — |

If Start is pressed instead of Redo at practice 3, practice 4 offers the lesson once
more.

### Practice done → the real sentences
Saving is learnt here by doing it once (ZIP mode), with the same steps as after every
part; only then are the real sentences introduced. One instruction at a time:

| Moment | Focus | Shows | Buttons |
|---|---|---|---|
| ZIP mode, before saving | Save recordings | blue ✓ · **Practice done** · "Now save your practice recordings. You will do the same after each part." | **Save recordings** (blue) |
| ZIP mode, the question | the answer | "Did the file save?" (see Break) | |
| ZIP mode, saved | Continue to part 1 | (no "saved" line: "Yes, I see it" has just said it) "Now the real sentences, the same way:" · the one action again, "Press **Start**, read the **green** sentence out loud, then press **Stop**." · "7 parts of 50 sentences. Rest after each part, or stop and carry on another day." | **Continue to part 1** (blue) |
| Folder mode | Continue to part 1 | the same, with "✓ Every recording is saved by itself in “…”." | **Continue to part 1** |

"Continue", not "Start": on this page blue moves on; green "Start" belongs to recording.

### Break (after each part of 50)
**End for today** is in the top bar (top left, as on the recording screen), never under
the main button, and always asks "End for today?" first ("Keep going" is the default).
The part's last sentence first stays on the recording screen ("That was the last sentence of part 2.", Redo possible,
**Finish part 2**). Then (the top of the screen stays put while it changes; the symbol is
neutral grey, so the blue button is the only blue):

| Moment | Focus | Shows | Buttons |
|---|---|---|---|
| Folder mode | Continue | grey ✓ · **Part 2 done** · "Take a rest. Carry on when you are ready." (nothing about saving unless something is not in the folder) · seven grey segments, two filled: "2 of 7 parts done" | **Continue to part 3** (blue) |
| ZIP mode, before saving | Save recordings | grey ✓ · **Part 2 done** · "Save your recordings, then take a rest." (one instruction) · the segments | **Save recordings** (blue) |
| ZIP mode, the question | the answer | **Did the file save?** iPhone/iPad: "If Safari asks, tap Download. Then tap ⬇ next to the web address and look for “SEMG1_part02”." (Android: the download notification; computers: the browser's downloads) | **Yes, I see it** (blue) · Save it again · Not sure (text). Nothing is pre-chosen, not even on a computer: the answer is given after looking. On a computer the first press of Space, Enter or a clicker highlights **Yes, I see it**; the next one chooses it. |
| ZIP mode, saved | Continue | "Take a rest. Carry on when you are ready." · the segments (no "saved" line: "Yes, I see it" has just said it) | **Continue to part 3** |
| ZIP mode, not saved | Save recordings | "Not saved yet. Your recordings are still on this device." (amber) | **Save recordings** · Continue without saving (asks first: "Continue without saving?" · "Your recordings stay on this device. You can save them at the next break." · **Save now** is the default; its "Continue without saving" counts only after a second, since it lands where the link was; Esc changes nothing) |

The ZIP files are named after the participant and the part, then the time
(`SEMG1_part02_2026-10-05T14-03-11.zip`); the question names only the first part.
A device that is almost full shows its own version of this screen: a warning symbol,
"This device is almost full. Please save your recordings to go on.", Save recordings;
once they are saved and there is room again, straight back to the sentence. Still full
after saving: **Make room on this device** · check that the last saved file is there ·
"It is saved — make room" (grey, not blue: it removes something), which asks first
("Remove the copy from this device?" · "Only if you found the saved file. The file
itself is not changed." · **Cancel**, blue, is the default; "Remove the copy" is grey).
A full device offers no "Continue without saving" (Start would only bring this screen
back), and its "almost full" message is gone once the recordings are saved.

### Done
| | End for today | All sentences done |
|---|---|---|
| Shows | ✓ · **Great work today** · "We’ll keep your place. You can close this page." · "✓ All recordings are saved." | ✓ · **All sentences done** · "Thank you so much! You can close this page." · save status |
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
- A confirmation that removes or ends something (Sign out, Reset progress, Delete backup
  copies, Clear storage) has **Cancel** as its blue main answer and the action in plain
  grey above it (red means recording).
- Sentences & progress: Participant, Position, Sentence set (with a note on each set) ·
  *Go to a sentence*: ← Previous sentence · Next sentence (skip) → (asks first) · Go to
  sentence [ ] Go · *Practice*: Practice again or Skip practice (bypass warm-up) ·
  *Holding the button*: Held-press limit (note) · *Research team*: Switch participant… ·
  Reset progress… (red, asks first) · a note on rounds (`repeat<n>`).
- Saving: Saved to, Folder access (Allowed, Ask again or Not allowed), Not saved yet, Backup copies, Storage used (note) ·
  Save all recordings now · Save backup copies again · Choose folder… · Use ZIP files ·
  Delete backup copies… and Clear storage… (red, ask first). Recordings that are not
  saved anywhere yet can never be deleted here: Clear storage asks to save them first.
- In dark mode the sheet is dark grey with an edge, so it stands out from the dimmed
  page. On a phone a setting's name sits above its choice, which takes the full width
  (never cut off).
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
| Speaking before Start (not in the first 1.5 s after a take: people often say a word after Stop) | Not recording yet. Press Start first, then read. |
| Start held ≥ 1 s (push-to-talk habit) | Dialog "Press once, then let go": Press Start once and let go. It records until you press Stop. (take not used) |
| Stop held ≥ 1 s | Take kept; the next sentence says, once: "Let go right after pressing." |
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
| Camera/microphone lost | Screen: what happened, "Close other apps that use the camera or microphone, then press Reconnect. We’ll keep your place.", **Reconnect** |
| Camera and microphone not allowed | Screen: "Please allow the camera and microphone, then reload this page.", how to allow them on this device, **Reload** |
| Browser cannot record (e.g. inside another app) | Screen: "Please open this page in Safari, Chrome or Edge: copy the link, then paste it there.", **Copy link** (then "Link copied") |
| Page could not load | Screen: "Please reload this page. We’ll keep your place.", **Reload** (the technical detail goes to the event log only) |
| Page already open in another tab | Screen: **Use this tab instead** (the other copy stops) |
| This tab was taken over | A neutral screen (nothing is wrong): "Recording continues in the other tab. You can close this one." · Use this tab instead (text) |

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
  the microphone or the sound output is Bluetooth (the output where the browser lists it:
  Chrome, Edge), there is no cue and recording starts at the press. The sentence turns green once the recorder reports that it runs and has run
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
  anything recorded (Clear progress, Go to, Practice again) starts the next round. The
  last sentence can still be redone before that, within the same round.
- **One usable recording per sentence and round.** When a usable recording replaces an
  earlier one of the same sentence (Redo, Previous, Go to, Practice again), the earlier
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
- Browser scenario tests (52 in Chrome, 41 in WebKit, the iPad/iPhone engine, and in Firefox):
  - first-run flow end to end, including the test recording, practice and the Redo
    lesson;
  - every error path, Redo (also after a reload, and of a part's last sentence),
    rounds, recorder start failures with silent retry, the bitrate cap on a 16 kHz
    microphone, storage failures, a 22-second take, two open tabs;
  - folder and ZIP saving (backups), every Settings option, theme, sign-in.
- Screenshots of every screen on:
  - phone, upright and sideways, also inside Safari's bars (375×553, 750×340: a page
    taller than the screen is flagged, since its bottom button would need scrolling);
  - iPad mini upright, iPad upright and sideways;
  - laptop;
  - in light and dark.
- Independent reviews of the screenshots and flows:
  - a first-time participant's view;
  - a product designer's view;
  - a research data manager's view.
