"""Tests for the FastAPI /simulate, /calibrate, and static frontend routes."""
from __future__ import annotations

from fastapi.testclient import TestClient

from epidemic_toolkit.api.app import app

client = TestClient(app)


def test_simulate_sir_returns_trajectory() -> None:
    """A valid SIR request returns S/I/R series parallel to t."""
    response = client.post(
        "/simulate",
        json={
            "model": "sir",
            "beta": 0.3,
            "gamma": 0.1,
            "s0": 990.0,
            "i0": 10.0,
            "r0": 0.0,
            "t_end": 50.0,
            "dt": 1.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["t"][0] == 0.0
    assert set(body["compartments"].keys()) == {"S", "I", "R"}
    for series in body["compartments"].values():
        assert len(series) == len(body["t"])


def test_simulate_seir_returns_trajectory() -> None:
    """A valid SEIR request returns S/E/I/R series parallel to t."""
    response = client.post(
        "/simulate",
        json={
            "model": "seir",
            "beta": 0.3,
            "sigma": 0.5,
            "gamma": 0.1,
            "s0": 760.0,
            "e0": 3.0,
            "i0": 0.0,
            "r0": 0.0,
            "t_end": 50.0,
            "dt": 1.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body["compartments"].keys()) == {"S", "E", "I", "R"}


def test_simulate_rejects_negative_beta() -> None:
    """A negative beta fails Pydantic's gt=0 validation."""
    response = client.post(
        "/simulate",
        json={
            "model": "sir",
            "beta": -1.0,
            "gamma": 0.1,
            "s0": 990.0,
            "i0": 10.0,
            "r0": 0.0,
            "t_end": 50.0,
            "dt": 1.0,
        },
    )
    assert response.status_code == 422


def test_simulate_seir_requires_sigma() -> None:
    """model="seir" without sigma fails the cross-field validator."""
    response = client.post(
        "/simulate",
        json={
            "model": "seir",
            "beta": 0.3,
            "gamma": 0.1,
            "s0": 760.0,
            "e0": 3.0,
            "i0": 0.0,
            "r0": 0.0,
            "t_end": 50.0,
            "dt": 1.0,
        },
    )
    assert response.status_code == 422


def test_simulate_rejects_zero_population() -> None:
    """All-zero initial compartments would divide by zero in the model."""
    response = client.post(
        "/simulate",
        json={
            "model": "sir",
            "beta": 0.3,
            "gamma": 0.1,
            "s0": 0.0,
            "i0": 0.0,
            "r0": 0.0,
            "t_end": 50.0,
            "dt": 1.0,
        },
    )
    assert response.status_code == 422


def test_simulate_rejects_too_many_steps() -> None:
    """A dt/t_end combination past MAX_SIMULATION_STEPS is rejected."""
    response = client.post(
        "/simulate",
        json={
            "model": "sir",
            "beta": 0.3,
            "gamma": 0.1,
            "s0": 990.0,
            "i0": 10.0,
            "r0": 0.0,
            "t_end": 1000.0,
            "dt": 0.01,
        },
    )
    assert response.status_code == 422


def test_calibrate_returns_fitted_params_in_sane_range() -> None:
    """The endpoint wires calibrate_seir up correctly against the real dataset."""
    response = client.get("/calibrate")
    assert response.status_code == 200
    body = response.json()
    assert body["beta"] > 0
    assert body["gamma"] > 0
    assert body["r0"] < 1000.0
    assert len(body["days"]) == len(body["observed_infected"]) == len(body["predicted_infected"])


def test_root_serves_frontend_index() -> None:
    """The static mount serves frontend/index.html at the site root."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Epidemic Modeling Toolkit" in response.text
