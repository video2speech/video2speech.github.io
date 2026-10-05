// Getting recordings off the device.
//
// Folder mode (Chrome/Edge on a computer): every recording goes into the folder chosen
// at setup — never anywhere else. A take leaves the browser's storage only after the
// file was written AND read back with the right size. If the browser no longer has
// permission for the folder, nothing is silently redirected: the screens ask for
// permission again (see main.js) and recordings wait safely in the browser meanwhile.
//
// ZIP mode (iPad, phones, Safari, Firefox, or when chosen): a ZIP per part (at most
// ZIP_MAX_TAKES recordings each). Where the browser offers a save dialog (Chrome/Edge),
// the person picks the location; elsewhere it is a normal download followed by "Did the
// file save?". After a confirmed save the recordings stay on the device as backup copies
// (left out of later ZIPs) until space is needed, so a mistaken "Yes" loses nothing.
//
// Layout in the folder or ZIP:
//   <participant>/                  exactly one usable take per sentence and round
//                                   (accepted, qc_overridden), each with a JSON sidecar
//   <participant>/not_used/         failed or discarded takes, and takes replaced by a
//                                   newer take of the same sentence (superseded)
//   <participant>/logs/             session logs, superseded.json (every replaced take)
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
    const ids = await V2S.storage.takeIds();
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
    const lists = await V2S.storage.allSupersedeLists().catch(() => []);
    for (const { participantId, setKey, list } of lists) {
      if (list.some(item => !item.done)) await applySuperseded(participantId, setKey);
    }
    return { written, failed };
  }

  // Writes this session's log into <participant>/logs/ (folder mode only).
  async function writeSessionLog(participantId, summary) {
    if (!isFolderActive()) return false;
    try {
      await writeChain;
      const directory = await directoryFor([safeName(participantId), 'logs']);
      const events = V2S.util.getEvents();
      const name = `session-${V2S.util.timestamp().slice(0, 8)}-${V2S.util.getSessionId() || 'unknown'}.json`;
      await writeFile(directory, name, new Blob([JSON.stringify({ ...summary, events }, null, 2)], { type: 'application/json' }));
      return true;
    } catch (error) {
      logEvent('session_log_failed', { error: String(error) });
      return false;
    }
  }

  const flushFolderWrites = () => writeChain;

  // A usable take that was replaced by a newer take of the same sentence (Redo, going
  // back, practising again) must not stay among the usable recordings. Storage marks it
  // "superseded" while it is cached (it is then written straight into not_used/) and
  // lists it either way; here the folder copies are moved: copied into not_used/ with the
  // sidecar updated, verified, then removed. Queued behind any write still in progress.
  // Every job on the folder chain catches its own errors: one failed write must never stop
  // the writes queued after it (the chain would stay rejected for the rest of the visit).
  function chain(job, label) {
    writeChain = writeChain.then(job).catch(error => {
      noteWriteFailure(error, label);
      return false;
    });
    return writeChain;
  }

  function applySuperseded(participantId, setKey) {
    if (saveMode !== 'folder') return Promise.resolve(false);
    return chain(async () => {
      if (!isFolderActive()) return false;
      const list = await V2S.storage.getSupersedeList(participantId, setKey);
      const open = list.filter(item => !item.done);
      if (!open.length) return true;
      const cached = await V2S.storage.cachedNames(open.map(item => item.sentenceIndex));
      const finished = [];
      for (const item of open) {
        if (cached.has(item.fileName)) continue; // still on the device: it will go to not_used/
        try {
          await moveToNotUsed(participantId, item.fileName, item.supersededBy);
          finished.push(item.fileName);
        } catch (error) {
          noteWriteFailure(error, item.fileName);
          if (!isFolderActive()) break;
        }
      }
      if (finished.length) await V2S.storage.markSupersedeDone(participantId, setKey, finished);
      await writeSupersedeLog(participantId);
      return true;
    }, 'superseded.json');
  }

  // logs/superseded.json lists every replaced recording of the participant, all sentence
  // sets together (each write replaces the whole file).
  async function writeSupersedeLog(participantId) {
    const lists = (await V2S.storage.allSupersedeLists()).filter(item => item.participantId === participantId && item.list.length);
    if (!lists.length) return;
    const directory = await directoryFor([safeName(participantId), 'logs']);
    await writeFile(directory, 'superseded.json', new Blob([JSON.stringify(supersedeDocument(participantId, lists), null, 2)], { type: 'application/json' }));
  }

  function supersedeDocument(participantId, lists) {
    return {
      about: 'Recordings replaced by a newer recording of the same sentence (in the same round). Use the newer one; the replaced one is in not_used/ (or in an earlier ZIP file).',
      participantId,
      updatedAt: new Date().toISOString(),
      replaced: lists.flatMap(({ setKey, list }) => list.map(item => ({
        fileName: item.fileName,
        supersededBy: item.supersededBy,
        sentenceSet: setKey,
        sentenceIndex: item.sentenceIndex,
        sentence: item.sentence || null,
        round: item.round || null,
        at: item.at
      })))
    };
  }

  // Moves one file (and its sidecar) from <participant>/ to <participant>/not_used/.
  // Nothing to do if it is not among the usable recordings (already moved, or never there).
  async function moveToNotUsed(participantId, fileName, supersededBy) {
    const base = participantId ? safeName(participantId) : LEGACY_FOLDER;
    const source = await directoryFor([base]);
    let fileHandle;
    try {
      fileHandle = await source.getFileHandle(fileName);
    } catch (error) {
      return false;
    }
    const target = await directoryFor([base, 'not_used']);
    await writeFile(target, fileName, await fileHandle.getFile());
    const sideName = sidecarName(fileName);
    let meta = {};
    try {
      meta = JSON.parse(await (await (await source.getFileHandle(sideName)).getFile()).text());
    } catch (error) { /* no sidecar */ }
    meta = { ...meta, status: 'superseded', usable: false, supersededBy };
    await writeFile(target, sideName, new Blob([JSON.stringify(meta, null, 2)], { type: 'application/json' }));
    await source.removeEntry(fileName);
    try { await source.removeEntry(sideName); } catch (error) { /* no sidecar */ }
    logEvent('superseded_moved', { fileName, supersededBy });
    return true;
  }

  // The browser could not store a take (folder mode only): write it straight into the
  // folder, with its full sidecar. Returns false if that is not possible either.
  async function rescueTake(blob, info, replaced) {
    if (!isFolderActive()) return false;
    try {
      await writeRecordToFolder({ ...info, mimeType: info.mimeType || blob.type }, blob);
      logEvent('rescue_folder', { fileName: info.fileName });
      if (replaced && replaced.fileName) chain(() => moveToNotUsed(info.participantId, replaced.fileName, info.fileName), replaced.fileName);
      return true;
    } catch (error) {
      noteWriteFailure(error, info.fileName);
      return false;
    }
  }

  // ---- ZIP ----
  function zipFileName(participantId, owners, label) {
    const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
    const onlyEarlierPage = owners.size === 1 && owners.has(null);
    if (onlyEarlierPage) return `${LEGACY_FOLDER}-${stamp}.zip`;
    const owner = participantId ? `${safeName(participantId)}_` : '';
    return `${owner}${label ? `${label}_` : ''}${stamp}.zip`;
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

  // Builds a ZIP of the recordings not saved yet (oldest first, at most ZIP_MAX_TAKES, so
  // the file stays small enough for phones and tablets) — or of the backup copies when
  // `backups` is set — and saves it to `target` (from pickZipTarget) or downloads it.
  // Returns { count, ids, fileName, verified, remaining }.
  async function saveZip({ participantId, label, summary, target, fileName, onProgress, backups = false }) {
    if (typeof JSZip !== 'function') throw new Error('The ZIP library did not load. Please reload the page.');
    const exported = new Set(await V2S.storage.exportedIds());
    const wanted = (await V2S.storage.takeIds()).filter(id => exported.has(id) === backups);
    if (!wanted.length) return { count: 0, ids: [], remaining: 0 };
    const chosen = wanted.slice(0, cfg.ZIP_MAX_TAKES);
    const zip = new JSZip();
    const ids = [];
    const records = [];
    const owners = new Set();
    for (const id of chosen) {
      const record = await V2S.storage.getTake(id); // one video in memory at a time while reading
      if (!record) continue;
      owners.add(record.participantId || null);
      const path = destination(record).join('/') + '/';
      const meta = sidecar(record);
      zip.file(path + record.fileName, record.arrayBuffer, { binary: true, compression: 'STORE' });
      zip.file(path + sidecarName(record.fileName), JSON.stringify(meta, null, 2));
      records.push({ path: path + record.fileName, ...meta });
      ids.push(record.id);
      if (onProgress) onProgress(ids.length, chosen.length);
    }
    // Every replaced take so far, for each participant in this ZIP: the latest ZIP always
    // carries the full list, including takes that left the device in an earlier ZIP.
    const superseded = {};
    const lists = await V2S.storage.allSupersedeLists();
    owners.forEach(owner => {
      if (!owner) return;
      const own = lists.filter(item => item.participantId === owner && item.list.length);
      if (!own.length) return;
      superseded[owner] = supersedeDocument(owner, own);
      zip.file(`${safeName(owner)}/logs/superseded.json`, JSON.stringify(superseded[owner], null, 2));
    });
    const events = await V2S.storage.getAllEvents();
    zip.file('manifest.json', JSON.stringify({
      appVersion: cfg.APP_VERSION,
      exportedAt: new Date().toISOString(),
      participantId: participantId || null,
      recordCount: records.length,
      backupCopies: backups,
      summary: summary || null,
      records,
      superseded,
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
    logEvent('zip_saved', { fileName: target ? target.name : name, count: ids.length, size: blob.size, verified, backups });
    return { count: ids.length, ids, fileName: target ? target.name : name, verified, remaining: wanted.length - ids.length };
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
    applySuperseded,
    writeSessionLog,
    rescueTake,
    pickZipTarget,
    saveZip,
    isUsable
  };
})();
