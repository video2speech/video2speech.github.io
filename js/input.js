// One place for every press on the recording screen. Three rules only:
//   1. keyboard auto-repeat is ignored;
//   2. a key or touch held for HOLD_MS triggers the hold handler (the session then
//      throws the take away and restarts the same sentence);
//   3. presses closer together than DEBOUNCE_MS are ignored.
// Presses act immediately on key-down / pointer-down, never on release.
window.V2S = window.V2S || {};

V2S.input = (() => {
  const cfg = V2S.config;
  const { logEvent } = V2S.util;
  const PRIMARY_KEYS = new Set([' ', 'Spacebar', 'Enter', 'ArrowRight', 'PageDown']);
  const SECONDARY_KEYS = new Set(['ArrowLeft', 'PageUp']);

  let handlers = { primary: null, secondary: null, hold: null };
  let enabled = false;
  let press = null;
  let lastPressAt = -Infinity;
  let pointerDown = false;
  let lastPointerUpAt = -Infinity;
  let releaseWaiters = [];

  function configure(next) {
    handlers = { ...handlers, ...next };
  }

  function setEnabled(value) {
    enabled = Boolean(value);
    if (!enabled) cancelPress();
  }

  function keyKind(event) {
    if (event.code === 'Space' || PRIMARY_KEYS.has(event.key)) return 'primary';
    if (SECONDARY_KEYS.has(event.key)) return 'secondary';
    return null;
  }

  function isEditable(target) {
    return Boolean(target && target.closest && target.closest('input, textarea, select, [contenteditable="true"], [contenteditable=""]'));
  }

  function blocked() {
    return !enabled || (V2S.ui && V2S.ui.isOverlayOpen());
  }

  function settleWaiters(result) {
    const waiting = releaseWaiters;
    releaseWaiters = [];
    waiting.forEach(resolve => resolve(result));
  }

  function beginPress(kind, source, extra = {}) {
    const now = performance.now();
    if (press) return false;
    if (now - lastPressAt < cfg.DEBOUNCE_MS) {
      logEvent('press_debounced', { kind, source });
      return false;
    }
    lastPressAt = now;
    press = { kind, source, downAt: now, held: false, ...extra };
    press.timer = setTimeout(() => {
      if (!press) return;
      press.held = true;
      logEvent('press_held', { kind: press.kind, source: press.source });
      settleWaiters('hold');
      if (handlers.hold) handlers.hold({ kind: press.kind, source: press.source });
    }, cfg.HOLD_MS);
    logEvent('press', { kind, source });
    const handler = kind === 'primary' ? handlers.primary : handlers.secondary;
    if (handler) handler({ source });
    return true;
  }

  function endPress() {
    if (!press) return;
    clearTimeout(press.timer);
    const wasHeld = press.held;
    logEvent('release', { kind: press.kind, source: press.source, heldMs: Math.round(performance.now() - press.downAt) });
    press = null;
    if (!wasHeld) settleWaiters('released');
  }

  function cancelPress() {
    if (press) clearTimeout(press.timer);
    press = null;
    settleWaiters('released');
  }

  // Resolves 'released' when no press is down, or 'hold' if the current press is held too long.
  function waitForRelease() {
    if (!press) return Promise.resolve('released');
    if (press.held) return Promise.resolve('hold');
    return new Promise(resolve => releaseWaiters.push(resolve));
  }

  const isPressed = () => Boolean(press);

  function onKeyDown(event) {
    const kind = keyKind(event);
    if (!kind || blocked() || isEditable(event.target)) return;
    event.preventDefault();
    event.stopPropagation();
    document.documentElement.classList.add('has-keyboard');
    if (event.repeat) return;
    beginPress(kind, 'key', { key: event.code || event.key });
  }

  function onKeyUp(event) {
    if (!press || press.source !== 'key') return;
    if ((event.code || event.key) === press.key) {
      event.preventDefault();
      endPress();
    }
  }

  function bindButton(button, kind) {
    button.addEventListener('pointerdown', event => {
      if (blocked()) return;
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      event.preventDefault();
      pointerDown = true;
      if (button.getAttribute('aria-disabled') === 'true') return;
      try { button.setPointerCapture(event.pointerId); } catch (error) { /* not capturable */ }
      beginPress(kind, event.pointerType || 'pointer', { pointerId: event.pointerId });
    });
    const release = event => {
      if (pointerDown) lastPointerUpAt = performance.now();
      pointerDown = false;
      if (press && press.pointerId === event.pointerId) endPress();
    };
    button.addEventListener('pointerup', release);
    button.addEventListener('pointercancel', release);
    button.addEventListener('lostpointercapture', release);
    // The browser sends a click after every pointer press, however long it was held;
    // those are ignored (the press already acted on pointer-down). A click with no
    // pointer press before it comes from assistive technology and counts as a tap.
    button.addEventListener('click', event => {
      event.preventDefault();
      if (blocked() || pointerDown || performance.now() - lastPointerUpAt < 800) return;
      if (button.getAttribute('aria-disabled') === 'true') return;
      if (beginPress(kind, 'assistive')) endPress();
    });
    button.addEventListener('contextmenu', event => event.preventDefault());
  }

  window.addEventListener('keydown', onKeyDown, true);
  window.addEventListener('keyup', onKeyUp, true);
  window.addEventListener('blur', cancelPress);
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancelPress(); });

  return { configure, setEnabled, bindButton, waitForRelease, isPressed };
})();
