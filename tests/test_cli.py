from __future__ import annotations

import pytest

from pearl.cli import main

EXPECTED = (
    "N0: H5(161) H11(154) H2(128) H4(122)\n"
    "N1: H9(23) H8(21) H7(20) H1(18)\n"
    "N2: H6(128) H3(120) H10(86) H0(83)\n"
)


def test_end_to_end_writes_the_expected_output_file(sample_input, tmp_path):
    # This is the assertion the original single test made, preserved.
    out = tmp_path / "generated_output.txt"
    assert main([str(sample_input), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == EXPECTED


def test_stdout_mode_prints_the_result(sample_input, capsys):
    assert main([str(sample_input), "--stdout"]) == 0
    assert capsys.readouterr().out == EXPECTED


def test_verify_reports_success(sample_input, capsys):
    assert main([str(sample_input), "--stdout", "--verify"]) == 0
    assert "verified: stable placement of 12 buyers" in capsys.readouterr().err


def test_missing_file_exits_with_code_two(tmp_path, capsys):
    assert main([str(tmp_path / "nope.txt")]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_malformed_input_exits_with_code_two(write_input, capsys):
    bad = write_input("N N0 E:1 W:1\nH H0 E:1 W:1 R:1 N0\n")
    assert main([str(bad)]) == 2
    assert "line 1" in capsys.readouterr().err


def test_unknown_scorer_is_rejected_by_argparse(sample_input):
    with pytest.raises(SystemExit):
        main([str(sample_input), "--scorer", "nope"])
