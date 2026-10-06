"""Browser-side test shims injected with add_init_script.

FSA_SHIM — the File System Access API with Chrome's real rules, backed by the
origin-private file system so tests can read back what was written:
  * showDirectoryPicker / showSaveFilePicker / requestPermission throw SecurityError
    unless called during a user activation (exactly like Chrome);
  * a folder picked in this page is writable; after a "new browser session"
    (sessionStorage __fsa_mode = 'prompt') queryPermission says 'prompt' until
    requestPermission is called during a click; mode 'deny' refuses permission;
  * writes without permission fail with NotAllowedError.
  Every call is logged in window.__fsaLog with whether a user activation was active.

MEDIA_SHIM — getUserMedia for engines without a fake capture device (WebKit, Firefox),
or when a test must control the sound precisely: a moving canvas as the camera and a
synthetic voice as the microphone. window.__v2sAudio.set(kind) switches the sound
('speech', 'continuous', 'silence', 'fan', 'loud') at any moment.
"""

FSA_SHIM = r"""
(() => {
  if (!window.FileSystemHandle || !navigator.storage || !navigator.storage.getDirectory) return;
  const MODE_KEY = '__fsa_mode';
  const PICK_KEY = '__fsa_pick';
  const mode = () => sessionStorage.getItem(MODE_KEY) || 'granted';
  const state = { granted: mode() === 'granted' };
  const savedFiles = new WeakSet();
  const isActive = () => (navigator.userActivation ? navigator.userActivation.isActive : true);
  window.__fsaLog = [];
  const log = event => window.__fsaLog.push({ event, active: isActive() });
  const gestureError = () => new DOMException('Must be handling a user gesture to show a file picker.', 'SecurityError');

  window.showDirectoryPicker = async function () {
    log('showDirectoryPicker');
    if (!isActive()) throw gestureError();
    const root = await navigator.storage.getDirectory();
    state.granted = true;
    sessionStorage.setItem(MODE_KEY, 'granted');
    return root.getDirectoryHandle(sessionStorage.getItem(PICK_KEY) || 'picked', { create: true });
  };

  window.showSaveFilePicker = async function (options) {
    log('showSaveFilePicker');
    if (!isActive()) throw gestureError();
    const root = await navigator.storage.getDirectory();
    const dir = await root.getDirectoryHandle('saved-zips', { create: true });
    const file = await dir.getFileHandle((options && options.suggestedName) || 'file.zip', { create: true });
    savedFiles.add(file);
    return file;
  };

  const proto = FileSystemHandle.prototype;
  proto.queryPermission = async function () {
    log('queryPermission');
    if (state.granted) return 'granted';
    return mode() === 'deny' ? 'denied' : 'prompt';
  };
  proto.requestPermission = async function () {
    log('requestPermission');
    if (!isActive()) throw new DOMException('User activation is required to request permissions.', 'SecurityError');
    if (mode() === 'deny') return 'denied';
    state.granted = true;
    sessionStorage.setItem(MODE_KEY, 'granted');
    return 'granted';
  };

  const notAllowed = () => Promise.reject(new DOMException('The request is not allowed by the user agent or the platform in the current context.', 'NotAllowedError'));
  const guard = (target, name, needsWrite) => {
    const original = target[name];
    target[name] = function (...args) {
      if (needsWrite.call(this, args) && !state.granted && !savedFiles.has(this)) return notAllowed();
      return original.apply(this, args);
    };
  };
  guard(FileSystemDirectoryHandle.prototype, 'getFileHandle', args => Boolean(args[1] && args[1].create));
  guard(FileSystemDirectoryHandle.prototype, 'getDirectoryHandle', args => Boolean(args[1] && args[1].create));
  guard(FileSystemFileHandle.prototype, 'createWritable', () => true);
})();
"""

# Tests must be silent on the machine running them: every AudioContext output goes through a
# zero gain, and media elements always play muted. (Chrome is also launched with --mute-audio.)
MUTE_SHIM = r"""
(() => {
  const AC = window.AudioContext || window.webkitAudioContext;
  if (AC) {
    const owner = [AC.prototype, window.BaseAudioContext && BaseAudioContext.prototype].find(p => p && Object.getOwnPropertyDescriptor(p, 'destination'));
    const real = owner && Object.getOwnPropertyDescriptor(owner, 'destination');
    if (real && real.get) {
      Object.defineProperty(AC.prototype, 'destination', {
        configurable: true,
        get() {
          if (!this.__silent) {
            this.__silent = this.createGain();
            this.__silent.gain.value = 0;
            this.__silent.connect(real.get.call(this));
          }
          return this.__silent;
        }
      });
    }
  }
  const play = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function (...args) {
    this.muted = true;
    this.volume = 0;
    return play.apply(this, args);
  };
})();
"""

MEDIA_SHIM = r"""
(() => {
  const AC = window.AudioContext || window.webkitAudioContext;
  let ctx = null;
  let gains = null;
  let kind = sessionStorage.getItem('__audio_kind') || 'speech';

  function buffer(seconds, fn) {
    const rate = ctx.sampleRate;
    const buf = ctx.createBuffer(1, Math.floor(seconds * rate), rate);
    const data = buf.getChannelData(0);
    let seed = 1;
    const random = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let i = 0; i < data.length; i++) data[i] = fn(i / rate, random);
    return buf;
  }

  const voiced = (t, random) => {
    const env = 0.5 * (1 - Math.cos(2 * Math.PI * ((t % 0.3) / 0.3)));
    return 0.12 * env * (Math.sin(2 * Math.PI * 180 * t) + 0.5 * Math.sin(2 * Math.PI * 360 * t)) + 0.01 * (random() - 0.5);
  };

  function source(buf) {
    const node = ctx.createBufferSource();
    node.buffer = buf;
    node.loop = true;
    return node;
  }

  function apply() {
    if (!gains) return;
    Object.entries(gains).forEach(([name, gain]) => { gain.gain.value = name === kind ? 1 : 0; });
  }

  window.__v2sAudio = { set(next) { kind = next; apply(); }, get: () => kind };

  // Engines only start audio during a user gesture (and the resume promise can stay
  // pending otherwise), so wake the synthetic voice on every press instead of waiting.
  const wake = () => { if (ctx && ctx.state !== 'running') ctx.resume().catch(() => {}); };
  ['pointerdown', 'keydown', 'click'].forEach(type => window.addEventListener(type, wake, true));

  async function build() {
    // sessionStorage __audio_rate imitates a low-rate (e.g. 16 kHz Bluetooth) microphone.
    const rate = Number(sessionStorage.getItem('__audio_rate')) || 0;
    if (!ctx) ctx = rate ? new AC({ sampleRate: rate }) : new AC();
    wake();
    const destination = ctx.createMediaStreamDestination();
    const generators = {
      speech: buffer(2, (t, r) => ((t % 2) < 1.2 ? voiced(t, r) : 0.002 * (r() - 0.5))),
      continuous: buffer(2, voiced),
      silence: buffer(1, (t, r) => 0.0015 * (r() - 0.5)),
      fan: buffer(1, (t, r) => 0.035 * (r() - 0.5)),
      loud: buffer(1, t => (Math.sin(2 * Math.PI * 220 * t) >= 0 ? 1 : -1))
    };
    gains = {};
    Object.entries(generators).forEach(([name, buf]) => {
      const gain = ctx.createGain();
      gain.gain.value = 0;
      const node = source(buf);
      node.connect(gain);
      gain.connect(destination);
      node.start();
      gains[name] = gain;
    });
    apply();

    // window.__V2S_PORTRAIT: an upright camera (9:16), as a phone or tablet held upright gives.
    const portrait = Boolean(window.__V2S_PORTRAIT);
    const W = portrait ? 360 : 640;
    const H = portrait ? 640 : 360;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const g = canvas.getContext('2d');
    let frame = 0;
    const draw = () => {
      frame += 1;
      g.fillStyle = `hsl(${(frame * 2) % 360}, 35%, 35%)`;
      g.fillRect(0, 0, W, H);
      g.fillStyle = '#f2e9dc';
      g.beginPath();
      g.ellipse(W / 2 + 40 * Math.sin(frame / 25), H * 0.47, portrait ? 110 : 95, portrait ? 145 : 125, 0, 0, Math.PI * 2);
      g.fill();
    };
    draw();
    setInterval(draw, 33);
    const videoTrack = canvas.captureStream(30).getVideoTracks()[0];
    return new MediaStream([videoTrack, destination.stream.getAudioTracks()[0]]);
  }

  const fake = async () => build();
  if (window.MediaDevices && MediaDevices.prototype) {
    Object.defineProperty(MediaDevices.prototype, 'getUserMedia', { value: fake, configurable: true, writable: true });
  }
  if (navigator.mediaDevices) {
    Object.defineProperty(navigator.mediaDevices, 'getUserMedia', { value: fake, configurable: true, writable: true });
  }
})();
"""
