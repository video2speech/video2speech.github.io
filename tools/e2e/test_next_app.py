"""Scenario tests for the new recorder (app_next.html, or app.html after the switch).

Run:  <venv>/bin/python tools/e2e/test_next_app.py [scenario-name ...]
"""
import asyncio
import json
import os
import sys
import tempfile
import time
import zipfile

from playwright.async_api import async_playwright

from common import NEXT_PAGE, Checks, launch, static_server

STATE_JS = """() => {
  const ctx = V2S.session.getContext();
  const visible = [...document.querySelectorAll('.screen')].find(s => !s.hidden);
  const fb = document.getElementById('feedback');
  const coach = document.getElementById('coach');
  return {
    screen: visible ? visible.id.replace('screen-', '') : null,
    state: V2S.session.getState(),
    index: ctx ? ctx.progress.currentIndex : null,
    card: document.getElementById('sentenceCard').dataset.state,
    feedback: fb.hidden ? null : document.getElementById('feedbackText').textContent,
    coach: coach.hidden ? null : coach.textContent,
    dialog: V2S.ui.isDialogOpen() ? document.getElementById('dialogTitle').textContent : null,
    focus: document.activeElement && document.activeElement.tagName === 'BUTTON' ? document.activeElement.textContent.trim() : (document.activeElement ? document.activeElement.id || document.activeElement.tagName : null),
    progressMain: document.getElementById('progressMain').textContent,
    progressSub: document.getElementById('progressSub').textContent
  };
}"""

TAKES_JS = """async () => {
  const out = [];
  await V2S.storage.forEachTake(r => out.push({ index: r.sentenceIndex, status: r.status, fileName: r.fileName,
     speechMs: r.metadata && r.metadata.qc && r.metadata.qc.speechMs, supersedes: r.metadata && r.metadata.supersedes,
     participantId: r.participantId, size: r.size }));
  return out;
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


async def setup_participant(page, base, participant='P017', save='zip', before_submit=None):
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.fill('#setupId', participant)
    if before_submit:
        await before_submit(page)
    await page.click('#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.click('#setupConfirmYes')
    folder_step = page.locator('#setupStepFolder:not([hidden])')
    try:
        await folder_step.wait_for(timeout=1500)
        await page.click('#setupFolderChoose' if save == 'folder' else '#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)


async def start_session(page):
    await page.click('#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, "() => document.getElementById('checkOk').getAttribute('aria-disabled') === 'false'")
    await page.click('#checkOk')
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)


async def boot(pw, base, audio='speech', **kwargs):
    browser, context, page, errors = await launch(pw, audio=audio, **kwargs)
    await setup_participant(page, base)
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


# ---------------------------------------------------------------- scenarios

async def s_normal(pw, base):
    c = Checks('Normal take: Start, read, Stop → next sentence')
    browser, _, page, errors = await boot(pw, base)
    s = await state(page)
    c.check(s['card'] == 'ready' and s['index'] == 0, 'starts on warm-up 1, not recording', s)
    c.check(s['coach'] and 'Press Start' in s['coach'], 'first-time tip shown', s['coach'])
    await page.keyboard.press('Space')
    await page.wait_for_timeout(300)
    s = await state(page)
    c.check(s['card'] == 'recording', 'Space starts recording immediately', s['card'])
    c.check(s['coach'] and 'Press Stop' in s['coach'], 'tip explains Stop while recording', s['coach'])
    await page.wait_for_timeout(1300)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(200)
    c.check((await state(page))['card'] == 'finishing', 'Stop shows Saving… during the tail')
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 1 and s['card'] == 'ready', 'moved to warm-up 2', s)
    c.check(len(t) == 1 and t[0]['status'] == 'accepted', 'one accepted take', t)
    c.check(t and '_warmup1-5_repeat1_' in t[0]['fileName'], 'legacy-compatible file name', t and t[0]['fileName'])
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_hold(pw, base):
    c = Checks('Held presses abort the take and restart the same sentence')
    browser, _, page, errors = await boot(pw, base)
    await hold_key(page, 'Space', 2200)
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and s['card'] == 'ready', 'held Space at Start: same sentence, not recording', s)
    c.check(s['feedback'] and "don't hold" in s['feedback'], 'explains "tap, don\'t hold"', s['feedback'])
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
    c.check(s['index'] == 0 and [x['status'] for x in t] == ['aborted_hold'] * 2, 'held mouse: same sentence, aborted_hold', (s, t))

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
    c.check(s['index'] == 0 and s['feedback'] and "didn't hear" in s['feedback'], 'first failure: same sentence + reason', s)
    await record(page, 1300, stop=False)
    await page.keyboard.press('Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    c.check(s['dialog'] and "twice" in s['dialog'], 'second failure opens the keep/try-again choice', s['dialog'])
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


async def s_start_over_and_redo(pw, base):
    c = Checks('Start over and Redo last')
    browser, _, page, errors = await boot(pw, base)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(1000)
    await page.keyboard.press('ArrowLeft')
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 0 and 'again' in (s['feedback'] or ''), 'Start over: same sentence', s)
    c.check([x['status'] for x in t] == ['restarted'], 'take kept as restarted', t)
    c.check(not await page.is_visible('#secondaryButton') or await page.locator('#secondaryButton').get_attribute('aria-disabled') == 'true',
            'no Redo last before anything was accepted')

    await record(page)
    s = await state(page)
    c.check(s['index'] == 1, 'accepted, on warm-up 2', s)
    c.check(await page.locator('#secondaryButton').get_attribute('aria-disabled') == 'false', 'Redo last available')
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 0 and 'previous' in (s['feedback'] or ''), 'Redo last goes back one sentence', s)
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 1, 'after the redo it returns to where it was', s)
    c.check(t[-1]['fileName'].endswith('_redo.webm') or t[-1]['fileName'].endswith('_redo.mp4'), 'redo file has _redo', t[-1]['fileName'])
    c.check(t[-1]['supersedes'] == t[1]['fileName'], 'redo records which take it supersedes', (t[-1]['supersedes'], t[1]['fileName']))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_speech_before_start(pw, base):
    c = Checks('Speaking before Start shows "Not recording yet"')
    browser, _, page, errors = await boot(pw, base)
    await page.wait_for_timeout(3500)
    s = await state(page)
    c.check(s['feedback'] and 'Not recording yet' in s['feedback'], 'hint shown while idle', s['feedback'])
    c.check(not s['coach'], 'only one message at a time', s['coach'])
    await page.keyboard.press('Space')
    await page.wait_for_timeout(300)
    c.check((await state(page))['feedback'] is None, 'hint cleared when recording starts')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_device_failure(pw, base):
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


async def s_block_break_zip(pw, base):
    c = Checks('Warm-up done screen, block break and ZIP save with confirmation')
    browser, _, page, errors = await boot(pw, base)
    await set_index(page, 4)
    await record(page)
    await page.wait_for_selector('#screen-break:not([hidden])')
    c.check(await page.text_content('#breakTitle') == 'Warm-up done', 'warm-up done screen')
    await page.click('#breakPrimary')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['progressMain'] == 'Sentence 1 of 50', 'first formal sentence', s['progressMain'])
    c.check('Block 1 of 7' in s['progressSub'] and '50 more' in s['progressSub'], 'shows block and sentences until the break', s['progressSub'])

    await set_index(page, 5 + 49)
    s = await state(page)
    c.check('Last sentence before your break' in s['progressSub'], 'last sentence before the break is announced', s['progressSub'])
    await record(page)
    await page.wait_for_selector('#screen-break:not([hidden])')
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
    usable = [n for n in names if not n.startswith('not_used/') and n.endswith(('.mp4', '.webm'))]
    c.check(download.suggested_filename.startswith('P017_video-recordings-') and '_block01' in download.suggested_filename,
            'ZIP name has participant and block', download.suggested_filename)
    c.check(len(usable) == cached_before and all(n.count('/') == 0 for n in usable), 'accepted takes at the top level', usable)
    c.check(manifest['recordCount'] == cached_before and manifest['events'], 'manifest with records and event log', manifest['recordCount'])

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
    c.check(s['index'] == 55 and 'Block 2 of 7' in s['progressSub'], 'continues with block 2', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


FOLDER_MOCK = """
window.showDirectoryPicker = async () => {
  const root = await navigator.storage.getDirectory();
  return root.getDirectoryHandle('picked', { create: true });
};
"""

LIST_OPFS_JS = """async () => {
  const out = [];
  async function walk(dir, prefix) {
    for await (const [name, handle] of dir.entries()) {
      if (handle.kind === 'directory') await walk(handle, prefix + name + '/');
      else out.push(prefix + name);
    }
  }
  const root = await navigator.storage.getDirectory();
  await walk(await root.getDirectoryHandle('picked', { create: true }), '');
  return out.sort();
}"""


async def s_folder_mode(pw, base):
    c = Checks('Folder mode writes every take and clears the cache')
    browser, _, page, errors = await launch(pw, audio='speech', init_scripts=[FOLDER_MOCK])
    await setup_participant(page, base, save='folder')
    await start_session(page)
    await record(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(900)
    await page.keyboard.press('ArrowLeft')  # Start over → not_used
    await wait_ready(page)
    await page.wait_for_timeout(800)
    files = await page.evaluate(LIST_OPFS_JS)
    usable = [f for f in files if f.startswith('P017/') and f.count('/') == 1 and f.endswith(('.mp4', '.webm'))]
    unused = [f for f in files if f.startswith('P017/not_used/') and f.endswith(('.mp4', '.webm'))]
    c.check(len(usable) == 1 and len(unused) == 1, 'accepted take in P017/, discarded one in P017/not_used/', files)
    c.check(all(f.replace('.webm', '.json').replace('.mp4', '.json') in files for f in usable + unused), 'each video has its JSON sidecar', files)
    c.check(len(await takes(page)) == 0, 'cache emptied after successful writes')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_legacy_progress(pw, base):
    c = Checks('Progress from the legacy page carries over')

    async def seed(page):
        await page.evaluate("""() => new Promise((resolve, reject) => {
          const request = indexedDB.open('VideoRecorderDB', 2);
          request.onsuccess = () => {
            const tx = request.result.transaction(['progress'], 'readwrite');
            tx.objectStore('progress').put({ sentenceSet: '50words_350sentences', currentIndex: 120, repetitionCount: 0, completed: false });
            tx.oncomplete = () => resolve();
            tx.onerror = () => reject(tx.error);
          };
          request.onerror = () => reject(request.error);
        })""")

    browser, _, page, errors = await launch(pw, audio='speech')
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await seed(page)
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
    c.check(await page.text_content('#welcomeBlock') == 'Block 3 of 7', 'welcome shows block 3', await page.text_content('#welcomeBlock'))
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 120 and s['progressMain'] == 'Sentence 16 of 50', 'resumes at the same sentence', s)
    c.check(s['coach'] is not None, 'first session in the new page still gets the two tips', s['coach'])
    await record(page)
    mirror = await page.evaluate("async () => (await V2S.storage.getProgress('50words_350sentences')).currentIndex")
    c.check(mirror == 121, 'legacy key mirrors the new progress (fallback page stays in sync)', mirror)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_keyboard_only(pw, base):
    c = Checks('The whole flow works with the keyboard alone')
    browser, _, page, errors = await launch(pw, audio='speech')
    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'setupId'")
    await page.keyboard.type('p030')
    await page.keyboard.press('Enter')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.wait_for_timeout(200)
    await page.keyboard.press('Enter')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await page.keyboard.press('Tab')
        await page.keyboard.press('Tab')
        await page.keyboard.press('Enter')
    except Exception:
        pass
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
    c.check(s['index'] == 0 and '1 minute' in (s['feedback'] or ''), 'same sentence, explains the timeout', s)
    c.check([x['status'] for x in t] == ['aborted_timeout'], 'take kept as aborted_timeout', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


FULL_STORAGE = """
if (navigator.storage) navigator.storage.estimate = async () => ({ usage: 95, quota: 100 });
"""


async def s_storage_full(pw, base):
    c = Checks('Nearly full device: save first, then recording continues (no loop)')
    browser, _, page, errors = await launch(pw, audio='speech', init_scripts=[FULL_STORAGE])
    await setup_participant(page, base)
    await start_session(page)
    await record(page)
    c.check((await state(page))['index'] == 1, 'first take is accepted (nothing cached before it)')
    await page.wait_for_timeout(500)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])', timeout=8000)
    c.check('Save' in await page.text_content('#breakTitle'), 'goes to the save screen instead of recording',
            await page.text_content('#breakTitle'))
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
    c.check(s['screen'] == 'record' and s['card'] == 'recording', 'recording works again (device still "full", nothing cached)', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_finish_and_admin(pw, base):
    c = Checks('Finish for today, Record more, researcher panel')
    browser, _, page, errors = await launch(pw, audio='speech')
    await setup_participant(page, base)
    c.check(await page.is_hidden('#adminButton'), 'no researcher button for participants')
    await start_session(page)
    await record(page)
    await page.click('#finishButton')
    await page.wait_for_selector('#screen-done:not([hidden])')
    c.check(await page.text_content('#doneTitle') == 'Great work today', 'done screen')
    c.check('1 recording is not saved' in await page.text_content('#doneUnsavedText'), 'reminds about unsaved recordings',
            await page.text_content('#doneUnsavedText'))
    await page.click('#doneAgain')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.is_visible('#welcomeUnsaved'), 'welcome repeats the reminder')

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


SCENARIOS = {
    'storage_full': s_storage_full,
    'finish_admin': s_finish_and_admin,
    'normal': s_normal,
    'hold': s_hold,
    'no_speech': s_no_speech,
    'redo': s_start_over_and_redo,
    'speech_before_start': s_speech_before_start,
    'device': s_device_failure,
    'reload': s_reload,
    'break_zip': s_block_break_zip,
    'folder': s_folder_mode,
    'legacy': s_legacy_progress,
    'keyboard': s_keyboard_only,
    'timeout': s_timeout,
}


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
    print('\nALL PASSED' if ok else '\nSOME CHECKS FAILED')
    return ok


if __name__ == '__main__':
    chosen = sys.argv[1:] or list(SCENARIOS)
    sys.exit(0 if asyncio.run(main(chosen)) else 1)
