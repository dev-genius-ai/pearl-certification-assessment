"""Correctness of the placement algorithm.

Every test here is expressed against the brief's own rule, checked by
``find_blocking_pair``, rather than against a hard-coded answer. The
``REGRESSION`` cases are inputs on which the original implementation was
demonstrably wrong.
"""

from __future__ import annotations

import pytest

from pearl.matching import assign, capacities, find_blocking_pair, is_stable
from pearl.models import HomeBuyer, Neighborhood
from pearl.parsing import parse_file, parse_lines
from tests.conftest import make_input_text

# (neighborhoods, buyers, seed) triples on which the pre-uplift implementation
# produced an unstable placement, dropped a buyer, or placed one buyer twice.
REGRESSION = [(3, 12, 1), (4, 12, 2), (4, 16, 1), (5, 20, 0), (3, 13, 0)]

SWEEP = [
    (n, b, seed)
    for n, b in [(2, 10), (3, 12), (3, 13), (4, 12), (4, 17), (5, 20), (6, 31)]
    for seed in range(12)
]


def _load(text):
    return parse_lines(text.splitlines())


def test_capacities_split_evenly_when_divisible():
    hoods = [Neighborhood(f"N{i}", {"E": 0, "W": 0, "R": 0}) for i in range(3)]
    assert capacities(12, hoods) == {"N0": 4, "N1": 4, "N2": 4}


def test_capacities_never_drop_a_buyer_when_not_divisible():
    # The original used floor division, so 13 buyers over 3 neighborhoods left
    # one buyer with nowhere to go and the output was silently short.
    hoods = [Neighborhood(f"N{i}", {"E": 0, "W": 0, "R": 0}) for i in range(3)]
    room = capacities(13, hoods)
    assert sum(room.values()) == 13
    assert max(room.values()) - min(room.values()) == 1


def test_capacities_require_a_neighborhood():
    with pytest.raises(ValueError, match="at least one neighborhood"):
        capacities(5, [])


def test_shipped_input_reproduces_the_expected_answer(sample_input):
    from pearl.rendering import format_assignment

    neighborhoods, buyers = parse_file(sample_input)
    result = format_assignment(assign(buyers, neighborhoods))
    assert result == (
        "N0: H5(161) H11(154) H2(128) H4(122)\n"
        "N1: H9(23) H8(21) H7(20) H1(18)\n"
        "N2: H6(128) H3(120) H10(86) H0(83)\n"
    )


@pytest.mark.parametrize(("hoods", "buyer_count", "seed"), REGRESSION)
def test_regression_inputs_are_now_stable(hoods, buyer_count, seed):
    neighborhoods, buyers = _load(make_input_text(hoods, buyer_count, seed))
    assignment = assign(buyers, neighborhoods)
    blocking = find_blocking_pair(assignment, buyers, neighborhoods)
    assert blocking is None, blocking.describe()


@pytest.mark.parametrize(("hoods", "buyer_count", "seed"), SWEEP)
def test_every_generated_input_yields_a_stable_placement(hoods, buyer_count, seed):
    neighborhoods, buyers = _load(make_input_text(hoods, buyer_count, seed))
    assert is_stable(assign(buyers, neighborhoods), buyers, neighborhoods)


@pytest.mark.parametrize(("hoods", "buyer_count", "seed"), SWEEP)
def test_every_buyer_is_placed_exactly_once(hoods, buyer_count, seed):
    neighborhoods, buyers = _load(make_input_text(hoods, buyer_count, seed))
    placed = assign(buyers, neighborhoods).placed_buyers
    assert sorted(placed) == sorted(b.name for b in buyers)
    assert len(set(placed)) == len(placed)


@pytest.mark.parametrize(("hoods", "buyer_count", "seed"), SWEEP)
def test_capacity_is_respected(hoods, buyer_count, seed):
    neighborhoods, buyers = _load(make_input_text(hoods, buyer_count, seed))
    assignment = assign(buyers, neighborhoods)
    room = capacities(len(buyers), neighborhoods)
    for name, placed in assignment.placements.items():
        assert len(placed) == room[name]


def test_placements_are_ordered_by_fit_descending():
    neighborhoods, buyers = _load(make_input_text(3, 12, 7))
    for placed in assign(buyers, neighborhoods).placements.values():
        fits = [p.fit for p in placed]
        assert fits == sorted(fits, reverse=True)


def test_output_is_deterministic_when_fits_tie():
    # Two identical buyers competing for one slot: the result must not depend
    # on dict or set iteration order.
    text = "N N0 E:1 W:1 R:1\nN N1 E:0 W:0 R:0\nH HA E:5 W:5 R:5 N0>N1\nH HB E:5 W:5 R:5 N0>N1\n"
    neighborhoods, buyers = _load(text)
    first = assign(buyers, neighborhoods)
    assert first.placements["N0"][0].buyer == "HA"
    assert all(assign(buyers, neighborhoods) == first for _ in range(5))


def test_unknown_preference_is_rejected():
    neighborhoods = [Neighborhood("N0", {"E": 1, "W": 1, "R": 1})]
    buyers = [HomeBuyer("H0", {"E": 1, "W": 1, "R": 1}, ("N9",))]
    with pytest.raises(ValueError, match="unknown neighborhood"):
        assign(buyers, neighborhoods)


def test_blocking_pair_is_detected_in_a_deliberately_bad_assignment():
    # Swap the two buyers so each sits in the neighborhood the other fits.
    from pearl.models import Assignment, Placement

    text = (
        "N N0 E:10 W:0 R:0\nN N1 E:0 W:10 R:0\nH HA E:10 W:0 R:0 N0>N1\nH HB E:0 W:10 R:0 N1>N0\n"
    )
    neighborhoods, buyers = _load(text)
    swapped = Assignment({"N0": (Placement("HB", 0),), "N1": (Placement("HA", 0),)})
    blocking = find_blocking_pair(swapped, buyers, neighborhoods)
    assert blocking is not None
    assert blocking.buyer == "HA" and blocking.wants == "N0"
    assert "prefers N0" in blocking.describe()


def test_single_neighborhood_takes_everyone():
    text = "N N0 E:1 W:1 R:1\n" + "".join(f"H H{i} E:{i} W:1 R:1 N0\n" for i in range(5))
    neighborhoods, buyers = _load(text)
    assignment = assign(buyers, neighborhoods)
    assert len(assignment.placements["N0"]) == 5


def test_a_buyer_with_a_partial_preference_list_may_go_unplaced():
    # Two buyers, two neighborhoods, but HB will only consider the full one.
    text = "N N0 E:1 W:1 R:1\nN N1 E:1 W:1 R:1\nH HA E:9 W:9 R:9 N0>N1\nH HB E:1 W:1 R:1 N0\n"
    neighborhoods, buyers = _load(text)
    assignment = assign(buyers, neighborhoods)
    assert assignment.neighborhood_of("HA") == "N0"
    assert assignment.neighborhood_of("HB") is None


def test_fewer_buyers_than_neighborhoods_leaves_some_empty():
    # Capacities come out 1/1/0 here, and both buyers rank the zero-capacity
    # neighborhood first. That used to crash on an empty heap.
    text = (
        "N A E:1 W:1 R:1\nN B E:1 W:1 R:1\nN C E:1 W:1 R:1\n"
        "H H0 E:1 W:1 R:1 C>A>B\nH H1 E:2 W:2 R:2 C>B>A\n"
    )
    neighborhoods, buyers = _load(text)
    assignment = assign(buyers, neighborhoods)
    assert assignment.placements["C"] == ()
    assert sorted(assignment.placed_buyers) == ["H0", "H1"]
    assert is_stable(assignment, buyers, neighborhoods)


@pytest.mark.parametrize("seed", range(6))
def test_more_neighborhoods_than_buyers_is_stable(seed):
    neighborhoods, buyers = _load(make_input_text(7, 4, seed))
    assignment = assign(buyers, neighborhoods)
    assert sorted(assignment.placed_buyers) == sorted(b.name for b in buyers)
    assert is_stable(assignment, buyers, neighborhoods)


def test_blocking_pair_check_tolerates_a_neighborhood_missing_from_the_assignment():
    # One buyer, two neighborhoods: N1 has capacity 0 and is absent from the
    # assignment entirely. The check used to raise KeyError looking it up.
    neighborhoods, buyers = _load("N N0 E:1 W:1 R:1\nN N1 E:1 W:1 R:1\nH HA E:1 W:1 R:1 N1>N0\n")
    from pearl.models import Assignment, Placement

    partial = Assignment({"N0": (Placement("HA", 3),)})
    assert find_blocking_pair(partial, buyers, neighborhoods) is None
