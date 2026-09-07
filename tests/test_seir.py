"""Tests for the SEIR derivative function."""
from __future__ import annotations

import math

from epidemic_toolkit.integrators.solvers import rk4
from epidemic_toolkit.models.seir import seir_derivatives


def test_derivatives_sum_to_zero() -> None:
    """Total population has zero net derivative: SEIR has no births/deaths."""
    d_s, d_e, d_i, d_r = seir_derivatives(
        (700.0, 10.0, 40.0, 13.0), t=0.0, beta=0.3, sigma=0.5, gamma=0.1
    )
    assert math.isclose(d_s + d_e + d_i + d_r, 0.0, abs_tol=1e-9)


def test_no_change_when_no_exposed_or_infected() -> None:
    """With zero exposed and infected, nothing happens regardless of params."""
    derivatives = seir_derivatives(
        (763.0, 0.0, 0.0, 0.0), t=0.0, beta=0.5, sigma=0.5, gamma=0.2
    )
    assert derivatives == (0.0, 0.0, 0.0, 0.0)


def test_susceptible_decreases_and_recovered_increases() -> None:
    """S can only shrink and R can only grow while I > 0."""
    d_s, _, _, d_r = seir_derivatives(
        (700.0, 10.0, 40.0, 13.0), t=0.0, beta=0.4, sigma=0.5, gamma=0.1
    )
    assert d_s < 0
    assert d_r > 0


def test_exposed_flows_into_infected() -> None:
    """With E > 0 and I = 0, exposed drains into infectious via sigma alone."""
    d_s, d_e, d_i, d_r = seir_derivatives(
        (760.0, 3.0, 0.0, 0.0), t=0.0, beta=0.4, sigma=0.5, gamma=0.1
    )
    assert d_e < 0
    assert d_i > 0


def test_derivatives_independent_of_t() -> None:
    """SEIR is autonomous: t should not affect the result."""
    y = (700.0, 50.0, 10.0, 3.0)
    assert seir_derivatives(y, t=0.0, beta=0.3, sigma=0.5, gamma=0.1) == seir_derivatives(
        y, t=100.0, beta=0.3, sigma=0.5, gamma=0.1
    )


def test_seir_conserves_population_under_rk4() -> None:
    """S + E + I + R must stay constant at every step when driven by rk4."""
    y0 = (760.0, 3.0, 0.0, 0.0)
    n0 = sum(y0)
    trajectory = rk4(seir_derivatives, y0, (0.0, 50.0), 0.1, 0.3, 0.5, 0.1)
    for _, y in trajectory:
        assert math.isclose(sum(y), n0, rel_tol=1e-6)
