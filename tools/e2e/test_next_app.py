"""Scenario tests for the new recorder (app_next.html, or app.html after the switch).

Run:
  <venv>/bin/python tools/e2e/test_next_app.py                    # every scenario, Chrome
  <venv>/bin/python tools/e2e/test_next_app.py --engine webkit     # Safari's engine
  <venv>/bin/python tools/e2e/test_next_app.py --engine firefox
  <venv>/bin/python tools/e2e/test_next_app.py normal folder ...   # chosen scenarios
"""
import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
import zipfile

from playwright.async_api import async_playwright

from common import NEXT_PAGE, Checks, launch, static_server

ENGINE = 'chrome'

STATE_JS = """() => {
  const ctx = V2S.session.getContext();
  const visible = [...document.querySelectorAll('.screen')].find(s => !s.hidden);
  const msg = document.getElementById('recMessage');
  const active = document.activeElement;
  return {
    screen: visible ? visible.id.replace('screen-', '') : null,
    state: V2S.session.getState(),
    index: ctx ? ctx.progress.currentIndex : null,
    card: document.getElementById('screen-record').dataset.state,
    frame: document.body.dataset.rec || 'off',
    message: msg.classList.contains('is-empty') ? null : document.getElementById('recMessageText').textContent,
    tone: (msg.className.match(/tone-(\\w+)/) || [])[1] || null,
    highlight: ['primaryButton', 'secondaryButton', 'saveStatus'].find(id => document.getElementById(id).classList.contains('is-highlighted')) || null,
    stateText: document.getElementById('recStateText').textContent,
    sentenceColor: getComputedStyle(document.getElementById('sentenceText')).color,
    dialog: V2S.ui.isDialogOpen() ? document.getElementById('dialogTitle').textContent : null,
    focus: active && active.tagName === 'BUTTON' ? active.textContent.trim() : (active ? active.id || active.tagName : null),
    progressMain: document.getElementById('progressMain').textContent,
    progressSub: document.getElementById('progressSub').textContent,
    saveStatus: document.getElementById('saveStatus').textContent
  };
}"""

TAKES_JS = """async () => {
  await V2S.session.flush();
  const out = [];
  await V2S.storage.forEachTake(r => out.push({ index: r.sentenceIndex, status: r.status, fileName: r.fileName,
     speechMs: r.metadata && r.metadata.qc && r.metadata.qc.speechMs, supersedes: r.metadata && r.metadata.supersedes,
     participantId: r.participantId, size: r.size }));
  return out;
}"""

LAST_META_JS = """async () => { await V2S.session.flush(); let m = null; await V2S.storage.forEachTake(r => { m = r.metadata; }); return m; }"""

LIST_OPFS_JS = """async (dirName) => {
  const out = [];
  async function walk(dir, prefix) {
    for await (const [name, handle] of dir.entries()) {
      if (handle.kind === 'directory') await walk(handle, prefix + name + '/');
      else out.push(prefix + name);
    }
  }
  const root = await navigator.storage.getDirectory();
  try { await walk(await root.getDirectoryHandle(dirName), ''); } catch (e) { return []; }
  return out.sort();
}"""

WAVE_PIXELS_JS = """() => {
  const c = document.getElementById('recordWave');
  if (!c.width || !c.height) return 0;
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0;
  for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
  return n;
}"""


async def state(page):
    return await page.evaluate(STATE_JS)


async def takes(page):
    return await page.evaluate(TAKES_JS)


async def wait_for(page, js, timeout=15000):
    await page.wait_for_function(js, timeout=timeout)


async def wait_ready(page, timeout=15000):
    """Until the take is settled: back to ready, a dialog is asking, or another screen took over."""
    await wait_for(page, "() => V2S.ui.isDialogOpen() || ['ready', 'idle'].includes(V2S.session.getState())", timeout)
    # A person needs a moment before the next press; it also keeps the next press
    # outside the 300 ms debounce window.
    await page.wait_for_timeout(450)


def track_downloads(page):
    downloads = []
    page.on('download', lambda d: downloads.append(d.suggested_filename))
    return downloads


async def setup_participant(page, base, participant='P017', save='zip', before_submit=None):
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.fill('#setupId', participant)
    if before_submit:
        await before_submit(page)
    await page.click('#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.click('#setupConfirmYes')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await page.click('#setupFolderChoose' if save == 'folder' else '#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)


async def start_session(page):
    await page.click('#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])', timeout=15000)
    await wait_for(page, "() => document.getElementById('checkOk').getAttribute('aria-disabled') === 'false'")
    await page.click('#checkOk')
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)


async def boot(pw, base, audio='speech', save='zip', **kwargs):
    kwargs.setdefault('engine', ENGINE)
    browser, context, page, errors = await launch(pw, audio=audio, **kwargs)
    await setup_participant(page, base, save=save)
    await start_session(page)
    return browser, context, page, errors


async def record(page, ms=1600, stop=True):
    await page.keyboard.press('Space')
    await page.wait_for_timeout(ms)
    if stop:
        await page.keyboard.press('Space')
        await wait_ready(page)


async def hold_key(page, key='Space', ms=2000):
    await page.keyboard.down(key)
    end = time.time() + ms / 1000
    await page.wait_for_timeout(500)
    while time.time() < end:
        await page.keyboard.down(key)  # auto-repeat
        await page.wait_for_timeout(33)
    await page.keyboard.up(key)


async def set_index(page, index):
    await page.evaluate("""async i => {
      const app = V2S.app.state();
      app.progress.currentIndex = i;
      app.progress.completed = false;
      await V2S.storage.saveParticipantProgress(app.progress);
      await V2S.app.restartSession();
    }""", index)
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    await start_session(page)


async def css_var(page, name):
    return await page.evaluate("n => { const s = document.createElement('span'); s.style.color = getComputedStyle(document.documentElement).getPropertyValue(n); document.body.appendChild(s); const c = getComputedStyle(s).color; s.remove(); return c; }", name)


# ---------------------------------------------------------------- scenarios

async def s_normal(pw, base):
    c = Checks('Normal take: green sentence, red frame, quick next sentence')
    browser, _, page, errors = await boot(pw, base)
    s = await state(page)
    c.check(s['card'] == 'ready' and s['index'] == 0 and s['frame'] == 'off', 'starts on warm-up 1, not recording', s)
    idle = await css_var(page, '--sentence-idle')
    live = await css_var(page, '--sentence-live')
    c.check(s['sentenceColor'] == idle, 'sentence is grey while waiting', (s['sentenceColor'], idle))
    await page.keyboard.press('Space')
    await page.wait_for_timeout(300)
    s = await state(page)
    c.check(s['card'] == 'recording' and s['frame'] == 'on', 'Space starts recording at once: red screen frame', s)
    c.check(s['sentenceColor'] == live, 'sentence turns green to read', (s['sentenceColor'], live))
    c.check(s['stateText'] == 'Recording', 'state label says Recording', s['stateText'])
    await page.wait_for_timeout(1300)
    c.check(await page.evaluate(WAVE_PIXELS_JS) > 0, 'waveform is drawn while recording')
    t_stop = await page.evaluate('performance.now()')
    await page.keyboard.press('Space')
    await page.wait_for_timeout(150)
    s = await state(page)
    c.check(s['card'] == 'finishing' and s['frame'] == 'off', 'Stop: frame off, Saving…', s)
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    t_ready = await page.evaluate('performance.now()')
    meta = await page.evaluate(LAST_META_JS)
    tail = meta['timing']['tailMs']
    c.check(700 <= tail <= 900, 'kept recording 0.7 s after Stop', tail)
    c.check((t_ready - t_stop) - tail < 450, 'next sentence appears right after the tail (no waiting for storage)',
            round(t_ready - t_stop - tail))
    s = await state(page)
    c.check(s['index'] == 1 and s['stateText'] == 'Saved', 'moved on and shows Saved', s)
    t = await takes(page)
    c.check(len(t) == 1 and t[0]['status'] == 'accepted', 'one accepted take', t)
    c.check(t and '_warmup1-5_repeat1_' in t[0]['fileName'], 'legacy-compatible file name', t and t[0]['fileName'])
    mk = meta['markers']
    ordered = mk['sentenceShown'] <= mk['startPress'] <= mk['recorderStart'] <= mk['stopPress'] <= mk['recorderStop']
    c.check(ordered, 'time markers in order', mk)
    c.check(120 <= mk['recorderStart'] - mk['startPress'] <= 400, 'recorder starts after the start sound', mk['recorderStart'] - mk['startPress'])
    c.check(meta['participantId'] == 'P017' and meta['qc']['speechMs'] > 300, 'sidecar has participant and check metrics')
    await page.wait_for_timeout(1600)
    c.check((await state(page))['stateText'] == 'Not recording', 'Saved label fades back to Not recording')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_tutorial(pw, base):
    c = Checks('First-session tutorial: Start/Stop, Redo last, Start over, saving')
    browser, _, page, errors = await boot(pw, base, audio='silence', media='shim')
    s = await state(page)
    c.check(s['tone'] == 'tip' and 'Press Start' in (s['message'] or '') and s['highlight'] == 'primaryButton', 'step 1: Start (highlighted)', s)
    await speak_take(page)
    s = await state(page)
    c.check('Redo last' in (s['message'] or '') and s['highlight'] == 'secondaryButton', 'step 2: Redo last (highlighted)', s)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check('Start over' in (s['message'] or '') and s['highlight'] == 'secondaryButton', 'step 2: Start over (highlighted)', s)
    await speak_take(page, started=True)
    s = await state(page)
    c.check('save' in (s['message'] or '').lower() and s['highlight'] == 'saveStatus', 'step 3: how saving works (save status highlighted)', s)
    await speak_take(page)
    s = await state(page)
    c.check(s['message'] is None and s['highlight'] is None, 'no more tips after the tutorial', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def speak_take(page, started=False):
    """One accepted take with the synthetic voice switched on only while recording
    (so the 'Not recording yet' hint never replaces the tips)."""
    shim = await page.evaluate("Boolean(window.__v2sAudio)")
    if not started:
        await page.keyboard.press('Space')
        await page.wait_for_timeout(300)
    if shim:
        await page.evaluate("window.__v2sAudio.set('continuous')")
    await page.wait_for_timeout(1300)
    if shim:
        await page.evaluate("window.__v2sAudio.set('silence')")
    await page.keyboard.press('Space')
    await wait_ready(page)


async def s_hold(pw, base):
    c = Checks('Held presses abort the take and restart the same sentence')
    browser, _, page, errors = await boot(pw, base)
    await hold_key(page, 'Space', 2200)
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and s['card'] == 'ready', 'held Space at Start: same sentence, not recording', s)
    c.check(s['message'] and "don't hold" in s['message'], 'explains "tap, don\'t hold"', s['message'])
    c.check([x['status'] for x in t] == ['aborted_hold'], 'take kept as aborted_hold, no fragments', t)

    box = await page.locator('#primaryButton').bounding_box()
    await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    await page.mouse.down()
    await page.wait_for_timeout(300)
    c.check((await state(page))['card'] == 'recording', 'mouse press starts on press, not on release')
    await page.wait_for_timeout(1700)
    await page.mouse.up()
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and s['card'] == 'ready' and [x['status'] for x in t] == ['aborted_hold'] * 2,
            'held mouse: same sentence, aborted_hold, nothing starts on release', (s, t))

    await page.keyboard.press('Space')
    await page.wait_for_timeout(1500)
    await hold_key(page, 'Space', 1800)  # hold the Stop press
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and t[-1]['status'] == 'aborted_hold', 'held Stop: take discarded, same sentence', (s, t[-1]))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_no_speech(pw, base):
    c = Checks('No speech: retry; second failure offers Keep')
    browser, _, page, errors = await boot(pw, base, audio='fan')
    await page.keyboard.press('Space')
    await page.wait_for_timeout(150)
    await page.keyboard.press('Space')  # tremor double tap: ignored (debounce)
    await page.wait_for_timeout(300)
    c.check((await state(page))['card'] == 'recording', 'double tap does not stop the take')
    await page.wait_for_timeout(1000)
    await page.keyboard.press('Space')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 0 and s['tone'] == 'warn' and "didn't hear" in (s['message'] or ''), 'first failure: same sentence + reason', s)
    await record(page, 1300, stop=False)
    await page.keyboard.press('Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    c.check(s['dialog'] and 'twice' in s['dialog'], 'second failure opens the keep/try-again choice', s['dialog'])
    c.check(s['focus'] == 'Try again', 'default button is Try again', s['focus'])
    await page.keyboard.press('Enter')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 0 and not s['dialog'], 'Enter = try again, same sentence', s)
    await record(page, 1300, stop=False)
    await page.keyboard.press('Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    await page.get_by_role('button', name='Keep it and continue').click()
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 1, 'Keep it and continue moves on', s)
    c.check([x['status'] for x in t] == ['qc_failed', 'qc_failed', 'qc_overridden'], 'statuses recorded', [x['status'] for x in t])
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_redo(pw, base):
    c = Checks('Start over and Redo last')
    browser, _, page, errors = await boot(pw, base)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(1000)
    await page.keyboard.press('ArrowLeft')
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and 'again' in (s['message'] or ''), 'Start over: same sentence', s)
    c.check([x['status'] for x in t] == ['restarted'], 'take kept as restarted', t)
    c.check(await page.locator('#secondaryButton').get_attribute('aria-disabled') == 'true', 'no Redo last before anything was accepted')

    await record(page)
    s = await state(page)
    c.check(s['index'] == 1, 'accepted, on warm-up 2', s)
    c.check(await page.locator('#secondaryButton').get_attribute('aria-disabled') == 'false', 'Redo last available')
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 0 and 'previous' in (s['message'] or ''), 'Redo last goes back one sentence', s)
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 1, 'after the redo it returns to where it was', s)
    c.check('_redo.' in t[-1]['fileName'], 'redo file has _redo', t[-1]['fileName'])
    c.check(t[-1]['supersedes'] == t[1]['fileName'], 'redo records which take it supersedes', (t[-1]['supersedes'], t[1]['fileName']))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_speech_before_start(pw, base):
    c = Checks('Speaking before Start shows "Not recording yet"')
    browser, _, page, errors = await boot(pw, base)
    await page.wait_for_timeout(3500)
    s = await state(page)
    c.check(s['message'] and 'Not recording yet' in s['message'], 'hint shown while idle', s['message'])
    await page.keyboard.press('Space')
    await page.wait_for_timeout(300)
    c.check('Not recording yet' not in ((await state(page))['message'] or ''), 'hint cleared when recording starts')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_tail(pw, base):
    c = Checks('After Stop: a fixed 0.7 s tail, also while still speaking')
    browser, _, page, errors = await boot(pw, base, audio='continuous', media='shim')
    await page.keyboard.press('Space')
    await page.wait_for_timeout(1500)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await page.wait_for_timeout(400)
    await page.keyboard.press('Space')
    await wait_ready(page)
    tail = (await page.evaluate(LAST_META_JS))['timing']['tailMs']
    c.check(700 <= tail <= 900, 'silent at Stop: tail is 0.7 s', tail)
    await page.evaluate("window.__v2sAudio.set('continuous')")
    await page.keyboard.press('Space')
    await page.wait_for_timeout(1500)
    await page.keyboard.press('Space')
    await wait_ready(page)
    tail = (await page.evaluate(LAST_META_JS))['timing']['tailMs']
    c.check(700 <= tail <= 900, 'still speaking at Stop: tail is still 0.7 s (no speech detection)', tail)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_device(pw, base):
    c = Checks('Camera stops mid-take → Reconnect → same sentence')
    browser, _, page, errors = await boot(pw, base)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(800)
    await page.evaluate("() => V2S.media.getStream().getVideoTracks()[0].stop()")
    await page.wait_for_selector('#screen-error:not([hidden])', timeout=10000)
    t = await takes(page)
    c.check(len(t) == 1 and t[0]['status'] == 'aborted_device', 'partial take kept as aborted_device', t)
    await page.click('#errorAction')
    await page.wait_for_selector('#screen-record:not([hidden])', timeout=10000)
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 0 and s['card'] == 'ready', 'back on the same sentence', s)
    await record(page)
    c.check((await state(page))['index'] == 1, 'recording works after reconnect')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_reload(pw, base):
    c = Checks('Reload during a take → same sentence')
    browser, _, page, errors = await boot(pw, base)
    await record(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(800)
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    title = await page.text_content('#welcomeTitle')
    c.check(title == 'Welcome back', 'returns to Welcome back', title)
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 1, 'still on warm-up 2 (nothing skipped)', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_break_zip(pw, base):
    c = Checks('Download-only browsers: block break, ZIP, cleared only after "Yes"')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE,
                                            init_scripts=['delete window.showDirectoryPicker; delete window.showSaveFilePicker;'])
    await setup_participant(page, base)
    await start_session(page)
    await set_index(page, 4)
    await record(page)
    await page.wait_for_selector('#screen-break:not([hidden])')
    c.check(await page.text_content('#breakTitle') == 'Warm-up done', 'warm-up done screen')
    await page.click('#breakPrimary')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['progressMain'] == 'Sentence 1 of 50' and s['progressSub'] == 'Break in 50', 'first formal sentence, break in 50', s)

    await set_index(page, 5 + 49)
    s = await state(page)
    c.check(s['progressSub'] == 'Break after this one', 'last sentence before the break is announced', s['progressSub'])
    await record(page)
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakTitle') == 'Block 1 done', 'block 1 done')
    c.check('Save your recordings' in await page.text_content('#breakSaveText'), 'asks to save before continuing')
    cached_before = len(await takes(page))

    async with page.expect_download() as info:
        await page.click('#breakPrimary')
    download = await info.value
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    c.check(s['dialog'] == 'Did the file save?' and s['focus'] == 'Not sure', 'asks for confirmation, default Not sure', s)
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(500)
    c.check(cached_before == 2 and len(await takes(page)) == cached_before, 'Not sure keeps every cached take', cached_before)
    c.check('Not saved yet' in await page.text_content('#breakSaveText'), 'says it is not saved yet')

    path = os.path.join(tempfile.mkdtemp(), download.suggested_filename)
    await download.save_as(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('manifest.json'))
    usable = [n for n in names if n.endswith(('.mp4', '.webm'))]
    c.check(download.suggested_filename.startswith('P017_video-recordings-') and '_block01' in download.suggested_filename,
            'ZIP name has participant and block', download.suggested_filename)
    c.check(len(usable) == cached_before and all(n.startswith('P017/') and n.count('/') == 1 for n in usable),
            'accepted takes in P017/', usable)
    c.check(manifest['recordCount'] == cached_before and manifest['events'], 'manifest with records and event log')

    async with page.expect_download():
        await page.click('#breakPrimary')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    await page.get_by_role('button', name='Yes, it saved').click()
    await page.wait_for_timeout(600)
    c.check(len(await takes(page)) == 0, 'Yes clears the cache')
    c.check('Saved' in await page.text_content('#breakSaveText'), 'shows Saved')
    await page.click('#breakPrimary')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 55 and s['progressMain'] == 'Sentence 1 of 50', 'continues with block 2', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_zip_picker(pw, base):
    c = Checks('ZIP mode in Chrome: save dialog opens on the click, file written where chosen')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True)
    downloads = track_downloads(page)
    await setup_participant(page, base, save='zip')
    await start_session(page)
    await set_index(page, 5 + 49)
    await record(page)
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    await page.click('#breakPrimary')
    await wait_for(page, "() => document.getElementById('breakSaveText').textContent.includes('Saved')", timeout=20000)
    log = await page.evaluate('window.__fsaLog')
    picker = [e for e in log if e['event'] == 'showSaveFilePicker']
    c.check(picker and all(e['active'] for e in picker), 'save dialog opened during the click', log)
    files = await page.evaluate(LIST_OPFS_JS, 'saved-zips')
    c.check(len(files) == 1 and files[0].startswith('P017_video-recordings-'), 'ZIP written to the chosen location', files)
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(len(await takes(page)) == 0, 'verified save clears the cache without asking')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_folder(pw, base):
    c = Checks('Folder mode: every take goes to the chosen folder, nothing is downloaded')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True)
    downloads = track_downloads(page)
    await setup_participant(page, base, save='folder')
    log = await page.evaluate('window.__fsaLog')
    c.check(any(e['event'] == 'showDirectoryPicker' and e['active'] for e in log), 'folder picker opened during the click', log)
    await start_session(page)
    s = await state(page)
    c.check('picked/P017' in s['saveStatus'], 'save status names the folder', s['saveStatus'])
    await record(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(900)
    await page.keyboard.press('ArrowLeft')  # Start over → not_used
    await wait_ready(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    usable = [f for f in files if f.startswith('P017/') and f.count('/') == 1 and f.endswith(('.mp4', '.webm'))]
    unused = [f for f in files if f.startswith('P017/not_used/') and f.endswith(('.mp4', '.webm'))]
    c.check(len(usable) == 1 and len(unused) == 1, 'accepted take in P017/, discarded one in P017/not_used/', files)
    c.check(all(f.rsplit('.', 1)[0] + '.json' in files for f in usable + unused), 'each video has its JSON sidecar')
    c.check(len(await takes(page)) == 0, 'cache emptied after verified writes')
    await page.click('#finishButton')
    await page.wait_for_selector('#screen-done:not([hidden])')
    await wait_for(page, "() => document.getElementById('doneSaveText').textContent.includes('saved in')")
    c.check('picked/P017' in await page.text_content('#doneSaveText'), 'done screen confirms the folder')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check(any(f.startswith('P017/session-') for f in files), 'session log written next to the recordings')
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_folder_new_session(pw, base):
    c = Checks('Folder mode, next session: permission asked on Start, still the same folder')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True)
    downloads = track_downloads(page)
    await setup_participant(page, base, save='folder')
    await page.evaluate("sessionStorage.setItem('__fsa_mode', 'prompt')")  # a new browser session
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await page.evaluate('window.__fsaLog.length = 0')
    await start_session(page)
    log = await page.evaluate('window.__fsaLog')
    requests = [e for e in log if e['event'] == 'requestPermission']
    c.check(requests and all(e['active'] for e in requests), 'permission requested during the Start click', log)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check(any(f.startswith('P017/') and f.endswith(('.mp4', '.webm')) for f in files), 'take written to the same folder', files)
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_folder_denied(pw, base):
    c = Checks('Folder permission refused: recording waits, person chooses; never a download')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True)
    downloads = track_downloads(page)
    await setup_participant(page, base, save='folder')
    await page.evaluate("sessionStorage.setItem('__fsa_mode', 'deny')")
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await page.click('#welcomeStart')
    await page.wait_for_selector('#screen-folder:not([hidden])', timeout=10000)
    c.check(True, 'asks about the folder instead of recording elsewhere')
    await page.click('#folderAllow')
    await page.wait_for_timeout(300)
    c.check(await page.is_visible('#folderError'), 'explains that permission was not given')
    await page.evaluate("sessionStorage.setItem('__fsa_mode', 'granted'); sessionStorage.setItem('__fsa_pick', 'second')")
    await page.click('#folderChoose')
    await page.wait_for_selector('#screen-check:not([hidden])', timeout=10000)
    await wait_for(page, "() => document.getElementById('checkOk').getAttribute('aria-disabled') === 'false'")
    await page.click('#checkOk')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'second')
    c.check(any(f.startswith('P017/') and f.endswith(('.mp4', '.webm')) for f in files), 'take written to the newly chosen folder', files)
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


SEED_LEGACY_TAKE = """() => new Promise((resolve, reject) => {
  const request = indexedDB.open('VideoRecorderDB', 2);
  request.onupgradeneeded = () => {
    const db = request.result;
    if (!db.objectStoreNames.contains('videos')) db.createObjectStore('videos', { keyPath: 'id', autoIncrement: true });
    if (!db.objectStoreNames.contains('progress')) db.createObjectStore('progress', { keyPath: 'sentenceSet' });
  };
  request.onsuccess = () => {
    const tx = request.result.transaction(['videos'], 'readwrite');
    const bytes = new Uint8Array(2048).fill(7);
    tx.objectStore('videos').add({ fileName: 'When did you know_1-290_repeat1_20260313_151311.mp4', arrayBuffer: bytes.buffer,
      mimeType: 'video/mp4', sentence: 'When did you know?', sentenceSet: '350_nonrepeating_sentences', sentenceIndex: 5,
      timestamp: '2026-03-13T19:13:11.000Z', size: 2048, metadata: { appVersion: '90' } });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  };
  request.onerror = () => reject(request.error);
})"""


async def s_folder_legacy(pw, base):
    c = Checks('Recordings left by the earlier page go to previous-page-recordings/, never labelled with the new ID')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True)
    downloads = track_downloads(page)
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.evaluate(SEED_LEGACY_TAKE)
    await page.fill('#setupId', 'SEMG0')
    await page.click('#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.click('#setupConfirmYes')
    await page.wait_for_selector('#setupStepFolder:not([hidden])')
    await page.click('#setupFolderChoose')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await wait_for(page, "async () => (await V2S.storage.countTakes()) === 0", timeout=10000)
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check('previous-page-recordings/When did you know_1-290_repeat1_20260313_151311.mp4' in files,
            'old recording written to previous-page-recordings/', files)
    c.check(not any(f.startswith('SEMG0/') for f in files), 'nothing labelled with the new participant', files)
    await page.evaluate("() => V2S.app.showWelcome()")
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.is_hidden('#welcomeNotice'), 'welcome shows nothing left to save')
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_real_picker(pw, base):
    c = Checks('Real Chrome folder picker opens from the click (CDP intercept)')
    browser, context, page, errors = await launch(pw, audio='speech')
    cdp = await context.new_cdp_session(page)
    opened = []
    cdp.on('Page.fileChooserOpened', lambda event: opened.append(event))
    await cdp.send('Page.enable')
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await cdp.send('Page.setInterceptFileChooserDialog', {'enabled': True})
    await page.fill('#setupId', 'P018')
    await page.click('#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.click('#setupConfirmYes')
    await page.wait_for_selector('#setupStepFolder:not([hidden])')
    await page.click('#setupFolderChoose')
    await page.wait_for_timeout(800)
    c.check(len(opened) == 1, "Chrome's real folder picker was opened by the click", opened)
    c.check(await page.is_visible('#setupStepFolder') and await page.is_hidden('#setupFolderError'),
            'a cancelled picker leaves the person on the same step, no error')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


SEED_PROGRESS = """() => new Promise((resolve, reject) => {
  const request = indexedDB.open('VideoRecorderDB', 2);
  request.onsuccess = () => {
    const tx = request.result.transaction(['progress'], 'readwrite');
    tx.objectStore('progress').put({ sentenceSet: '50words_350sentences', currentIndex: 120, repetitionCount: 0, completed: false });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  };
  request.onerror = () => reject(request.error);
})"""


async def s_legacy_progress(pw, base):
    c = Checks('Progress from the legacy page carries over')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE)
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.evaluate(SEED_PROGRESS)
    await page.fill('#setupId', 'P020')
    await page.click('#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    legacy_text = await page.text_content('#setupLegacy')
    c.check('Continue from sentence 116 of 350' in legacy_text, 'offers to continue from the earlier progress', legacy_text)
    await page.click('#setupConfirmYes')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await page.click('#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.text_content('#welcomeBlock') == 'Block 3 of 7', 'welcome shows block 3')
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 120 and s['progressMain'] == 'Sentence 16 of 50', 'resumes at the same sentence', s)
    c.check(s['message'] is not None, 'first session in the new page still gets the tips', s['message'])
    await record(page)
    await page.evaluate('V2S.session.flush()')
    mirror = await page.evaluate("async () => (await V2S.storage.getProgress('50words_350sentences')).currentIndex")
    c.check(mirror == 121, 'legacy key mirrors the new progress (fallback page stays in sync)', mirror)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


FULL_STORAGE = """
(() => {
  const estimate = async () => ({ usage: 95, quota: 100 });
  if (window.StorageManager) Object.defineProperty(StorageManager.prototype, 'estimate', { value: estimate, configurable: true, writable: true });
  if (navigator.storage) Object.defineProperty(navigator.storage, 'estimate', { value: estimate, configurable: true, writable: true });
})();
"""


async def s_storage_full(pw, base):
    c = Checks('Nearly full device: save first, then recording continues (no loop)')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE,
                                            init_scripts=[FULL_STORAGE, 'delete window.showDirectoryPicker; delete window.showSaveFilePicker;'])
    await setup_participant(page, base)
    await start_session(page)
    await record(page)
    c.check((await state(page))['index'] == 1, 'first take is accepted (nothing cached before it)')
    await page.wait_for_timeout(800)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])', timeout=8000)
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check('Save' in await page.text_content('#breakTitle'), 'goes to the save screen instead of recording')
    async with page.expect_download():
        await page.click('#breakPrimary')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    await page.get_by_role('button', name='Yes, it saved').click()
    await page.wait_for_timeout(600)
    await page.click('#breakPrimary')  # Continue
    await wait_ready(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['screen'] == 'record' and s['card'] == 'recording', 'recording works again', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_finish_and_admin(pw, base):
    c = Checks('Finish for today, Record more, researcher panel')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE,
                                            init_scripts=['delete window.showDirectoryPicker; delete window.showSaveFilePicker;'])
    await setup_participant(page, base)
    c.check(await page.is_hidden('#adminButton'), 'no researcher button for participants')
    await start_session(page)
    await record(page)
    await page.click('#finishButton')
    await page.wait_for_selector('#screen-done:not([hidden])')
    await wait_for(page, "() => !document.getElementById('doneSave').hidden")
    c.check(await page.text_content('#doneTitle') == 'Great work today', 'done screen')
    c.check('1 recording is not saved' in await page.text_content('#doneSaveText'), 'reminds about unsaved recordings')
    await page.click('#doneAgain')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.is_visible('#welcomeNotice'), 'welcome repeats the reminder')

    await page.goto(f'{base}/{NEXT_PAGE}?admin=1')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    c.check(await page.is_visible('#adminButton'), '?admin=1 shows the researcher button')
    await page.click('#adminButton')
    await page.wait_for_selector('#adminPanel:not([hidden])')
    text = await page.text_content('#adminBody')
    c.check('P017' in text and 'Cached takes' in text, 'panel shows participant and cached takes')
    await page.select_option('#adminTheme', 'dark')
    await page.wait_for_timeout(200)
    c.check(await page.get_attribute('html', 'data-theme') == 'dark', 'theme switches to dark')
    await page.click('#adminClose')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    c.check(await page.get_attribute('html', 'data-theme') == 'dark', 'theme is remembered after reload')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_keyboard_only(pw, base):
    c = Checks('The whole flow works with the keyboard alone')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE,
                                            init_scripts=['delete window.showDirectoryPicker; delete window.showSaveFilePicker;'])
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'setupId'")
    await page.keyboard.type('p030')
    await page.keyboard.press('Enter')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.wait_for_timeout(200)
    await page.keyboard.press('Enter')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=8000)
    await page.wait_for_timeout(200)
    await page.keyboard.press('Enter')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, "() => document.getElementById('checkOk').getAttribute('aria-disabled') === 'false'")
    await page.wait_for_timeout(300)
    await page.keyboard.press('Enter')
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(300)
    await record(page)
    s = await state(page)
    c.check(s['index'] == 1, 'setup → welcome → check → one take, keyboard only', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_timeout(pw, base):
    c = Checks('A take longer than 60 s restarts the same sentence')
    browser, _, page, errors = await boot(pw, base)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(61500)
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and '1 minute' in (s['message'] or ''), 'same sentence, explains the timeout', s)
    c.check([x['status'] for x in t] == ['aborted_timeout'], 'take kept as aborted_timeout', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_no_audio(pw, base):
    c = Checks('No audio analysis at all: device message, same sentence')
    browser, _, page, errors = await boot(pw, base)
    await page.evaluate('() => V2S.meter.detach()')
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and 'microphone did not respond' in (s['message'] or ''), 'blames the microphone, not the speaker', s['message'])
    c.check([x['status'] for x in t] == ['qc_failed'], 'take kept as qc_failed', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


SCENARIOS = {
    'normal': s_normal,
    'tutorial': s_tutorial,
    'hold': s_hold,
    'no_speech': s_no_speech,
    'redo': s_redo,
    'speech_before_start': s_speech_before_start,
    'tail': s_tail,
    'device': s_device,
    'reload': s_reload,
    'break_zip': s_break_zip,
    'zip_picker': s_zip_picker,
    'folder': s_folder,
    'folder_new_session': s_folder_new_session,
    'folder_denied': s_folder_denied,
    'folder_legacy': s_folder_legacy,
    'real_picker': s_real_picker,
    'legacy': s_legacy_progress,
    'storage_full': s_storage_full,
    'finish_admin': s_finish_and_admin,
    'keyboard': s_keyboard_only,
    'no_audio': s_no_audio,
    'timeout': s_timeout,
}

# Scenarios that make sense in every engine (no Chrome-only file dialogs or flags).
CROSS_ENGINE = ['normal', 'tutorial', 'hold', 'no_speech', 'redo', 'speech_before_start', 'tail', 'device',
                'reload', 'break_zip', 'legacy', 'storage_full', 'finish_admin', 'keyboard', 'no_audio']


async def main(names):
    results = []
    with static_server() as base:
        async with async_playwright() as pw:
            for name in names:
                try:
                    results.append(await SCENARIOS[name](pw, base))
                except Exception as error:  # report and keep going
                    print(f'  [FAIL] scenario {name} crashed: {error!r}')
                    results.append(False)
    ok = all(results)
    print(f'\n[{ENGINE}] ' + ('ALL PASSED' if ok else 'SOME CHECKS FAILED'))
    return ok


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['chrome', 'webkit', 'firefox'], default='chrome')
    parser.add_argument('scenarios', nargs='*')
    args = parser.parse_args()
    ENGINE = args.engine
    default = list(SCENARIOS) if ENGINE == 'chrome' else CROSS_ENGINE
    sys.exit(0 if asyncio.run(main(args.scenarios or default)) else 1)
