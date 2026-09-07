"""FastAPI app: POST /simulate (SIR/SEIR trajectories) and GET /calibrate.

Both endpoints are thin wrappers around the already-tested engine in
models/, integrators/, and calibration/ - no new modeling or calibration
logic lives here. The frontend/ directory is mounted as static files at
"/" (after the API routes, so they take precedence), serving the vanilla
JS/HTML/CSS UI from the same process - no separate dev server or CORS
setup needed to use the app.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from epidemic_toolkit.calibration.datasets import (
    BOARDING_SCHOOL_TOTAL_POPULATION,
    load_boarding_school_flu,
)
from epidemic_toolkit.calibration.fit import calibrate_seir
from epidemic_toolkit.integrators.solvers import rk4
from epidemic_toolkit.models.seir import seir_derivatives
from epidemic_toolkit.models.sir import sir_derivatives

MAX_SIMULATION_STEPS: Final[int] = 2000
FRONTEND_DIR: Final[Path] = Path(__file__).resolve().parents[3] / "frontend"

app = FastAPI(title="Epidemic Toolkit API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SimulateRequest(BaseModel):
    """Request body for POST /simulate.

    Attributes:
        model: Which compartmental model to integrate, "sir" or "seir".
        beta: Transmission rate.
        gamma: Recovery rate.
        sigma: Incubation rate. Required (and only used) when model="seir".
        s0: Initial susceptible count.
        e0: Initial exposed count. Ignored when model="sir".
        i0: Initial infectious count.
        r0: Initial recovered count.
        t_end: End time of the simulation (start is always 0.0).
        dt: Fixed integrator step size.
    """

    model: Literal["sir", "seir"]
    beta: float = Field(gt=0)
    gamma: float = Field(gt=0)
    sigma: float | None = Field(default=None, gt=0)
    s0: float = Field(ge=0)
    e0: float = Field(default=0.0, ge=0)
    i0: float = Field(ge=0)
    r0: float = Field(default=0.0, ge=0)
    t_end: float = Field(gt=0)
    dt: float = Field(gt=0)

    @model_validator(mode="after")
    def _validate(self) -> "SimulateRequest":
        """Enforce cross-field invariants that Field() alone can't express.

        Returns:
            self, unchanged, once all checks pass.

        Raises:
            ValueError: If model="seir" but sigma is missing; if the
                initial compartments sum to zero (division by zero in the
                model derivatives); or if t_end/dt would exceed
                MAX_SIMULATION_STEPS integrator steps.
        """
        if self.model == "seir" and self.sigma is None:
            raise ValueError("sigma is required when model='seir'")
        if self.s0 + self.e0 + self.i0 + self.r0 == 0:
            raise ValueError("initial compartments must not all be zero")
        if self.t_end / self.dt > MAX_SIMULATION_STEPS:
            raise ValueError(f"t_end/dt must not exceed {MAX_SIMULATION_STEPS} steps")
        return self


class SimulateResponse(BaseModel):
    """Response body for POST /simulate.

    Attributes:
        model: Which compartmental model was integrated.
        t: Time points of the trajectory, including t=0.
        compartments: One list per compartment (e.g. "S", "I", "R" for sir;
            "S", "E", "I", "R" for seir), each parallel to t.
    """

    model: Literal["sir", "seir"]
    t: list[float]
    compartments: dict[str, list[float]]


class CalibrateResponse(BaseModel):
    """Response body for GET /calibrate.

    Attributes:
        beta: Fitted transmission rate.
        gamma: Fitted recovery rate.
        beta_stderr: Standard error of beta.
        gamma_stderr: Standard error of gamma.
        r0: Implied basic reproduction number (beta / gamma).
        days: Observed days from the vendored flu dataset.
        observed_infected: Observed "in bed" counts, parallel to days.
        predicted_infected: Model's I(t) at each day under the fit,
            parallel to days.
    """

    beta: float
    gamma: float
    beta_stderr: float
    gamma_stderr: float
    r0: float
    days: list[int]
    observed_infected: list[int]
    predicted_infected: list[float]


def _run_simulation(request: SimulateRequest) -> SimulateResponse:
    """Integrate the requested model with rk4 and package the trajectory.

    Args:
        request: Validated simulation parameters.

    Returns:
        SimulateResponse with the time points and one series per
        compartment.
    """
    if request.model == "sir":
        y0 = (request.s0, request.i0, request.r0)
        trajectory = rk4(
            sir_derivatives, y0, (0.0, request.t_end), request.dt, request.beta, request.gamma
        )
        labels = ("S", "I", "R")
    else:
        assert request.sigma is not None
        y0 = (request.s0, request.e0, request.i0, request.r0)
        trajectory = rk4(
            seir_derivatives,
            y0,
            (0.0, request.t_end),
            request.dt,
            request.beta,
            request.sigma,
            request.gamma,
        )
        labels = ("S", "E", "I", "R")

    t = [point[0] for point in trajectory]
    compartments = {
        label: [point[1][index] for point in trajectory] for index, label in enumerate(labels)
    }
    return SimulateResponse(model=request.model, t=t, compartments=compartments)


def _run_calibration() -> CalibrateResponse:
    """Fit SEIR to the vendored flu dataset and package the result.

    Returns:
        CalibrateResponse with the fitted parameters and both the observed
        and predicted infected counts, for plotting fitted-vs-observed.
    """
    observed = load_boarding_school_flu()
    result = calibrate_seir(
        observed.days,
        observed.in_bed,
        n_total=float(BOARDING_SCHOOL_TOTAL_POPULATION),
        e0=1.0,
        i0=0.0,
        r0=0.0,
    )
    return CalibrateResponse(
        beta=result.beta,
        gamma=result.gamma,
        beta_stderr=result.beta_stderr,
        gamma_stderr=result.gamma_stderr,
        r0=result.r0,
        days=observed.days,
        observed_infected=observed.in_bed,
        predicted_infected=result.predicted_infected,
    )


@app.post("/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest) -> SimulateResponse:
    """Simulate an SIR or SEIR trajectory from caller-supplied parameters.

    Args:
        request: Model choice, rate parameters, initial conditions, and
            integration settings.

    Returns:
        The simulated trajectory.
    """
    return _run_simulation(request)


@app.get("/calibrate", response_model=CalibrateResponse)
def calibrate() -> CalibrateResponse:
    """Fit SEIR's beta/gamma to the vendored 1978 flu outbreak dataset.

    Returns:
        The fitted parameters plus observed and predicted infected counts.
    """
    return _run_calibration()


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
