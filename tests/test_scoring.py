from __future__ import annotations

import pytest

from pearl.models import HomeBuyer, Neighborhood
from pearl.scoring import (
    available_scorers,
    dot_product,
    fit_matrix,
    get_scorer,
    register_scorer,
)


def test_dot_product_matches_the_brief():
    # H0 E:3 W:9 R:2 against N2 E:7 W:6 R:4 -> 21 + 54 + 8 = 83
    buyer = HomeBuyer("H0", {"E": 3, "W": 9, "R": 2}, ("N2",))
    neighborhood = Neighborhood("N2", {"E": 7, "W": 6, "R": 4})
    assert dot_product(buyer, neighborhood) == 83


def test_fit_matrix_covers_every_pair():
    buyers = [HomeBuyer("H0", {"E": 1, "W": 1, "R": 1}, ("N0", "N1"))]
    neighborhoods = [
        Neighborhood("N0", {"E": 1, "W": 2, "R": 3}),
        Neighborhood("N1", {"E": 0, "W": 0, "R": 0}),
    ]
    assert fit_matrix(buyers, neighborhoods) == {"H0": {"N0": 6, "N1": 0}}


def test_default_scorer_is_registered():
    assert "dot" in available_scorers()
    assert get_scorer("dot") is dot_product


def test_unknown_scorer_names_the_alternatives():
    with pytest.raises(KeyError, match="dot"):
        get_scorer("nope")


def test_a_custom_scorer_can_be_registered_and_used():
    @register_scorer("energy-only")
    def energy_only(buyer, neighborhood):
        return buyer.goals["E"] * neighborhood.scores["E"]

    try:
        assert get_scorer("energy-only") is energy_only
        buyer = HomeBuyer("H0", {"E": 2, "W": 9, "R": 9}, ("N0",))
        neighborhood = Neighborhood("N0", {"E": 3, "W": 9, "R": 9})
        assert get_scorer("energy-only")(buyer, neighborhood) == 6
    finally:
        from pearl import scoring

        scoring._REGISTRY.pop("energy-only", None)


def test_registering_a_duplicate_name_is_rejected():
    with pytest.raises(ValueError, match="already registered"):
        register_scorer("dot")(dot_product)
