// Getting recordings off the device.
//
// Folder mode (Chrome/Edge on a computer): every recording goes into the folder chosen
// at setup — never anywhere else. A take leaves the browser's storage only after the
// file was written AND read back with the right size. If the browser no longer has
// permission for the folder, nothing is silently redirected: the screens ask for
// permission again (see main.js) and recordings wait safely in the browser meanwhile.
//
// ZIP mode (iPad, phones, Safari, Firefox, or when chosen): a ZIP per block. Where the
// browser offers a save dialog (Chrome/Edge), the person picks the location; elsewhere
// it is a normal download and cached takes are deleted only after "Yes, it saved".
//
// Layout in the folder or ZIP:
//   <participant>/                  usable takes (accepted, qc_overridden)
//   <participant>/not_used/         failed or discarded takes
//   previous-page-recordings/       takes the earlier recording page left unsaved
window.V2S = window.V2S || {};

V2S.exporter = (() => {
  const cfg = V2S.config;
  const { logEvent, downloadBlob, sanitize } = V2S.util;
  const LEGACY_FOLDER = 'previous-page-recordings';

  let folderHandle = null;
  let permission = 'none';       // 'granted' | 'prompt' | 'denied' | 'none'
  let saveMode = 'zip';
  let writeChain = Promise.resolve();
  let lastWriteFailed = false;
  let writing = 0;
  const listeners = new Set();

  const folderSupported = () => typeof window.showDirectoryPicker === 'function';
  const saveFileSupported = () => typeof window.showSaveFilePicker === 'function';
  const sidecarName = fileName => fileName.replace(/\.[^.]+$/, '') + '.json';
  const safeName = text => sanitize(text || 'unknown').replace(/\s+/g, '_') || 'unknown';

  function isUsable(record) {
    const status = record.status || (record.metadata && record.metadata.status);
    if (status) return status === 'accepted' || status === 'qc_overridden';
    // Legacy-recorder takes: usable unless the legacy check asked for a retry.
    return !(record.metadata && record.metadata.requiresRetry);
  }

  // Where a take belongs, relative to the folder or ZIP root.
  function destination(record) {
    const owner = record.participantId || null;
    const base = owner ? safeName(owner) : LEGACY_FOLDER;
    return isUsable(record) ? [base] : [base, 'not_used'];
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

  // ---- status for the screens ----
  function status() {
    return {
      mode: saveMode,
      folderName: folderHandle ? folderHandle.name : null,
      permission,
      saving: writing > 0,
      problem: saveMode === 'folder' && (permission !== 'granted' || lastWriteFailed)
    };
  }

  function onStatus(listener) {
    listeners.add(listener);
  }

  function emit() {
    const current = status();
    listeners.forEach(listener => {
      try { listener(current); } catch (error) { console.warn(error); }
    });
  }

  // ---- folder ----
  async function init() {
    saveMode = await V2S.storage.getSetting('saveMode', 'zip');
    folderHandle = await V2S.storage.getSetting('folderHandle', null);
    if (saveMode === 'folder' && !folderHandle) saveMode = 'zip';
    if (saveMode === 'folder') await checkPermission();
    emit();
  }

  const getSaveMode = () => saveMode;
  const folderName = () => (folderHandle ? folderHandle.name : null);
  const isFolderActive = () => saveMode === 'folder' && permission === 'granted';

  async function setSaveMode(mode) {
    saveMode = mode === 'folder' && folderHandle ? 'folder' : 'zip';
    await V2S.storage.setSetting('saveMode', saveMode);
    logEvent('save_mode', { mode: saveMode });
    emit();
  }

  async function checkPermission() {
    if (!folderHandle) {
      permission = 'none';
      return permission;
    }
    try {
      permission = await folderHandle.queryPermission({ mode: 'readwrite' });
    } catch (error) {
      permission = 'denied';
    }
    return permission;
  }

  // Call as the FIRST thing in a click handler: the browser only shows its folder
  // picker during a user action. Resolves to the folder name, or null if cancelled.
  async function chooseFolder() {
    let handle;
    try {
      handle = await window.showDirectoryPicker({ id: 'v2s-recordings', mode: 'readwrite', startIn: 'documents' });
    } catch (error) {
      if (error && error.name === 'AbortError') return null;
      throw error;
    }
    folderHandle = handle;
    permission = 'granted';
    lastWriteFailed = false;
    await V2S.storage.setSetting('folderHandle', handle);
    await setSaveMode('folder');
    logEvent('folder_chosen', { name: handle.name });
    return handle.name;
  }

  // Call as the FIRST thing in a click handler (the browser asks the person).
  async function requestFolderPermission() {
    if (!folderHandle) return 'none';
    try {
      permission = await folderHandle.requestPermission({ mode: 'readwrite' });
    } catch (error) {
      logEvent('folder_permission_error', { error: String(error && error.name || error) });
      permission = 'denied';
    }
    if (permission === 'granted') lastWriteFailed = false;
    logEvent('folder_permission', { permission });
    emit();
    return permission;
  }

  async function writeFile(directory, name, blob) {
    const fileHandle = await directory.getFileHandle(name, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(blob);
    await writable.close();
    const written = await fileHandle.getFile();
    if (written.size !== blob.size) throw new Error(`size check failed for ${name}: ${written.size} != ${blob.size}`);
  }

  async function directoryFor(parts) {
    let directory = folderHandle;
    for (const part of parts) directory = await directory.getDirectoryHandle(part, { create: true });
    return directory;
  }

  async function writeRecordToFolder(record, blob) {
    const directory = await directoryFor(destination(record));
    await writeFile(directory, record.fileName, blob || new Blob([record.arrayBuffer], { type: record.mimeType }));
    await writeFile(directory, sidecarName(record.fileName), new Blob([JSON.stringify(sidecar(record), null, 2)], { type: 'application/json' }));
  }

  function noteWriteFailure(error, fileName) {
    lastWriteFailed = true;
    const name = error && error.name;
    if (name === 'NotAllowedError' || name === 'SecurityError') permission = 'prompt';
    logEvent('folder_write_failed', { fileName, error: String(name || error) });
  }

  // Writes one stored take to the folder, then removes the cached copy. If writing
  // fails, the take stays cached and the screens show that the folder needs attention.
  function queueFolderWrite(id, record, blob) {
    if (!isFolderActive()) {
      emit();
      return Promise.resolve(false);
    }
    writing += 1;
    emit();
    writeChain = writeChain.then(async () => {
      try {
        await writeRecordToFolder(record, blob);
        await V2S.storage.deleteTakes([id]);
        lastWriteFailed = false;
        logEvent('folder_write', { fileName: record.fileName });
        return true;
      } catch (error) {
        noteWriteFailure(error, record.fileName);
        return false;
      } finally {
        writing -= 1;
        emit();
      }
    });
    return writeChain;
  }

  // Writes every cached take (including ones the earlier page left behind) into the
  // folder. Returns { written, failed }.
  async function flushPendingToFolder(onProgress) {
    if (!isFolderActive()) return { written: 0, failed: await V2S.storage.countTakes() };
    await writeChain;
    const ids = (await V2S.storage.listTakeSummaries()).map(take => take.id);
    let written = 0;
    let failed = 0;
    writing += 1;
    emit();
    try {
      for (const id of ids) {
        const record = await V2S.storage.getTake(id);
        if (!record) continue;
        try {
          await writeRecordToFolder(record);
          await V2S.storage.deleteTakes([id]);
          written += 1;
        } catch (error) {
          noteWriteFailure(error, record.fileName);
          failed += 1;
          if (!isFolderActive()) break;
        }
        if (onProgress) onProgress(written + failed, ids.length);
      }
      if (!failed) lastWriteFailed = false;
    } finally {
      writing -= 1;
      emit();
    }
    logEvent('folder_flush', { written, failed });
    return { written, failed };
  }

  // Writes the session log next to the recordings (folder mode only).
  async function writeSessionLog(participantId, summary) {
    if (!isFolderActive()) return false;
    try {
      await writeChain;
      const directory = await directoryFor([safeName(participantId)]);
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

  // Storage failed for a take: get it to safety some other way.
  async function rescueTake(blob, fileName, metadata) {
    if (isFolderActive()) {
      try {
        await writeRecordToFolder({ fileName, metadata, mimeType: blob.type, participantId: metadata.participantId, status: metadata.status }, blob);
        logEvent('rescue_folder', { fileName });
        return;
      } catch (error) {
        noteWriteFailure(error, fileName);
      }
    }
    downloadBlob(blob, fileName);
    downloadBlob(new Blob([JSON.stringify(metadata, null, 2)], { type: 'application/json' }), sidecarName(fileName));
    logEvent('rescue_download', { fileName });
  }

  // ---- ZIP ----
  function zipFileName(participantId, owners, label) {
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const onlyEarlierPage = owners.size === 1 && owners.has(null);
    if (onlyEarlierPage) return `${LEGACY_FOLDER}-${stamp}.zip`;
    const owner = participantId ? `${safeName(participantId)}_` : '';
    return `${owner}video-recordings-${stamp}${label ? `_${label}` : ''}.zip`;
  }

  // Call as the FIRST thing in a click handler. Returns a file handle where the browser
  // can save directly (Chrome/Edge), null where it will be a normal download, or
  // undefined if the person cancelled the save dialog.
  async function pickZipTarget(suggestedName) {
    if (!saveFileSupported()) return null;
    try {
      return await window.showSaveFilePicker({
        suggestedName,
        types: [{ description: 'ZIP archive', accept: { 'application/zip': ['.zip'] } }]
      });
    } catch (error) {
      if (error && error.name === 'AbortError') return undefined;
      logEvent('save_picker_failed', { error: String(error && error.name || error) });
      return null;
    }
  }

  async function previewZipName(participantId, label) {
    const owners = new Set();
    (await V2S.storage.listTakeSummaries()).forEach(take => owners.add(take.participantId || null));
    return zipFileName(participantId, owners, label);
  }

  // Builds the ZIP of every cached take and saves it to `target` (from pickZipTarget)
  // or downloads it. Returns { count, ids, fileName, verified }.
  async function saveZip({ participantId, label, summary, target, fileName, onProgress }) {
    if (typeof JSZip !== 'function') throw new Error('The ZIP library did not load. Please reload the page.');
    const total = await V2S.storage.countTakes();
    if (!total) return { count: 0, ids: [] };
    const zip = new JSZip();
    const ids = [];
    const records = [];
    const owners = new Set();
    let done = 0;
    await V2S.storage.forEachTake(record => {
      owners.add(record.participantId || null);
      const path = destination(record).join('/') + '/';
      const meta = sidecar(record);
      zip.file(path + record.fileName, record.arrayBuffer, { binary: true, compression: 'STORE' });
      zip.file(path + sidecarName(record.fileName), JSON.stringify(meta, null, 2));
      records.push({ path: path + record.fileName, ...meta });
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
    const name = fileName || zipFileName(participantId, owners, label);
    const blob = await zip.generateAsync({ type: 'blob', compression: 'STORE', streamFiles: true });
    let verified = false;
    if (target) {
      const writable = await target.createWritable();
      await writable.write(blob);
      await writable.close();
      verified = (await target.getFile()).size === blob.size;
    } else {
      downloadBlob(blob, name);
    }
    logEvent('zip_saved', { fileName: target ? target.name : name, count: ids.length, size: blob.size, verified });
    return { count: ids.length, ids, fileName: target ? target.name : name, verified };
  }

  return {
    init,
    status,
    onStatus,
    folderSupported,
    getSaveMode,
    setSaveMode,
    folderName,
    checkPermission,
    chooseFolder,
    requestFolderPermission,
    isFolderActive,
    queueFolderWrite,
    flushPendingToFolder,
    flushFolderWrites,
    writeSessionLog,
    rescueTake,
    pickZipTarget,
    previewZipName,
    saveZip,
    isUsable
  };
})();
