const grid = document.getElementById("grid");
const headline = document.getElementById("headline");
const detail = document.getElementById("detail");
const detailBody = document.getElementById("detailBody");
const fmt = new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"});

let guide = null;
let mode = "now";

function pct(start, end, now = new Date()) {
  const a = new Date(start), b = new Date(end);
  const p = ((now - a) / (b - a)) * 100;
  return Math.max(0, Math.min(100, p));
}

function currentIndex(programs) {
  const now = new Date();
  const i = programs.findIndex(p => new Date(p.start) <= now && now < new Date(p.end));
  return i >= 0 ? i : 0;
}

function modeIndex(programs, wanted) {
  if (wanted === "now") return currentIndex(programs);
  const now = new Date();
  const hm = wanted === "2015" ? [20,15] : [22,0];
  const target = new Date(now);
  target.setHours(hm[0], hm[1], 0, 0);
  let i = programs.findIndex(p => new Date(p.start) <= target && target < new Date(p.end));
  if (i < 0) i = programs.findIndex(p => new Date(p.start) >= target);
  return i >= 0 ? i : 0;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

function showDetail(channel, program) {
  detailBody.innerHTML =
    "<h2>" + escapeHtml(program.title) + "</h2>" +
    "<p><strong>" + escapeHtml(channel.name) + "</strong></p>" +
    "<p class=\"detail-time\">" + fmt.format(new Date(program.start)) + "–" +
    fmt.format(new Date(program.end)) + "</p>" +
    "<p>Detailinformationen kommen aus dem später angeschlossenen EPG-Provider.</p>";
  detail.showModal();
}

function render() {
  if (!guide) return;

  headline.textContent =
    mode === "now" ? "Hauptsender: Das aktuelle TV-Programm jetzt" :
    mode === "2015" ? "Hauptsender: TV-Programm um 20:15 Uhr" :
    mode === "2200" ? "Hauptsender: TV-Programm um 22:00 Uhr" :
    "Hauptsender: Andere Zeiten";

  grid.innerHTML = "";

  for (const channel of guide.channels) {
    const base = modeIndex(channel.programs, mode);
    const programs = channel.programs.slice(base, base + 6);
    const section = document.createElement("section");
    section.className = "channel";
    section.innerHTML =
      '<div class="channel-name">' + escapeHtml(channel.name) +
      '</div><div class="programs"></div>';
    const list = section.querySelector(".programs");

    programs.forEach((program, idx) => {
      const row = document.createElement("div");
      const isCurrent = mode === "now" && idx === 0;
      row.className = "program" + (isCurrent ? " current" : "");
      row.innerHTML =
        '<span class="time">' + fmt.format(new Date(program.start)) + '</span>' +
        '<span class="title">' + escapeHtml(program.title) + '</span>' +
        (isCurrent
          ? '<div class="progress-track"><div class="progress-fill" style="width:' +
            pct(program.start, program.end) + '%"></div></div>'
          : "");
      row.addEventListener("click", () => showDetail(channel, program));
      list.appendChild(row);
    });

    grid.appendChild(section);
  }
}

async function init() {
  const url = new URL("api/guide", window.location.href);
  const res = await fetch(url);
  if (!res.ok) throw new Error("Programmdaten konnten nicht geladen werden.");
  guide = await res.json();
  render();
}

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    if (btn.dataset.mode === "other") return;
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    mode = btn.dataset.mode;
    render();
  });
});

detail.querySelector(".close").addEventListener("click", () => detail.close());
detail.addEventListener("click", e => {
  if (e.target === detail) detail.close();
});

init().catch(err => {
  grid.innerHTML = '<p>' + escapeHtml(err.message) + '</p>';
});

setInterval(() => {
  if (mode === "now") render();
}, 60000);
