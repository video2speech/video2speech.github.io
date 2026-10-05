// IndexedDB access.
// - VideoRecorderDB (v2) is shared with the legacy recorder: same stores, same record
//   shape, never upgraded, so the legacy page can still open and export it.
// - V2SAppState holds settings, the chosen folder handle and the event log.
window.V2S = window.V2S || {};

V2S.storage = (() => {
  const cfg = V2S.config;
  let videoDb = null;
  let stateDb = null;

  function promisify(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // Runs fn inside a transaction and resolves once the transaction has committed.
  // If fn returns an IDBRequest, the promise resolves with that request's result.
  function transact(db, storeNames, mode, fn) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeNames, mode);
      let outcome;
      tx.oncomplete = () => resolve(outcome);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('Transaction aborted'));
      try {
        const value = fn(tx);
        if (value instanceof IDBRequest) {
          value.onsuccess = () => { outcome = value.result; };
        } else {
          outcome = value;
        }
      } catch (error) {
        try { tx.abort(); } catch (abortError) { /* already finished */ }
        reject(error);
      }
    });
  }

  function openVideoDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(cfg.DB_NAME, cfg.DB_VERSION);
      request.onerror = () => reject(request.error);
      request.onblocked = () => reject(new Error('Recording storage is open in another tab. Please close other tabs.'));
      request.onsuccess = () => resolve(request.result);
      request.onupgradeneeded = event => {
        // Identical to the legacy recorder's schema.
        const db = event.target.result;
        if (!db.objectStoreNames.contains('videos')) {
          const store = db.createObjectStore('videos', { keyPath: 'id', autoIncrement: true });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('sentence', 'sentence', { unique: false });
          store.createIndex('sentenceSet', 'sentenceSet', { unique: false });
          store.createIndex('sentenceIndex', 'sentenceIndex', { unique: false });
        }
        if (!db.objectStoreNames.contains('progress')) {
          db.createObjectStore('progress', { keyPath: 'sentenceSet' });
        }
      };
    });
  }

  function openStateDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(cfg.STATE_DB_NAME, cfg.STATE_DB_VERSION);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
      request.onupgradeneeded = event => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains('kv')) db.createObjectStore('kv');
        if (!db.objectStoreNames.contains('events')) {
          db.createObjectStore('events', { keyPath: 'seq', autoIncrement: true });
        }
      };
    });
  }

  async function init() {
    if (!window.indexedDB) throw new Error('This browser has no storage for recordings.');
    videoDb = await openVideoDb();
    stateDb = await openStateDb();
  }

  // ---- settings (key/value) ----
  async function getSetting(key, fallback = null) {
    const tx = stateDb.transaction(['kv'], 'readonly');
    const value = await promisify(tx.objectStore('kv').get(key));
    return value === undefined ? fallback : value;
  }

  function setSetting(key, value) {
    return transact(stateDb, ['kv'], 'readwrite', tx => { tx.objectStore('kv').put(value, key); });
  }

  function deleteSetting(key) {
    return transact(stateDb, ['kv'], 'readwrite', tx => { tx.objectStore('kv').delete(key); });
  }

  // ---- progress ----
  const progressKey = (participantId, setKey) => `${participantId}::${setKey}`;

  async function getProgress(key) {
    const tx = videoDb.transaction(['progress'], 'readonly');
    return (await promisify(tx.objectStore('progress').get(key))) || null;
  }

  function putProgress(record) {
    return transact(videoDb, ['progress'], 'readwrite', tx => { tx.objectStore('progress').put(record); });
  }

  function deleteProgress(key) {
    return transact(videoDb, ['progress'], 'readwrite', tx => { tx.objectStore('progress').delete(key); });
  }

  // Progress the legacy recorder left on this device, if nobody has claimed it yet.
  async function findUnclaimedLegacyProgress(setKey) {
    if (await getSetting(`legacyClaimedBy:${setKey}`)) return null;
    let legacy = await getProgress(setKey);
    const alias = cfg.SETS[setKey] && cfg.SETS[setKey].legacyProgressKey;
    if (!legacy && alias) legacy = await getProgress(alias);
    if (!legacy || !Number.isFinite(Number(legacy.currentIndex))) return null;
    return legacy;
  }

  // Creates this participant's progress record. The first participant on a device
  // claims the legacy slot (optionally continuing from it); later ones start fresh.
  async function createParticipantProgress(participantId, setKey, legacy = null) {
    // Someone who already learnt how it works (on another sentence set) is not taught again.
    const others = await Promise.all(Object.keys(cfg.SETS).filter(key => key !== setKey)
      .map(key => getProgress(progressKey(participantId, key))));
    const coached = others.some(other => other && other.coachDone);
    const toldHow = others.some(other => other && other.howtoSeen);
    const record = {
      sentenceSet: progressKey(participantId, setKey),
      participantId,
      set: setKey,
      currentIndex: legacy ? Math.max(0, Number(legacy.currentIndex) || 0) : 0,
      repetitionCount: legacy ? Number(legacy.repetitionCount) || 0 : 0,
      round: legacy ? roundOf(legacy) : 1,
      completed: legacy ? Boolean(legacy.completed) : false,
      completedAt: legacy ? legacy.completedAt || null : null,
      tutorialTakes: 0,
      coachDone: coached,
      howtoSeen: toldHow,
      takeCounts: {},
      usable: {},
      adoptedFromLegacy: Boolean(legacy),
      createdAt: new Date().toISOString(),
      timestamp: new Date().toISOString()
    };
    await putProgress(record);
    if (!(await getSetting(`legacyClaimedBy:${setKey}`))) {
      await setSetting(`legacyClaimedBy:${setKey}`, participantId);
    }
    return record;
  }

  // The pass through the sentence set that new recordings belong to ("repeat<n>" in file
  // names). repetitionCount keeps the legacy meaning: passes completed. After the last
  // sentence the completed pass stays current (its last sentence can still be redone)
  // until the participant moves on (startNewRound).
  function roundOf(progress) {
    if (Number.isInteger(progress.round) && progress.round > 0) return progress.round;
    const done = Number(progress.repetitionCount) || 0;
    return progress.completed ? Math.max(1, done) : done + 1;
  }

  // Saves the participant record and mirrors it to the legacy key so the legacy
  // recorder (fallback page) continues from the same sentence on this device.
  async function saveParticipantProgress(record) {
    record.timestamp = new Date().toISOString();
    await transact(videoDb, ['progress'], 'readwrite', tx => {
      const store = tx.objectStore('progress');
      store.put(record);
      store.put(legacyMirror(record));
    });
  }

  function legacyMirror(record) {
    return {
      sentenceSet: record.set,
      currentIndex: record.currentIndex,
      repetitionCount: record.repetitionCount || 0,
      completed: Boolean(record.completed),
      completedAt: record.completedAt || null,
      timestamp: record.timestamp,
      mirroredFrom: record.participantId
    };
  }

  // ---- takes (the "videos" store) ----
  // One usable recording per sentence: when a usable take replaces an earlier usable take
  // of the same sentence (Redo, going back, practising again), the earlier one becomes
  // "superseded" in the SAME transaction if it is still on this device. If it has already
  // left the device (written to the folder, or exported in a ZIP), its name goes on the
  // participant's supersede list, also in this transaction; the folder copy is then moved
  // to not_used/, and every later ZIP lists it in superseded.json.
  const supersedeKey = (participantId, setKey) => `supersede::${participantId}::${setKey}`;

  // Stores a take and the progress it causes in ONE transaction: either both are saved
  // or neither, so progress can never move past a take that was not stored.
  // `supersede` ({ fileName }) is the sentence's earlier usable take in this round: it is
  // marked superseded here if it is still on this device, and always listed.
  function commitTake(record, progress, supersede = null) {
    progress.timestamp = new Date().toISOString();
    return new Promise((resolve, reject) => {
      const tx = videoDb.transaction(['videos', 'progress'], 'readwrite');
      const videos = tx.objectStore('videos');
      const progressStore = tx.objectStore('progress');
      let newId = null;
      progressStore.put(progress);
      progressStore.put(legacyMirror(progress));
      const add = videos.add(record);
      add.onsuccess = () => { newId = add.result; };
      if (supersede && supersede.fileName) {
        const key = supersedeKey(record.participantId, progress.set);
        const get = progressStore.get(key);
        get.onsuccess = () => {
          const list = (get.result && get.result.list) || [];
          if (!list.some(item => item.fileName === supersede.fileName)) {
            list.push({ fileName: supersede.fileName, supersededBy: record.fileName, sentenceIndex: record.sentenceIndex, sentence: record.sentence, round: progress.round || null, at: new Date().toISOString(), done: false });
          }
          progressStore.put({ sentenceSet: key, kind: 'supersede', list, timestamp: new Date().toISOString() });
        };
        const cursorRequest = videos.index('sentenceIndex').openCursor(IDBKeyRange.only(record.sentenceIndex));
        cursorRequest.onsuccess = () => {
          const cursor = cursorRequest.result;
          if (!cursor) return;
          if (cursor.value.fileName === supersede.fileName) {
            const old = cursor.value;
            cursor.update({
              ...old,
              status: 'superseded',
              metadata: { ...(old.metadata || {}), status: 'superseded', usable: false, supersededBy: record.fileName }
            });
          }
          cursor.continue();
        };
      }
      tx.oncomplete = () => resolve(newId);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error || new Error('Transaction aborted'));
    });
  }

  async function getSupersedeList(participantId, setKey) {
    const record = await getProgress(supersedeKey(participantId, setKey));
    return (record && record.list) || [];
  }

  // Every supersede list on this device, by participant (for ZIPs, which may hold
  // several participants' recordings).
  async function allSupersedeLists() {
    const tx = videoDb.transaction(['progress'], 'readonly');
    const records = await promisify(tx.objectStore('progress').getAll());
    return records.filter(record => String(record.sentenceSet).startsWith('supersede::'))
      .map(record => {
        const [, participantId, setKey] = String(record.sentenceSet).split('::');
        return { participantId, setKey, list: record.list || [] };
      });
  }

  // Entries stay listed for good (they are the record of what was replaced); `done` means
  // the folder no longer holds the file among the usable recordings.
  function markSupersedeDone(participantId, setKey, fileNames) {
    const key = supersedeKey(participantId, setKey);
    return transact(videoDb, ['progress'], 'readwrite', tx => {
      const store = tx.objectStore('progress');
      const request = store.get(key);
      request.onsuccess = () => {
        if (!request.result) return;
        store.put({ ...request.result, list: request.result.list.map(item => (fileNames.includes(item.fileName) ? { ...item, done: true } : item)) });
      };
    });
  }

  // ---- ZIP backups ----
  // In ZIP mode a confirmed save does not delete the recordings: they stay on the device as
  // backup copies, are left out of later ZIPs, and are removed only when the device needs
  // the space. A mistaken "Yes, it saved" therefore loses nothing. The list of backup ids
  // lives in the settings store (the video records are never rewritten: each holds its
  // whole video).
  async function exportedIds() {
    return getSetting('exportedTakeIds', []);
  }

  // The most recent confirmed ZIP is remembered separately: its copies are never deleted
  // automatically (only after the participant confirms that file is saved).
  async function markExported(ids, fileName = null) {
    const list = await exportedIds();
    await setSetting('exportedTakeIds', [...list, ...ids.filter(id => !list.includes(id))]);
    await setSetting('lastExport', { ids: ids.slice(), fileName, at: new Date().toISOString() });
  }

  // Backup ids that still exist, oldest first (ids of takes deleted elsewhere — e.g. by the
  // earlier page's Save All or Clear Storage — are dropped from the list).
  async function liveExportedIds() {
    const [list, present] = await Promise.all([exportedIds(), takeIds()]);
    const existing = new Set(present);
    const live = list.filter(id => existing.has(id));
    if (live.length !== list.length) await setSetting('exportedTakeIds', live);
    return live;
  }

  // Deletes backup copies, oldest first; with keepLatest the most recent ZIP's copies stay.
  // Returns how many were removed.
  async function pruneExported(count, { keepLatest = false } = {}) {
    const latest = keepLatest ? new Set(((await getSetting('lastExport', null)) || { ids: [] }).ids) : new Set();
    const remove = (await liveExportedIds()).filter(id => !latest.has(id)).slice(0, Math.max(0, count));
    if (remove.length) await deleteTakes(remove);
    return remove.length;
  }

  // The most recent ZIP's copies still on the device: { fileName, ids }.
  async function latestBackup() {
    const last = await getSetting('lastExport', null);
    if (!last) return { fileName: null, ids: [] };
    const live = new Set(await liveExportedIds());
    return { fileName: last.fileName, ids: last.ids.filter(id => live.has(id)) };
  }

  // The participant confirmed the most recent ZIP is saved: its copies may go.
  async function releaseLatestBackup() {
    const { ids } = await latestBackup();
    if (ids.length) await deleteTakes(ids);
    await deleteSetting('lastExport');
    return ids.length;
  }

  // Takes not saved anywhere yet: every cached take that is not a backup copy.
  async function countUnsaved() {
    const [ids, exported] = await Promise.all([takeIds(), exportedIds()]);
    const saved = new Set(exported);
    return ids.filter(id => !saved.has(id)).length;
  }

  function addTake(record) {
    return transact(videoDb, ['videos'], 'readwrite', tx => tx.objectStore('videos').add(record));
  }

  async function getTake(id) {
    const tx = videoDb.transaction(['videos'], 'readonly');
    return (await promisify(tx.objectStore('videos').get(id))) || null;
  }

  async function deleteTakes(ids) {
    await transact(videoDb, ['videos'], 'readwrite', tx => {
      const store = tx.objectStore('videos');
      ids.forEach(id => store.delete(id));
    });
    const exported = await getSetting('exportedTakeIds', []);
    if (exported.some(id => ids.includes(id))) await setSetting('exportedTakeIds', exported.filter(id => !ids.includes(id)));
  }

  // The ids of every cached take, oldest first, without loading the videos.
  async function takeIds() {
    const tx = videoDb.transaction(['videos'], 'readonly');
    return promisify(tx.objectStore('videos').getAllKeys());
  }

  // File names of the cached takes of the given sentences (loads only those takes).
  async function cachedNames(sentenceIndexes) {
    const names = new Set();
    const tx = videoDb.transaction(['videos'], 'readonly');
    const index = tx.objectStore('videos').index('sentenceIndex');
    for (const i of new Set(sentenceIndexes)) {
      (await promisify(index.getAll(IDBKeyRange.only(i)))).forEach(record => names.add(record.fileName));
    }
    return names;
  }

  function updateTake(id, patch) {
    return transact(videoDb, ['videos'], 'readwrite', tx => {
      const store = tx.objectStore('videos');
      const request = store.get(id);
      request.onsuccess = () => {
        if (request.result) store.put({ ...request.result, ...patch });
      };
    });
  }

  // Rewrites one cached take with fn(record); does nothing if it is no longer cached.
  function modifyTake(id, fn) {
    return transact(videoDb, ['videos'], 'readwrite', tx => {
      const store = tx.objectStore('videos');
      const request = store.get(id);
      request.onsuccess = () => {
        if (request.result) store.put(fn(request.result));
      };
    });
  }

  // Visits every cached take one at a time (each record holds its video bytes).
  function forEachTake(visitor) {
    return new Promise((resolve, reject) => {
      const tx = videoDb.transaction(['videos'], 'readonly');
      const request = tx.objectStore('videos').openCursor();
      request.onsuccess = () => {
        const cursor = request.result;
        if (!cursor) return;
        try {
          visitor(cursor.value);
          cursor.continue();
        } catch (error) {
          reject(error);
        }
      };
      request.onerror = () => reject(request.error);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async function countTakes() {
    const tx = videoDb.transaction(['videos'], 'readonly');
    return promisify(tx.objectStore('videos').count());
  }

  // Reads every cached video: use only where the cache is small (folder mode). For counts,
  // use takeIds / exportedIds / countUnsaved.
  async function listTakeSummaries() {
    const exported = new Set(await exportedIds());
    const out = [];
    await forEachTake(record => {
      out.push({
        id: record.id,
        fileName: record.fileName,
        size: Number(record.size) || 0,
        status: record.status || (record.metadata && record.metadata.status) || 'legacy',
        participantId: record.participantId || null,
        sentenceIndex: record.sentenceIndex,
        exported: exported.has(record.id)
      });
    });
    return out;
  }

  async function storageEstimate(extraBytes = 0) {
    if (!navigator.storage || typeof navigator.storage.estimate !== 'function') return null;
    try {
      const { usage = 0, quota = 0 } = await navigator.storage.estimate();
      if (!quota) return null;
      const projected = usage + Math.max(0, extraBytes);
      return { usage, quota, projected, ratio: projected / quota, blocked: projected >= quota * cfg.STORAGE_BLOCK_RATIO };
    } catch (error) {
      console.warn('Storage estimate failed', error);
      return null;
    }
  }

  async function requestPersistence() {
    try {
      if (navigator.storage && typeof navigator.storage.persist === 'function') {
        return await navigator.storage.persist();
      }
    } catch (error) {
      console.warn('Persistent storage request failed', error);
    }
    return false;
  }

  // ---- event log ----
  function appendEvents(entries) {
    if (!entries.length || !stateDb) return Promise.resolve();
    return transact(stateDb, ['events'], 'readwrite', tx => {
      const store = tx.objectStore('events');
      entries.forEach(entry => store.add({ ...entry }));
    });
  }

  async function getAllEvents(limit = cfg.EVENT_LOG_LIMIT) {
    const tx = stateDb.transaction(['events'], 'readonly');
    const all = await promisify(tx.objectStore('events').getAll());
    return all.slice(-limit);
  }

  async function trimEvents(keep = cfg.EVENT_LOG_LIMIT) {
    const tx = stateDb.transaction(['events'], 'readonly');
    const keys = await promisify(tx.objectStore('events').getAllKeys());
    if (keys.length <= keep) return;
    const remove = keys.slice(0, keys.length - keep);
    await transact(stateDb, ['events'], 'readwrite', t => {
      const store = t.objectStore('events');
      remove.forEach(key => store.delete(key));
    });
  }

  return {
    init,
    getSetting,
    setSetting,
    deleteSetting,
    progressKey,
    getProgress,
    deleteProgress,
    findUnclaimedLegacyProgress,
    createParticipantProgress,
    saveParticipantProgress,
    commitTake,
    roundOf,
    getSupersedeList,
    allSupersedeLists,
    markSupersedeDone,
    exportedIds,
    markExported,
    pruneExported,
    latestBackup,
    releaseLatestBackup,
    countUnsaved,
    takeIds,
    cachedNames,
    addTake,
    getTake,
    deleteTakes,
    updateTake,
    modifyTake,
    forEachTake,
    countTakes,
    listTakeSummaries,
    storageEstimate,
    requestPersistence,
    appendEvents,
    getAllEvents,
    trimEvents
  };
})();
