// Loads and validates the reading material (same files and checks as the legacy recorder).
window.V2S = window.V2S || {};

V2S.sentences = (() => {
  const cfg = V2S.config;
  const cache = {};

  async function loadFile(path) {
    const separator = path.includes('?') ? '&' : '?';
    const response = await fetch(`${path}${separator}v=${cfg.MATERIAL_VERSION}`, { cache: 'no-store' });
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    const lines = (await response.text()).replace(/\r/g, '').split('\n');
    if (lines.length && lines[lines.length - 1].trim() === '') lines.pop();
    const blank = lines.findIndex(line => line.trim() === '');
    if (blank !== -1) throw new Error(`${path}: blank line at ${blank + 1}`);
    return lines.map(line => line.trim());
  }

  function findDuplicates(list) {
    const seen = new Set();
    const duplicates = new Set();
    list.forEach(sentence => {
      const key = sentence.toLowerCase();
      if (seen.has(key)) duplicates.add(sentence);
      else seen.add(key);
    });
    return [...duplicates];
  }

  // `shortRepeats`: sentences of 1-3 words may appear this many times (v3).
  function validate(label, list, expected, shortRepeats = 1) {
    if (list.length !== expected) throw new Error(`${label} must contain ${expected} sentences, but has ${list.length}.`);
    const counts = new Map();
    list.forEach(s => counts.set(s.toLowerCase(), (counts.get(s.toLowerCase()) || 0) + 1));
    const words = s => s.split(/\s+/).filter(Boolean).length;
    const duplicates = shortRepeats > 1
      ? list.filter(s => counts.get(s.toLowerCase()) > (words(s) <= 3 ? shortRepeats : 1))
      : findDuplicates(list);
    if (duplicates.length) throw new Error(`${label} has duplicate sentences: ${duplicates.slice(0, 3).join(' | ')}`);
  }

  // A rotating set (v3): the part this participant starts from after the shared parts, from
  // the number in their ID (SEMG1 -> part 8, SEMG2 -> part 21, ...); null if the ID has none.
  function startPart(setKey, participantId) {
    const rot = (cfg.SETS[setKey] || {}).rotation;
    if (!rot) return null;
    const match = new RegExp(rot.idPattern).exec(String(participantId || ''));
    if (!match) return null;
    const span = rot.lastPart - rot.firstPart + 1;
    return rot.firstPart + ((Number(match[1]) - 1) * rot.step) % span;
  }

  // Returns { setKey, warmupCount, formalCount, all } where all = warm-up + formal. A rotating
  // set is in this participant's reading order and also gives `lines` (each formal sentence's
  // line in the file, 1-based), `startPart` and `fitList` (a sample to size the text by).
  async function load(setKey, participantId = null) {
    const set = cfg.SETS[setKey];
    if (!set) throw new Error(`Unknown sentence set: ${setKey}`);
    const start = set.rotation ? startPart(setKey, participantId) : null;
    if (set.rotation && start === null) throw new Error(`The sentence set ${set.label} needs a participant ID like SEMG1, SEMG2, ... (this one is ${participantId || 'not set'}).`);
    const cacheKey = start === null ? setKey : `${setKey}@${start}`;
    if (cache[cacheKey]) return cache[cacheKey];
    const [warmup, formal] = await Promise.all([loadFile(cfg.WARMUP_FILE), loadFile(set.file)]);
    validate('Warm-up file', warmup, cfg.WARMUP_COUNT);
    validate('Sentence file', formal, set.count, set.shortRepeats || 1);
    const combined = findDuplicates([...warmup, ...new Set(formal)]);
    if (combined.length) throw new Error(`Warm-up and sentence files overlap: ${combined.slice(0, 3).join(' | ')}`);
    let order = formal.map((_, i) => i);
    if (start !== null) {
      const { sharedParts, firstPart, lastPart } = set.rotation;
      const size = cfg.BLOCK_SIZE;
      const parts = [];
      for (let p = 1; p <= sharedParts; p += 1) parts.push(p);
      for (let i = 0; i <= lastPart - firstPart; i += 1) parts.push(firstPart + (start - firstPart + i) % (lastPart - firstPart + 1));
      order = parts.flatMap(p => Array.from({ length: size }, (_, j) => (p - 1) * size + j));
    }
    const ordered = order.map(i => formal[i]);
    const material = { setKey, warmupCount: warmup.length, formalCount: formal.length, all: [...warmup, ...ordered] };
    if (start !== null) {
      material.lines = order.map(i => i + 1);
      material.startPart = start;
      material.fitList = [...warmup, ...ordered.slice(0, 1000)];
    }
    cache[cacheKey] = material;
    return material;
  }

  // The Rainbow Passage, one sentence at a time (no practice of its own). Its file marks
  // its phrases: " || " between clauses (after a comma, before "and"), " | " between the
  // smaller phrases. Its lines break only there (ui.js). The sentences themselves (file
  // names, sidecars) are the words alone.
  const phraseMap = new Map();
  async function loadRainbow() {
    const key = cfg.RAINBOW.key;
    if (cache[key]) return cache[key];
    const marked = await loadFile(cfg.RAINBOW.file);
    const list = marked.map(line => {
      const parts = line.split(/\s*(\|\|?)\s*/);
      const phrases = [];
      for (let i = 0; i < parts.length; i += 2) phrases.push({ text: parts[i], major: i > 0 && parts[i - 1] === '||' });
      const sentence = phrases.map(phrase => phrase.text).join(' ');
      phraseMap.set(sentence, phrases);
      return sentence;
    });
    validate('Rainbow Passage file', list, cfg.RAINBOW.count);
    cache[key] = { setKey: key, warmupCount: 0, formalCount: list.length, all: list };
    return cache[key];
  }

  // A sentence's phrases, if its file marks them (the Rainbow Passage): [{ text, major }],
  // `major` when a clause boundary comes before it; otherwise null.
  const phrasesOf = sentence => phraseMap.get(sentence) || null;

  // ---- a set read a few parts a day (v3.3: 5; owner, 2026-10-21, 5 since 2026-10-23) ----
  // Patients see only today's parts: "Part 1 of 5" each day, the sentences going on from
  // where they stopped (also in the middle of a part). After the 5th, more parts are read
  // one at a time on request, shown without a total (Part 6, 7, ...). The progress record
  // keeps `day` = { date (the device's calendar day), startPart (the part in reading order,
  // from 1, that today's "Part 1" is) }.
  const dailyOf = setKey => (cfg.SETS[setKey] || {}).daily || null;
  const hasRainbow = setKey => Boolean(cfg.SETS[setKey]) && cfg.SETS[setKey].rainbow !== false;

  function today() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  // The part (in reading order, from 1) a sentence index is in; practice counts as part 1.
  function readingPart(material, index) {
    return Math.floor(Math.max(0, index - material.warmupCount) / cfg.BLOCK_SIZE) + 1;
  }

  // On a new day (or after moving back before today's start), today's "Part 1" is the part
  // being read now. `force`: start the count here (Settings moved the place). True if
  // the record changed (to be saved).
  function startDay(setKey, material, progress, { force = false } = {}) {
    if (!dailyOf(setKey) || !progress) return false;
    const part = readingPart(material, progress.currentIndex);
    const day = progress.day;
    if (!force && day && day.date === today() && day.startPart <= part) return false;
    progress.day = { date: today(), startPart: part };
    return true;
  }

  // What a part is shown as: { block, blocks } (blocks null after today's parts).
  // `part`: in reading order, from 1.
  function partView(setKey, material, progress, part) {
    const daily = dailyOf(setKey);
    if (!daily) return { block: part, blocks: Math.ceil(material.formalCount / cfg.BLOCK_SIZE) };
    const start = progress && progress.day && progress.day.startPart <= part ? progress.day.startPart : part;
    const block = part - start + 1;
    return { block, blocks: block <= daily.parts ? daily.parts : null };
  }

  return { load, loadRainbow, phrasesOf, startPart, dailyOf, hasRainbow, startDay, partView, readingPart, today };
})();
