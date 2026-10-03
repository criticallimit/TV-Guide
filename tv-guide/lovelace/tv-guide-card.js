class TVGuideCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {height: 900};
    this._hass = null;
    this._lastSrc = "";
  }

  static getStubConfig() {
    return {height: 900};
  }

  setConfig(config) {
    this._config = {
      height: Math.max(400, Math.min(2000, Number(config?.height || 900))),
      ingress_path: typeof config?.ingress_path === "string" ? config.ingress_path.trim() : ""
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return Math.max(8, Math.ceil(this._config.height / 50));
  }

  _findIngressPath() {
    if (this._config.ingress_path) {
      return this._config.ingress_path.startsWith("/")
        ? this._config.ingress_path
        : "/" + this._config.ingress_path;
    }

    const panels = this._hass?.panels || {};
    const entries = Object.entries(panels);

    for (const [key, panel] of entries) {
      const id = String(key || "");
      const title = String(panel?.title || panel?.config?.title || "");
      const component = String(panel?.component_name || panel?.component || "");
      if (
        id.endsWith("_tv_guide") ||
        id === "tv_guide" ||
        title === "TV Programm" ||
        (component.includes("iframe") && id.includes("tv_guide"))
      ) {
        return "/" + id.replace(/^\/+/, "");
      }
    }

    try {
      const home = document.querySelector("home-assistant");
      const rootPanels = home?.hass?.panels || {};
      for (const [key, panel] of Object.entries(rootPanels)) {
        const id = String(key || "");
        const title = String(panel?.title || panel?.config?.title || "");
        if (id.endsWith("_tv_guide") || id === "tv_guide" || title === "TV Programm") {
          return "/" + id.replace(/^\/+/, "");
        }
      }
    } catch {}

    return "";
  }

  _render() {
    const src = this._findIngressPath();

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card {
          overflow:hidden;
          padding:0;
          background:var(--ha-card-background,var(--card-background-color));
        }
        .frame {
          display:block;
          width:100%;
          height:${this._config.height}px;
          border:0;
          background:var(--primary-background-color);
        }
        .missing {
          padding:20px;
          color:var(--primary-text-color);
        }
        .missing strong { display:block; margin-bottom:6px; }
        .missing span { color:var(--secondary-text-color); }
      </style>
      <ha-card>
        ${src
          ? '<iframe class="frame" title="TV Guide" src="' + src + '" allow="clipboard-read; clipboard-write" loading="lazy"></iframe>'
          : '<div class="missing"><strong>TV Guide konnte die Ingress-Seite nicht finden.</strong><span>Öffne TV Guide einmal über die Seitenleiste und lade das Dashboard danach neu.</span></div>'}
      </ha-card>
    `;

    this._lastSrc = src;
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
    description:"Zeigt die originale TV-Guide-Ingress-Seite direkt im Dashboard",
    preview:false
  });
}
