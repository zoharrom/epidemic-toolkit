"""Tests for loading the vendored boarding-school influenza dataset."""
from __future__ import annotations

import pytest

from epidemic_toolkit.calibration.datasets import (
    BOARDING_SCHOOL_TOTAL_POPULATION,
    DEFAULT_DATASET_PATH,
    load_boarding_school_flu,
)


def test_load_returns_expected_shape() -> None:
    """The dataset has 14 daily observations, days 1 through 14."""
    obs = load_boarding_school_flu()
    assert len(obs.days) == 14
    assert len(obs.in_bed) == 14
    assert obs.days == list(range(1, 15))


def test_load_matches_known_values() -> None:
    """Spot-check the standard published counts, guarding against typos."""
    obs = load_boarding_school_flu()
    assert obs.in_bed[0] == 3
    assert obs.in_bed[5] == 298
    assert obs.in_bed[-1] == 4
    assert sum(obs.in_bed) == 1559


def test_total_population_constant() -> None:
    """The boarding school had 763 boys total."""
    assert BOARDING_SCHOOL_TOTAL_POPULATION == 763


def test_default_dataset_path_resolves_and_exists() -> None:
    """The default path points at a real, vendored file."""
    assert DEFAULT_DATASET_PATH.is_file()


def test_missing_file_raises() -> None:
    """Loading a nonexistent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_boarding_school_flu(DEFAULT_DATASET_PATH.parent / "nope.csv")
