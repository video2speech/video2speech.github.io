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

  function validate(label, list, expected) {
    if (list.length !== expected) throw new Error(`${label} must contain ${expected} sentences, but has ${list.length}.`);
    const duplicates = findDuplicates(list);
    if (duplicates.length) throw new Error(`${label} has duplicate sentences: ${duplicates.slice(0, 3).join(' | ')}`);
  }

  // Returns { setKey, warmupCount, formalCount, all } where all = warm-up + formal.
  async function load(setKey) {
    if (cache[setKey]) return cache[setKey];
    const set = cfg.SETS[setKey];
    if (!set) throw new Error(`Unknown sentence set: ${setKey}`);
    const [warmup, formal] = await Promise.all([loadFile(cfg.WARMUP_FILE), loadFile(set.file)]);
    validate('Warm-up file', warmup, cfg.WARMUP_COUNT);
    validate('Sentence file', formal, set.count);
    const combined = findDuplicates([...warmup, ...formal]);
    if (combined.length) throw new Error(`Warm-up and sentence files overlap: ${combined.slice(0, 3).join(' | ')}`);
    cache[setKey] = { setKey, warmupCount: warmup.length, formalCount: formal.length, all: [...warmup, ...formal] };
    return cache[setKey];
  }

  return { load };
})();
