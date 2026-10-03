const grid = document.getElementById("grid");
const headline = document.getElementById("headline");
const statusLine = document.getElementById("status");
const detail = document.getElementById("detail");
const detailBody = document.getElementById("detailBody");
const customTimeBar = document.getElementById("customTimeBar");
const customDate = document.getElementById("customDate");
const customTime = document.getElementById("customTime");
const applyCustomTime = document.getElementById("applyCustomTime");

const fmt = new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"});
const dateFmt = new Intl.DateTimeFormat("de-DE", {weekday:"short", day:"2-digit", month:"2-digit"});

let guide = null;
let mode = "now";
let customTarget = null;

function pct(start, end, now = new Date()) {
  const a = new Date(start), b = new Date(end);
  const p = ((now - a) / (b - a)) * 100;
  return Math.max(0, Math.min(100, p));
}

function currentIndex(programs) {
  const now = new Date();
  const i = programs.findIndex(p => new Date(p.start) <= now && now < new Date(p.end));
  const next = programs.findIndex(p => new Date(p.start) >= now);
  return i >= 0 ? i : Math.max(0, next);
}

function targetForMode(wanted) {
  const target = new Date();
  if (wanted === "2015") target.setHours(20, 15, 0, 0);
  else if (wanted === "2200") target.setHours(22, 0, 0, 0);
  else if (wanted === "other" && customTarget) return customTarget;
  return target;
}

function modeIndex(programs, wanted) {
  if (wanted === "now") return currentIndex(programs);
  const target = targetForMode(wanted);
  let i = programs.findIndex(p => new Date(p.start) <= target && target < new Date(p.end));
  if (i < 0) i = programs.findIndex(p => new Date(p.start) >= target);
  return i >= 0 ? i : Math.max(0, programs.length - 1);
}

function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

function showDetail(channel, program) {
  const description = program.desc
    ? "<p>" + escapeHtml(program.desc) + "</p>"
    : "<p>Keine Beschreibung verfügbar.</p>";
  const category = program.category
    ? "<p><strong>Kategorie:</strong> " + escapeHtml(program.category) + "</p>"
    : "";
  const subtitle = program.subtitle
    ? "<p class=\"detail-subtitle\">" + escapeHtml(program.subtitle) + "</p>"
    : "";

  detailBody.innerHTML =
    "<h2>" + escapeHtml(program.title) + "</h2>" +
    "<p><strong>" + escapeHtml(channel.name) + "</strong></p>" +
    "<p class=\"detail-time\">" +
      dateFmt.format(new Date(program.start)) + " · " +
      fmt.format(new Date(program.start)) + "–" + fmt.format(new Date(program.end)) +
    "</p>" +
    subtitle + category + description;

  detail.showModal();
}

function headlineText() {
  if (mode === "now") return "Hauptsender: Das aktuelle TV-Programm jetzt";
  if (mode === "2015") return "Hauptsender: TV-Programm um 20:15 Uhr";
  if (mode === "2200") return "Hauptsender: TV-Programm um 22:00 Uhr";
  if (customTarget) {
    return "Hauptsender: TV-Programm " +
      dateFmt.format(customTarget) + " um " + fmt.format(customTarget) + " Uhr";
  }
  return "Hauptsender: Andere Zeiten";
}

function render() {
  if (!guide) return;

  headline.textContent = headlineText();

  const availableCount = guide.channels.filter(c => c.available).length;
  statusLine.textContent = guide.error
    ? "EPG-Quelle aktuell nicht vollständig erreichbar – vorhandene Daten werden verwendet."
    : availableCount > 0
      ? "Live-EPG geladen · " + availableCount + " von " + guide.channels.length + " Sendern erkannt"
      : "EPG geladen, aber noch keine Programmdaten für die konfigurierten Sender erkannt";

  grid.innerHTML = "";

  for (const channel of guide.channels) {
    const section = document.createElement("section");
    section.className = "channel";

    const logo = channel.logo
      ? '<img class="channel-logo" src="' + escapeHtml(channel.logo) + '" alt="' + escapeHtml(channel.name) + '">'
      : '<span>' + escapeHtml(channel.name) + '</span>';

    section.innerHTML =
      '<div class="channel-name">' + logo + '</div><div class="programs"></div>';

    const list = section.querySelector(".programs");

    if (!channel.programs || channel.programs.length === 0) {
      list.innerHTML = '<div class="program unavailable"><span class="title">Keine EPG-Daten gefunden</span></div>';
      grid.appendChild(section);
      continue;
    }

    const base = modeIndex(channel.programs, mode);
    const programs = channel.programs.slice(base, base + 6);

    programs.forEach(program => {
      const row = document.createElement("div");
      const now = new Date();
      const isCurrent =
        new Date(program.start) <= now && now < new Date(program.end);

      row.className = "program" + (isCurrent && mode === "now" ? " current" : "");
      row.innerHTML =
        '<span class="time">' + fmt.format(new Date(program.start)) + '</span>' +
        '<span class="title">' + escapeHtml(program.title) + '</span>' +
        (isCurrent && mode === "now"
          ? '<div class="progress-track"><div class="progress-fill" style="width:' +
            pct(program.start, program.end) + '%"></div></div>'
          : "");

      row.addEventListener("click", () => showDetail(channel, program));
      list.appendChild(row);
    });

    grid.appendChild(section);
  }
}

function setMode(nextMode) {
  mode = nextMode;
  document.querySelectorAll(".tab").forEach(b => {
    b.classList.toggle("active", b.dataset.mode === nextMode);
  });
  customTimeBar.hidden = nextMode !== "other";
  render();
}

function initCustomDate() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString().slice(0, 10);
  customDate.value = local;
  customDate.min = local;

  if (guide?.channels?.length) {
    const lastDates = guide.channels
      .flatMap(c => c.programs || [])
      .map(p => new Date(p.end))
      .filter(d => !Number.isNaN(d.getTime()));

    if (lastDates.length) {
      const last = new Date(Math.max(...lastDates.map(d => d.getTime())));
      customDate.max = new Date(last.getTime() - last.getTimezoneOffset() * 60000)
        .toISOString().slice(0, 10);
    }
  }
}

async function loadGuide() {
  const url = new URL("api/guide", window.location.href);
  const res = await fetch(url, {cache: "no-store"});
  if (!res.ok) throw new Error("Programmdaten konnten nicht geladen werden.");

  guide = await res.json();

  const columns = guide.ui?.columns_desktop || 5;
  document.documentElement.style.setProperty("--desktop-columns", String(columns));

  if (!document.body.dataset.initialized) {
    const configured = guide.ui?.default_view || "now";
    mode = ["now", "2015", "2200"].includes(configured) ? configured : "now";
    document.body.dataset.initialized = "1";
    initCustomDate();
    setMode(mode);
  } else {
    initCustomDate();
    render();
  }
}

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

applyCustomTime.addEventListener("click", () => {
  if (!customDate.value || !customTime.value) return;
  const target = new Date(customDate.value + "T" + customTime.value + ":00");
  if (Number.isNaN(target.getTime())) return;
  customTarget = target;
  render();
});

detail.querySelector(".close").addEventListener("click", () => detail.close());
detail.addEventListener("click", e => {
  if (e.target === detail) detail.close();
});

loadGuide().catch(err => {
  statusLine.textContent = err.message;
});

setInterval(() => {
  loadGuide().catch(() => {});
}, 5 * 60 * 1000);

setInterval(() => {
  if (mode === "now") render();
}, 60 * 1000);
