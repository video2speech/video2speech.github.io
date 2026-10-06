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

  const SCREENS = ['loading', 'setup', 'welcome', 'folder', 'check', 'intro', 'record', 'break', 'done', 'error'];
  let currentScreen = 'loading';

  // A screen (or a step on it) changed: a press carried over from the last one does
  // nothing here (input.js).
  const pauseClicks = () => V2S.input.screenChanged();

  function show(name) {
    if (name !== currentScreen) pauseClicks();
    SCREENS.forEach(screen => { el(`screen-${screen}`).hidden = screen !== name; });
    currentScreen = name;
    document.body.dataset.screen = name;
    if (name !== 'record') {
      document.body.classList.remove('is-redo-lesson');
      setRecording(false);
      setWhere(null);
      // Breaks and Practice done keep End for today where it is on the recording screen
      // (top left), never under their main button.
      setFinishVisible(name === 'break');
    }
    el('helpButton').hidden = name !== 'record';
    window.scrollTo(0, 0);
    if (name === 'record') requestAnimationFrame(() => fitSentences());
    markOverflow();
  }

  // A flow screen whose words must scroll (a small phone held sideways) fades their edges,
  // so no line looks cut in half; one that fits shows every line in full.
  let overflowFrame = 0;
  function markOverflow() {
    cancelAnimationFrame(overflowFrame);
    overflowFrame = requestAnimationFrame(() => {
      document.querySelectorAll('.screen-flow:not([hidden]) .flow-body').forEach(body => {
        body.classList.toggle('is-overflowing', body.scrollHeight > body.clientHeight + 1);
      });
    });
  }
  window.addEventListener('resize', markOverflow);
  new MutationObserver(markOverflow).observe(document.querySelector('.screens') || document.body,
    { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['hidden'] });

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
    if (parts.length === 1) {
      node.textContent = parts[0];
      return;
    }
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
    setText('whereTiny', where.tiny || where.short || where.main);
    el('whereBar').style.transform = `scaleX(${Math.max(0, Math.min(1, where.progress || 0)).toFixed(4)})`;
  }

  function setFinishVisible(visible) {
    el('finishButton').hidden = !visible;
  }

  function labelTopbar() {
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
    setRecording(view.state !== 'ready', view.state === 'recording');
    setWhere(view.where);
    // Shown only while waiting (data-rec hides it otherwise), but it keeps its room.
    setFinishVisible(true);

    setText('cardStatusText', view.status);
    // The sentence sits in one inline span, so a highlight can follow its lines.
    const sentence = el('sentenceText');
    let line = sentence.firstElementChild;
    if (!line || !line.classList.contains('sentence-line')) {
      line = document.createElement('span');
      line.className = 'sentence-line';
      sentence.replaceChildren(line);
    }
    line.textContent = phrased(view.sentence);

    const main = el('mainButton');
    el('mainIcon').innerHTML = iconMarkup(view.main.icon);
    setText('mainLabel', view.main.label);
    main.classList.toggle('is-stop', view.main.icon === 'stop');
    main.classList.toggle('is-next', view.main.icon === 'next');
    main.classList.toggle('is-quiet', Boolean(view.main.quiet));
    main.setAttribute('aria-disabled', view.main.disabled ? 'true' : 'false');

    // Hidden controls keep their space so nothing else moves.
    const redo = el('redoButton');
    const redoView = view.redo || {};
    const redoVisible = Boolean(redoView.visible);
    redo.classList.toggle('is-invisible', !redoVisible);
    redo.classList.toggle('is-cancel', Boolean(redoView.cancel));
    redo.setAttribute('aria-hidden', redoVisible ? 'false' : 'true');
    redo.setAttribute('aria-disabled', redoVisible ? 'false' : 'true');
    el('redoIcon').innerHTML = iconMarkup(redoView.cancel ? 'cancel' : 'undo');
    setText('redoLabel', redoView.label || copy.record.redo);
    setText('redoCaption', redoVisible ? redoView.caption || '' : '');
    el('redoCaption').hidden = !(redoVisible && redoView.caption);
    // The Redo lesson: Redo is the one thing to press, as large as Start.
    redo.classList.toggle('is-lesson', view.pulse === 'redo' && redoVisible);
    document.body.classList.toggle('is-redo-lesson', view.pulse === 'redo' && redoVisible);
    fitRedoCaption();

    const message = el('message');
    const hasMessage = Boolean(view.message && view.message.text);
    message.className = `message${hasMessage ? ` tone-${view.message.tone}` : ' is-empty'}`;
    setSentences('messageText', hasMessage ? view.message.text : '');
    el('messageIcon').innerHTML = hasMessage ? ({ ok: ICONS.check, warn: ICONS.warn }[view.message.tone] || '') : '';

    setTimer(view.state === 'recording' ? view.liveSince : null);
    renderCoach(view.coach);
    main.classList.toggle('is-pulsing', view.pulse === 'main');
    redo.classList.toggle('is-pulsing', view.pulse === 'redo' && redoVisible);
  }

  // The guide keeps one height (CSS), so nothing moves while practising.
  function renderCoach(coach) {
    const box = el('coach');
    const visible = Boolean(coach);
    box.hidden = !visible;
    el('screen-record').classList.toggle('is-coaching', visible);
    if (visible) {
      const ack = coach.ack;
      el('coachAck').className = `coach-ack${ack ? ` tone-${ack.tone}` : ' is-empty'}`;
      el('coachAckIcon').innerHTML = ack ? ({ ok: ICONS.check, warn: ICONS.warn, info: ICONS.info }[ack.tone] || '') : '';
      setText('coachAckText', ack ? ack.text : '');
      setSentences('coachAction', coach.action || '');
      setText('coachDetail', coach.detail || '');
    }
    // Fit the sentence again when the coach appears or goes (practice ↔ real sentences).
    if (visible !== lastCoachVisible) {
      lastCoachVisible = visible;
      requestAnimationFrame(() => fitSentences());
    }
  }

  // Lines break between phrases: a short word that leads into the next one (the, a, to,
  // my…) is kept with it, so a sentence never splits as "Please put the / water".
  const LEADING_WORDS = /\b(a|an|the|to|of|in|on|at|for|with|my|your|our|his|her|their|its|this|that|some|no)\s+/gi;
  const phrased = text => String(text || '').replace(LEADING_WORDS, (match, word) => `${word}\u00a0`);

  // ---- sentence size ----
  // One size per screen and sentence set (see config.SENTENCE_SIZE), so the size never
  // changes from one sentence to the next, and the card keeps room for the longest one.
  let fitList = [];
  let twoLineCache = { key: null, size: 0 };
  let fitTimer = null;

  function deviceClass() {
    const matches = query => Boolean(window.matchMedia && window.matchMedia(query).matches);
    if (matches('(max-height: 500px) and (orientation: landscape)')) return 'flat';
    if (matches('(max-width: 600px)')) return 'phone';
    if (matches('(max-width: 1000px) and (orientation: portrait)')) return 'tall';
    return 'wide';
  }

  // Redo has Start's width; a long sentence on it shrinks to fit (down to 13 px, as iOS
  // shrinks a label) before it would be cut off.
  const REDO_CAPTION_MIN_PX = 13;
  function fitRedoCaption() {
    const caption = el('redoCaption');
    caption.style.fontSize = '';
    if (caption.hidden || !caption.textContent) return;
    let size = parseFloat(getComputedStyle(caption).fontSize) || 16;
    while (caption.scrollWidth > caption.clientWidth + 1 && size > REDO_CAPTION_MIN_PX) {
      size -= 0.5;
      caption.style.fontSize = `${size}px`;
    }
  }

  function fitSentences(list) {
    if (list) fitList = list.slice();
    const screenEl = el('screen-record');
    if (!fitList.length || screenEl.hidden) return;
    // The width the sentence really has (inside the card and its text area).
    const box = el('sentenceText').parentElement;
    const style = getComputedStyle(box);
    const width = Math.floor(box.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight));
    if (width < 120) return;
    // The highlight while recording pads each line by 0.22em on both sides.
    const pad = 0.44;
    const kind = deviceClass();
    const rule = cfg.SENTENCE_SIZE[kind];
    const probe = el('sentenceText').cloneNode(false);
    probe.removeAttribute('id');
    Object.assign(probe.style, { position: 'absolute', visibility: 'hidden', left: '0', top: '0', whiteSpace: 'nowrap', width: 'auto', maxWidth: 'none', fontSize: '100px', transition: 'none' });
    document.body.appendChild(probe);
    // Each sentence on one line at 100 px.
    const widths = fitList.map(text => {
      probe.textContent = phrased(text);
      return probe.getBoundingClientRect().width;
    });
    const totalChars = fitList.reduce((sum, text) => sum + text.length, 0) || 1;
    const charWidth = widths.reduce((sum, w) => sum + w, 0) / totalChars;
    const typicalWidth = V2S.util.percentile(widths, cfg.SENTENCE_ONE_LINE_SHARE);
    // Most sentences on one line, with some air at both ends. Where even the smallest size
    // cannot do that (phones held upright), most sentences on two lines instead; wrapped
    // lines lose some width at word breaks, hence 85%.
    const oneLine = width * cfg.SENTENCE_LINE_FILL;
    const targetLines = rule.min * (typicalWidth / 100 + pad) <= oneLine ? 1 : 2;
    const lineLimit = targetLines === 1 ? oneLine / (typicalWidth / 100 + pad) : width * 2 * 0.85 / (typicalWidth / 100 + 2 * pad);
    let size = Math.floor(Math.min(rule.max, lineLimit, width / (cfg.SENTENCE_MIN_CHARS_PER_LINE * charWidth / 100 + pad)));
    size = Math.max(rule.min, size);
    // Phones: most sentences on at most two lines as they really wrap (a phrase is never
    // split), going a little smaller before a third line; three short lines read as
    // keywords one by one ("Please put / the water / down here.").
    const fitKey = `${kind}:${width}:${fitList.length}:${fitList[0]}:${fitList[fitList.length - 1]}`;
    if (rule.twoLineShare && twoLineCache.key === fitKey) {
      size = twoLineCache.size;
    } else if (rule.twoLineShare) {
      probe.style.whiteSpace = 'normal';
      const linesOf = (text, px) => {
        probe.style.fontSize = `${px}px`;
        probe.style.width = probe.style.maxWidth = `${width - pad * px}px`;
        probe.textContent = phrased(text);
        return Math.round(probe.getBoundingClientRect().height / (px * 1.2));
      };
      const allowed = Math.floor(fitList.length * (1 - rule.twoLineShare));
      // A sentence that fits on one line at this size needs no measuring.
      let longer = fitList.filter((text, i) => widths[i] * size / 100 > width - 2 * pad * size && linesOf(text, size) > 2);
      while (longer.length > allowed && size > rule.twoLineMin) {
        size -= 1;
        longer = longer.filter(text => linesOf(text, size) > 2);
      }
      twoLineCache = { key: fitKey, size };
    }
    // The longest sentences, wrapped to the card: at most rule.lines lines.
    Object.assign(probe.style, { whiteSpace: 'normal', width: `${width}px`, maxWidth: `${width}px` });
    const longest = fitList.map((text, i) => [widths[i], text]).sort((a, b) => b[0] - a[0]).slice(0, 6).map(pair => pair[1]);
    const linesAt = px => {
      probe.style.fontSize = `${px}px`;
      probe.style.width = probe.style.maxWidth = `${width - pad * px}px`;
      return Math.max(...longest.map(text => {
        probe.textContent = phrased(text);
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
    fitTimer = setTimeout(() => { fitSentences(); fitRedoCaption(); }, 120);
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
      node.textContent = ms < cfg.TIMER_SHOW_AFTER_MS ? '' : `· ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
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

  // actions: [{ label, value, variant: 'go' | 'plain' | 'ghost' | 'caution' | 'text', default }]
  // input: { label, placeholder, value } adds a text field; the result is then
  // { action, value }.
  // armMs: answers count only after this long (a question that must be answered after
  // looking waits longer: on touch screens its main answer lands where the finger was).
  function dialog({ title, body, actions, dismissValue, input, focus = true, armMs = 350 }) {
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
        button.className = action.variant === 'text' ? 'btn-text dialog-link' : `btn btn-lg btn-block btn-${action.variant || 'ghost'}`;
        button.textContent = action.label;
        button.addEventListener('click', () => {
          // Ignore presses that started before the dialog appeared: a finger still down,
          // or the second tap of a double tap.
          if (!state.armed || (V2S.input && V2S.input.clicksPaused && V2S.input.clicksPaused())) return;
          finishDialog(action.value);
        });
        actionsEl.appendChild(button);
        if (action.default || !defaultButton) defaultButton = button;
      });
      dialogState = state;
      // A dialog with a text field stays near the top (the keyboard covers the bottom).
      overlay.classList.toggle('has-input', Boolean(field));
      overlay.hidden = false;
      document.body.classList.add('has-dialog');
      overlay.removeAttribute('data-armed');
      setTimeout(() => {
        state.armed = true;
        if (dialogState === state) overlay.dataset.armed = 'true';
      }, armMs);
      // A key or finger still down from before the dialog does nothing in it.
      if (V2S.input && V2S.input.screenChanged) V2S.input.screenChanged();
      // Keyboard users get the default answer focused; on touch screens no button is
      // singled out by a focus ring.
      const keys = document.documentElement.classList.contains('has-keyboard');
      // Without a pre-chosen answer the dialog itself takes the focus, so no key reaches
      // the screen behind it.
      requestAnimationFrame(() => {
        const target = field || (keys && focus ? defaultButton : overlay.querySelector('.dialog'));
        if (target) target.focus();
      });
    });
  }

  function finishDialog(value) {
    const state = dialogState;
    if (!state) return;
    dialogState = null;
    el('dialog').hidden = true;
    document.body.classList.remove('has-dialog');
    if (document.activeElement && typeof document.activeElement.blur === 'function') document.activeElement.blur();
    // A double tap on the answer must not reach the screen behind (start a recording, or
    // press the button that was under the dialog): closing it counts as a screen change.
    if (V2S.input && V2S.input.guard) V2S.input.guard();
    if (V2S.input && V2S.input.screenChanged) V2S.input.screenChanged();
    state.resolve(state.field ? { action: value, value: state.field.value } : value);
  }

  document.addEventListener('keydown', event => {
    if (!dialogState) return;
    if (event.key === 'Escape' && dialogState.dismissValue !== undefined) {
      event.preventDefault();
      event.stopImmediatePropagation(); // Esc closes only the dialog, not Settings behind it
      finishDialog(dialogState.dismissValue);
    } else if (event.key === 'Enter' && dialogState.field && document.activeElement === dialogState.field && !event.repeat) {
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
    } else if (['Enter', 'PageDown', 'ArrowRight'].includes(event.key) || event.code === 'Space') {
      // Nothing is pre-chosen (some answers must follow a look, e.g. "Did the file
      // save?"): the first press (a key or a clicker) highlights the first answer, the
      // next one chooses it.
      if (document.activeElement !== el('dialog').querySelector('.dialog')) {
        // The choosing press is not the second half of a double press (a tremor).
        if (dialogState.highlightedAt && performance.now() - dialogState.highlightedAt < V2S.config.REVERSE_GUARD_MS) {
          event.preventDefault();
          event.stopPropagation();
        }
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      const first = el('dialogActions').querySelector('button');
      if (first) {
        first.focus();
        dialogState.highlightedAt = performance.now();
      }
    }
  }, true);

  const isDialogOpen = () => Boolean(dialogState);
  const isOverlayOpen = () => Boolean(dialogState) || !el('settingsPanel').hidden;

  // Something that removes or ends (caution): keeping things as they are is the main,
  // blue answer, and the action itself is plain grey (red means recording).
  function confirm({ title, body, yes, no, caution }) {
    return dialog({
      title,
      body,
      actions: caution
        ? [
          { label: yes || copy.settings.confirm, value: true, variant: 'ghost' },
          { label: no || copy.common.cancel, value: false, variant: 'go', default: true }
        ]
        : [
          { label: yes || copy.settings.confirm, value: true, variant: 'go' },
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

  // How to record (the ? button): the steps in order, then the fix for a mistake.
  function showHowto(keys) {
    const list = document.createElement('ol');
    list.className = 'steps';
    copy.howto.steps(keys).forEach(text => {
      const item = document.createElement('li');
      item.appendChild(richText(text));
      list.appendChild(item);
    });
    const fix = document.createElement('p');
    fix.className = 'steps-fix';
    fix.appendChild(richText(copy.howto.fix(keys)));
    return dialog({
      title: copy.howto.title,
      body: [list, fix],
      actions: [{ label: copy.howto.close, value: true, variant: 'go', default: true }],
      dismissValue: true
    });
  }

  function richText(text) {
    const span = document.createElement('span');
    String(text || '').split('**').forEach((part, index) => {
      if (!part) return;
      if (index % 2) {
        const bold = document.createElement('b');
        bold.textContent = part;
        span.appendChild(bold);
      } else {
        span.appendChild(document.createTextNode(part));
      }
    });
    return span;
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
    pauseClicks,
    clicksPaused: () => V2S.input.clicksPaused(),
    screen,
    setText,
    setSentences,
    setRich,
    setRecording,
    setWhere,
    labelTopbar,
    renderRecord,
    fitSentences,
    phrased,
    watchPreviewShape,
    dialog,
    confirm,
    alert,
    isDialogOpen,
    isOverlayOpen,
    helpText,
    showHowto,
    showCameraHelp,
    ICONS
  };
})();
