"""Common interface for listing sources."""

from abc import ABC, abstractmethod
from typing import List

from ..models import CondoListing


class ListingSource(ABC):
    """A source knows how to produce a list of CondoListing records."""

    name = "unknown-source"

    @abstractmethod
    def fetch_listings(self) -> List[CondoListing]:
        """Return the listings this source can currently provide."""
        raise NotImplementedError
