"""Shared helpers for the browser scenario tests.

Runs the site from a local static server and drives the installed Google Chrome
through Playwright with fake camera/microphone input (a generated WAV file).
"""
import contextlib
import math
import os
import random
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
import wave

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAMPLE_RATE = 48000
MEDIA_DIR = os.path.join(tempfile.gettempdir(), 'v2s_e2e_media')


def _write_wav(path, seconds, sample_fn):
    random.seed(0)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for i in range(int(seconds * SAMPLE_RATE)):
            v = max(-1.0, min(1.0, sample_fn(i / SAMPLE_RATE)))
            frames += struct.pack('<h', int(v * 32767))
        w.writeframes(bytes(frames))


def _speech(t):
    """1.2 s of voiced, syllable-shaped sound then 0.8 s of near silence, repeating."""
    cyc = t % 2.0
    if cyc < 1.2:
        env = 0.5 * (1 - math.cos(2 * math.pi * (cyc / 0.3)))
        return 0.12 * env * (math.sin(2 * math.pi * 180 * t) + 0.5 * math.sin(2 * math.pi * 360 * t)) \
            + 0.01 * (random.random() - 0.5)
    return 0.002 * (random.random() - 0.5)


def _fan(t):
    """Steady broadband noise (a fan / air conditioner): loud enough to pass level checks, no speech."""
    return 0.035 * (random.random() - 0.5)


def _quiet(t):
    return 0.003 * (random.random() - 0.5)


def _loud(t):
    return 1.0 if math.sin(2 * math.pi * 220 * t) >= 0 else -1.0


def media_file(kind):
    """Path to a generated fake-microphone WAV: speech, fan, quiet or loud."""
    os.makedirs(MEDIA_DIR, exist_ok=True)
    path = os.path.join(MEDIA_DIR, f'{kind}.wav')
    if not os.path.exists(path):
        fn = {'speech': _speech, 'fan': _fan, 'quiet': _quiet, 'loud': _loud}[kind]
        _write_wav(path, 12, fn)
    return path


def _free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def static_server():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', REPO],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f'http://127.0.0.1:{port}'
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(base + '/version.json', timeout=1)
                break
            except Exception:
                time.sleep(0.1)
        yield base
    finally:
        proc.terminate()
        proc.wait(timeout=5)


async def launch(playwright, audio='speech', viewport=None, init_scripts=(), authed=True,
                 has_touch=False, is_mobile=False):
    """Returns (browser, context, page, errors)."""
    browser = await playwright.chromium.launch(channel='chrome', headless=True, args=[
        '--use-fake-device-for-media-stream',
        '--use-fake-ui-for-media-stream',
        '--autoplay-policy=no-user-gesture-required',
        '--use-file-for-fake-audio-capture=' + media_file(audio),
    ])
    context = await browser.new_context(
        viewport=viewport or {'width': 1440, 'height': 900},
        permissions=['camera', 'microphone'],
        accept_downloads=True,
        has_touch=has_touch,
        is_mobile=is_mobile,
    )
    if authed:
        await context.add_init_script("sessionStorage.setItem('v2s_auth_ok','1');")
    for script in init_scripts:
        await context.add_init_script(script)
    page = await context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    return browser, context, page, errors


class Checks:
    """Collects pass/fail lines and prints a summary."""

    def __init__(self, title):
        self.title = title
        self.failed = []
        self.count = 0
        print(f'\n== {title} ==')

    def check(self, ok, label, detail=''):
        self.count += 1
        mark = 'PASS' if ok else 'FAIL'
        print(f'  [{mark}] {label}' + (f'  ({detail})' if detail else ''))
        if not ok:
            self.failed.append(label)
        return ok

    def done(self):
        print(f'-- {self.title}: {self.count - len(self.failed)}/{self.count} passed')
        return not self.failed
