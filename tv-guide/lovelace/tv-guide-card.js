const TV_GUIDE_PICKER_LOGO = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 250 100\" width=\"250\" height=\"100\"><title>TV Guide</title><g transform=\"translate(0,2) scale(.75)\"><rect x=\"12\" y=\"21\" width=\"104\" height=\"77\" rx=\"19\" fill=\"#25b9bf\"/><rect x=\"23\" y=\"32\" width=\"82\" height=\"54\" rx=\"10\" fill=\"#102d3e\"/><rect x=\"33\" y=\"42\" width=\"12\" height=\"7\" rx=\"3\" fill=\"#fff\"/><rect x=\"52\" y=\"42\" width=\"42\" height=\"7\" rx=\"3\" fill=\"#fff\"/><rect x=\"33\" y=\"56\" width=\"12\" height=\"7\" rx=\"3\" fill=\"#76e3d8\"/><rect x=\"52\" y=\"56\" width=\"32\" height=\"7\" rx=\"3\" fill=\"#76e3d8\"/><rect x=\"33\" y=\"70\" width=\"12\" height=\"7\" rx=\"3\" fill=\"#fff\" opacity=\".7\"/><rect x=\"52\" y=\"70\" width=\"37\" height=\"7\" rx=\"3\" fill=\"#fff\" opacity=\".7\"/><path d=\"M48 106h32\" stroke=\"#25b9bf\" stroke-width=\"9\" stroke-linecap=\"round\"/></g><text x=\"105\" y=\"60\" font-family=\"Segoe UI,Arial,sans-serif\" font-size=\"29\" font-weight=\"700\" fill=\"#31949b\">TV Guide</text></svg>";

const TV_GUIDE_CARD_TRANSLATIONS = {"da":{"TV Guide wird geladen …":"TV Guide indlæses …","TV Guide konnte nicht geladen werden.":"TV Guide kunne ikke indlæses.","TV Guide ist nicht installiert.":"TV Guide er ikke installeret.","TV Guide ist nicht gestartet.":"TV Guide er ikke startet.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Ingen ingress-adresse er tilgængelig for TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"TV Guide-kortet kunne ikke oprettes.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide blev ikke fundet i Home Assistant."},"de":{"TV Guide wird geladen …":"TV Guide wird geladen …","TV Guide konnte nicht geladen werden.":"TV Guide konnte nicht geladen werden.","TV Guide ist nicht installiert.":"TV Guide ist nicht installiert.","TV Guide ist nicht gestartet.":"TV Guide ist nicht gestartet.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Für TV Guide ist keine Ingress-Adresse verfügbar.","TV-Guide-Karte konnte nicht aufgebaut werden.":"TV-Guide-Karte konnte nicht aufgebaut werden.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV-Guide-App wurde in Home Assistant nicht gefunden."},"en":{"TV Guide wird geladen …":"Loading TV Guide …","TV Guide konnte nicht geladen werden.":"Could not load TV Guide.","TV Guide ist nicht installiert.":"TV Guide is not installed.","TV Guide ist nicht gestartet.":"TV Guide is not running.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"No ingress address is available for TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Could not create the TV Guide card.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide was not found in Home Assistant."},"nl":{"TV Guide wird geladen …":"TV Guide laden …","TV Guide konnte nicht geladen werden.":"TV Guide kon niet worden geladen.","TV Guide ist nicht installiert.":"TV Guide is niet geïnstalleerd.","TV Guide ist nicht gestartet.":"TV Guide is niet gestart.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Geen ingress-adres beschikbaar voor TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"De TV Guide-kaart kon niet worden gemaakt.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide is niet gevonden in Home Assistant."},"fr":{"TV Guide wird geladen …":"Chargement de TV Guide…","TV Guide konnte nicht geladen werden.":"Impossible de charger TV Guide.","TV Guide ist nicht installiert.":"TV Guide n’est pas installé.","TV Guide ist nicht gestartet.":"TV Guide n’est pas démarré.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Aucune adresse ingress disponible pour TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Impossible de créer la carte TV Guide.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide est introuvable dans Home Assistant."},"it":{"TV Guide wird geladen …":"Caricamento di TV Guide…","TV Guide konnte nicht geladen werden.":"Impossibile caricare TV Guide.","TV Guide ist nicht installiert.":"TV Guide non è installato.","TV Guide ist nicht gestartet.":"TV Guide non è avviato.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Nessun indirizzo ingress disponibile per TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Impossibile creare la scheda TV Guide.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide non è stato trovato in Home Assistant."},"nb":{"TV Guide wird geladen …":"Laster TV Guide …","TV Guide konnte nicht geladen werden.":"Kunne ikke laste TV Guide.","TV Guide ist nicht installiert.":"TV Guide er ikke installert.","TV Guide ist nicht gestartet.":"TV Guide er ikke startet.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Ingen ingress-adresse er tilgjengelig for TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Kunne ikke opprette TV Guide-kortet.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide ble ikke funnet i Home Assistant."},"sv":{"TV Guide wird geladen …":"Läser in TV Guide …","TV Guide konnte nicht geladen werden.":"TV Guide kunde inte läsas in.","TV Guide ist nicht installiert.":"TV Guide är inte installerad.","TV Guide ist nicht gestartet.":"TV Guide är inte startad.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Ingen Ingress-adress är tillgänglig för TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"TV Guide-kortet kunde inte skapas.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide hittades inte i Home Assistant."}};

class TVGuideCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._hass = null;
    this._config = {};
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = {...(config || {})};
    this._render();
  }

  _changed(patch) {
    const config = {...this._config, ...patch};
    for (const [key, value] of Object.entries(config)) {
      if (value === "" || value === undefined || value === null) delete config[key];
    }
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail:{config},
      bubbles:true,
      composed:true
    }));
  }

  _render() {
    if (!this.shadowRoot) return;
    const themes = Object.keys(this._hass?.themes?.themes || {}).sort((a,b) => a.localeCompare(b));
    const currentTheme = String(this._config?.theme || "");
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        .form { display:grid; gap:16px; padding:8px 0; }
        label { display:grid; gap:6px; color:var(--primary-text-color); font-size:14px; }
        select {
          width:100%; box-sizing:border-box; min-height:44px; padding:8px 10px;
          border:1px solid var(--divider-color); border-radius:8px;
          background:var(--card-background-color, var(--ha-card-background));
          color:var(--primary-text-color); font:inherit;
        }
        .hint { color:var(--secondary-text-color); font-size:12px; line-height:1.4; }
      </style>
      <div class="form">
        <label>
          <span>Theme</span>
          <select id="theme">
            <option value="">Home Assistant / Dashboard</option>
            ${themes.map(name => `<option value="${name.replace(/&/g,"&amp;").replace(/"/g,"&quot;")}"${name === currentTheme ? " selected" : ""}>${name.replace(/&/g,"&amp;").replace(/</g,"&lt;")}</option>`).join("")}
          </select>
          <span class="hint">Uses the selected Home Assistant theme only for this TV Guide card.</span>
        </label>
      </div>
    `;
    this.shadowRoot.getElementById("theme")?.addEventListener("change", (event) => {
      this._changed({theme:event.target.value});
    });
  }
}

if (!customElements.get("tv-guide-card-editor")) {
  customElements.define("tv-guide-card-editor", TVGuideCardEditor);
}

class TVGuideCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {height: 1000};
    this._hass = null;
    this._started = false;
    this._startGeneration = 0;
    this._session = "";
    this._sessionTimer = null;
    this._iframe = null;
    this._themeProperties = new Set();
    this._themeFingerprint = "";
    this._lastThemeMessageSignature = "";
    this._themeReadyListening = false;
    this._themeObserver = null;
    this._themeSyncFrame = null;
    this._themeRetryTimer = null;
    this._themeReadyHandler = (event) => {
      if (
        event.origin === window.location.origin &&
        event.source === this._iframe?.contentWindow
      ) {
        if (event.data?.type === "tv-guide-theme-request") this._sendThemeToIframe(true);
        else if (event.data?.type === "tv-guide-theme-ready") this._iframe.style.opacity = "1";
      }
    };
  }

  _attachThemeReadyListener() {
    if (this._themeReadyListening) return;
    window.addEventListener("message", this._themeReadyHandler);
    this._themeReadyListening = true;
  }

  _detachThemeReadyListener() {
    if (!this._themeReadyListening) return;
    window.removeEventListener("message", this._themeReadyHandler);
    this._themeReadyListening = false;
  }

  _scheduleThemeSync() {
    if (!this.isConnected || !this._iframe || this._themeSyncFrame !== null) return;
    this._themeSyncFrame = window.requestAnimationFrame(() => {
      this._themeSyncFrame = null;
      if (this.isConnected) this._sendThemeToIframe();
    });
  }

  _watchInheritedTheme() {
    this._themeObserver?.disconnect();
    this._themeObserver = new MutationObserver(() => this._scheduleThemeSync());
    // Dashboard themes can change on a shadow host without changing hass.themes.
    for (let node = this; node; node = node.parentNode || node.host) {
      if (node.nodeType === 1) {
        this._themeObserver.observe(node, {attributes:true, attributeFilter:["class", "style"]});
      }
    }
  }

  _themeMessage() {
    const style = getComputedStyle(this);
    const names = [
      "--primary-background-color",
      "--secondary-background-color",
      "--card-background-color",
      "--ha-card-background",
      "--primary-text-color",
      "--secondary-text-color",
      "--divider-color",
      "--primary-color",
      "--accent-color",
      "--lovelace-background"
    ];
    const vars = {};
    for (const name of names) {
      const value = style.getPropertyValue(name).trim();
      if (value) vars[name] = value;
    }
    const background = vars["--primary-background-color"] || "";
    let darkMode = Boolean(this._hass?.themes?.darkMode);
    const hex = background.match(/^#([0-9a-f]{6})$/i);
    const rgb = background.match(/rgba?\((\d+)\D+(\d+)\D+(\d+)/i);
    let channels = null;
    if (hex) {
      channels = [
        parseInt(hex[1].slice(0, 2), 16),
        parseInt(hex[1].slice(2, 4), 16),
        parseInt(hex[1].slice(4, 6), 16)
      ];
    } else if (rgb) {
      channels = [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])];
    }
    if (channels) {
      const brightness = (channels[0] * 299 + channels[1] * 587 + channels[2] * 114) / 1000;
      darkMode = brightness < 128;
    }
    return {
      type:"tv-guide-theme",
      vars,
      darkMode
    };
  }

  _sendThemeToIframe(force = false) {
    const target = this._iframe?.contentWindow;
    if (!target) return;
    const message = this._themeMessage();
    const signature = JSON.stringify(message);
    if (!force && signature === this._lastThemeMessageSignature) return;
    this._lastThemeMessageSignature = signature;
    target.postMessage(message, window.location.origin);
  }

  static getConfigElement() {
    return document.createElement("tv-guide-card-editor");
  }

  _t(message) {
    const language = String(this._hass?.locale?.language || this._hass?.language || "en").toLowerCase().replace("_", "-").split("-")[0];
    return (TV_GUIDE_CARD_TRANSLATIONS[language === "no" ? "nb" : language] || TV_GUIDE_CARD_TRANSLATIONS.en)[message] || message;
  }

  static getStubConfig() {
    return {height:1000};
  }

  getGridOptions() {
    return {
      columns:"full",
      min_columns:6
    };
  }

  setConfig(config) {
    this._config = {
      ...config,
      height:Math.max(500, Math.min(2200, Number(config?.height || 1000))),
      theme:String(config?.theme || "").trim()
    };
    this._applyConfiguredTheme();
    this._renderShell();
    this._scheduleThemeSync();
  }

  _applyConfiguredTheme() {
    const themeName = String(this._config?.theme || "").trim();
    const darkMode = Boolean(this._hass?.themes?.darkMode);
    const themes = this._hass?.themes?.themes || {};
    const selectedTheme = themeName ? themes[themeName] : null;
    const inheritedThemeName = String(this._hass?.themes?.theme || "");
    const inheritedTheme = inheritedThemeName ? themes[inheritedThemeName] : null;
    const sourceTheme = themeName ? selectedTheme : inheritedTheme;
    const fingerprint = JSON.stringify([
      themeName || "__inherit__",
      inheritedThemeName,
      darkMode,
      sourceTheme || null
    ]);

    if (fingerprint === this._themeFingerprint) return false;
    this._themeFingerprint = fingerprint;

    for (const property of this._themeProperties) this.style.removeProperty(property);
    this._themeProperties.clear();

    if (!themeName || !selectedTheme || typeof selectedTheme !== "object") return true;

    const modeValues = selectedTheme.modes?.[darkMode ? "dark" : "light"] || {};
    const values = {...selectedTheme, ...modeValues};
    delete values.modes;

    for (const [rawName, rawValue] of Object.entries(values)) {
      if (rawValue === undefined || rawValue === null || typeof rawValue === "object") continue;
      const property = rawName.startsWith("--") ? rawName : "--" + rawName;
      this.style.setProperty(property, String(rawValue));
      this._themeProperties.add(property);
    }
    return true;
  }

  set hass(hass) {
    this._hass = hass;
    this._applyConfiguredTheme();
    this._scheduleThemeSync();
    const loading = this.shadowRoot?.querySelector(".loading");
    if (loading && !this._started) loading.textContent = this._t("TV Guide wird geladen …");
    if (this.isConnected && !this._started) this._start();
  }

  _isCardPicker() {
    let node = this;
    while (node) {
      if (node.localName === "hui-card-picker") return true;
      node = node.parentNode || node.host;
    }
    return false;
  }

  connectedCallback() {
    this._attachThemeReadyListener();
    this._watchInheritedTheme();
    this._renderShell();
    if (this._hass && !this._started) this._start();
  }

  disconnectedCallback() {
    this._startGeneration++;
    this._detachThemeReadyListener();
    this._themeObserver?.disconnect();
    this._themeObserver = null;
    if (this._themeSyncFrame !== null) window.cancelAnimationFrame(this._themeSyncFrame);
    this._themeSyncFrame = null;
    if (this._themeRetryTimer !== null) window.clearTimeout(this._themeRetryTimer);
    this._themeRetryTimer = null;
    if (this._sessionTimer) window.clearInterval(this._sessionTimer);
    this._sessionTimer = null;
    this._started = false;
    this._iframe = null;
  }

  getCardSize() {
    return Math.max(10, Math.ceil(this._config.height / 50));
  }

  _renderShell(message = this._t("TV Guide wird geladen …")) {
    if (!this.shadowRoot) return;
    if (this._isCardPicker()) {
      this.shadowRoot.innerHTML = `
        <style>
          :host { display:block; width:100%; }
          .brand { display:flex; align-items:center; justify-content:center;
            min-height:180px; padding:16px; box-sizing:border-box; }
          svg { display:block; width:250px; max-width:100%; height:auto; }
        </style>
        <div class="brand" role="img" aria-label="TV Guide">${TV_GUIDE_PICKER_LOGO}</div>
      `;
      return;
    }
    const iframe = this._iframe;
    if (iframe && iframe.isConnected) {
      iframe.style.height = this._config.height + "px";
      return;
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display:block;
          width:100%;
        }
        ha-card {
          display:block;
          width:100%;
          padding:0;
          margin:0;
          overflow:hidden;
          background:var(--primary-background-color);
          box-shadow:none;
          border:0;
        }
        .loading {
          box-sizing:border-box;
          min-height:180px;
          display:flex;
          align-items:center;
          justify-content:center;
          padding:24px;
          color:var(--secondary-text-color);
          font:var(--paper-font-body1_-_font,inherit);
        }
        iframe {
          display:block;
          width:100%;
          border:0;
          background:var(--primary-background-color);
        }
      </style>
      <ha-card>
        <div class="loading">${message}</div>
      </ha-card>
    `;
  }

  _setError(message) {
    // Promise.all can reject while the ingress-session request is still pending.
    // Invalidate that request before it can overwrite a working session cookie.
    this._startGeneration++;
    this._session = "";
    this._started = false;
    this._iframe = null;
    this._renderShell(message || this._t("TV Guide konnte nicht geladen werden."));
  }

  _panelCandidates() {
    const panels = this._hass?.panels || {};
    return Object.entries(panels).map(([key, panel]) => ({
      key:String(key || ""),
      title:String(panel?.title || panel?.config?.title || ""),
      addon:String(panel?.config?.addon || "")
    }));
  }

  async _findAddonSlug() {
    for (const panel of this._panelCandidates()) {
      if (
        panel.key.endsWith("_tv_guide") ||
        panel.key === "tv_guide" ||
        panel.title === "TV Programm" ||
        panel.title === "TV Guide"
      ) {
        return panel.addon || panel.key;
      }
    }

    const result = await this._hass.callWS({
      type:"supervisor/api",
      endpoint:"/ingress/panels",
      method:"get"
    });
    const panels = result?.panels || {};
    for (const [key, panel] of Object.entries(panels)) {
      const title = String(panel?.title || "");
      if (
        String(key).endsWith("_tv_guide") ||
        String(key) === "tv_guide" ||
        title === "TV Programm" ||
        title === "TV Guide"
      ) {
        return String(key);
      }
    }

    throw new Error(this._t("TV-Guide-App wurde in Home Assistant nicht gefunden."));
  }

  async _createIngressSession(generation = this._startGeneration) {
    const response = await this._hass.callWS({
      type:"supervisor/api",
      endpoint:"/ingress/session",
      method:"post"
    });
    if (!this.isConnected || generation !== this._startGeneration) return "";
    const session = String(response?.session || "");
    if (!session) throw new Error("Ingress-Sitzung konnte nicht erstellt werden.");

    document.cookie =
      "ingress_session=" + session +
      ";path=/api/hassio_ingress/;SameSite=Strict" +
      (location.protocol === "https:" ? ";Secure" : "");

    this._session = session;
    return session;
  }

  async _loadAddonInfo(slug) {
    return this._hass.callWS({
      type:"supervisor/api",
      endpoint:"/addons/" + encodeURIComponent(slug) + "/info",
      method:"get"
    });
  }

  _startSessionKeepAlive() {
    const generation = this._startGeneration;
    let pending = false;
    if (this._sessionTimer) window.clearInterval(this._sessionTimer);
    this._sessionTimer = window.setInterval(async () => {
      if (pending || !this.isConnected || generation !== this._startGeneration || !this._hass || !this._session) return;
      pending = true;
      try {
        await this._hass.callWS({
          type:"supervisor/api",
          endpoint:"/ingress/validate_session",
          method:"post",
          data:{session:this._session}
        });
      } catch {
        if (!this.isConnected || generation !== this._startGeneration) return;
        try {
          await this._createIngressSession(generation);
        } catch {}
      } finally {
        pending = false;
      }
    }, 60000);
  }

  async _start() {
    if (!this.isConnected || this._started || !this._hass || this._isCardPicker()) return;
    const generation = ++this._startGeneration;
    const isCurrent = () => this.isConnected && generation === this._startGeneration;
    this._started = true;
    this._renderShell();

    try {
      const slug = await this._findAddonSlug();
      if (!isCurrent()) return;
      const [, addon] = await Promise.all([
        this._createIngressSession(generation),
        this._loadAddonInfo(slug)
      ]);
      if (!isCurrent()) return;

      if (!addon?.version) {
        throw new Error(this._t("TV Guide ist nicht installiert."));
      }
      if (!addon?.state || !["startup","started"].includes(addon.state)) {
        throw new Error(this._t("TV Guide ist nicht gestartet."));
      }
      if (!addon?.ingress_url) {
        throw new Error(this._t("Für TV Guide ist keine Ingress-Adresse verfügbar."));
      }

      const card = this.shadowRoot.querySelector("ha-card");
      if (!card) throw new Error(this._t("TV-Guide-Karte konnte nicht aufgebaut werden."));

      card.innerHTML = "";
      const iframe = document.createElement("iframe");
      this._lastThemeMessageSignature = "";
      iframe.title = "TV Guide";
      const iframeUrl = new URL(addon.ingress_url, window.location.origin);
      iframeUrl.searchParams.set("tv_guide_card", "1");
      iframeUrl.searchParams.set("tv_guide_version", addon.version);
      iframeUrl.searchParams.set("tv_guide_theme", this._config.theme || "__dashboard__");
      iframe.src = iframeUrl.toString();
      iframe.style.height = this._config.height + "px";
      iframe.style.background =
        getComputedStyle(this).getPropertyValue("--primary-background-color").trim() ||
        "transparent";
      iframe.style.opacity = "0";
      iframe.style.transition = "opacity 80ms linear";
      iframe.setAttribute("allow", "clipboard-read; clipboard-write");
      iframe.addEventListener("load", () => {
        if (!isCurrent() || this._iframe !== iframe) return;
        this._sendThemeToIframe(true);
        if (this._themeRetryTimer !== null) window.clearTimeout(this._themeRetryTimer);
        this._themeRetryTimer = window.setTimeout(() => {
          this._themeRetryTimer = null;
          if (isCurrent() && this._iframe === iframe && iframe.style.opacity !== "1") {
            this._sendThemeToIframe(true);
          }
        }, 120);
      });
      card.appendChild(iframe);
      this._iframe = iframe;
      this._startSessionKeepAlive();
    } catch (err) {
      if (!isCurrent()) return;
      console.error("[TV Guide] Ingress konnte nicht geladen werden", err);
      this._setError(err?.message || this._t("TV Guide konnte nicht geladen werden."));
    }
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
    description:"Full-width TV guide with the same features as the sidebar panel",
    preview:true
  });
}
