const TV_GUIDE_CARD_TRANSLATIONS = {"de":{"TV Guide wird geladen …":"TV Guide wird geladen …","TV Guide konnte nicht geladen werden.":"TV Guide konnte nicht geladen werden.","TV Guide ist nicht installiert.":"TV Guide ist nicht installiert.","TV Guide ist nicht gestartet.":"TV Guide ist nicht gestartet.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Für TV Guide ist keine Ingress-Adresse verfügbar.","TV-Guide-Karte konnte nicht aufgebaut werden.":"TV-Guide-Karte konnte nicht aufgebaut werden.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV-Guide-App wurde in Home Assistant nicht gefunden."},"en":{"TV Guide wird geladen …":"Loading TV Guide …","TV Guide konnte nicht geladen werden.":"Could not load TV Guide.","TV Guide ist nicht installiert.":"TV Guide is not installed.","TV Guide ist nicht gestartet.":"TV Guide is not running.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"No ingress address is available for TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Could not create the TV Guide card.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide was not found in Home Assistant."},"nl":{"TV Guide wird geladen …":"TV Guide laden …","TV Guide konnte nicht geladen werden.":"TV Guide kon niet worden geladen.","TV Guide ist nicht installiert.":"TV Guide is niet geïnstalleerd.","TV Guide ist nicht gestartet.":"TV Guide is niet gestart.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Geen ingress-adres beschikbaar voor TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"De TV Guide-kaart kon niet worden gemaakt.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide is niet gevonden in Home Assistant."},"fr":{"TV Guide wird geladen …":"Chargement de TV Guide…","TV Guide konnte nicht geladen werden.":"Impossible de charger TV Guide.","TV Guide ist nicht installiert.":"TV Guide n’est pas installé.","TV Guide ist nicht gestartet.":"TV Guide n’est pas démarré.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Aucune adresse ingress disponible pour TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Impossible de créer la carte TV Guide.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide est introuvable dans Home Assistant."},"it":{"TV Guide wird geladen …":"Caricamento di TV Guide…","TV Guide konnte nicht geladen werden.":"Impossibile caricare TV Guide.","TV Guide ist nicht installiert.":"TV Guide non è installato.","TV Guide ist nicht gestartet.":"TV Guide non è avviato.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Nessun indirizzo ingress disponibile per TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Impossibile creare la scheda TV Guide.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide non è stato trovato in Home Assistant."},"nb":{"TV Guide wird geladen …":"Laster TV Guide …","TV Guide konnte nicht geladen werden.":"Kunne ikke laste TV Guide.","TV Guide ist nicht installiert.":"TV Guide er ikke installert.","TV Guide ist nicht gestartet.":"TV Guide er ikke startet.","Für TV Guide ist keine Ingress-Adresse verfügbar.":"Ingen ingress-adresse er tilgjengelig for TV Guide.","TV-Guide-Karte konnte nicht aufgebaut werden.":"Kunne ikke opprette TV Guide-kortet.","TV-Guide-App wurde in Home Assistant nicht gefunden.":"TV Guide ble ikke funnet i Home Assistant."}};
class TVGuideCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {height: 1000};
    this._hass = null;
    this._started = false;
    this._session = "";
    this._sessionTimer = null;
    this._iframe = null;
  }

  _t(message) {
    const language = String(this._hass?.locale?.language || this._hass?.language || "en").toLowerCase().replace("_", "-").split("-")[0];
    return (TV_GUIDE_CARD_TRANSLATIONS[language === "no" ? "nb" : language] || TV_GUIDE_CARD_TRANSLATIONS.en)[message] || message;
  }

  static getStubConfig() {
    return {height: 1000};
  }

  getGridOptions() {
    return {
      columns:"full",
      min_columns:6
    };
  }

  setConfig(config) {
    this._config = {
      height:Math.max(500, Math.min(2200, Number(config?.height || 1000)))
    };
    this._renderShell();
  }

  set hass(hass) {
    this._hass = hass;
    const loading = this.shadowRoot?.querySelector(".loading");
    if (loading && !this._started) loading.textContent = this._t("TV Guide wird geladen …");
    if (this.isConnected && !this._started) this._start();
  }

  connectedCallback() {
    this._renderShell();
    if (this._hass && !this._started) this._start();
  }

  disconnectedCallback() {
    if (this._sessionTimer) window.clearInterval(this._sessionTimer);
    this._sessionTimer = null;
    this._started = false;
  }

  getCardSize() {
    return Math.max(10, Math.ceil(this._config.height / 50));
  }

  _renderShell(message = this._t("TV Guide wird geladen …")) {
    if (!this.shadowRoot) return;
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

  async _createIngressSession() {
    const response = await this._hass.callWS({
      type:"supervisor/api",
      endpoint:"/ingress/session",
      method:"post"
    });
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
    if (this._sessionTimer) window.clearInterval(this._sessionTimer);
    this._sessionTimer = window.setInterval(async () => {
      if (!this._hass || !this._session) return;
      try {
        await this._hass.callWS({
          type:"supervisor/api",
          endpoint:"/ingress/validate_session",
          method:"post",
          data:{session:this._session}
        });
      } catch {
        try {
          await this._createIngressSession();
        } catch {}
      }
    }, 60000);
  }

  async _start() {
    if (this._started || !this._hass) return;
    this._started = true;
    this._renderShell();

    try {
      const slug = await this._findAddonSlug();
      const sessionPromise = this._createIngressSession();
      const addon = await this._loadAddonInfo(slug);
      await sessionPromise;

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
      iframe.title = "TV Guide";
      iframe.src = addon.ingress_url;
      iframe.style.height = this._config.height + "px";
      iframe.setAttribute("allow", "clipboard-read; clipboard-write");
      card.appendChild(iframe);
      this._iframe = iframe;
      this._startSessionKeepAlive();
    } catch (err) {
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
    preview:false
  });
}
