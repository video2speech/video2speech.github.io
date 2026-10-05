// One place for every press on the recording screen. Three rules only:
//   1. keyboard auto-repeat is ignored;
//   2. a key or touch held for HOLD_MS triggers the hold handler (the session then
//      throws the take away and restarts the same sentence);
//   3. presses closer together than DEBOUNCE_MS are ignored.
// Presses act immediately on key-down / pointer-down, never on release.
//
// On every screen: when a screen (or a step on it) changes, clicks are ignored for
// ENTER_GUARD_MS, and a key or finger still down from the press that changed it does
// nothing on the new screen (see screenChanged).
window.V2S = window.V2S || {};

V2S.input = (() => {
  const cfg = V2S.config;
  const { logEvent } = V2S.util;
  const PRIMARY_KEYS = new Set([' ', 'Spacebar', 'Enter', 'ArrowRight', 'PageDown']);
  const SECONDARY_KEYS = new Set(['ArrowLeft', 'PageUp']);

  let handlers = { primary: null, secondary: null, hold: null };
  let holdMs = cfg.HOLD_MS;   // Settings: 1, 2 or 3 s (people who release buttons slowly)
  let enabled = false;
  let press = null;
  let lastPressAt = -Infinity;
  let pointerDown = false;
  let lastPointerUpAt = -Infinity;
  let releaseWaiters = [];

  function configure(next) {
    handlers = { ...handlers, ...next };
  }

  function setHoldMs(ms) {
    holdMs = Number(ms) >= 1000 ? Number(ms) : cfg.HOLD_MS;
  }

  // `guard`: the press that opened the recording screen (Continue, Continue to part 2…)
  // may be followed by a second one, so presses in the first ENTER_GUARD_MS are ignored.
  function setEnabled(value, { guard = false } = {}) {
    enabled = Boolean(value);
    if (!enabled) cancelPress();
    else if (guard) lastPressAt = Math.max(lastPressAt, performance.now() + cfg.ENTER_GUARD_MS - cfg.DEBOUNCE_MS);
  }

  // Ignore presses for the next ENTER_GUARD_MS (after a dialog closes: a double tap on OK
  // must not start a recording).
  function guard() {
    lastPressAt = Math.max(lastPressAt, performance.now() + cfg.ENTER_GUARD_MS - cfg.DEBOUNCE_MS);
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
    }, holdMs);
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

  // ---------- every screen: a press carried over to the next screen ----------
  // The second tap of a double tap, or a tremor's bounce, must not press the button that
  // has just appeared under the finger: clicks are ignored for a moment after a change.
  // A key or finger still down from the press that changed the screen does nothing
  // there: auto-repeat never presses a button, and that key's or finger's release is
  // ignored, so holding Space or Enter cannot run on through the next screens.
  const ACTIVATING_KEYS = new Set(['Space', 'Enter', 'NumpadEnter']);
  const keysDown = new Set();
  const pointersDown = new Set();
  let carriedKeys = new Set();
  let carriedPointers = new Set();
  let clicksFrom = 0;

  const holdClicks = ms => { clicksFrom = Math.max(clicksFrom, performance.now() + ms); };
  const clicksPaused = () => performance.now() < clicksFrom;

  function screenChanged() {
    holdClicks(cfg.ENTER_GUARD_MS);
    carriedKeys = new Set(keysDown);
    carriedPointers = new Set(pointersDown);
  }

  function forgetHeld() {
    keysDown.clear();
    pointersDown.clear();
    carriedKeys.clear();
    carriedPointers.clear();
  }

  function trackKeyDown(event) {
    const key = event.code || event.key;
    if (!ACTIVATING_KEYS.has(key)) return;
    if (event.repeat) {
      event.preventDefault();
      return;
    }
    carriedKeys.delete(key);   // released unnoticed and pressed again: a new press
    keysDown.add(key);
  }

  function trackKeyUp(event) {
    const key = event.code || event.key;
    keysDown.delete(key);
    if (!carriedKeys.delete(key) || isEditable(event.target)) return;
    event.preventDefault();    // Space presses the focused button on release
    holdClicks(150);
  }

  function trackPointerUp(event) {
    pointersDown.delete(event.pointerId);
    if (carriedPointers.delete(event.pointerId)) holdClicks(cfg.ENTER_GUARD_MS);   // the click this release makes
  }

  document.addEventListener('click', event => {
    if (!clicksPaused()) return;
    const target = event.target && event.target.closest && event.target.closest('button');
    if (!target || target.closest('#dialog') || target.closest('#settingsPanel')) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);

  // A top-bar button reached with Tab (End for today, ?, Settings) keeps Space and Enter.
  function ownKeys(event) {
    const button = event.target && event.target.closest && event.target.closest('button');
    if (!button || button.id === 'mainButton' || button.id === 'redoButton') return false;
    if (event.code !== 'Space' && event.key !== 'Enter') return false;
    try { return button.matches(':focus-visible'); } catch (error) { return false; }
  }

  function onKeyDown(event) {
    const kind = keyKind(event);
    if (!kind || blocked() || isEditable(event.target) || ownKeys(event)) return;
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

  // The carried-press listeners come first: they must see a key before the press it
  // makes changes the screen.
  window.addEventListener('keydown', trackKeyDown, true);
  window.addEventListener('keyup', trackKeyUp, true);
  window.addEventListener('pointerdown', event => pointersDown.add(event.pointerId), true);
  window.addEventListener('pointerup', trackPointerUp, true);
  window.addEventListener('pointercancel', trackPointerUp, true);
  window.addEventListener('keydown', onKeyDown, true);
  window.addEventListener('keyup', onKeyUp, true);
  window.addEventListener('blur', () => { cancelPress(); forgetHeld(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelPress(); forgetHeld(); } });

  // For tests: a press now would count (not within DEBOUNCE_MS of the last, nor guarded).
  const pressReady = () => performance.now() - lastPressAt >= cfg.DEBOUNCE_MS;

  return { guard, configure, setEnabled, setHoldMs, getHoldMs: () => holdMs, bindButton, waitForRelease, isPressed, screenChanged, clicksPaused, pressReady };
})();
