from __future__ import annotations

import pytest

from pearl.parsing import InputError, parse_file, parse_lines


def test_parses_the_shipped_input(sample_input):
    neighborhoods, buyers = parse_file(sample_input)
    assert [n.name for n in neighborhoods] == ["N0", "N1", "N2"]
    assert len(buyers) == 12
    assert neighborhoods[0].scores == {"E": 7, "W": 7, "R": 10}
    assert buyers[0].name == "H0"
    assert buyers[0].goals == {"E": 3, "W": 9, "R": 2}
    assert buyers[0].preferences == ("N2", "N0", "N1")


def test_blank_lines_and_comments_are_ignored():
    text = """
    # a comment

    N N0 E:1 W:1 R:1
    H H0 E:1 W:1 R:1 N0   # trailing comment
    """
    neighborhoods, buyers = parse_lines(text.splitlines())
    assert len(neighborhoods) == 1
    assert len(buyers) == 1


def test_trailing_blank_line_does_not_crash():
    # The original reader indexed parts[0] unconditionally and raised
    # IndexError on any empty line.
    _, buyers = parse_lines(["N N0 E:1 W:1 R:1", "H H0 E:1 W:1 R:1 N0", "", "  "])
    assert len(buyers) == 1


@pytest.mark.parametrize(
    ("line", "fragment"),
    [
        ("X X0 E:1 W:1 R:1", "unknown record type"),
        ("N N0 E:1 W:1", "expected 5 fields"),
        ("N N0 E:1 W:1 R:1 extra", "expected 5 fields"),
        ("N N0 E:1 W:1 Q:1", "unknown axis"),
        ("N N0 E:1 E:2 R:1", "given twice"),
        ("N N0 E:1 W:1 Rx", "expected AXIS:VALUE"),
    ],
)
def test_malformed_records_are_rejected(line, fragment):
    with pytest.raises(InputError, match=fragment):
        parse_lines([line, "H H0 E:1 W:1 R:1 N0"])


def test_duplicate_names_are_rejected():
    with pytest.raises(InputError, match="duplicate name"):
        parse_lines(["N N0 E:1 W:1 R:1", "N N0 E:2 W:2 R:2", "H H0 E:1 W:1 R:1 N0"])


def test_repeated_preference_is_rejected():
    with pytest.raises(InputError, match="more than once"):
        parse_lines(["N N0 E:1 W:1 R:1", "H H0 E:1 W:1 R:1 N0>N0"])


def test_error_reports_the_line_number():
    with pytest.raises(InputError) as excinfo:
        parse_lines(["N N0 E:1 W:1 R:1", "H H0 E:1 W:1 R:1 N0", "N N9 E:1 W:1"])
    assert excinfo.value.line_number == 3


def test_input_without_neighborhoods_is_rejected():
    with pytest.raises(InputError, match="no neighborhood"):
        parse_lines(["H H0 E:1 W:1 R:1 N0"])


def test_input_without_buyers_is_rejected():
    with pytest.raises(InputError, match="no home buyer"):
        parse_lines(["N N0 E:1 W:1 R:1"])


def test_whole_file_errors_carry_no_line_number():
    with pytest.raises(InputError) as excinfo:
        parse_lines(["# only a comment", ""])
    assert excinfo.value.line_number is None
    assert not str(excinfo.value).startswith("line")
