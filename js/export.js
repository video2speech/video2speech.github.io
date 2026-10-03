// Getting recordings off the device.
// - Folder mode (Chrome/Edge on a computer): every take is written to a chosen folder as
//   soon as it is saved; it leaves the browser's storage only after the write succeeded.
// - ZIP mode (iPad, phones, Safari, Firefox): a ZIP is downloaded; cached takes are
//   deleted only after the person confirms the file saved.
// Usable takes go at the top level with their legacy-compatible names; failed or
// discarded takes go in not_used/ so existing scripts never pick them up.
window.V2S = window.V2S || {};

V2S.exporter = (() => {
  const cfg = V2S.config;
  const { logEvent, downloadBlob, sanitize } = V2S.util;

  let folderHandle = null;
  let folderReady = false;
  let saveMode = 'zip';
  let writeChain = Promise.resolve();
  let folderFailures = 0;

  const folderSupported = () => typeof window.showDirectoryPicker === 'function';
  const sidecarName = fileName => fileName.replace(/\.[^.]+$/, '') + '.json';

  function isUsable(record) {
    const status = record.status || (record.metadata && record.metadata.status);
    if (status) return status === 'accepted' || status === 'qc_overridden';
    // Legacy-recorder takes: usable unless the legacy check asked for a retry.
    return !(record.metadata && record.metadata.requiresRetry);
  }

  function sidecar(record) {
    return {
      ...(record.metadata || {}),
      fileName: record.fileName,
      size: record.size,
      storedAt: record.timestamp,
      mimeType: record.mimeType,
      sentence: record.sentence,
      sentenceSet: record.sentenceSet,
      sentenceIndex: record.sentenceIndex,
      participantId: record.participantId || (record.metadata && record.metadata.participantId) || null,
      status: record.status || (record.metadata && record.metadata.status) || 'legacy'
    };
  }

  async function init() {
    saveMode = await V2S.storage.getSetting('saveMode', 'zip');
    folderHandle = await V2S.storage.getSetting('folderHandle', null);
    if (saveMode === 'folder' && !folderHandle) saveMode = 'zip';
  }

  const getSaveMode = () => saveMode;
  const folderName = () => (folderHandle ? folderHandle.name : null);
  const isFolderActive = () => saveMode === 'folder' && folderReady;
  const getFolderFailures = () => folderFailures;

  async function setSaveMode(mode) {
    saveMode = mode === 'folder' && folderHandle ? 'folder' : 'zip';
    await V2S.storage.setSetting('saveMode', saveMode);
    logEvent('save_mode', { mode: saveMode });
  }

  // Must run inside a click handler (the browser shows a folder picker).
  async function chooseFolder() {
    const handle = await window.showDirectoryPicker({ id: 'v2s-recordings', mode: 'readwrite', startIn: 'documents' });
    folderHandle = handle;
    await V2S.storage.setSetting('folderHandle', handle);
    folderReady = true;
    await setSaveMode('folder');
    return handle.name;
  }

  // Checks (and, inside a click handler, requests) write access to the saved folder.
  async function ensureFolderPermission(interactive) {
    if (saveMode !== 'folder' || !folderHandle) {
      folderReady = false;
      return false;
    }
    try {
      const options = { mode: 'readwrite' };
      let state = await folderHandle.queryPermission(options);
      if (state === 'prompt' && interactive) state = await folderHandle.requestPermission(options);
      folderReady = state === 'granted';
    } catch (error) {
      logEvent('folder_permission_error', { error: String(error) });
      folderReady = false;
    }
    return folderReady;
  }

  async function writeFile(directory, name, blob) {
    const fileHandle = await directory.getFileHandle(name, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(blob);
    await writable.close();
  }

  async function participantDirectory(participantId) {
    return folderHandle.getDirectoryHandle(sanitize(participantId || 'unknown').replace(/\s+/g, '_') || 'unknown', { create: true });
  }

  // Queues the folder write for a take already stored in IndexedDB (id), then removes the
  // cached copy. On failure the take stays cached and will go into the next ZIP.
  function queueFolderWrite(id, record, blob) {
    if (!isFolderActive()) return Promise.resolve(false);
    writeChain = writeChain.then(async () => {
      try {
        const base = await participantDirectory(record.participantId);
        const directory = isUsable(record) ? base : await base.getDirectoryHandle('not_used', { create: true });
        await writeFile(directory, record.fileName, blob);
        await writeFile(directory, sidecarName(record.fileName), new Blob([JSON.stringify(sidecar(record), null, 2)], { type: 'application/json' }));
        await V2S.storage.deleteTakes([id]);
        logEvent('folder_write', { fileName: record.fileName });
        return true;
      } catch (error) {
        folderFailures += 1;
        logEvent('folder_write_failed', { fileName: record.fileName, error: String(error && error.name || error) });
        return false;
      }
    });
    return writeChain;
  }

  // Writes the session log next to the recordings (folder mode only).
  async function writeSessionLog(participantId, summary) {
    if (!isFolderActive()) return false;
    try {
      await writeChain;
      const directory = await participantDirectory(participantId);
      const events = await V2S.storage.getAllEvents();
      const name = `session-${V2S.util.timestamp().slice(0, 8)}-${V2S.util.getSessionId() || 'unknown'}.json`;
      await writeFile(directory, name, new Blob([JSON.stringify({ ...summary, events }, null, 2)], { type: 'application/json' }));
      return true;
    } catch (error) {
      logEvent('session_log_failed', { error: String(error) });
      return false;
    }
  }

  const flushFolderWrites = () => writeChain;

  // Builds and downloads a ZIP of every cached take. Returns the ids it contains so the
  // caller can delete exactly those after the person confirms the download.
  async function downloadZip({ participantId, label, summary, onProgress }) {
    if (typeof JSZip !== 'function') throw new Error('The ZIP library did not load. Please reload the page.');
    const total = await V2S.storage.countTakes();
    if (!total) return { count: 0, ids: [] };
    const zip = new JSZip();
    const ids = [];
    const records = [];
    let done = 0;
    await V2S.storage.forEachTake(record => {
      const owner = record.participantId || null;
      // Another participant's takes on a shared device are kept apart in their own folder.
      const prefix = owner && participantId && owner !== participantId ? `${sanitize(owner).replace(/\s+/g, '_')}/` : '';
      const folder = prefix + (isUsable(record) ? '' : 'not_used/');
      const meta = sidecar(record);
      zip.file(folder + record.fileName, record.arrayBuffer, { binary: true, compression: 'STORE' });
      zip.file(folder + sidecarName(record.fileName), JSON.stringify(meta, null, 2));
      records.push({ path: folder + record.fileName, ...meta });
      ids.push(record.id);
      done += 1;
      if (onProgress) onProgress(done, total);
    });
    const events = await V2S.storage.getAllEvents();
    zip.file('manifest.json', JSON.stringify({
      appVersion: cfg.APP_VERSION,
      exportedAt: new Date().toISOString(),
      participantId: participantId || null,
      recordCount: records.length,
      summary: summary || null,
      records,
      events
    }, null, 2));
    const blob = await zip.generateAsync({ type: 'blob', compression: 'STORE', streamFiles: true });
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const owner = participantId ? `${sanitize(participantId).replace(/\s+/g, '_')}_` : '';
    const fileName = `${owner}video-recordings-${stamp}${label ? `_${label}` : ''}.zip`;
    downloadBlob(blob, fileName);
    logEvent('zip_download', { fileName, count: ids.length, size: blob.size });
    return { count: ids.length, ids, fileName, size: blob.size };
  }

  return {
    init,
    folderSupported,
    getSaveMode,
    setSaveMode,
    folderName,
    chooseFolder,
    ensureFolderPermission,
    isFolderActive,
    queueFolderWrite,
    flushFolderWrites,
    writeSessionLog,
    getFolderFailures,
    downloadZip,
    isUsable
  };
})();
