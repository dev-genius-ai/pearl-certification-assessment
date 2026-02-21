"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from pearl.matching import assign, find_blocking_pair
from pearl.parsing import InputError, parse_file
from pearl.rendering import format_assignment, write_assignment
from pearl.scoring import available_scorers, get_scorer

DEFAULT_INPUT = "input.txt"
DEFAULT_OUTPUT = "generated_output.txt"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pearl",
        description="Place home buyers into neighborhoods by certification fit.",
    )
    parser.add_argument(
        "input", nargs="?", default=DEFAULT_INPUT, help=f"input file (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT, help=f"output file (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="print the result instead of writing a file"
    )
    parser.add_argument(
        "--scorer",
        default="dot",
        choices=available_scorers(),
        help="fit function to use (default: dot)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="re-check the result against the brief's stability rule and fail if it is violated",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        neighborhoods, buyers = parse_file(args.input)
    except InputError as exc:
        print(f"error: {args.input}: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {args.input}: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"error: cannot read {args.input}: not UTF-8 text", file=sys.stderr)
        return 2

    scorer = get_scorer(args.scorer)
    try:
        assignment = assign(buyers, neighborhoods, scorer)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.verify:
        blocking = find_blocking_pair(assignment, buyers, neighborhoods, scorer)
        if blocking is not None:
            print(f"error: unstable assignment: {blocking.describe()}", file=sys.stderr)
            return 1
        print(
            f"verified: stable placement of {len(buyers)} buyers "
            f"across {len(neighborhoods)} neighborhoods",
            file=sys.stderr,
        )

    if args.stdout:
        sys.stdout.write(format_assignment(assignment))
    else:
        try:
            write_assignment(args.output, assignment)
        except OSError as exc:
            print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
