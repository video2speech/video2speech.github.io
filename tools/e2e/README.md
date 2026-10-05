# Browser scenario tests

Drive real browser engines against a local copy of the site and print PASS/FAIL per
check. Each script starts its own static server on a free port.

**Every run is silent.** `common.launch()` mutes the browser (Chrome `--mute-audio`,
Firefox `media.volume_scale` 0, and `shims.MUTE_SHIM` for every engine), so the
recorder's cue sounds and test playback never play on the machine running the tests.
Launch browsers only through `common.launch()`.

```bash
python3 -m venv ~/.venvs/v2s-e2e
~/.venvs/v2s-e2e/bin/pip install playwright
~/.venvs/v2s-e2e/bin/playwright install webkit firefox   # only for --engine webkit/firefox

~/.venvs/v2s-e2e/bin/python tools/e2e/test_legacy_hotfix.py              # legacy app.html (v114)
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py                   # new recorder, Chrome, 51 scenarios
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py --engine webkit   # Safari's engine (iPad/iPhone stand-in), 40 scenarios
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py --engine firefox
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py hold redo fit     # only these scenarios
~/.venvs/v2s-e2e/bin/python tools/e2e/screenshots.py --engine webkit OUT_DIR --only phone ipad --theme light
```

Chrome runs as the installed Google Chrome (`channel='chrome'`), with a fake camera and
a generated fake microphone (speech-like sound, fan noise, a quiet room, or a clipping tone).

`shims.py` holds scripts injected before the page loads:

- `MUTE_SHIM`: silence (see above).
- `MEDIA_SHIM`: a moving canvas as the camera and a synthetic voice as the microphone.
  - The sound can be switched during a test:
    `window.__v2sAudio.set('speech' | 'silence' | 'fan' | …)`.
  - `sessionStorage.__audio_rate` sets the microphone's sample rate (e.g. 16000, as
    with Bluetooth headsets).
  - Used for WebKit and Firefox, which have no fake capture devices, and wherever a
    test must control exactly when the person speaks.
- `FSA_SHIM`: the folder and save dialogs (File System Access API) with Chrome's rules,
  backed by the browser's private file system so the test can read back what was
  written.
  - Pickers and permission requests only work during a click.
  - A new browser session starts at `prompt`.
  - Permission can be refused.
  - `real_picker` additionally checks through DevTools that the real Chrome folder
    picker opens from the click.

`test_next_app.py` adds a few more:
- `FLAKY_RECORDER`: MediaRecorder start failures, like Chrome's "Encoder
  initialization failed".
- `BLUETOOTH_MIC`: AirPods as the microphone, with a built-in one available.
- `FAIL_COMMIT`: makes storing a take fail (`window.__failCommits = n`, optionally
  `window.__failQuota = true` for a full device, `window.__failDelayMs` for a failure
  noticed late).
- `FAIL_SUPERSEDE_LOG`: makes one folder step fail (`window.__failMarks = n`).

`screenshots.py` prints `OVERFLOW` for anything wider than the screen or the settings
panel, and for any button whose label spills over its edge, and one line per take with
its check result, so a screenshot never silently shows the wrong state.
- `window.__V2S_TEST = { testRecordMs: 1200 }`: shortens the 5-second microphone test
  so each session start stays quick.

`settings_parity` lists every option of the earlier page (`LEGACY_OPTIONS`); keep it in
step with `docs/recorder-checklist.md`.
