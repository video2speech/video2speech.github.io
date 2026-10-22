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

from common import NEXT_PAGE, REPO, SCENARIO_LINES, Checks, launch, next_url, say, static_server

ENGINE = 'chrome'
SCENARIO_LIMIT_S = 300
RUN_ALONE = {'file_integrity'}
# A short microphone test and a small picture (many browsers record side by side; the
# file_integrity scenario records at the real settings).
# Scenarios about other things keep the earlier default set and skip the sentence-set
# question before each session (s_set_check tests both as the page really is).
CLASSIC = "defaultSet: '50words_350sentences', setCheck: false"
FAST = "window.__V2S_TEST = { testRecordMs: 1200, resolution: '360p', " + CLASSIC + " };"
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
    fit: rec.dataset.fit || null,
    // The floating guide (practice and a part's end): its parts, or null when hidden.
    prompt: document.getElementById('cardPrompt').hidden ? null : Object.fromEntries(
      ['Label', 'Head', 'Text', 'Detail', 'Note'].map(k => [k.toLowerCase(), document.getElementById('prompt' + k).textContent])),
    spot: (document.querySelector('.is-spotlit') || {}).id || null
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


READ_OPFS_B64 = """async ([dirName, path]) => {
  let dir = await (await navigator.storage.getDirectory()).getDirectoryHandle(dirName);
  const parts = path.split('/');
  for (const part of parts.slice(0, -1)) dir = await dir.getDirectoryHandle(part);
  const buf = new Uint8Array(await (await (await dir.getFileHandle(parts[parts.length - 1])).getFile()).arrayBuffer());
  let bin = '';
  for (let i = 0; i < buf.length; i += 0x8000) bin += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
  return btoa(bin);
}"""


def probe_media(path):
    """A recording as a player sees it: (problems, info). Decodes every frame with ffmpeg,
    checks there is a picture and a sound track, the length, and that the sound is not silent."""
    import subprocess
    problems = []
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path],
                         capture_output=True, text=True)
    if out.returncode:
        return [f'ffprobe failed: {out.stderr.strip()[:200]}'], {}
    data = json.loads(out.stdout)
    kinds = {st['codec_type']: st for st in data.get('streams', [])}
    video, audio = kinds.get('video'), kinds.get('audio')
    if not video or not int(video.get('width') or 0):
        problems.append('no picture')
    if not audio:
        problems.append('no sound track')
    decode = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af', 'volumedetect', '-f', 'null', '-'],
                            capture_output=True, text=True)
    # volumedetect prints at info level: run again for it (errors only above).
    if decode.stderr.strip():
        problems.append('decode errors: ' + decode.stderr.strip()[:200])
    vol = subprocess.run(['ffmpeg', '-i', path, '-vn', '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True)
    mean = re.search(r'mean_volume: (-?[\d.]+) dB', vol.stderr)
    frames = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                             'stream=nb_read_frames', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    # Duration from the decoded stream end (some WebM files have no duration in the header).
    dur = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'packet=pts_time', '-select_streams', 'a:0', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.split()
    try:
        duration = max(float(x.strip(',')) for x in dur if x.strip(',') not in ('', 'N/A'))
    except ValueError:
        duration = None
    info = {'video': video and f"{video.get('codec_name')} {video.get('width')}x{video.get('height')}",
            'audio': audio and f"{audio.get('codec_name')} {audio.get('sample_rate')} Hz",
            'frames': frames, 'duration': duration, 'meanVolume': mean and float(mean.group(1))}
    if mean is None or float(mean.group(1)) < -60:
        problems.append('sound is silent')
    if not frames.isdigit() or int(frames) < 10:
        problems.append('too few video frames')

    def times(stream):
        rows = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream, '-show_entries', 'packet=pts_time,duration_time',
                               '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.split()
        out = []
        for row in rows:
            parts = row.split(',')
            try:
                out.append((float(parts[0]), float(parts[1]) if len(parts) > 1 and parts[1] not in ('', 'N/A') else 0.0))
            except ValueError:
                pass
        return sorted(out)
    vt, at = times('v:0'), times('a:0')
    # The picture never stops: no gap between frames over 0.25 s, and no frozen stretch.
    vgap = max((b[0] - a[0] for a, b in zip(vt, vt[1:])), default=None)
    info['videoMaxGap'] = vgap and round(vgap, 3)
    if vgap is None or vgap > 0.25:
        problems.append(f'video has a gap of {vgap} s (dropped or frozen frames)')
    freeze = subprocess.run(['ffmpeg', '-i', path, '-an', '-vf', 'freezedetect=n=0.001:d=0.5', '-f', 'null', '-'],
                            capture_output=True, text=True).stderr
    if 'freeze_start' in freeze:
        problems.append('picture frozen for 0.5 s or more')
    # The sound is continuous: each packet starts where the one before ended (within 20 ms),
    # no stretch of digital silence (a dropout), and it lines up with the picture.
    # (The encoder's first packet can sit apart from the rest at 0 s: AAC priming, not a dropout.)
    gaps = [(b[0] - (a[0] + a[1]), a[0] + a[1]) for a, b in zip(at, at[1:]) if a[0] + a[1] > 0.1]
    agap = max((g for g, _ in gaps), default=None)
    info['audioMaxGap'] = agap and round(agap, 3)
    info['audioGapsAt'] = [round(t, 3) for g, t in gaps if g > 0.02]
    if agap is None or agap > 0.02:
        problems.append(f'sound has a gap of {agap} s')
    dropout = subprocess.run(['ffmpeg', '-i', path, '-vn', '-af', 'silencedetect=n=-90dB:d=0.05', '-f', 'null', '-'],
                             capture_output=True, text=True).stderr
    if 'silence_start' in dropout:
        problems.append('sound drops out (digital silence)')
    if vt and at:
        v_end, a_end = vt[-1][0], at[-1][0] + at[-1][1]
        info['avStart'] = round(at[0][0] - vt[0][0], 3)
        info['avEnd'] = round(a_end - v_end, 3)
        if abs(at[0][0] - vt[0][0]) > 0.2:
            problems.append(f'sound and picture start {info["avStart"]} s apart')
        if abs(a_end - v_end) > 0.3:
            problems.append(f'sound and picture end {info["avEnd"]} s apart')
    return problems, info


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
    # The practice intro (first time), or how it works line by line (coming back).
    for _ in range(8):
        if not await page.is_visible('#screen-intro'):
            break
        await click(page, '#introStart')
        await page.wait_for_timeout(150)


async def start_session(page):
    """Welcome → check (camera, then the test recording) → recording screen, waiting."""
    if await page.is_visible('#welcomeLater'):   # unsaved recordings: go on without saving (it asks first)
        await click(page, '#welcomeLater')
        await dialog_ready(page)
        await page.locator('#dialogActions button', has_text='Continue without saving').click()
    else:
        await click(page, '#welcomeStart')
    if await page.evaluate('() => V2S.config.SET_CHECK'):   # the page as it really is: confirm the set
        await wait_for(page, '() => V2S.ui.isDialogOpen()', timeout=20000)
        await dialog_ready(page)
        await page.locator('#dialogActions button', has_text='Yes, start').click()
    await pass_check(page)
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(500)  # presses in the first 0.4 s are ignored (double press)


async def boot(pw, base, audio='speech', save='zip', trained=True, index=None, init_scripts=(), progress=None, set_key=None, **kwargs):
    """Set up P017 and open the recording screen. trained=True skips How to record and the
    practice coaching (most scenarios are about real sentences); index jumps there."""
    kwargs.setdefault('engine', ENGINE)
    browser, context, page, errors = await launch(pw, audio=audio, init_scripts=[FAST, *init_scripts], **kwargs)
    await setup_participant(page, base, save=save)
    if set_key:   # another sentence set, as chosen in Settings
        await page.evaluate("key => V2S.storage.setSetting('setKey', key)", set_key)
        await page.reload()
        await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    fields = {}
    if trained:
        fields.update(howtoSeen=True, coachDone=True)
    if index is not None:
        fields.update(currentIndex=index, completed=False)
    fields.update(progress or {})
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
    c.check(question == 'Could you see your face and hear your voice clearly?' and await page.text_content('#checkMicTitle') == 'Did the test work?',
            'after the playback: the title asks, then whether the face is visible and the sound is clear', question)
    # iPhone/iPad with the microphone on turn a video's own sound down (or to the earpiece):
    # the test plays through the audio context, from the speaker, like the cue sounds.
    routed = await page.evaluate("document.getElementById('checkPlayback').dataset.speaker === '1'")
    c.check(routed, 'the test recording plays through the audio context (loud from the speaker on iPhone)', routed)
    await page.evaluate("window.__v2sAudio.set('silence')")  # sitting quietly, reading the screen
    await click(page, '#testYes')
    # Before the practice: the one thing to remember (no page of rules).
    await page.wait_for_selector('#screen-intro:not([hidden])')
    intro = {k: (await page.text_content(f'#intro{k}')).replace('\xa0', ' ') for k in ('Title', 'Rule', 'Lead', 'Start')}
    c.check(intro['Title'] == 'One thing to remember' and intro['Rule'].startswith('Press Space to start recording, then read the green sentence out loud.')
            and 'Press Space again to stop recording.' in intro['Rule'] and '5 short sentences' in intro['Lead']
            and 'only for practice' in intro['Lead'] and intro['Start'] == 'Begin practice',
            'before the practice: the one thing to remember, and that it is only practice', intro)
    await click(page, '#introStart')
    # How to record is taught inside the practice, one step at a time, in a guide that
    # floats next to the control to press.
    await page.wait_for_selector('#screen-record:not([hidden])')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(400)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['where'] == 'Practice 1 of 5' and s['status'] == '', 'Practice 1 of 5, no status text while waiting', s['where'])
    c.check(pr.get('label') == 'Step 1 · Start recording' and 'Space' in pr.get('text', '') and 'to start recording' in pr.get('text', '')
            and pr.get('detail') == 'Then read the green sentence out loud.' and s['spot'] == 'mainButton',
            'step 1: press Space to start recording, then read; Start is lifted out', pr)
    c.check(s['redo'] is None, 'no Redo before anything is recorded', s['redo'])

    await page.evaluate("window.__v2sAudio.set('speech')")
    await press(page, 'Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'")
    await page.wait_for_timeout(1300)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(' '.join(pr.get('text', '').split()) == 'When you finish, press Space to end recording' and s['message'] is None,
            'while recording: when you finish, press Space to end recording; nothing else appears', pr)
    c.check(s['status'] == 'Recording' and s['timer'] == '', 'pill: "Recording" (no clock on short takes)', s)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await press(page, 'Space')
    await wait_ready(page)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['index'] == 1 and pr.get('label') == 'Step 2 · Every sentence' and pr.get('detail') == 'Every sentence works the same way.',
            'practice 2: every sentence works the same way', pr)
    c.check(s['redo'] and 'I need the water' in s['redo'], 'Redo names the sentence it would record again', s['redo'])

    await take_quietly(page)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['index'] == 2 and pr.get('label') == 'Step 3 · Redo last sentence' and '←' in pr.get('text', '')
            and pr.get('note') == 'This is only practice — nothing went wrong.' and s['spot'] == 'redoButton',
            'practice 3: the Redo lesson alone (Redo lifted out; says it is only practice)', pr)
    await page.evaluate("window.__v2sAudio.set('speech')")   # reading the new sentence aloud
    await page.wait_for_timeout(2600)
    s = await state(page)
    await page.evaluate("window.__v2sAudio.set('silence')")
    c.check((s['prompt'] or {}).get('label') == 'Step 3 · Redo last sentence' and not s['message'],
            'reading aloud during the lesson: still the lesson (no "Not recording yet")', s['prompt'])
    await press(page, 'Space')   # the lesson is not skipped by Space (owner, 2026-10-15)
    await page.wait_for_timeout(400)
    c.check((await state(page))['state'] == 'ready', 'Space does not skip the Redo lesson')
    await press(page, 'ArrowLeft')
    await page.wait_for_timeout(400)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['index'] == 1 and pr.get('label') == 'Redo' and 'read it again' in pr.get('text', '') and s['redoLabel'] == 'Cancel redo',
            'Redo goes back to practice 2: read it again; Cancel redo offered', s)
    await take_quietly(page)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['index'] == 2 and pr.get('label') == 'Redo done', 'back on practice 3: Redo done, then the next sentence', pr)
    t = await takes(page)
    c.check([x['status'] for x in t if x['index'] == 1] == ['superseded', 'accepted'], 'the replaced recording is marked superseded', t)
    c.check(t[-1]['fileName'].rsplit('.', 1)[0].endswith('_redo'), 'the new one ends with _redo', t[-1]['fileName'])

    await take_quietly(page)
    await take_quietly(page)
    await take_quietly(page)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['state'] == 'partEnd' and s['main'] == 'Continue' and 'Practice done' in (pr.get('head') or ''),
            'after practice 5 the sentence stays: Practice done, then Continue', s)
    await press(page, 'Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakTitle') == 'Practice done', 'Practice done screen')
    c.check('Save your practice recordings now' in await page.text_content('#breakLead') and await page.text_content('#breakPrimary') == 'Save recordings'
            and await page.is_hidden('#breakParts'),
            'saving is learnt by doing it once (ZIP mode): one instruction, Save recordings', await page.text_content('#breakLead'))
    async with page.expect_download() as info:
        await click(page, '#breakPrimary')
    c.check((await info.value).suggested_filename.startswith('P017_practice_'), 'a practice ZIP', (await info.value).suggested_filename)
    await confirm_dialog(page, 'Yes, I see it')
    await page.wait_for_timeout(300)
    c.check(await page.text_content('#breakPrimary') == 'Continue' and await page.text_content('#breakSaveText') == 'Your practice recordings are saved.'
            and await page.is_hidden('#breakRule') and await page.is_hidden('#breakParts'),
            'practice done, saved: only that, and Continue', await page.text_content('#breakSaveText'))
    await click(page, '#breakPrimary')
    # How to record, confirmed one line at a time, then a page to get ready for part 1.
    await page.wait_for_selector('#screen-intro:not([hidden])')
    c.check(await page.text_content('#introTitle') == 'Before the real sentences' and await page.is_visible('#introReview'),
            'then how to record, one line at a time', await page.text_content('#introTitle'))
    lines = await page.evaluate("[...document.querySelectorAll('#introReview li')].length")
    for _ in range(lines):
        await click(page, '#introStart')
        await page.wait_for_timeout(150)
    await page.wait_for_function("() => document.getElementById('introTitle').textContent === 'Part 1 of 7'")
    c.check(await page.text_content('#introStart') == 'Start part 1' and '50 sentences in each part' in await page.text_content('#introLead'),
            'then get ready: Part 1 of 7, 50 sentences each, Start part 1')
    await click(page, '#introStart')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['prompt'] is None and s['where'] == 'Part 1 of 7 · Sentence 1 of 50',
            'real sentences: no guide, "Part 1 of 7 · Sentence 1 of 50"', s)
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
    await press(page, 'Space')
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
    await press(page, 'Space')
    await page.wait_for_timeout(300)  # after the 0.14 s colour change, within the 0.7 s tail
    s = await state(page)
    # The next sentence shows at once (owner, 2026-10-15); the take finishes behind it.
    c.check(s['card'] == 'ready-busy' and s['sentence'].replace('\xa0', ' ') == 'What is that there?' and s['status'] == ''
            and s['sentenceColor'] == await css_color(page, '--sentence-wait'),
            'Stop: the next sentence shows at once, grey (the take finishes behind it)', s)
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    t_ready = await page.evaluate('performance.now()')
    meta = await page.evaluate(LAST_META_JS)
    tail = meta['timing']['tailMs']
    c.check(700 <= tail <= 900, 'kept recording 0.7 s after Stop', tail)
    c.check((t_ready - t_stop) - tail < 450, 'next sentence right after the tail (storage in the background)', round(t_ready - t_stop - tail))
    s = await state(page)
    c.check(s['index'] == 6 and s['status'] == '' and s['message'] == 'Press Space to start, then read.',
            'next sentence: the sentence, Start and the one quiet hint (no "Recorded")', s)
    mk = meta['markers']
    # The sentence turns green as the recorder is started (instant start): a few ms either way.
    c.check(mk['startPress'] <= mk['recorderStart'] and mk['startPress'] <= mk['readNow'] <= mk['stopPress'] <= mk['recorderStop']
            and abs(mk['readNow'] - mk['recorderStart']) <= 50, 'time markers in order', mk)
    lead = meta['timing']['startCueLeadMs']
    c.check(lead <= 150 and mk['recorderStart'] - mk['startPress'] <= 190, 'recording starts right after the short cue (no missed words)',
            {'cueLeadMs': lead, 'pressToRecorder': round(mk['recorderStart'] - mk['startPress'])})
    c.check(-50 <= mk['readNow'] - mk['recorderStart'] <= 300, 'green as soon as the recorder runs', round(mk['readNow'] - mk['recorderStart']))
    c.check(meta['timing']['startAttempts'] == 1 and meta['participantId'] == 'P017' and meta['qc']['speechMs'] > 300,
            'sidecar: one start attempt, participant, check metrics', meta['timing'])
    c.check('_1-350_repeat1_' in meta['fileName'], 'legacy-compatible file name', meta['fileName'])
    # Other scenarios shorten some limits for speed; the real ones are these.
    real = await page.evaluate("[V2S.config.MAX_TAKE_MS, V2S.config.TIMER_SHOW_AFTER_MS, V2S.config.QC.QUIET_RMS, V2S.config.QC.QUIET_PEAK, V2S.config.QC.QUIET_SKIP_MS]")
    c.check(real == [120000, 20000, 0.0025, 0.02, 250], 'the real limits: a take stops at 2 min, its clock shows after 20 s; too quiet below RMS 0.0025 and peak 0.02', real)
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
    c = Checks('No sound: retry with a reason; second failure offers Keep')
    # The microphone check passes with speech; then the room is silent. (A fan alone now
    # passes, as on the page before the redesign: only a nearly silent take is retried.)
    browser, _, page, errors = await boot(pw, base, audio='speech', media='shim', index=5)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await press(page, 'Space')
    await page.wait_for_timeout(150)
    await page.keyboard.press('Space')  # tremor double tap: ignored (debounce)
    await page.wait_for_timeout(500)
    c.check((await state(page))['card'] == 'recording', 'a double tap does not stop the take')
    await page.wait_for_timeout(900)
    await press(page, 'Space')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 5 and s['tone'] == 'warn' and "couldn’t hear" in (s['message'] or '') and 'press Space' in (s['message'] or ''), 'first failure: same sentence + reason (names the key)', s)
    await record(page, 1300, stop=False)
    await press(page, 'Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    s = await state(page)
    c.check(s['dialog'] and 'twice' in s['dialog'] and s['focus'] == 'Try again', 'second failure: Try again (default) or Keep', s)
    await press(page, 'Enter')
    await wait_ready(page)
    c.check((await state(page))['index'] == 5, 'Enter = try again, same sentence')
    await record(page, 1300, stop=False)
    await press(page, 'Space')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    await page.wait_for_timeout(450)
    await page.get_by_role('button', name='Keep it and go on').click()
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 6, 'Keep it and go on moves on', s)
    c.check([x['status'] for x in t] == ['qc_failed', 'qc_failed', 'qc_overridden'], 'statuses recorded', [x['status'] for x in t])
    # The start cue from a speaker, picked up in the first moments, then silence: still
    # "nothing heard" (the quiet check leaves out the first 250 ms).
    await page.evaluate("""() => document.addEventListener('keydown', () => {
      __v2sAudio.set('speech'); setTimeout(() => __v2sAudio.set('silence'), 80); }, { once: true, capture: true })""")
    await record(page, 1300)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 6 and s['tone'] == 'warn' and t[-1]['status'] == 'qc_failed',
            'a start cue picked up at the start, then silence: still retried (nothing heard)', (s['message'], t[-1]['status']))
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
    c.check(s['index'] == 7 and s['redoLabel'] == 'Redo last sentence' and 'again' not in (s['message'] or ''), 'Cancel redo: back where they were, nothing recorded', s)
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
    await press(page, 'ArrowLeft')
    await page.wait_for_timeout(400)
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    videos = [f for f in files if f.endswith(('.mp4', '.webm'))]
    usable = [f for f in videos if '/not_used/' not in f]
    unused = [f for f in videos if '/not_used/' in f]
    c.check(len(usable) == 2 and any(f.rsplit('.', 1)[0].endswith('_redo') for f in usable), 'P017/<session>/: one file per sentence, the redo included', usable)
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
    # When the card turned ready and when each message showed, timed in the page itself
    # (so a busy test machine cannot shift them).
    watch = """document.addEventListener('DOMContentLoaded', () => {
      window.__timeline = [];
      const note = () => {
        const rec = document.getElementById('screen-record');
        const msg = document.getElementById('messageText');
        if (rec && msg) window.__timeline.push({ t: performance.now(), on: !rec.hidden && rec.dataset.state === 'ready', message: msg.textContent });
      };
      new MutationObserver(note).observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['data-state', 'hidden'] });
    });"""
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=[watch])
    await page.wait_for_timeout(4500)
    timing = await page.evaluate("""() => {
      const tl = window.__timeline;
      const warn = tl.find(e => e.message.startsWith('Not recording yet'));
      // The last moment the sentence came on screen, waiting for Start, before the warning.
      let readyAt = null;
      tl.forEach((e, i) => { if (e.on && !(i && tl[i - 1].on) && (!warn || e.t <= warn.t)) readyAt = e.t; });
      return { readyAt, warnAt: warn ? warn.t : null };
    }""")
    gap = timing['warnAt'] - timing['readyAt'] if timing['warnAt'] and timing['readyAt'] else None
    c.check(gap is not None and gap >= 1500 + 500, 'no warning in the first moments (people often say a word after Stop): not before 1.5 s + 0.5 s of speech',
            None if gap is None else round(gap))
    s = await state(page)
    c.check(s['message'] == 'Not recording yet. Press Space first, then read.' and s['status'] == '', 'hint while not recording (names the key on a computer)', s)
    await press(page, 'Space')
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
    c = Checks('Microphone test hears nothing: says so; three equal choices (try again, another microphone, a condition that stops the voice)')
    browser, _, page, errors = await launch(pw, audio='silence', media='shim', engine=ENGINE, init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await wait_for(page, '() => V2S.media.getStream() !== null')
    await click(page, '#checkNext')
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testChoices').hidden", timeout=10000)
    titles = await page.locator('#testChoices .choice-title').all_text_contents()
    c.check(await page.text_content('#checkMicTitle') == 'We couldn’t hear you'
            and titles == ['Try again', 'Use another microphone', 'My condition stops me making enough sound'],
            'the title says nothing was heard; three choices', titles)
    await page.mouse.move(1, 1)   # no pointer resting on one of them (hover)
    await page.wait_for_timeout(100)
    styles = await page.evaluate("[...document.querySelectorAll('#testChoices .choice')].map(b => { const c = getComputedStyle(b); return [c.backgroundColor, c.borderColor, c.color, c.fontSize].join(' '); })")
    c.check(len(set(styles)) == 1, 'the three choices look the same (none stands out by colour)', styles)
    c.check(await page.is_hidden('#testRecord') and await page.is_hidden('#testYes') and await page.is_hidden('#checkHelp'),
            'nothing else to press: no Start, no Continue, no help link', None)
    c.check(await page.evaluate("document.activeElement.id") == 'testRetry', 'keys: Try again is focused')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await click(page, '#testRetry')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden", timeout=10000)
    c.check(await page.is_hidden('#testChoices') and await page.text_content('#checkMicTitle') == 'Did the test work?',
            'Try again with sound: the playback and question appear, the choices are gone')
    # A condition that stops the voice: asked once, then the recording goes on without sound.
    await click(page, '#testAgain')
    await page.wait_for_selector('#checkStepCamera:not([hidden])')
    await page.evaluate("window.__v2sAudio.set('silence')")
    await click(page, '#checkNext')
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testChoices').hidden", timeout=10000)
    await click(page, '#testNoVoice')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    c.check(await page.text_content('#dialogTitle') == 'Record without sound?', 'asks first: Record without sound?')
    await confirm_dialog(page, 'Yes, record without sound')
    await wait_for(page, "() => !document.getElementById('screen-intro').hidden")
    c.check(await page.evaluate('V2S.qc.allowsSilent()'), 'yes: recordings are kept without sound for this participant')
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
    await ready_for_press(page)   # the part's end takes presses after 1 s
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
    c.check(s['dialog'] == 'How to record' and len(steps) == 3 and 'green' in steps[1] and 'Made a mistake?' in await page.text_content('#dialogBody')
            and '←' in await page.text_content('#dialogBody'),
            'three numbered steps (Start, read when green, Stop), then how to fix a mistake (←)', steps)
    await page.keyboard.press('Space')   # straight away, as a person might
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
    await press(page, 'Space')
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
    await press(page, 'Space')
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
    c.check(s['state'] == 'partEnd' and s['main'] == 'Go to break' and s['status'] == '' and s['redoLabel'] == 'Redo last sentence'
            and 'Part 1 done' in ((s['prompt'] or {}).get('head') or ''),
            "part's last sentence: stays on screen, Redo still possible; the guide says Part 1 done, Go to break", s)
    await press(page, 'Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakTitle') == 'Part 1 done', 'Part 1 done')
    c.check(await page.text_content('#breakLead') == 'First, save the recordings from this\xa0part.' and await page.text_content('#breakPrimary') == 'Save recordings'
            and await page.is_hidden('#breakSecondary') and await page.is_visible('#finishButton'),
            'one instruction: save first (the rest comes after); End for today in the top bar, not under the button', await page.text_content('#breakLead'))
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
    c.check(len(usable) == cached_before and all(re.match(r'P017/session-[\d_-]+/[^/]+$', n) for n in usable), 'accepted takes in P017/<session>/', usable)
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
    await press(page, 'Space')  # Finish part 1
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
    usable = [f for f in files if re.match(r'P017/session-[\d_-]+/[^/]+\.(mp4|webm)$', f)]
    unused = [f for f in files if re.match(r'P017/session-[\d_-]+/not_used/[^/]+\.(mp4|webm)$', f)]
    c.check(len(usable) == 1 and len(unused) == 1, 'accepted take in P017/<session>/, the held (discarded) one in its not_used/', files)
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
    browser, context, page, errors = await launch(pw, audio='speech', init_scripts=['window.__V2S_TEST = { ' + CLASSIC + ' };'])
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
    await press(page, 'Space')
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
    await press(page, 'Space')
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
    await press(page, 'Enter')
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
    await press(page, 'Space')  # Continue
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden", timeout=15000)
    await wait_for(page, "() => document.getElementById('breakSaveText').textContent.includes('by itself')", timeout=15000)
    c.check('picked/P017' in await page.text_content('#breakSaveText') and await page.text_content('#breakPrimary') == 'Continue',
            'names the folder; Continue', await page.text_content('#breakSaveText'))
    await page.evaluate('V2S.exporter.flushFolderWrites()')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    c.check(any(re.match(r'P017/session-[\d_-]+/practice/[^/]+\.(mp4|webm)$', f) for f in files),
            'the practice recording is already in the folder, apart from the real ones (practice/)', files)
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
    await press(page, 'ArrowLeft')  # Redo: its folder step fails
    await page.wait_for_timeout(400)
    await record(page)
    await record(page)  # the next take must still reach the folder
    await end_for_today(page)
    await wait_for(page, "() => /saved in/.test(document.getElementById('doneSaveText').textContent)", timeout=25000)
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    videos = [f for f in files if f.endswith(('.mp4', '.webm')) and '/not_used/' not in f]
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
    c = Checks('A take longer than the limit (2 min; 4 s here) restarts the same sentence')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=["window.__V2S_TEST = { testRecordMs: 1200, resolution: '360p', maxTakeMs: 4000, " + CLASSIC + " };"])
    await press(page, 'Space')
    await page.wait_for_timeout(5500)
    await wait_ready(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['index'] == 5 and 'over 2 minutes' in (s['message'] or ''), 'same sentence, explains the timeout', s)
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
    ('Switch participant', None, 'button:has-text("Switch participant")'),
    ('Held-press limit', None, 'select#setHold'),
    ('Light / dark', None, '.segmented button:has-text("Dark")'),
    ('Download event log', 'About', 'button:has-text("Download event log")'),
]
LEGACY_LABEL_PAGES = {'setSentenceSet': 'Sentences & progress', 'setResolution': 'Recording quality', 'setBitrate': 'Recording quality', 'setFps': 'Recording quality', 'setAudio': 'Recording quality'}

# The earlier page's option texts, word for word.
LEGACY_LABELS = {
    'setSentenceSet': ['50words_350sentences', 'Open_300sentences', 'oct16-openVocab-350', 'open-vocab-350-oct17', 'open-vocab-v3', 'open-vocab-v3.1', 'open-vocab-v3.3'],   # the earlier page's two, then the sets added 2026-10-16/17/18/21
    'setResolution': ['720p (1280×720) - Standard', '1080p (1920×1080) - Recommended', '480p (854×480) - Standard', '360p (640×360) - Low Quality', 'Auto - Camera Default'],
    'setBitrate': ['8 Mbps - Compatibility', '12 Mbps - High Quality', '15 Mbps - Research Quality', '25 Mbps - Fast Motion', '40 Mbps - Maximum Quality'],
    'setFps': ['30 fps - Standard', '60 fps - Fast Motion'],
    'setAudio': ['Raw - Disable Browser Processing', 'Fallback - Browser Default'],
}


RAINBOW_FIRST = 'When the sunlight strikes raindrops in the air, they act as a prism and form a rainbow.'
# The owner's text (2026-10-14), word for word, with the classic "act as a prism"
# (Fairbanks 1960; owner's choice, 2026-10-15).
RAINBOW_TEXT = ('When the sunlight strikes raindrops in the air, they act as a prism and form a rainbow. '
                'The rainbow is a division of white light into many beautiful colors. '
                'These take the shape of a long round arch, with its path high above, and its two ends apparently beyond the horizon. '
                'There is, according to legend, a boiling pot of gold at one end. '
                'People look, but no one ever finds it. '
                'When a man looks for something beyond his reach, his friends say he is looking for the pot of gold at the end of the rainbow.')

# The practice sentence on the card: clear of the Recording sign; how far its middle is from
# the card's middle (a share of the card's height).
PRACTICE_ROOM_JS = """() => {
  const $ = id => document.getElementById(id);
  const card = $('card').getBoundingClientRect(), line = $('sentenceText').getBoundingClientRect(), sign = $('cardStatus').getBoundingClientRect();
  return { coaching: $('screen-record').classList.contains('is-coaching'), clear: line.top >= sign.bottom + 2,
           offset: Math.round(((line.top + line.bottom) / 2 - (card.top + card.bottom) / 2) / card.height * 100) / 100,
           fit: $('screen-record').dataset.fit };
}"""

# Each passage sentence on the card as laid out now: every line whole phrases, and the
# browser shows exactly those lines (no extra wrap).
PHRASE_BREAKS_JS = r"""async () => {
  const m = await V2S.sentences.loadRainbow();
  const line = document.getElementById('sentenceText').firstElementChild;
  const keep = line.dataset.text;
  const bad = [];
  let lines = 0;
  for (const s of m.all) {
    V2S.ui.writeSentence(line, s);
    const layout = V2S.ui.passageLayout(s);
    if (!layout) { bad.push('no layout: ' + s.slice(0, 24)); continue; }
    const phrases = V2S.sentences.phrasesOf(s).map(p => p.text);
    let k = 0;
    for (const l of layout) {
      const acc = [];
      while (k < phrases.length && acc.join(' ') !== l) acc.push(phrases[k++]);
      if (acc.join(' ') !== l) { bad.push('not whole phrases: ' + l); break; }
    }
    const range = document.createRange();
    range.selectNodeContents(line);
    const tops = new Set([...range.getClientRects()].filter(r => r.width > 1).map(r => Math.round(r.top)));
    if (tops.size !== layout.length) bad.push(`shown in ${tops.size} lines, laid out in ${layout.length}: ${s.slice(0, 24)}`);
    lines += layout.length;
  }
  if (keep) V2S.ui.writeSentence(line, keep);
  return { bad, lines };
}"""

# Each sentence of the set and of the Rainbow Passage on the card, against the Recording sign
# and the longest message the card can show (in both its styles).
CARD_ROOM_JS = r"""async () => {
  const ui = V2S.ui, $ = id => document.getElementById(id);
  const keys = document.documentElement.classList.contains('has-keyboard');
  const text = e => (typeof e === 'function' ? e(keys) : e);
  const r = V2S.copy.record;
  const messages = [...Object.values(V2S.copy.feedback).map(text), r.partEndPart(7), r.partEndAll, r.partEndRainbow, text(r.redoing)];
  const line = $('sentenceText').firstElementChild, message = $('message'), body = $('messageText');
  const out = {};
  for (const [name, list] of [['main', V2S.app.state().material.all], ['rainbow', (await V2S.sentences.loadRainbow()).all]]) {
    ui.fitSentences(list);
    await new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)));
    const status = $('cardStatus').getBoundingClientRect();
    let messageTop = Infinity;
    for (const tone of ['warn', 'note']) {
      message.className = `message tone-${tone}`;
      for (const m of messages) { body.textContent = m; messageTop = Math.min(messageTop, message.getBoundingClientRect().top); }
    }
    message.className = 'message is-empty';
    body.textContent = '';
    const hits = [];
    for (const s of list) {
      ui.writeSentence(line, s);
      const box = $('sentenceText').getBoundingClientRect();
      if (box.top < status.bottom + 2 || box.bottom > messageTop - 2) hits.push(s.slice(0, 30));
    }
    out[name] = { fit: $('screen-record').dataset.fit, hits };
  }
  return out;
}"""


async def finish_set(page):
    """The 350-sentence set's very last sentence, then Continue: the Rainbow Passage (no question)."""
    await record(page)
    await press(page, 'Space')   # Continue
    await wait_for(page, "() => V2S.session.getState() === 'ready' && V2S.session.getContext().setKey === 'rainbow'")


async def s_rainbow(pw, base):
    c = Checks('Rainbow Passage (folder): read once, right after the 350 sentences, sentence by sentence, saved to <ID>/<session>/rainbow/')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
    await setup_participant(page, base, save='folder')
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=354, completed=False)
    await start_session(page)
    await record(page)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(s['state'] == 'partEnd' and pr.get('head') == 'All 7 parts done.' and pr.get('detail') == 'Next: the Rainbow Passage, 6 sentences.'
            and s['main'] == 'Continue', "the set's last sentence: All 7 parts done; next, the Rainbow Passage (no question)", pr)
    await press(page, 'Space')
    await wait_for(page, "() => V2S.session.getState() === 'ready' && V2S.session.getContext().setKey === 'rainbow'")
    s = await state(page)
    sentence = (await page.text_content('#sentenceText')).replace('\xa0', ' ')
    c.check(sentence == RAINBOW_FIRST and s['coach'] is None, 'the passage from its first sentence, one at a time, no coaching', sentence)
    words = await page.evaluate("V2S.sentences.loadRainbow().then(m => m.all)")
    c.check(' '.join(words) == RAINBOW_TEXT, 'the six sentences are exactly the owner\'s text (the phrase marks are not part of them)')
    breaks = await page.evaluate(PHRASE_BREAKS_JS)
    c.check(breaks['bad'] == [], f'lines break only between its phrases ({breaks["lines"]} lines for the six)', breaks['bad'][:3])
    c.check(s['where'] == 'Rainbow Passage · 1 of 6', 'where you are: Rainbow Passage · 1 of 6', s['where'])
    await record(page)
    await record(page)
    # Settings moves within the passage; the sentence set stays as it is (no new round).
    await open_settings(page, 'Sentences & progress')
    body = await page.text_content('#settingsBody')
    c.check('Rainbow Passage · 3 of 6' in body and 'Practise again' not in body and 'Skip practice' not in body,
            'Settings during the passage: where it is in the passage; no practice options', body[:200])
    await page.locator('#settingsPanel button', has_text='Previous sentence').click()
    await wait_ready(page)
    s = await state(page)
    main = await page.evaluate("(() => { const p = V2S.app.state().progress; return [V2S.storage.roundOf(p), p.completed, p.rainbow]; })()")
    c.check(s['where'] == 'Rainbow Passage · 2 of 6' and await page.evaluate("V2S.session.getContext().setKey") == 'rainbow'
            and main[:2] == [1, True] and main[2] != 'done', 'Previous: the passage\'s sentence 2; the set untouched (round 1, all done)', (s['where'], main))
    for _ in range(5):
        await record(page)
    s = await state(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Finish' and (s['prompt'] or {}).get('head') == 'Rainbow Passage done.',
            'its last sentence: stays with Finish (Redo still possible)', s)
    await press(page, 'Space')
    await page.wait_for_selector('#screen-done:not([hidden])', timeout=10000)
    c.check(await page.text_content('#doneTitle') == 'All sentences done', 'then all done')
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    videos = sorted(f for f in files if re.match(r'P017/session-[\d_-]+/rainbow/[^/]+\.(mp4|webm)$', f))
    c.check(len(videos) == 6 and all(re.search(r'_rainbow[1-6]-6_repeat1_', f) for f in videos),
            'six recordings in P017/<session>/rainbow/, named …_rainbow<n>-6_repeat1_…', videos)
    c.check(all(f.rsplit('.', 1)[0] + '.json' in files for f in videos), 'each with its JSON sidecar')
    replaced = [f for f in files if re.match(r'P017/session-[\d_-]+/rainbow/not_used/[^/]+\.(mp4|webm)$', f)]
    c.check(len(replaced) == 1 and '_rainbow2-6_repeat1_' in replaced[0], 'the replaced take of sentence 2 in its rainbow/not_used/', replaced)
    meta = await page.evaluate(READ_OPFS_JSON, ['picked', videos[0].rsplit('.', 1)[0] + '.json'])
    c.check(meta.get('sentenceSet') == 'rainbow' and meta.get('status') == 'accepted', 'the sidecar: sentenceSet rainbow, accepted', meta.get('sentenceSet'))
    set_files = [f for f in files if re.match(r'P017/session-[\d_-]+/[^/]+\.(mp4|webm)$', f)]
    c.check(len(set_files) == 1 and '_350-350_' in set_files[0], "the set's last sentence stays in P017/<session>/", set_files)
    await page.evaluate('() => V2S.app.showWelcome()')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.text_content('#welcomeTitle') == 'All sentences done', 'coming back: all done (the passage is read once)')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_rainbow_zip(pw, base):
    c = Checks('Rainbow Passage (ZIP): a reload goes on where it was; saved under <ID>/<session>/rainbow/; End for today before it; after every set, each its own')
    browser, _, page, errors = await boot(pw, base, index=354, init_scripts=[NO_PICKERS])
    await finish_set(page)
    await record(page)
    await record(page)
    await page.evaluate('V2S.session.flush()')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    part = await page.text_content('#welcomePart')
    count = await page.text_content('#welcomeCount')
    c.check(await page.text_content('#welcomeTitle') == 'Welcome back' and part == 'Rainbow Passage' and count == 'Sentence 3 of 6',
            'a reload mid-passage: Welcome back, Rainbow Passage, sentence 3 of 6', (part, count))
    await start_session(page)
    s = await state(page)
    c.check(await page.evaluate("V2S.session.getContext().setKey") == 'rainbow' and s['index'] == 2 and s['where'] == 'Rainbow Passage · 3 of 6',
            'it goes on with the passage, at sentence 3', s)
    breaks = await page.evaluate(PHRASE_BREAKS_JS)
    c.check(not breaks['bad'], f'{ENGINE}: the passage shows exactly its lines of whole phrases ({breaks["lines"]} lines)', breaks['bad'][:3])
    for _ in range(4):
        await record(page)
    await press(page, 'Space')   # Finish
    await page.wait_for_selector('#screen-done:not([hidden])', timeout=10000)
    async with page.expect_download() as info:
        await click(page, '#doneSave')
    download = await info.value
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Yes, I see it').click()
    path = os.path.join(tempfile.mkdtemp(), download.suggested_filename)
    await download.save_as(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    videos = [n for n in names if re.match(r'P017/session-[\d_-]+/rainbow/[^/]+\.(mp4|webm)$', n)]
    c.check(len(videos) == 6 and all('_rainbow' in n and '-6_repeat1_' in n for n in videos), 'the ZIP holds the six under P017/<session>/rainbow/', videos)
    c.check(any(re.match(r'P017/session-[\d_-]+/[^/]+_350-350_', n) for n in names), "the set's last sentence at P017/<session>/", names)
    await page.evaluate('() => V2S.app.showWelcome()')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.text_content('#welcomeTitle') == 'All sentences done', 'afterwards: all done (the passage is read once)')
    c.check(not errors, 'no page errors', errors)
    await browser.close()

    # End for today on the last sentence: the next visit goes on with the passage.
    browser, _, page, errors = await boot(pw, base, index=354, init_scripts=[NO_PICKERS])
    await record(page)
    await end_for_today(page)
    await page.evaluate('V2S.session.flush()')
    await page.evaluate('() => V2S.app.showWelcome()')
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    c.check(await page.text_content('#welcomePart') == 'Rainbow Passage' and await page.is_visible('#welcomeStart'),
            'End for today on the last sentence: the next visit has Continue, the Rainbow Passage', await page.text_content('#welcomePart'))
    await start_session(page)
    s = await state(page)
    c.check(await page.evaluate("V2S.session.getContext().setKey") == 'rainbow' and s['where'] == 'Rainbow Passage · 1 of 6',
            'Continue: the check, then the passage from its first sentence', s['where'])
    c.check(not errors, 'no page errors', errors)
    await browser.close()

    # Every set ends with the Rainbow Passage (owner, 2026-10-16), each set its own: a passage
    # read after the 350-sentence set (before 2026-10-16, without `afterSet`) does not count.
    browser, _, page, errors = await launch(pw, audio='speech', init_scripts=[FAST, NO_PICKERS])
    await setup_participant(page, base)
    await page.evaluate("""async () => {
      const p = await V2S.storage.createParticipantProgress('P017', 'rainbow', null);
      Object.assign(p, { currentIndex: 5, completed: true, completedAt: new Date().toISOString() });
      await V2S.storage.saveParticipantProgress(p);
      await V2S.storage.setSetting('setKey', 'Open_300sentences');
    }""")
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=304, completed=False)
    await start_session(page)
    await record(page)
    s = await state(page)
    pr = s['prompt'] or {}
    c.check(pr.get('detail') == 'Next: the Rainbow Passage, 6 sentences.' and s['main'] == 'Continue',
            'the 300-sentence set ends with the Rainbow Passage too', pr)
    await press(page, 'Space')   # Continue
    await wait_for(page, "() => V2S.session.getState() === 'ready' && V2S.session.getContext().setKey === 'rainbow'")
    s = await state(page)
    c.check(s['where'] == 'Rainbow Passage · 1 of 6', "its own passage, from sentence 1 (the 350 set's earlier one does not count)", s['where'])
    await record(page)
    meta = await page.evaluate(LAST_META_JS)
    c.check(meta['sentenceSet'] == 'rainbow' and meta['rainbowAfterSet'] == 'Open_300sentences',
            'the sidecar says which set the passage followed', (meta['sentenceSet'], meta.get('rainbowAfterSet')))
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def check_from_settings(page):
    """Settings → Camera and microphone → Record a new test, then Yes. Opened from Settings, the
    check comes back at the step it was left on."""
    await open_settings(page, 'Camera and microphone')
    await page.locator('#settingsPanel button', has_text='Record a new test').click()
    await page.wait_for_selector('#screen-check:not([hidden])', timeout=15000)
    await wait_for(page, "() => V2S.media.getStream() && !(document.getElementById('checkStepCamera').hidden && document.getElementById('checkStepMic').hidden)")
    if await page.is_visible('#checkStepCamera'):
        await click(page, '#checkNext')
    await wait_for(page, "() => !document.getElementById('testRecord').hidden && !document.getElementById('checkStepMic').hidden")
    await click(page, '#testRecord')
    await wait_for(page, "() => !document.getElementById('testAsk').hidden || !document.getElementById('testError').hidden", timeout=20000)
    await click(page, '#testYes')


async def s_rainbow_edges(pw, base):
    c = Checks('Rainbow Passage edges: a double press starts one passage; left on its Finish; a test from Settings; sentence 350 not stored')
    # Continue on sentence 350 pressed twice: one passage, at its first sentence.
    browser, _, page, errors = await boot(pw, base, index=354, init_scripts=[NO_PICKERS])
    await record(page)
    await ready_for_press(page)
    await page.keyboard.press('Space')
    await page.wait_for_timeout(120)
    await page.keyboard.press('Space')   # a double press
    await wait_for(page, "() => V2S.session.getState() === 'ready' && V2S.session.getContext().setKey === 'rainbow'")
    await page.wait_for_timeout(600)
    s = await state(page)
    same = await page.evaluate("V2S.app.state().rainbow.progress === V2S.session.getContext().progress")
    c.check(s['where'] == 'Rainbow Passage · 1 of 6' and s['state'] == 'ready' and same,
            'a double press on Continue: one passage, waiting at its first sentence', s['where'])
    # A new microphone test from Settings during the passage: back to the same sentence.
    await record(page)
    await check_from_settings(page)
    await page.wait_for_selector('#screen-record:not([hidden])', timeout=10000)
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    s = await state(page)
    c.check(s['where'] == 'Rainbow Passage · 2 of 6', 'a test from Settings during the passage: back to its sentence 2', s['where'])
    # Left on the passage's Finish (End for today, a reload): it is done, never read again.
    for _ in range(5):
        await record(page)
    c.check((await state(page))['main'] == 'Finish', "the passage's last sentence, Finish showing")
    await end_for_today(page)
    await page.evaluate('V2S.session.flush()')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    answer = await page.evaluate("V2S.app.state().progress.rainbow")
    takes = await page.evaluate("""async () => { const ids = await V2S.storage.takeIds(); let n = 0;
      for (const id of ids) { const r = await V2S.storage.getTake(id); if (r && r.sentenceSet === 'rainbow') n++; } return n; }""")
    c.check(await page.text_content('#welcomeTitle') == 'All sentences done' and answer == 'done' and takes == 6,
            'left on its Finish: all done next time, not read again (6 passage takes)', (answer, takes))
    c.check(not errors, 'no page errors', errors)
    await browser.close()

    # Sentence 350 could not be stored after all (its write, late, fails): no passage yet; it
    # is recorded again first.
    browser, _, page, errors = await boot(pw, base, index=354, init_scripts=[FAIL_COMMIT, NO_PICKERS])
    await page.evaluate('window.__failDelayMs = 2500; window.__failCommits = 1')
    await record(page)
    await press(page, 'Space')   # Continue, while the write is still under way
    await wait_for(page, "() => V2S.session.getState() === 'ready'", timeout=15000)
    await page.wait_for_timeout(3000)
    s = await state(page)
    key = await page.evaluate("V2S.session.getContext().setKey")
    c.check(key != 'rainbow' and s['index'] == 354 and 'could not be stored' in (s['message'] or ''),
            'its last take not stored: back to sentence 350 (no passage yet)', (key, s['index'], s['message']))
    await record(page)
    await press(page, 'Space')   # Continue
    await wait_for(page, "() => V2S.session.getState() === 'ready' && V2S.session.getContext().setKey === 'rainbow'", timeout=15000)
    c.check(True, 'recorded again: then the passage')
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_card_room(pw, base):
    c = Checks('The card keeps its top (Recording) and bottom (the longest message) free: no sentence of any set reaches them')
    shapes = [(375, 553), (320, 568), (360, 640), (390, 664), (667, 330), (750, 340), (820, 1180), (1440, 900)]
    for set_key in [None, 'oct16-openVocab-350']:   # the default set (and the passage); the set with the longest sentences
        for w, h in shapes:
            mobile = w < 1000
            browser, _, page, errors = await boot(pw, base, index=100, init_scripts=[NO_PICKERS], viewport={'width': w, 'height': h},
                                                  has_touch=mobile, is_mobile=mobile, set_key=set_key)
            r = await page.evaluate(CARD_ROOM_JS)
            label = set_key or 'main'
            for name in ('main', 'rainbow'):
                x = r[name]
                c.check(not x['hits'], f'{w}×{h} {label if name == "main" else name}: {x["fit"]}, every sentence clear of the Recording sign and the longest message', x['hits'][:2])
            breaks = await page.evaluate(PHRASE_BREAKS_JS)   # fitted to the passage last
            c.check(not breaks['bad'], f'{w}×{h}: the passage\'s lines end only between its phrases ({breaks["lines"]} lines)', breaks['bad'][:3])
            c.check(not errors, f'{w}×{h}: no page errors', errors)
            await browser.close()
    # The practice: the coach speaks below the card, which shows no message then; the
    # sentence is in the middle of the card, clear of the Recording sign (on a short card
    # it starts just below the sign).
    for w, h in [(375, 553), (390, 844), (667, 330)]:
        browser, _, page, errors = await boot(pw, base, trained=False, init_scripts=[NO_PICKERS], viewport={'width': w, 'height': h},
                                              has_touch=True, is_mobile=True)
        await page.wait_for_timeout(400)
        r = await page.evaluate(PRACTICE_ROOM_JS)
        c.check(r['coaching'] and r['clear'] and abs(r['offset']) < 0.05,
                f'{w}×{h} practice: {r["fit"]}, the sentence near the middle of the card, clear of the Recording sign', r)
        c.check(not errors, f'{w}×{h} practice: no page errors', errors)
        await browser.close()
    return c.done()


async def enter_id(page, participant):
    """On Set up (already showing): type the ID and confirm it."""
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.fill('#setupId', participant)
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')


NEW_PARTICIPANT_STATE = """async () => ({ id: await V2S.storage.getSetting('participantId', null), pending: await V2S.app.pendingCount(),
  theme: document.documentElement.dataset.theme, hold: V2S.input.getHoldMs(), field: document.getElementById('setupId').value })"""


async def s_new_participant(pw, base):
    c = Checks('Settings → New participant: everything saved first, then Set up; the previous participant comes back where they were, with their own settings')
    browser, _, page, errors = await boot(pw, base, index=7, init_scripts=[NO_PICKERS])
    downloads = track_downloads(page)
    await record(page)
    await record(page)
    # This participant's own settings: dark, and a held press counts only after 2 s.
    await open_settings(page)
    await page.locator('#settingsPanel .segmented button', has_text='Dark').click()
    await page.wait_for_timeout(300)
    await click(page, '#settingsClose')
    await open_settings(page)
    await page.select_option('#setHold', '2000')
    await page.wait_for_timeout(300)
    await click(page, '#settingsClose')
    await page.wait_for_timeout(500)
    # New participant, with two recordings not saved yet: they are saved first.
    await open_settings(page)
    c.check(await page.is_visible('#newParticipant') and (await page.text_content('#newParticipant')).strip() == 'New participant…',
            'Settings: "New participant…" on its first page, under the participant')
    await page.locator('#newParticipant').click()
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    title = await page.text_content('#dialogTitle')
    body = await page.text_content('#dialogBody')
    c.check(title == 'New participant?' and '2 recordings not saved yet' in body, 'it asks first, and says the 2 recordings are saved first', body)
    async with page.expect_download():
        await confirm_dialog(page, 'Save and continue')
    await wait_for(page, '() => V2S.ui.isDialogOpen()', timeout=20000)   # Did the file save?
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Yes, I see it').click()
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    st = await page.evaluate(NEW_PARTICIPANT_STATE)
    c.check(st['id'] is None and st['pending'] == 0 and st['field'] == '' and len(downloads) == 1,
            'saved first (one ZIP, confirmed), then Set up with an empty ID', st)
    c.check(st['theme'] == 'light' and st['hold'] == 1000, 'the next participant starts with the default settings (light, 1 s)', st)
    await enter_id(page, 'P018')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    fresh = await page.evaluate("() => V2S.app.state().progress.currentIndex")
    c.check(await page.text_content('#welcomeTitle') == 'Welcome' and fresh == 0, 'P018: a first visit, from the very beginning', fresh)
    # P017 again: nothing to save, then their ID: on where they left off, with their settings.
    await open_settings(page)
    await page.locator('#newParticipant').click()
    await confirm_dialog(page, 'New participant')
    await enter_id(page, 'P017')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    back = await page.evaluate("() => ({ index: V2S.app.state().progress.currentIndex, theme: document.documentElement.dataset.theme, hold: V2S.input.getHoldMs() })")
    c.check(await page.text_content('#welcomeTitle') == 'Welcome back' and back == {'index': 9, 'theme': 'dark', 'hold': 2000},
            'P017 again: where they left off, with their own settings (dark, 2 s)', back)
    kept = await page.evaluate("async () => (await V2S.storage.takeIds()).length")
    c.check(kept >= 2, "P017's recordings are still on this device (saved, kept as a backup)", kept)
    c.check(not errors, 'no page errors', errors)
    await browser.close()

    if ENGINE == 'chrome':
        # A folder: recordings are already in it; the next participant keeps the folder.
        browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST])
        await setup_participant(page, base, save='folder')
        await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=7, completed=False)
        await start_session(page)
        await record(page)
        await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
        await open_settings(page)
        await page.locator('#newParticipant').click()
        await confirm_dialog(page, 'New participant')
        await enter_id(page, 'P018')
        await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
        mode = await page.evaluate("V2S.exporter.getSaveMode()")
        c.check(mode == 'folder' and await page.is_hidden('#setupStepFolder'), 'a folder: the next participant keeps it (no folder question)', mode)
        c.check(not errors, 'no page errors', errors)
        await browser.close()
    return c.done()


# The first page of Settings, top to bottom: the parts in order, by their first words.
SETTINGS_HOME_JS = """() => [...document.querySelectorAll('#settingsBody > .group')].map(g => g.textContent.replace(/\\s+/g, ' ').trim().slice(0, 60))"""


async def s_settings_home(pw, base):
    c = Checks('Settings, first page: the participant and New participant first, then saving (with Save now), their own settings, the sentences, this device')
    browser, _, page, errors = await boot(pw, base, index=7, init_scripts=[NO_PICKERS])
    downloads = track_downloads(page)
    await record(page)
    await open_settings(page)
    groups = await page.evaluate(SETTINGS_HOME_JS)
    expect = ['ParticipantP017New participant…Switch participant…', 'Saving 1 recording is not saved yet', 'For P017 Appearance', 'Sentences & progress',
              'This device Camera and microphone', 'About', 'Sign out']
    order = [any(g.replace(' ', '').startswith(e.replace(' ', '')) for g in groups[i:i + 1]) for i, e in enumerate(expect)]
    c.check(len(groups) == len(expect) and all(order), 'in order: participant, saving, their own settings, sentences, this device, About, Sign out', groups)
    c.check(await page.is_visible('#mainSaveNow') and 'Held-press limit' in groups[2], 'not saved: the amber line and Save all recordings now, right there; held-press limit with the theme', groups[1:3])
    async with page.expect_download():
        await page.locator('#mainSaveNow').click()
    await confirm_dialog(page, 'Yes, I see it')
    await page.wait_for_selector('#settingsPanel:not([hidden])', timeout=10000)
    await wait_for(page, "() => document.getElementById('settingsTitle').textContent === 'Settings'")
    await page.wait_for_timeout(400)
    groups = await page.evaluate(SETTINGS_HOME_JS)
    c.check(groups[1].replace(' ', '').startswith('SavingAllrecordingsaresaved') and await page.is_hidden('#mainSaveNow') and len(downloads) == 1,
            'saved from the first page: back on it, all saved, no Save button', groups[1])
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


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
    c.check(s['index'] == 0 and s['prompt'] and s['prompt']['label'] == 'Step 1 · Start recording', 'a new participant starts with coached practice', s)
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
    await press(page, 'ArrowLeft')  # Redo sentence 2
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
    await press(page, 'ArrowLeft')
    await page.wait_for_timeout(400)
    await page.evaluate('V2S.session.flush()')
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await start_session(page)
    await press(page, 'ArrowLeft')  # Cancel redo
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 7 and s['redoLabel'] == 'Redo last sentence', 'Cancel redo after a reload: back where they were', s)
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
    c.check(s['index'] == 0 and s['where'] == 'Practice 1 of 5' and (s['prompt'] or {}).get('label') == 'Step 1 · Start recording', 'practice 1, coached', s)
    for _ in range(2):
        await record(page)
    s = await state(page)
    c.check(s['index'] == 2 and s['spot'] == 'redoButton', 'practice 3: the Redo lesson', s)
    await press(page, 'ArrowLeft')   # the lesson goes on only with Redo
    await page.wait_for_timeout(400)
    await record(page)
    c.check((await state(page))['index'] == 2, 'after the Redo, back on practice 3')
    for _ in range(3):
        await record(page)
    c.check((await state(page))['state'] == 'partEnd', 'practice 5 done: pause on the last practice sentence')
    await page.evaluate('V2S.session.flush()')
    stored = await page.evaluate("async () => (await V2S.storage.getProgress('P017::50words_350sentences')).currentIndex")
    c.check(stored == 25, 'the place to come back to is already stored (End for today here would keep it)', stored)
    await press(page, 'Space')
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    c.check(await page.text_content('#breakPrimary') == 'Save recordings', 'practice done (ZIP mode): save the practice recordings first')
    async with page.expect_download():
        await click(page, '#breakPrimary')
    await confirm_dialog(page, 'Yes, I see it')
    await page.wait_for_timeout(300)
    c.check(await page.text_content('#breakPrimary') == 'Continue', 'then Continue')
    await click(page, '#breakPrimary')
    await page.wait_for_selector('#screen-intro:not([hidden])')
    for _ in range(await page.evaluate("document.querySelectorAll('#introReview li').length")):
        await click(page, '#introStart')
        await page.wait_for_timeout(150)
    await page.wait_for_function("() => document.getElementById('introStart').textContent === 'Continue part 1'")
    c.check(True, 'how to record, then: Continue part 1 (they were in the middle of it)')
    await click(page, '#introStart')
    await wait_ready(page)
    s = await state(page)
    c.check(s['index'] == 25 and s['prompt'] is None, 'back on the sentence they were on, no guide', s)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_rounds(pw, base):
    c = Checks('Rounds: Redo after the last sentence stays in the round; recording again starts round 2')
    # The Rainbow Passage was read in an earlier round (it is read once ever).
    browser, _, page, errors = await boot(pw, base, index=354, init_scripts=[NO_PICKERS], progress={'rainbow': 'done'})
    await record(page)
    s = await state(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Finish', 'the very last sentence: pause with Finish', s)
    await page.evaluate('V2S.session.flush()')
    progress = await page.evaluate("V2S.storage.getProgress('50words_350sentences')")
    c.check(progress['completed'] and progress['repetitionCount'] == 1, 'legacy key: completed, repetitionCount 1 (as the earlier page)', progress)
    await press(page, 'ArrowLeft')  # Redo the last sentence
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
    await press(page, 'Space')  # Finish
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
    await press(page, 'Space')  # Finish part 1
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
    c.check(s['state'] == 'partEnd' and s['redoLabel'] == 'Redo last sentence' and 'When can I drink water' in (s['redo'] or ''), 'Redo offered for the last sentence', s)
    await press(page, 'ArrowLeft')
    await page.wait_for_timeout(400)
    s = await state(page)
    c.check(s['index'] == 54 and s['redoLabel'] == 'Cancel redo', 'redoing sentence 50 of part 1', s)
    await record(page)
    s = await state(page)
    t = await takes(page)
    c.check(s['state'] == 'partEnd' and s['main'] == 'Go to break', 'then the pause again, Go to break', s)
    c.check([x['status'] for x in t] == ['superseded', 'accepted'], 'the first take of it is superseded', t)
    await press(page, 'Space')
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
    usable = [n for n in names if n.endswith(('.mp4', '.webm')) and '/not_used/' not in n]
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
    # The camera health check runs on real time (12 s here); the clock threshold is
    # shortened from 20 s to 8 s.
    c = Checks('A long take (13 s): no false camera failure; the clock appears only on long takes')
    browser, _, page, errors = await boot(pw, base, index=5, init_scripts=["window.__V2S_TEST = { testRecordMs: 1200, resolution: '360p', timerAfterMs: 8000, " + CLASSIC + " };"])
    await press(page, 'Space')
    await wait_for(page, "() => V2S.session.getState() === 'recording'")
    await page.wait_for_timeout(6000)
    s = await state(page)
    c.check(s['state'] == 'recording' and s['timer'] == '', 'after 6 s: still recording, no clock yet', s)
    await page.wait_for_timeout(6500)
    s = await state(page)
    c.check(s['state'] == 'recording' and re.fullmatch(r'· 0:1[0-9]', s['timer'] or ''), 'after 12 s: still recording, the clock shows on Stop', s)
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
    # The open-vocabulary set has much longer sentences (up to 88 characters): the size stays
    # in the same range; every sentence fits the card, within the lines the layout allows.
    for name, viewport, kind in FIT_VIEWPORTS:
        browser, _, page, errors = await boot(pw, base, index=5, viewport=viewport, has_touch=kind != 'wide' and ENGINE != 'firefox',
                                              is_mobile=kind in ('phone', 'flat'), set_key='oct16-openVocab-350')
        r = await page.evaluate(FIT_JS)
        low, high, _ = FIT_RULES[kind]
        allowed = int(r['fit'].split(':')[2])
        c.check(r['fit'].startswith(kind) and low <= r['size'] <= high and r['worst'] <= min(allowed, 5) and r['cardFits'] and r['overflow'] <= 1,
                f'{name} (oct16-openVocab-350): size {r["size"]} px within {low}–{high}, at most {min(allowed, 5)} lines, inside the card', r)
        c.check(kind == 'phone' or r['twoLines'] >= 0.95, f'{name} (oct16-openVocab-350): {r["twoLines"]:.0%} on at most two lines (phones excepted)', r)
        c.check(not errors, f'{name} (oct16-openVocab-350): no page errors', errors)
        await browser.close()
    return c.done()



async def s_file_integrity(pw, base):
    c = Checks('Saved files are complete: each plays with picture and sound, the right length, its sidecar matches')
    import base64
    # Folder mode: the files exactly as written to the chosen folder.
    real = 'window.__V2S_TEST = { testRecordMs: 1200, ' + CLASSIC + ' };'   # the real picture size (1080p)
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[real])
    await setup_participant(page, base, save='folder')
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=5)
    await start_session(page)
    for ms in (1600, 2600, 1200):
        await record(page, ms=ms)
    await press(page, 'ArrowLeft')   # Redo the last one: the first version moves to not_used/
    await page.wait_for_timeout(400)
    await record(page, ms=1600)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    videos = [f for f in files if f.endswith(('.mp4', '.webm'))]
    usable = [f for f in videos if '/not_used/' not in f]
    unused = [f for f in videos if '/not_used/' in f]
    c.check(len(usable) == 3 and len(unused) == 1, '3 usable recordings and the replaced one in not_used/', files)
    c.check(all(re.match(r'P017/session-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}/', f) for f in videos), 'all inside this session\'s folder', videos)
    c.check(any(f.rsplit('.', 1)[0].endswith('_redo') for f in usable), 'the new version ends with _redo', usable)
    tmp = tempfile.mkdtemp()
    for f in videos:
        local = os.path.join(tmp, f.replace('/', '__'))
        with open(local, 'wb') as handle:
            handle.write(base64.b64decode(await page.evaluate(READ_OPFS_B64, ['picked', f])))
        problems, info = await asyncio.to_thread(probe_media, local)
        name = f.rsplit('/', 1)[-1]
        c.check(not problems, f'plays with picture and sound: {name}', f'{problems} {info}')
        c.check(info.get('duration') is not None and 0.8 < info['duration'] < 6, f'length fits the take: {name}', info.get('duration'))
        meta = await page.evaluate(READ_OPFS_JSON, ['picked', f.rsplit('.', 1)[0] + '.json'])
        size = os.path.getsize(local)
        c.check(meta.get('fileName') == name and meta.get('participantId') == 'P017' and meta.get('size') in (None, size),
                f'sidecar names this file, the participant and its size: {name}', {k: meta.get(k) for k in ('fileName', 'participantId', 'size', 'status')})
        status = meta.get('status')
        c.check(status == ('superseded' if '/not_used/' in f else 'accepted'), f'sidecar status: {name}', status)
    await browser.close()

    # ZIP mode: the files inside a saved part.
    browser, _, page, errors2 = await boot(pw, base, fsa=True, index=5 + 48, init_scripts=[real])
    await record(page, ms=1600)
    await record(page, ms=2000)
    await press(page, 'Space')   # Go to break
    await page.wait_for_selector('#screen-break:not([hidden])')
    await wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    await click(page, '#breakPrimary')
    await wait_for(page, "() => /Continue to part 2/.test(document.getElementById('breakPrimary').textContent)", timeout=30000)
    zips = await page.evaluate(LIST_OPFS_JS, 'saved-zips')
    c.check(len(zips) == 1, 'one ZIP for the part', zips)
    path = os.path.join(tmp, 'part.zip')
    with open(path, 'wb') as handle:
        handle.write(base64.b64decode(await page.evaluate(READ_OPFS_B64, ['saved-zips', zips[0]])))
    with zipfile.ZipFile(path) as archive:
        c.check(archive.testzip() is None, 'the ZIP is not damaged (every entry checks)')
        names = archive.namelist()
        manifest = json.loads(archive.read('manifest.json'))
        archive.extractall(os.path.join(tmp, 'zip'))
    vids = [n for n in names if n.endswith(('.mp4', '.webm'))]
    c.check(len(vids) == 2 and manifest.get('recordCount') == 2, 'both recordings and the manifest', names)
    for n in vids:
        problems, info = await asyncio.to_thread(probe_media, os.path.join(tmp, 'zip', n))
        c.check(not problems and info.get('duration') and 0.8 < info['duration'] < 6, f'plays with picture and sound: {n.rsplit("/", 1)[-1]}', f'{problems} {info}')
        c.check(n.rsplit('.', 1)[0] + '.json' in names, f'its sidecar is in the ZIP: {n.rsplit("/", 1)[-1]}')
    c.check(not errors and not errors2, 'no page errors', errors + errors2)
    await browser.close()
    return c.done()

async def s_rotation(pw, base):
    c = Checks('v3 / v3.1 / v3.3 (10,000 sentences): the ID decides where after the shared 350 each participant goes on; files name the set\'s line')
    for set_key, set_file in (('open-vocab-v3', 'open-vocab-v3-10000.txt'), ('open-vocab-v3.1', 'open-vocab-v3.1-10000.txt'), ('open-vocab-v3.3', 'open-vocab-v3.3-10000.txt')):
        await rotation_checks(pw, base, c, set_key, set_file)
    return c.done()


async def rotation_checks(pw, base, c, set_key, set_file):
    browser, _, page, errors = await launch(pw, audio='speech', init_scripts=[FAST, NO_PICKERS], engine=ENGINE)
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.evaluate("key => V2S.storage.setSetting('setKey', key)", set_key)
    await page.reload()
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await page.fill('#setupId', 'P01')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupError:not([hidden])')
    c.check('SEMG1' in (await page.text_content('#setupError')), f'{set_key}: an ID without the number (P01): asked for one like SEMG1', await page.text_content('#setupError'))
    await page.fill('#setupId', 'semg2')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await click(page, '#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=20000)
    file_lines = (await page.evaluate("f => fetch('newset/' + f).then(r => r.text())", set_file)).rstrip('\n').split('\n')
    m = await page.evaluate("""() => { const a = V2S.app.state(); const m = a.material;
      return { start: m.startPart, kept: a.progress.startPart, n: m.formalCount, w: m.warmupCount, first: m.all[m.warmupCount],
               s350: m.all[m.warmupCount + 349], s351: m.all[m.warmupCount + 350], last: m.all[m.all.length - 1],
               l351: m.lines[350], lLast: m.lines[m.lines.length - 1], uniq: new Set(m.lines).size }; }""")
    c.check(m['start'] == 21 and m['kept'] == 21, f'{set_key}: SEMG2 goes on from part 21 after the shared parts; kept with the progress', (m['start'], m['kept']))
    c.check(m['n'] == 10000 and m['uniq'] == 10000, f'{set_key}: all 10,000 sentences, each once', (m['n'], m['uniq']))
    c.check(m['first'] == file_lines[0] and m['s350'] == file_lines[349], f'{set_key}: the shared 350 first, in their own order')
    c.check(m['s351'] == file_lines[1000] and m['l351'] == 1001, f'{set_key}: then part 21 (line 1,001)', (m['s351'], m['l351']))
    c.check(m['lLast'] == 1000 and m['last'] == file_lines[999], f'{set_key}: round the rest: part 20 last (line 1,000)', m['lLast'])
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=m['w'] + 350, completed=False)
    await start_session(page)
    s = await state(page)
    c.check(s['sentence'].replace('\xa0', ' ') == file_lines[1000], f'{set_key}: the first sentence after the shared 350 is line 1,001', s['sentence'])
    await record(page)
    meta = await page.evaluate("""async () => { await V2S.session.flush(); const out = [];
      await V2S.storage.forEachTake(r => out.push({ f: r.fileName, line: r.metadata.materialLine, start: r.metadata.rotationStartPart, pos: r.metadata.position }));
      return out; }""")
    c.check(len(meta) == 1 and '_1001-10000_' in meta[0]['f'] and meta[0]['line'] == 1001 and meta[0]['start'] == 21 and meta[0]['pos'] == 351,
            'its file is named by line 1,001 of 10,000; the sidecar has the line, the start part and the reading position', meta)
    c.check(not errors, f'{set_key}: no page errors', errors)
    await browser.close()


async def s_set_check(pw, base):
    c = Checks('As the page really is (owner, 2026-10-21): open-vocab-v3.3 by default; before every session, "Is this the right sentence set?"')
    browser, _, page, errors = await launch(pw, audio='speech', init_scripts=["window.__V2S_TEST = { testRecordMs: 1200, resolution: '360p' };", NO_PICKERS], engine=ENGINE)
    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    c.check(await page.evaluate("V2S.app.state().setKey") == 'open-vocab-v3.3', 'a new device uses open-vocab-v3.3')
    await page.fill('#setupId', 'P01')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupError:not([hidden])')
    c.check('SEMG' in (await page.text_content('#setupError')), 'it needs an ID like SEMG3', await page.text_content('#setupError'))
    await page.fill('#setupId', 'semg3')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await click(page, '#setupConfirmYes')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await click(page, '#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=20000)
    m = await page.evaluate("() => { const a = V2S.app.state(); return { id: a.participantId, start: a.material.startPart, n: a.material.formalCount }; }")
    c.check(m == {'id': 'SEMG3', 'start': 34, 'n': 10000}, 'SEMG3: all 10,000, going on from part 34 after the shared 350', m)
    file_lines = (await page.evaluate("fetch('newset/open-vocab-v3.3-10000.txt').then(r => r.text())")).rstrip('\n').split('\n')
    first = await page.evaluate("() => { const m = V2S.app.state().material; return [m.all[m.warmupCount], m.all[m.warmupCount + 350], m.lines[350]]; }")
    c.check(first == [file_lines[0], file_lines[1650], 1651], 'first the shared line 1, then line 1,651 (part 34)', first)

    # Begin: the question comes first, and the press that opened it cannot answer it.
    await click(page, '#welcomeStart')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    title = await page.text_content('#dialogTitle')
    body = await page.text_content('#dialogBody')
    c.check(title == 'Is this the right sentence set?', 'Begin asks about the sentence set', title)
    c.check('open-vocab-v3.3' in body and 'SEMG3' in body and 'Practice' in body, 'it names the set, the participant and where they are', body)
    # Pressed at once (in the page, so a slow test machine cannot make it late).
    early = await page.evaluate("""() => { const armed = document.getElementById('dialog').dataset.armed || null;
      [...document.querySelectorAll('#dialogActions button')].find(b => b.textContent === 'Yes, start').click();
      return armed; }""")
    await page.wait_for_timeout(200)
    c.check(early is None and await page.evaluate('() => V2S.ui.isDialogOpen()') and await page.is_visible('#screen-welcome'), 'a press in its first second does nothing (a double press on Begin)', early)
    # Change sentence set: Settings, where the set is chosen; closing it leaves Welcome as it was.
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Change sentence set').click()
    await page.wait_for_selector('#settingsPanel:not([hidden])')
    c.check(await page.is_visible('#setSentenceSet') and await page.input_value('#setSentenceSet') == 'open-vocab-v3.3', 'Change sentence set opens Settings at the set', await page.input_value('#setSentenceSet') if await page.is_visible('#setSentenceSet') else None)
    await page.click('#settingsClose')
    await page.wait_for_selector('#settingsPanel', state='hidden')
    c.check(await page.is_visible('#screen-welcome'), 'closing Settings: back on Welcome, nothing started')
    # Esc: stays on Welcome.
    await click(page, '#welcomeStart')
    await dialog_ready(page)
    await page.keyboard.press('Escape')
    await page.wait_for_timeout(300)
    c.check(not await page.evaluate('() => V2S.ui.isDialogOpen()') and await page.is_visible('#screen-welcome'), 'Esc: no session, still on Welcome')
    # Yes, start: on to the camera and microphone check.
    await click(page, '#welcomeStart')
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Yes, start').click()
    await page.wait_for_selector('#screen-check:not([hidden])', timeout=10000)
    c.check(True, 'Yes, start goes on to the check')

    # A device that chose another set earlier keeps it, and the question shows which.
    await page.evaluate("V2S.storage.setSetting('setKey', 'open-vocab-v3.1')")
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=20000)
    await click(page, '#welcomeStart')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    body = await page.text_content('#dialogBody')
    c.check('open-vocab-v3.1' in body, 'a device that chose open-vocab-v3.1 is asked about open-vocab-v3.1', body)
    await dialog_ready(page)
    await page.locator('#dialogActions button', has_text='Change sentence set').click()
    await page.wait_for_selector('#settingsPanel:not([hidden])')
    await page.select_option('#setSentenceSet', 'open-vocab-v3.3')
    await confirm_dialog(page, 'Yes, continue')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=10000)
    await click(page, '#welcomeStart')
    await wait_for(page, '() => V2S.ui.isDialogOpen()')
    body = await page.text_content('#dialogBody')
    c.check('open-vocab-v3.3' in body, 'switched there: the next question names open-vocab-v3.3', body)
    c.check(not errors, 'no page errors', errors)
    await browser.close()
    return c.done()


async def s_daily(pw, base):
    c = Checks('open-vocab-v3.3, 7 parts a day (owner, 2026-10-21): today counts from Part 1 of 7; then "All 7 parts for today are done", one more part at a time; the next day Part 1 of 7 again, the sentences going on')
    browser, _, page, errors = await launch(pw, audio='speech', fsa=True, init_scripts=[FAST], engine=ENGINE)
    await setup_participant(page, base, participant='SEMG3', save='folder')
    await page.evaluate("V2S.storage.setSetting('setKey', 'open-vocab-v3.3')")
    await page.reload()
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=20000)
    file_lines = (await page.evaluate("fetch('newset/open-vocab-v3.3-10000.txt').then(r => r.text())")).rstrip('\n').split('\n')
    w = await page.evaluate('V2S.app.state().material.warmupCount')
    today = await page.evaluate('V2S.sentences.today()')
    welcome = "() => ({ part: document.getElementById('welcomePart').textContent, count: document.getElementById('welcomeCount').textContent, start: document.getElementById('welcomeStart').textContent, lead: document.getElementById('welcomeLead').textContent })"

    async def reload_welcome():
        await page.reload()
        await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=20000)
        return await page.evaluate(welcome)

    # Today began at part 1; the last sentence of part 7 is next.
    await set_progress(page, howtoSeen=True, coachDone=True, currentIndex=w + 6 * 50 + 49, completed=False, day={'date': today, 'startPart': 1})
    v = await reload_welcome()
    c.check(v['part'] == 'Part 7 of 7' and v['count'] == 'Sentence 50 of 50', 'Welcome: Part 7 of 7, sentence 50 (never 200 or 10,000)', v)
    await start_session(page)
    s = await state(page)
    c.check(s['where'] == 'Part 7 of 7 · Sentence 50 of 50', 'recording: Part 7 of 7 · Sentence 50 of 50', s['where'])
    await record(page)
    await press(page, 'Space')   # to the break
    await wait_for(page, "() => document.getElementById('breakPrimary').textContent === 'Read one more part'", timeout=20000)
    b = await page.evaluate("() => ({ title: breakTitle.textContent, lead: breakLead.textContent, second: breakSecondary.hidden ? null : breakSecondary.textContent })")
    c.check(b['title'] == 'All 7 parts for today are done' and b['second'] == 'End for today' and 'You can stop here' in b['lead'],
            'after part 7: "All 7 parts for today are done", Read one more part or End for today', b)
    await click(page, '#breakPrimary')
    await wait_for(page, "() => V2S.session.getState() === 'ready'")
    s = await state(page)
    c.check(s['where'] == 'Part 8 · Sentence 1 of 50', 'Read one more part: Part 8, no total', s['where'])
    c.check(s['sentence'].replace('\xa0', ' ') == file_lines[1650], 'SEMG3: after the shared 350 comes line 1,651 (part 34 of the file)', s['sentence'])
    await end_for_today(page)
    v = await reload_welcome()
    c.check(v['part'] == 'All 7 parts for today are done' and v['start'] == 'Read one more part', 'the same day, Welcome: today is done; one more part if they want', v)

    # The next day: Part 1 of 7 again, at the same sentence.
    await set_progress(page, day={'date': '2000-01-01', 'startPart': 1})
    v = await reload_welcome()
    c.check(v['part'] == 'Part 1 of 7' and v['start'] == 'Continue', 'the next day: Part 1 of 7, Continue', v)
    await start_session(page)
    s = await state(page)
    c.check(s['where'] == 'Part 1 of 7 · Sentence 1 of 50' and s['sentence'].replace('\xa0', ' ') == file_lines[1650], 'the next day starts where the last one stopped (line 1,651)', (s['where'], s['sentence']))
    await record(page)
    await page.evaluate('V2S.session.flush().then(() => V2S.exporter.flushFolderWrites())')
    files = await page.evaluate(LIST_OPFS_JS, 'picked')
    side = [f for f in files if '_1651-10000_' in f and f.endswith('.json')]
    m = await page.evaluate(READ_OPFS_JSON, ['picked', side[0]]) if side else {}
    meta = {'f': side[0] if side else None, 'line': m.get('materialLine'), 'block': m.get('blockIndex'), 'dayPart': m.get('dayPart'), 'dayDate': m.get('dayDate')}
    c.check(meta['f'] and meta['line'] == 1651 and meta['block'] == 8 and meta['dayPart'] == 1 and meta['dayDate'] == today,
            "the file and sidecar keep the real place (line 1,651, part 8 in reading order) and today's part", meta)
    # Stopped in the middle: the same day comes back to that sentence, still today's Part 1.
    await end_for_today(page)
    v = await reload_welcome()
    c.check(v['part'] == 'Part 1 of 7' and v['count'] == 'Sentence 2 of 50', 'stopped mid-part: back at sentence 2 of today\'s Part 1', v)
    # And on another day in the middle of a part: Part 1 of 7 · Sentence 2 of 50.
    await set_progress(page, day={'date': '2000-01-02', 'startPart': 3})
    v = await reload_welcome()
    c.check(v['part'] == 'Part 1 of 7' and v['count'] == 'Sentence 2 of 50', 'a new day in the middle of a part: Part 1 of 7 at sentence 2', v)
    c.check(await page.evaluate("V2S.sentences.hasRainbow('open-vocab-v3.3')") is False, 'no Rainbow Passage with this set')
    c.check(not errors, 'no page errors', errors)
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
    'rainbow': s_rainbow,
    'rainbow_zip': s_rainbow_zip,
    'rainbow_edges': s_rainbow_edges,
    'new_participant': s_new_participant,
    'settings_home': s_settings_home,
    'card_room': s_card_room,
    'zip_backups': s_zip_backups,
    'part_end_redo': s_part_end_redo,
    'two_tabs': s_two_tabs,
    'long_take': s_long_take,
    'store_failure': s_store_failure,
    'timeout': s_timeout,
    'file_integrity': s_file_integrity,
    'rotation': s_rotation,
    'set_check': s_set_check,
    'daily': s_daily,
}

# Scenarios that make sense in every engine (no Chrome-only file dialogs, flags or sample rates).
CROSS_ENGINE = ['first_run', 'normal', 'hold', 'no_speech', 'redo', 'speech_before_start', 'tail', 'recorder_retry',
                'bluetooth', 'mic_test_silent', 'help', 'double_tap', 'held_keys', 'save_keys', 'camera_denied', 'card_stable', 'device', 'reload', 'break_zip', 'legacy', 'storage_full',
                'finish_settings', 'signin', 'keyboard', 'clicker', 'too_loud', 'set_switch', 'no_audio', 'fit', 'settings_parity', 'settings_fit', 'redo_reload',
                'practice_again', 'rounds', 'zip_backups', 'part_end_redo', 'two_tabs', 'long_take', 'store_failure',
                'store_failure_late', 'stale_backups', 'rainbow_zip', 'card_room', 'new_participant', 'rotation', 'set_check']


async def main(names, jobs):
    """Runs the scenarios `jobs` at a time (each in its own browser), printing each one's
    lines together when it ends, then the failures again at the end."""
    started = time.time()
    gate = asyncio.Semaphore(jobs)
    failed = []

    async def one(name, pw, base):
        async with gate:
            lines = []
            SCENARIO_LINES.set(lines)
            t0 = time.time()
            try:
                # No scenario may hang the run: each has a few minutes at most.
                ok = await asyncio.wait_for(SCENARIOS[name](pw, base), SCENARIO_LIMIT_S)
            except asyncio.TimeoutError:
                say(f'  [FAIL] scenario {name} took over {SCENARIO_LIMIT_S} s (stuck)')
                ok = False
            except Exception as error:  # report and keep going
                say(f'  [FAIL] scenario {name} crashed: {error!r}')
                ok = False
            lines.append(f'   ({name}: {time.time() - t0:.0f} s)')
            print('\n'.join(lines), flush=True)
            if not ok:
                failed.append((name, [line for line in lines if '[FAIL]' in line]))
            return ok

    # Scenarios that judge the recorded files run alone afterwards: with several browsers
    # encoding at once, a starved encoder drops frames that a real session would not.
    alone = [name for name in names if name in RUN_ALONE]
    together = [name for name in names if name not in RUN_ALONE]
    with static_server() as base:
        async with async_playwright() as pw:
            results = await asyncio.gather(*(one(name, pw, base) for name in together))
            for name in alone:
                results.append(await one(name, pw, base))
    ok = all(results)
    if failed:
        print('\nFailures:')
        for name, lines in failed:
            print(f'  {name}:')
            for line in lines:
                print('  ' + line[:300])
    print(f'\n[{ENGINE}] ' + ('ALL PASSED' if ok else f'{len(failed)} of {len(names)} scenarios FAILED') + f'  ({time.time() - started:.0f} s, {jobs} at a time)')
    return ok


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['chrome', 'webkit', 'firefox'], default='chrome')
    parser.add_argument('scenarios', nargs='*')
    parser.add_argument('-j', '--jobs', type=int, default=4, help='scenarios run at the same time (1 = one by one)')
    args = parser.parse_args()
    ENGINE = args.engine
    default = list(SCENARIOS) if ENGINE == 'chrome' else CROSS_ENGINE
    sys.exit(0 if asyncio.run(main(args.scenarios or default, args.jobs)) else 1)
