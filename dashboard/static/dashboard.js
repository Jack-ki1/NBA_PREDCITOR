const PLOT_LAYOUT = {
  paper_bgcolor: "#161a22", plot_bgcolor: "#161a22",
  font: { color: "#e8eaed" }, margin: { t: 40, r: 20, b: 60, l: 50 },
};
const PLOT_CONFIG = { displayModeBar: false, responsive: true };
let TEAMS = [];
 
// ── Tab switching ─────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});
 
// ── Load teams ───────────────────────────────────────────────────────────
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
    <td class="num">${i + 1}</td><td>${t.id}</td><td>${t.name}</td>
    <td>${t.conference}</td><td class="num">${t.elo}</td>
    <td class="num">${t.wins}-${t.losses}</td></tr>`).join("");
  document.getElementById("teamsTable").innerHTML = `<table>
    <thead><tr><th class="num">#</th><th>Abbr</th><th>Team</th>
    <th>Conf</th><th class="num">Elo</th><th class="num">Record</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}
 
// ── Game prediction ──────────────────────────────────────────────────────
async function runPredict() {
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
  if (data.error) { alert(data.error); return; }
 
  const p = data.prediction, m = data.meta;
  let extra = "";
  if (p.home_cover_probability !== undefined)
    extra += `<span>ATS (${p.spread}): home covers <b>${(p.home_cover_probability * 100).toFixed(1)}%</b></span>`;
  if (p.over_probability !== undefined)
    extra += `<span>O/U (${p.total_line}): over <b>${(p.over_probability * 100).toFixed(1)}%</b></span>`;
 
  document.getElementById("predictResult").innerHTML = `
    <div class="headline">${m.away_team} @ ${m.home_team}
      <span class="badge ${m.confidence}">${m.confidence}</span></div>
    <div class="row">
      <span>Home win: <b>${(p.home_win_probability * 100).toFixed(1)}%</b></span>
      <span>Proj. score: <b>${p.projected_home_score.toFixed(0)}–${p.projected_away_score.toFixed(0)}</b></span>
      <span>Margin: <b>${p.expected_margin > 0 ? "+" : ""}${p.expected_margin.toFixed(1)}</b></span>
      <span>Total: <b>${p.expected_total.toFixed(0)}</b></span>
      ${extra}
    </div>`;
 
  Plotly.newPlot("winChart", [{
    type: "bar", x: [data.away.name, data.home.name],
    y: [p.away_win_probability * 100, p.home_win_probability * 100],
    marker: { color: ["#f55f4c", "#4c8bf5"] },
    text: [(p.away_win_probability * 100).toFixed(1) + "%", (p.home_win_probability * 100).toFixed(1) + "%"],
    textposition: "auto",
  }], { ...PLOT_LAYOUT, title: "Win Probability", yaxis: { title: "%", range: [0, 100] } }, PLOT_CONFIG);
 
  // Approximate normal margin distribution for display.
  const mean = p.expected_margin, sd = p.margin_std;
  const xs = [], ys = [];
  for (let x = mean - 3 * sd; x <= mean + 3 * sd; x += sd / 15) {
    xs.push(x);
    ys.push(Math.exp(-0.5 * ((x - mean) / sd) ** 2));
  }
  Plotly.newPlot("marginChart", [{
    type: "scatter", mode: "lines", x: xs, y: ys, fill: "tozeroy",
    line: { color: "#4c8bf5" },
  }], {
    ...PLOT_LAYOUT, title: "Home Margin Distribution",
    xaxis: { title: "Margin (home − away)", zeroline: true, zerolinecolor: "#f55f4c" },
    yaxis: { showticklabels: false },
  }, PLOT_CONFIG);
}
 
// ── Standings sim ────────────────────────────────────────────────────────
async function runStandings() {
  const sims = document.getElementById("standSims").value;
  const res = await fetch(`/api/standings?sims=${sims}`);
  const data = await res.json();
  const s = data.standings;
 
  Plotly.newPlot("standChart", [{
    type: "bar", orientation: "h",
    y: s.map((t) => t.team_id).reverse(),
    x: s.map((t) => t.projected_wins).reverse(),
    marker: { color: s.map((t) => t.conference === "East" ? "#4c8bf5" : "#f5a24c").reverse() },
    text: s.map((t) => t.projected_wins.toFixed(0)).reverse(), textposition: "auto",
  }], { ...PLOT_LAYOUT, title: "Projected Wins (blue = East, orange = West)",
    xaxis: { title: "Wins" }, margin: { ...PLOT_LAYOUT.margin, l: 60 } }, PLOT_CONFIG);
 
  const rows = s.map((t) => `<tr><td>${t.team_id}</td><td>${t.conference}</td>
    <td class="num">${t.current_wins}</td><td class="num">${t.projected_wins.toFixed(1)}</td>
    <td class="num">${(t.playoff_probability * 100).toFixed(1)}%</td>
    <td class="num">${(t.top_seed_probability * 100).toFixed(1)}%</td></tr>`).join("");
  document.getElementById("standTable").innerHTML = `<table>
    <thead><tr><th>Team</th><th>Conf</th><th class="num">Cur W</th>
    <th class="num">Proj W</th><th class="num">Playoff%</th><th class="num">Top Seed%</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}
 
// ── Title odds ───────────────────────────────────────────────────────────
async function runTitle() {
  const sims = document.getElementById("titleSims").value;
  const res = await fetch(`/api/title-odds?sims=${sims}`);
  const data = await res.json();
  const top = data.teams.filter((t) => t.title_probability > 0).slice(0, 14);
 
  Plotly.newPlot("titleChart", [
    { type: "bar", name: "Title", y: top.map((t) => t.team_id).reverse(),
      x: top.map((t) => t.title_probability * 100).reverse(), orientation: "h",
      marker: { color: "#f5c14c" } },
    { type: "bar", name: "Finals", y: top.map((t) => t.team_id).reverse(),
      x: top.map((t) => t.finals_probability * 100).reverse(), orientation: "h",
      marker: { color: "#4c8bf5" } },
  ], { ...PLOT_LAYOUT, barmode: "group", title: "Championship & Finals Odds (%)",
    xaxis: { title: "%" }, margin: { ...PLOT_LAYOUT.margin, l: 60 } }, PLOT_CONFIG);
}
 
document.getElementById("runPredict").addEventListener("click", runPredict);
document.getElementById("runStandings").addEventListener("click", runStandings);
document.getElementById("runTitle").addEventListener("click", runTitle);
 
loadTeams().then(runPredict);
