/* Shared model-picker behavior, independent of the chat rendering code. */
globalThis.NcnrModelPicker = class {
  constructor(select, storage, onChange, isBusy = () => false) {
    this.select = select;
    this.storage = storage;
    this.onChange = onChange;
    this.isBusy = isBusy;
    this.revision = 0;
    this.storageKey = 'ncnr_selected_model';
    try { this.saved = JSON.parse(storage.getItem(this.storageKey)); } catch { this.saved = null; }
    const match = [...select.options].find(o =>
      o.value === this.saved?.model && o.dataset.provider === this.saved?.provider);
    if (match) select.selectedIndex = [...select.options].indexOf(match);
    select.addEventListener('change', () => this.remember());
    onChange();
  }

  remember() {
    const option = this.select.selectedOptions[0];
    if (!option) return;
    this.saved = { model: option.value, provider: option.dataset.provider };
    this.storage.setItem(this.storageKey, JSON.stringify(this.saved));
    this.onChange();
  }

  async refresh(rchatKey = '') {
    const revision = ++this.revision;
    try {
      const response = await fetch('/api/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_keys: { rchat: rchatKey } }),
      });
      if (!response.ok) return;
      const data = await response.json();
      if (revision !== this.revision || this.isBusy()) return;
      const groups = [];
      const labels = { openai: 'OpenAI', anthropic: 'Anthropic', google: 'Google Gemini', rchat: 'NIST rchat' };
      for (const [provider, models] of Object.entries(data.models || {})) {
        if (!labels[provider] || !Array.isArray(models)) continue;
        const group = document.createElement('optgroup');
        group.label = labels[provider];
        for (const model of models) {
          if (typeof model !== 'string' || !model.trim()) continue;
          const option = document.createElement('option');
          option.value = model;
          option.textContent = model;
          option.dataset.provider = provider;
          group.appendChild(option);
        }
        if (group.children.length) groups.push(group);
      }
      if (!groups.length) return;
      const previous = this.saved || {
        model: this.select.value, provider: this.select.selectedOptions[0]?.dataset.provider,
      };
      this.select.replaceChildren(...groups);
      const options = [...this.select.options];
      const chosen = options.find(o => o.value === previous.model && o.dataset.provider === previous.provider)
        || options.find(o => o.value === 'Muse-Glimmer-30B' && o.dataset.provider === 'rchat')
        || options.find(o => o.dataset.provider === 'rchat') || options[0];
      this.select.selectedIndex = options.indexOf(chosen);
      // Preserve a saved live-only selection until authenticated discovery can
      // confirm it; an offline fallback must not erase that preference.
      if (data.rchat_live) this.remember();
      else this.onChange();
    } catch {
      // Keep the usable fallback picker when the server/catalog is unavailable.
    }
  }
};
