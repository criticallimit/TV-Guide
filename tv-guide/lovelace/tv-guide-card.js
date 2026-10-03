class TVGuideCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: "open"});
    this._config = {view: "now", columns: 5, max_channels: 0};
    this._data = null;
    this._timer = null;
    this._selectedDate = this._startOfDay(new Date());
  }

  static getStubConfig() {
    return {view: "now", columns: 5, max_channels: 0};
  }

  setConfig(config) {
    this._config = {
      view: ["now","2015","2200"].includes(config?.view) ? config.view : "now",
      columns: Math.max(1, Math.min(6, Number(config?.columns || 5))),
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
    if (!this._data?.channels?.length) return 6;
    const count = this._config.max_channels > 0
      ? Math.min(this._data.channels.length, this._config.max_channels)
      : this._data.channels.length;
    return Math.max(6, Math.ceil(count / Math.max(1, this._config.columns)) * 4);
  }

  _startOfDay(value) {
    const d = new Date(value);
    d.setHours(0,0,0,0);
    return d;
  }

  _dateKey(value) {
    const d = new Date(value);
    const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0,10);
  }

  _sameDay(a,b) {
    return this._dateKey(a) === this._dateKey(b);
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
    if (this._config.view === "now" && this._sameDay(this._selectedDate, new Date())) return new Date();

    const target = new Date(this._selectedDate);
    if (this._config.view === "now") target.setHours(new Date().getHours(), new Date().getMinutes(), 0, 0);
    if (this._config.view === "2015") target.setHours(20,15,0,0);
    if (this._config.view === "2200") target.setHours(22,0,0,0);
    return target;
  }

  _programme(channel) {
    const target = this._target();
    const list = Array.isArray(channel.programs) ? channel.programs : [];
    let index = list.findIndex(p => new Date(p.start) <= target && target < new Date(p.end));
    if (index < 0) index = list.findIndex(p => new Date(p.start) >= target);
    return index >= 0 ? list.slice(index, index + 5) : [];
  }

  _time(value) {
    return new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"}).format(new Date(value));
  }

  _day(value) {
    return new Intl.DateTimeFormat("de-DE", {weekday:"short"}).format(new Date(value)).replace(".","").toUpperCase();
  }

  _date(value) {
    return new Intl.DateTimeFormat("de-DE", {day:"2-digit", month:"2-digit"}).format(new Date(value));
  }

  _escape(value) {
    return String(value || "").replace(/[&<>"']/g, c => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
    }[c]));
  }

  _isCurrent(program) {
    const now = new Date();
    return this._config.view === "now" &&
      this._sameDay(this._selectedDate, now) &&
      new Date(program.start) <= now && now < new Date(program.end);
  }

  _remaining(program) {
    return Math.max(0, Math.ceil((new Date(program.end) - new Date()) / 60000));
  }

  _progress(program) {
    const start = new Date(program.start);
    const end = new Date(program.end);
    const value = ((new Date() - start) / (end - start)) * 100;
    return Math.max(0, Math.min(100, value));
  }

  _setView(view) {
    this._config.view = view;
    if (view === "now") this._selectedDate = this._startOfDay(new Date());
    this._render();
  }

  _setDate(dateValue) {
    this._selectedDate = this._startOfDay(dateValue);
    if (this._config.view === "now" && !this._sameDay(this._selectedDate, new Date())) {
      this._config.view = "2015";
    }
    this._render();
  }

  _headline() {
    if (this._config.view === "now") return "Das aktuelle TV-Programm jetzt";
    const target = this._target();
    const date = new Intl.DateTimeFormat("de-DE", {weekday:"short", day:"2-digit", month:"2-digit"}).format(target);
    return "TV-Programm " + date + " um " + this._time(target) + " Uhr";
  }

  _render() {
    const channels = this._data?.channels || [];
    const shown = this._config.max_channels > 0 ? channels.slice(0, this._config.max_channels) : channels;
    const first = this._startOfDay(new Date());
    const dates = Array.from({length:8}, (_,i) => {
      const d = new Date(first);
      d.setDate(d.getDate()+i);
      return d;
    });

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display:block;
          --mint: var(--primary-color,#69c2b3);
          --mint-dark: var(--accent-color,#4b9f92);
          --red:#d71920;
          --card:var(--ha-card-background,var(--card-background-color,#fff));
          --text:var(--primary-text-color,#111);
          --muted:var(--secondary-text-color,#666);
          --line:var(--divider-color,rgba(127,127,127,.25));
          --current-bg:color-mix(in srgb,var(--mint) 12%,var(--card));
          --hover-bg:color-mix(in srgb,var(--mint) 8%,var(--card));
        }
        * { box-sizing:border-box; }
        ha-card {
          background:transparent;
          color:var(--text);
          box-shadow:none;
          border:0;
          overflow:visible;
        }
        .wrap { width:100%; }
        .headline-row {
          position:relative;
          min-height:44px;
          display:flex;
          align-items:center;
          justify-content:center;
          padding:0 12px;
          margin:0 0 4px;
        }
        .times {
          position:absolute;
          left:12px;
          top:50%;
          transform:translateY(-50%);
          display:flex;
          gap:3px;
        }
        .tab {
          border:0;
          border-radius:4px;
          background:transparent;
          color:var(--text);
          padding:5px 8px;
          font-size:11px;
          font-weight:650;
          cursor:pointer;
        }
        .tab.active {
          font-weight:850;
          color:var(--mint-dark);
          background:var(--hover-bg);
        }
        h2 {
          width:100%;
          margin:0;
          text-align:center;
          font-size:clamp(22px,2.2vw,34px);
          line-height:1.15;
        }
        .status {
          text-align:center;
          color:var(--muted);
          margin:0 0 12px;
          font-size:12px;
        }
        .date-strip {
          display:flex;
          gap:1px;
          overflow-x:auto;
          background:var(--card);
          border-bottom:1px solid var(--line);
        }
        .date-button {
          flex:1 0 90px;
          border:0;
          border-right:1px solid var(--line);
          background:transparent;
          color:var(--text);
          padding:8px 10px;
          text-align:center;
          cursor:pointer;
        }
        .date-button span {
          display:block;
          font-size:11px;
          color:var(--muted);
        }
        .date-button strong {
          display:block;
          margin-top:2px;
          font-size:14px;
        }
        .date-button.active {
          color:var(--red);
          background:rgba(215,25,32,.05);
        }
        .date-button.active span { color:var(--red); }
        .group-row {
          min-height:46px;
          display:flex;
          align-items:center;
          justify-content:center;
          background:var(--card);
          border-bottom:1px solid var(--line);
        }
        .group {
          padding:8px 13px;
          color:var(--mint-dark);
          font-weight:700;
        }
        .grid {
          display:grid;
          grid-template-columns:repeat(${this._config.columns},minmax(0,1fr));
          gap:16px;
          margin-top:0;
        }
        .channel { min-width:0; }
        .brand {
          min-height:84px;
          display:grid;
          grid-template-rows:64px auto;
          place-items:center;
          background:var(--card);
          border:1px solid var(--line);
          border-bottom:0;
          padding:10px;
        }
        .brand img {
          width:calc(100% - 20px);
          height:44px;
          max-width:240px;
          object-fit:contain;
          object-position:center;
          display:block;
        }
        .brand span {
          display:block;
          max-width:100%;
          margin-top:1px;
          color:var(--muted);
          font-size:10px;
          font-weight:700;
          line-height:1.1;
          text-align:center;
          white-space:nowrap;
          overflow:hidden;
          text-overflow:ellipsis;
        }
        .programs {
          border:1px solid var(--line);
          background:var(--card);
        }
        .program {
          width:100%;
          min-height:68px;
          position:relative;
          display:grid;
          grid-template-columns:58px minmax(0,1fr) 18px;
          gap:8px;
          align-items:center;
          border-top:1px solid var(--line);
          background:var(--card);
          padding:9px 8px;
          text-align:left;
        }
        .program:first-child { border-top:0; }
        .program.current {
          min-height:92px;
          background:var(--current-bg);
        }
        .program-time {
          align-self:start;
          font-size:12px;
          color:var(--red);
        }
        .program-time span:last-child {
          display:block;
          margin-top:3px;
          font-weight:700;
        }
        .now-dot {
          display:inline-block !important;
          margin:0 0 3px !important;
          background:var(--red);
          color:#fff;
          border-radius:3px;
          padding:2px 4px;
          font-size:9px;
          letter-spacing:.04em;
        }
        .program-main strong {
          display:block;
          line-height:1.2;
          font-size:14px;
        }
        .category {
          margin-top:5px;
          color:var(--muted);
          font-size:11px;
        }
        .remaining {
          margin-top:5px;
          color:var(--muted);
          font-size:10px;
        }
        .chevron {
          font-size:28px;
          font-weight:200;
          color:rgba(127,127,127,.6);
        }
        .progress-track {
          position:absolute;
          left:0;
          right:0;
          bottom:0;
          height:4px;
          background:rgba(127,127,127,.2);
        }
        .progress-fill {
          height:100%;
          background:var(--red);
        }
        .empty {
          min-height:68px;
          display:flex;
          align-items:center;
          padding:12px;
          color:var(--muted);
          font-style:italic;
        }
        .error {
          padding:16px;
          color:var(--red);
          background:var(--card);
        }
        @media(max-width:1100px){
          .grid{grid-template-columns:repeat(3,minmax(0,1fr));}
        }
        @media(max-width:720px){
          .headline-row {
            min-height:70px;
            padding:34px 8px 0;
          }
          .times {
            left:50%;
            top:14px;
            transform:translateX(-50%);
            width:max-content;
          }
          h2 { font-size:20px; }
          .grid {
            grid-template-columns:1fr;
            gap:8px;
          }
          .channel {
            display:grid;
            grid-template-columns:92px minmax(0,1fr);
            background:var(--card);
            border-top:1px solid var(--line);
            border-bottom:1px solid var(--line);
          }
          .brand {
            min-height:0;
            grid-template-rows:52px auto;
            border:0;
            border-right:1px solid var(--line);
            padding:10px;
          }
          .brand img {
            width:calc(100% - 20px);
            height:32px;
            max-width:76px;
          }
          .programs { border:0; }
        }
      </style>
      <ha-card>
        <div class="wrap">
          <div class="headline-row">
            <div class="times">
              <button class="tab ${this._config.view==="now"?"active":""}" data-view="now">JETZT</button>
              <button class="tab ${this._config.view==="2015"?"active":""}" data-view="2015">20:15</button>
              <button class="tab ${this._config.view==="2200"?"active":""}" data-view="2200">22:00</button>
            </div>
            <h2>${this._escape(this._headline())}</h2>
          </div>

          <div class="status">${this._escape(this._data?.updated_at ? "Aktualisiert " + this._time(this._data.updated_at) : "")}</div>

          <div class="date-strip">
            ${dates.map(d => `
              <button class="date-button ${this._sameDay(d,this._selectedDate)?"active":""}" data-date="${this._dateKey(d)}">
                <span>${this._day(d)}</span>
                <strong>${this._date(d)}</strong>
              </button>
            `).join("")}
          </div>

          <div class="group-row"><div class="group">Hauptsender</div></div>

          ${this._error ? '<div class="error">'+this._escape(this._error)+'</div>' : `
            <div class="grid">
              ${shown.map(ch => {
                const programs = this._programme(ch);
                return `
                  <section class="channel">
                    <div class="brand">
                      <img src="/local/tv-guide-logos/${encodeURIComponent(ch.id)}.png" alt="${this._escape(ch.name)}"
                        onerror="this.style.display='none'">
                      <span>${this._escape(ch.name)}</span>
                    </div>
                    <div class="programs">
                      ${programs.length ? programs.map(p => {
                        const current = this._isCurrent(p);
                        return `
                          <div class="program ${current?"current":""}">
                            <div class="program-time">
                              ${current?'<span class="now-dot">JETZT</span>':""}
                              <span>${this._time(p.start)}</span>
                            </div>
                            <div class="program-main">
                              <strong>${this._escape(p.title)}</strong>
                              ${p.category?'<div class="category">'+this._escape(p.category)+'</div>':""}
                              ${current?'<div class="remaining">noch '+this._remaining(p)+' Min.</div>':""}
                            </div>
                            <div class="chevron">›</div>
                            ${current?'<div class="progress-track"><div class="progress-fill" style="width:'+this._progress(p)+'%"></div></div>':""}
                          </div>
                        `;
                      }).join("") : '<div class="empty">Für diese Zeit keine EPG-Daten verfügbar</div>'}
                    </div>
                  </section>
                `;
              }).join("")}
            </div>
          `}
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll("[data-view]").forEach(btn => {
      btn.addEventListener("click", () => this._setView(btn.dataset.view));
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
    type: "tv-guide-card",
    name: "TV Guide",
    description: "Fernsehprogramm direkt im Home-Assistant-Dashboard",
    preview: false
  });
}
