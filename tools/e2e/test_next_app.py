"""Scenario tests for the recorder (app_next.html, or app.html after the switch).

Run:
  <venv>/bin/python tools/e2e/test_next_app.py                    # every scenario, Chrome
  <venv>/bin/python tools/e2e/test_next_app.py --engine webkit     # Safari's engine
  <venv>/bin/python tools/e2e/test_next_app.py --engine firefox
  <venv>/bin/python tools/e2e/test_next_app.py normal folder ...   # chosen scenarios

Every browser is muted (common.launch). The 5-second microphone test is shortened to
1.2 s through window.__V2S_TEST so each session start stays quick.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import tempfile
import time
import zipfile

from playwright.async_api import async_playwright

from common import NEXT_PAGE, REPO, Checks, launch, next_url, static_server

ENGINE = 'chrome'
FAST = 'window.__V2S_TEST = { testRecordMs: 1200 };'
NO_PICKERS = 'delete window.showDirectoryPicker; delete window.showSaveFilePicker;'

STATE_JS = """() => {
  const ctx = V2S.session.getContext();
  const visible = [...document.querySelectorAll('.screen')].find(s => !s.hidden);
  const rec = document.getElementById('screen-record');
  const msg = document.getElementById('message');
  const coach = document.getElementById('coach');
  const ackEl = document.getElementById('coachAck');
  const line = document.querySelector('#sentenceText .sentence-line');
  const redo = document.getElementById('redoButton');
  const main = document.getElementById('mainButton');
  const active = document.activeElement;
  return {
    screen: visible ? visible.id.replace('screen-', '') : null,
    state: V2S.session.getState(),
    index: ctx ? ctx.progress.currentIndex : null,
    card: rec.dataset.state,
    rec: document.body.dataset.rec || 'off',
    saved: rec.classList.contains('is-saved'),
    status: document.getElementById('cardStatusText').textContent,
    timer: document.getElementById('cardTimer').textContent,
    message: msg.classList.contains('is-empty') ? null : document.getElementById('messageText').textContent,
    tone: (msg.className.match(/tone-(\\w+)/) || [])[1] || null,
    coach: coach.hidden ? null : document.getElementById('coachAction').textContent,
    ack: coach.hidden || ackEl.classList.contains('is-empty') ? null : document.getElementById('coachAckText').textContent,
    detail: coach.hidden ? null : document.getElementById('coachDetail').textContent || null,
    mainQuiet: main.classList.contains('is-quiet'),
    mainBg: getComputedStyle(main).backgroundColor,
    pillBg: getComputedStyle(document.getElementById('cardStatus')).backgroundColor,
    bandBg: line ? getComputedStyle(line).backgroundColor : null,
    pulse: main.classList.contains('is-pulsing') ? 'main' : (redo.classList.contains('is-pulsing') ? 'redo' : null),
    redo: redo.classList.contains('is-invisible') ? null : document.getElementById('redoCaption').textContent,
    redoLabel: redo.classList.contains('is-invisible') ? null : document.getElementById('redoLabel').textContent,
    redoSaved: !msg.classList.contains('is-empty') && msg.classList.contains('tone-ok'),
    main: document.getElementById('mainLabel').textContent,
    sentence: document.getElementById('sentenceText').textContent,
    sentenceColor: getComputedStyle(document.getElementById('sentenceText')).color,
    cardBg: getComputedStyle(document.getElementById('card')).backgroundColor,
    dialog: V2S.ui.isDialogOpen() ? document.getElementById('dialogTitle').textContent : null,
    focus: active && active.tagName === 'BUTTON' ? active.textContent.trim() : (active ? active.id || active.tagName : null),
    where: document.getElementById('whereMain').textContent,
    whereBar: document.getElementById('whereBar').style.transform,
    fit: rec.dataset.fit || null
  };
}"""

TAKES_JS = """async () => {
  await V2S.session.flush();
  const exported = new Set(await V2S.storage.exportedIds());
  const out = [];
  await V2S.storage.forEachTake(r => out.push({ index: r.sentenceIndex, status: r.status, fileName: r.fileName,
     speechMs: r.metadata && r.metadata.qc && r.metadata.qc.speechMs, supersedes: r.metadata && r.metadata.supersedes,
     supersededBy: r.metadata && r.metadata.supersededBy, participantId: r.participantId, size: r.size,
     round: r.metadata && r.metadata.round, exported: exported.has(r.id) }));
  return out;
}"""

UNSAVED_JS = "async () => { await V2S.session.flush(); return V2S.storage.countUnsaved(); }"

LAST_META_JS = """async () => { await V2S.session.flush(); let m = null; await V2S.storage.forEachTake(r => { if (r.status === 'accepted') m = r.metadata; }); return m; }"""

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

READ_OPFS_JSON = """async ([dirName, path]) => {
  let dir = await (await navigator.storage.getDirectory()).getDirectoryHandle(dirName);
  const parts = path.split('/');
  for (const part of parts.slice(0, -1)) dir = await dir.getDirectoryHandle(part);
  return JSON.parse(await (await (await dir.getFileHandle(parts[parts.length - 1])).getFile()).text());
}"""

WAVE_PIXELS_JS = """() => {
  const c = document.getElementById('recordWave');
  if (!c.width || !c.height) return 0;
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0;
  for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
  return n;
}"""

# MediaRecorder that fails to start while window.__failStarts > 0 — like Chrome's
# "EncodingError: Encoder initialization failed" with a 16 kHz Bluetooth microphone.
FLAKY_RECORDER = """
(() => {
  const Original = window.MediaRecorder;
  if (!Original) return;
  window.__failStarts = 0;
  class Flaky extends Original {
    start(...args) {
      const result = super.start(...args);
      if (window.__failStarts > 0) {
        window.__failStarts -= 1;
        setTimeout(() => {
          const event = new Event('error');
          event.error = new DOMException('Encoder initialization failed.', 'EncodingError');
          this.dispatchEvent(event);
          try { Original.prototype.stop.call(this); } catch (e) { /* already stopped */ }
        }, 30);
      }
      return result;
    }
  }
  Flaky.isTypeSupported = type => Original.isTypeSupported(type);
  window.MediaRecorder = Flaky;
})();
"""

# Bluetooth headphones as the microphone, with a built-in microphone also available.
BLUETOOTH_MIC = """
(() => {
  Object.defineProperty(MediaStreamTrack.prototype, 'label', {
    configurable: true,
    get() { return this.kind === 'audio' ? 'AirPods (Bluetooth)' : 'FaceTime HD Camera'; }
  });
  const list = async () => [
    { kind: 'videoinput', deviceId: 'cam-1', label: 'FaceTime HD Camera', groupId: 'g1' },
    { kind: 'audioinput', deviceId: 'mic-airpods', label: 'AirPods (Bluetooth)', groupId: 'g2' },
    { kind: 'audioinput', deviceId: 'mic-builtin', label: 'MacBook Pro Microphone', groupId: 'g3' }
  ];
  if (window.MediaDevices) Object.defineProperty(MediaDevices.prototype, 'enumerateDevices', { value: list, configurable: true, writable: true });
  if (navigator.mediaDevices) Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', { value: list, configurable: true, writable: true });
})();
"""


async def state(page):
    return await page.evaluate(STATE_JS)


async def takes(page):
    return await page.evaluate(TAKES_JS)


async def wait_for(page, js, timeout=15000):
    await page.wait_for_function(js, timeout=timeout)


READY_FOR_PRESS = """() => !(window.V2S && V2S.ui && V2S.ui.clicksPaused && V2S.ui.clicksPaused())
  && !(window.V2S && V2S.input && V2S.input.pressReady && !V2S.input.pressReady())"""


async def ready_for_press(page):
    """Like a person: not in the moment after a screen (or a step) appears, nor within a
    second of the last press (the page takes those as a double press)."""
    await wait_for(page, READY_FOR_PRESS)


DIALOG_READY = ("() => V2S.ui.isDialogOpen() && document.getElementById('dialog').dataset.armed === 'true'"
                " && !V2S.input.clicksPaused()")


async def dialog_ready(page):
    """Like a person: answer a dialog once it takes answers (it ignores presses in its
    first moment, and "Did the file save?" for a second: it is answered after looking)."""
    await wait_for(page, DIALOG_READY)


async def click(page, selector, **kwargs):
    await ready_for_press(page)
    await page.click(selector, **kwargs)


async def press(page, key):
    await ready_for_press(page)
    await page.keyboard.press(key)


async def wait_ready(page, timeout=15000):
    """Until the take is settled: back to ready, a dialog is asking, or another screen took over."""
    await wait_for(page, "() => V2S.ui.isDialogOpen() || ['ready', 'idle', 'partEnd'].includes(V2S.session.getState())", timeout)
    # A person needs a moment before the next press; it also keeps the next press
    # outside the 300 ms debounce window.
    await page.wait_for_timeout(450)


def track_downloads(page):
    downloads = []
    page.on('download', lambda d: downloads.append(d.suggested_filename))
    return downloads


async def setup_participant(page, base, participant='P017', save='zip', before_submit=None):
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.fill('#setupId', participant)
    if before_submit:
        await before_submit(page)
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await click(page, '#setupFolderChoose' if save == 'folder' else '#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)


async def set_progress(page, **fields):
    """Change this participant's progress while on the welcome screen (before Begin)."""
    await page.evaluate("""async fields => {
      const app = V2S.app.state();
      Object.assign(app.progress, fields);
      await V2S.storage.saveParticipantProgress(app.progress);
    }""", fields)


async def pass_check(page):
    """The camera and microphone check: Next (camera placed), record the test, watch it
    back, answer Yes."""
    await page.wait_for_selector('#screen-check:not([hidden])', timeout=15000)
    await wait_for(page, "() => V2S.media.getStream() && !document.getElementById('checkStepCamera').hidden")
    await click(page, '#checkNext')
    await wait_for(page, "() => !document.getElementById('testRecord').hidden && !document.getElementById('checkStepMic').hidden")
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden || !document.getElementById('testError').hidden", timeout=20000)
    if await page.is_visible('#testError'):
        raise AssertionError('microphone test failed: ' + (await page.text_content('#testError')))
    await click(page, '#testYes')
    # The first time: the one thing to remember, before the practice.
    await wait_for(page, "() => !document.getElementById('screen-intro').hidden || !document.getElementById('screen-record').hidden")
    if await page.is_visible('#screen-intro'):
        await click(page, '#introStart')


async def start_session(page):
    """Welcome → check (camera, then the test recording) → recording screen, waiting."""
    if await page.is_visible('#welcomeLater'):   # unsaved recordings: go on without saving (it asks first)
        await click(page, '#welcomeLater')
        await dialog_ready(page)
        await page.locator('#dialogActions button', has_text='Continue without saving').click()
    else:
        await click(page, '#welcomeStart')
    await pass_check(page)
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(500)  # presses in the first 0.4 s are ignored (double press)


async def boot(pw, base, audio='speech', save='zip', trained=True, index=None, init_scripts=(), **kwargs):
    """Set up P017 and open the recording screen. trained=True skips How to record and the
    practice coaching (most scenarios are about real sentences); index jumps there."""
    kwargs.setdefault('engine', ENGINE)
    browser, context, page, errors = await launch(pw, audio=audio, init_scripts=[FAST, *init_scripts], **kwargs)
    await setup_participant(page, base, save=save)
    fields = {}
    if trained:
        fields.update(howtoSeen=True, coachDone=True)
    if index is not None:
        fields.update(currentIndex=index, completed=False)
    if fields:
        await set_progress(page, **fields)
    await start_session(page)
    return browser, context, page, errors


async def record(page, ms=1600, stop=True):
    await ready_for_press(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(ms)
    if stop:
        await page.keyboard.press('Space')
        await wait_ready(page)


async def take_quietly(page, ms=1400):
    """One take with the synthetic voice (media='shim'), silent again after Stop."""
    await page.evaluate("window.__v2sAudio.set('speech')")
    await ready_for_press(page)
    await page.keyboard.press('Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'")
    await page.wait_for_timeout(ms)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await page.keyboard.press('Space')
    await wait_ready(page)


async def hold_key(page, key='Space', ms=2000):
    await ready_for_press(page)
    await page.keyboard.down(key)
    end = time.time() + ms / 1000
    await page.wait_for_timeout(500)
    while time.time() < end:
        await page.keyboard.down(key)  # auto-repeat
        await page.wait_for_timeout(33)
    await page.keyboard.up(key)


async def end_for_today(page):
    """The top-bar End for today, confirmed in its dialog."""
    await click(page, '#finishButton')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='End for today').click()
    await page.wait_for_selector('#screen-done:not([hidden])')


async def confirm_dialog(page, name):
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text=name).click()
    await page.wait_for_timeout(300)


async def open_settings(page, section=None):
    """Settings, optionally on one of its pages (the row's name, e.g. 'Saving')."""
    await click(page, '#settingsButton')
    await page.wait_for_selector('#settingsPanel:not([hidden])')
    await page.wait_for_timeout(200)
    if section:
        await page.locator('#settingsBody button.row', has_text=section).first.click()
        await wait_for(page, f"() => document.getElementById('settingsTitle').textContent === {section!r}")
        await page.wait_for_timeout(150)


async def dismiss_dialog(page):
    await dialog_ready(page)
    await page.locator('#dialogActions button').first.click()
    await page.wait_for_timeout(300)


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


async def css_color(page, name):
    return await page.evaluate("n => { const s = document.createElement('span'); s.style.color = getComputedStyle(document.documentElement).getPropertyValue(n); document.body.appendChild(s); const c = getComputedStyle(s).color; s.remove(); return c; }", name)


async def css_background(page, name):
    return await page.evaluate("n => { const s = document.createElement('span'); s.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue(n); document.body.appendChild(s); const c = getComputedStyle(s).backgroundColor; s.remove(); return c; }", name)


# ---------------------------------------------------------------- scenarios

async def s_first_run(pw, base):
    c = Checks('First run: welcome, microphone test, How to record, coached practice with the Redo lesson')
    # The synthetic voice falls silent after each Stop, like a person who has finished
    # (continuous sound would rightly show "Not recording yet").
    browser, _, page, errors = await launch(pw, audio='speech', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    c.check(await page.text_content('#welcomeTitle') == 'Welcome' and await page.is_visible('#welcomeStages'),
            'first visit: Welcome, with the three stages')
    c.check(await page.text_content('#welcomeStart') == 'Begin', 'button says Begin')
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, '() => V2S.media.getStream() !== null')
    await page.wait_for_timeout(300)
    camera_text = await page.text_content('#checkCameraText')
    c.check(camera_text == 'Put your face inside the oval.', 'one short instruction: the face inside the oval', camera_text)
    c.check(await page.text_content('#checkCameraStep') == 'Step 1 of 2' and await page.is_visible('#checkNext') and await page.is_hidden('#testRecord'),
            'check, one step at a time: first only the camera (Next), the test is not shown yet')
    await click(page, '#checkNext')
    await page.wait_for_selector('#checkStepMic:not([hidden])')
    c.check(await page.text_content('#checkMicStep') == 'Step 2 of 2' and await page.is_visible('#testRecord') and await page.is_hidden('#testAsk'),
            'step 2: one button to record the test')
    await click(page, '#testRecord')
    await page.wait_for_timeout(300)
    c.check(await page.is_visible('#testLive') and 'Hello' in await page.text_content('#testSay'), 'while recording: tells what to say')
    await wait_for(page, "() => !document.getElementById('checkPlayback').hidden", timeout=10000)
    c.check(True, 'plays the test back, picture and sound')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden", timeout=10000)
    question = await page.text_content('#testQuestion')
    c.check(question == 'Can you see your face and hear yourself clearly?', 'asks whether the face is visible and the sound is clear', question)
    # iPhone/iPad with the microphone on turn a video's own sound down (or to the earpiece):
    # the test plays through the audio context, from the speaker, like the cue sounds.
    routed = await page.evaluate("document.getElementById('checkPlayback').dataset.speaker === '1'")
    c.check(routed, 'the test recording plays through the audio context (loud from the speaker on iPhone)', routed)
    await page.evaluate("window.__v2sAudio.set('silence')")  # sitting quietly, reading the screen
    await click(page, '#testYes')
    # Before the practice: the one thing to remember (no page of rules).
    await page.wait_for_selector('#screen-intro:not([hidden])')
    intro = {k: await page.text_content(f'#intro{k}') for k in ('Title', 'Rule', 'Lead', 'Start')}
    c.check(intro['Title'] == 'One thing to remember' and intro['Rule'].replace('\xa0', ' ') == 'Press Space, read the green sentence out loud, then press Space again.'
            and '5 short sentences' in intro['Lead'] and 'only for practice' in intro['Lead'] and intro['Start'] == 'Begin practice',
            'before the practice: the one thing to remember, and that it is only practice', intro)
    await click(page, '#introStart')
    # How to record is taught inside the practice, one step at a time.
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['where'] == 'Practice 1 of 5' and s['status'] == '', 'Practice 1 of 5, no status text while waiting', s)
    c.check(s['coach'] == 'Press Space once.' and s['detail'] == 'No need to hold it.' and s['ack'] is None and s['pulse'] == 'main',
            'coach: press Start (Space on a computer) once, no need to hold it; that button pulses', s)
    c.check(s['redo'] is None, 'no Redo before anything is recorded', s['redo'])

    await page.evaluate("window.__v2sAudio.set('speech')")
    await page.keyboard.press('Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'")
    await page.wait_for_timeout(1300)
    s = await state(page)
    c.check('Read the green sentence' in (s['coach'] or '') and s['message'] is None, 'coach: read the green sentence, then Stop; nothing else appears', s)
    c.check(s['status'] == 'Recording' and s['timer'] == '', 'pill: "Recording" (no clock on short takes)', s)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await page.keyboard.press('Space')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 1 and (s['ack'] or '').startswith('That’s it.') and 'Next sentence' in (s['coach'] or '') and s['status'] == '',
            'practice 2: first what happened (Recorded), then the one next step; "Saved" next to the sentence just recorded', s)
    c.check(s['redo'] and 'I need the water' in s['redo'], 'Redo names the sentence it would record again', s['redo'])

    await take_quietly(page)
    s = await state(page)
    c.check(s['index'] == 2 and s['ack'] == 'This is only practice — nothing went wrong.' and s['coach'] == 'Now try Redo: press ←.'
            and s['detail'] == 'If you ever misread a sentence, Redo lets you read it again.'
            and s['pulse'] == 'redo' and s['mainQuiet'], 'practice 3: the Redo lesson alone (Redo pulses, Start is plain)', s)
    await page.evaluate("window.__v2sAudio.set('speech')")   # reading the new sentence aloud
    await page.wait_for_timeout(2600)
    s = await state(page)
    await page.evaluate("window.__v2sAudio.set('silence')")
    c.check(s['ack'] == 'This is only practice — nothing went wrong.' and not s['message'],
            'reading aloud during the lesson: still the lesson (no "Not recording yet")', s)
    c.check(await page.get_attribute('#mainButton', 'aria-disabled') == 'false', 'Start still works (a single-switch user can go on)')
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 1 and s['ack'] == 'This is the sentence before.' and 'read it again' in (s['coach'] or '') and s['redoLabel'] == 'Cancel redo',
            'Redo goes back to practice 2: says so, then the one next step; Cancel redo offered', s)
    await take_quietly(page)
    s = await state(page)
    c.check(s['index'] == 2 and s['ack'] == 'That’s how Redo works.' and 'go on' in (s['coach'] or ''),
            'back on practice 3: first what Redo did, then (separately) carry on', s)
    t = await takes(page)
    c.check([x['status'] for x in t if x['index'] == 1] == ['superseded', 'accepted'], 'the replaced recording is marked superseded', t)
    c.check(t[-1]['fileName'].rsplit('.', 1)[0].endswith('_redo'), 'the new one ends with _redo', t[-1]['fileName'])

    await take_quietly(page)
    s = await state(page)
    c.check(s['index'] == 3 and not s['ack'] and 'more to practice' in (s['coach'] or ''), 'practice 4: no "Recorded", just the next step', s)
    await take_quietly(page)
    await take_quietly(page)
    s = await state(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Continue' and s['status'] == '' and (s['ack'] or '').replace('\xa0', ' ') == 'That was the last practice sentence.'
            and 'continue' in (s['coach'] or '').lower() and s['redoLabel'] == 'Redo',
            'after practice 5 the sentence stays (Recorded, Redo possible): what it was, then Continue', s)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakTitle') == 'Practice done', 'Practice done screen')
    c.check('save your practice recordings' in await page.text_content('#breakLead') and await page.text_content('#breakPrimary') == 'Save recordings'
            and await page.is_hidden('#breakParts'),
            'saving is learnt by doing it once (ZIP mode): one instruction, Save recordings', await page.text_content('#breakLead'))
    async with page.expect_download() as info:
        await click(page, '#breakPrimary')
    c.check((await info.value).suggested_filename.startswith('P017_practice_'), 'a practice ZIP', (await info.value).suggested_filename)
    await confirm_dialog(page, 'Yes, I see it')
    await page.wait_for_timeout(300)
    c.check(await page.text_content('#breakPrimary') == 'Continue to part 1' and '7 parts of 50 sentences' in await page.text_content('#breakPartsLabel')
            and await page.is_hidden('#breakSave') and 'Press Space, read the green\xa0sentence' in await page.text_content('#breakRule'),
            'then the real sentences: the one thing to remember again, 7 parts of 50, Continue to part 1 (no "saved" line: Yes just said it)',
            await page.text_content('#breakRule'))
    await click(page, '#breakPrimary')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['coach'] is None and s['where'] == 'Part 1 of 7 · Sentence 1 of 50',
            'real sentences: no coach, "Part 1 of 7 · Sentence 1 of 50"', s)
    c.check(s['redo'] is None, 'Redo does not reach back into the practice', s['redo'])
    progress = await page.evaluate('V2S.app.state().progress')
    c.check(progress.get('coachDone') and progress.get('howtoSeen'), 'the practice is remembered')
    t = await takes(page)
    c.check(len(t) == 6 and all(x['exported'] for x in t), 'the practice recordings were saved (kept as backup copies)', len(t))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_normal(pw, base):
    c = Checks('A real sentence: Starting…, the sentence turns green (quiet red signs only), fixed tail, Saved next to it')
    browser, _, page, errors = await boot(pw, base, index=5)
    s = await state(page)
    c.check(s['card'] == 'ready' and s['status'] == '' and s['main'] == 'Start' and s['rec'] == 'off',
            'waiting: "Not recording", Start', s)
    c.check(s['sentenceColor'] == await css_color(page, '--sentence-wait'), 'sentence is grey while waiting', s['sentenceColor'])
    t_press = await page.evaluate('performance.now()')
    await page.keyboard.press('Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'", timeout=3000)
    green_ms = await page.evaluate('performance.now()') - t_press
    c.check(green_ms < 400, f'almost no wait: the sentence turns green {green_ms:.0f} ms after the press', green_ms)
    await page.wait_for_timeout(1200)
    s = await state(page)
    c.check(s['status'] == 'Recording' and s['timer'] == '' and s['message'] is None,
            'pill: "Recording"; no text appears near the sentence', s)
    c.check(s['sentenceColor'] == await css_color(page, '--read-text') and s['bandBg'] == await css_background(page, '--read-band'),
            'the sentence turns vivid green on a soft highlight', (s['sentenceColor'], s['bandBg']))
    c.check(s['cardBg'] == await css_background(page, '--surface') and s['pillBg'] == await css_background(page, '--rec-tint')
            and s['mainBg'] == await css_background(page, '--rec-tint'), 'only quiet signs around it: red Recording sign, soft red Stop; the card keeps its colour', s)
    c.check(s['main'] == 'Stop' and s['redo'] is None, 'only Stop is offered while recording', s)
    c.check(await page.evaluate(WAVE_PIXELS_JS) > 0, 'the waveform moves')
    t_stop = await page.evaluate('performance.now()')
    await page.keyboard.press('Space')
    await page.wait_for_timeout(300)  # after the 0.14 s colour change, within the 0.7 s tail
    s = await state(page)
    c.check(s['card'] == 'finishing' and s['status'] == '' and s['main'] == 'Finishing…' and s['sentenceColor'] == await css_color(page, '--sentence-wait'),
            'Stop: the sentence is no longer green; the button says Finishing…', s)
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    t_ready = await page.evaluate('performance.now()')
    meta = await page.evaluate(LAST_META_JS)
    tail = meta['timing']['tailMs']
    c.check(700 <= tail <= 900, 'kept recording 0.7 s after Stop', tail)
    c.check((t_ready - t_stop) - tail < 450, 'next sentence right after the tail (storage in the background)', round(t_ready - t_stop - tail))
    s = await state(page)
    c.check(s['index'] == 6 and s['status'] == '' and not s['message'], 'next sentence: just the sentence and Start (no "Recorded")', s)
    mk = meta['markers']
    c.check(mk['startPress'] <= mk['recorderStart'] <= mk['readNow'] <= mk['stopPress'] <= mk['recorderStop'], 'time markers in order', mk)
    lead = meta['timing']['startCueLeadMs']
    c.check(lead <= 150 and mk['recorderStart'] - mk['startPress'] <= 190, 'recording starts right after the short cue (no missed words)',
            {'cueLeadMs': lead, 'pressToRecorder': round(mk['recorderStart'] - mk['startPress'])})
    c.check(0 <= mk['readNow'] - mk['recorderStart'] <= 300, 'green as soon as the recorder runs', round(mk['readNow'] - mk['recorderStart']))
    c.check(meta['timing']['startAttempts'] == 1 and meta['participantId'] == 'P017' and meta['qc']['speechMs'] > 300,
            'sidecar: one start attempt, participant, check metrics', meta['timing'])
    c.check('_1-350_repeat1_' in meta['fileName'], 'legacy-compatible file name', meta['fileName'])
    legacy_keys = ['appVersion', 'materialCacheVersion', 'createdAt', 'startedAt', 'fileName', 'sidecarFileName', 'mimeType', 'fileExt', 'size',
                   'sentenceSet', 'sentenceIndex', 'phase', 'position', 'total', 'sentence', 'redo', 'quality', 'frameRate', 'audioMode',
                   'requestedVideoConstraints', 'requestedAudioConstraints', 'recorderConfig', 'stopDelayMs', 'audioQuality', 'mediaAtStart',
                   'mediaAtSave', 'browser', 'downloadClearPolicy', 'audioQualityWarning', 'qcIssue', 'qcFailuresInARow', 'qcOverride', 'requiresRetry']
    missing = [k for k in legacy_keys if k not in meta]
    c.check(not missing, "sidecar has every key the earlier page wrote", missing)
    c.check(meta['quality'].get('label') == '15 Mbps - Research Quality' and meta['frameRate'] == {'label': '30 fps - Standard', 'fps': 30}
            and meta['audioMode'] == {'mode': 'raw', 'label': 'Raw - Disable Browser Processing'} and meta['startedAt'] and meta['qcIssue'] is None,
            'legacy shapes: quality / frameRate / audioMode labels, startedAt, qcIssue', (meta['quality'], meta['frameRate'], meta['audioMode']))
    await page.wait_for_timeout(1600)
    await page.wait_for_timeout(1200)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_hold(pw, base):
    c = Checks('Holding the button (push-to-talk habit): a held Start is explained and restarts; a held Stop keeps the take')
    browser, _, page, errors = await boot(pw, base, media='shim', index=5)
    await hold_key(page, 'Space', 2200)
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    s = await state(page)
    c.check(s['dialog'] == 'Press once, then let go' and 'not kept' in await page.text_content('#dialogBody'),
            'held key: a dialog says the recording was not kept and to press once, then let go', s['dialog'])
    await page.wait_for_timeout(450)
    await page.keyboard.press('Enter')
    await wait_ready(page)
    s = await state(page)
    c.check(s['message'] == 'Press Space once, then read.', 'after OK: what to do next (the key, on a computer)', s['message'])
    t = await takes(page)
    c.check(s['index'] == 5 and s['card'] == 'ready' and not s['dialog'], 'Enter closes it; same sentence, not recording', s)
    c.check(all(x['status'] == 'aborted_hold' for x in t), 'whatever was recorded is kept as aborted_hold', t)

    box = await page.locator('#mainButton').bounding_box()
    await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    await page.mouse.down()
    await page.wait_for_timeout(250)
    c.check((await state(page))['card'] in ('starting', 'recording'), 'a mouse press acts on press, not on release')
    await page.wait_for_timeout(1700)
    await page.mouse.up()
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dismiss_dialog(page)
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['card'] == 'ready', 'held mouse: same sentence, nothing starts on release', s)

    await page.keyboard.press('Space')
    await page.wait_for_timeout(1500)
    await page.evaluate("window.__v2sAudio.set('silence')")  # done reading
    await hold_key(page, 'Space', 1800)  # hold the Stop press
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 6 and not s['dialog'] and t and t[-1]['status'] == 'accepted', 'held Stop: the recording is kept, next sentence', (s, t[-1:]))
    c.check('let go' in (s['message'] or '') and s['tone'] == 'info', 'a gentle tip: let go right after pressing', s['message'])
    await page.evaluate("window.__v2sAudio.set('speech')")
    await record(page)
    c.check((await state(page))['index'] == 7, 'a normal press afterwards works')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_no_speech(pw, base):
    c = Checks('No speech: retry with a reason; second failure offers Keep')
    # The microphone check passes with speech; then only fan noise is left.
    browser, _, page, errors = await boot(pw, base, audio='speech', media='shim', index=5)
    await page.evaluate("window.__v2sAudio.set('fan')")
    await page.keyboard.press('Space')
    await page.wait_for_timeout(150)
    await page.keyboard.press('Space')  # tremor double tap: ignored (debounce)
    await page.wait_for_timeout(500)
    c.check((await state(page))['card'] == 'recording', 'a double tap does not stop the take')
    await page.wait_for_timeout(900)
    await page.keyboard.press('Space')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['tone'] == 'warn' and "couldn’t hear" in (s['message'] or '') and 'press Space' in (s['message'] or ''), 'first failure: same sentence + reason (names the key)', s)
    await record(page, 1300, stop=False)
    await page.keyboard.press('Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    c.check(s['dialog'] and 'twice' in s['dialog'] and s['focus'] == 'Try again', 'second failure: Try again (default) or Keep', s)
    await page.keyboard.press('Enter')
    await wait_ready(page)
    c.check((await state(page))['index'] == 5, 'Enter = try again, same sentence')
    await record(page, 1300, stop=False)
    await page.keyboard.press('Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    await page.get_by_role('button', name='Keep it and go on').click()
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 6, 'Keep it and go on moves on', s)
    c.check([x['status'] for x in t] == ['qc_failed', 'qc_failed', 'qc_overridden'], 'statuses recorded', [x['status'] for x in t])
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_redo(pw, base):
    c = Checks('Redo: names the sentence, records it again, the replaced take is marked superseded')
    browser, _, page, errors = await boot(pw, base, index=5)
    c.check((await state(page))['redo'] is None, 'no Redo before the first recording of the part')
    await record(page)
    await record(page)
    s = await state(page)
    c.check(s['index'] == 7 and s['redo'] and 'What is that there' in s['redo'], 'Redo names the previous sentence', s['redo'])
    await click(page, '#redoButton')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 6 and 'read this sentence again' in (s['message'] or '') and s['redoLabel'] == 'Cancel redo',
            'Redo: back to that sentence, says so; Cancel redo instead of a second Redo', s)
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 7, 'afterwards it returns to where it was', s)
    replaced = [x for x in t if x['index'] == 6]
    c.check([x['status'] for x in replaced] == ['superseded', 'accepted'], 'old take superseded, new one accepted', replaced)
    c.check(replaced[-1]['supersedes'] == replaced[0]['fileName'] and replaced[0]['supersededBy'] == replaced[-1]['fileName'],
            'both sidecars point at each other', replaced)
    await click(page, '#redoButton')
    await page.wait_for_timeout(400)
    await click(page, '#redoButton')  # a double press: the Redo stays
    await page.wait_for_timeout(300)
    c.check((await state(page))['redoLabel'] == 'Cancel redo', 'a second press within 1 s does not cancel the Redo just made')
    await page.wait_for_timeout(800)
    await click(page, '#redoButton')  # Cancel redo, deliberately
    await page.wait_for_timeout(400)
    s = await state(page)
    # (the fake microphone talks all the time, so "Not recording yet" may show by now)
    c.check(s['index'] == 7 and s['redoLabel'] == 'Redo' and 'again' not in (s['message'] or ''), 'Cancel redo: back where they were, nothing recorded', s)
    c.check(len(await takes(page)) == len(t), 'cancelling records nothing')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_redo_folder(pw, base):
    c = Checks('Redo in folder mode: the replaced recording moves to not_used/ (no cleaning by hand)')
    browser, _, page, errors = await boot(pw, base, save='folder', fsa=True, index=5)
    await record(page)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(400)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    videos = [f for f in files if f.endswith(('.mp4', '.webm'))]
    usable = [f for f in videos if f.count('/') == 1]
    unused = [f for f in videos if '/not_used/' in f]
    c.check(len(usable) == 2 and any(f.rsplit('.', 1)[0].endswith('_redo') for f in usable), 'P017/: one file per sentence, the redo included', usable)
    c.check(len(unused) == 1 and 'What is that there' in unused[0], 'P017/not_used/: the replaced recording', unused)
    meta = await page.evaluate(READ_OPFS_JSON, ['picked', unused[0].rsplit('.', 1)[0] + '.json'])
    c.check(meta['status'] == 'superseded' and meta['supersededBy'].endswith(('_redo.mp4', '_redo.webm')), 'its sidecar says superseded, by which file', meta.get('status'))
    log = await page.evaluate(READ_OPFS_JSON, ['picked', 'P017/logs/superseded.json'])
    c.check(len(log['replaced']) == 1 and log['replaced'][0]['fileName'] == unused[0].split('/')[-1], 'P017/logs/superseded.json lists it', log)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_speech_before_start(pw, base):
    c = Checks('Speaking before Start: "Not recording yet"')
    browser, _, page, errors = await boot(pw, base, index=5)
    await page.wait_for_timeout(1200)
    c.check(not (await state(page))['message'], 'no hint in the first moments (people often say a word after Stop)')
    await page.wait_for_timeout(3300)
    s = await state(page)
    c.check(s['message'] == 'Not recording yet. Press Space first, then read.' and s['status'] == '', 'hint while not recording (names the key on a computer)', s)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(300)
    c.check('Not recording yet' not in ((await state(page))['message'] or ''), 'hint cleared when recording starts')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_tail(pw, base):
    c = Checks('After Stop: a fixed 0.7 s tail, also while still speaking')
    browser, _, page, errors = await boot(pw, base, audio='continuous', media='shim', index=5)
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


async def s_recorder_retry(pw, base):
    c = Checks('Recorder fails to start: silent retries; told only when every try fails')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[FLAKY_RECORDER])
    await page.evaluate('window.__failStarts = 1')
    await press(page, 'Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'", timeout=4000)
    s = await state(page)
    c.check(s['tone'] != 'warn' and s['status'] == 'Recording', 'one failure: retried silently (no warning), recording', s)
    await page.wait_for_timeout(1300)
    await press(page, 'Space')
    await wait_ready(page)
    meta = await page.evaluate(LAST_META_JS)
    c.check(meta['timing']['startAttempts'] == 2 and len(meta['timing']['startErrors']) == 1, 'sidecar records 2 start attempts', meta['timing'])
    c.check((await state(page))['index'] == 6, 'take accepted')

    await page.evaluate('window.__failStarts = 3')
    await press(page, 'Space')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 6 and "didn’t start" in (s['message'] or ''), 'every try failed: "The recording didn’t start", same sentence', s)
    await page.evaluate('window.__failStarts = 3')
    await press(page, 'Space')
    await page.wait_for_selector('#screen-error:not([hidden])', timeout=5000)
    c.check(await page.text_content('#errorTitle') == 'Recording cannot start' and 'Bluetooth' in await page.text_content('#errorBody'),
            'twice in a row: a screen suggests the built-in microphone')
    await page.evaluate('window.__failStarts = 0')
    await click(page, '#errorSecondary')
    await wait_ready(page)
    await record(page)
    c.check((await state(page))['index'] == 7, 'Try again: recording works')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_low_rate_mic(pw, base):
    c = Checks('16 kHz (Bluetooth-like) microphone: 64 kbps audio, no encoder failures')
    browser, _, page, errors = await boot(pw, base, media='shim', index=5,
                                          init_scripts=["sessionStorage.setItem('__audio_rate', '16000');"])
    rate = await page.evaluate('V2S.media.current().sampleRate')
    for _ in range(4):
        await record(page, 1300)
    t = await takes(page)
    meta = await page.evaluate(LAST_META_JS)
    events = await page.evaluate("async () => (await V2S.storage.getAllEvents()).filter(e => e.type === 'recorder_error').length")
    c.check(rate == 16000, 'the microphone runs at 16 kHz', rate)
    c.check(meta['recorderConfig']['options']['audioBitsPerSecond'] == 64000, 'audio bitrate 64 kbps', meta['recorderConfig'])
    c.check(len([x for x in t if x['status'] == 'accepted']) == 4 and events == 0, '4 takes accepted, no recorder errors', (t, events))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_bluetooth(pw, base):
    c = Checks('Bluetooth microphone: the check warns and offers the built-in one')
    browser, _, page, errors = await launch(pw, audio='speech', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS, BLUETOOTH_MIC])
    await setup_participant(page, base)
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, '() => V2S.media.getStream() !== null')
    await click(page, '#checkNext')  # the microphone is step 2
    await wait_for(page, "() => !document.getElementById('micWarning').hidden && !document.getElementById('micSwitch').hidden", timeout=8000)
    c.check('Bluetooth' in await page.text_content('#micWarningText'), 'warns about lower sound quality')
    c.check(await page.text_content('#micSwitch') == 'Use MacBook Pro Microphone', 'offers the built-in microphone by name')
    await click(page, '#micSwitch')
    await page.wait_for_timeout(800)
    stored = await page.evaluate("V2S.storage.getSetting('mediaSettings', null)")
    c.check(stored and stored.get('audioDeviceId') == 'mic-builtin', 'remembers the chosen microphone', stored)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_mic_test_silent(pw, base):
    c = Checks('Microphone test hears nothing: says so, offers to record again')
    browser, _, page, errors = await launch(pw, audio='silence', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, '() => V2S.media.getStream() !== null')
    await click(page, '#checkNext')
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testError').hidden", timeout=10000)
    c.check("couldn’t hear anything" in await page.text_content('#testError'), 'explains that nothing was heard')
    c.check(await page.is_visible('#testRecord') and await page.is_hidden('#testYes'), 'no way to continue; record again')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden", timeout=10000)
    c.check(True, 'with sound, the playback and question appear')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_double_tap(pw, base):
    c = Checks('Double tap: the second tap does not press the button that appears under it')
    browser, _, page, errors = await launch(pw, audio='speech', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, '() => V2S.media.getStream() !== null')
    await click(page, '#checkNext')
    # the second tap, 0.1 s later, on the button that has just appeared
    await page.wait_for_timeout(100)
    await page.click('#testRecord', force=True)
    await page.wait_for_timeout(300)
    c.check(await page.is_visible('#testRecord') and await page.is_hidden('#testLive'), 'the test did not start')
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testLive').hidden || !document.getElementById('testAsk').hidden", timeout=5000)
    c.check(True, 'a deliberate tap a moment later starts it')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


HELD_SNAP = """() => ({
  screen: document.body.dataset.screen,
  dialog: V2S.ui.isDialogOpen() ? document.getElementById('dialogTitle').textContent : null,
  breakTitle: document.getElementById('breakTitle').textContent,
  checkStep: document.getElementById('checkStepCamera').hidden ? (document.getElementById('checkStepMic').hidden ? '-' : 'mic') : 'camera',
  testRunning: !document.getElementById('testLive').hidden,
  state: V2S.session.getState()
})"""


async def s_held_keys(pw, base):
    c = Checks('A key or button held down does not run on through the next screens')
    # The last practice sentence: Space held on Continue → Practice done, and it stays.
    browser, _, page, errors = await boot(pw, base, trained=False, index=4, init_scripts=[NO_PICKERS])
    downloads = track_downloads(page)
    await record(page)
    await hold_key(page, 'Space', 1600)
    await page.wait_for_timeout(1500)
    s = await page.evaluate(HELD_SNAP)
    c.check(s['screen'] == 'break' and s['breakTitle'] == 'Practice done' and not s['dialog'] and not downloads,
            'practice: Space held on Continue shows Practice done, and nothing more', s)
    await browser.close()

    # The end of part 1 (ZIP): Space held on Finish part 1 → the break, no download.
    browser, _, page, errors2 = await boot(pw, base, index=54, init_scripts=[NO_PICKERS])
    downloads = track_downloads(page)
    await record(page)
    await hold_key(page, 'Space', 1600)
    await page.wait_for_timeout(1500)
    s = await page.evaluate(HELD_SNAP)
    c.check(s['screen'] == 'break' and s['breakTitle'] == 'Part 1 done' and not s['dialog'] and not downloads,
            'part end: Space held on Finish part 1 shows the break; nothing is saved by itself', s)
    async with page.expect_download(timeout=20000):
        await page.keyboard.press('Enter')
    await wait_for(page, '() => V2S.ui.isDialogOpen()', timeout=20000)
    c.check(len(downloads) == 1, 'a new press of Enter then saves (the button still works)', downloads)
    await browser.close()

    # The end of part 1, a long press with the mouse (or a finger) on Finish part 1.
    browser, _, page, errors3 = await boot(pw, base, index=54, init_scripts=[NO_PICKERS])
    downloads = track_downloads(page)
    await record(page)
    box = await page.locator('#mainButton').bounding_box()
    await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    await page.mouse.down()
    await page.wait_for_timeout(1600)
    await page.mouse.up()
    await page.wait_for_timeout(1500)
    s = await page.evaluate(HELD_SNAP)
    c.check(s['screen'] == 'break' and not s['dialog'] and not downloads, 'part end: a long press shows the break, and nothing more', s)
    await browser.close()

    # Welcome: Enter held on Begin → the camera step, and the test does not start.
    browser, _, page, errors4 = await launch(pw, audio='speech', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await page.wait_for_timeout(600)
    await page.focus('#welcomeStart')
    await hold_key(page, 'Enter', 2500)
    await page.wait_for_timeout(800)
    s = await page.evaluate(HELD_SNAP)
    c.check(s['screen'] == 'check' and s['checkStep'] == 'camera' and not s['testRunning'], 'welcome: Enter held on Begin stops at the camera step', s)
    await browser.close()

    # Welcome: Space held on Begin acts once, when it is let go.
    browser, _, page, errors5 = await launch(pw, audio='speech', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await page.wait_for_timeout(600)
    await page.focus('#welcomeStart')
    await hold_key(page, 'Space', 1600)
    await page.wait_for_timeout(800)
    s = await page.evaluate(HELD_SNAP)
    c.check(s['screen'] == 'check' and s['checkStep'] == 'camera', 'welcome: Space held on Begin acts once, on release', s)
    await browser.close()
    errors = errors + errors2 + errors3 + errors4 + errors5
    c.check(not errors, 'no page errors', errors)
    return c.done()


async def s_save_keys(pw, base):
    c = Checks('"Did the file save?" with keys alone: the first press highlights, a later one chooses')
    browser, _, page, errors = await boot(pw, base, index=54, init_scripts=[NO_PICKERS])
    downloads = track_downloads(page)
    await record(page)
    await press(page, 'Space')   # Finish part 1
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'breakPrimary'", timeout=15000)
    await press(page, 'Enter')   # Save recordings
    await wait_for(page, '() => V2S.ui.isDialogOpen()', timeout=20000)
    await page.wait_for_timeout(500)
    c.check(await page.evaluate("document.activeElement.classList.contains('dialog')"), 'nothing is pre-chosen')
    await page.keyboard.press('Space')
    await page.wait_for_timeout(100)
    focused = await page.evaluate('document.activeElement.textContent')
    await page.keyboard.press('Space')   # the second half of a double press
    await page.wait_for_timeout(300)
    c.check(focused == 'Yes, I see it' and await page.evaluate('V2S.ui.isDialogOpen()'),
            'the first press highlights "Yes, I see it"; a double press does not choose it', focused)
    await page.wait_for_timeout(800)
    await page.keyboard.press('PageDown')   # a clicker, a moment later
    await wait_for(page, '() => !V2S.ui.isDialogOpen()')
    await wait_for(page, "() => document.getElementById('breakPrimary').textContent === 'Continue to part 2'", timeout=10000)
    c.check(len(downloads) == 1, 'answered with a clicker: saved, one file', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


DENY_CAMERA = """
(() => {
  const deny = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
  if (window.MediaDevices) Object.defineProperty(MediaDevices.prototype, 'getUserMedia', { value: deny, configurable: true, writable: true });
  if (navigator.mediaDevices) Object.defineProperty(navigator.mediaDevices, 'getUserMedia', { value: deny, configurable: true, writable: true });
})();
"""


async def s_camera_denied(pw, base):
    c = Checks('Camera permission refused: says permission is needed (not "disconnected")')
    browser, _, page, errors = await launch(pw, audio='speech', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS, DENY_CAMERA])
    await setup_participant(page, base)
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-error:not([hidden])', timeout=15000)
    c.check(await page.text_content('#errorTitle') == 'Camera and microphone are needed', 'the permission screen', await page.text_content('#errorTitle'))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


CARD_RECT = """() => {
  const r = document.getElementById('card').getBoundingClientRect();
  const m = document.getElementById('mainButton').getBoundingClientRect();
  return [Math.round(r.top), Math.round(r.bottom), Math.round(m.top)];
}"""


async def s_card_stable(pw, base):
    c = Checks('Nothing moves within a part: a problem message or Redo never moves the card or Start')
    all_errors = []
    for name, viewport in (('phone', {'width': 390, 'height': 844}), ('laptop', {'width': 1440, 'height': 900})):
        browser, _, page, errors = await boot(pw, base, audio='speech', media='shim', index=5, viewport=viewport)
        await take_quietly(page)
        waiting = await page.evaluate(CARD_RECT)
        await page.evaluate("window.__v2sAudio.set('fan')")   # a take with no speech
        await press(page, 'Space')
        await wait_for(page, "() => V2S.session.getState() === 'recording'")
        await page.wait_for_timeout(1400)
        await press(page, 'Space')
        await wait_ready(page)
        problem = await page.evaluate(CARD_RECT)
        message = (await state(page))['message']
        await page.evaluate("window.__v2sAudio.set('silence')")
        await press(page, 'ArrowLeft')   # Redo: a two-line instruction appears
        await page.wait_for_timeout(500)
        redoing = await page.evaluate(CARD_RECT)
        c.check(waiting == problem == redoing and message, f'{name}: the card and Start stay put (waiting, a problem, after Redo)', (waiting, problem, redoing, message))
        all_errors += errors
        await browser.close()
    c.check(not all_errors, 'no page errors', all_errors)
    return c.done()


async def s_help(pw, base):
    c = Checks('"?" shows How to record (the steps in order) over the same sentence')
    browser, _, page, errors = await boot(pw, base, index=5)
    await record(page)
    await click(page, '#helpButton')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    s = await state(page)
    steps = await page.locator('#dialogBody .steps li').all_text_contents()
    c.check(s['dialog'] == 'How to record' and len(steps) == 3 and 'green' in steps[1] and 'Redo' in await page.text_content('#dialogBody'),
            'three numbered steps (Start, read when green, Stop), then how to Redo', steps)
    await page.keyboard.press('Space')
    s = await state(page)
    c.check(s['state'] == 'idle' and s['dialog'] == 'How to record', 'Space does not start a recording behind the help', s)
    await dismiss_dialog(page)
    await wait_ready(page)
    s = await state(page)
    c.check(s['screen'] == 'record' and s['index'] == 6, 'back on the same sentence', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_device(pw, base):
    c = Checks('Camera stops mid-take → Reconnect → same sentence')
    browser, _, page, errors = await boot(pw, base, index=5)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(900)
    await page.evaluate("() => V2S.media.getStream().getVideoTracks()[0].stop()")
    await page.wait_for_selector('#screen-error:not([hidden])', timeout=10000)
    c.check(await page.text_content('#errorTitle') == 'Camera or microphone disconnected', 'says what happened')
    t = await takes(page)
    c.check(len(t) == 1 and t[0]['status'] == 'aborted_device', 'partial take kept as aborted_device', t)
    await click(page, '#errorAction')
    await page.wait_for_selector('#screen-record:not([hidden])', timeout=10000)
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['card'] == 'ready', 'back on the same sentence', s)
    await record(page)
    c.check((await state(page))['index'] == 6, 'recording works after reconnect')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_reload(pw, base):
    c = Checks('Reload during a take → same sentence')
    browser, _, page, errors = await boot(pw, base, index=5)
    await record(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(900)
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    c.check(await page.text_content('#welcomeTitle') == 'Welcome back', 'returns to Welcome back')
    c.check(await page.text_content('#welcomePart') == 'Part 1 of 7' and await page.text_content('#welcomeCount') == 'Sentence 2 of 50',
            'welcome shows where they are (in the recording screen\'s words)')
    c.check(await page.text_content('#welcomeStart') == 'Save recordings' and await page.is_visible('#welcomeLater'),
            'unsaved recordings: Save recordings first, with a way on')
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 6, 'still on the second sentence (nothing skipped)', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_break_zip(pw, base):
    c = Checks('Download-only browsers: part break, ZIP, cleared only after "Yes"')
    browser, _, page, errors = await boot(pw, base, index=5 + 48, init_scripts=[NO_PICKERS])
    s = await state(page)
    c.check(s['where'] == 'Part 1 of 7 · Sentence 49 of 50', 'where you are: sentence 49 of 50', s['where'])
    await record(page)
    await record(page)
    s = await state(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Finish part 1' and s['status'] == '' and s['redoLabel'] == 'Redo',
            "part's last sentence: stays on screen (Recorded), Redo still possible, then Finish part 1", s)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakTitle') == 'Part 1 done', 'Part 1 done')
    c.check(await page.text_content('#breakLead') == 'Save your recordings, then take a rest.' and await page.text_content('#breakPrimary') == 'Save recordings'
            and await page.is_hidden('#breakSecondary') and await page.is_visible('#finishButton'),
            'one instruction: save, then rest; End for today in the top bar, not under the button')
    await click(page, '#finishButton')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    c.check(await page.text_content('#dialogTitle') == 'End for today?', 'End for today on a break asks first')
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Keep going').click()
    await page.wait_for_timeout(500)
    c.check(await page.is_visible('#screen-break') and await page.text_content('#breakPrimary') == 'Save recordings', 'Keep going: still on the break')
    cached_before = len(await takes(page))

    async with page.expect_download() as info:
        await click(page, '#breakPrimary')
    download = await info.value
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    focus = await page.evaluate("document.activeElement && document.activeElement.className")
    c.check(s['dialog'] == 'Did the file save?' and focus == 'dialog' and '“P017_part01”' in await page.text_content('#dialogBody'),
            'asks for confirmation: nothing pre-chosen (look first), and where to look for “P017_part01”', s)
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Not sure').click()
    await page.wait_for_timeout(500)
    c.check(cached_before == 2 and len(await takes(page)) == cached_before, 'Not sure keeps every cached take', cached_before)
    c.check('save them again to be sure' in await page.text_content('#breakSaveText'), 'asks to save again to be sure (it does not claim the file is missing)')

    path = os.path.join(tempfile.mkdtemp(), download.suggested_filename)
    await download.save_as(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('manifest.json'))
    usable = [n for n in names if n.endswith(('.mp4', '.webm'))]
    c.check(download.suggested_filename.startswith('P017_part01_') and download.suggested_filename.endswith('.zip'),
            'ZIP name has participant and part', download.suggested_filename)
    c.check(len(usable) == cached_before and all(n.startswith('P017/') and n.count('/') == 1 for n in usable), 'accepted takes in P017/', usable)
    c.check(manifest['recordCount'] == cached_before and manifest['events'], 'manifest with records and event log')

    async with page.expect_download():
        await click(page, '#breakPrimary')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dialog_ready(page)
    await page.get_by_role('button', name='Yes, I see it').click()
    await page.wait_for_timeout(600)
    t = await takes(page)
    c.check(await page.evaluate(UNSAVED_JS) == 0 and len(t) == 2 and all(x['exported'] for x in t),
            'Yes: nothing left to save; the recordings stay as backup copies', t)
    c.check(await page.text_content('#breakPrimary') == 'Continue to part 2', 'button: Continue to part 2')
    await click(page, '#breakPrimary')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 55 and s['where'] == 'Part 2 of 7 · Sentence 1 of 50' and s['redo'] is None,
            'part 2 starts; Redo does not reach back into part 1', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_zip_picker(pw, base):
    c = Checks('ZIP mode in Chrome: the save dialog opens on the click; file written where chosen')
    browser, _, page, errors = await boot(pw, base, fsa=True, index=5 + 49)
    downloads = track_downloads(page)
    await record(page)
    await page.keyboard.press('Space')  # Finish part 1
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    await click(page, '#breakPrimary')
    # Saved: the button moves on (no routine "saved" line)
    await wait_for(page, "() => document.getElementById('breakPrimary').textContent === 'Continue to part 2'", timeout=20000)
    log = await page.evaluate('window.__fsaLog')
    picker = [e for e in log if e['event'] == 'showSaveFilePicker']
    c.check(picker and all(e['active'] for e in picker), 'save dialog opened during the click', log)
    files = await page.evaluate(LIST_OPFS_JS, 'saved-zips')
    c.check(len(files) == 1 and files[0].startswith('P017_part01_'), 'ZIP written to the chosen location', files)
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(await page.evaluate(UNSAVED_JS) == 0, 'a verified save needs no question; nothing left to save')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_folder(pw, base):
    c = Checks('Folder mode: every take goes to the chosen folder; nothing is downloaded')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
    downloads = track_downloads(page)
    await setup_participant(page, base, save='folder')
    log = await page.evaluate('window.__fsaLog')
    c.check(any(e['event'] == 'showDirectoryPicker' and e['active'] for e in log), 'folder picker opened during the click', log)
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=5)
    await start_session(page)
    await record(page)
    await hold_key(page, 'Space', 1500)  # a held press → not_used
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dismiss_dialog(page)
    await wait_ready(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    usable = [f for f in files if f.startswith('P017/') and f.count('/') == 1 and f.endswith(('.mp4', '.webm'))]
    unused = [f for f in files if f.startswith('P017/not_used/') and f.endswith(('.mp4', '.webm'))]
    c.check(len(usable) == 1 and len(unused) == 1, 'accepted take in P017/, the held (discarded) one in P017/not_used/', files)
    c.check(all(f.rsplit('.', 1)[0] + '.json' in files for f in usable + unused), 'each video has its JSON sidecar')
    c.check(len(await takes(page)) == 0, 'cache emptied after verified writes')
    await end_for_today(page)
    await wait_for(page, "() => document.getElementById('doneSaveText').textContent.includes('saved in')")
    c.check('picked/P017' in await page.text_content('#doneSaveText'), 'done screen confirms the folder')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check(any(f.startswith('P017/logs/session-') for f in files), 'session log written to P017/logs/')
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_folder_new_session(pw, base):
    c = Checks('Folder mode, next session: permission asked on Begin, still the same folder')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
    downloads = track_downloads(page)
    await setup_participant(page, base, save='folder')
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=5)
    await page.evaluate("sessionStorage.setItem('__fsa_mode', 'prompt')")  # a new browser session
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await page.evaluate('window.__fsaLog.length = 0')
    await start_session(page)
    log = await page.evaluate('window.__fsaLog')
    requests = [e for e in log if e['event'] == 'requestPermission']
    c.check(requests and all(e['active'] for e in requests), 'permission requested during the Begin click', log)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check(any(f.startswith('P017/') and f.endswith(('.mp4', '.webm')) for f in files), 'take written to the same folder', files)
    c.check(not downloads, 'no browser download happened', downloads)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_folder_denied(pw, base):
    c = Checks('Folder permission refused: recording waits, the person chooses; never a download')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
    downloads = track_downloads(page)
    await setup_participant(page, base, save='folder')
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=5)
    await page.evaluate("sessionStorage.setItem('__fsa_mode', 'deny')")
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-folder:not([hidden])', timeout=10000)
    c.check(True, 'asks about the folder instead of recording elsewhere')
    await click(page, '#folderAllow')
    await page.wait_for_timeout(300)
    c.check(await page.is_visible('#folderError'), 'explains that permission was not given')
    await page.evaluate("sessionStorage.setItem('__fsa_mode', 'granted'); sessionStorage.setItem('__fsa_pick', 'second')")
    await click(page, '#folderChoose')
    await pass_check(page)
    await page.wait_for_selector('#screen-record:not([hidden])')
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
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
    downloads = track_downloads(page)
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.evaluate(SEED_LEGACY_TAKE)
    await page.fill('#setupId', 'SEMG0')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')
    await page.wait_for_selector('#setupStepFolder:not([hidden])')
    await click(page, '#setupFolderChoose')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await wait_for(page, "async () => (await V2S.storage.countTakes()) === 0", timeout=10000)
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check('previous-page-recordings/When did you know_1-290_repeat1_20260313_151311.mp4' in files,
            'old recording written to previous-page-recordings/', files)
    c.check(not any(f.startswith('SEMG0/') for f in files), 'nothing labelled with the new participant', files)
    await page.evaluate('() => V2S.app.showWelcome()')
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
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await cdp.send('Page.setInterceptFileChooserDialog', {'enabled': True})
    await page.fill('#setupId', 'P018')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')
    await page.wait_for_selector('#setupStepFolder:not([hidden])')
    await click(page, '#setupFolderChoose')
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
    c = Checks('Progress from the legacy page carries over; How to record shown once, no practice')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.evaluate(SEED_PROGRESS)
    await page.fill('#setupId', 'P020')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')
    # the earlier progress: its own question, after the ID
    await page.wait_for_selector('#setupStepLegacy:not([hidden])')
    legacy_text = await page.text_content('#setupLegacyContinue')
    c.check('Continue from sentence 116 of 350' in legacy_text, 'offers to continue from the earlier progress (its own step)', legacy_text)
    await click(page, '#setupLegacyContinue')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await click(page, '#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.text_content('#welcomePart') == 'Part 3 of 7', 'welcome shows part 3')
    await click(page, '#welcomeStart')
    await pass_check(page)
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 120 and s['where'] == 'Part 3 of 7 · Sentence 16 of 50' and s['coach'] is None, 'resumes at the same sentence, no coach', s)
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
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[FULL_STORAGE, NO_PICKERS])
    await record(page)
    c.check((await state(page))['index'] == 6, 'first take is accepted (nothing cached before it)')
    await page.wait_for_timeout(800)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])', timeout=8000)
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check('Save' in await page.text_content('#breakTitle') and 'almost full' in await page.text_content('#breakLead')
            and 'symbol-warn' in await page.get_attribute('#breakSymbol', 'class'),
            'goes to the save screen instead of recording: says why (device almost full), with a warning symbol')
    async with page.expect_download():
        await click(page, '#breakPrimary')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dialog_ready(page)
    await page.get_by_role('button', name='Yes, I see it').click()
    await page.wait_for_timeout(800)
    t = await takes(page)
    c.check(len(t) == 1 and t[0]['exported'], 'right after "Yes" the copy of the saved file is still on the device', t)
    c.check(await page.text_content('#breakTitle') == 'Make room on this device' and 'Check that the last saved file is there' in await page.text_content('#breakSaveText')
            and await page.is_visible('#breakSaveText') and await page.text_content('#breakPrimary') == 'It is saved — make room',
            'the device is full: it asks (visibly) to check the file before removing its copy', await page.text_content('#breakSaveText'))
    c.check(await page.evaluate("document.activeElement.id") != 'breakPrimary', '"make room" is not pre-selected for the keyboard')
    c.check('btn-go' not in await page.get_attribute('#breakPrimary', 'class'), '"make room" is not the blue "go on" button')
    await click(page, '#breakPrimary')  # It is saved — make room
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    c.check(await page.text_content('#dialogTitle') == 'Remove the copy from this device?' and len(await takes(page)) == 1, 'it asks before removing anything')
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Remove the copy').click()
    await page.wait_for_selector('#screen-record:not([hidden])', timeout=10000)
    c.check(len(await takes(page)) == 0, 'only then is the copy removed; straight back to the sentence')
    await wait_ready(page)
    await press(page, 'Space')
    await wait_for(page, "() => ['starting', 'recording'].includes(V2S.session.getState())", timeout=3000)
    c.check((await state(page))['screen'] == 'record', 'recording works again')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_finish_settings(pw, base):
    c = Checks('Finish for today, Settings (always reachable, one page per topic), light/dark, sign out')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[NO_PICKERS])
    await record(page)
    c.check(await page.is_visible('#settingsButton') and await page.is_visible('#finishButton') and await page.is_visible('#helpButton'),
            'top bar: End for today, help and settings (no other buttons)')
    c.check(await page.evaluate("document.getElementById('cardStatus').textContent.trim()") == '', 'no status text while waiting (and no clock)')
    await press(page, 'Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'")
    hidden = await page.evaluate("[...document.querySelectorAll('.topbar-start, .topbar-end')].every(n => getComputedStyle(n).visibility === 'hidden')")
    c.check(hidden, 'top-bar actions hidden while recording')
    await page.wait_for_timeout(1200)  # a real take (a second press within 1 s is a double press)
    await page.keyboard.press('Space')
    await wait_ready(page)
    await open_settings(page)
    text = await page.text_content('#settingsBody')
    for section in ['Sentences & progress', 'Saving', 'Camera and microphone', 'Recording quality', 'Appearance', 'About', 'Sign out']:
        c.check(section in text, f'settings: {section}')
    await page.locator('#settingsBody button.row', has_text='Recording quality').click()
    await wait_for(page, "() => document.getElementById('setResolution') !== null")
    values = await page.evaluate("['setResolution', 'setBitrate', 'setFps', 'setAudio'].map(id => document.getElementById(id).value)")
    c.check(values == ['1080p', '15000000', '30', 'raw'], 'recording quality (its own page): same defaults as the earlier page', values)
    await click(page, '#settingsBack')
    await page.locator('#settingsBody .segmented button', has_text='Dark').click()
    await page.wait_for_timeout(200)
    c.check(await page.get_attribute('html', 'data-theme') == 'dark', 'Settings → Appearance turns dark mode on')
    await click(page, '#settingsClose')
    await click(page, '#finishButton')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    c.check(s['dialog'] == 'End for today?' and s['focus'] == 'Keep going', 'End for today asks first; Keep going is the default', s)
    await page.keyboard.press('Enter')
    await page.wait_for_timeout(400)
    c.check((await state(page))['screen'] == 'record', 'Keep going: still recording')
    await end_for_today(page)
    await wait_for(page, "() => !document.getElementById('doneSave').hidden")
    c.check(await page.text_content('#doneTitle') == 'Great work today', 'done screen')
    c.check('2 recordings are not saved' in await page.text_content('#doneSaveText'), 'reminds about unsaved recordings')
    c.check(await page.text_content('#doneBody') == 'Please save your recordings before you close this page.',
            'does not say "you can close this page" while recordings are unsaved', await page.text_content('#doneBody'))
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    c.check(await page.get_attribute('html', 'data-theme') == 'dark', 'dark mode is remembered after reload')
    await click(page, '#settingsButton')
    await page.wait_for_selector('#settingsPanel:not([hidden])')
    visited = []
    page.on('framenavigated', lambda frame: visited.append(frame.url) if frame == page.main_frame else None)
    await page.get_by_role('button', name='Sign out').click()
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Sign out').click()
    await page.wait_for_timeout(1500)
    # (These tests sign in automatically on every page load, so the sign-in page forwards
    # straight back; what matters is that Sign out went there.)
    c.check(any('/index.html?next=' in url and 'app' in url for url in visited), 'Sign out goes to the sign-in page, which returns here', visited)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_signin(pw, base):
    c = Checks('Sign-in page: same style, light/dark, wrong password, then into the recorder')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE, authed=False, init_scripts=[FAST])
    html = open(os.path.join(REPO, 'index.html'), encoding='utf-8').read()
    user, password = re.search(r"username === '([^']+)' && password === '([^']+)'", html).groups()
    await page.goto(f'{base}/index.html?next=/{NEXT_PAGE}')
    await page.wait_for_selector('#loginForm')
    font = await page.evaluate("getComputedStyle(document.body).fontFamily")
    c.check('-apple-system' in font, 'same font as the recorder (the system font)', font)
    await click(page, '#themeButton')
    c.check(await page.get_attribute('html', 'data-theme') == 'dark', 'light/dark switch')
    await page.fill('#username', 'someone')
    await page.fill('#password', 'wrong')
    await click(page, 'button[type="submit"]')
    c.check(await page.text_content('#error') == 'Invalid username or password.', 'wrong password: plain message')
    await page.fill('#username', user)
    await page.fill('#password', password)
    await click(page, 'button[type="submit"]')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    c.check(NEXT_PAGE in page.url, 'signed in: the recorder opens (setup on a new device)', page.url)
    c.check(await page.get_attribute('html', 'data-theme') == 'dark', 'the theme carries over')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_keyboard_only(pw, base):
    c = Checks('Keyboard alone: setup → welcome → microphone test → How to record → a take')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'setupId'")
    await page.keyboard.type('p030')
    await press(page, 'Enter')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.wait_for_timeout(200)
    await press(page, 'Enter')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=8000)
    await page.wait_for_timeout(200)
    await press(page, 'Enter')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, "() => V2S.media.getStream() && document.activeElement && document.activeElement.id === 'checkNext'")
    await press(page, 'Enter')
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'testRecord'")
    await press(page, 'Enter')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden", timeout=10000)
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'testYes'")
    await press(page, 'Enter')
    await page.wait_for_selector('#screen-intro:not([hidden])')
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'introStart'")
    await press(page, 'Enter')
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(500)  # a press right after the screen appears is ignored (double press)
    await record(page)
    s = await state(page)
    c.check(s['index'] == 1, 'one practice take, keyboard only', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_clicker(pw, base):
    c = Checks('A presentation clicker alone (PageDown): welcome → camera → test → takes')
    browser, _, page, errors = await launch(pw, audio='speech', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await page.wait_for_timeout(300)
    await press(page, 'PageDown')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, "() => V2S.media.getStream() && document.activeElement && document.activeElement.id === 'checkNext'")
    await press(page, 'PageDown')
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'testRecord'")
    await press(page, 'PageDown')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden && document.activeElement && document.activeElement.id === 'testYes'", timeout=10000)
    await press(page, 'PageDown')
    await page.wait_for_selector('#screen-intro:not([hidden])')
    await wait_for(page, "() => document.activeElement && document.activeElement.id === 'introStart'")
    await press(page, 'PageDown')
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)
    await press(page, 'PageDown')
    await page.wait_for_timeout(1600)
    await press(page, 'PageDown')
    await wait_ready(page)
    c.check((await state(page))['index'] == 1, 'PageDown starts and stops a take')
    await press(page, 'PageUp')
    await page.wait_for_timeout(400)
    c.check((await state(page))['index'] == 0, 'PageUp = Redo')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_practice_save(pw, base):
    c = Checks('Folder mode, practice done: says where every recording goes; nothing to do')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
    await setup_participant(page, base, save='folder')
    await set_progress(page, howtoSeen=True, coachDone=False, currentIndex=4)
    await start_session(page)
    await record(page)
    await page.keyboard.press('Space')  # Continue
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden", timeout=15000)
    await wait_for(page, "() => document.getElementById('breakSaveText').textContent.includes('by itself')", timeout=15000)
    c.check('picked/P017' in await page.text_content('#breakSaveText') and await page.text_content('#breakPrimary') == 'Continue to part 1',
            'names the folder; Continue to part 1', await page.text_content('#breakSaveText'))
    await page.evaluate('V2S.exporter.flushFolderWrites()')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check(any(f.startswith('P017/') and f.endswith(('.mp4', '.webm')) for f in files), 'the practice recording is already in the folder', files)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_set_switch(pw, base):
    c = Checks('Switching the sentence set: a trained participant is not taught again')
    browser, _, page, errors = await boot(pw, base, index=7, init_scripts=[NO_PICKERS])
    await open_settings(page, 'Sentences & progress')
    await page.select_option('#setSentenceSet', 'Open_300sentences')
    await confirm_dialog(page, 'Yes, continue')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=10000)
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 0 and s['coach'] is None and s['where'] == 'Practice 1 of 5', 'new set: from its first sentence, no coaching', s)
    c.check(await page.evaluate("V2S.app.state().setKey") == 'Open_300sentences', 'the new set is in use')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_store_failure_late(pw, base):
    c = Checks('A store that fails after End for today: the next session starts at that sentence')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[FAIL_COMMIT, NO_PICKERS])
    await record(page)
    await page.evaluate('window.__failDelayMs = 2500; window.__failCommits = 1')
    await record(page)  # sentence 2: stored late, and that fails
    await end_for_today(page)
    await page.wait_for_timeout(3500)
    await page.evaluate('V2S.session.flush()')
    stored = await page.evaluate("async () => (await V2S.storage.getProgress('P017::50words_350sentences')).currentIndex")
    c.check(stored == 6, 'stored progress went back to the sentence that failed', stored)
    await page.evaluate('() => V2S.app.showWelcome()')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.text_content('#welcomeCount') == 'Sentence 2 of 50', 'welcome: sentence 2 of 50 is next', await page.text_content('#welcomeCount'))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


FAIL_SUPERSEDE_LOG = """
window.__failMarks = 0;
document.addEventListener('DOMContentLoaded', () => {
  const wait = setInterval(() => {
    if (!window.V2S || !V2S.storage || !V2S.storage.markSupersedeDone) return;
    clearInterval(wait);
    const original = V2S.storage.markSupersedeDone;
    V2S.storage.markSupersedeDone = (...args) => {
      if (window.__failMarks > 0) {
        window.__failMarks -= 1;
        return Promise.reject(new DOMException('Simulated failure', 'NoModificationAllowedError'));
      }
      return original(...args);
    };
  }, 5);
});
"""


async def s_folder_failure(pw, base):
    c = Checks('Folder mode: one failed write never stops the writes after it')
    browser, _, page, errors = await boot(pw, base, save='folder', fsa=True, index=5, init_scripts=[FAIL_SUPERSEDE_LOG])
    await record(page)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    await page.evaluate('window.__failMarks = 1')
    await page.keyboard.press('ArrowLeft')  # Redo: its folder step fails
    await page.wait_for_timeout(400)
    await record(page)
    await record(page)  # the next take must still reach the folder
    await end_for_today(page)
    await wait_for(page, "() => !document.getElementById('doneSaveText').textContent.includes('Saving')", timeout=25000)
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    videos = [f for f in files if f.endswith(('.mp4', '.webm')) and f.count('/') == 1]
    c.check(len(videos) >= 3, 'later takes were still written to the folder', videos)
    c.check('saved in' in await page.text_content('#doneSaveText'), 'the done screen settles (no endless "Saving…")', await page.text_content('#doneSaveText'))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_stale_backups(pw, base):
    c = Checks('Backup list out of date (the earlier page cleared storage): unsaved recordings still counted')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[NO_PICKERS])
    await page.evaluate("V2S.storage.setSetting('exportedTakeIds', [99990, 99991])")
    await record(page)
    await end_for_today(page)
    await wait_for(page, "() => !document.getElementById('doneSave').hidden", timeout=10000)
    c.check('1 recording is not saved' in await page.text_content('#doneSaveText'), 'still says 1 recording is not saved', await page.text_content('#doneSaveText'))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_too_loud(pw, base):
    c = Checks('Too loud (clipping): retry with a reason, same sentence')
    browser, _, page, errors = await boot(pw, base, media='shim', index=5)
    await page.evaluate("window.__v2sAudio.set('loud')")
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 5 and 'Too loud' in (s['message'] or ''), 'says it was too loud; same sentence', s['message'])
    c.check([x['status'] for x in t] == ['qc_failed'], 'kept as qc_failed', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_no_audio(pw, base):
    c = Checks('No audio analysis at all: blames the microphone, same sentence')
    browser, _, page, errors = await boot(pw, base, index=5)
    await page.evaluate('() => V2S.meter.detach()')
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 5 and 'microphone sent no sound' in (s['message'] or ''), 'says the microphone sent no sound', s['message'])
    c.check([x['status'] for x in t] == ['qc_failed'], 'take kept as qc_failed', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_timeout(pw, base):
    c = Checks('A take longer than 60 s restarts the same sentence')
    browser, _, page, errors = await boot(pw, base, index=5)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(61500)
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 5 and 'over a minute' in (s['message'] or ''), 'same sentence, explains the timeout', s)
    c.check([x['status'] for x in t] == ['aborted_timeout'], 'take kept as aborted_timeout', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


# Every option the earlier page (app.html v114) offered, checked by the words its users
# know (the earlier page's own labels), plus what was added since. Found in Settings, on
# the page of its topic (None = the first page).
LEGACY_OPTIONS = [
    ('Select Sentence Set', 'Sentences & progress', 'select#setSentenceSet'),
    ('Previous', 'Sentences & progress', 'button:has-text("Previous sentence")'),
    ('Next / Skip', 'Sentences & progress', 'button:has-text("Next sentence (skip)")'),
    ('Reset Progress', 'Sentences & progress', 'button:has-text("Reset progress")'),
    ('Clear Storage', 'Saving', 'button:has-text("Clear storage")'),
    ('Save All', 'Saving', 'button:has-text("Save all recordings now")'),
    ('Logout', None, 'button:has-text("Sign out (log out)")'),
    ('Recording Resolution', 'Recording quality', 'select#setResolution'),
    ('Recording Quality', 'Recording quality', 'select#setBitrate'),
    ('Recording Frame Rate', 'Recording quality', 'select#setFps'),
    ('Audio Mode', 'Recording quality', 'select#setAudio'),
    ('Mirror Video Display', 'Recording quality', 'input#setMirror'),
    # added since
    ('Go to sentence', 'Sentences & progress', 'input#setJump'),
    ('Camera', 'Camera and microphone', 'select#setCamera'),
    ('Microphone', 'Camera and microphone', 'select#setMicrophone'),
    ('Switch participant', 'Sentences & progress', 'button:has-text("Switch participant")'),
    ('Held-press limit', 'Sentences & progress', 'select#setHold'),
    ('Light / dark', None, '.segmented button:has-text("Dark")'),
    ('Download event log', 'About', 'button:has-text("Download event log")'),
]
LEGACY_LABEL_PAGES = {'setSentenceSet': 'Sentences & progress', 'setResolution': 'Recording quality', 'setBitrate': 'Recording quality', 'setFps': 'Recording quality', 'setAudio': 'Recording quality'}

# The earlier page's option texts, word for word.
LEGACY_LABELS = {
    'setSentenceSet': ['50words_350sentences', 'Open_300sentences'],
    'setResolution': ['720p (1280×720) - Standard', '1080p (1920×1080) - Recommended', '480p (854×480) - Standard', '360p (640×360) - Low Quality', 'Auto - Camera Default'],
    'setBitrate': ['8 Mbps - Compatibility', '12 Mbps - High Quality', '15 Mbps - Research Quality', '25 Mbps - Fast Motion', '40 Mbps - Maximum Quality'],
    'setFps': ['30 fps - Standard', '60 fps - Fast Motion'],
    'setAudio': ['Raw - Disable Browser Processing', 'Fallback - Browser Default'],
}


async def s_settings_parity(pw, base):
    c = Checks('Settings hold every option of the earlier page, and they work')
    browser, _, page, errors = await boot(pw, base, index=7, init_scripts=[NO_PICKERS])
    for section in [None, 'Sentences & progress', 'Saving', 'Camera and microphone', 'Recording quality', 'About']:
        await open_settings(page, section)
        for label, where, selector in LEGACY_OPTIONS:
            if where == section:
                c.check(await page.locator(f'#settingsPanel {selector}').count() >= 1, f'option: {label} ({where or "first page"})')
        for select_id, labels in LEGACY_LABELS.items():
            if LEGACY_LABEL_PAGES[select_id] == section:
                found = await page.evaluate("id => [...document.getElementById(id).options].map(o => o.textContent)", select_id)
                c.check(sorted(found) == sorted(labels), f'{select_id}: the earlier page\'s options, same words', found)
        if section == 'Sentences & progress':
            c.check('Round 1' in await page.text_content('#settingsBody'), 'says which round (repeat number) new recordings get')
        await click(page, '#settingsClose')
        await page.wait_for_timeout(150)
    await open_settings(page, 'Sentences & progress')
    await page.locator('#settingsPanel button', has_text='Previous sentence').click()
    await wait_ready(page)
    c.check((await state(page))['index'] == 6, 'Previous: one sentence back')
    await open_settings(page, 'Sentences & progress')
    await page.locator('#settingsPanel button', has_text='Next sentence (skip)').click()
    await confirm_dialog(page, 'Yes, continue')
    await wait_ready(page)
    c.check((await state(page))['index'] == 7, 'Next (skip): asks first, then one sentence on')
    await open_settings(page, 'Sentences & progress')
    await page.fill('#setJump', '120')
    await page.get_by_role('button', name='Go', exact=True).click()
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 + 119 and s['where'] == 'Part 3 of 7 · Sentence 20 of 50', 'Go to sentence 120', s)
    c.check(s['redo'] is None, 'Redo never reaches across a jump', s)
    await open_settings(page, 'Sentences & progress')
    await page.locator('#settingsPanel button', has_text='Reset progress').click()
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(300)
    c.check(await page.is_visible('#settingsPanel') and not await page.evaluate('V2S.ui.isDialogOpen()'),
            'Esc closes only the question, Settings stays open')
    await click(page, '#settingsClose')
    c.check(not errors, 'no page errors', errors)
    await browser.close()

    # Skip practice (bypass warm-up), from the very first sentence.
    browser, _, page, errors = await boot(pw, base, trained=False, init_scripts=[NO_PICKERS])
    s = await state(page)
    c.check(s['index'] == 0 and s['coach'], 'a new participant starts with coached practice', s)
    await open_settings(page, 'Sentences & progress')
    await page.locator('#settingsPanel button', has_text='Skip practice (bypass warm-up)').click()
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['coach'] is None and s['where'] == 'Part 1 of 7 · Sentence 1 of 50', 'Skip practice: Part 1, sentence 1, no coaching', s)
    progress = await page.evaluate('V2S.app.state().progress')
    c.check(progress['coachDone'] and progress['howtoSeen'], 'practice and How to record count as done')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


SHEET_FITS_JS = """() => {
  const sheet = document.querySelector('#settingsPanel .sheet');
  const limit = Math.min(window.innerWidth, sheet.getBoundingClientRect().right) + 1;
  const wide = [...sheet.querySelectorAll('*')].filter(n => n.getClientRects().length && n.getBoundingClientRect().right > limit);
  return { scroll: sheet.scrollWidth - sheet.clientWidth, wide: wide.slice(0, 5).map(n => n.tagName + '.' + n.className + ' ' + (n.textContent || '').slice(0, 30)) };
}"""


async def s_settings_fit(pw, base):
    c = Checks('Settings fit every screen: nothing wider than the panel')
    for name, viewport, kind in FIT_VIEWPORTS:
        browser, _, page, errors = await boot(pw, base, index=7, viewport=viewport, has_touch=kind != 'wide' and ENGINE != 'firefox',
                                              is_mobile=kind in ('phone', 'flat'), init_scripts=[NO_PICKERS])
        for section in [None, 'Sentences & progress', 'Saving', 'Camera and microphone', 'Recording quality', 'About']:
            await open_settings(page, section)
            r = await page.evaluate(SHEET_FITS_JS)
            c.check(r['scroll'] <= 1 and not r['wide'], f'{name}: settings ({section or "first page"}) fits', r)
            await click(page, '#settingsClose')
            await page.wait_for_timeout(150)
        c.check(not errors, f'{name}: no page errors', errors)
        await browser.close()
    return c.done()


async def s_redo_reload(pw, base):
    c = Checks('A Redo under way survives a reload; it still returns to the right place')
    browser, _, page, errors = await boot(pw, base, index=5)
    await record(page)
    await record(page)
    await page.keyboard.press('ArrowLeft')  # Redo sentence 2
    await page.wait_for_timeout(400)
    await page.evaluate('V2S.session.flush()')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 6 and s['redoLabel'] == 'Cancel redo', 'back on the sentence being redone, Cancel redo offered', s)
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 7, 'afterwards: on to where they were', s)
    c.check([x['status'] for x in t if x['index'] == 6] == ['superseded', 'accepted'], 'the replaced take is superseded', t)
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(400)
    await page.evaluate('V2S.session.flush()')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await start_session(page)
    await page.keyboard.press('ArrowLeft')  # Cancel redo
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 7 and s['redoLabel'] == 'Redo', 'Cancel redo after a reload: back where they were', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_practice_again(pw, base):
    c = Checks('Practice again (Settings): coached practice, then back to the same sentence')
    browser, _, page, errors = await boot(pw, base, index=5 + 20, init_scripts=[NO_PICKERS])
    await open_settings(page, 'Sentences & progress')
    await page.locator('#settingsPanel button', has_text='Practice again').click()
    await confirm_dialog(page, 'Yes, continue')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 0 and s['where'] == 'Practice 1 of 5' and s['coach'] == 'Press Space once.' and s['detail'] == 'No need to hold it.', 'practice 1, coached', s)
    for _ in range(2):
        await record(page)
    s = await state(page)
    c.check(s['index'] == 2 and s['pulse'] == 'redo', 'practice 3 suggests Redo', s)
    await record(page)  # Start right away instead of Redo: allowed
    c.check((await state(page))['index'] == 3, 'Start works without doing the Redo lesson')
    for _ in range(2):
        await record(page)
    c.check((await state(page))['state'] == 'partEnd', 'practice 5 done: pause on the last practice sentence')
    await page.evaluate('V2S.session.flush()')
    stored = await page.evaluate("async () => (await V2S.storage.getProgress('P017::50words_350sentences')).currentIndex")
    c.check(stored == 25, 'the place to come back to is already stored (End for today here would keep it)', stored)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakPrimary') == 'Save recordings', 'practice done (ZIP mode): save the practice recordings first')
    async with page.expect_download():
        await click(page, '#breakPrimary')
    await confirm_dialog(page, 'Yes, I see it')
    await page.wait_for_timeout(300)
    c.check(await page.text_content('#breakPrimary') == 'Continue to part 1', 'then back to where they were')
    await click(page, '#breakPrimary')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 25 and s['coach'] is None, 'back on the sentence they were on, no coach', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_rounds(pw, base):
    c = Checks('Rounds: Redo after the last sentence stays in the round; recording again starts round 2')
    browser, _, page, errors = await boot(pw, base, index=354, init_scripts=[NO_PICKERS])
    await record(page)
    s = await state(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Finish', 'the very last sentence: pause with Finish', s)
    await page.evaluate('V2S.session.flush()')
    progress = await page.evaluate("V2S.storage.getProgress('50words_350sentences')")
    c.check(progress['completed'] and progress['repetitionCount'] == 1, 'legacy key: completed, repetitionCount 1 (as the earlier page)', progress)
    await page.keyboard.press('ArrowLeft')  # Redo the last sentence
    await page.wait_for_timeout(400)
    await page.evaluate('V2S.session.flush()')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    c.check(await page.is_visible('#welcomeStart'), 'a reload during that Redo comes back to it (not "all done")')
    await start_session(page)
    s = await state(page)
    c.check(s['index'] == 354 and s['redoLabel'] == 'Cancel redo', 'still redoing the last sentence', s)
    await record(page)
    t = await takes(page)
    c.check([x['status'] for x in t] == ['superseded', 'accepted'] and all('_repeat1_' in x['fileName'] for x in t),
            'Redo of the last sentence: still repeat1, replaces the first take', t)
    await page.keyboard.press('Space')  # Finish
    await page.wait_for_selector('#screen-done:not([hidden])')
    c.check(await page.text_content('#doneTitle') == 'All sentences done', 'all done')
    await page.evaluate('() => V2S.app.showWelcome()')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    title = await page.text_content('#welcomeTitle')
    label = await page.text_content('#welcomeStart') if await page.is_visible('#welcomeStart') else None
    c.check(title == 'All sentences done' and label in (None, 'Save recordings') and await page.is_hidden('#welcomeLater'),
            'welcome: all done — nothing to start (only saving, if something is unsaved)', (title, label))
    await open_settings(page, 'Sentences & progress')
    await page.locator('#settingsPanel button', has_text='Reset progress').click()
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    body = await page.text_content('#dialogBody')
    c.check('round 2' in body and 'repeat2' in body, 'Reset progress after the end says it starts round 2', body)
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Yes, continue').click()
    try:
        await wait_for(page, "() => document.body.dataset.screen === 'welcome' && document.getElementById('welcomeTitle').textContent === 'Welcome'", timeout=10000)
        c.check(True, 'back to the very start (Welcome, as on the first visit)')
    except Exception:
        c.check(False, 'back to the very start (Welcome, as on the first visit)', await page.text_content('#welcomeTitle'))
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=5)
    await start_session(page)
    await record(page)
    t = await takes(page)
    c.check('_1-350_repeat2_' in t[-1]['fileName'] and t[-1]['status'] == 'accepted' and t[-1]['round'] == 2,
            'new recordings: repeat2', t[-1])
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_zip_backups(pw, base):
    c = Checks('ZIP backups: kept after "Yes", left out of the next ZIP, can be saved again')
    browser, _, page, errors = await boot(pw, base, index=5 + 49, init_scripts=[NO_PICKERS])
    await record(page)
    await page.keyboard.press('Space')  # Finish part 1
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    async with page.expect_download():
        await click(page, '#breakPrimary')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await dialog_ready(page)
    await page.get_by_role('button', name='Yes, I see it').click()
    await page.wait_for_timeout(600)
    await click(page, '#breakPrimary')  # Continue to part 2
    await wait_ready(page)
    await record(page)
    await open_settings(page, 'Saving')
    text = await page.text_content('#settingsSavingStatus')
    c.check('Not saved yet1 recording' in text and 'Backup copies1' in text, 'Settings: 1 not saved yet, plus 1 backup copy', text)
    async with page.expect_download() as info:
        await page.locator('#settingsPanel button', has_text='Save all recordings now').click()
    download = await info.value
    path = os.path.join(tempfile.mkdtemp(), download.suggested_filename)
    await download.save_as(path)
    with zipfile.ZipFile(path) as archive:
        videos = [n for n in archive.namelist() if n.endswith(('.mp4', '.webm'))]
    c.check(len(videos) == 1 and '_51-350_' in videos[0], 'the new ZIP holds only what was not saved yet', videos)
    await confirm_dialog(page, 'Yes, I see it')
    await page.wait_for_selector('#settingsPanel:not([hidden])')
    async with page.expect_download() as info:
        await page.locator('#settingsPanel button', has_text='Save backup copies again').click()
    download = await info.value
    path = os.path.join(tempfile.mkdtemp(), download.suggested_filename)
    await download.save_as(path)
    with zipfile.ZipFile(path) as archive:
        videos = [n for n in archive.namelist() if n.endswith(('.mp4', '.webm'))]
        manifest = json.loads(archive.read('manifest.json'))
    c.check(len(videos) == 2 and manifest['backupCopies'], 'backup copies can be saved again (a mistaken "Yes" loses nothing)', videos)
    await confirm_dialog(page, 'Yes, I see it')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_part_end_redo(pw, base):
    c = Checks("A part's last sentence can be redone before the break; the ZIP keeps only the new take usable")
    browser, _, page, errors = await boot(pw, base, index=5 + 49, init_scripts=[NO_PICKERS])
    await record(page)
    s = await state(page)
    c.check(s['state'] == 'partEnd' and s['redo'] and 'This sentence again' in s['redo'], 'Redo offered for the last sentence', s)
    await page.keyboard.press('ArrowLeft')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 54 and s['redoLabel'] == 'Cancel redo', 'redoing sentence 50 of part 1', s)
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Finish part 1', 'then the pause again, Finish part 1', s)
    c.check([x['status'] for x in t] == ['superseded', 'accepted'], 'the first take of it is superseded', t)
    await page.keyboard.press('Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    c.check(await page.text_content('#breakTitle') == 'Part 1 done', 'Part 1 done')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    async with page.expect_download() as info:
        await click(page, '#breakPrimary')
    download = await info.value
    path = os.path.join(tempfile.mkdtemp(), download.suggested_filename)
    await download.save_as(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        log = json.loads(archive.read('P017/logs/superseded.json'))
    usable = [n for n in names if n.endswith(('.mp4', '.webm')) and n.count('/') == 1]
    unused = [n for n in names if '/not_used/' in n and n.endswith(('.mp4', '.webm'))]
    c.check(len(usable) == 1 and usable[0].rsplit('.', 1)[0].endswith('_redo'), 'ZIP: P017/ holds only the new take', usable)
    c.check(len(unused) == 1 and unused[0].split('/')[-1] == t[0]['fileName'], 'ZIP: the replaced take is in P017/not_used/', unused)
    c.check(log['replaced'][0]['fileName'] == t[0]['fileName'], 'ZIP: P017/logs/superseded.json lists it', log)
    await confirm_dialog(page, 'Yes, I see it')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_two_tabs(pw, base):
    c = Checks('Opened twice: the second copy asks first; taking over stops the first one')
    browser, context, page, errors = await boot(pw, base, index=5)
    second = await context.new_page()
    await second.goto(next_url(base))
    await second.wait_for_selector('#screen-error:not([hidden])', timeout=15000)
    c.check(await second.text_content('#errorTitle') == 'Already open in another tab', 'the second tab says the page is already open')
    await click(second, '#errorAction')  # Use this tab instead
    await page.wait_for_selector('#screen-error:not([hidden])', timeout=10000)
    c.check(await page.text_content('#errorTitle') == 'Opened in another tab', 'the first tab stops and says why')
    c.check(await page.evaluate('V2S.media.getStream()') is None, 'the first tab released the camera')
    await second.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    c.check(True, 'the second tab carries on (Welcome back)')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_long_take(pw, base):
    c = Checks('A long take (22 s): no false camera failure; the clock appears after 20 s')
    browser, _, page, errors = await boot(pw, base, index=5)
    await page.keyboard.press('Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'")
    await page.wait_for_timeout(12000)
    s = await state(page)
    c.check(s['state'] == 'recording' and s['timer'] == '', 'after 12 s: still recording, no clock yet', s)
    await page.wait_for_timeout(9500)
    s = await state(page)
    c.check(s['state'] == 'recording' and re.fullmatch(r'· 0:2[0-9]', s['timer'] or ''), 'after 20 s: still recording, the clock shows on Stop', s)
    c.check(s['message'] is None and s['pulse'] == 'main', 'a quiet reminder: Stop pulses (no text near the sentence)', s)
    await page.keyboard.press('Space')
    await wait_ready(page)
    t = await takes(page)
    c.check((await state(page))['index'] == 6 and [x['status'] for x in t] == ['accepted'], 'accepted', t)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


FAIL_COMMIT = """
window.__failCommits = 0;
window.__failQuota = false;
window.__failDelayMs = 0;   // a store that fails only after a while (noticed late)
document.addEventListener('DOMContentLoaded', () => {
  const wait = setInterval(() => {
    if (!window.V2S || !V2S.storage || !V2S.storage.commitTake) return;
    clearInterval(wait);
    const original = V2S.storage.commitTake;
    V2S.storage.commitTake = (...args) => {
      if (window.__failCommits > 0) {
        window.__failCommits -= 1;
        const error = new DOMException('Simulated failure', window.__failQuota ? 'QuotaExceededError' : 'UnknownError');
        return new Promise((resolve, reject) => setTimeout(() => reject(error), window.__failDelayMs));
      }
      return original(...args);
    };
  }, 5);
});
"""


async def s_store_failure(pw, base):
    c = Checks('A take that cannot be stored: back to that sentence (nothing skipped); repeated failures explained')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[FAIL_COMMIT, NO_PICKERS])
    await page.evaluate('window.__failCommits = 1')
    await record(page)
    await page.wait_for_timeout(800)
    s = await state(page)
    c.check(s['index'] == 5 and 'could not be stored' in (s['message'] or ''), 'back on the same sentence, says so', s)
    await record(page)
    await page.wait_for_timeout(500)
    c.check((await state(page))['index'] == 6, 'recording it again works')
    progress = await page.evaluate("V2S.storage.getProgress('P017::50words_350sentences')")
    c.check(progress['currentIndex'] == 6, 'stored progress matches', progress['currentIndex'])
    await page.evaluate('window.__failCommits = 2')
    await record(page)
    await page.wait_for_timeout(800)
    await record(page)
    await page.wait_for_selector('#screen-error:not([hidden])', timeout=8000)
    c.check(await page.text_content('#errorTitle') == 'Recordings cannot be saved on this device', 'twice in a row: a screen explains')
    await click(page, '#errorAction')  # Try again
    await wait_ready(page)
    await record(page)
    await page.wait_for_timeout(500)
    c.check((await state(page))['index'] == 7, 'afterwards recording works, from the sentence that failed')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


FIT_RULES = {'wide': (40, 56, 2), 'tall': (36, 52, 2), 'phone': (28, 36, 3), 'flat': (26, 34, 2)}
FIT_VIEWPORTS = [
    ('laptop', {'width': 1440, 'height': 900}, 'wide'),
    ('tablet sideways', {'width': 1180, 'height': 820}, 'wide'),
    ('tablet upright', {'width': 820, 'height': 1180}, 'tall'),
    ('phone upright', {'width': 390, 'height': 844}, 'phone'),
    ('small phone upright', {'width': 375, 'height': 667}, 'phone'),
    ('Android phone upright', {'width': 360, 'height': 740}, 'phone'),
    ('phone sideways', {'width': 844, 'height': 390}, 'flat'),
]

FIT_JS = """async () => {
  const rec = document.getElementById('screen-record');
  const card = document.getElementById('card');
  const sentence = document.getElementById('sentenceText');
  const all = V2S.app.state().material.all;
  const size = parseFloat(getComputedStyle(sentence).fontSize);
  const out = { fit: rec.dataset.fit, size, overflow: rec.scrollHeight - rec.clientHeight, worst: 0, oneLine: 0, twoLines: 0, cardFits: true };
  for (const text of all) {
    // as the page shows it while recording: in its highlighted line span, phrases kept whole
    const line = document.createElement('span');
    line.className = 'sentence-line';
    line.textContent = V2S.ui.phrased(text);
    sentence.replaceChildren(line);
    const lines = Math.round(sentence.getBoundingClientRect().height / (size * 1.2));
    out.worst = Math.max(out.worst, lines);
    if (lines === 1) out.oneLine += 1;
    if (lines <= 2) out.twoLines += 1;
    if (sentence.scrollWidth > card.clientWidth) out.cardFits = false;
  }
  out.oneLine = out.oneLine / all.length;
  out.twoLines = out.twoLines / all.length;
  return out;
}"""


async def s_fit(pw, base):
    c = Checks('Sentence size on every device: one continuous line where possible, never cramped, nothing moves')
    for name, viewport, kind in FIT_VIEWPORTS:
        browser, _, page, errors = await boot(pw, base, index=5, viewport=viewport, has_touch=kind != 'wide' and ENGINE != 'firefox', is_mobile=kind in ('phone', 'flat'))
        r = await page.evaluate(FIT_JS)
        low, high, lines = FIT_RULES[kind]
        c.check(r['fit'].startswith(kind) and low <= r['size'] <= high, f'{name}: {kind} size {r["size"]} px within {low}–{high}', r)
        c.check(r['worst'] <= lines and r['cardFits'] and r['overflow'] <= 1, f'{name}: every sentence fits in {lines} lines, inside the card, nothing overflows', r)
        if kind != 'phone':
            c.check(r['oneLine'] >= 0.9, f'{name}: {r["oneLine"]:.0%} of sentences on one line', r)
        else:
            # never "keywords one by one": most sentences on at most two lines
            c.check(r['twoLines'] >= 0.975, f'{name}: {r["twoLines"]:.1%} of sentences on at most two lines', r)
        c.check(not errors, f'{name}: no page errors', errors)
        await browser.close()
    return c.done()


SCENARIOS = {
    'first_run': s_first_run,
    'normal': s_normal,
    'hold': s_hold,
    'no_speech': s_no_speech,
    'redo': s_redo,
    'redo_folder': s_redo_folder,
    'speech_before_start': s_speech_before_start,
    'tail': s_tail,
    'recorder_retry': s_recorder_retry,
    'low_rate_mic': s_low_rate_mic,
    'bluetooth': s_bluetooth,
    'mic_test_silent': s_mic_test_silent,
    'help': s_help,
    'double_tap': s_double_tap,
    'held_keys': s_held_keys,
    'save_keys': s_save_keys,
    'camera_denied': s_camera_denied,
    'card_stable': s_card_stable,
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
    'finish_settings': s_finish_settings,
    'signin': s_signin,
    'keyboard': s_keyboard_only,
    'clicker': s_clicker,
    'too_loud': s_too_loud,
    'practice_save': s_practice_save,
    'store_failure_late': s_store_failure_late,
    'folder_failure': s_folder_failure,
    'stale_backups': s_stale_backups,
    'set_switch': s_set_switch,
    'no_audio': s_no_audio,
    'fit': s_fit,
    'settings_parity': s_settings_parity,
    'settings_fit': s_settings_fit,
    'redo_reload': s_redo_reload,
    'practice_again': s_practice_again,
    'rounds': s_rounds,
    'zip_backups': s_zip_backups,
    'part_end_redo': s_part_end_redo,
    'two_tabs': s_two_tabs,
    'long_take': s_long_take,
    'store_failure': s_store_failure,
    'timeout': s_timeout,
}

# Scenarios that make sense in every engine (no Chrome-only file dialogs, flags or sample rates).
CROSS_ENGINE = ['first_run', 'normal', 'hold', 'no_speech', 'redo', 'speech_before_start', 'tail', 'recorder_retry',
                'bluetooth', 'mic_test_silent', 'help', 'double_tap', 'held_keys', 'save_keys', 'camera_denied', 'card_stable', 'device', 'reload', 'break_zip', 'legacy', 'storage_full',
                'finish_settings', 'signin', 'keyboard', 'clicker', 'too_loud', 'set_switch', 'no_audio', 'fit', 'settings_parity', 'settings_fit', 'redo_reload',
                'practice_again', 'rounds', 'zip_backups', 'part_end_redo', 'two_tabs', 'long_take', 'store_failure',
                'store_failure_late', 'stale_backups']


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
