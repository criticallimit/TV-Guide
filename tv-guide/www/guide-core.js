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
    const defaultLogo = channel.logo_file ? logoPrefix + channel.logo_file : fallback;
    const lightLogo = channel.logo_file_light ? logoPrefix + channel.logo_file_light : defaultLogo;

    const lightImage = '<img class="channel-logo channel-logo-light" src="' + lightLogo +
      '" alt="' + escapeHtml(channel.name) + '" loading="eager">';
    const darkImage = '<img class="channel-logo channel-logo-dark" src="' + defaultLogo +
      '" alt="' + escapeHtml(channel.name) + '" loading="eager">';

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

    const programs = channel.programs.slice(base, base + 5);
    return programs.map(program => {
      const now = new Date();
      const isCurrent = mode === "now" && sameDay(selectedDate, now) &&
        new Date(program.start) <= now && now < new Date(program.end);
      const category = program.category
        ? '<div class="category">' + escapeHtml(program.category) + '</div>'
        : "";
      return '<button type="button" class="program' + (isCurrent ? ' current' : '') +
        '" data-program-start="' + escapeHtml(program.start) + '">' +
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