"""SEIR (Susceptible-Exposed-Infected-Recovered) compartmental epidemic model."""
from __future__ import annotations


def seir_derivatives(
    y: tuple[float, float, float, float],
    t: float,
    beta: float,
    sigma: float,
    gamma: float,
) -> tuple[float, float, float, float]:
    """Compute the SEIR model derivatives (dS/dt, dE/dt, dI/dt, dR/dt) at state y.

    Args:
        y: Current state (S, E, I, R) as population counts or fractions.
        t: Current time. Unused since the SEIR system is time-invariant, but
            kept so this function matches the f(y, t, *params) signature
            expected by the integrators in epidemic_toolkit.integrators.
        beta: Effective transmission rate (contacts per unit time scaled by
            transmission probability).
        sigma: Incubation rate, the inverse of the mean incubation period
            (time spent exposed but not yet infectious).
        gamma: Recovery rate (inverse of the mean infectious period).

    Returns:
        Tuple of derivatives (dS/dt, dE/dt, dI/dt, dR/dt).
    """
    s, e, i, r = y
    n = s + e + i + r
    new_infections = beta * s * i / n
    new_infectious = sigma * e
    recoveries = gamma * i
    d_s = -new_infections
    d_e = new_infections - new_infectious
    d_i = new_infectious - recoveries
    d_r = recoveries
    return (d_s, d_e, d_i, d_r)
