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
    const record = {
      sentenceSet: progressKey(participantId, setKey),
      participantId,
      set: setKey,
      currentIndex: legacy ? Math.max(0, Number(legacy.currentIndex) || 0) : 0,
      repetitionCount: legacy ? Number(legacy.repetitionCount) || 0 : 0,
      completed: legacy ? Boolean(legacy.completed) : false,
      completedAt: legacy ? legacy.completedAt || null : null,
      tutorialTakes: 0,
      takeCounts: {},
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

  // Saves the participant record and mirrors it to the legacy key so the legacy
  // recorder (fallback page) continues from the same sentence on this device.
  async function saveParticipantProgress(record) {
    record.timestamp = new Date().toISOString();
    const mirror = {
      sentenceSet: record.set,
      currentIndex: record.currentIndex,
      repetitionCount: record.repetitionCount || 0,
      completed: Boolean(record.completed),
      completedAt: record.completedAt || null,
      timestamp: record.timestamp,
      mirroredFrom: record.participantId
    };
    await transact(videoDb, ['progress'], 'readwrite', tx => {
      const store = tx.objectStore('progress');
      store.put(record);
      store.put(mirror);
    });
  }

  // ---- takes (the "videos" store) ----
  function addTake(record) {
    return transact(videoDb, ['videos'], 'readwrite', tx => tx.objectStore('videos').add(record));
  }

  async function getTake(id) {
    const tx = videoDb.transaction(['videos'], 'readonly');
    return (await promisify(tx.objectStore('videos').get(id))) || null;
  }

  function deleteTakes(ids) {
    return transact(videoDb, ['videos'], 'readwrite', tx => {
      const store = tx.objectStore('videos');
      ids.forEach(id => store.delete(id));
    });
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

  async function listTakeSummaries() {
    const out = [];
    await forEachTake(record => {
      out.push({
        id: record.id,
        fileName: record.fileName,
        size: Number(record.size) || 0,
        status: record.status || (record.metadata && record.metadata.status) || 'legacy',
        participantId: record.participantId || null,
        sentenceIndex: record.sentenceIndex,
        folderWritten: Boolean(record.folderWritten)
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
    addTake,
    getTake,
    deleteTakes,
    updateTake,
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
