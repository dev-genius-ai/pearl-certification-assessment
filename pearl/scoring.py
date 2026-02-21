"""How well a buyer fits a neighborhood.

The fit function is the one piece of this program a future developer is most
likely to want to change -- weight the axes, normalise them, use a distance
rather than a dot product -- so it is the single extension seam. Register an
alternative with :func:`register_scorer` and select it with ``--scorer``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol

from pearl.models import AXES, HomeBuyer, Neighborhood


class Scorer(Protocol):
    """Computes a buyer's fit for a neighborhood. Higher is a better fit."""

    def __call__(self, buyer: HomeBuyer, neighborhood: Neighborhood) -> int: ...


_REGISTRY: dict[str, Scorer] = {}


def register_scorer(name: str) -> Callable[[Scorer], Scorer]:
    """Register a named scorer, e.g. ``@register_scorer("dot")``."""

    def decorate(scorer: Scorer) -> Scorer:
        if name in _REGISTRY:
            raise ValueError(f"scorer {name!r} is already registered")
        _REGISTRY[name] = scorer
        return scorer

    return decorate


def get_scorer(name: str) -> Scorer:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"unknown scorer {name!r}; available: {', '.join(available_scorers())}"
        ) from None


def available_scorers() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


@register_scorer("dot")
def dot_product(buyer: HomeBuyer, neighborhood: Neighborhood) -> int:
    """The fit defined by the brief: the dot product of goals and scores."""
    return sum(buyer.goals[axis] * neighborhood.scores[axis] for axis in AXES)


def fit_matrix(
    buyers: list[HomeBuyer],
    neighborhoods: list[Neighborhood],
    scorer: Scorer = dot_product,
) -> dict[str, dict[str, int]]:
    """Precompute every ``fit[buyer][neighborhood]``.

    Built once up front so the matching loop never recomputes a score: the
    matching is O(buyers x neighborhoods) proposals and each one is a dict
    lookup rather than an arithmetic pass over the axes.
    """
    return {buyer.name: {n.name: scorer(buyer, n) for n in neighborhoods} for buyer in buyers}


def scores_for(fits: Mapping[str, Mapping[str, int]], neighborhood: str) -> dict[str, int]:
    """Slice the fit matrix to one neighborhood: ``{buyer: fit}``."""
    return {buyer: row[neighborhood] for buyer, row in fits.items()}
