# Recorder checklist (v204)

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
| A1 | Sign-in and version gate | Same gate (`app_next.html` head); sign-in page restyled | `signin` |
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
| A30 | "Update available" prompt every 60 s | Version checked only when the page opens (never mid-session) | gate in `app_next.html` |
| A31 | How to Record checklist: "Position the camera below chin level and angle it upward so your mouth, throat, and cheeks are visible" | Camera check: the same instruction, a head-and-neck outline, and the playback question "Can you see your mouth, cheeks and throat…?"; docs/recorder.md device advice follows it. **Owner to confirm it is still the protocol.** | `first_run` |
| A32 | Warm-up explained saving and ran a real Save All | Practice done screen: in ZIP mode the practice recordings are saved once (same steps as after every part); in folder mode it says where recordings go | `first_run`, `practice_save` |
| A33 | ← pressed repeatedly walked back several sentences | Redo reaches only the previous sentence (approved plan, 2026-10-03); a second ← cancels the Redo. Settings → Previous / Go to reach further back | `redo`, `clicker` |
| A34 | The last sentence could be redone after completion | Redo of the last sentence before **Finish**; afterwards Go to / Reset progress start the next round | `rounds` |
| A35 | Recording stopped after 8 s without sound | Removed (approved plan): a quiet start is not a failure; only real device failures stop a take | `long_take` |
| A36 | Stop beep | Start sound before recording, "saved" / "retry" tones after the check | code review |
| A37 | ZIP: flat, `video-recordings-<date>.zip` | `<participant>_video-recordings-<time>_blockNN.zip`, files under `<participant>/` (same layout as folder mode; keeps participants apart). **Owner: scripts that unzip must look in `<participant>/`.** | `break_zip` |
| A38 | On-screen counter "n / 350" | Top bar: "Part 2 of 7 · Sentence 14 of 50"; the overall n/350 in Settings → Position | `first_run`, `settings_parity` |

## B. Requirements for the redesign

| # | Requirement | How it is met | Verified by |
|---|---|---|---|
| B1 | Usable by a first-time patient without help | Welcome lists 3 stages; How to record (3 steps + Redo); coached practice with a Start → Read → Stop strip; one main button per screen | `first_run`, `keyboard`, `clicker`, reviews |
| B2 | Always obvious whether it is recording | Not recording: grey pill "Not recording", grey sentence. Recording: green card, green sentence, solid green "Recording" pill, green frame round the screen, moving waveform, Stop button | `normal`, shots |
| B3 | Reading while not recording | "Not recording yet. Press Start first, then read." | `speech_before_start` |
| B4 | Press-and-hold habit (Enter/Space/touch) | Held Start → take thrown away + "Press once, then let go" dialog, same sentence; held Stop → take kept, gentle tip; limit 1/2/3 s in Settings | `hold` |
| B5 | Whole sentence recorded | Recorder must run 0.2 s before the sentence turns green; fixed 0.7 s after Stop | `normal`, `tail` |
| B6 | Patient knows to redo a misread sentence, and how | How to record and practice teach it (practice 3 does a Redo); reminder in practice 4; Redo shows the sentence it would record again; Cancel redo | `first_run`, `redo` |
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
| B28 | Saving explained in the tutorial (requested 2026-10-03/04) | See A32 | `practice_save` |
| B29 | Old names kept where the research team knows them | Settings names and option texts as on the earlier page (A4, A12, A15) | `settings_parity` |

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

## Left for the user to decide

- The sign-in page says "This website is solely for displaying reading materials", while
  the page also records video and sound (which do stay on the device). The wording is
  unchanged.
- Possible cut-off at the end of a sentence (`speechAtEnd`) is recorded in the sidecar
  only, as decided; it never rejects a take.
