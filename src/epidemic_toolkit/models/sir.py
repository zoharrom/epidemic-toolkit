"""SIR (Susceptible-Infected-Recovered) compartmental epidemic model."""
from __future__ import annotations


def sir_derivatives(
    y: tuple[float, float, float],
    t: float,
    beta: float,
    gamma: float,
) -> tuple[float, float, float]:
    """Compute the SIR model derivatives (dS/dt, dI/dt, dR/dt) at state y.

    Args:
        y: Current state (S, I, R) as population counts or fractions.
        t: Current time. Unused since the SIR system is time-invariant, but
            kept so this function matches the f(y, t, *params) signature
            expected by the integrators in epidemic_toolkit.integrators.
        beta: Effective transmission rate (contacts per unit time scaled by
            transmission probability).
        gamma: Recovery rate (inverse of the mean infectious period).

    Returns:
        Tuple of derivatives (dS/dt, dI/dt, dR/dt).
    """
    s, i, r = y
    n = s + i + r
    new_infections = beta * s * i / n
    recoveries = gamma * i
    d_s = -new_infections
    d_i = new_infections - recoveries
    d_r = recoveries
    return (d_s, d_i, d_r)
