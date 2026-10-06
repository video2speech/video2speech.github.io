# Recorder checklist (v208)

<!-- Keep in step with LEGACY_OPTIONS / LEGACY_LABELS in tools/e2e/test_next_app.py. -->

Re-run this list before every hand-over. It has three parts:
- A. everything the earlier page (`app.html` v114) offered;
- B. every requirement stated for the redesign;
- C. what the independent reviews found.

Each item says where it lives now and how it is verified.

**Tests** are scenarios in `tools/e2e/test_next_app.py` (run silently in Chrome, WebKit and
Firefox). **Shots** are `tools/e2e/screenshots.py` (6 screen shapes, light and dark).

## A. Parity with the earlier page

| # | Earlier page | Now | Verified by |
|---|---|---|---|
| A1 | Sign-in and version gate | Same gate (`app.html` head); sign-in page restyled | `signin` |
| A2 | "Initialize Camera + Microphone" | Welcome → Begin → camera and microphone check | `first_run` |
| A3 | Warm-up / Bypass warm-up (startup choice) | Practice runs once per participant (also after switching the sentence set); Settings → **Skip practice (bypass warm-up)** | `first_run`, `settings_parity` (Skip practice from sentence 1) |
| A4 | Select Sentence Set (`50words_350sentences`, `Open_300sentences`) | Settings → **Sentence set**, same option names, with a one-line description (progress kept per set) | `settings_parity` (option words) |
| A5 | Previous / Next / Skip | Settings → **← Previous sentence**, **Next sentence (skip) →** (the old Next and Skip did the same) | `settings_parity` |
| A6 | (none) | Settings → **Go to sentence N** | `settings_parity` |
| A7 | Start/Stop button, Space | Start/Stop button; Space, Enter, →, PageDown (clickers, switches) | `normal`, `keyboard`, `clicker` |
| A8 | Redo button, ← | Redo button; ←, PageUp. Records the previous sentence again, then returns | `redo`, `clicker` |
| A9 | Save All | Settings → **Save all recordings now**; also automatic (folder) or at every break (ZIP) | `zip_backups`, `folder`, `break_zip` |
| A10 | Storage info line | Settings → Saving: not saved yet, backup copies, storage used | `zip_backups` |
| A11 | "Near storage limit, click Save All" | Recording stops at the save screen when the device is nearly full | `storage_full` |
| A12 | Reset Progress | Settings → **Reset progress…** (asks first; explains rounds) | `rounds`, `settings_parity` |
| A13 | Clear Storage | Settings → **Clear storage (delete recordings on this device)…** (says how many are unsaved) | `settings_parity` |
| A14 | Logout | Settings → **Sign out (log out)**; returns to this page after signing in | `finish_settings` |
| A15 | Recording Resolution / Quality / Frame Rate, Audio Mode, Mirror Video Display | Settings → Recording quality: same names, same option texts word for word ("15 Mbps - Research Quality", "Fallback - Browser Default", …), same defaults | `finish_settings`, `settings_parity` (option words) |
| A16 | Camera/microphone choice (browser default) | Settings → Camera, Microphone; Bluetooth warning with one-tap switch | `bluetooth`, `settings_parity` |
| A17 | Modal dialogs, Enter activates | Dialogs: Enter = highlighted button, Esc = safe choice, focus trapped | `hold`, `no_speech`, `finish_settings` |
| A18 | Recording timer | Shown only after 20 s (see B9) | `long_take` |
| A19 | Too loud / too quiet warnings, retry | Recording check: no_speech (the approved rules fold "too quiet" into it), too_loud, no_audio; **Keep it and go on** after 2 failures | `no_speech`, `too_loud`, `no_audio` |
| A20 | Camera/microphone health | Track ended, muted, frozen picture (own monitor video) → Reconnect, same sentence | `device`, `long_take` |
| A21 | Completion view | "All sentences are done" | `rounds` |
| A22 | Progress text (Warm-up 1/5, 1/350) | Top bar: "Practice 1 of 5", "Part 2 of 7 · Sentence 14 of 50 · 37 to go before the break" | `first_run`, `break_zip` |
| A23 | Card height fixed by the longest sentence | One sentence size per screen; room kept for the longest sentence | `fit` |
| A24 | File names `<sentence>_<pos>-<total>_repeat<n>_<time>[_redo]` | Unchanged | `normal`, `rounds` |
| A25 | Sidecar JSON (`startedAt`, `quality{label,…}`, `frameRate{label,fps}`, `audioMode{mode,label}`, `requestedVideoConstraints`, `requestedAudioConstraints`, `stopDelayMs`, `mediaAtStart`, `qcIssue`, `qcFailuresInARow`, `audioQualityWarning`, `downloadClearPolicy`, …) | Every legacy key, same shape, plus participant, status, check metrics, time markers | `normal` (legacy keys) |
| A26 | IndexedDB `VideoRecorderDB` v2, progress by set | Same database and record shape; progress per participant, mirrored to the old key | `legacy`, `rounds` |
| A27 | repetitionCount (+1 when the set is completed) | Same meaning; `round` decides `repeat<n>` (B20) | `rounds` |
| A28 | Hotfixes v113/v114: key auto-repeat ignored, no clearing without confirmation, no skipping on silence, recording border, save dialog first | Kept: input rules, confirmed saves, recording check, green card + screen frame, picker first | `hold`, `break_zip`, `no_speech`, `normal`, `zip_picker` |
| A29 | Dark page only (dark background, white sentence, green while reading, red ring while recording) | Light by default (recommended: lights the face, easier reading, fewer reflections); dark in the top bar and Settings. **Owner to confirm the default.** | `finish_settings`, shots |
| A30 | "Update available" prompt every 60 s | Version checked only when the page opens (never mid-session) | gate in `app.html` |
| A31 | How to Record checklist: "Position the camera below chin level and angle it upward so your mouth, throat, and cheeks are visible" | Camera check step 1: one head oval and "Put your face inside the oval." — the owner decided (2026-10-05) that participants only need their face in the frame; the playback asks "Can you see your face and hear yourself clearly?". The camera position stays a setup tip in docs/recorder.md | `first_run` |
| A32 | Warm-up explained saving and ran a real Save All | Practice done screen: in ZIP mode the practice recordings are saved once (same steps as after every part); in folder mode it says where recordings go | `first_run`, `practice_save` |
| A33 | ← pressed repeatedly walked back several sentences | Redo reaches only the previous sentence (approved plan, 2026-10-03); a second ← cancels the Redo. Settings → Previous / Go to reach further back | `redo`, `clicker` |
| A34 | The last sentence could be redone after completion | Redo of the last sentence before **Finish**; afterwards Go to / Reset progress start the next round | `rounds` |
| A35 | Recording stopped after 8 s without sound | Removed (approved plan): a quiet start is not a failure; only real device failures stop a take | `long_take` |
| A36 | Stop beep | Start sound before recording, "saved" / "retry" tones after the check | code review |
| A37 | ZIP: flat, `video-recordings-<date>.zip` | `<participant>_video-recordings-<time>_blockNN.zip`, files under `<participant>/` (same layout as folder mode; keeps participants apart). Approved by the owner (2026-10-05). | `break_zip` |
| A38 | On-screen counter "n / 350" | Top bar: "Part 2 of 7 · Sentence 14 of 50"; the overall n/350 in Settings → Position | `first_run`, `settings_parity` |

## B. Requirements for the redesign

| # | Requirement | How it is met | Verified by |
|---|---|---|---|
| B1 | Usable by a first-time patient without help | One purpose and one main button per screen; Welcome lists 3 stages as plain rows; the check one step at a time; How to record taught inside the coached practice, one instruction at a time (the ? button shows it as a short dialog) | `first_run`, `keyboard`, `clicker`, `help`, reviews |
| B2 | Always obvious whether it is recording | Not recording: grey pill "Not recording", grey sentence. Recording: green card, green sentence, solid green "Recording" pill, green frame round the screen, moving waveform, Stop button | `normal`, shots |
| B3 | Reading while not recording | "Not recording yet. Press Start first, then read." | `speech_before_start` |
| B4 | Press-and-hold habit (Enter/Space/touch) | Held Start → take thrown away + "Press once, then let go" dialog, same sentence; held Stop → take kept, gentle tip; limit 1/2/3 s in Settings | `hold` |
| B5 | Whole sentence recorded | 0.06 s cue, recording ~0.1 s after the press (no cue if output is slow); green once the recorder runs; fixed 0.7 s after Stop | `normal`, `tail` |
| B6 | Patient knows to redo a misread sentence, and how | Practice 3 teaches it by doing a Redo ("Now try Redo. It records the last sentence again."); reminder in practice 4; the ? dialog; Redo shows the sentence it would record again; Cancel redo | `first_run`, `redo`, `help` |
| B7 | Minimal cleaning afterwards | Exactly one usable take per sentence and round in `<participant>/`; every replaced or failed take in `not_used/` with its reason; `logs/superseded.json` | `redo`, `redo_folder`, `part_end_redo`, `rounds` |
| B8 | Mistakes never skip or lose a sentence | Every failure returns to the same sentence; progress only moves when a take is stored (one transaction); storage failure → back to that sentence | `store_failure`, `reload`, `device`, `timeout` |
| B9 | Calm screen: sentence central, few colours, no competing black buttons | Neutral palette, green only for recording, amber only for problems; soft green Start; clock only on takes over 20 s | shots, reviews |
| B10 | Sentence size: continuous sentence, not keywords; never too small | Per-device size rule (90% on one line, ≥ 18 characters per line, 2 lines reserved) | `fit` |
| B11 | Every device shape | Phone upright/sideways, tablet upright/sideways, computer: layout rules per shape | `fit`, shots (6 shapes × 2 themes) |
| B12 | Orientation advice for patients | docs/recorder.md, "Device recommendations" | — |
| B13 | Same media settings as the earlier page | Same constraints and defaults; 64 kbps audio only for low-rate (Bluetooth) microphones | `finish_settings`, `low_rate_mic` |
| B14 | Zoom-like microphone test | Records 5 s, plays it back, asks "Did you see and hear yourself clearly?" | `first_run`, `mic_test_silent` |
| B15 | "Recording stopped…" must not appear without cause | Start failures retried silently (3 tries); only real failures are reported | `recorder_retry`, `low_rate_mic` |
| B16 | Settings complete but out of the way | Gear button; all of A plus held-press limit, backups, rounds note, event log | `settings_parity` |
| B17 | Sign-in page in the same style, light/dark | `index.html` with `css/base.css` | `signin` |
| B18 | ID example like SEMG1 | Placeholder "e.g. SEMG1"; saved in capitals | `first_run` |
| B19 | Silent tests | All browsers muted (`common.launch`) | every test |
| B20 | Repeated passes stay apart | Round = pass through the set (`repeat<n>`); after the last sentence anything recorded is the next round | `rounds` |
| B21 | Two copies of the page open | Second copy asks; taking over stops the first | `two_tabs` |
| B22 | ZIP saves on tablets and phones | At most 60 recordings per ZIP; confirmed saves kept as backup copies (≤ 100) until space is needed; can be saved again | `zip_backups`, `break_zip` |
| B23 | Folder saving (computers) | Written and read back before leaving the browser; permission asked during a click; never silently elsewhere | `folder`, `folder_new_session`, `folder_denied`, `real_picker` |
| B24 | Practice can be repeated | Settings → Practise again; afterwards back to the same sentence | `practice_again` |
| B25 | A Redo survives a reload / End for today | Pending Redo stored with progress | `redo_reload` |
| B26 | Long takes | 60 s limit (restarts the sentence); no false camera failure | `timeout`, `long_take` |
| B27 | Not pushed without approval | Commits stay local; push only after the user's OK | process |
| B28 | Saving explained in the tutorial (requested 2026-10-03/04) | Practice done (ZIP mode): "Now save your practice recordings. You will do the same after each part." — saved once with the real steps, then the real sentences; folder mode names the folder. See A32 | `first_run`, `practice_save`, `practice_again` |
| B29 | Old names kept where the research team knows them | Settings names and option texts as on the earlier page (A4, A12, A15) | `settings_parity` |
| B30 | The sentence is the only focal point while reading (2026-10-05) | No card tint, ring or screen frame; no waveform under the sentence; formal recording shows no text | `normal`, shots |
| B31 | Recording obvious on the sentence itself; recording sign red | Sentence vivid green on a highlight; "● Recording" red dot; soft red Stop | `normal`, shots |
| B32 | Camera picture and sound level: off = grey/still, on = live; never competing | Monitor in the card's corner: grey when not recording, live while recording | shots |
| B33 | Practice instructions: one at a time, prominent, intent explicit, never conflicting | Coach panel: what happened (small), the one next action (large), rarely why; problems replace the first line | `first_run`, `practice_again` |
| B34 | On computers, Space and ← taught as the controls | The coach and the ? dialog name the keys; buttons show their key | `first_run`, `help`, shots |
| B35 | Camera guide: one head in the middle, as on the first version; do not change it (owner, 2026-10-05) | One head oval in the middle (74% of the picture's height, 54% for an upright picture), the rest dimmed | shots |
| B37 | Misread recordings are never deleted or overwritten (owner, 2026-10-05) | Every attempt is its own file; a replaced one moves to `not_used/` (status superseded) with its sidecar; takes leave the device only once saved | `redo`, `redo_folder`, `part_end_redo` |
| B36 | No hint text near the sentence in formal recording | "Read it out loud…" removed; 20 s reminder is the Stop pulse and clock only | `normal`, `long_take` |
| B38 | Apple-level appearance, interaction and clarity before any single requirement (owner, 2026-10-05) | Redesign v209: system font, white/black screens, one centred column per screen, blue = move on, grouped Settings with pages, one step at a time; independent design and first-time-user reviews | shots, reviews |
| B39 | Sentence as high as balance allows (owner: rather lower than unbalanced) | Every device: sentence, guide and buttons as one group a little above the middle (phones held sideways: the sentence on the left, the guide and buttons on the right) | shots |
| B40 | Start: no noticeable delay, never a missed word; cue not in the recording | Soft 0.04 s cue; recording ≤ 0.16 s after the press (output, input and room delay counted; no cue if that is longer); green once the recorder has run 0.08 s without an error (~0.22 s after the press); presses in the first 0.4 s on the recording screen ignored | `normal` |
| B41 | The 5-second test is never saved | Played back from memory only; only its result is in the event log | code |
| B42 | Settings not confusing | Settings app layout: a short list, one page per topic with group titles, red for destructive actions; Clear storage never deletes unsaved recordings | `settings_parity`, `settings_fit`, shots |

## C. Review findings (2026-10-04)

| # | Finding | Fix | Verified by |
|---|---|---|---|
| C1 | Held Stop threw away a good take | Held Stop keeps the take; tip on the next sentence | `hold` |
| C2 | "Saved" shown on the new sentence, not the one saved | "Saved" sits on the Redo button, next to the saved sentence | `normal`, `first_run` |
| C3 | No Redo for a part's last sentence | Pause on the last sentence (Saved, Redo, Take a break) | `part_end_redo`, `break_zip` |
| C4 | Settings lacked options of the earlier page | Full parity (part A) | `settings_parity` |
| C5 | Two usable takes of one sentence after Redo/jumps | One usable take per sentence and round, enforced in storage | `redo`, `rounds` |
| C6 | A Redo lost on reload | Stored with progress | `redo_reload` |
| C7 | Storage failure could skip a sentence | Back to that sentence; repeated failures explained | `store_failure` |
| C8 | A mistaken "Yes, it saved" lost recordings | Backup copies | `zip_backups` |
| C9 | Practise again lost the place | Returns to the same sentence | `practice_again` |
| C10 | Redo lesson blocked Start (single-switch users) | Start always works; Redo is suggested | `practice_again`, `first_run` |
| C11 | Frozen-picture check used the hidden preview | Own always-rendered monitor video | `long_take` |
| C12 | Recorder stop could hang | 3 s limit | code review |
| C13 | Page hidden counted as a device failure | Own status `aborted_hidden` | code review |
| C14 | Running clock from 0:00 hurries slow speakers | Clock only after 20 s | `long_take`, `normal` |
| C15 | Green used for "Saved" as well as recording | "Saved" pill is neutral; green means recording | shots |
| C16 | Two-sentence messages broke mid-sentence | Each sentence wraps as a unit | shots |
| C17 | Break screen could wait forever on a slow folder | Stops waiting after 20 s, says saving continues | code review |
| C18 | Sign out lost the page | Sign-in returns to this page | `finish_settings` |
| C19 | Two tabs could record into the same storage | Tab lock | `two_tabs` |
| C20 | Second review (parity): renamed options, missing camera protocol, saving not taught, sidecar keys, held-press limit not recorded, Esc closing Settings, silent "nothing to save/delete", practice repeated per set | All fixed (A3, A4, A12, A15, A25, A31, A32; `timing.holdMs` = setting) | `settings_parity`, `practice_save`, `set_switch`, `normal` |
| C21 | Second review (data): on a full device "Yes, it saved" removed the backup copies at once | The most recent ZIP's copies are removed only after "It is saved — make room" on the save screen; older copies go first | `storage_full` |
| C22 | One failed folder write (superseded.json) stopped all later folder writes | Every folder job catches its own error; break/done screens never wait on a failure | `folder_failure` |
| C23 | Stale backup ids (earlier page's Save All / Clear Storage) hid unsaved recordings | Unsaved = takes not in the backup list, counted by id; stale ids dropped | `stale_backups` |
| C24 | A store failure noticed after End for today was forgotten; a rollback could erase a newer Redo | Progress goes back at once (also with no session on screen); only the failed take's own entry is undone | `store_failure_late`, `store_failure` |
| C25 | Redo of the very last sentence lost on reload; Practise again + End for today lost the place | Not "completed" while that Redo is pending; the return place is stored with the last practice take | `rounds`, `practice_again` |
| C26 | Merged folders/ZIPs could hold two usable takes of a sentence | `logs/superseded.json` lists all sets; `tools/apply_superseded.py` moves listed files to `not_used/` after merging | code review |
| C27 | Second review (participant): Redo lesson contradicted by "Press Start first"; lesson lost if Start pressed | During the lesson: "Not recording yet. Press Redo first."; practice 4 offers the lesson again | `first_run`, `practice_again` |
| C28 | A forgotten Stop had no prompt until the 60 s cut-off | At 20 s: "Still recording. Press Stop when you have finished." and Stop pulses | `long_take` |
| C29 | Done screen said "You can close this page" with unsaved recordings | Then: "Please save your recordings before you close this page.", no green check | `finish_settings` |
| C30 | The coach's step chip looked like a second Start button | Step strip is plain progress text (1 Start → 2 Read → 3 Stop) | shots |
| C31 | Buttons overflowing ("Take a break" sideways, 175% zoom); Redo row hidden under "Practice now" on small phones; Welcome stage 3 under "Begin" sideways | Flexible button width; compact How to record on phones; stages side by side sideways; screenshots.py flags any spilling button | shots (OVERFLOW check) |
| C32 | Messages and the hidden step strip moved the sentence | Icon inline with the text; the strip keeps its room | shots |
| C33 | Wording: hold dialog, keep dialog, "Break after 50 more", iOS download hint, Next (skip) without confirmation | "That recording was not kept…"; reason-only keep dialog; "50 to go before the break"; "⬇ next to the web address"; Skip asks first | `hold`, `settings_parity` |
| C34 | Owner's review of v204 (2026-10-05): body outline on the camera guide; too many green/bright things while recording (waveform); keyboard not taught; Redo lesson unclear and mixed with other instructions; camera hidden while recording; hint text near the sentence | Redesigned by the principles in recorder-design.md (B30–B36) | see B30–B36 |
| C35 | "Not recording yet" could fire right after a take (it counted the take's own last second) | Only sound after the waiting began counts | `first_run`, `speech_before_start` |
| C36 | Independent reviews of v209 (2026-10-05): first-time participant walkthrough, Apple-level design critique, requirements audit (subagents, as the owner asked) | "Saved" used for a take and for saving files → "Recorded" for a take; "Did the file save?" had three equal grey answers → one blue "Yes, I see it", "Save it again", "Not sure" as text, `part02.zip`; break gave two instructions → one; Redo lesson crowded → Redo as large as Start, set apart; phones had an empty middle → one centred group everywhere; green ticks and a red "Live" dot broke the colour rules → neutral ticks, no live badge; two button shapes → capsules; check picture moved → fixed; recording highlight fainter than the waiting text → clear green band, dark green text; practice save step had been dropped → restored; keys named in every message on computers; 2 s grace before "Not recording yet"; clock on Stop instead of under the sentence; Clear storage refuses unsaved recordings; microphone shown on the check; Play it again | `first_run`, `break_zip`, `speech_before_start`, `long_take`, shots |
| C37 | Second review round (2026-10-05) | Redo lesson: Redo the only filled button, Start an outline; real sentences: smaller guide (80 px), messages two short lines, no wider than Start; "✓ Recorded" moved from the Redo button to a quiet line above Start; practice end says what it was ("That was the last practice sentence."); lines break between phrases; highlight with room around the letters (dark mode opaque); neutral symbols; "We’ll keep your place"; "Finish part 2"; ZIP names `SEMG1_part02_<time>.zip`; no pre-chosen answer in "Did the file save?" (the dialog takes the focus, so no key reaches the screen behind); backup copies never removed by count; main buttons keep the keyboard focus after the save question; presses ignored for 0.4 s after any dialog closes; a storage-full screen of its own; no start cue where the output delay is not reported or with Bluetooth; Settings pages switch title and content together | `first_run`, `normal`, `break_zip`, `storage_full`, `settings_parity`, shots |
| C38 | Third review round (2026-10-05) | A key or button held down ran on through the next screens (part end → break skipped or a ZIP download started; Welcome → the test started): auto-repeat never presses a button, a key or finger still down from the press that changed the screen does nothing on the new one, and for 0.4 s after any screen or step change clicks are ignored (double tap); "It is saved — make room" is never pre-focused; the 0.4 s guard also after Settings and Reconnect; Start and Redo 16 px apart on every device, one width for Start, the Redo lesson and messages; in the practice Redo keeps its room, so nothing moves; waiting is plain grey text (only Recording is a red capsule); the check centred on computers; the page behind a dialog loses its colour; parts shown in grey (blue only for the button); no start cue with Bluetooth headphones or speakers where the browser lists them; folder mode's device-full screen no longer says "saved" above "not in the folder yet" | `held_keys`, `double_tap`, shots |
| C39 | Fourth review round (2026-10-05) | Redo cut off ("Record this sentence a…") after the shared width → two lines, "↶ Redo" over the sentence, the Redo lesson's shape, one fixed place; the break ran off a sideways phone → its top follows the height; a double press 0.3–1 s apart stopped an empty take or cancelled a Redo → a press that would undo the one just made counts only after 1 s; Start turning into Continue at a part's end → 0.4 s guard; a double press on Save recordings downloaded twice and on Reconnect opened the camera twice → one at a time; a held Enter re-submitted text fields → auto-repeat of Space and Enter never acts; the save question could not be answered with keys or a clicker → the first press highlights "Yes, I see it"; a top-bar button reached with Tab keeps Space and Enter; device full in folder mode said "saved" while still writing; the iPhone make-room hint lost its icon; camera instruction names the device ("Put the iPad…"); the test phrase shown before the test; "No, try again" goes back to positioning; wording: "It records the sentence before this one again.", "Sit closer, then press Start.", "We’ll keep your place on this device.", "Rest after each part, or stop and carry on another day."; lines never split "turns green", "cheeks and throat", "last sentence"; the page behind a dialog fades | `held_keys`, `double_tap`, `redo`, `first_run`, `keyboard`, `clicker`, shots |
| C40 | Fifth review round (2026-10-05) | The make-room step's explanation was hidden (only "It is saved — make room" showed) → the panel shows, the lead is cleared; a double tap on "Not sure" pressed Save recordings behind the dialog → closing a dialog counts as a screen change; a refused camera permission said "disconnected" (a DOMException's code cannot be changed) → the permission screen; the 1 s window also swallowed Start right after a take or after Redo → only a press that undoes the one just made waits 1 s; Redo has Start's width (no longer grows and shrinks) and a long sentence on it shrinks to fit; the practice note two lines again ("End for today" back on a sideways phone); computers: "Tilt the screen back…"; "Can’t hear it? Turn the volume up…"; the save question's choosing press waits 1 s after the highlight; the break and Done share one top (a little lower on upright tablets); Start and Redo 24 px apart (two bars of one width: a slightly low tap must not land on Redo); on a sideways phone a long sentence on Redo takes a second line | `camera_denied`, `save_keys`, `redo`, `storage_full`, shots |

## Left for the user to decide

- The sign-in page says "This website is solely for displaying reading materials", while
  the page also records video and sound (which do stay on the device). The wording is
  unchanged.
- Possible cut-off at the end of a sentence (`speechAtEnd`) is recorded in the sidecar
  only, as decided; it never rejects a take.
- Saving the practice recordings at Practice done (ZIP mode). It teaches saving once, as
  the owner asked and as the legacy warm-up did, while little is at stake. But it puts
  the most technical step — a browser download, then finding and confirming the file —
  between the practice and the first real sentence. A first-timer alone may stop there.
  The alternative is to keep the practice takes for the part-1 ZIP and meet saving first
  at the first break.
- "Not recording yet" sensitivity: 0.5 s of speech while waiting, at most every 6 s. A
  helper's voice, or a participant rehearsing aloud, can set it off. A proposal to approve
  or reject: 1.5 s of speech, at most once per sentence.
- The held-press limit (1 s; Settings offers 2 or 3 s). People who cannot let go within
  1 s lose takes until a helper changes it. A proposal to approve or reject: keep
  recording when nobody spoke during the hold.
- Staying signed in on the device. Today the sign-in lasts as long as the browser tab,
  so a participant alone has to type the username and password each time.
- The default theme (light recommended).
