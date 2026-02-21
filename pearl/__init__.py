"""Pearl Certification neighborhood placement.

Assigns home buyers to Charlottesville neighborhoods so that the result is
*stable*: no buyer can move to a neighborhood they prefer and be a better fit
than someone already living there.
"""

from pearl.matching import assign, find_blocking_pair, is_stable
from pearl.models import Assignment, HomeBuyer, Neighborhood

__all__ = [
    "Assignment",
    "HomeBuyer",
    "Neighborhood",
    "assign",
    "find_blocking_pair",
    "is_stable",
]

__version__ = "1.0.0"
