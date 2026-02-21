"""Domain types.

These are plain immutable value objects with no I/O and no algorithm in them,
so every other module can depend on this one without depending on anything else.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

#: The three certification axes a neighborhood is scored on and a buyer has
#: goals for: Energy efficiency, Water, Resilience.
AXES: tuple[str, ...] = ("E", "W", "R")


@dataclass(frozen=True, slots=True)
class Neighborhood:
    """A neighborhood and its certification scores."""

    name: str
    scores: Mapping[str, int]

    def __post_init__(self) -> None:
        missing = [axis for axis in AXES if axis not in self.scores]
        if missing:
            raise ValueError(f"neighborhood {self.name!r} is missing axes {missing}")


@dataclass(frozen=True, slots=True)
class HomeBuyer:
    """A home buyer, their goals on each axis, and their neighborhood ranking.

    ``preferences`` is ordered most-preferred first.
    """

    name: str
    goals: Mapping[str, int]
    preferences: Sequence[str]

    def __post_init__(self) -> None:
        missing = [axis for axis in AXES if axis not in self.goals]
        if missing:
            raise ValueError(f"home buyer {self.name!r} is missing axes {missing}")
        if not self.preferences:
            raise ValueError(f"home buyer {self.name!r} has no preferences")
        if len(set(self.preferences)) != len(self.preferences):
            raise ValueError(f"home buyer {self.name!r} lists a neighborhood more than once")


@dataclass(frozen=True, slots=True)
class Placement:
    """One buyer placed in one neighborhood, with the fit score that earned it."""

    buyer: str
    fit: int


@dataclass(frozen=True, slots=True)
class Assignment:
    """The complete result: every neighborhood mapped to its placed buyers.

    Placements within a neighborhood are ordered by fit, highest first.
    """

    placements: Mapping[str, tuple[Placement, ...]] = field(default_factory=dict)

    def neighborhood_of(self, buyer: str) -> str | None:
        """Return the neighborhood ``buyer`` was placed in, or ``None``."""
        for name, placed in self.placements.items():
            if any(p.buyer == buyer for p in placed):
                return name
        return None

    @property
    def placed_buyers(self) -> tuple[str, ...]:
        return tuple(p.buyer for placed in self.placements.values() for p in placed)
