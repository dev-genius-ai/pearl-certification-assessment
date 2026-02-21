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


def test_non_utf8_input_exits_with_code_two(tmp_path, capsys):
    bad = tmp_path / "latin1.txt"
    bad.write_bytes(b"N N\xe9 E:1 W:1 R:1\n")
    assert main([str(bad)]) == 2
    assert "not UTF-8" in capsys.readouterr().err


def test_unwritable_output_exits_with_code_two(sample_input, tmp_path, capsys):
    out = tmp_path / "missing-dir" / "out.txt"
    assert main([str(sample_input), "-o", str(out)]) == 2
    assert "cannot write" in capsys.readouterr().err
    assert not out.exists()


def test_unplaced_buyers_are_named_on_stderr(write_input, capsys):
    path = write_input(
        "N N0 E:1 W:1 R:1\nN N1 E:1 W:1 R:1\nH HA E:9 W:9 R:9 N0>N1\nH HB E:1 W:1 R:1 N0\n"
    )
    assert main([str(path), "--stdout", "--verify"]) == 0
    captured = capsys.readouterr()
    assert "1 buyer(s) left unplaced" in captured.err
    assert "HB" in captured.err
    assert "stable placement of 1 buyers" in captured.err
    assert captured.out == "N0: HA(27)\nN1:\n"


def test_no_warning_when_everyone_is_placed(sample_input, capsys):
    assert main([str(sample_input), "--stdout"]) == 0
    assert "warning" not in capsys.readouterr().err
