"""Writing the output format.

One line per neighborhood, in the order the neighborhoods appeared in the
input, buyers ordered by fit (highest first)::

    N0: H5(161) H11(154) H2(128) H4(122)
"""

from __future__ import annotations

from pathlib import Path

from pearl.models import Assignment


def format_assignment(assignment: Assignment) -> str:
    """Render an assignment as the expected output text, newline-terminated."""
    lines = [
        f"{name}: " + " ".join(f"{p.buyer}({p.fit})" for p in placed)
        for name, placed in assignment.placements.items()
    ]
    return "".join(f"{line.rstrip()}\n" for line in lines)


def write_assignment(path: str | Path, assignment: Assignment) -> None:
    """Write the rendered assignment to ``path``."""
    Path(path).write_text(format_assignment(assignment), encoding="utf-8")
