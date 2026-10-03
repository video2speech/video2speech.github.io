# Browser scenario tests

Drive the installed Google Chrome with a fake camera and a generated fake microphone
(speech-like sound, fan noise, a quiet room, or a clipping tone) against a local copy of the site.

```bash
python3 -m venv ~/.venvs/v2s-e2e
~/.venvs/v2s-e2e/bin/pip install playwright
~/.venvs/v2s-e2e/bin/python tools/e2e/test_legacy_hotfix.py   # legacy app.html (v113)
~/.venvs/v2s-e2e/bin/python tools/e2e/test_next_app.py        # new recorder (app_next.html)
```

No `playwright install` is needed: the tests use the system Chrome (`channel='chrome'`).
Each script starts its own static server on a free port and prints PASS/FAIL per check.
