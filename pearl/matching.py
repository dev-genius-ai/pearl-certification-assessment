"""The placement algorithm.

The brief asks for an assignment in which "no home buyer could subsequently
move to a more preferred neighborhood and be a better fit than those already
residing there". That is the definition of a *stable matching* in the
hospitals/residents problem, with neighborhoods as the hospitals, their
capacity as the even share of buyers, and each neighborhood ranking buyers by
fit score.

Buyer-proposing Gale-Shapley solves it exactly. It is guaranteed to terminate,
to place every buyer whose preference list is complete, and to produce the
buyer-optimal stable matching -- the one where every buyer does at least as
well as in any other stable assignment.
"""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from typing import NamedTuple

from pearl.models import Assignment, HomeBuyer, Neighborhood, Placement
from pearl.scoring import Scorer, dot_product, fit_matrix


class BlockingPair(NamedTuple):
    """Evidence that an assignment is unstable."""

    buyer: str
    wants: str
    instead_of: str | None
    beats: str | None

    def describe(self) -> str:
        placed = f"placed in {self.instead_of}" if self.instead_of else "unplaced"
        beaten = f"outfits {self.beats}" if self.beats else "and there is a free slot"
        return f"{self.buyer} ({placed}) prefers {self.wants} and {beaten}"


def capacities(buyer_count: int, neighborhoods: Sequence[Neighborhood]) -> dict[str, int]:
    """Split ``buyer_count`` places as evenly as possible across neighborhoods.

    When the split is not exact the remainder goes to the earliest
    neighborhoods in input order, so every capacity differs by at most one and
    the total is exactly ``buyer_count`` -- no buyer is silently dropped.
    """
    if not neighborhoods:
        raise ValueError("at least one neighborhood is required")
    base, extra = divmod(buyer_count, len(neighborhoods))
    return {n.name: base + (1 if i < extra else 0) for i, n in enumerate(neighborhoods)}


def _rank_tables(
    buyers: Sequence[HomeBuyer],
    neighborhoods: Sequence[Neighborhood],
    fits: Mapping[str, Mapping[str, int]],
) -> dict[str, dict[str, int]]:
    """For each neighborhood, rank every buyer. Rank 0 is the best fit.

    Equal fits are broken by buyer name so the whole program is deterministic:
    the same input always yields byte-identical output.
    """
    tables: dict[str, dict[str, int]] = {}
    for n in neighborhoods:
        ordered = sorted(buyers, key=lambda b: (-fits[b.name][n.name], b.name))
        tables[n.name] = {b.name: rank for rank, b in enumerate(ordered)}
    return tables


def assign(
    buyers: Sequence[HomeBuyer],
    neighborhoods: Sequence[Neighborhood],
    scorer: Scorer = dot_product,
) -> Assignment:
    """Place every buyer, returning a stable :class:`Assignment`.

    Buyers whose preference list does not cover enough neighborhoods may end up
    unplaced; every buyer listing all neighborhoods is always placed.
    """
    if not neighborhoods:
        raise ValueError("at least one neighborhood is required")
    known = {n.name for n in neighborhoods}
    for buyer in buyers:
        unknown = [p for p in buyer.preferences if p not in known]
        if unknown:
            raise ValueError(f"home buyer {buyer.name!r} prefers unknown neighborhood(s) {unknown}")

    fits = fit_matrix(list(buyers), list(neighborhoods), scorer)
    ranks = _rank_tables(buyers, neighborhoods, fits)
    room = capacities(len(buyers), neighborhoods)

    # Each neighborhood holds a max-heap on rank, so heap[0] is its worst
    # current occupant -- the one a better proposer displaces.
    held: dict[str, list[tuple[int, str]]] = {n.name: [] for n in neighborhoods}
    next_choice = {b.name: 0 for b in buyers}
    prefs = {b.name: b.preferences for b in buyers}
    free = deque(b.name for b in buyers)

    while free:
        buyer = free.popleft()
        options = prefs[buyer]
        while next_choice[buyer] < len(options):
            target = options[next_choice[buyer]]
            next_choice[buyer] += 1
            rank = ranks[target][buyer]
            occupants = held[target]
            if not room[target]:
                continue  # fewer buyers than neighborhoods: this one takes nobody
            if len(occupants) < room[target]:
                heapq.heappush(occupants, (-rank, buyer))
                break
            worst_rank, worst_buyer = occupants[0]
            if rank < -worst_rank:  # a better fit than the neighborhood's weakest
                heapq.heapreplace(occupants, (-rank, buyer))
                free.append(worst_buyer)
                break
            # rejected; fall through to the buyer's next preference

    placements = {
        n.name: tuple(
            sorted(
                (Placement(buyer, fits[buyer][n.name]) for _, buyer in held[n.name]),
                key=lambda p: (-p.fit, p.buyer),
            )
        )
        for n in neighborhoods
    }
    return Assignment(placements)


def find_blocking_pair(
    assignment: Assignment,
    buyers: Sequence[HomeBuyer],
    neighborhoods: Sequence[Neighborhood],
    scorer: Scorer = dot_product,
) -> BlockingPair | None:
    """Return the first violation of the brief's rule, or ``None`` if stable.

    This is the requirement restated as an executable check, independent of the
    algorithm that produced the assignment. It is what the tests assert against
    and what ``--verify`` runs.
    """
    fits = fit_matrix(list(buyers), list(neighborhoods), scorer)
    ranks = _rank_tables(buyers, neighborhoods, fits)
    room = capacities(len(buyers), neighborhoods)

    # Index the assignment once. Rescanning it per buyer would make this check
    # quadratic, and it exists to be cheap enough that --verify is always on.
    where = {
        placement.buyer: name
        for name, placed in assignment.placements.items()
        for placement in placed
    }
    occupancy = {name: len(placed) for name, placed in assignment.placements.items()}
    weakest: dict[str, str | None] = {}
    for name, placed in assignment.placements.items():
        rank_of = ranks[name]
        weakest[name] = max((p.buyer for p in placed), key=rank_of.__getitem__, default=None)

    for buyer in buyers:
        current = where.get(buyer.name)
        for wanted in buyer.preferences:
            if wanted == current:
                break  # nothing below this is an improvement
            if occupancy.get(wanted, 0) < room[wanted]:
                return BlockingPair(buyer.name, wanted, current, None)
            worst = weakest.get(wanted)
            if worst is not None and ranks[wanted][buyer.name] < ranks[wanted][worst]:
                return BlockingPair(buyer.name, wanted, current, worst)
    return None


def is_stable(
    assignment: Assignment,
    buyers: Sequence[HomeBuyer],
    neighborhoods: Sequence[Neighborhood],
    scorer: Scorer = dot_product,
) -> bool:
    """True when no buyer can improve on their placement. See the brief."""
    return find_blocking_pair(assignment, buyers, neighborhoods, scorer) is None


def iter_placements(assignment: Assignment) -> Iterable[tuple[str, Placement]]:
    for name, placed in assignment.placements.items():
        for placement in placed:
            yield name, placement
