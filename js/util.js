// Small shared helpers: DOM access, timing, naming, platform detection and the
// session event log.
window.V2S = window.V2S || {};

V2S.util = (() => {
  const el = id => document.getElementById(id);
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

  function uid() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  }

  function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const value = bytes / (1024 ** exponent);
    return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
  }

  // Same file-name rules as the legacy recorder, so existing scripts keep working.
  function sanitize(text) {
    return String(text).replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, ' ').trim();
  }

  function timestamp(date = new Date()) {
    const pad = n => String(n).padStart(2, '0');
    return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
  }

  function percentile(values, fraction) {
    if (!values.length) return 0;
    const sorted = Array.from(values).sort((a, b) => a - b);
    const position = Math.min(sorted.length - 1, Math.max(0, Math.floor(fraction * (sorted.length - 1))));
    return sorted[position];
  }

  function detectPlatform() {
    const ua = navigator.userAgent || '';
    const touchMac = /Macintosh/.test(ua) && navigator.maxTouchPoints > 1; // iPadOS reports as a Mac
    const ios = /iPhone|iPad|iPod/.test(ua) || touchMac;
    const android = /Android/.test(ua);
    const edge = /Edg\//.test(ua);
    const chrome = /Chrome\//.test(ua) && !edge && !/OPR\//.test(ua);
    const safari = /Safari\//.test(ua) && !/Chrome\/|Chromium\/|CriOS\/|FxiOS\/|EdgiOS\//.test(ua);
    return {
      ios,
      android,
      mobile: ios || android,
      mac: /Macintosh/.test(ua) && !touchMac,
      windows: /Windows/.test(ua),
      safari,
      chrome,
      edge
    };
  }

  const platform = detectPlatform();

  // Session event log: kept in memory and mirrored to IndexedDB by storage.js.
  const events = [];
  let sessionId = null;
  let sessionStartedAt = performance.now();
  const eventListeners = [];

  function startSession() {
    sessionId = uid();
    sessionStartedAt = performance.now();
    logEvent('session_start', { platform, userAgent: navigator.userAgent });
    return sessionId;
  }

  function sinceSessionStart() {
    return Math.round(performance.now() - sessionStartedAt);
  }

  function logEvent(type, data = {}) {
    const entry = { at: new Date().toISOString(), ms: sinceSessionStart(), sessionId, type, ...data };
    events.push(entry);
    if (events.length > V2S.config.EVENT_LOG_LIMIT) events.shift();
    eventListeners.forEach(listener => {
      try { listener(entry); } catch (error) { console.warn('Event listener failed', error); }
    });
    return entry;
  }

  function onEvent(listener) {
    eventListeners.push(listener);
  }

  function getSessionId() {
    return sessionId;
  }

  function getEvents() {
    return events.slice();
  }

  function downloadBlob(blob, fileName) {
    const link = document.createElement('a');
    link.download = fileName;
    link.href = URL.createObjectURL(blob);
    document.body.appendChild(link);
    link.click();
    link.remove();
    const url = link.href;
    setTimeout(() => URL.revokeObjectURL(url), 120000);
  }

  return {
    el,
    sleep,
    uid,
    formatBytes,
    sanitize,
    timestamp,
    percentile,
    platform,
    startSession,
    sinceSessionStart,
    logEvent,
    onEvent,
    getSessionId,
    getEvents,
    downloadBlob
  };
})();
