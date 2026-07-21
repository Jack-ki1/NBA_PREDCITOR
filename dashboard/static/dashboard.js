// ── Theme tokens (shared with styles.css) ──────────────────────────────────
const CSS = getComputedStyle(document.documentElement);
const C = {
  accent: (CSS.getPropertyValue("--accent") || "#ff5a2c").trim(),
  blue: (CSS.getPropertyValue("--blue") || "#3d8bfd").trim(),
  amber: (CSS.getPropertyValue("--amber") || "#f5b73d").trim(),
  text: (CSS.getPropertyValue("--text") || "#eef2f8").trim(),
  muted: (CSS.getPropertyValue("--muted") || "#93a0b5").trim(),
  grid: "rgba(255,255,255,0.07)",
};

const PLOT_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: C.text, family: "Inter, system-ui, sans-serif", size: 12 },
  margin: { t: 16, r: 16, b: 48, l: 52 },
  xaxis: { gridcolor: C.grid, zerolinecolor: C.grid, linecolor: C.grid, tickfont: { color: C.muted } },
  yaxis: { gridcolor: C.grid, zerolinecolor: C.grid, linecolor: C.grid, tickfont: { color: C.muted } },
  hoverlabel: { bgcolor: "#121a2c", bordercolor: C.grid, font: { color: C.text } },
  legend: { orientation: "h", y: 1.08, x: 0, font: { color: C.muted } },
};
const PLOT_CONFIG = { displayModeBar: false, responsive: true };

// Team brand-ish colors for tokens (fallback gradient otherwise).
const TEAM_COLORS = {
  ATL: "#E03A3E", BOS: "#007A33", BKN: "#000000", CHA: "#1D1160", CHI: "#CE1141",
  CLE: "#860038", DAL: "#00538C", DEN: "#0E2240", DET: "#C8102E", GSW: "#1D428A",
  HOU: "#CE1141", IND: "#002D62", LAC: "#C8102E", LAL: "#552583", MEM: "#5D76A9",
  MIA: "#98002E", MIL: "#00471B", MIN: "#0C2340", NOP: "#0C2340", NYK: "#F58426",
  OKC: "#007AC1", ORL: "#0077C0", PHI: "#006BB6", PHX: "#1D1160", POR: "#E03A3E",
  SAC: "#5A2D81", SAS: "#C4CED4", TOR: "#CE1141", UTA: "#002B5C", WAS: "#002B5C",
};
const tokenColor = (id) => TEAM_COLORS[id] || "#334155";

let TEAMS = [];

// ── Tab switching ──────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    // Plotly needs a resize nudge when a hidden chart becomes visible.
    window.dispatchEvent(new Event("resize"));
  });
});

const loading = (el, label) => {
  el.innerHTML = `<div class="empty"><span class="spinner"></span>${label}</div>`;
};

// ── Load teams ───────────────────────────────────────────────────────────────
async function loadTeams() {
  const res = await fetch("/api/teams");
  const data = await res.json();
  TEAMS = data.teams;

  const homeSel = document.getElementById("home");
  const awaySel = document.getElementById("away");
  const opts = TEAMS.slice().sort((a, b) => a.name.localeCompare(b.name))
    .map((t) => `<option value="${t.id}">${t.id} — ${t.name}</option>`).join("");
  homeSel.innerHTML = opts;
  awaySel.innerHTML = opts;
  homeSel.value = "BOS";
  awaySel.value = "LAL";

  const rows = TEAMS.map((t, i) => `<tr>
    <td><span class="rank-pill">${i + 1}</span></td>
    <td><div class="team-cell">
      <span class="team-dot" style="background:${tokenColor(t.id)}">${t.id}</span>
      <span>${t.name}</span>
    </div></td>
    <td><span class="conf-tag ${t.conference.toLowerCase()}">${t.conference}</span></td>
    <td class="num">${t.elo}</td>
    <td class="num">${t.wins}-${t.losses}</td></tr>`).join("");
  document.getElementById("teamsTable").innerHTML = `<div class="table-wrap"><table>
    <thead><tr><th class="num">#</th><th>Team</th>
    <th>Conf</th><th class="num">Elo</th><th class="num">Record</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

// ── Game prediction ──────────────────────────────────────────────────────────
async function runPredict() {
  const resultEl = document.getElementById("predictResult");
  loading(resultEl, "Simulating matchup…");
  const body = {
    home: document.getElementById("home").value,
    away: document.getElementById("away").value,
    sims: document.getElementById("sims").value,
    spread: document.getElementById("spread").value,
    total: document.getElementById("total").value,
    neutral: document.getElementById("neutral").checked,
  };
  const res = await fetch("/api/predict", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.error) { resultEl.innerHTML = `<div class="empty">${data.error}</div>`; return; }

  const p = data.prediction, m = data.meta;
  const awayPct = p.away_win_probability * 100;
  const homePct = p.home_win_probability * 100;
  const margin = p.expected_margin;
  const marginCls = margin > 0 ? "pos" : margin < 0 ? "neg" : "";

  const extra = [];
  if (p.home_cover_probability !== undefined)
    extra.push(`<div class="stat"><div class="k">ATS ${p.spread}</div><div class="v">${(p.home_cover_probability * 100).toFixed(1)}%</div></div>`);
  if (p.over_probability !== undefined)
    extra.push(`<div class="stat"><div class="k">Over ${p.total_line}</div><div class="v">${(p.over_probability * 100).toFixed(1)}%</div></div>`);

  resultEl.innerHTML = `
    <div class="matchup-card">
      <div class="matchup-top">
        <div class="team-side">
          <span class="team-token" style="background:${tokenColor(data.away.id)}">${data.away.id}</span>
          <span class="tname">${m.away_team}</span>
          <span class="twin" style="color:${homePct >= awayPct ? C.muted : C.accent}">${awayPct.toFixed(1)}%</span>
        </div>
        <div class="vs">VS<span class="conf-badge ${m.confidence}">${m.confidence}</span></div>
        <div class="team-side">
          <span class="team-token" style="background:${tokenColor(data.home.id)}">${data.home.id}</span>
          <span class="tname">${m.home_team}</span>
          <span class="twin" style="color:${homePct >= awayPct ? C.blue : C.muted}">${homePct.toFixed(1)}%</span>
        </div>
      </div>
      <div class="winbar">
        <div class="away-fill" style="width:${awayPct}%"></div>
        <div class="home-fill" style="width:${homePct}%"></div>
      </div>
      <div class="stat-strip">
        <div class="stat"><div class="k">Proj. Score</div><div class="v">${p.projected_home_score.toFixed(0)}–${p.projected_away_score.toFixed(0)}</div></div>
        <div class="stat"><div class="k">Margin</div><div class="v ${marginCls}">${margin > 0 ? "+" : ""}${margin.toFixed(1)}</div></div>
        <div class="stat"><div class="k">Total</div><div class="v">${p.expected_total.toFixed(0)}</div></div>
        ${extra.join("")}
      </div>
    </div>`;

  Plotly.newPlot("winChart", [{
    type: "bar", x: [data.away.name, data.home.name],
    y: [awayPct, homePct],
    marker: { color: [C.accent, C.blue], line: { width: 0 } },
    text: [awayPct.toFixed(1) + "%", homePct.toFixed(1) + "%"],
    textposition: "outside", textfont: { color: C.text, size: 13 },
    hovertemplate: "%{x}<br><b>%{y:.1f}%</b><extra></extra>",
  }], { ...PLOT_LAYOUT, yaxis: { ...PLOT_LAYOUT.yaxis, title: "Win %", range: [0, 100] } }, PLOT_CONFIG);

  // Approximate normal margin distribution for display.
  const mean = p.expected_margin, sd = p.margin_std;
  const xs = [], ys = [];
  for (let x = mean - 3 * sd; x <= mean + 3 * sd; x += sd / 15) {
    xs.push(x);
    ys.push(Math.exp(-0.5 * ((x - mean) / sd) ** 2));
  }
  Plotly.newPlot("marginChart", [{
    type: "scatter", mode: "lines", x: xs, y: ys, fill: "tozeroy",
    line: { color: C.blue, width: 2.5 },
    fillcolor: "rgba(61,139,253,0.18)",
    hovertemplate: "Margin %{x:.1f}<extra></extra>",
  }], {
    ...PLOT_LAYOUT,
    xaxis: { ...PLOT_LAYOUT.xaxis, title: "Margin (home − away)", zeroline: true, zerolinecolor: C.accent, zerolinewidth: 1.5 },
    yaxis: { ...PLOT_LAYOUT.yaxis, showticklabels: false, showgrid: false },
  }, PLOT_CONFIG);
}

// ── Standings sim ────────────────────────────────────────────────────────────
async function runStandings() {
  const tableEl = document.getElementById("standTable");
  loading(tableEl, "Running season simulation…");
  const sims = document.getElementById("standSims").value;
  const res = await fetch(`/api/standings?sims=${sims}`);
  const data = await res.json();
  const s = data.standings;

  Plotly.newPlot("standChart", [{
    type: "bar", orientation: "h",
    y: s.map((t) => t.team_id).reverse(),
    x: s.map((t) => t.projected_wins).reverse(),
    marker: { color: s.map((t) => t.conference === "East" ? C.blue : C.accent).reverse() },
    text: s.map((t) => t.projected_wins.toFixed(0)).reverse(), textposition: "auto",
    textfont: { color: "#fff" },
    hovertemplate: "%{y}<br>Proj wins <b>%{x:.1f}</b><extra></extra>",
  }], {
    ...PLOT_LAYOUT,
    xaxis: { ...PLOT_LAYOUT.xaxis, title: "Projected wins" },
    margin: { ...PLOT_LAYOUT.margin, l: 56 },
  }, PLOT_CONFIG);

  const rows = s.map((t) => `<tr>
    <td><div class="team-cell"><span class="team-dot" style="background:${tokenColor(t.team_id)}">${t.team_id}</span></div></td>
    <td><span class="conf-tag ${t.conference.toLowerCase()}">${t.conference}</span></td>
    <td class="num">${t.current_wins}</td>
    <td class="num">${t.projected_wins.toFixed(1)}</td>
    <td class="num">${(t.playoff_probability * 100).toFixed(1)}%</td>
    <td class="num">${(t.top_seed_probability * 100).toFixed(1)}%</td></tr>`).join("");
  tableEl.innerHTML = `<div class="table-wrap"><table>
    <thead><tr><th>Team</th><th>Conf</th><th class="num">Cur W</th>
    <th class="num">Proj W</th><th class="num">Playoff %</th><th class="num">Top Seed %</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

// ── Title odds ─────────────────────────────────────────────────────────────
async function runTitle() {
  const sims = document.getElementById("titleSims").value;
  const res = await fetch(`/api/title-odds?sims=${sims}`);
  const data = await res.json();
  const top = data.teams.filter((t) => t.title_probability > 0).slice(0, 14);

  Plotly.newPlot("titleChart", [
    { type: "bar", name: "Finals", y: top.map((t) => t.team_id).reverse(),
      x: top.map((t) => t.finals_probability * 100).reverse(), orientation: "h",
      marker: { color: C.blue },
      hovertemplate: "%{y}<br>Finals <b>%{x:.1f}%</b><extra></extra>" },
    { type: "bar", name: "Title", y: top.map((t) => t.team_id).reverse(),
      x: top.map((t) => t.title_probability * 100).reverse(), orientation: "h",
      marker: { color: C.amber },
      hovertemplate: "%{y}<br>Title <b>%{x:.1f}%</b><extra></extra>" },
  ], {
    ...PLOT_LAYOUT, barmode: "group",
    xaxis: { ...PLOT_LAYOUT.xaxis, title: "Probability (%)" },
    margin: { ...PLOT_LAYOUT.margin, l: 56 },
  }, PLOT_CONFIG);
}

document.getElementById("runPredict").addEventListener("click", runPredict);
document.getElementById("runStandings").addEventListener("click", runStandings);
document.getElementById("runTitle").addEventListener("click", runTitle);

loadTeams().then(runPredict);
