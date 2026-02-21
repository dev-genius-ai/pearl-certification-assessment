"""Reading the input format.

Each non-empty line is either::

    N <name> E:<int> W:<int> R:<int>
    H <name> E:<int> W:<int> R:<int> <pref>><pref>><pref>

Parsing is deliberately strict and reports the offending line number, because
a silent misparse of a take-home input is worse than a refusal.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from pathlib import Path

from pearl.models import AXES, HomeBuyer, Neighborhood

_AXIS = re.compile(r"^([A-Z]):(-?\d+)$")


class InputError(ValueError):
    """Raised when the input file cannot be understood."""

    def __init__(self, line_number: int, message: str, line: str = "") -> None:
        self.line_number = line_number
        detail = f" in {line.strip()!r}" if line.strip() else ""
        super().__init__(f"line {line_number}: {message}{detail}")


def _parse_axes(tokens: Sequence[str], line_number: int, line: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for token in tokens:
        match = _AXIS.match(token)
        if not match:
            raise InputError(line_number, f"expected AXIS:VALUE, got {token!r}", line)
        axis, raw = match.group(1), match.group(2)
        if axis not in AXES:
            raise InputError(line_number, f"unknown axis {axis!r}", line)
        if axis in values:
            raise InputError(line_number, f"axis {axis!r} given twice", line)
        values[axis] = int(raw)
    missing = [axis for axis in AXES if axis not in values]
    if missing:
        raise InputError(line_number, f"missing axes {missing}", line)
    return values


def parse_lines(lines: Iterable[str]) -> tuple[list[Neighborhood], list[HomeBuyer]]:
    """Parse input lines. Blank lines and ``#`` comments are ignored."""
    neighborhoods: list[Neighborhood] = []
    buyers: list[HomeBuyer] = []
    seen: set[str] = set()

    for line_number, raw in enumerate(lines, start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        kind = parts[0]
        if kind not in {"N", "H"}:
            raise InputError(line_number, f"unknown record type {kind!r}", raw)
        expected = 5 if kind == "N" else 6
        if len(parts) != expected:
            raise InputError(line_number, f"expected {expected} fields, got {len(parts)}", raw)
        name = parts[1]
        if name in seen:
            raise InputError(line_number, f"duplicate name {name!r}", raw)
        seen.add(name)
        values = _parse_axes(parts[2:5], line_number, raw)
        if kind == "N":
            neighborhoods.append(Neighborhood(name, values))
        else:
            preferences = tuple(p for p in parts[5].split(">") if p)
            try:
                buyers.append(HomeBuyer(name, values, preferences))
            except ValueError as exc:
                raise InputError(line_number, str(exc), raw) from None

    if not neighborhoods:
        raise InputError(0, "input contains no neighborhood (N) records")
    if not buyers:
        raise InputError(0, "input contains no home buyer (H) records")
    return neighborhoods, buyers


def parse_file(path: str | Path) -> tuple[list[Neighborhood], list[HomeBuyer]]:
    """Parse an input file, streaming it a line at a time."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return parse_lines(handle)
