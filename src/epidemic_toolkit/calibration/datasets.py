"""Loading the vendored boarding-school influenza dataset.

Data source: "Influenza in a boarding school," British Medical Journal,
4 March 1978.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Final, NamedTuple

BOARDING_SCHOOL_TOTAL_POPULATION: Final[int] = 763

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
DEFAULT_DATASET_PATH: Final[Path] = _REPO_ROOT / "data" / "boarding_school_flu.csv"


class ObservedOutbreak(NamedTuple):
    """Parsed daily observations from a historical outbreak dataset.

    Attributes:
        days: Observed integer days, in ascending order.
        in_bed: Observed daily case counts, parallel to days by index.
    """

    days: list[int]
    in_bed: list[int]


def load_boarding_school_flu(path: Path | None = None) -> ObservedOutbreak:
    """Load the 1978 English boarding-school influenza dataset.

    Args:
        path: Optional override path to a CSV file with `day,in_bed`
            columns. Defaults to the vendored copy shipped in the repo's
            data/ directory.

    Returns:
        ObservedOutbreak with days (1..14) and in_bed (observed daily
        "boys in bed" counts, out of a total population of
        BOARDING_SCHOOL_TOTAL_POPULATION), parallel by index.

    Raises:
        FileNotFoundError: If no CSV file exists at path.
    """
    dataset_path = path if path is not None else DEFAULT_DATASET_PATH
    if not dataset_path.is_file():
        raise FileNotFoundError(f"No dataset found at {dataset_path}")

    days: list[int] = []
    in_bed: list[int] = []
    with dataset_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            days.append(int(row["day"]))
            in_bed.append(int(row["in_bed"]))
    return ObservedOutbreak(days=days, in_bed=in_bed)
