from __future__ import annotations

from pearl.models import Assignment, Placement
from pearl.rendering import format_assignment, write_assignment

SAMPLE = Assignment(
    {
        "N0": (Placement("H5", 161), Placement("H11", 154)),
        "N1": (),
    }
)


def test_format_matches_the_expected_shape():
    assert format_assignment(SAMPLE) == "N0: H5(161) H11(154)\nN1:\n"


def test_an_empty_neighborhood_has_no_trailing_space():
    assert "N1:\n" in format_assignment(SAMPLE)
    assert "N1: \n" not in format_assignment(SAMPLE)


def test_write_assignment_round_trips(tmp_path):
    path = tmp_path / "out.txt"
    write_assignment(path, SAMPLE)
    assert path.read_text(encoding="utf-8") == format_assignment(SAMPLE)
