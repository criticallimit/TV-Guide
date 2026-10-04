const grid = document.getElementById("grid");
const headline = document.getElementById("headline");
const statusLine = document.getElementById("status");
const detail = document.getElementById("detail");
const detailBody = document.getElementById("detailBody");
const bookmarkProgram = document.getElementById("bookmarkProgram");
const bookmarkCount = document.getElementById("bookmarkCount");
const showBookmarks = document.getElementById("showBookmarks");
const bookmarksDialog = document.getElementById("bookmarksDialog");
const bookmarksBody = document.getElementById("bookmarksBody");
const testNotification = document.getElementById("testNotification");
const testNotificationStatus = document.getElementById("testNotificationStatus");
const customTimeBar = document.getElementById("customTimeBar");
const customDate = document.getElementById("customDate");
const customTime = document.getElementById("customTime");
const applyCustomTime = document.getElementById("applyCustomTime");
const reminderEnabled = document.getElementById("reminderEnabled");
const reminderMinutes = document.getElementById("reminderMinutes");
const reminderStatus = document.getElementById("reminderStatus");
const showChannelSettings = document.getElementById("showChannelSettings");
const channelSettingsDialog = document.getElementById("channelSettingsDialog");
const channelSettingsList = document.getElementById("channelSettingsList");
const saveChannelSettings = document.getElementById("saveChannelSettings");
const resetChannelSettings = document.getElementById("resetChannelSettings");
const cancelChannelSettings = document.getElementById("cancelChannelSettings");
const channelSettingsStatus = document.getElementById("channelSettingsStatus");
const showAppSettings = document.getElementById("showAppSettings");
const appSettingsDialog = document.getElementById("appSettingsDialog");
const settingDefaultView = document.getElementById("settingDefaultView");
const settingColumns = document.getElementById("settingColumns");
const settingMaxChannels = document.getElementById("settingMaxChannels");
const settingTheme = document.getElementById("settingTheme");
const settingRefresh = document.getElementById("settingRefresh");
const settingEpgUrl = document.getElementById("settingEpgUrl");
const settingNotificationService = document.getElementById("settingNotificationService");
const saveAppSettings = document.getElementById("saveAppSettings");
const cancelAppSettings = document.getElementById("cancelAppSettings");
const appSettingsStatus = document.getElementById("appSettingsStatus");
const lovelaceCardState = document.getElementById("lovelaceCardState");
const lovelaceResourceUrl = document.getElementById("lovelaceResourceUrl");
const copyLovelaceResource = document.getElementById("copyLovelaceResource");
const openLovelaceResources = document.getElementById("openLovelaceResources");
const checkLovelaceCard = document.getElementById("checkLovelaceCard");
const lovelaceSetupStatus = document.getElementById("lovelaceSetupStatus");

const THEME_VARS = [
  "--primary-background-color",
  "--secondary-background-color",
  "--card-background-color",
  "--ha-card-background",
  "--primary-text-color",
  "--secondary-text-color",
  "--divider-color",
  "--primary-color",
  "--accent-color"
];

function rgbLuminance(value) {
  const m = String(value || "").match(/rgba?\((\d+)\D+(\d+)\D+(\d+)/i);
  if (!m) return null;
  const [r,g,b] = [Number(m[1]), Number(m[2]), Number(m[3])].map(v => v / 255);
  const linear = c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
}

function syncHomeAssistantTheme() {
  const configured = guide?.ui?.theme_mode || "auto";
  if (configured === "dark" || configured === "light") {
    for (const name of THEME_VARS) {
      document.documentElement.style.removeProperty(name);
    }
    document.documentElement.dataset.haTheme = configured;
    return true;
  }

  try {
    if (window.parent !== window) {
      const parentDoc = window.parent.document;
      const parentStyle = window.parent.getComputedStyle(parentDoc.documentElement);
      let copied = 0;

      for (const name of THEME_VARS) {
        const value = parentStyle.getPropertyValue(name).trim();
        if (value) {
          document.documentElement.style.setProperty(name, value);
          copied++;
        }
      }

      const parentBody = parentDoc.body;
      const parentHtml = parentDoc.documentElement;
      const bodyStyle = parentBody ? window.parent.getComputedStyle(parentBody) : null;
      const bg =
        parentStyle.getPropertyValue("--primary-background-color").trim() ||
        bodyStyle?.backgroundColor ||
        "";
      const lum = rgbLuminance(bg);

      const dark =
        parentHtml.classList.contains("dark-mode") ||
        parentBody?.classList.contains("dark-mode") ||
        parentStyle.colorScheme.includes("dark") ||
        (lum !== null && lum < 0.35);

      document.documentElement.dataset.haTheme = dark ? "dark" : "light";
      if (copied > 0) return true;
    }
  } catch {}

  document.documentElement.dataset.haTheme =
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  return false;
}

function watchHomeAssistantTheme() {
  syncHomeAssistantTheme();
  try {
    if (window.parent === window) return;
    const target = window.parent.document.documentElement;
    const observer = new MutationObserver(() => syncHomeAssistantTheme());
    observer.observe(target, {attributes:true, attributeFilter:["class","style"]});
    if (window.parent.document.body) {
      observer.observe(window.parent.document.body, {attributes:true, attributeFilter:["class","style"]});
    }
  } catch {}
}

const fmt = new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"});
const dateFmt = new Intl.DateTimeFormat("de-DE", {weekday:"short", day:"2-digit", month:"2-digit"});

let guide = null;
let mode = "now";
let selectedDate = startOfDay(new Date());
let customTarget = null;
let activeDetail = null;
let bookmarks = loadBookmarksLocal();
let startupReloadTimer = null;
let channelSettings = null;
let channelView = "main";
let draggedChannelId = null;
let reminders = [];

function startOfDay(value) {
  return TVGuideCore.startOfDay(value);
}

function dateKey(value) {
  return TVGuideCore.dateKey(value);
}

function sameDay(a,b) {
  return TVGuideCore.sameDay(a,b);
}

function loadBookmarksLocal() {
  try { return JSON.parse(localStorage.getItem("tvguide-bookmarks") || "[]"); }
  catch { return []; }
}

function saveBookmarksLocal() {
  localStorage.setItem("tvguide-bookmarks", JSON.stringify(bookmarks));
  bookmarkCount.textContent = String(bookmarks.length);
}

async function syncBookmark(action, item) {
  const url = new URL("api/bookmarks", window.location.href);
  const body = action === "remove"
    ? {action:"remove", id:item.id}
    : {action:"upsert", ...item};
  const res = await fetch(url, {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const payload = await res.json();
  if (!res.ok || !payload.ok) throw new Error(payload.error || "Merkliste konnte nicht gespeichert werden.");
  bookmarks = Array.isArray(payload.bookmarks) ? payload.bookmarks : [];
  saveBookmarksLocal();
}

async function loadBookmarksRemote() {
  const local = loadBookmarksLocal();
  const migrationDone = localStorage.getItem("tvguide-bookmarks-migrated") === "1";

  try {
    const url = new URL("api/bookmarks", window.location.href);
    const res = await fetch(url, {cache:"no-store"});
    if (!res.ok) throw new Error("Merkliste konnte nicht geladen werden.");
    const payload = await res.json();
    bookmarks = Array.isArray(payload.bookmarks) ? payload.bookmarks : [];

    // Import old browser-only bookmarks exactly once. Afterwards the
    // persistent add-on store is authoritative so deleted entries cannot
    // reappear from a stale browser cache.
    if (!migrationDone) {
      for (const item of local) {
        if (!bookmarks.some(x => x.id === item.id) && new Date(item.end) > new Date()) {
          await syncBookmark("upsert", item);
        }
      }
      localStorage.setItem("tvguide-bookmarks-migrated", "1");
    }
  } catch {
    bookmarks = local;
  }

  saveBookmarksLocal();
}

function bookmarkId(channel, program) {
  return channel.id + "|" + program.start + "|" + program.title;
}

function pct(start, end, now = new Date()) {
  return TVGuideCore.pct(start, end, now);
}

function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

function activeChannels() {
  if (!guide?.channels?.length) return [];
  const ids = channelView === "custom"
    ? (guide.custom_channel_ids || [])
    : (guide.main_channel_ids || []);
  const byId = new Map(guide.channels.map(channel => [channel.id, channel]));
  return ids.map(id => byId.get(id)).filter(Boolean);
}

function targetForMode(wanted) {
  return TVGuideCore.targetForMode(wanted, selectedDate, customTarget);
}

function modeIndex(programs, wanted) {
  return TVGuideCore.modeIndex(programs, wanted, selectedDate, customTarget);
}

function remainingMinutes(program) {
  return TVGuideCore.remainingMinutes(program);
}

function channelHeader(channel) {
  return TVGuideCore.channelHeader(channel, "");
}

function isBookmarked(channel, program) {
  const id = bookmarkId(channel, program);
  return bookmarks.some(x => x.id === id);
}

function reminderFor(channel, program) {
  const id = bookmarkId(channel, program);
  return reminders.find(item => item.id === id) || null;
}

function updateDetailControls() {
  if (!activeDetail) return;
  const {channel, program} = activeDetail;
  const marked = isBookmarked(channel, program);
  const reminder = reminderFor(channel, program);
  const started = new Date(program.start) <= new Date();

  bookmarkProgram.textContent = marked ? "★ Löschen" : "☆ Merken";
  bookmarkProgram.classList.toggle("active", marked);

  reminderEnabled.checked = Boolean(reminder);
  reminderEnabled.disabled = !marked || started;
  reminderMinutes.hidden = !reminderEnabled.checked;
  reminderMinutes.disabled = started || !reminderEnabled.checked;
  reminderMinutes.value = reminder ? String(reminder.minutes) : "10";

  if (!marked) {
    reminderStatus.textContent = "";
  } else if (started) {
    reminderStatus.textContent = reminder ? "Erinnerung ist gesetzt." : "";
  } else if (reminder) {
    reminderStatus.textContent = "Erinnerung " + reminder.minutes + " Minuten vorher.";
  } else {
    reminderStatus.textContent = "";
  }
}

async function loadReminders() {
  try {
    const url = new URL("api/reminders", window.location.href);
    const res = await fetch(url, {cache:"no-store"});
    if (!res.ok) throw new Error("Erinnerungen konnten nicht geladen werden.");
    const payload = await res.json();
    reminders = Array.isArray(payload.reminders) ? payload.reminders : [];
  } catch {
    reminders = [];
  }
}

async function saveReminderForActiveDetail(enabled, minutes) {
  if (!activeDetail) return;
  const {channel, program} = activeDetail;
  const id = bookmarkId(channel, program);

  const url = new URL("api/reminders", window.location.href);
  const body = enabled
    ? {
        action:"upsert",
        id,
        channel:channel.name,
        channelId:channel.id,
        title:program.title,
        start:program.start,
        end:program.end,
        minutes
      }
    : {action:"remove", id};

  const res = await fetch(url, {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(body)
  });
  const payload = await res.json();
  if (!res.ok || !payload.ok) {
    throw new Error(payload.error || "Erinnerung konnte nicht gespeichert werden.");
  }
  reminders = Array.isArray(payload.reminders) ? payload.reminders : [];
}

function showDetail(channel, program) {
  activeDetail = {channel, program};
  const subtitle = program.subtitle ? '<p class="detail-subtitle">' + escapeHtml(program.subtitle) + '</p>' : "";
  const category = program.category ? '<p><strong>Genre:</strong> ' + escapeHtml(program.category) + '</p>' : "";
  const description = program.desc ? '<p>' + escapeHtml(program.desc) + '</p>' : '<p>Keine Beschreibung verfügbar.</p>';

  detailBody.innerHTML =
    '<div class="detail-channel">' + escapeHtml(channel.name) + '</div>' +
    '<h2>' + escapeHtml(program.title) + '</h2>' +
    '<p class="detail-time">' + dateFmt.format(new Date(program.start)) + ' · ' +
      fmt.format(new Date(program.start)) + '–' + fmt.format(new Date(program.end)) + '</p>' +
    subtitle + category + description;
  updateDetailControls();
  detail.showModal();
}

async function removeReminderById(id) {
  if (!reminders.some(item => item.id === id)) return;
  try {
    const url = new URL("api/reminders", window.location.href);
    const res = await fetch(url, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({action:"remove", id})
    });
    const payload = await res.json();
    if (res.ok && payload.ok) {
      reminders = Array.isArray(payload.reminders) ? payload.reminders : [];
    }
  } catch {}
}

async function toggleBookmark() {
  if (!activeDetail) return;
  const {channel, program} = activeDetail;
  const id = bookmarkId(channel, program);
  const index = bookmarks.findIndex(x => x.id === id);

  bookmarkProgram.disabled = true;

  try {
    if (index >= 0) {
      const item = bookmarks[index];
      bookmarks.splice(index,1);
      saveBookmarksLocal();
      await Promise.allSettled([
        syncBookmark("remove", item),
        removeReminderById(id)
      ]);
      updateDetailControls();
      return;
    }

    const item = {
      id,
      channel:channel.name,
      channelId:channel.id,
      title:program.title,
      start:program.start,
      end:program.end
    };
    bookmarks.push(item);
    bookmarks.sort((a,b) => new Date(a.start) - new Date(b.start));
    saveBookmarksLocal();
    try {
      await syncBookmark("upsert", item);
    } catch {}
    updateDetailControls();
  } finally {
    bookmarkProgram.disabled = false;
  }
}

function renderBookmarks() {
  const now = new Date();
  bookmarks = bookmarks.filter(x => new Date(x.end) > now);
  saveBookmarksLocal();
  if (!bookmarks.length) {
    bookmarksBody.innerHTML = '<p class="empty-bookmarks">Noch keine Sendung gemerkt.</p>';
    return;
  }
  bookmarksBody.innerHTML = bookmarks.map(item => {
    const reminder = reminders.find(r => r.id === item.id);
    const reminderText = reminder ? ' · ⏰ ' + reminder.minutes + ' Min.' : '';
    return '<div class="bookmark-row"><div><strong>' + escapeHtml(item.title) + '</strong>' +
      '<div>' + escapeHtml(item.channel) + ' · ' + dateFmt.format(new Date(item.start)) +
      ' · ' + fmt.format(new Date(item.start)) + reminderText + '</div></div>' +
      '<button type="button" data-remove="' + escapeHtml(item.id) + '">×</button></div>';
  }).join("");
  bookmarksBody.querySelectorAll("[data-remove]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.remove;
      const item = bookmarks.find(x => x.id === id) || {id};
      bookmarks = bookmarks.filter(x => x.id !== id);
      saveBookmarksLocal();
      await Promise.allSettled([
        syncBookmark("remove", item),
        removeReminderById(id)
      ]);
      renderBookmarks();
    });
  });
}

async function testConfiguredNotification() {
  testNotification.disabled = true;
  testNotificationStatus.textContent = "Wird gesendet …";
  try {
    const url = new URL("api/test-notification", window.location.href);
    const res = await fetch(url, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({test:true})
    });
    const payload = await res.json();
    if (!res.ok || !payload.ok) throw new Error(payload.error || "Testbenachrichtigung konnte nicht gesendet werden.");
    testNotificationStatus.textContent = "Gesendet über " + payload.service;
  } catch (err) {
    testNotificationStatus.textContent = err.message;
  } finally {
    testNotification.disabled = false;
  }
}

function lovelaceCardRegistered() {
  const hosts = [window, window.parent, window.top];
  for (const host of hosts) {
    try {
      if (host?.customElements?.get("tv-guide-card")) return true;
      if (Array.isArray(host?.customCards) &&
          host.customCards.some(card => card?.type === "tv-guide-card")) return true;
    } catch {}
  }
  return false;
}

function getHomeAssistantConnection() {
  const docs = [];
  try { docs.push(window.document); } catch {}
  try { if (window.parent?.document) docs.push(window.parent.document); } catch {}
  try { if (window.top?.document) docs.push(window.top.document); } catch {}

  for (const doc of docs) {
    try {
      const root = doc.querySelector("home-assistant");
      const connection = root?.hass?.connection;
      if (connection?.sendMessagePromise) return connection;
    } catch {}
  }
  return null;
}

async function lovelaceResourceRegistered() {
  const connection = getHomeAssistantConnection();
  if (!connection) return null;

  try {
    const resources = await connection.sendMessagePromise({type:"lovelace/resources"});
    if (!Array.isArray(resources)) return false;
    return resources.some(resource => {
      const url = String(resource?.url || "").split("?")[0];
      return url === "/local/tv-guide-card-loader.js";
    });
  } catch {
    return null;
  }
}

async function checkLovelaceSetup() {
  lovelaceCardState.textContent = "Wird geprüft …";
  lovelaceCardState.className = "lovelace-state";
  lovelaceSetupStatus.textContent = "";

  let assetReady = false;
  try {
    const res = await fetch("/local/tv-guide-card-loader.js?t=" + Date.now(), {
      method:"GET",
      cache:"no-store"
    });
    assetReady = res.ok;
  } catch {}

  const cardLoaded = lovelaceCardRegistered();
  const resourceRegistered = await lovelaceResourceRegistered();

  if (cardLoaded) {
    lovelaceCardState.textContent = "Bereit";
    lovelaceCardState.className = "lovelace-state ready";
    lovelaceSetupStatus.textContent = "Die TV-Guide-Karte ist geladen und steht im Kartenwähler zur Verfügung.";
    return;
  }

  if (resourceRegistered === true) {
    lovelaceCardState.textContent = "Ressource eingetragen";
    lovelaceCardState.className = "lovelace-state pending";
    lovelaceSetupStatus.textContent = "Die Ressource ist bereits in Home Assistant eingetragen. Lade die Home-Assistant-Oberfläche jetzt einmal vollständig neu; danach sollte TV Guide im Kartenwähler erscheinen.";
    return;
  }

  if (assetReady && resourceRegistered === false) {
    lovelaceCardState.textContent = "Ressource fehlt";
    lovelaceCardState.className = "lovelace-state pending";
    lovelaceSetupStatus.textContent = "Die Kartendatei ist installiert, aber noch nicht als Home-Assistant-Ressource eingetragen.";
    return;
  }

  if (assetReady) {
    lovelaceCardState.textContent = "Datei bereit";
    lovelaceCardState.className = "lovelace-state pending";
    lovelaceSetupStatus.textContent = "Die Kartendatei ist installiert. Der Ressourcenstatus konnte aus der Ingress-Seite nicht sicher gelesen werden. Falls du sie bereits eingetragen hast, lade Home Assistant einmal vollständig neu.";
  } else {
    lovelaceCardState.textContent = "Noch nicht bereit";
    lovelaceCardState.className = "lovelace-state error";
    lovelaceSetupStatus.textContent = "Die Kartendatei ist noch nicht unter /local erreichbar. Falls /local bisher nicht verwendet wurde, starte Home Assistant einmal neu und prüfe danach erneut.";
  }
}

async function copyLovelaceResourceUrl() {
  const value = lovelaceResourceUrl.textContent.trim();

  const clipboardTargets = [];
  try { if (window.top?.navigator?.clipboard?.writeText) clipboardTargets.push(window.top.navigator.clipboard); } catch {}
  try { if (window.parent?.navigator?.clipboard?.writeText) clipboardTargets.push(window.parent.navigator.clipboard); } catch {}
  try { if (navigator.clipboard?.writeText) clipboardTargets.push(navigator.clipboard); } catch {}

  for (const clipboard of clipboardTargets) {
    try {
      await clipboard.writeText(value);
      lovelaceSetupStatus.textContent = "Ressourcen-URL kopiert.";
      return;
    } catch {}
  }

  const docs = [];
  try { if (window.top?.document) docs.push(window.top.document); } catch {}
  try { if (window.parent?.document) docs.push(window.parent.document); } catch {}
  docs.push(document);

  for (const doc of docs) {
    try {
      const textarea = doc.createElement("textarea");
      textarea.value = value;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.top = "0";
      textarea.style.opacity = "0";
      doc.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      textarea.setSelectionRange(0, value.length);
      const ok = doc.execCommand("copy");
      textarea.remove();

      if (ok) {
        lovelaceSetupStatus.textContent = "Ressourcen-URL kopiert.";
        return;
      }
    } catch {}
  }

  try {
    const range = document.createRange();
    range.selectNodeContents(lovelaceResourceUrl);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    lovelaceSetupStatus.textContent = "Automatisches Kopieren wird vom Browser blockiert. Die Ressourcen-URL ist markiert; bitte einmal manuell kopieren.";
  } catch {
    lovelaceSetupStatus.textContent = "Automatisches Kopieren wird vom Browser blockiert. Bitte die Ressourcen-URL manuell kopieren.";
  }
}

function openLovelaceResourcesPage() {
  try {
    if (window.parent !== window) {
      window.parent.location.href = "/config/lovelace/resources";
    } else {
      window.location.href = "/config/lovelace/resources";
    }
  } catch {
    lovelaceSetupStatus.textContent = "Öffnen nicht möglich. Bitte Einstellungen → Dashboards → Ressourcen manuell öffnen.";
  }
}

async function loadNotificationServiceChoices(currentService) {
  const fallback = currentService || "persistent_notification.create";
  const url = new URL("api/notification-services", window.location.href);
  let services = [];

  try {
    const res = await fetch(url, {cache:"no-store"});
    if (!res.ok) throw new Error("Empfänger konnten nicht geladen werden.");
    const payload = await res.json();
    services = Array.isArray(payload.services) ? payload.services : [];
  } catch {
    services = [{
      service:"persistent_notification.create",
      label:"Home Assistant",
      type:"home_assistant"
    }];
  }

  if (!services.some(item => item.service === fallback)) {
    services.push({
      service:fallback,
      label:"Aktuell konfiguriert · " + fallback,
      type:"existing"
    });
  }

  settingNotificationService.innerHTML = services
    .map(item =>
      '<option value="' + escapeHtml(item.service) + '">' +
      escapeHtml(item.label || item.service) +
      '</option>'
    )
    .join("");
  settingNotificationService.value = fallback;
}

async function openAppSettings() {
  appSettingsStatus.textContent = "Einstellungen werden geladen …";
  appSettingsDialog.showModal();
  try {
    const url = new URL("api/settings", window.location.href);
    const res = await fetch(url, {cache:"no-store"});
    if (!res.ok) throw new Error("Einstellungen konnten nicht geladen werden.");
    const settings = await res.json();
    settingDefaultView.value = settings.default_view || "now";
    settingColumns.value = String(settings.columns_desktop || 5);
    settingMaxChannels.value = String(settings.max_channels ?? 0);
    settingTheme.value = settings.theme_mode || "auto";
    settingRefresh.value = String(settings.refresh_minutes || 180);
    settingEpgUrl.value = settings.epg_url || "";
    await loadNotificationServiceChoices(
      settings.notification_service || "persistent_notification.create"
    );
    appSettingsStatus.textContent = "";
    await checkLovelaceSetup();
  } catch (err) {
    appSettingsStatus.textContent = err.message;
  }
}

async function persistAppSettings() {
  appSettingsStatus.textContent = "Wird gespeichert …";
  saveAppSettings.disabled = true;
  try {
    const url = new URL("api/settings", window.location.href);
    const res = await fetch(url, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        default_view:settingDefaultView.value,
        columns_desktop:Number(settingColumns.value),
        max_channels:Number(settingMaxChannels.value),
        theme_mode:settingTheme.value,
        refresh_minutes:Number(settingRefresh.value),
        epg_url:settingEpgUrl.value.trim(),
        notification_service:settingNotificationService.value.trim()
      })
    });
    const payload = await res.json();
    if (!res.ok || !payload.ok) throw new Error(payload.error || "Einstellungen konnten nicht gespeichert werden.");
    appSettingsStatus.textContent = payload.refresh_started
      ? "Gespeichert. Programmdaten werden im Hintergrund aktualisiert."
      : "Gespeichert.";
    await loadGuide();
    window.setTimeout(() => appSettingsDialog.close(), 500);
  } catch (err) {
    appSettingsStatus.textContent = err.message;
  } finally {
    saveAppSettings.disabled = false;
  }
}

function channelSettingsRow(channel, hiddenSet) {
  const row = document.createElement("div");
  row.className = "channel-settings-row";
  row.draggable = true;
  row.dataset.channelId = channel.id;

  const checked = Boolean(channel.selected) && !hiddenSet.has(channel.id);
  const logo = channel.logo_normalized_light || channel.logo_file_light || channel.logo_file || channel.logo_light || channel.logo || "";
  row.innerHTML =
    '<span class="drag-handle" title="Ziehen">☰</span>' +
    '<label class="channel-visible-toggle">' +
      '<input type="checkbox" ' + (checked ? 'checked' : '') + ' aria-label="' + escapeHtml(channel.name) + ' anzeigen">' +
    '</label>' +
    (logo
      ? '<img src="' + escapeHtml(logo) + '" alt="" class="settings-logo" onerror="this.style.display=\'none\'">'
      : '<span class="settings-logo settings-logo-fallback">TV</span>') +
    '<span class="settings-channel-name">' + escapeHtml(channel.name) + '</span>' +
    '<div class="settings-order-buttons">' +
      '<button type="button" class="move-up" title="Nach oben">↑</button>' +
      '<button type="button" class="move-down" title="Nach unten">↓</button>' +
    '</div>';

  row.addEventListener("dragstart", () => {
    draggedChannelId = channel.id;
    row.classList.add("dragging");
  });
  row.addEventListener("dragend", () => {
    draggedChannelId = null;
    row.classList.remove("dragging");
  });
  row.addEventListener("dragover", e => {
    e.preventDefault();
    if (!draggedChannelId || draggedChannelId === channel.id) return;
    const dragged = channelSettingsList.querySelector('[data-channel-id="' + CSS.escape(draggedChannelId) + '"]');
    if (!dragged) return;
    const rect = row.getBoundingClientRect();
    channelSettingsList.insertBefore(dragged, e.clientY < rect.top + rect.height / 2 ? row : row.nextSibling);
  });

  row.querySelector(".move-up").addEventListener("click", () => {
    const prev = row.previousElementSibling;
    if (prev) channelSettingsList.insertBefore(row, prev);
  });
  row.querySelector(".move-down").addEventListener("click", () => {
    const next = row.nextElementSibling;
    if (next) channelSettingsList.insertBefore(next, row);
  });

  return row;
}

function renderChannelSettings() {
  if (!channelSettings) return;
  const byId = new Map(channelSettings.channels.map(channel => [channel.id, channel]));
  const hiddenSet = new Set(channelSettings.hidden || []);
  channelSettingsList.innerHTML = "";

  const rendered = new Set();
  for (const id of channelSettings.order || []) {
    const channel = byId.get(id);
    if (!channel) continue;
    channelSettingsList.appendChild(channelSettingsRow(channel, hiddenSet));
    rendered.add(id);
  }

  for (const channel of channelSettings.channels) {
    if (rendered.has(channel.id)) continue;
    channelSettingsList.appendChild(channelSettingsRow(channel, hiddenSet));
  }
}

async function openChannelSettings() {
  channelSettingsStatus.textContent = "Senderliste wird geladen …";
  channelSettingsDialog.showModal();
  try {
    const url = new URL("api/channel-settings", window.location.href);
    const res = await fetch(url, {cache:"no-store"});
    if (!res.ok) throw new Error("Senderliste konnte nicht geladen werden.");
    channelSettings = await res.json();
    renderChannelSettings();
    channelSettingsStatus.textContent = "";
  } catch (err) {
    channelSettingsStatus.textContent = err.message;
  }
}

async function persistChannelSettings(reset = false) {
  channelSettingsStatus.textContent = "Wird gespeichert …";
  const rows = [...channelSettingsList.querySelectorAll(".channel-settings-row")];
  const order = rows.map(row => row.dataset.channelId);
  const hidden = rows
    .filter(row => !row.querySelector('input[type="checkbox"]').checked)
    .map(row => row.dataset.channelId);

  try {
    const url = new URL("api/channel-settings", window.location.href);
    const res = await fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(reset ? {reset:true} : {order, hidden})
    });
    const payload = await res.json();
    if (!res.ok || !payload.ok) throw new Error(payload.error || "Senderreihenfolge konnte nicht gespeichert werden.");

    if (reset) {
      const reload = await fetch(url, {cache:"no-store"});
      channelSettings = await reload.json();
      renderChannelSettings();
      channelSettingsStatus.textContent = "Standardsortierung wiederhergestellt.";
      return;
    }

    channelSettingsDialog.close();
    channelView = "custom";
    document.querySelectorAll("[data-channel-view]").forEach(button =>
      button.classList.toggle("active", button.dataset.channelView === channelView));
    await loadGuide();
  } catch (err) {
    channelSettingsStatus.textContent = err.message;
  }
}

function headlineText() {
  return TVGuideCore.headlineText(mode, selectedDate, customTarget);
}

function render() {
  if (!guide) return;
  headline.textContent = (channelView === "custom" ? "Meine Sender: " : "Hauptsender: ") + headlineText();

  const channels = activeChannels();
  const availableCount = channels.filter(c => c.available).length;
  statusLine.textContent = guide.error
    ? "EPG-Quelle aktuell nicht vollständig erreichbar – vorhandene Daten werden verwendet."
    : guide.refresh_running
      ? "EPG wird im Hintergrund aktualisiert · " + availableCount + " von " + channels.length + " Sendern"
      : "Live-EPG · " + availableCount + " von " + channels.length + " Sendern";

  grid.innerHTML = channels.length
    ? channels.map(channel => TVGuideCore.renderChannelCard(channel, mode, selectedDate, customTarget, "")).join("")
    : '<div class="empty-channel-list">Noch keine eigenen Sender ausgewählt. Über „☰ Sender“ kannst du deine Senderliste zusammenstellen.</div>';

  grid.querySelectorAll(".channel-card").forEach(section => {
    const channel = channels.find(item => item.id === section.dataset.channelId);
    if (!channel) return;
    section.querySelectorAll("[data-program-start]").forEach(row => {
      const program = (channel.programs || []).find(item => item.start === row.dataset.programStart);
      if (program) row.addEventListener("click", () => showDetail(channel, program));
    });
  });
}

function setMode(nextMode) {
  mode = nextMode;
  if (nextMode === "now") selectedDate = startOfDay(new Date());
  document.querySelectorAll(".tab").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === nextMode));
  customTimeBar.hidden = nextMode !== "other";
  render();
}

function initCustomDate() {
  customDate.value = dateKey(selectedDate);
  customDate.min = dateKey(new Date());
  if (guide?.channels?.length) {
    const dates = guide.channels.flatMap(c => c.programs || [])
      .map(p => new Date(p.end)).filter(d => !Number.isNaN(d.getTime()));
    if (dates.length) customDate.max = dateKey(new Date(Math.max(...dates.map(d => d.getTime()))));
  }
}

async function loadGuide() {
  const url = new URL("api/guide", window.location.href);
  const res = await fetch(url, {cache:"no-store"});
  if (!res.ok) throw new Error("Programmdaten konnten nicht geladen werden.");
  guide = await res.json();

  const columns = Number(guide.ui?.columns_desktop || 5);
  document.documentElement.style.setProperty("--desktop-columns", String(Math.max(3, Math.min(6, columns))));
  syncHomeAssistantTheme();

  if (!document.body.dataset.initialized) {
    mode = ["now","2015","2200"].includes(guide.ui?.default_view) ? guide.ui.default_view : "now";
    document.body.dataset.initialized = "1";
    saveBookmarksLocal();
  }
  initCustomDate();
  document.querySelectorAll(".tab").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === mode));
  render();

  clearTimeout(startupReloadTimer);
  if (guide.refresh_running) {
    startupReloadTimer = setTimeout(() => loadGuide().catch(() => {}), 1500);
  } else {
    startupReloadTimer = null;
  }
}

document.querySelectorAll(".tab").forEach(btn =>
  btn.addEventListener("click", () => setMode(btn.dataset.mode)));

document.querySelectorAll("[data-channel-view]").forEach(button =>
  button.addEventListener("click", () => {
    channelView = button.dataset.channelView === "custom" ? "custom" : "main";
    document.querySelectorAll("[data-channel-view]").forEach(item =>
      item.classList.toggle("active", item.dataset.channelView === channelView));
    initCustomDate();
      render();
  }));


applyCustomTime.addEventListener("click", () => {
  if (!customDate.value || !customTime.value) return;
  const target = new Date(customDate.value + "T" + customTime.value + ":00");
  if (Number.isNaN(target.getTime())) return;
  selectedDate = startOfDay(target);
  customTarget = target;
  render();
});

bookmarkProgram.addEventListener("click", toggleBookmark);
reminderEnabled.addEventListener("change", async () => {
  if (!activeDetail || reminderEnabled.disabled) return;
  reminderEnabled.disabled = true;
  reminderMinutes.hidden = !reminderEnabled.checked;
  reminderMinutes.disabled = true;
  reminderStatus.textContent = reminderEnabled.checked
    ? "Erinnerung wird gespeichert …"
    : "Erinnerung wird entfernt …";
  try {
    await saveReminderForActiveDetail(
      reminderEnabled.checked,
      Number(reminderMinutes.value || 10)
    );
  } catch (err) {
    reminderStatus.textContent = err.message;
  }
  updateDetailControls();
});
reminderMinutes.addEventListener("change", async () => {
  if (!activeDetail || !reminderEnabled.checked || reminderMinutes.disabled) return;
  reminderMinutes.disabled = true;
  reminderStatus.textContent = "Erinnerung wird aktualisiert …";
  try {
    await saveReminderForActiveDetail(
      true,
      Number(reminderMinutes.value || 10)
    );
  } catch (err) {
    reminderStatus.textContent = err.message;
  }
  updateDetailControls();
});
showBookmarks.addEventListener("click", () => {
  renderBookmarks();
  testNotificationStatus.textContent = "";
  bookmarksDialog.showModal();
});
testNotification.addEventListener("click", testConfiguredNotification);
showAppSettings.addEventListener("click", openAppSettings);
copyLovelaceResource.addEventListener("click", copyLovelaceResourceUrl);
openLovelaceResources.addEventListener("click", openLovelaceResourcesPage);
checkLovelaceCard.addEventListener("click", checkLovelaceSetup);
saveAppSettings.addEventListener("click", persistAppSettings);
cancelAppSettings.addEventListener("click", () => appSettingsDialog.close());
showChannelSettings.addEventListener("click", openChannelSettings);
saveChannelSettings.addEventListener("click", () => persistChannelSettings(false));
resetChannelSettings.addEventListener("click", () => persistChannelSettings(true));
cancelChannelSettings.addEventListener("click", () => channelSettingsDialog.close());
detail.querySelector(".close").addEventListener("click", () => detail.close());
bookmarksDialog.querySelector(".bookmarks-close").addEventListener("click", () => bookmarksDialog.close());
appSettingsDialog.querySelector(".app-settings-close").addEventListener("click", () => appSettingsDialog.close());
channelSettingsDialog.querySelector(".channel-settings-close").addEventListener("click", () => channelSettingsDialog.close());
detail.addEventListener("click", e => { if (e.target === detail) detail.close(); });
bookmarksDialog.addEventListener("click", e => { if (e.target === bookmarksDialog) bookmarksDialog.close(); });
appSettingsDialog.addEventListener("click", e => { if (e.target === appSettingsDialog) appSettingsDialog.close(); });
channelSettingsDialog.addEventListener("click", e => { if (e.target === channelSettingsDialog) channelSettingsDialog.close(); });

watchHomeAssistantTheme();
Promise.all([loadBookmarksRemote(), loadReminders(), loadGuide()]).catch(err => { statusLine.textContent = err.message; });
setInterval(() => {
  loadGuide().catch(() => {});
  loadReminders().catch(() => {});
  loadBookmarksRemote().then(() => {
    if (bookmarksDialog.open) renderBookmarks();
  }).catch(() => {});
}, 5 * 60 * 1000);
setInterval(() => { if (mode === "now") render(); }, 60 * 1000);
