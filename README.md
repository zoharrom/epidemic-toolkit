# Epidemic Modeling Toolkit

A small full-stack toolkit for simulating and calibrating compartmental epidemic models (SIR/SEIR): hand-written numerical integrators, a real-data calibration pipeline, a FastAPI backend, and a vanilla JS frontend where you can build your own epidemic curve.

## What it does

- **Build your own epidemic curve** — move sliders for the transmission rate (β), incubation rate (σ), and recovery rate (γ), and watch a live SEIR simulation update. A banner explains what's happening to R0 as you go, including why the outbreak dies out when R0 < 1.
- **See a real calibrated example** — beta and gamma fitted via `scipy.optimize.curve_fit` against a real 1978 English boarding-school influenza outbreak, plotted against the actual observed case counts.

Run it locally (see [Setup](#setup)) and open `http://127.0.0.1:8000/`.

## The Math

### SIR model

The population splits into three compartments: **S**usceptible, **I**nfectious, **R**ecovered, with N = S + I + R held constant (no births/deaths).

```
dS/dt = -beta * S * I / N
dI/dt =  beta * S * I / N  -  gamma * I
dR/dt =  gamma * I
```

- **beta** — transmission rate: effective contacts per unit time, scaled by the probability of transmission per contact.
- **gamma** — recovery rate: the inverse of the average infectious period (gamma = 0.2 means people are infectious for about 5 days on average).
- **R0 = beta / gamma** — the basic reproduction number: how many people one infectious person infects, on average, in a fully susceptible population. R0 > 1 means the epidemic grows; R0 < 1 means it dies out on its own — the app's live banner shows this as you move the sliders.

### SEIR model

Adds an **E**xposed compartment for people who are infected but not yet infectious — the incubation period:

```
dS/dt = -beta * S * I / N
dE/dt =  beta * S * I / N  -  sigma * E
dI/dt =  sigma * E  -  gamma * I
dR/dt =  gamma * I
```

- **sigma** — incubation rate: the inverse of the average incubation period (sigma = 0.5 means about 2 days from exposure to becoming infectious).
- R0 is still `beta / gamma` — sigma delays *when* the epidemic takes off, but doesn't change how many people each infectious person eventually infects.

The Exposed compartment matters most when the incubation period is long relative to how fast an outbreak unfolds — see the Calibration section below for what happens when it isn't.

## Numerical Methods

Two hand-written, fixed-step integrators solve these ODEs — no numpy/scipy here; the point of this part of the project is demonstrating the algorithms themselves, not calling a library (`src/epidemic_toolkit/integrators/solvers.py`).

**Explicit Euler** steps forward using the current slope:
```
y(t + dt) = y(t) + dt * f(y(t), t)
```
Simple and fast, but its error grows roughly linearly with `dt` — it needs a small step size to stay accurate.

**Classical 4th-order Runge-Kutta (RK4)** averages four slope estimates across each step (one at `t`, two at the midpoint, one at `t + dt`) for a far more accurate update:
```
k1 = f(y, t)
k2 = f(y + dt/2 * k1, t + dt/2)
k3 = f(y + dt/2 * k2, t + dt/2)
k4 = f(y + dt * k3, t + dt)
y(t + dt) = y(t) + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
```

Both integrators are completely model-agnostic: they only ever call `f(y, t, *params) -> dy/dt` and never know what the state actually represents, so the exact same `euler`/`rk4` functions drive SIR, SEIR, or any other ODE system expressed the same way. `tests/test_solvers.py` verifies RK4 is meaningfully more accurate than Euler at an equal step size, against a known analytic solution.

## Calibration

`calibrate_seir()` (`src/epidemic_toolkit/calibration/fit.py`) fits beta and gamma to a real historical outbreak — the 1978 English boarding-school influenza epidemic (`data/boarding_school_flu.csv`) — via `scipy.optimize.curve_fit`, holding sigma fixed at a literature incubation value (2 days).

> Data source: "Influenza in a boarding school," *British Medical Journal*, 4 March 1978.

Worth knowing: the resulting fitted R0 (~22) is far higher than real influenza's actual R0 (roughly 1.2–1.4). That's not a bug in the fit — it's what happens when the incubation rate is held fixed while a real outbreak rises faster than that fixed delay can explain on its own, forcing the transmission rate to inflate to compensate. The app's "Real-world example" section explains this live, with the real published influenza parameters alongside it, for comparison.

## Architecture

```
src/epidemic_toolkit/
├── models/          # ODE right-hand sides (dy/dt), pure functions, no I/O
├── integrators/     # Generic fixed-step ODE solvers (euler, rk4), model-agnostic
├── calibration/      # Dataset loading + curve_fit-based parameter fitting
└── api/             # FastAPI app: POST /simulate, GET /calibrate; serves frontend/ as static files

frontend/            # Vanilla JS/HTML/CSS, no framework, no build step
data/                # Vendored historical datasets (static CSVs, no network access)
tests/               # One test file per source module (flat, mirrors module names)
```

`models/` defines *what* the equations are; `integrators/` defines *how* to step them forward in time. Any integrator can drive any model because both share the `f(y, t, *params) -> dy/dt` convention.

## Tech Stack

- **Python 3.11+**, stdlib only in `models/`/`integrators/` — hand-written to demonstrate the algorithms, not wrap a library.
- **numpy/scipy** in `calibration/` only, for `scipy.optimize.curve_fit`.
- **FastAPI + uvicorn** for the backend; also serves the frontend as static files (one process, no CORS setup needed to run it).
- **Vanilla JavaScript + Chart.js** (via CDN) for the frontend — no framework, no build step.
- **pytest** for testing (36 tests; `httpx`/`TestClient` for the API tests).

## Setup

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

## Run the app

```bash
uvicorn epidemic_toolkit.api.app:app --reload
```

Open `http://127.0.0.1:8000/` for the app, or `http://127.0.0.1:8000/docs` for interactive API docs.

## Roadmap

1. **Core engine** — SIR model + hand-written Euler and RK4 integrators, stdlib only.
2. **SEIR extension + calibration** — SEIR model + parameter calibration against real historical data via `scipy.optimize.curve_fit`.
3. **FastAPI backend** — `/simulate` and `/calibrate` endpoints.
4. **Frontend** — vanilla JS + Chart.js, sliders, live R0 explanation, real-data comparison.
5. **Tests, documentation, README.**

See `CLAUDE.md` for further implementation notes.
