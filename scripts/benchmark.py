"""Measure where the time actually goes, so the README's numbers are reproducible.

Run with: python scripts/benchmark.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pearl.matching import assign, is_stable
from pearl.parsing import parse_lines
from tests.conftest import make_input_text

CASES = [(3, 12), (10, 1_000), (25, 10_000), (50, 50_000)]


def main() -> int:
    header = f"{'neighborhoods':>14} {'buyers':>8} {'parse':>9} {'assign':>9} {'verify':>9}"
    print(header)
    print("-" * len(header))
    for hood_count, buyer_count in CASES:
        text = make_input_text(hood_count, buyer_count, seed=1)

        start = time.perf_counter()
        neighborhoods, buyers = parse_lines(text.splitlines())
        t_parse = time.perf_counter() - start

        start = time.perf_counter()
        assignment = assign(buyers, neighborhoods)
        t_assign = time.perf_counter() - start

        start = time.perf_counter()
        stable = is_stable(assignment, buyers, neighborhoods)
        t_verify = time.perf_counter() - start

        assert stable, "produced an unstable assignment"
        assert len(assignment.placed_buyers) == buyer_count
        print(
            f"{hood_count:>14} {buyer_count:>8} "
            f"{t_parse:>8.3f}s {t_assign:>8.3f}s {t_verify:>8.3f}s"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
