const assert = require('node:assert/strict');
const { test } = require('node:test');
require('../static/model-picker.js');

function element(tag) {
  return { tag, children: [], dataset: {}, appendChild(child) { this.children.push(child); } };
}
global.document = { createElement: element };
function setup(saved = null, busy = () => false) {
  const select = {
    options: [{ value: 'Muse-Glimmer-30B', dataset: { provider: 'rchat' } }],
    selectedIndex: 0,
    get value() { return this.options[this.selectedIndex]?.value; },
    set value(value) { this.selectedIndex = this.options.findIndex(o => o.value === value); },
    get selectedOptions() { return this.options.slice(this.selectedIndex, this.selectedIndex + 1); },
    addEventListener(name, fn) { this.change = fn; },
    replaceChildren(...groups) { this.options = groups.flatMap(g => g.children); },
  };
  const storage = { value: saved && JSON.stringify(saved), getItem() { return this.value; },
    setItem(key, value) { this.value = value; } };
  let selected;
  const picker = new NcnrModelPicker(select, storage, () => {
    selected = { model: select.value, provider: select.selectedOptions[0]?.dataset.provider };
  }, busy);
  return { select, storage, picker, selected: () => selected };
}
function catalog(models, live = true) {
  return { ok: true, json: async () => ({ models: { rchat: models }, rchat_live: live }) };
}

test('live-only saved selection is restored with its provider', async () => {
  const s = setup({ model: 'Muse-New', provider: 'rchat' });
  global.fetch = async (url, options) => {
    assert.equal(url, '/api/models');
    assert.equal(options.method, 'POST');
    assert.deepEqual(JSON.parse(options.body), { api_keys: { rchat: 'key' } });
    return catalog(['Muse-Glimmer-30B', 'Muse-New']);
  };
  await s.picker.refresh('key');
  assert.deepEqual(s.selected(), { model: 'Muse-New', provider: 'rchat' });
});
test('retired selection falls back and new choices persist', async () => {
  const s = setup({ model: 'gpt-oss-120b', provider: 'rchat' });
  global.fetch = async () => catalog(['Muse-Glimmer-30B', 'Muse-Spark']);
  await s.picker.refresh();
  assert.equal(s.select.value, 'Muse-Glimmer-30B');
  s.select.value = 'Muse-Spark';
  s.select.change();
  assert.deepEqual(JSON.parse(s.storage.value), { model: 'Muse-Spark', provider: 'rchat' });
});
test('network failure and offline fallback preserve saved live preference', async () => {
  const s = setup({ model: 'Muse-New', provider: 'rchat' });
  global.fetch = async () => { throw new Error('offline'); };
  await s.picker.refresh();
  assert.equal(s.select.value, 'Muse-Glimmer-30B');
  global.fetch = async () => catalog(['Muse-Glimmer-30B'], false);
  await s.picker.refresh();
  assert.equal(JSON.parse(s.storage.value).model, 'Muse-New');
});
test('out-of-order refresh cannot overwrite the latest catalog', async () => {
  const s = setup();
  let resolveFirst;
  global.fetch = () => new Promise(resolve => { resolveFirst = resolve; });
  const first = s.picker.refresh('old-key');
  global.fetch = async () => catalog(['Muse-New']);
  await s.picker.refresh('new-key');
  resolveFirst(catalog(['Muse-Old']));
  await first;
  assert.equal(s.select.value, 'Muse-New');
});
test('discovery does not switch models during generation', async () => {
  const s = setup(null, () => true);
  global.fetch = async () => catalog(['Muse-New']);
  await s.picker.refresh();
  assert.equal(s.select.value, 'Muse-Glimmer-30B');
});
test('identical model IDs in different providers retain RChat routing', async () => {
  const s = setup({ model: 'gpt-4o', provider: 'rchat' });
  global.fetch = async () => ({ ok: true, json: async () => ({
    models: { openai: ['gpt-4o'], rchat: ['gpt-4o'] }, rchat_live: true,
  }) });
  await s.picker.refresh();
  assert.deepEqual(s.selected(), { model: 'gpt-4o', provider: 'rchat' });
});
