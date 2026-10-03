class TVGuideCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: "open"});
    this._config = {view: "now", columns: 4, max_channels: 0};
    this._data = null;
    this._timer = null;
  }

  static getStubConfig() {
    return {view: "now", columns: 4, max_channels: 0};
  }

  setConfig(config) {
    this._config = {
      view: ["now","2015","2200"].includes(config?.view) ? config.view : "now",
      columns: Math.max(1, Math.min(6, Number(config?.columns || 4))),
      max_channels: Math.max(0, Number(config?.max_channels || 0))
    };
    if (this.isConnected) this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  connectedCallback() {
    this._load();
    this._timer = window.setInterval(() => this._load(), 60000);
  }

  disconnectedCallback() {
    if (this._timer) window.clearInterval(this._timer);
    this._timer = null;
  }

  getCardSize() {
    if (!this._data?.channels?.length) return 4;
    const count = this._config.max_channels > 0
      ? Math.min(this._data.channels.length, this._config.max_channels)
      : this._data.channels.length;
    return Math.max(4, Math.ceil(count / this._config.columns) * 3);
  }

  async _load() {
    try {
      const res = await fetch("/local/tv-guide-data.json?t=" + Date.now(), {cache: "no-store"});
      if (!res.ok) throw new Error("TV-Guide-Daten sind noch nicht verfügbar.");
      this._data = await res.json();
      this._error = "";
    } catch (err) {
      this._error = err?.message || "TV-Guide-Daten konnten nicht geladen werden.";
    }
    this._render();
  }

  _target() {
    const now = new Date();
    if (this._config.view === "now") return now;
    const target = new Date(now);
    if (this._config.view === "2015") target.setHours(20,15,0,0);
    if (this._config.view === "2200") target.setHours(22,0,0,0);
    return target;
  }

  _programme(channel) {
    const target = this._target();
    const list = Array.isArray(channel.programs) ? channel.programs : [];
    let index = list.findIndex(p => new Date(p.start) <= target && target < new Date(p.end));
    if (index < 0) index = list.findIndex(p => new Date(p.start) >= target);
    return index >= 0 ? list.slice(index, index + 2) : [];
  }

  _time(value) {
    return new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"}).format(new Date(value));
  }

  _escape(value) {
    return String(value || "").replace(/[&<>"']/g, c => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
    }[c]));
  }

  _setView(view) {
    this._config.view = view;
    this._render();
  }

  _render() {
    const title = this._config.view === "now" ? "TV-Programm jetzt" : "TV-Programm " + (this._config.view === "2015" ? "20:15" : "22:00");
    const channels = this._data?.channels || [];
    const shown = this._config.max_channels > 0 ? channels.slice(0, this._config.max_channels) : channels;

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card {
          overflow:hidden;
          background:var(--ha-card-background,var(--card-background-color));
          color:var(--primary-text-color);
        }
        .head {
          display:flex; align-items:center; justify-content:space-between; gap:12px;
          padding:14px 16px 10px;
        }
        h2 { margin:0; font-size:18px; }
        .tabs { display:flex; gap:4px; flex-wrap:wrap; }
        .tabs button {
          border:0; border-radius:6px; background:transparent;
          color:var(--secondary-text-color); padding:6px 8px; cursor:pointer;
        }
        .tabs button.active {
          color:var(--primary-color);
          background:color-mix(in srgb,var(--primary-color) 10%,transparent);
          font-weight:700;
        }
        .status { padding:0 16px 10px; color:var(--secondary-text-color); font-size:12px; }
        .grid {
          display:grid;
          grid-template-columns:repeat(${this._config.columns},minmax(0,1fr));
          gap:10px; padding:0 12px 14px;
        }
        .channel {
          min-width:0; border:1px solid var(--divider-color);
          border-radius:10px; overflow:hidden;
          background:var(--card-background-color,var(--ha-card-background));
        }
        .brand {
          min-height:58px; display:flex; align-items:center; justify-content:center;
          gap:8px; padding:8px 10px; border-bottom:1px solid var(--divider-color);
        }
        .brand img { width:74px; height:34px; object-fit:contain; }
        .brand span { font-size:11px; color:var(--secondary-text-color); text-align:center; }
        .program { display:grid; grid-template-columns:50px minmax(0,1fr); gap:8px; padding:9px 10px; }
        .program + .program { border-top:1px solid var(--divider-color); }
        .time { color:var(--error-color,#d71920); font-size:12px; font-weight:700; }
        .title { font-size:13px; font-weight:650; line-height:1.25; overflow:hidden; text-overflow:ellipsis; }
        .empty { color:var(--secondary-text-color); font-size:12px; padding:12px; }
        .error { padding:16px; color:var(--error-color,#d71920); }
        @media(max-width:900px){ .grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
        @media(max-width:600px){
          .head{align-items:flex-start; flex-direction:column;}
          .grid{grid-template-columns:1fr;}
        }
      </style>
      <ha-card>
        <div class="head">
          <h2>${this._escape(title)}</h2>
          <div class="tabs">
            <button data-view="now" class="${this._config.view==="now"?"active":""}">JETZT</button>
            <button data-view="2015" class="${this._config.view==="2015"?"active":""}">20:15</button>
            <button data-view="2200" class="${this._config.view==="2200"?"active":""}">22:00</button>
          </div>
        </div>
        ${this._error ? '<div class="error">'+this._escape(this._error)+'</div>' : `
          <div class="status">${this._escape(this._data?.updated_at ? "Aktualisiert " + this._time(this._data.updated_at) : "")}</div>
          <div class="grid">
            ${shown.map(ch => {
              const programs = this._programme(ch);
              return `
                <div class="channel">
                  <div class="brand">
                    <img src="/local/tv-guide-logos/${encodeURIComponent(ch.id)}.png" alt="${this._escape(ch.name)}"
                      onerror="this.style.display='none'">
                    <span>${this._escape(ch.name)}</span>
                  </div>
                  ${programs.length ? programs.map(p => `
                    <div class="program">
                      <div class="time">${this._time(p.start)}</div>
                      <div class="title">${this._escape(p.title)}</div>
                    </div>`).join("") : '<div class="empty">Keine Programmdaten</div>'}
                </div>`;
            }).join("")}
          </div>
        `}
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll("[data-view]").forEach(btn => {
      btn.addEventListener("click", () => this._setView(btn.dataset.view));
    });
  }
}

if (!customElements.get("tv-guide-card")) {
  customElements.define("tv-guide-card", TVGuideCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "tv-guide-card")) {
  window.customCards.push({
    type: "tv-guide-card",
    name: "TV Guide",
    description: "Fernsehprogramm direkt im Home-Assistant-Dashboard",
    preview: true
  });
}
