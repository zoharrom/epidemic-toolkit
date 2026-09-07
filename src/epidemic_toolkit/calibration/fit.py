"""Fit SEIR's beta and gamma to observed infected counts via scipy.optimize.curve_fit."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import curve_fit

from epidemic_toolkit.integrators.solvers import rk4
from epidemic_toolkit.models.seir import seir_derivatives

SIGMA_INFLUENZA: Final[float] = 0.5
DEFAULT_STEPS_PER_DAY: Final[int] = 10

# Search ranges for curve_fit. Without an upper bound on beta and a lower
# bound on gamma, curve_fit can drift toward degenerate solutions (gamma ->
# 0 with beta finite, giving an arbitrarily huge R0 = beta/gamma with no
# real improvement in fit). These bounds are wide enough not to clip the
# genuine best fit (verified against the unconstrained optimum for the
# boarding-school dataset) - they guard against blow-up, not against a
# high R0. For a short, sharp outbreak curve, a fixed (not fitted) sigma
# can genuinely require a high beta/gamma ratio to reproduce the observed
# rise, independent of initial conditions: see calibrate_seir's docstring.
DEFAULT_BETA_BOUNDS: Final[tuple[float, float]] = (0.0, 20.0)
DEFAULT_GAMMA_BOUNDS: Final[tuple[float, float]] = (1.0 / 14.0, 2.0)


@dataclass(frozen=True)
class SEIRFitResult:
    """Result of fitting SEIR's beta and gamma to observed data.

    Attributes:
        beta: Fitted transmission rate.
        gamma: Fitted recovery rate.
        beta_stderr: Standard error of beta from the fit covariance.
        gamma_stderr: Standard error of gamma from the fit covariance.
        covariance: 2x2 parameter covariance matrix returned by curve_fit,
            ordered (beta, gamma).
        predicted_infected: Model's I(t) at each observed day, using the
            fitted beta/gamma.
    """

    beta: float
    gamma: float
    beta_stderr: float
    gamma_stderr: float
    covariance: NDArray[np.float64]
    predicted_infected: list[float]

    @property
    def r0(self) -> float:
        """Basic reproduction number implied by the fitted parameters (beta/gamma)."""
        return self.beta / self.gamma


def simulate_infected(
    days: Sequence[int],
    beta: float,
    gamma: float,
    *,
    n_total: float,
    e0: float,
    i0: float,
    r0: float = 0.0,
    sigma: float = SIGMA_INFLUENZA,
    steps_per_day: int = DEFAULT_STEPS_PER_DAY,
) -> NDArray[np.float64]:
    """Integrate SEIR with RK4 and sample I(t) at the given integer days.

    Uses a fixed step size dt = 1/steps_per_day so that every integer day
    in days lands exactly on an integrator step (index = day *
    steps_per_day), avoiding any interpolation between steps.

    Args:
        days: Non-negative integer days at which to sample I(t), with t=0
            being the moment corresponding to the initial state derived
            from n_total, e0, i0, r0.
        beta: Transmission rate.
        gamma: Recovery rate.
        n_total: Total population N (S0 is derived as N - e0 - i0 - r0).
        e0: Initial exposed count at t=0.
        i0: Initial infectious count at t=0.
        r0: Initial recovered count at t=0. Defaults to 0.
        sigma: Fixed incubation rate (not fitted). Defaults to
            SIGMA_INFLUENZA.
        steps_per_day: Integrator sub-steps per day; dt = 1/steps_per_day.
            Defaults to 10 (dt = 0.1).

    Returns:
        1-D float64 array of I(day) for each day in days, same order.

    Raises:
        ValueError: If any day in days is negative.
    """
    if any(day < 0 for day in days):
        raise ValueError("days must be non-negative")

    s0 = n_total - e0 - i0 - r0
    y0 = (s0, e0, i0, r0)
    dt = 1.0 / steps_per_day
    t_end = float(max(days)) if days else 0.0

    trajectory = rk4(seir_derivatives, y0, (0.0, t_end), dt, beta, sigma, gamma)
    infected = np.array(
        [trajectory[day * steps_per_day][1][2] for day in days], dtype=np.float64
    )
    return infected


def calibrate_seir(
    days: Sequence[int],
    observed_infected: Sequence[float],
    *,
    n_total: float,
    e0: float,
    i0: float = 0.0,
    r0: float = 0.0,
    sigma: float = SIGMA_INFLUENZA,
    steps_per_day: int = DEFAULT_STEPS_PER_DAY,
    beta0: float = 1.0,
    gamma0: float = 0.5,
    beta_bounds: tuple[float, float] = DEFAULT_BETA_BOUNDS,
    gamma_bounds: tuple[float, float] = DEFAULT_GAMMA_BOUNDS,
) -> SEIRFitResult:
    """Fit SEIR's beta and gamma to observed infected counts via curve_fit.

    sigma and the initial conditions (n_total, e0, i0, r0) are held fixed;
    only beta and gamma are estimated, via scipy.optimize.curve_fit bounded
    to beta_bounds/gamma_bounds. The default bounds are wide enough to
    reach the genuine best fit rather than clipping it - they only guard
    against a degenerate gamma -> 0 blow-up. For a fixed sigma, note that
    a short/sharp outbreak curve can genuinely require a high beta/gamma
    ratio (a high implied R0) to reproduce the observed rise: this is a
    real property of holding the incubation rate fixed rather than fitting
    it, not a fitting bug. Callers who need a lower R0 should either supply
    a tighter gamma_bounds/beta_bounds (accepting a worse fit) or fit sigma
    too instead of using a fixed SIGMA_INFLUENZA.

    Args:
        days: Observed integer days (e.g. 1..14).
        observed_infected: Observed I(t) counts, same length/order as days.
        n_total: Total population N.
        e0: Fixed initial exposed count at t=0.
        i0: Fixed initial infectious count at t=0. Defaults to 0.
        r0: Fixed initial recovered count at t=0. Defaults to 0.
        sigma: Fixed incubation rate. Defaults to SIGMA_INFLUENZA (0.5/day).
        steps_per_day: Integrator resolution passed to simulate_infected.
        beta0: Initial guess for beta passed to curve_fit.
        gamma0: Initial guess for gamma passed to curve_fit.
        beta_bounds: (min, max) allowed values for beta. Defaults to
            DEFAULT_BETA_BOUNDS.
        gamma_bounds: (min, max) allowed values for gamma. Defaults to
            DEFAULT_GAMMA_BOUNDS.

    Returns:
        SEIRFitResult with fitted beta, gamma, their standard errors, the
        full covariance matrix, and predicted I(t) at days under the fit.
    """

    def _model(t: NDArray[np.float64], beta: float, gamma: float) -> NDArray[np.float64]:
        return simulate_infected(
            t.astype(int).tolist(),
            beta,
            gamma,
            n_total=n_total,
            e0=e0,
            i0=i0,
            r0=r0,
            sigma=sigma,
            steps_per_day=steps_per_day,
        )

    beta_lo, beta_hi = beta_bounds
    gamma_lo, gamma_hi = gamma_bounds
    popt, pcov = curve_fit(
        _model,
        np.asarray(days, dtype=np.float64),
        np.asarray(observed_infected, dtype=np.float64),
        p0=(beta0, gamma0),
        bounds=([beta_lo, gamma_lo], [beta_hi, gamma_hi]),
    )
    beta, gamma = popt
    predicted = simulate_infected(
        list(days),
        beta,
        gamma,
        n_total=n_total,
        e0=e0,
        i0=i0,
        r0=r0,
        sigma=sigma,
        steps_per_day=steps_per_day,
    )
    return SEIRFitResult(
        beta=float(beta),
        gamma=float(gamma),
        beta_stderr=float(np.sqrt(pcov[0, 0])),
        gamma_stderr=float(np.sqrt(pcov[1, 1])),
        covariance=pcov,
        predicted_infected=[float(value) for value in predicted],
    )
