const state = {
  lang: "en",
  players: [],
  filtered: [],
  selectedId: null,
  view: "rankings",
  compareIds: [],
  selectedReportId: null,
};

const i18n = {
  en: {
    appTitle: "Youth Potential Index",
    appSubtitle: "U21 five-league prospect rankings and scouting reports",
    navRankings: "Rankings",
    navReports: "Reports",
    navCompare: "Compare",
    navMethodology: "Methodology",
    exportCsv: "Export CSV",
    metricPlayers: "Players",
    metricOfficial: "Officially scored",
    metricTopScore: "Top score",
    metricReports: "Generated reports",
    searchLabel: "Search",
    searchPlaceholder: "Name, club, league, nation...",
    position: "Position",
    league: "League",
    minMinutes: "Min minutes",
    sortBy: "Sort by",
    sortScore: "Total score",
    sortCore: "Core performance",
    sortMinutes: "Minutes",
    sortAge: "Age",
    sortFifaPotential: "FIFA potential",
    officialOnly: "Officially scored only",
    resultLimit: "Result limit",
    clearFilters: "Clear",
    rankingsTitle: "Top U21 Potential Ranking",
    player: "Player",
    age: "Age",
    minutes: "Minutes",
    score: "Score",
    reportsTitle: "Report Library",
    reportsSubtitle: "Generated Markdown, DOCX and radar assets",
    searchReports: "Find report",
    reportSearchPlaceholder: "Search generated reports...",
    compareTitle: "Player Comparison",
    compareSubtitle: "Add players from the ranking table and compare scouting dimensions",
    clearCompare: "Clear compare",
    methodTitle: "Scoring Model",
    formulaText: "Age 15% + Reliability 15% + Position core 45% + Style 15% + League 10% - Risk",
    ageAdvantage: "Age advantage",
    reliability: "Playing reliability",
    corePerformance: "Same-position core performance",
    styleBehavior: "Style and behavior",
    leagueStrength: "League strength correction",
    dataSources: "Data Sources",
    sourcesText: "The product combines FBref performance data, Transfermarkt player metadata and FIFA ratings, then normalizes leagues, positions and per90 metrics before scoring.",
    searchTitle: "Search Coverage",
    searchText: "Search matches names, clubs, leagues, nationality and positions with accent-insensitive text matching and fuzzy name fallback.",
    allPositions: "All positions",
    allLeagues: "All leagues",
    noResults: "No players match the current filters.",
    showing: "Showing",
    of: "of",
    playersMatched: "matched players",
    rankOfficial: "Official rank",
    totalScore: "Total score",
    scoreBreakdown: "Score breakdown",
    core: "Core",
    reliabilityShort: "Reliability",
    style: "Style",
    leagueShort: "League",
    risk: "Risk",
    addCompare: "Add compare",
    removeCompare: "Remove",
    openReport: "Open report",
    downloadMd: "Markdown",
    downloadDocx: "DOCX",
    noReport: "Report not generated for this player yet.",
    reportUnavailable: "No generated report is available for this selection.",
    compareEmpty: "Choose players from the ranking snapshot to build a comparison.",
    selected: "Selected",
    marketValue: "Market value",
    fifaOverall: "FIFA overall",
    fifaPotential: "FIFA potential",
    goals90: "Goals/90",
    assists90: "Assists/90",
    shots90: "Shots/90",
    dribbles90: "Dribbles/90",
    keyPasses90: "Key passes/90",
    xg90: "xG/90",
    xa90: "xA/90",
    official: "Official",
    exploratory: "Exploratory",
  },
  zh: {
    appTitle: "年轻球员潜力榜",
    appSubtitle: "五大联赛 U21 潜力排行与球探报告门户",
    navRankings: "潜力榜",
    navReports: "报告库",
    navCompare: "对比",
    navMethodology: "方法论",
    exportCsv: "导出 CSV",
    metricPlayers: "球员总数",
    metricOfficial: "正式评分",
    metricTopScore: "最高分",
    metricReports: "已生成报告",
    searchLabel: "搜索",
    searchPlaceholder: "姓名、俱乐部、联赛、国籍、位置...",
    position: "位置",
    league: "联赛",
    minMinutes: "最低分钟",
    sortBy: "排序",
    sortScore: "总分",
    sortCore: "核心表现",
    sortMinutes: "出场时间",
    sortAge: "年龄",
    sortFifaPotential: "FIFA 潜力",
    officialOnly: "只看正式评分",
    resultLimit: "结果数量",
    clearFilters: "清除",
    rankingsTitle: "五大联赛 U21 潜力榜",
    player: "球员",
    age: "年龄",
    minutes: "分钟",
    score: "分数",
    reportsTitle: "报告库",
    reportsSubtitle: "已生成 Markdown、DOCX 与雷达图资源",
    searchReports: "查找报告",
    reportSearchPlaceholder: "搜索已生成报告...",
    compareTitle: "球员对比",
    compareSubtitle: "从排行榜球员快照中加入对比，横向查看球探维度",
    clearCompare: "清空对比",
    methodTitle: "评分模型",
    formulaText: "年龄 15% + 可靠性 15% + 位置核心 45% + 风格 15% + 联赛 10% - 风险",
    ageAdvantage: "年龄优势",
    reliability: "出场可靠性",
    corePerformance: "同位置核心表现",
    styleBehavior: "场上风格与行为",
    leagueStrength: "联赛强度修正",
    dataSources: "数据来源",
    sourcesText: "系统融合 FBref 表现数据、Transfermarkt 球员信息和 FIFA 评分，并在联赛、位置和 per90 指标归一化后进行评分。",
    searchTitle: "搜索覆盖",
    searchText: "搜索覆盖姓名、俱乐部、联赛、国籍和位置，支持忽略重音符号的文本匹配，并带有姓名模糊匹配兜底。",
    allPositions: "全部位置",
    allLeagues: "全部联赛",
    noResults: "当前筛选下没有匹配球员。",
    showing: "显示",
    of: "共",
    playersMatched: "名匹配球员",
    rankOfficial: "正式排名",
    totalScore: "总分",
    scoreBreakdown: "评分拆解",
    core: "核心",
    reliabilityShort: "可靠性",
    style: "风格",
    leagueShort: "联赛",
    risk: "风险",
    addCompare: "加入对比",
    removeCompare: "移除",
    openReport: "打开报告",
    downloadMd: "Markdown",
    downloadDocx: "DOCX",
    noReport: "该球员暂未生成报告。",
    reportUnavailable: "当前选择没有可用报告。",
    compareEmpty: "从排行榜右侧球员快照中选择球员加入对比。",
    selected: "已选择",
    marketValue: "身价",
    fifaOverall: "FIFA 总评",
    fifaPotential: "FIFA 潜力",
    goals90: "进球/90",
    assists90: "助攻/90",
    shots90: "射门/90",
    dribbles90: "过人/90",
    keyPasses90: "关键传球/90",
    xg90: "xG/90",
    xa90: "xA/90",
    official: "正式",
    exploratory: "观察",
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const t = (key) => i18n[state.lang][key] || i18n.en[key] || key;

function normalizeText(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, " ")
    .trim();
}

function initials(name) {
  return String(name || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function score(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(1) : "-";
}

function integer(value) {
  const num = Number(value);
  return Number.isFinite(num) ? String(Math.round(num)) : "-";
}

function money(value) {
  const num = Number(value);
  if (!Number.isFinite(num) || num <= 0) return "-";
  if (num >= 1_000_000) return `€${(num / 1_000_000).toFixed(num >= 10_000_000 ? 0 : 1)}M`;
  if (num >= 1_000) return `€${(num / 1_000).toFixed(0)}K`;
  return `€${num.toFixed(0)}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function levenshtein(a, b) {
  if (!a || !b) return Math.max(a.length, b.length);
  const row = Array.from({ length: b.length + 1 }, (_, index) => index);
  for (let i = 1; i <= a.length; i += 1) {
    let previous = row[0];
    row[0] = i;
    for (let j = 1; j <= b.length; j += 1) {
      const temp = row[j];
      row[j] = Math.min(
        row[j] + 1,
        row[j - 1] + 1,
        previous + (a[i - 1] === b[j - 1] ? 0 : 1)
      );
      previous = temp;
    }
  }
  return row[b.length];
}

function fuzzyNameMatch(query, player) {
  const name = normalizeText(player.player_name);
  const compactName = name.replace(/\s+/g, "");
  const compactQuery = query.replace(/\s+/g, "");
  if (compactName.includes(compactQuery)) return true;
  if (compactQuery.length < 4) return false;
  const limit = Math.max(2, Math.floor(compactQuery.length * 0.25));
  return name.split(" ").some((part) => levenshtein(compactQuery, part) <= limit) ||
    levenshtein(compactQuery, compactName.slice(0, compactQuery.length + 2)) <= limit;
}

function translateStaticText() {
  $$("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  $$("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  $("#languageToggle").textContent = state.lang === "en" ? "中文" : "EN";
}

function buildSelectOptions() {
  const positions = [...new Set(state.players.map((p) => p.standard_position).filter(Boolean))].sort();
  const leagues = [...new Set(state.players.map((p) => p.league).filter(Boolean))].sort();
  $("#positionFilter").innerHTML = `<option value="">${escapeHtml(t("allPositions"))}</option>${positions.map((v) => `<option>${escapeHtml(v)}</option>`).join("")}`;
  $("#leagueFilter").innerHTML = `<option value="">${escapeHtml(t("allLeagues"))}</option>${leagues.map((v) => `<option>${escapeHtml(v)}</option>`).join("")}`;
  const suggestions = state.players
    .slice()
    .sort((a, b) => Number(b.total_score || 0) - Number(a.total_score || 0))
    .slice(0, 140)
    .map((p) => `<option value="${escapeHtml(p.player_name)}">${escapeHtml(p.team || "")}</option>`)
    .join("");
  $("#playerSuggestions").innerHTML = suggestions;
}

function updateMetrics() {
  const official = state.players.filter((p) => p.is_official).length;
  const reportCount = state.players.filter((p) => p.report_md_path).length;
  const topScore = Math.max(...state.players.map((p) => Number(p.total_score || 0)));
  $("#metricPlayers").textContent = state.players.length;
  $("#metricOfficial").textContent = official;
  $("#metricTopScore").textContent = score(topScore);
  $("#metricReports").textContent = reportCount;
}

function playerMatchesSearch(player, rawQuery) {
  const query = normalizeText(rawQuery);
  if (!query) return true;
  const tokens = query.split(/\s+/).filter(Boolean);
  return tokens.every((token) => player.search_text.includes(token) || fuzzyNameMatch(token, player));
}

function applyFilters() {
  const rawQuery = $("#searchInput").value;
  const position = $("#positionFilter").value;
  const league = $("#leagueFilter").value;
  const minMinutes = Number($("#minMinutes").value || 0);
  const officialOnly = $("#officialOnly").checked;
  const sortBy = $("#sortBy").value;
  const limit = Number($("#resultLimit").value || 50);

  state.filtered = state.players
    .filter((p) => !officialOnly || p.is_official)
    .filter((p) => !position || p.standard_position === position)
    .filter((p) => !league || p.league === league)
    .filter((p) => Number(p.minutes || 0) >= minMinutes)
    .filter((p) => playerMatchesSearch(p, rawQuery))
    .sort((a, b) => {
      if (sortBy === "age") return Number(a.age ?? 99) - Number(b.age ?? 99);
      return Number(b[sortBy] ?? -999) - Number(a[sortBy] ?? -999);
    })
    .slice(0, limit);

  if (!state.selectedId || !state.filtered.some((p) => p.id === state.selectedId)) {
    state.selectedId = state.filtered[0]?.id || state.players[0]?.id || null;
  }
  renderRanking();
  renderSnapshot();
}

function renderRanking() {
  $("#resultLimitValue").textContent = $("#resultLimit").value;
  const totalMatched = state.players.filter((p) => {
    return (!$("#officialOnly").checked || p.is_official) &&
      (!$("#positionFilter").value || p.standard_position === $("#positionFilter").value) &&
      (!$("#leagueFilter").value || p.league === $("#leagueFilter").value) &&
      Number(p.minutes || 0) >= Number($("#minMinutes").value || 0) &&
      playerMatchesSearch(p, $("#searchInput").value);
  }).length;
  $("#rankingCount").textContent = `${t("showing")} ${state.filtered.length} ${t("of")} ${totalMatched} ${t("playersMatched")}`;

  const body = $("#playerTableBody");
  if (!state.filtered.length) {
    body.innerHTML = `<tr><td colspan="7" class="empty-state">${escapeHtml(t("noResults"))}</td></tr>`;
    return;
  }
  body.innerHTML = state.filtered
    .map((p, index) => `
      <tr data-id="${p.id}" class="${p.id === state.selectedId ? "is-selected" : ""}">
        <td>${p.official_rank || index + 1}</td>
        <td>
          <div class="player-main">
            <span class="avatar">${escapeHtml(initials(p.player_name))}</span>
            <div>
              <div class="player-name">${escapeHtml(p.player_name)}</div>
              <div class="player-sub">${escapeHtml(p.team || "-")} · ${escapeHtml(p.nation_ || "-")}</div>
            </div>
          </div>
        </td>
        <td><span class="pill">${escapeHtml(p.standard_position || "-")}</span></td>
        <td>${escapeHtml(p.league || "-")}</td>
        <td>${integer(p.age)}</td>
        <td>${integer(p.minutes)}</td>
        <td><span class="score-badge">${score(p.total_score)}</span></td>
      </tr>
    `)
    .join("");

  $$("#playerTableBody tr[data-id]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedId = row.dataset.id;
      renderRanking();
      renderSnapshot();
    });
  });
}

function selectedPlayer() {
  return state.players.find((p) => p.id === state.selectedId) || state.players[0];
}

function breakdownRows(player) {
  const rows = [
    [t("age"), player.age_score],
    [t("reliabilityShort"), player.reliability_score],
    [t("core"), player.core_performance],
    [t("style"), player.behavior_score],
    [t("leagueShort"), player.league_score],
  ];
  return rows
    .map(([label, value]) => {
      const pct = Math.max(0, Math.min(100, Number(value || 0)));
      return `
        <div class="bar-row">
          <div class="bar-label"><span>${escapeHtml(label)}</span><b>${score(value)}</b></div>
          <div class="bar-track"><div class="bar-fill" style="width: ${pct}%"></div></div>
        </div>
      `;
    })
    .join("");
}

function renderSnapshot() {
  const player = selectedPlayer();
  const container = $("#snapshotContent");
  if (!player) {
    container.innerHTML = `<p class="empty-state">${escapeHtml(t("noResults"))}</p>`;
    return;
  }
  const inCompare = state.compareIds.includes(player.id);
  const radar = player.chart_path
    ? `<div class="radar-frame"><img src="${escapeHtml(player.chart_path)}" alt="${escapeHtml(player.player_name)} radar chart" /></div>`
    : `<div class="radar-frame muted">${escapeHtml(t("noReport"))}</div>`;
  container.innerHTML = `
    <div class="snapshot-inner">
      <div class="hero-player">
        <div>
          <div class="hero-meta">
            <span>${escapeHtml(player.standard_position || "-")}</span>
            <span>${escapeHtml(player.league || "-")}</span>
            <span>${integer(player.age)}</span>
            <span>${player.is_official ? t("official") : t("exploratory")}</span>
          </div>
          <h2>${escapeHtml(player.player_name)}</h2>
          <p>${escapeHtml(player.team || "-")} · ${escapeHtml(player.nation_ || "-")}</p>
        </div>
        <div class="score-large">${score(player.total_score)}</div>
      </div>
      ${radar}
      <section>
        <h3>${escapeHtml(t("scoreBreakdown"))}</h3>
        <div class="breakdown">${breakdownRows(player)}</div>
      </section>
      <div class="mini-stats">
        <div class="mini-stat"><span>${escapeHtml(t("rankOfficial"))}</span><strong>${player.official_rank || "-"}</strong></div>
        <div class="mini-stat"><span>${escapeHtml(t("risk"))}</span><strong>${score(player.risk_penalty)}</strong></div>
        <div class="mini-stat"><span>${escapeHtml(t("marketValue"))}</span><strong>${money(player.market_value)}</strong></div>
        <div class="mini-stat"><span>${escapeHtml(t("fifaPotential"))}</span><strong>${score(player.fifa_potential)}</strong></div>
      </div>
      <div class="snapshot-actions">
        <button id="compareToggle" class="primary-btn" type="button">${escapeHtml(inCompare ? t("removeCompare") : t("addCompare"))}</button>
        ${player.report_md_path ? `<button id="snapshotReport" class="secondary-btn" type="button">${escapeHtml(t("openReport"))}</button>` : ""}
      </div>
    </div>
  `;
  $("#compareToggle").addEventListener("click", () => toggleCompare(player.id));
  const reportButton = $("#snapshotReport");
  if (reportButton) {
    reportButton.addEventListener("click", () => {
      state.selectedReportId = player.id;
      switchView("reports");
      renderReports();
    });
  }
}

function toggleCompare(id) {
  if (state.compareIds.includes(id)) {
    state.compareIds = state.compareIds.filter((item) => item !== id);
  } else {
    state.compareIds = [...state.compareIds, id].slice(-4);
  }
  renderSnapshot();
  renderCompare();
}

function switchView(view) {
  state.view = view;
  $$(".nav-tab").forEach((tab) => tab.classList.toggle("is-active", tab.dataset.view === view));
  $$(".view").forEach((panel) => panel.classList.toggle("is-active", panel.id === `view-${view}`));
}

function reportPlayers() {
  const query = normalizeText($("#reportSearch")?.value || "");
  return state.players
    .filter((p) => p.report_md_path)
    .filter((p) => !query || p.search_text.includes(query) || fuzzyNameMatch(query, p))
    .sort((a, b) => Number(a.official_rank || 9999) - Number(b.official_rank || 9999));
}

function renderReports() {
  const reports = reportPlayers();
  if (!state.selectedReportId || !reports.some((p) => p.id === state.selectedReportId)) {
    state.selectedReportId = reports[0]?.id || null;
  }
  $("#reportList").innerHTML = reports
    .map((p) => `
      <button class="report-item ${p.id === state.selectedReportId ? "is-active" : ""}" type="button" data-id="${p.id}">
        <strong>${escapeHtml(p.player_name)}</strong>
        <span>${escapeHtml(p.standard_position || "-")} · ${escapeHtml(p.league || "-")} · ${score(p.total_score)}</span>
      </button>
    `)
    .join("") || `<p class="empty-state">${escapeHtml(t("reportUnavailable"))}</p>`;

  $$(".report-item").forEach((item) => {
    item.addEventListener("click", () => {
      state.selectedReportId = item.dataset.id;
      renderReports();
    });
  });
  loadReportPreview();
}

async function loadReportPreview() {
  const player = state.players.find((p) => p.id === state.selectedReportId);
  const actions = $("#reportActions");
  const preview = $("#reportPreview");
  if (!player?.report_md_path) {
    actions.innerHTML = "";
    preview.innerHTML = `<p class="empty-state">${escapeHtml(t("reportUnavailable"))}</p>`;
    return;
  }
  actions.innerHTML = `
    <a class="primary-btn" href="${escapeHtml(player.report_md_path)}" download>${escapeHtml(t("downloadMd"))}</a>
    ${player.report_docx_path ? `<a class="secondary-btn" href="${escapeHtml(player.report_docx_path)}" download>${escapeHtml(t("downloadDocx"))}</a>` : ""}
    ${player.chart_path ? `<a class="secondary-btn" href="${escapeHtml(player.chart_path)}" download>Radar PNG</a>` : ""}
  `;
  try {
    const response = await fetch(encodeURI(player.report_md_path));
    const text = await response.text();
    preview.innerHTML = renderMarkdown(text);
  } catch (error) {
    preview.innerHTML = `<p class="empty-state">${escapeHtml(t("reportUnavailable"))}</p>`;
  }
}

function renderMarkdown(markdown) {
  const lines = markdown.split(/\r?\n/);
  const html = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    if (line.startsWith("# ")) {
      html.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
    } else if (line.startsWith("## ")) {
      html.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
    } else if (line.startsWith("### ")) {
      html.push(`<h3>${escapeHtml(line.slice(4))}</h3>`);
    } else if (line.startsWith(">")) {
      html.push(`<blockquote>${escapeHtml(line.replace(/^>\s?/, ""))}</blockquote>`);
    } else if (line.includes("|") && lines[index + 1]?.includes("---")) {
      const tableLines = [];
      while (lines[index]?.includes("|")) {
        if (!lines[index].includes("---")) tableLines.push(lines[index]);
        index += 1;
      }
      index -= 1;
      const rows = tableLines.map((row) => row.split("|").slice(1, -1).map((cell) => cell.trim()));
      const [head, ...body] = rows;
      html.push(`<table><thead><tr>${head.map((cell) => `<th>${escapeHtml(cell)}</th>`).join("")}</tr></thead><tbody>${body.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell.replace(/\*\*/g, ""))}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
    } else if (line.startsWith("- ")) {
      const items = [];
      while (lines[index]?.startsWith("- ")) {
        items.push(`<li>${escapeHtml(lines[index].slice(2).replace(/\*\*/g, ""))}</li>`);
        index += 1;
      }
      index -= 1;
      html.push(`<ul>${items.join("")}</ul>`);
    } else if (!line.startsWith("---")) {
      html.push(`<p>${escapeHtml(line.replace(/\*\*/g, ""))}</p>`);
    }
    index += 1;
  }
  return html.join("");
}

function renderCompare() {
  const players = state.compareIds.map((id) => state.players.find((p) => p.id === id)).filter(Boolean);
  const container = $("#compareContent");
  if (!players.length) {
    container.innerHTML = `<p class="empty-state">${escapeHtml(t("compareEmpty"))}</p>`;
    return;
  }
  container.innerHTML = `
    <div class="compare-grid">
      ${players.map((p) => `
        <article class="compare-card">
          <div class="player-main">
            <span class="avatar">${escapeHtml(initials(p.player_name))}</span>
            <div>
              <div class="player-name">${escapeHtml(p.player_name)}</div>
              <div class="player-sub">${escapeHtml(p.team || "-")} · ${escapeHtml(p.standard_position || "-")}</div>
            </div>
          </div>
          <div class="score-large">${score(p.total_score)}</div>
          <div class="breakdown">${breakdownRows(p)}</div>
          <div class="mini-stats">
            <div class="mini-stat"><span>${escapeHtml(t("goals90"))}</span><strong>${score(p.goals_per90)}</strong></div>
            <div class="mini-stat"><span>${escapeHtml(t("assists90"))}</span><strong>${score(p.assists_per90)}</strong></div>
            <div class="mini-stat"><span>${escapeHtml(t("dribbles90"))}</span><strong>${score(p.dribbles_per90)}</strong></div>
            <div class="mini-stat"><span>${escapeHtml(t("keyPasses90"))}</span><strong>${score(p.key_passes_per90)}</strong></div>
            <div class="mini-stat"><span>${escapeHtml(t("xg90"))}</span><strong>${score(p.xg_per90)}</strong></div>
            <div class="mini-stat"><span>${escapeHtml(t("xa90"))}</span><strong>${score(p.xa_per90)}</strong></div>
          </div>
          <button class="secondary-btn remove-compare" type="button" data-id="${p.id}">${escapeHtml(t("removeCompare"))}</button>
        </article>
      `).join("")}
    </div>
  `;
  $$(".remove-compare").forEach((button) => {
    button.addEventListener("click", () => toggleCompare(button.dataset.id));
  });
}

function wireEvents() {
  ["searchInput", "positionFilter", "leagueFilter", "minMinutes", "sortBy", "officialOnly", "resultLimit"].forEach((id) => {
    $(`#${id}`).addEventListener("input", applyFilters);
  });
  $("#clearFilters").addEventListener("click", () => {
    $("#searchInput").value = "";
    $("#positionFilter").value = "";
    $("#leagueFilter").value = "";
    $("#minMinutes").value = 0;
    $("#sortBy").value = "total_score";
    $("#officialOnly").checked = true;
    $("#resultLimit").value = 50;
    applyFilters();
  });
  $("#languageToggle").addEventListener("click", () => {
    state.lang = state.lang === "en" ? "zh" : "en";
    translateStaticText();
    buildSelectOptions();
    applyFilters();
    renderReports();
    renderCompare();
  });
  $$(".nav-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      switchView(tab.dataset.view);
      if (tab.dataset.view === "reports") renderReports();
      if (tab.dataset.view === "compare") renderCompare();
    });
  });
  $("#reportSearch").addEventListener("input", renderReports);
  $("#clearCompare").addEventListener("click", () => {
    state.compareIds = [];
    renderCompare();
    renderSnapshot();
  });
}

async function init() {
  const response = await fetch("./data/players.json");
  const data = await response.json();
  state.players = data.players.map((player) => ({
    ...player,
    id: String(player.id),
    search_text: normalizeText([
      player.player_name,
      player.team,
      player.league,
      player.standard_position,
      player.position,
      player.tm_sub_position,
      player.nation_,
    ].join(" ")),
  }));
  state.selectedId = state.players.find((p) => p.is_official)?.id || state.players[0]?.id || null;
  translateStaticText();
  buildSelectOptions();
  updateMetrics();
  wireEvents();
  applyFilters();
  renderReports();
  renderCompare();
}

init().catch((error) => {
  document.body.innerHTML = `<main class="empty-state">Unable to load site data: ${escapeHtml(error.message)}</main>`;
});
