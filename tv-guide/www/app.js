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
const dateStrip = document.getElementById("dateStrip");
const customTimeBar = document.getElementById("customTimeBar");
const customDate = document.getElementById("customDate");
const customTime = document.getElementById("customTime");
const applyCustomTime = document.getElementById("applyCustomTime");

const fmt = new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"});
const dateFmt = new Intl.DateTimeFormat("de-DE", {weekday:"short", day:"2-digit", month:"2-digit"});
const weekdayFmt = new Intl.DateTimeFormat("de-DE", {weekday:"short"});
const dayFmt = new Intl.DateTimeFormat("de-DE", {day:"2-digit", month:"2-digit"});

let guide = null;
let mode = "now";
let selectedDate = startOfDay(new Date());
let customTarget = null;
let activeDetail = null;
let bookmarks = loadBookmarks();

function startOfDay(value) {
  const d = new Date(value);
  d.setHours(0,0,0,0);
  return d;
}

function dateKey(value) {
  const d = new Date(value);
  const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0,10);
}

function sameDay(a,b) {
  return dateKey(a) === dateKey(b);
}

function loadBookmarks() {
  try { return JSON.parse(localStorage.getItem("tvguide-bookmarks") || "[]"); }
  catch { return []; }
}

function saveBookmarks() {
  localStorage.setItem("tvguide-bookmarks", JSON.stringify(bookmarks));
  bookmarkCount.textContent = String(bookmarks.length);
}

function bookmarkId(channel, program) {
  return channel.id + "|" + program.start + "|" + program.title;
}

function pct(start, end, now = new Date()) {
  const a = new Date(start), b = new Date(end);
  const p = ((now - a) / (b - a)) * 100;
  return Math.max(0, Math.min(100, p));
}

function escapeHtml(s) {
  return String(s || "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

function renderDateStrip() {
  dateStrip.innerHTML = "";
  const first = startOfDay(new Date());
  for (let i=0;i<8;i++) {
    const d = new Date(first);
    d.setDate(d.getDate()+i);
    const btn = document.createElement("button");
    btn.className = "date-button" + (sameDay(d, selectedDate) ? " active" : "");
    btn.dataset.date = dateKey(d);
    btn.innerHTML = '<span>' + weekdayFmt.format(d).replace(".","").toUpperCase() +
      '</span><strong>' + dayFmt.format(d) + '</strong>';
    btn.addEventListener("click", () => {
      selectedDate = startOfDay(d);
      customTarget = null;
      if (mode === "now" && !sameDay(selectedDate, new Date())) mode = "2015";
      document.querySelectorAll(".tab").forEach(b =>
        b.classList.toggle("active", b.dataset.mode === mode));
      renderDateStrip();
      render();
    });
    dateStrip.appendChild(btn);
  }
}

function targetForMode(wanted) {
  if (wanted === "now") return new Date();
  if (wanted === "other" && customTarget) return customTarget;
  const target = new Date(selectedDate);
  if (wanted === "2015") target.setHours(20,15,0,0);
  else if (wanted === "2200") target.setHours(22,0,0,0);
  else target.setHours(20,15,0,0);
  return target;
}

function modeIndex(programs, wanted) {
  const target = targetForMode(wanted);
  let i = programs.findIndex(p => new Date(p.start) <= target && target < new Date(p.end));
  if (i < 0) i = programs.findIndex(p => new Date(p.start) >= target);
  return i >= 0 ? i : Math.max(0, programs.length - 1);
}

function remainingMinutes(program) {
  return Math.max(0, Math.ceil((new Date(program.end) - new Date()) / 60000));
}

function channelHeader(channel) {
  const logo = channel.logo_url || channel.logo;
  if (logo) {
    return '<img class="channel-logo" src="' + escapeHtml(logo) +
      '" alt="' + escapeHtml(channel.name) + '" loading="eager" referrerpolicy="no-referrer" ' +
      'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\'">' +
      '<span class="channel-text-logo logo-fallback" style="display:none">' +
      escapeHtml(channel.name) + '</span>';
  }
  return '<span class="channel-text-logo">' + escapeHtml(channel.name) + '</span>';
}

function isBookmarked(channel, program) {
  const id = bookmarkId(channel, program);
  return bookmarks.some(x => x.id === id);
}

function updateBookmarkButton() {
  if (!activeDetail) return;
  const marked = isBookmarked(activeDetail.channel, activeDetail.program);
  bookmarkProgram.textContent = marked ? "★ Gemerkt" : "☆ Sendung merken";
  bookmarkProgram.classList.toggle("active", marked);
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
  updateBookmarkButton();
  detail.showModal();
}

function toggleBookmark() {
  if (!activeDetail) return;
  const {channel, program} = activeDetail;
  const id = bookmarkId(channel, program);
  const index = bookmarks.findIndex(x => x.id === id);
  if (index >= 0) bookmarks.splice(index,1);
  else bookmarks.push({
    id,
    channel: channel.name,
    channelId: channel.id,
    title: program.title,
    start: program.start,
    end: program.end
  });
  bookmarks.sort((a,b) => new Date(a.start) - new Date(b.start));
  saveBookmarks();
  updateBookmarkButton();
}

function renderBookmarks() {
  const now = new Date();
  bookmarks = bookmarks.filter(x => new Date(x.end) > now);
  saveBookmarks();
  if (!bookmarks.length) {
    bookmarksBody.innerHTML = '<p class="empty-bookmarks">Noch keine Sendung gemerkt.</p>';
    return;
  }
  bookmarksBody.innerHTML = bookmarks.map(item =>
    '<div class="bookmark-row"><div><strong>' + escapeHtml(item.title) + '</strong>' +
    '<div>' + escapeHtml(item.channel) + ' · ' + dateFmt.format(new Date(item.start)) +
    ' · ' + fmt.format(new Date(item.start)) + '</div></div>' +
    '<button type="button" data-remove="' + escapeHtml(item.id) + '">×</button></div>'
  ).join("");
  bookmarksBody.querySelectorAll("[data-remove]").forEach(btn => {
    btn.addEventListener("click", () => {
      bookmarks = bookmarks.filter(x => x.id !== btn.dataset.remove);
      saveBookmarks();
      renderBookmarks();
    });
  });
}

function headlineText() {
  if (mode === "now") return "Das aktuelle TV-Programm jetzt";
  const target = targetForMode(mode);
  return "TV-Programm " + dateFmt.format(target) + " um " + fmt.format(target) + " Uhr";
}

function render() {
  if (!guide) return;
  headline.textContent = headlineText();

  const availableCount = guide.channels.filter(c => c.available).length;
  statusLine.textContent = guide.error
    ? "EPG-Quelle aktuell nicht vollständig erreichbar – vorhandene Daten werden verwendet."
    : "Live-EPG · " + availableCount + " von " + guide.channels.length + " Sendern";

  grid.innerHTML = "";

  for (const channel of guide.channels) {
    const section = document.createElement("section");
    section.className = "channel-card";
    section.innerHTML =
      '<div class="channel-brand">' + channelHeader(channel) + '</div>' +
      '<div class="programs"></div>';

    const list = section.querySelector(".programs");
    if (!channel.programs || channel.programs.length === 0) {
      list.innerHTML = '<div class="program unavailable">Keine EPG-Daten gefunden</div>';
      grid.appendChild(section);
      continue;
    }

    const base = modeIndex(channel.programs, mode);
    const programs = channel.programs.slice(base, base + 5);
    programs.forEach((program, idx) => {
      const row = document.createElement("button");
      row.type = "button";
      const now = new Date();
      const isCurrent = mode === "now" &&
        new Date(program.start) <= now && now < new Date(program.end);

      row.className = "program" + (isCurrent ? " current" : "");
      const category = program.category
        ? '<div class="category">' + escapeHtml(program.category) + '</div>'
        : "";
      row.innerHTML =
        '<div class="program-time">' +
          (isCurrent ? '<span class="now-dot">JETZT</span>' : '') +
          '<span>' + fmt.format(new Date(program.start)) + '</span>' +
        '</div>' +
        '<div class="program-main"><strong>' + escapeHtml(program.title) + '</strong>' +
          category +
          (isCurrent ? '<div class="remaining">noch ' + remainingMinutes(program) + ' Min.</div>' : '') +
        '</div>' +
        '<div class="program-chevron">›</div>' +
        (isCurrent ? '<div class="progress-track"><div class="progress-fill" style="width:' +
          pct(program.start, program.end) + '%"></div></div>' : '');

      row.addEventListener("click", () => showDetail(channel, program));
      list.appendChild(row);
    });
    grid.appendChild(section);
  }
}

function setMode(nextMode) {
  mode = nextMode;
  if (nextMode === "now") selectedDate = startOfDay(new Date());
  document.querySelectorAll(".tab").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === nextMode));
  customTimeBar.hidden = nextMode !== "other";
  renderDateStrip();
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

  if (!document.body.dataset.initialized) {
    mode = ["now","2015","2200"].includes(guide.ui?.default_view) ? guide.ui.default_view : "now";
    document.body.dataset.initialized = "1";
    saveBookmarks();
  }
  initCustomDate();
  renderDateStrip();
  document.querySelectorAll(".tab").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === mode));
  render();
}

document.querySelectorAll(".tab").forEach(btn =>
  btn.addEventListener("click", () => setMode(btn.dataset.mode)));

applyCustomTime.addEventListener("click", () => {
  if (!customDate.value || !customTime.value) return;
  const target = new Date(customDate.value + "T" + customTime.value + ":00");
  if (Number.isNaN(target.getTime())) return;
  selectedDate = startOfDay(target);
  customTarget = target;
  renderDateStrip();
  render();
});

bookmarkProgram.addEventListener("click", toggleBookmark);
showBookmarks.addEventListener("click", () => {
  renderBookmarks();
  bookmarksDialog.showModal();
});
detail.querySelector(".close").addEventListener("click", () => detail.close());
bookmarksDialog.querySelector(".bookmarks-close").addEventListener("click", () => bookmarksDialog.close());
detail.addEventListener("click", e => { if (e.target === detail) detail.close(); });
bookmarksDialog.addEventListener("click", e => { if (e.target === bookmarksDialog) bookmarksDialog.close(); });

loadGuide().catch(err => { statusLine.textContent = err.message; });
setInterval(() => loadGuide().catch(() => {}), 5 * 60 * 1000);
setInterval(() => { if (mode === "now") render(); }, 60 * 1000);
