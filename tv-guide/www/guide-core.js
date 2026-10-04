(function () {
  const fmt = new Intl.DateTimeFormat("de-DE", {hour:"2-digit", minute:"2-digit"});
  const dateFmt = new Intl.DateTimeFormat("de-DE", {weekday:"short", day:"2-digit", month:"2-digit"});
  const weekdayFmt = new Intl.DateTimeFormat("de-DE", {weekday:"short"});
  const dayFmt = new Intl.DateTimeFormat("de-DE", {day:"2-digit", month:"2-digit"});

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, c => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
    }[c]));
  }

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

  function targetForMode(mode, selectedDate, customTarget) {
    if (mode === "now" && sameDay(selectedDate, new Date())) return new Date();
    if (mode === "other" && customTarget) return customTarget;
    const target = new Date(selectedDate);
    if (mode === "2015") target.setHours(20,15,0,0);
    else if (mode === "2200") target.setHours(22,0,0,0);
    else target.setHours(new Date().getHours(), new Date().getMinutes(), 0, 0);
    return target;
  }

  function modeIndex(programs, mode, selectedDate, customTarget) {
    const target = targetForMode(mode, selectedDate, customTarget);
    let i = programs.findIndex(p => new Date(p.start) <= target && target < new Date(p.end));
    if (i < 0) i = programs.findIndex(p => new Date(p.start) >= target);
    return i;
  }

  function remainingMinutes(program) {
    return Math.max(0, Math.ceil((new Date(program.end) - new Date()) / 60000));
  }

  function pct(start, end, now = new Date()) {
    const a = new Date(start), b = new Date(end);
    const p = ((now - a) / (b - a)) * 100;
    return Math.max(0, Math.min(100, p));
  }

  function headlineText(mode, selectedDate, customTarget) {
    if (mode === "now") return "Das aktuelle TV-Programm jetzt";
    const target = targetForMode(mode, selectedDate, customTarget);
    return "TV-Programm " + dateFmt.format(target) + " um " + fmt.format(target) + " Uhr";
  }

  function renderDateStrip(selectedDate, availableDateKeys = []) {
    const todayKey = dateKey(new Date());
    const keys = [...new Set(
      (Array.isArray(availableDateKeys) ? availableDateKeys : [])
        .filter(key => typeof key === "string" && key >= todayKey)
    )].sort().slice(0, 8);

    if (!keys.length) keys.push(todayKey);

    let html = "";
    for (const key of keys) {
      const d = new Date(key + "T00:00:00");
      html += '<button class="date-button' + (sameDay(d, selectedDate) ? ' active' : '') +
        '" data-date="' + key + '">' +
        '<span>' + weekdayFmt.format(d).replace(".","").toUpperCase() + '</span>' +
        '<strong>' + dayFmt.format(d) + '</strong></button>';
    }
    return html;
  }

  function channelHeader(channel, logoPrefix="") {
    const fallback = logoPrefix + "logos/" + encodeURIComponent(channel.id) + ".png";

    const localLight = channel.logo_file_light ? logoPrefix + channel.logo_file_light : "";
    const localDark = channel.logo_file ? logoPrefix + channel.logo_file : "";
    const feedLight = channel.logo_light || channel.logo || "";
    const feedDark = channel.logo_dark || channel.logo || "";

    const lightLogo = localLight || localDark || feedLight || feedDark || fallback;
    const darkLogo = localDark || localLight || feedDark || feedLight || fallback;
    const isFeedLogo = !localLight && !localDark && Boolean(feedLight || feedDark);
    const extraClass = isFeedLogo ? " channel-logo-feed" : "";
    const onerror = "this.style.display='none';const f=this.parentElement.querySelector('.logo-fallback');if(f)f.style.display='block'";

    const lightImage = '<img class="channel-logo channel-logo-light' + extraClass +
      '" src="' + escapeHtml(lightLogo) + '" alt="' + escapeHtml(channel.name) +
      '" loading="eager" onerror="' + onerror + '">';
    const darkImage = '<img class="channel-logo channel-logo-dark' + extraClass +
      '" src="' + escapeHtml(darkLogo) + '" alt="' + escapeHtml(channel.name) +
      '" loading="eager" onerror="' + onerror + '">';

    return lightImage + darkImage +
      '<span class="channel-text-logo logo-fallback" style="display:none">' +
      escapeHtml(channel.name) + '</span>' +
      '<span class="channel-label">' + escapeHtml(channel.name) + '</span>';
  }

  function renderPrograms(channel, mode, selectedDate, customTarget) {
    if (!channel.programs || channel.programs.length === 0) {
      return '<div class="program unavailable">Keine EPG-Daten gefunden</div>';
    }

    const base = modeIndex(channel.programs, mode, selectedDate, customTarget);
    if (base < 0) {
      return '<div class="program unavailable">Für diese Zeit keine EPG-Daten verfügbar</div>';
    }

    const programs = channel.programs.slice(base, base + 7);
    return programs.map((program, index) => {
      const now = new Date();
      const isCurrent = mode === "now" && sameDay(selectedDate, now) &&
        new Date(program.start) <= now && now < new Date(program.end);
      const isFeatured = index === 0;

      const metaParts = [];
      if (program.subtitle) metaParts.push(program.subtitle);
      if (program.category) metaParts.push(program.category);
      const meta = isFeatured && metaParts.length
        ? '<div class="program-meta">' + escapeHtml(metaParts.join(" · ")) + '</div>'
        : "";

      return '<button type="button" class="program' +
        (isFeatured ? ' featured' : '') + (isCurrent ? ' current' : '') +
        '" data-program-start="' + escapeHtml(program.start) + '">' +
        '<div class="program-time">' + fmt.format(new Date(program.start)) + '</div>' +
        '<div class="program-main"><strong>' + escapeHtml(program.title) + '</strong>' +
          meta + '</div>' +
        (isCurrent ? '<div class="progress-track"><div class="progress-fill" style="width:' +
          pct(program.start, program.end) + '%"></div></div>' : '') +
      '</button>';
    }).join("");
  }

  function renderChannelCard(channel, mode, selectedDate, customTarget, logoPrefix="") {
    return '<section class="channel-card" data-channel-id="' + escapeHtml(channel.id) + '">' +
      '<div class="channel-brand">' + channelHeader(channel, logoPrefix) + '</div>' +
      '<div class="programs">' + renderPrograms(channel, mode, selectedDate, customTarget) + '</div>' +
      '</section>';
  }

  window.TVGuideCore = {
    fmt, dateFmt, startOfDay, dateKey, sameDay, targetForMode, modeIndex,
    remainingMinutes, pct, escapeHtml, headlineText, renderDateStrip,
    channelHeader, renderPrograms, renderChannelCard
  };
})();