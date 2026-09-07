"""Hand-written fixed-step ODE integrators: explicit Euler and classical RK4.

Both integrators operate on any derivative function of the form
f(y, t, *params) -> dy/dt, so they work with SIR, SEIR, or any other system
of ODEs expressed as a tuple of floats. No numpy/scipy is used here on
purpose, to demonstrate the numerical methods themselves.
"""
from __future__ import annotations

from collections.abc import Callable

State = tuple[float, ...]
DerivativeFunc = Callable[..., State]


def euler(
    f: DerivativeFunc,
    y0: State,
    t_span: tuple[float, float],
    dt: float,
    *args: float,
) -> list[tuple[float, State]]:
    """Integrate dy/dt = f(y, t, *args) with the explicit Euler method.

    Args:
        f: Derivative function taking (y, t, *args) and returning dy/dt.
        y0: Initial state at t_span[0].
        t_span: (t_start, t_end) time interval, inclusive of both ends.
        dt: Fixed step size.
        *args: Extra positional parameters forwarded to f (e.g. beta, gamma).

    Returns:
        List of (t, y) pairs, one per step, including the initial condition
        as the first entry.
    """
    t0, t1 = t_span
    n_steps = round((t1 - t0) / dt)
    trajectory: list[tuple[float, State]] = [(t0, y0)]
    t, y = t0, y0
    for _ in range(n_steps):
        dydt = f(y, t, *args)
        y = tuple(yi + dt * dyi for yi, dyi in zip(y, dydt))
        t += dt
        trajectory.append((t, y))
    return trajectory


def rk4(
    f: DerivativeFunc,
    y0: State,
    t_span: tuple[float, float],
    dt: float,
    *args: float,
) -> list[tuple[float, State]]:
    """Integrate dy/dt = f(y, t, *args) with the classical 4th-order Runge-Kutta method.

    Args:
        f: Derivative function taking (y, t, *args) and returning dy/dt.
        y0: Initial state at t_span[0].
        t_span: (t_start, t_end) time interval, inclusive of both ends.
        dt: Fixed step size.
        *args: Extra positional parameters forwarded to f (e.g. beta, gamma).

    Returns:
        List of (t, y) pairs, one per step, including the initial condition
        as the first entry.
    """
    t0, t1 = t_span
    n_steps = round((t1 - t0) / dt)
    trajectory: list[tuple[float, State]] = [(t0, y0)]
    t, y = t0, y0
    for _ in range(n_steps):
        k1 = f(y, t, *args)
        y2 = tuple(yi + dt / 2 * ki for yi, ki in zip(y, k1))
        k2 = f(y2, t + dt / 2, *args)
        y3 = tuple(yi + dt / 2 * ki for yi, ki in zip(y, k2))
        k3 = f(y3, t + dt / 2, *args)
        y4 = tuple(yi + dt * ki for yi, ki in zip(y, k3))
        k4 = f(y4, t + dt, *args)
        y = tuple(
            yi + dt / 6 * (k1i + 2 * k2i + 2 * k3i + k4i)
            for yi, k1i, k2i, k3i, k4i in zip(y, k1, k2, k3, k4)
        )
        t += dt
        trajectory.append((t, y))
    return trajectory
