"""Scenario tests for the v113 hotfix of the legacy recorder (app.html).

Run:  <venv>/bin/python tools/e2e/test_legacy_hotfix.py
"""
import asyncio
import sys
import time

from playwright.async_api import async_playwright

from common import Checks, launch, static_server

STATE_JS = """() => ({
  rec: recording, idx, modal: modalOpen,
  title: modalOpen ? el('modalTitle').textContent : null,
  text: modalOpen ? el('modalMessage').innerText : null,
  framed: el('currentText').classList.contains('is-recording'),
  focus: document.activeElement && document.activeElement.id
})"""

RECORDS_JS = """() => new Promise(resolve => {
  const out = [];
  const tx = db.transaction(['videos'], 'readonly');
  tx.objectStore('videos').openCursor().onsuccess = e => {
    const c = e.target.result;
    if (!c) return resolve(out);
    const m = c.value.metadata || {};
    out.push({ index: c.value.sentenceIndex, issue: m.qcIssue, override: m.qcOverride,
               retry: m.requiresRetry, speechMs: m.audioQuality && m.audioQuality.speechMs });
    c.continue();
  };
})"""


async def boot(page, base):
    await page.goto(f'{base}/app.html?v=113')
    await page.wait_for_selector('#init')
    await page.check('#startupBypassMode')
    await page.click('#init')
    await page.wait_for_selector('#initCameraOverlay', state='hidden', timeout=20000)
    await page.wait_for_function('() => sentenceSetLoadRequest === sentenceSetLoadedRequest && idx === 5')
    await page.wait_for_timeout(600)


async def settle(page):
    """Wait until the take is saved: either idle again or a dialog is showing."""
    await page.wait_for_function(
        '() => modalOpen || (!recording && !recordingStopPending && !recordingSavePending)', timeout=15000)
    await page.wait_for_timeout(300)


async def record_once(page, ms=1600):
    await page.keyboard.press('Space')
    await page.wait_for_timeout(ms)
    await page.keyboard.press('Space')
    await settle(page)


async def scenario_hold(pw, base):
    c = Checks('Holding Space no longer machine-guns through sentences')
    browser, _, page, errors = await launch(pw, audio='speech')
    await boot(page, base)
    await page.keyboard.down('Space')
    await page.wait_for_timeout(500)
    end = time.time() + 5.5
    while time.time() < end:
        await page.keyboard.down('Space')  # OS-style auto-repeat (event.repeat = true)
        await page.wait_for_timeout(33)
    s = await page.evaluate(STATE_JS)
    c.check(s['rec'] is True, 'still recording during the hold (repeats ignored)', s)
    c.check(s['framed'] is True, 'red frame shown while recording')
    await page.keyboard.up('Space')
    await page.wait_for_timeout(300)
    c.check((await page.evaluate(STATE_JS))['rec'] is True, 'releasing the key does not stop')
    c.check(len(await page.evaluate(RECORDS_JS)) == 0, 'no fragments saved during the hold')
    await page.keyboard.press('Space')
    await settle(page)
    s = await page.evaluate(STATE_JS)
    recs = await page.evaluate(RECORDS_JS)
    c.check(len(recs) == 1 and recs[0]['issue'] is None, 'one take saved and it passed QC', recs)
    c.check(s['idx'] == 6 and not s['framed'], 'moved to the next sentence, frame gone', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def scenario_no_speech(pw, base):
    c = Checks('A take without speech is retried; 2nd failure offers Keep')
    browser, _, page, errors = await launch(pw, audio='fan')
    await boot(page, base)
    await record_once(page)
    s = await page.evaluate(STATE_JS)
    c.check(s['modal'] and s['title'] == 'Recording Check' and "didn't hear" in (s['text'] or ''),
            'first failure explains "We didn\'t hear you"', s)
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(400)
    s = await page.evaluate(STATE_JS)
    c.check(not s['modal'], 'Enter closes the notice')
    c.check(s['idx'] == 5, 'still on the same sentence')

    await record_once(page)
    s = await page.evaluate(STATE_JS)
    c.check(bool(s['modal']) and 'keep this recording' in (s['text'] or '').lower(),
            'second failure offers keep / record again', s)
    c.check(s['focus'] == 'modalCancel', 'default focus is "Record again"', s['focus'])
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(500)
    s = await page.evaluate(STATE_JS)
    c.check(not s['modal'] and s['idx'] == 5, 'Enter = record again, same sentence', s)

    await record_once(page)
    s = await page.evaluate(STATE_JS)
    c.check(s['modal'], 'third failure asks again')
    await page.click('#modalOk')
    await page.wait_for_function('() => !recordingSavePending && !modalOpen', timeout=10000)
    await page.wait_for_timeout(400)
    s = await page.evaluate(STATE_JS)
    recs = await page.evaluate(RECORDS_JS)
    c.check(s['idx'] == 6, 'Keep it and continue moves on', s)
    c.check([r['issue'] for r in recs] == ['no_speech'] * 3, 'all three takes kept and labelled no_speech', recs)
    c.check([r['override'] for r in recs] == [False, False, True], 'only the kept take has qcOverride', recs)
    c.check([r['retry'] for r in recs] == [True, True, False], 'requiresRetry marks the rejected takes', recs)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def scenario_save_unverified(pw, base):
    c = Checks('Unverified ZIP download is never cleared without "Yes"')
    browser, _, page, errors = await launch(
        pw, audio='speech', init_scripts=['delete window.showSaveFilePicker;'])
    downloads = []
    page.on('download', lambda d: downloads.append(d.suggested_filename))
    await boot(page, base)
    await record_once(page)
    c.check(len(await page.evaluate(RECORDS_JS)) == 1, 'one take cached')

    async def save_all():
        await page.click('#downloadAll')
        await page.wait_for_selector('#appModal.is-open')
        await page.click('#modalOk')  # "This will download all N cached videos" → Continue
        await page.wait_for_function("() => modalOpen && el('modalTitle').textContent === 'Did the file save?'",
                                     timeout=15000)
        await page.wait_for_timeout(200)

    await save_all()
    s = await page.evaluate(STATE_JS)
    c.check(s['focus'] == 'modalCancel', 'default focus is "No, keep them"', s['focus'])
    await page.keyboard.press('Enter')
    await page.wait_for_function('() => !saveAllInProgress', timeout=15000)
    c.check(len(await page.evaluate(RECORDS_JS)) == 1, 'answering No keeps the cached take')

    await save_all()
    await page.click('#modalOk')
    await page.wait_for_function('() => !saveAllInProgress', timeout=15000)
    c.check(len(await page.evaluate(RECORDS_JS)) == 0, 'answering Yes clears the cache')
    c.check(len(downloads) == 2, 'two ZIP downloads happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def main():
    results = []
    with static_server() as base:
        async with async_playwright() as pw:
            for scenario in (scenario_hold, scenario_no_speech, scenario_save_unverified):
                results.append(await scenario(pw, base))
    ok = all(results)
    print('\nALL PASSED' if ok else '\nSOME CHECKS FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    asyncio.run(main())
