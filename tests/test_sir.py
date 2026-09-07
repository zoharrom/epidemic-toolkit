"""Tests for the SIR derivative function."""
from __future__ import annotations

import math

from epidemic_toolkit.models.sir import sir_derivatives


def test_derivatives_sum_to_zero() -> None:
    """Total population has zero net derivative: SIR has no births/deaths."""
    d_s, d_i, d_r = sir_derivatives((990.0, 10.0, 0.0), t=0.0, beta=0.3, gamma=0.1)
    assert math.isclose(d_s + d_i + d_r, 0.0, abs_tol=1e-9)


def test_no_change_when_no_infected() -> None:
    """With zero infected, nothing happens regardless of beta/gamma."""
    derivatives = sir_derivatives((1000.0, 0.0, 0.0), t=0.0, beta=0.5, gamma=0.2)
    assert derivatives == (0.0, 0.0, 0.0)


def test_susceptible_decreases_and_recovered_increases() -> None:
    """S can only shrink and R can only grow while I > 0."""
    d_s, _, d_r = sir_derivatives((900.0, 100.0, 0.0), t=0.0, beta=0.4, gamma=0.1)
    assert d_s < 0
    assert d_r > 0


def test_derivatives_independent_of_t() -> None:
    """SIR is autonomous: t should not affect the result."""
    y = (800.0, 150.0, 50.0)
    assert sir_derivatives(y, t=0.0, beta=0.3, gamma=0.1) == sir_derivatives(
        y, t=100.0, beta=0.3, gamma=0.1
    )
