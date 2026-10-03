# Browser scenario tests

Drive real browser engines against a local copy of the site and print PASS/FAIL per
check. Each script starts its own static server on a free port.

```bash
python3 -m venv ~/.venvs/v2s-e2e
~/.venvs/v2s-e2e/bin/pip install playwright
~/.venvs/v2s-e2e/bin/playwright install webkit firefox   # only for --engine webkit/firefox

~/.venvs/v2s-e2e/bin/python tools/e2e/test_legacy_hotfix.py              # legacy app.html (v114)
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py                   # new recorder, Chrome, all scenarios
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py --engine webkit   # Safari's engine (iPad/iPhone stand-in)
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py --engine firefox
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py folder hold       # only these scenarios
~/.venvs/v2s-e2e/bin/python tools/e2e/screenshots.py --engine webkit OUT_DIR --only phone ipad
```

Chrome runs as the installed Google Chrome (`channel='chrome'`), with a fake camera and
a generated fake microphone (speech-like sound, fan noise, a quiet room, or a clipping tone).

`shims.py` holds two scripts injected before the page loads:

- `MEDIA_SHIM`: a moving canvas as the camera and a synthetic voice as the microphone,
  switchable from the test (`window.__v2sAudio.set('speech' | 'silence' | …)`). Used for
  WebKit and Firefox, which have no fake capture devices, and wherever a test must
  control exactly when the person speaks.
- `FSA_SHIM`: the folder and save dialogs (File System Access API) with Chrome's rules
  — pickers and permission requests only work during a click, a new browser session
  starts at `prompt`, permission can be refused — backed by the browser's private file
  system so the test can read back what was written. `real_picker` additionally checks
  through DevTools that the real Chrome folder picker opens from the click.
