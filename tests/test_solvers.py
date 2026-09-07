"""Tests for the hand-written Euler and RK4 integrators."""
from __future__ import annotations

import math

import pytest

from epidemic_toolkit.integrators.solvers import DerivativeFunc, State, euler, rk4
from epidemic_toolkit.models.sir import sir_derivatives

INTEGRATORS = [euler, rk4]
INTEGRATOR_IDS = ["euler", "rk4"]


def exponential_decay(y: State, t: float, k: float) -> State:
    """dy/dt = -k*y, with known analytic solution y(t) = y0 * exp(-k*t)."""
    (value,) = y
    return (-k * value,)


@pytest.mark.parametrize("integrator", INTEGRATORS, ids=INTEGRATOR_IDS)
def test_population_is_conserved(integrator: DerivativeFunc) -> None:
    """S + I + R must stay constant at every step, for both integrators."""
    y0 = (990.0, 10.0, 0.0)
    n0 = sum(y0)
    trajectory = integrator(sir_derivatives, y0, (0.0, 160.0), 0.1, 0.3, 0.1)
    for _, y in trajectory:
        assert math.isclose(sum(y), n0, rel_tol=1e-6)


@pytest.mark.parametrize("integrator", INTEGRATORS, ids=INTEGRATOR_IDS)
def test_outbreak_dies_out(integrator: DerivativeFunc) -> None:
    """When R0 = beta/gamma > 1, I rises then decays to near zero."""
    y0 = (990.0, 10.0, 0.0)
    trajectory = integrator(sir_derivatives, y0, (0.0, 200.0), 0.1, 0.3, 0.1)
    infected = [y[1] for _, y in trajectory]
    assert max(infected) > y0[1]
    assert infected[-1] < 1.0


@pytest.mark.parametrize("integrator", INTEGRATORS, ids=INTEGRATOR_IDS)
def test_no_outbreak_when_r0_below_one(integrator: DerivativeFunc) -> None:
    """When R0 = beta/gamma < 1, I decreases monotonically from the start."""
    y0 = (990.0, 10.0, 0.0)
    trajectory = integrator(sir_derivatives, y0, (0.0, 100.0), 0.1, 0.1, 0.3)
    infected = [y[1] for _, y in trajectory]
    assert all(a >= b - 1e-9 for a, b in zip(infected, infected[1:]))


def test_rk4_more_accurate_than_euler_on_known_solution() -> None:
    """RK4 should track y' = -k*y far more closely than Euler at equal step size."""
    y0 = (1.0,)
    k = 1.0
    t_end = 5.0
    dt = 0.5
    exact = math.exp(-k * t_end)

    euler_result = euler(exponential_decay, y0, (0.0, t_end), dt, k)[-1][1][0]
    rk4_result = rk4(exponential_decay, y0, (0.0, t_end), dt, k)[-1][1][0]

    euler_error = abs(euler_result - exact)
    rk4_error = abs(rk4_result - exact)
    assert rk4_error < euler_error
    assert rk4_error < 1e-3


def test_trajectory_includes_initial_condition() -> None:
    """The returned trajectory's first entry is exactly (t0, y0)."""
    y0 = (100.0, 5.0, 0.0)
    trajectory = rk4(sir_derivatives, y0, (0.0, 1.0), 0.1, 0.3, 0.1)
    assert trajectory[0] == (0.0, y0)
