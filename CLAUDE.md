# Epidemic Modeling Toolkit

## Purpose

A full-stack toolkit for simulating and calibrating compartmental epidemic models (SIR/SEIR), built incrementally over several days.

The emphasis throughout is on understanding the underlying algorithms (hand-written numerical integrators, not just calling library functions) alongside clean software engineering practice (typed code, tests, clear structure).

## Roadmap

1. **Core engine**: SIR model + hand-written Euler and RK4 integrators, stdlib only.
2. **SEIR extension + calibration**: SEIR model + parameter calibration (beta, gamma) against real historical data via `scipy.optimize.curve_fit`.
3. **FastAPI backend**: exposing `/simulate` and `/calibrate` endpoints.
4. **Frontend**: Vanilla JS + Chart.js frontend with sliders and a chart (simulated vs. real data).
5. **Tests, documentation, README**: full test suite (36 tests), and a README explaining the math, numerical methods, and calibration approach for a human reader.

## Architecture

```
src/epidemic_toolkit/
├── models/          # ODE right-hand sides (dy/dt), pure functions, no I/O
│   ├── sir.py       # sir_derivatives(y, t, beta, gamma) -> (dS, dI, dR)
│   └── seir.py      # seir_derivatives(y, t, beta, sigma, gamma) -> (dS, dE, dI, dR)
├── integrators/     # Generic fixed-step ODE solvers, model-agnostic
│   └── solvers.py   # euler(f, y0, t_span, dt, *params), rk4(...)
├── calibration/     # Parameter fitting against real data; I/O allowed here
│   ├── datasets.py  # load_boarding_school_flu() -> ObservedOutbreak
│   └── fit.py       # calibrate_seir(...) -> SEIRFitResult (scipy.optimize.curve_fit)
└── api/             # FastAPI app; thin wrappers, no new modeling/calibration logic
    └── app.py        # POST /simulate, GET /calibrate; mounts frontend/ as static files

frontend/            # Vanilla JS/HTML/CSS, no framework, no build step
├── index.html       # sliders for beta/sigma/gamma + simulated chart; real-data comparison chart
├── app.js           # fetches /simulate and /calibrate, drives both Chart.js charts
└── style.css

data/                # Vendored historical datasets (static CSVs, no network access)
└── boarding_school_flu.csv
```

Design principle: `models/` defines *what* the equations are; `integrators/` defines *how* to step them forward in time. Any integrator can drive any model, because both share the `f(y, t, *params) -> dy/dt` convention. This is what lets SEIR (step 2) reuse `euler`/`rk4` unchanged.

## Tech Stack

- Python 3.11+, stdlib only in `models/` and `integrators/` (no numpy/scipy) — the integrators are hand-written to demonstrate the algorithms themselves, not wrap a library.
- numpy/scipy in `calibration/` only, for `scipy.optimize.curve_fit`-based fitting. Never used in the integrators themselves.
- FastAPI + uvicorn in `api/` — thin HTTP wrappers around the existing engine, no new modeling/calibration logic. Also serves `frontend/` as static files (mounted at `/`, after the API routes), so the whole app runs from one process with no separate dev server or CORS setup needed.
- Vanilla JavaScript + Chart.js (via CDN) for the frontend — no framework, no build step. Chart.js loaded from `cdn.jsdelivr.net`.
- pytest for testing (httpx via FastAPI's `TestClient` for the API tests).
- Dependency management via `pyproject.toml`, installed with plain `pip install -e ".[dev]"` (no poetry/uv).

## Datasets

`data/boarding_school_flu.csv` — daily "boys in bed" counts from the 1978 English boarding-school influenza outbreak ("Influenza in a boarding school," British Medical Journal, 4 March 1978), N=763 total. Vendored as a static CSV (no network access) so calibration tests stay deterministic and offline.

`calibrate_seir` fits both beta and gamma, with sigma (incubation rate) fixed at a literature influenza value (0.5/day, a 2-day incubation period). Because this outbreak's case count rises very fast (3 to 298 boys in 5 days), the fit genuinely implies a high R0 (~20+) to reproduce that rise given a fixed 2-day incubation delay — this is a real, documented consequence of holding sigma fixed rather than a fitting bug; see the docstrings in `calibration/fit.py` and `tests/test_fit.py::test_calibrate_seir_runs_on_real_dataset` for the full explanation.

## Frontend

Two independent charts: an interactive "build your own epidemic curve" SEIR simulation driven by sliders (debounced calls to `/simulate` as they move), and a static "real-world example" chart loaded once from `/calibrate` showing the flu dataset's fitted-vs-observed curve. They're kept separate rather than overlaid on one chart, since the interactive simulation's population/parameters generally won't match the flu dataset's fixed N=763, which would otherwise make the two curves' scales misleading side by side.

R0 (= beta / gamma) is computed client-side in `app.js` and shown live as sliders move. When R0 < 1, a banner explains that the outbreak cannot sustain itself and will die out — the simulation still runs and is shown (a dying-out curve is a valid, informative result), the banner is purely explanatory, not a validation error.

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Running the app

```bash
pip install -e ".[dev]"
uvicorn epidemic_toolkit.api.app:app --reload
```

Open `http://127.0.0.1:8000/` for the frontend, or `http://127.0.0.1:8000/docs` for interactive API docs (Swagger UI).

## Conventions

See `.claude/skills/engine-standards/SKILL.md` for the standards enforced on this codebase: type hints, docstrings, and a test for every new function.
