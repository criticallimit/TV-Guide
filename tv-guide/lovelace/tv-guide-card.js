class TVGuideCard extends HTMLElement {
  constructor() {
    super();
    if (!window.TVGuideCore) {
      throw new Error("TV Guide: gemeinsamer Renderer wurde nicht geladen.");
    }
    this.attachShadow({mode:"open"});
    this._config = {view:"now", columns:5, max_channels:0};
    this._data = null;
    this._timer = null;
    this._selectedDate = window.TVGuideCore.startOfDay(new Date());
  }

  static getStubConfig() {
    return {view:"now", columns:5, max_channels:0};
  }

  setConfig(config) {
    this._config = {
      view:["now","2015","2200"].includes(config?.view) ? config.view : "now",
      columns:Math.max(3, Math.min(6, Number(config?.columns || 5))),
      max_channels:Math.max(0, Number(config?.max_channels || 0))
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
    const count = this._data?.channels?.length || 0;
    const visible = this._config.max_channels > 0 ? Math.min(count, this._config.max_channels) : count;
    return Math.max(6, Math.ceil(visible / Math.max(1, this._config.columns)) * 5);
  }

  async _load() {
    try {
      const res = await fetch("/local/tv-guide-data.json?t=" + Date.now(), {cache:"no-store"});
      if (!res.ok) throw new Error("TV-Guide-Daten sind noch nicht verfügbar.");
      this._data = await res.json();
      this._error = "";
    } catch (err) {
      this._error = err?.message || "TV-Guide-Daten konnten nicht geladen werden.";
    }
    this._render();
  }

  _setMode(mode) {
    this._config.view = mode;
    if (mode === "now") this._selectedDate = window.TVGuideCore.startOfDay(new Date());
    this._render();
  }

  _setDate(value) {
    this._selectedDate = window.TVGuideCore.startOfDay(value);
    if (this._config.view === "now" && !window.TVGuideCore.sameDay(this._selectedDate, new Date())) {
      this._config.view = "2015";
    }
    this._render();
  }

  _render() {
    const channels = this._data?.channels || [];
    const shown = this._config.max_channels > 0 ? channels.slice(0, this._config.max_channels) : channels;
    const availableCount = shown.filter(channel => channel.available).length;

    this.shadowRoot.innerHTML = `
      <style>
        @import url("/local/tv-guide-styles.css");
        :host {
          display:block;
          --mint:var(--primary-color,#69c2b3);
          --mint-dark:var(--accent-color,#4b9f92);
          --red:#d71920;
          --bg:var(--primary-background-color,transparent);
          --surface:var(--secondary-background-color,var(--ha-card-background));
          --card:var(--ha-card-background,var(--card-background-color,#fff));
          --text:var(--primary-text-color,#111);
          --muted:var(--secondary-text-color,#666);
          --line:var(--divider-color,rgba(127,127,127,.25));
          --current-bg:color-mix(in srgb,var(--mint) 12%,var(--card));
          --hover-bg:color-mix(in srgb,var(--mint) 8%,var(--card));
          --desktop-columns:${this._config.columns};
        }
        ha-card {
          display:block;
          background:transparent;
          border:0;
          box-shadow:none;
          color:var(--text);
          overflow:visible;
        }
        main {
          max-width:none;
          padding:0;
        }
        .app-settings-button,
        .group-actions {
          display:none !important;
        }
      </style>
      <ha-card>
        <main>
          <div class="headline-row">
            <nav class="times" aria-label="Schnellwahl Uhrzeit">
              <button class="tab ${this._config.view==="now"?"active":""}" data-mode="now">JETZT</button>
              <button class="tab ${this._config.view==="2015"?"active":""}" data-mode="2015">20:15</button>
              <button class="tab ${this._config.view==="2200"?"active":""}" data-mode="2200">22:00</button>
            </nav>
            <h1>${window.TVGuideCore.escapeHtml(window.TVGuideCore.headlineText(this._config.view, this._selectedDate, null))}</h1>
          </div>
          <p class="status">${this._error
            ? window.TVGuideCore.escapeHtml(this._error)
            : "Live-EPG · " + availableCount + " von " + shown.length + " Sendern"}</p>

          <div class="date-strip" aria-label="Tage">
            ${window.TVGuideCore.renderDateStrip(this._selectedDate)}
          </div>

          <div class="group-row">
            <nav class="groups" aria-label="Sendergruppen">
              <button class="group active" type="button">Hauptsender</button>
              <button class="group disabled" type="button">Sky</button>
              <button class="group disabled" type="button">Kabel Pay-TV</button>
              <button class="group disabled" type="button">MagentaTV</button>
            </nav>
          </div>

          <div class="channel-grid">
            ${shown.map(channel =>
              window.TVGuideCore.renderChannelCard(channel, this._config.view, this._selectedDate, null, "/local/tv-guide-")
            ).join("")}
          </div>
        </main>
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll("[data-mode]").forEach(btn => {
      btn.addEventListener("click", () => this._setMode(btn.dataset.mode));
    });
    this.shadowRoot.querySelectorAll("[data-date]").forEach(btn => {
      btn.addEventListener("click", () => this._setDate(new Date(btn.dataset.date + "T00:00:00")));
    });
  }
}

if (!customElements.get("tv-guide-card")) {
  customElements.define("tv-guide-card", TVGuideCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some(card => card.type === "tv-guide-card")) {
  window.customCards.push({
    type:"tv-guide-card",
    name:"TV Guide",
    description:"Fernsehprogramm direkt im Home-Assistant-Dashboard",
    preview:false
  });
}
