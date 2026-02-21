"""Shared fixtures: a deterministic random input generator.

The generator is how the stability property is exercised -- the original
implementation looked correct on the one shipped input and was wrong on many
others, so the suite asserts the rule over hundreds of generated cases rather
than over a single golden file.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_input_text(neighborhood_count: int, buyer_count: int, seed: int) -> str:
    """Build a syntactically valid input file with complete preference lists."""
    rnd = random.Random(seed)
    names = [f"N{i}" for i in range(neighborhood_count)]
    lines = [
        f"N {name} E:{rnd.randint(0, 10)} W:{rnd.randint(0, 10)} R:{rnd.randint(0, 10)}"
        for name in names
    ]
    for i in range(buyer_count):
        prefs = names[:]
        rnd.shuffle(prefs)
        lines.append(
            f"H H{i} E:{rnd.randint(0, 10)} W:{rnd.randint(0, 10)} "
            f"R:{rnd.randint(0, 10)} {'>'.join(prefs)}"
        )
    return "\n".join(lines) + "\n"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def sample_input() -> Path:
    """The input file shipped with the brief."""
    return REPO_ROOT / "input.txt"


@pytest.fixture
def write_input(tmp_path: Path):
    def _write(text: str, name: str = "input.txt") -> Path:
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    return _write
