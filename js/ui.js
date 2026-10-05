// Rendering only: screens, the top bar, the recording screen, dialogs. No recording logic.
window.V2S = window.V2S || {};

V2S.ui = (() => {
  const cfg = V2S.config;
  const { el, platform } = V2S.util;
  const copy = V2S.copy;

  const ICONS = {
    warn: '<svg viewBox="0 0 24 24"><path d="M12 8v5M12 16.5v.5"/><circle cx="12" cy="12" r="9.5"/></svg>',
    info: '<svg viewBox="0 0 24 24"><path d="M12 11v6M12 7.5v.5"/><circle cx="12" cy="12" r="9.5"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>'
  };

  const SCREENS = ['loading', 'setup', 'welcome', 'folder', 'check', 'howto', 'record', 'break', 'done', 'error'];
  let currentScreen = 'loading';

  function show(name) {
    SCREENS.forEach(screen => { el(`screen-${screen}`).hidden = screen !== name; });
    currentScreen = name;
    document.body.dataset.screen = name;
    if (name !== 'record') {
      setRecording(false);
      setWhere(null);
      setFinishVisible(false);
    }
    el('helpButton').hidden = !['record', 'check'].includes(name);
    window.scrollTo(0, 0);
    if (name === 'record') requestAnimationFrame(() => fitSentences());
  }

  const screen = () => currentScreen;

  function setText(id, text) {
    const node = el(id);
    if (node) node.textContent = text == null ? '' : String(text);
  }

  // Two short sentences break between the sentences, not in the middle of one: each
  // sentence is an inline block (.sent in base.css), inside one group so that the space
  // between them survives in flex containers. A sentence ends at . ! or ? (and a closing
  // quote) followed by a capital or an opening quote, so a quoted sentence inside a line
  // (read “I need water.” again) stays in one piece.
  function setSentences(id, text) {
    const node = el(id);
    if (!node) return;
    node.replaceChildren();
    const group = document.createElement('span');
    group.className = 'sent-group';
    const parts = String(text || '').replace(/([.!?]["”’)]?)\s+(?=[A-Z“"‘(])/g, '$1\u0000').split('\u0000').filter(Boolean);
    parts.forEach((part, index) => {
      if (index) group.appendChild(document.createTextNode(' '));
      const span = document.createElement('span');
      span.className = 'sent';
      span.textContent = part;
      group.appendChild(span);
    });
    node.appendChild(group);
  }

  // Text with **bold** parts, built without innerHTML.
  function setRich(id, text) {
    const node = el(id);
    if (!node) return;
    node.replaceChildren();
    String(text || '').split('**').forEach((part, index) => {
      if (!part) return;
      if (index % 2) {
        const bold = document.createElement('b');
        bold.textContent = part;
        node.appendChild(bold);
      } else {
        node.appendChild(document.createTextNode(part));
      }
    });
  }

  // While a take is starting, recording or finishing, the top-bar actions are hidden.
  // data-live is only "on" while recording: it draws the green frame round the screen.
  function setRecording(on, live = false) {
    document.body.dataset.rec = on ? 'on' : 'off';
    document.body.dataset.live = live ? 'on' : 'off';
  }

  // ---- top bar ----
  function setWhere(where) {
    const box = el('where');
    box.hidden = !where;
    if (!where) return;
    setText('whereMain', where.main);
    setText('whereShort', where.short || where.main);
    setText('whereSub', where.sub || '');
    el('whereBar').style.transform = `scaleX(${Math.max(0, Math.min(1, where.progress || 0)).toFixed(4)})`;
  }

  function setFinishVisible(visible) {
    el('finishButton').hidden = !visible;
  }

  function labelTopbar(theme) {
    const label = theme === 'dark' ? copy.top.toLight : copy.top.toDark;
    el('themeButton').setAttribute('aria-label', label);
    el('themeButton').title = label;
    el('finishButton').setAttribute('aria-label', copy.top.finish);
    el('settingsButton').setAttribute('aria-label', copy.top.settings);
    el('settingsButton').title = copy.top.settings;
    el('helpButton').setAttribute('aria-label', copy.top.help);
    el('helpButton').title = copy.top.help;
  }

  // ---- recording screen ----
  function iconMarkup(icon) {
    if (icon === 'go') return '<span class="dot-go"></span>';
    if (icon === 'stop') return '<span class="square"></span>';
    if (icon === 'busy') return '<span class="spin"></span>';
    if (icon === 'next') return '<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
    if (icon === 'undo') return '<svg viewBox="0 0 24 24"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/></svg>';
    if (icon === 'cancel') return '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg>';
    return '';
  }

  let lastCoachVisible = null;

  function renderRecord(view) {
    const screenEl = el('screen-record');
    screenEl.dataset.state = view.state;
    screenEl.classList.toggle('is-saved', Boolean(view.saved));
    setRecording(view.state !== 'ready', view.state === 'recording');
    setWhere(view.where);
    setFinishVisible(view.state === 'ready');

    setText('cardStatusText', view.status);
    setText('sentenceText', view.sentence);

    const main = el('mainButton');
    el('mainIcon').innerHTML = iconMarkup(view.main.icon);
    setText('mainLabel', view.main.label);
    main.classList.toggle('is-stop', view.main.icon === 'stop');
    main.setAttribute('aria-disabled', view.main.disabled ? 'true' : 'false');

    // Hidden controls keep their space so nothing else moves.
    const redo = el('redoButton');
    const redoView = view.redo || {};
    const redoVisible = Boolean(redoView.visible);
    redo.classList.toggle('is-invisible', !redoVisible);
    redo.classList.toggle('is-cancel', Boolean(redoView.cancel));
    redo.setAttribute('aria-hidden', redoVisible ? 'false' : 'true');
    redo.setAttribute('aria-disabled', redoVisible ? 'false' : 'true');
    redo.tabIndex = redoVisible ? 0 : -1;
    el('redoIcon').innerHTML = iconMarkup(redoView.cancel ? 'cancel' : 'undo');
    setText('redoLabel', redoView.label || copy.record.redo);
    setText('redoCaption', redoVisible ? redoView.caption || '' : '');
    el('redoCaption').hidden = !(redoVisible && redoView.caption);
    // "Saved" belongs to the sentence just recorded: it is shown here, next to it.
    el('redoSaved').hidden = !(redoVisible && redoView.saved);
    el('recordFrame').classList.toggle('is-invisible', !view.showCamera);

    const message = el('message');
    const hasMessage = Boolean(view.message && view.message.text);
    message.className = `message${hasMessage ? ` tone-${view.message.tone}` : ' is-empty'}`;
    setSentences('messageText', hasMessage ? view.message.text : '');
    el('messageIcon').innerHTML = hasMessage ? (ICONS[view.message.tone] || '') : '';

    setTimer(view.state === 'recording' ? view.liveSince : null);
    renderCoach(view.coach);
    main.classList.toggle('is-pulsing', view.pulse === 'main');
    redo.classList.toggle('is-pulsing', view.pulse === 'redo' && redoVisible);
  }

  function renderCoach(coach) {
    const box = el('coach');
    const visible = Boolean(coach);
    box.hidden = !visible;
    if (visible) {
      setSentences('coachText', coach.text);
      // Hidden but still taking its room, so the card does not move.
      el('coachSteps').classList.toggle('is-invisible', !coach.step);
      el('coachSteps').querySelectorAll('li').forEach(item => {
        const step = Number(item.dataset.step);
        const done = Boolean(coach.step) && (coach.allDone || step < coach.step);
        item.classList.toggle('is-active', !coach.allDone && step === coach.step);
        item.classList.toggle('is-done', done);
        item.querySelector('.step-num').innerHTML = done ? ICONS.check : String(step);
      });
    }
    // The card changes size when the coach appears or goes: fit the sentence again.
    if (visible !== lastCoachVisible) {
      lastCoachVisible = visible;
      requestAnimationFrame(() => fitSentences());
    }
  }

  // ---- sentence size ----
  // One size per screen and sentence set (see config.SENTENCE_SIZE), so the size never
  // changes from one sentence to the next, and the card keeps room for the longest one.
  let fitList = [];
  let fitTimer = null;

  function deviceClass() {
    const matches = query => Boolean(window.matchMedia && window.matchMedia(query).matches);
    if (matches('(max-height: 500px) and (orientation: landscape)')) return 'flat';
    if (matches('(max-width: 600px)')) return 'phone';
    if (matches('(max-width: 1000px) and (orientation: portrait)')) return 'tall';
    return 'wide';
  }

  function fitSentences(list) {
    if (list) fitList = list.slice();
    const screenEl = el('screen-record');
    if (!fitList.length || screenEl.hidden) return;
    const card = el('card');
    const style = getComputedStyle(card);
    const width = Math.floor(card.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight));
    if (width < 120) return;
    const kind = deviceClass();
    const rule = cfg.SENTENCE_SIZE[kind];
    const probe = el('sentenceText').cloneNode(false);
    probe.removeAttribute('id');
    Object.assign(probe.style, { position: 'absolute', visibility: 'hidden', left: '0', top: '0', whiteSpace: 'nowrap', width: 'auto', maxWidth: 'none', fontSize: '100px', transition: 'none' });
    document.body.appendChild(probe);
    // Each sentence on one line at 100 px.
    const widths = fitList.map(text => {
      probe.textContent = text;
      return probe.getBoundingClientRect().width;
    });
    const totalChars = fitList.reduce((sum, text) => sum + text.length, 0) || 1;
    const charWidth = widths.reduce((sum, w) => sum + w, 0) / totalChars;
    const typicalWidth = V2S.util.percentile(widths, cfg.SENTENCE_ONE_LINE_SHARE);
    // Most sentences on one line, with some air at both ends. Where even the smallest size
    // cannot do that (phones held upright), most sentences on two lines instead; wrapped
    // lines lose some width at word breaks, hence 85%.
    const oneLine = width * cfg.SENTENCE_LINE_FILL;
    const targetLines = typicalWidth * rule.min / 100 <= oneLine ? 1 : 2;
    const lineLimit = targetLines === 1 ? oneLine * 100 / typicalWidth : width * 2 * 0.85 * 100 / typicalWidth;
    let size = Math.floor(Math.min(rule.max, lineLimit, width * 100 / (cfg.SENTENCE_MIN_CHARS_PER_LINE * charWidth)));
    size = Math.max(rule.min, size);
    // The longest sentences, wrapped to the card: at most rule.lines lines.
    Object.assign(probe.style, { whiteSpace: 'normal', width: `${width}px`, maxWidth: `${width}px` });
    const longest = fitList.map((text, i) => [widths[i], text]).sort((a, b) => b[0] - a[0]).slice(0, 6).map(pair => pair[1]);
    const linesAt = px => {
      probe.style.fontSize = `${px}px`;
      return Math.max(...longest.map(text => {
        probe.textContent = text;
        return Math.round(probe.getBoundingClientRect().height / (px * 1.2));
      }));
    };
    let lines = linesAt(size);
    while (lines > rule.lines && size > rule.min) {
      size -= 1;
      lines = linesAt(size);
    }
    probe.remove();
    const apply = () => {
      screenEl.style.setProperty('--sentence-size', `${size}px`);
      screenEl.style.setProperty('--sentence-lines', String(lines));
    };
    apply();
    // Very short screens (and the practice coach): the whole stack must still fit.
    for (let i = 0; i < 10 && screenEl.scrollHeight > screenEl.clientHeight + 1 && size > rule.min - 6; i++) {
      size -= 2;
      apply();
    }
    screenEl.dataset.fit = `${kind}:${size}:${lines}`;
  }

  window.addEventListener('resize', () => {
    clearTimeout(fitTimer);
    fitTimer = setTimeout(() => fitSentences(), 120);
  });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => fitSentences());

  // ---- recording timer (in the "Recording" pill) ----
  // Only on long takes (a forgotten Stop, or the 1-minute limit coming up): a clock
  // running from 0:00 would hurry people who speak slowly.
  let timerId = null;

  function setTimer(since) {
    clearInterval(timerId);
    timerId = null;
    const node = el('cardTimer');
    if (!since) {
      node.textContent = '';
      return;
    }
    const tick = () => {
      const ms = performance.now() - since;
      const seconds = Math.max(0, Math.floor(ms / 1000));
      node.textContent = ms < cfg.TIMER_SHOW_AFTER_MS ? '' : `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
    };
    tick();
    timerId = setInterval(tick, 250);
  }

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

  // actions: [{ label, value, variant: 'go' | 'plain' | 'ghost' | 'caution', default }]
  // input: { label, placeholder, value } adds a text field; the result is then
  // { action, value }.
  function dialog({ title, body, actions, dismissValue, input }) {
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
      let field = null;
      if (input) {
        const wrap = document.createElement('label');
        wrap.className = 'field';
        const label = document.createElement('span');
        label.className = 'field-label';
        label.textContent = input.label || '';
        field = document.createElement('input');
        field.className = 'input';
        field.type = 'text';
        field.autocomplete = 'off';
        field.spellcheck = false;
        field.placeholder = input.placeholder || '';
        field.value = input.value || '';
        wrap.append(label, field);
        bodyEl.appendChild(wrap);
      }
      actionsEl.replaceChildren();
      let defaultButton = null;
      const state = { resolve, dismissValue, armed: false, field };
      actions.forEach(action => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `btn btn-lg btn-block btn-${action.variant || 'ghost'}`;
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
      requestAnimationFrame(() => (field || defaultButton) && (field || defaultButton).focus());
    });
  }

  function finishDialog(value) {
    const state = dialogState;
    if (!state) return;
    dialogState = null;
    el('dialog').hidden = true;
    if (document.activeElement && typeof document.activeElement.blur === 'function') document.activeElement.blur();
    state.resolve(state.field ? { action: value, value: state.field.value } : value);
  }

  document.addEventListener('keydown', event => {
    if (!dialogState) return;
    if (event.key === 'Escape' && dialogState.dismissValue !== undefined) {
      event.preventDefault();
      event.stopImmediatePropagation(); // Esc closes only the dialog, not Settings behind it
      finishDialog(dialogState.dismissValue);
    } else if (event.key === 'Enter' && dialogState.field && document.activeElement === dialogState.field) {
      event.preventDefault();
      const first = el('dialogActions').querySelector('button');
      if (first && dialogState.armed) first.click();
    } else if (event.key === 'Tab') {
      const focusable = [dialogState.field, ...el('dialogActions').querySelectorAll('button')].filter(Boolean);
      const index = focusable.indexOf(document.activeElement);
      event.preventDefault();
      const next = event.shiftKey ? (index <= 0 ? focusable.length - 1 : index - 1) : (index + 1) % focusable.length;
      focusable[next].focus();
    } else if (event.repeat) {
      event.preventDefault();
    }
  }, true);

  const isDialogOpen = () => Boolean(dialogState);
  const isOverlayOpen = () => Boolean(dialogState) || !el('settingsPanel').hidden;

  function confirm({ title, body, yes, no, caution }) {
    return dialog({
      title,
      body,
      actions: [
        { label: yes || copy.settings.confirm, value: true, variant: caution ? 'caution' : 'go' },
        { label: no || copy.common.cancel, value: false, variant: 'ghost', default: true }
      ],
      dismissValue: false
    });
  }

  function alert(title, body) {
    return dialog({ title, body, actions: [{ label: copy.common.ok, value: true, variant: 'go', default: true }], dismissValue: true });
  }

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
      actions: [{ label: copy.help.close, value: true, variant: 'go', default: true }],
      dismissValue: true
    });
  }

  return {
    show,
    screen,
    setText,
    setSentences,
    setRich,
    setRecording,
    setWhere,
    labelTopbar,
    renderRecord,
    fitSentences,
    watchPreviewShape,
    dialog,
    confirm,
    alert,
    isDialogOpen,
    isOverlayOpen,
    helpText,
    showCameraHelp,
    ICONS
  };
})();
