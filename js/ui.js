// Rendering only: screens, the recording screen, dialogs. No recording logic here.
window.V2S = window.V2S || {};

V2S.ui = (() => {
  const { el, platform } = V2S.util;
  const copy = V2S.copy;

  const ICONS = {
    undo: '<svg viewBox="0 0 24 24"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/></svg>',
    restart: '<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>',
    warn: '<svg viewBox="0 0 24 24"><path d="M12 8v5M12 16.5v.5"/><circle cx="12" cy="12" r="9.5"/></svg>',
    tip: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12l7 7 7-7"/></svg>',
    info: '<svg viewBox="0 0 24 24"><path d="M12 11v6M12 7.5v.5"/><circle cx="12" cy="12" r="9.5"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>'
  };

  const SCREENS = ['loading', 'setup', 'welcome', 'folder', 'check', 'record', 'break', 'done', 'error'];
  let currentScreen = 'loading';

  function show(name) {
    SCREENS.forEach(screen => { el(`screen-${screen}`).hidden = screen !== name; });
    currentScreen = name;
    document.body.dataset.screen = name;
    if (name !== 'record') setRecordingFrame(false);
    window.scrollTo(0, 0);
  }

  const screen = () => currentScreen;

  function setText(id, text) {
    const node = el(id);
    if (node) node.textContent = text == null ? '' : String(text);
  }

  function setRecordingFrame(on) {
    document.body.dataset.rec = on ? 'on' : 'off';
  }

  // ---- recording screen ----
  function iconMarkup(icon) {
    if (icon === 'rec') return '<span class="icon-rec"></span>';
    if (icon === 'stop') return '<span class="icon-stop"></span>';
    if (icon === 'spinner') return '<span class="icon-spinner"></span>';
    return ICONS[icon] || '';
  }

  function renderRecord(view) {
    const screenEl = el('screen-record');
    screenEl.dataset.state = view.state;
    screenEl.classList.toggle('just-saved', Boolean(view.justSaved) && view.state === 'ready');
    setRecordingFrame(view.state === 'recording');

    setText('recStateText', view.stateText);
    setText('sentenceText', view.sentence);
    setText('progressMain', view.progressMain);
    setText('progressSub', view.progressSub);
    el('progressBar').style.transform = `scaleX(${Math.max(0, Math.min(1, view.progress || 0)).toFixed(4)})`;

    const primary = el('primaryButton');
    el('primaryIcon').innerHTML = iconMarkup(view.primary.icon);
    setText('primaryLabel', view.primary.label);
    primary.setAttribute('aria-disabled', view.primary.disabled ? 'true' : 'false');

    // A hidden secondary button keeps its space so nothing else moves.
    const secondary = el('secondaryButton');
    const secondaryHidden = Boolean(view.secondary.hidden);
    secondary.classList.toggle('is-invisible', secondaryHidden);
    secondary.setAttribute('aria-hidden', secondaryHidden ? 'true' : 'false');
    secondary.tabIndex = secondaryHidden ? -1 : 0;
    el('secondaryIcon').innerHTML = iconMarkup(view.secondary.icon);
    setText('secondaryLabel', view.secondary.label);
    secondary.setAttribute('aria-disabled', view.secondary.disabled || secondaryHidden ? 'true' : 'false');

    // One message at a time.
    const message = el('recMessage');
    const hasMessage = Boolean(view.message && view.message.text);
    message.className = `rec-message${hasMessage ? ` tone-${view.message.tone}` : ' is-empty'}`;
    setText('recMessageText', hasMessage ? view.message.text : '');
    el('recMessageIcon').innerHTML = hasMessage ? (ICONS[view.message.tone] || '') : '';

    primary.classList.toggle('is-highlighted', view.highlight === 'primary');
    secondary.classList.toggle('is-highlighted', view.highlight === 'secondary' && !secondaryHidden);
    el('saveStatus').classList.toggle('is-highlighted', view.highlight === 'save');

    el('finishButton').classList.toggle('is-invisible', !view.showFinish);
    el('finishButton').tabIndex = view.showFinish ? 0 : -1;
  }

  // Save status under the camera preview (folder or device).
  function setSaveStatus({ text, tone, actionable }) {
    const node = el('saveStatus');
    node.className = `save-status${tone ? ` is-${tone}` : ''}${node.classList.contains('is-highlighted') ? ' is-highlighted' : ''}`;
    node.innerHTML = (tone === 'ok' ? `<span class="btn-icon">${ICONS.check}</span>` : '') + '<span></span>';
    node.lastElementChild.textContent = text || '';
    node.disabled = !actionable;
    node.setAttribute('aria-disabled', actionable ? 'false' : 'true');
  }

  // Keep the sentence area tall enough for the longest sentence so nothing jumps.
  let fitList = [];
  let fitTimer = null;

  function fitSentences(list) {
    if (list) fitList = list;
    const sample = el('sentenceText');
    if (!fitList.length || el('screen-record').hidden) return;
    const stageWidth = sample.parentElement.clientWidth;
    if (!stageWidth) return;
    // Lines wrap at the smaller of the sentence's max-width and the stage width.
    const lineWidth = Math.min(parseFloat(getComputedStyle(sample).maxWidth) || stageWidth, stageWidth);
    const meter = sample.cloneNode(false);
    meter.removeAttribute('id');
    Object.assign(meter.style, { position: 'absolute', visibility: 'hidden', left: '-9999px', top: '0', width: 'auto', maxWidth: `${lineWidth}px`, minHeight: '0' });
    sample.parentElement.appendChild(meter);
    let tallest = 0;
    fitList.forEach(sentence => {
      meter.textContent = sentence;
      tallest = Math.max(tallest, meter.getBoundingClientRect().height);
    });
    meter.remove();
    sample.style.setProperty('--sentence-min', `${Math.ceil(tallest)}px`);
  }

  window.addEventListener('resize', () => {
    clearTimeout(fitTimer);
    fitTimer = setTimeout(() => fitSentences(), 150);
  });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => fitSentences());

  // Portrait camera streams (phones held upright) get a portrait frame.
  function watchPreviewShape(frameId, videoId) {
    const frame = el(frameId);
    const video = el(videoId);
    const update = () => {
      if (video.videoWidth && video.videoHeight) frame.classList.toggle('is-portrait', video.videoHeight > video.videoWidth);
    };
    video.addEventListener('loadedmetadata', update);
    video.addEventListener('resize', update);
  }

  // ---- dialog ----
  let dialogState = null;

  function dialog({ title, body, actions, dismissValue }) {
    if (dialogState) finishDialog(dialogState.dismissValue);
    return new Promise(resolve => {
      const overlay = el('dialog');
      const actionsEl = el('dialogActions');
      setText('dialogTitle', title);
      const bodyEl = el('dialogBody');
      bodyEl.replaceChildren();
      (Array.isArray(body) ? body : [body]).filter(Boolean).forEach(part => {
        if (part instanceof Node) {
          bodyEl.appendChild(part);
        } else {
          const p = document.createElement('p');
          p.textContent = part;
          bodyEl.appendChild(p);
        }
      });
      actionsEl.replaceChildren();
      let defaultButton = null;
      const state = { resolve, dismissValue, armed: false };
      actions.forEach(action => {
        const button = document.createElement('button');
        button.type = 'button';
        const variant = action.variant === 'primary' ? 'btn-primary' : action.variant === 'danger' ? 'btn-danger' : 'btn-quiet';
        button.className = `btn btn-lg btn-block ${variant}`;
        button.textContent = action.label;
        button.addEventListener('click', () => {
          // Ignore presses that started before the dialog appeared.
          if (!state.armed) return;
          finishDialog(action.value);
        });
        actionsEl.appendChild(button);
        if (action.default || !defaultButton) defaultButton = button;
      });
      dialogState = state;
      overlay.hidden = false;
      setTimeout(() => { state.armed = true; }, 350);
      requestAnimationFrame(() => defaultButton && defaultButton.focus());
    });
  }

  function finishDialog(value) {
    const state = dialogState;
    if (!state) return;
    dialogState = null;
    el('dialog').hidden = true;
    if (document.activeElement && typeof document.activeElement.blur === 'function') document.activeElement.blur();
    state.resolve(value);
  }

  document.addEventListener('keydown', event => {
    if (!dialogState) return;
    if (event.key === 'Escape' && dialogState.dismissValue !== undefined) {
      event.preventDefault();
      finishDialog(dialogState.dismissValue);
    } else if (event.key === 'Tab') {
      const buttons = Array.from(el('dialogActions').querySelectorAll('button'));
      if (!buttons.length) return;
      const index = buttons.indexOf(document.activeElement);
      event.preventDefault();
      const next = event.shiftKey ? (index <= 0 ? buttons.length - 1 : index - 1) : (index + 1) % buttons.length;
      buttons[next].focus();
    } else if (event.repeat) {
      event.preventDefault();
    }
  }, true);

  const isDialogOpen = () => Boolean(dialogState);
  const isOverlayOpen = () => Boolean(dialogState) || !el('adminPanel').hidden;

  function helpText() {
    if (platform.ios) return copy.help.ios;
    if (platform.android) return copy.help.android;
    if (platform.safari && platform.mac) return copy.help.macSafari;
    return copy.help.desktop;
  }

  function showCameraHelp() {
    return dialog({
      title: copy.help.title,
      body: helpText(),
      actions: [{ label: copy.help.close, value: true, variant: 'primary', default: true }],
      dismissValue: true
    });
  }

  return {
    show,
    screen,
    setText,
    setRecordingFrame,
    renderRecord,
    setSaveStatus,
    fitSentences,
    watchPreviewShape,
    dialog,
    isDialogOpen,
    isOverlayOpen,
    helpText,
    showCameraHelp
  };
})();
