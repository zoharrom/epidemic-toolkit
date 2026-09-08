const DT = 0.1;

const els = {
  population: document.getElementById("population"),
  exposed0: document.getElementById("exposed0"),
  beta: document.getElementById("beta"),
  sigma: document.getElementById("sigma"),
  gamma: document.getElementById("gamma"),
  days: document.getElementById("days"),
  betaValue: document.getElementById("beta-value"),
  sigmaValue: document.getElementById("sigma-value"),
  gammaValue: document.getElementById("gamma-value"),
  daysValue: document.getElementById("days-value"),
  r0Banner: document.getElementById("r0-banner"),
  calibrationSummary: document.getElementById("calibration-summary"),
  statPeak: document.getElementById("stat-peak"),
  statAttackRate: document.getElementById("stat-attack-rate"),
  statHerdImmunity: document.getElementById("stat-herd-immunity"),
};

function debounce(fn, delayMs) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delayMs);
  };
}

function updateR0Banner() {
  const beta = parseFloat(els.beta.value);
  const gamma = parseFloat(els.gamma.value);
  const r0 = beta / gamma;

  els.r0Banner.textContent =
    `R0 = beta / gamma = ${r0.toFixed(2)}. ` +
    (r0 < 1
      ? "Since R0 is below 1, each infectious person infects fewer than one other person on average, so this outbreak cannot sustain itself and will die out on its own. Increase beta or decrease gamma so R0 is above 1 to see the epidemic actually spread."
      : "Since R0 is above 1, each infectious person infects more than one other person on average, so the epidemic is expected to spread.");
  els.r0Banner.className = "r0-banner " + (r0 < 1 ? "warn" : "ok");
}

function simulationRequestBody() {
  const n = parseFloat(els.population.value);
  const e0 = parseFloat(els.exposed0.value);
  return {
    model: "seir",
    beta: parseFloat(els.beta.value),
    sigma: parseFloat(els.sigma.value),
    gamma: parseFloat(els.gamma.value),
    s0: n - e0,
    e0: e0,
    i0: 0,
    r0: 0,
    t_end: parseFloat(els.days.value),
    dt: DT,
  };
}

let simulationChart;

function initSimulationChart() {
  simulationChart = new Chart(document.getElementById("simulation-chart"), {
    type: "line",
    data: {
      datasets: [
        { label: "Susceptible", data: [], borderColor: "#2f6fed", pointRadius: 0 },
        { label: "Exposed", data: [], borderColor: "#e2a33a", pointRadius: 0 },
        { label: "Infectious", data: [], borderColor: "#d64545", pointRadius: 0 },
        { label: "Recovered", data: [], borderColor: "#3fa85c", pointRadius: 0 },
        {
          label: "Peak",
          data: [],
          borderColor: "#1c2333",
          backgroundColor: "#1c2333",
          showLine: false,
          pointRadius: 6,
          pointStyle: "triangle",
        },
      ],
    },
    options: {
      responsive: true,
      animation: false,
      parsing: false,
      scales: {
        x: { type: "linear", title: { display: true, text: "Day" } },
        y: { title: { display: true, text: "People" }, beginAtZero: true },
      },
    },
  });
}

function updateStats(data, n, beta, gamma) {
  const infectious = data.compartments.I;
  let peakIndex = 0;
  for (let i = 1; i < infectious.length; i++) {
    if (infectious[i] > infectious[peakIndex]) {
      peakIndex = i;
    }
  }
  const peakDay = Math.round(data.t[peakIndex]);
  const peakCount = Math.round(infectious[peakIndex]);
  els.statPeak.textContent = `Day ${peakDay}, ${peakCount.toLocaleString()} people`;

  const finalSusceptible = data.compartments.S[data.compartments.S.length - 1];
  const attackRate = ((n - finalSusceptible) / n) * 100;
  els.statAttackRate.textContent = `${attackRate.toFixed(1)}%`;

  const r0 = beta / gamma;
  els.statHerdImmunity.textContent =
    r0 > 1 ? `${((1 - 1 / r0) * 100).toFixed(1)}%` : "Not needed (R0 ≤ 1)";

  return { x: data.t[peakIndex], y: infectious[peakIndex] };
}

async function runSimulation() {
  const requestBody = simulationRequestBody();
  const response = await fetch("/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  const toPoints = (values) => data.t.map((t, i) => ({ x: t, y: values[i] }));

  simulationChart.data.datasets[0].data = toPoints(data.compartments.S);
  simulationChart.data.datasets[1].data = toPoints(data.compartments.E);
  simulationChart.data.datasets[2].data = toPoints(data.compartments.I);
  simulationChart.data.datasets[3].data = toPoints(data.compartments.R);

  const n = requestBody.s0 + requestBody.e0 + requestBody.i0 + requestBody.r0;
  const peakPoint = updateStats(data, n, requestBody.beta, requestBody.gamma);
  simulationChart.data.datasets[4].data = [peakPoint];

  simulationChart.update();
}

const runSimulationDebounced = debounce(runSimulation, 150);

function onControlChanged() {
  els.betaValue.textContent = parseFloat(els.beta.value).toFixed(2);
  els.sigmaValue.textContent = parseFloat(els.sigma.value).toFixed(2);
  els.gammaValue.textContent = parseFloat(els.gamma.value).toFixed(2);
  els.daysValue.textContent = els.days.value;
  updateR0Banner();
  runSimulationDebounced();
}

[els.population, els.exposed0, els.beta, els.sigma, els.gamma, els.days].forEach((el) =>
  el.addEventListener("input", onControlChanged)
);

let calibrationChart;

async function loadCalibration() {
  calibrationChart = new Chart(document.getElementById("calibration-chart"), {
    type: "line",
    data: { labels: [], datasets: [] },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: "Day" } },
        y: { title: { display: true, text: "Students in bed" }, beginAtZero: true },
      },
    },
  });

  const response = await fetch("/calibrate");
  if (!response.ok) {
    els.calibrationSummary.textContent = "Could not load the calibration fit.";
    return;
  }
  const data = await response.json();

  els.calibrationSummary.textContent =
    `Fitted beta = ${data.beta.toFixed(3)} (+/- ${data.beta_stderr.toFixed(3)}), ` +
    `gamma = ${data.gamma.toFixed(3)} (+/- ${data.gamma_stderr.toFixed(3)}), R0 = ${data.r0.toFixed(2)}.`;

  calibrationChart.data.labels = data.days;
  calibrationChart.data.datasets = [
    {
      label: "Observed (in bed)",
      data: data.observed_infected,
      borderColor: "#1c2333",
      backgroundColor: "#1c2333",
      showLine: false,
      pointRadius: 4,
    },
    {
      label: "Model fit",
      data: data.predicted_infected,
      borderColor: "#d64545",
      pointRadius: 0,
    },
  ];
  calibrationChart.update();
}

initSimulationChart();
updateR0Banner();
runSimulation();
loadCalibration();
